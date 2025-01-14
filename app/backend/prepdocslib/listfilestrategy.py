import base64
import hashlib
import logging
import os
import re
import tempfile
from abc import ABC
from glob import glob
from typing import IO, AsyncGenerator, Dict, List, Optional, Union

from azure.core.credentials_async import AsyncTokenCredential
from azure.storage.filedatalake.aio import (
    DataLakeServiceClient,
)

logger = logging.getLogger("scripts")


class File:
    """
    Represents a file for processing with optional access control metadata.
    
    This class encapsulates a file's content and its associated metadata, including:
    - File content as an IO stream
    - Access control lists (ACLs) for security
    - Optional URL for remote file access
    - Methods for generating unique identifiers and handling file extensions
    """

    def __init__(self, content: IO, acls: Optional[dict[str, list]] = None, url: Optional[str] = None):
        self.content = content
        self.acls = acls or {}
        self.url = url

    def filename(self) -> str:
        """Returns the base filename without path."""
        return os.path.basename(self.content.name)

    def file_extension(self) -> str:
        """Returns the file extension including the dot."""
        return os.path.splitext(self.content.name)[1]

    def filename_to_id(self) -> str:
        """
        Generates a unique identifier for the file based on filename and ACLs.
        """
        # Pre-encode values once for efficiency
        encoded_filename = self.filename().encode("utf-8")
        filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", self.filename())
        filename_hash = base64.b16encode(encoded_filename).decode("ascii")
        
        if not self.acls:
            return f"file-{filename_ascii}-{filename_hash}"
            
        acls_hash = base64.b16encode(str(self.acls).encode("utf-8")).decode("ascii")
        return f"file-{filename_ascii}-{filename_hash}{acls_hash}"

    def close(self):
        """Safely closes the file's IO stream if it exists."""
        if self.content:
            self.content.close()


class ListFileStrategy(ABC):
    """
    Abstract base class defining the interface for listing files from various sources.
    """

    async def list(self) -> AsyncGenerator[File, None]:
        """Lists available files, yielding File objects for processing."""
        if False:  # pragma: no cover - this is necessary for mypy to type check
            yield

    async def list_paths(self) -> AsyncGenerator[str, None]:
        """Lists available file paths as strings."""
        if False:  # pragma: no cover - this is necessary for mypy to type check
            yield


class LocalListFileStrategy(ListFileStrategy):
    """
    Strategy implementation for listing files from a local filesystem.
    """

    def __init__(self, path_pattern: str):
        self.path_pattern = path_pattern

    async def list_paths(self) -> AsyncGenerator[str, None]:
        """Lists all file paths matching the configured pattern."""
        async for p in self._list_paths(self.path_pattern):
            yield p

    async def _list_paths(self, path_pattern: str) -> AsyncGenerator[str, None]:
        """Internal recursive implementation of path listing."""
        for path in glob(path_pattern):
            if os.path.isdir(path):
                async for p in self._list_paths(f"{path}/*"):
                    yield p
            else:
                # Only yield non-MD5 files
                if not path.endswith('.md5'):
                    yield path

    async def list(self) -> AsyncGenerator[File, None]:
        """Lists files, yielding File objects for unchanged files only."""
        async for path in self.list_paths():
            if not self.check_md5(path):
                yield File(content=open(path, mode="rb"))

    def check_md5(self, path: str) -> bool:
        """
        Checks if a file has changed by comparing MD5 hashes.
        Returns True if unchanged, False if changed or no hash exists.
        """
        # Skip MD5 files themselves
        if path.endswith(".md5"):
            return True

        hash_path = f"{path}.md5"
        
        # If no hash file exists, file should be processed
        if not os.path.exists(hash_path):
            self._write_hash(path, hash_path)
            return False

        # Compare stored hash with current
        with open(path, "rb") as file:
            current_hash = hashlib.md5(file.read()).hexdigest()
            
        with open(hash_path, encoding="utf-8") as hash_file:
            stored_hash = hash_file.read().strip()
            
        if current_hash == stored_hash:
            logger.info("Skipping %s, no changes detected.", path)
            return True
            
        self._write_hash(path, hash_path, current_hash)
        return False
        
    def _write_hash(self, path: str, hash_path: str, current_hash: Optional[str] = None):
        """Helper to write MD5 hash file."""
        if current_hash is None:
            with open(path, "rb") as file:
                current_hash = hashlib.md5(file.read()).hexdigest()
                
        with open(hash_path, "w", encoding="utf-8") as hash_file:
            hash_file.write(current_hash)


class ADLSGen2ListFileStrategy(ListFileStrategy):
    """
    Strategy implementation for listing files from Azure Data Lake Storage Gen2.
    """

    def __init__(
        self,
        data_lake_storage_account: str,
        data_lake_filesystem: str,
        data_lake_path: str,
        credential: Union[AsyncTokenCredential, str],
    ):
        self.data_lake_storage_account = data_lake_storage_account
        self.data_lake_filesystem = data_lake_filesystem
        self.data_lake_path = data_lake_path
        self.credential = credential
        self._datalake_url = f"https://{data_lake_storage_account}.dfs.core.windows.net"

    async def list_paths(self) -> AsyncGenerator[str, None]:
        """Lists paths from Azure Data Lake Storage."""
        async with DataLakeServiceClient(
            account_url=self._datalake_url, 
            credential=self.credential
        ) as service_client, service_client.get_file_system_client(self.data_lake_filesystem) as filesystem_client:
            async for path in filesystem_client.get_paths(path=self.data_lake_path, recursive=True):
                if not path.is_directory:
                    yield path.name

    async def list(self) -> AsyncGenerator[File, None]:
        """Lists files from Azure Data Lake Storage, downloading to temp storage."""
        async with DataLakeServiceClient(
            account_url=self._datalake_url,
            credential=self.credential
        ) as service_client, service_client.get_file_system_client(self.data_lake_filesystem) as filesystem_client:
            async for path in self.list_paths():
                temp_file_path = os.path.join(tempfile.gettempdir(), os.path.basename(path))
                try:
                    async with filesystem_client.get_file_client(path) as file_client:
                        acls = await self._get_acls(file_client)
                        
                        with open(temp_file_path, "wb") as temp_file:
                            downloader = await file_client.download_file()
                            await downloader.readinto(temp_file)
                            
                        yield File(content=open(temp_file_path, "rb"), acls=acls, url=file_client.url)
                        
                except Exception as e:
                    logger.error("Error processing %s: %s", path, str(e))
                    self._cleanup_temp_file(temp_file_path)

    async def _get_acls(self, file_client) -> Dict[str, List[str]]:
        """Helper to extract ACLs from a file."""
        acls: Dict[str, List[str]] = {"oids": [], "groups": []}
        try:
            access_control = await file_client.get_access_control(upn=False)
            for acl in access_control["acl"].split(","):
                acl_parts = acl.split(":")
                if len(acl_parts) == 3 and acl_parts[1]:
                    if acl_parts[0] == "user" and "r" in acl_parts[2]:
                        acls["oids"].append(acl_parts[1])
                    elif acl_parts[0] == "group" and "r" in acl_parts[2]:
                        acls["groups"].append(acl_parts[1])
        except Exception as e:
            logger.warning("Failed to get ACLs: %s", str(e))
        return acls

    def _cleanup_temp_file(self, temp_file_path: str):
        """Helper to safely remove temporary files."""
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception as e:
            logger.error("Failed to delete temporary file %s: %s", temp_file_path, str(e))