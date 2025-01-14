"""
Azure Blob Storage Manager Module

This module provides functionality for managing Azure Blob Storage operations, including:
- Uploading and removing blobs containing citation information
- Managing and converting PDF files to page-specific images
- Handling SAS token generation for secure access
- Supporting both synchronous and asynchronous operations
"""

import datetime
import io
import logging
import os
import re
from typing import List, Optional, Union

import fitz  # type: ignore
from azure.core.credentials_async import AsyncTokenCredential
from azure.storage.blob import (
    BlobSasPermissions,
    UserDelegationKey,
    generate_blob_sas,
)
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

from .listfilestrategy import File

logger = logging.getLogger("scripts")


class BlobManager:
    """
    Manages blob storage operations for document processing and storage.
    
    This class handles the upload, removal, and conversion of documents in Azure Blob Storage,
    with special handling for PDF documents that need to be converted to images.
    
    Attributes:
        endpoint (str): The Azure Blob Storage endpoint URL
        container (str): The name of the blob container
        account (str): The storage account name
        credential (Union[AsyncTokenCredential, str]): Azure credentials or connection string
        resourceGroup (str): Azure resource group name
        subscriptionId (str): Azure subscription ID
        store_page_images (bool): Whether to store individual page images
        user_delegation_key (Optional[UserDelegationKey]): Cached delegation key for SAS generation
    """

    def __init__(
        self,
        endpoint: str,
        container: str,
        account: str,
        credential: Union[AsyncTokenCredential, str],
        resourceGroup: str,
        subscriptionId: str,
        store_page_images: bool = False,
    ):
        """
        Initialize the BlobManager with Azure storage configuration.

        Args:
            endpoint: The Azure Blob Storage endpoint URL
            container: The name of the blob container
            account: The storage account name
            credential: Azure credentials or connection string
            resourceGroup: Azure resource group name
            subscriptionId: Azure subscription ID
            store_page_images: Whether to store individual page images (default: False)
        """
        self.endpoint = endpoint
        self.credential = credential
        self.account = account
        self.container = container
        self.store_page_images = store_page_images
        self.resourceGroup = resourceGroup
        self.subscriptionId = subscriptionId
        self.user_delegation_key: Optional[UserDelegationKey] = None

    async def upload_blob(self, file: File) -> Optional[List[str]]:
        """
        Upload a file to blob storage and optionally convert PDF pages to images.

        Args:
            file: File object containing the content to upload

        Returns:
            Optional[List[str]]: List of SAS URIs for uploaded page images if store_page_images is True,
                               None otherwise
        """
        async with BlobServiceClient(
            account_url=self.endpoint, credential=self.credential, max_single_put_size=4 * 1024 * 1024
        ) as service_client, service_client.get_container_client(self.container) as container_client:
            if not await container_client.exists():
                await container_client.create_container()

            if file.url is None:
                with open(file.content.name, "rb") as reopened_file:
                    blob_name = BlobManager.blob_name_from_file_name(file.content.name)
                    logger.info("Uploading blob for whole file -> %s", blob_name)
                    blob_client = await container_client.upload_blob(blob_name, reopened_file, overwrite=True)
                    file.url = blob_client.url

            if self.store_page_images:
                if os.path.splitext(file.content.name)[1].lower() == ".pdf":
                    return await self.upload_pdf_blob_images(service_client, container_client, file)
                else:
                    logger.info("File %s is not a PDF, skipping image upload", file.content.name)

        return None

    def get_managedidentity_connectionstring(self) -> str:
        """
        Generate a connection string for managed identity authentication.
        
        Returns:
            str: Formatted connection string
        """
        return f"ResourceId=/subscriptions/{self.subscriptionId}/resourceGroups/{self.resourceGroup}/providers/Microsoft.Storage/storageAccounts/{self.account};"

    async def upload_pdf_blob_images(
        self, service_client: BlobServiceClient, container_client: ContainerClient, file: File
    ) -> List[str]:
        """
        Convert PDF pages to images and upload them to blob storage.
        
        Args:
            service_client: Azure BlobServiceClient instance
            container_client: Azure ContainerClient instance
            file: File object containing the PDF content
            
        Returns:
            List[str]: List of SAS URIs for the uploaded page images
        """
        with open(file.content.name, "rb") as reopened_file:
            reader = PdfReader(reopened_file)
            page_count = len(reader.pages)
            
        doc = fitz.open(file.content.name)
        sas_uris = []
        start_time = datetime.datetime.now(datetime.timezone.utc)
        expiry_time = start_time + datetime.timedelta(days=1)

        font = None
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 20)
            except OSError:
                logger.info("Unable to find arial.ttf or FreeMono.ttf, using default font")

        for i in range(page_count):
            blob_name = BlobManager.blob_image_name_from_file_page(file.content.name, i)
            logger.info("Converting page %s to image and uploading -> %s", i, blob_name)

            doc = fitz.open(file.content.name)
            page = doc.load_page(i)
            pix = page.get_pixmap()
            original_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            text_height = 40
            new_img = Image.new("RGB", (original_img.width, original_img.height + text_height), "white")
            new_img.paste(original_img, (0, text_height))

            draw = ImageDraw.Draw(new_img)
            text = f"SourceFileName:{blob_name}"
            draw.text((10, 10), text, font=font, fill="black")

            output = io.BytesIO()
            new_img.save(output, format="PNG")
            output.seek(0)

            blob_client = await container_client.upload_blob(blob_name, output, overwrite=True)
            
            if not self.user_delegation_key:
                self.user_delegation_key = await service_client.get_user_delegation_key(start_time, expiry_time)

            if blob_client.account_name:
                sas_token = generate_blob_sas(
                    account_name=blob_client.account_name,
                    container_name=blob_client.container_name,
                    blob_name=blob_client.blob_name,
                    user_delegation_key=self.user_delegation_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=expiry_time,
                    start=start_time,
                )
                sas_uris.append(f"{blob_client.url}?{sas_token}")

        return sas_uris

    async def remove_blob(self, path: Optional[str] = None):
        """
        Remove blobs from storage, either a specific path or all blobs.
        
        Args:
            path: Optional path to specific blob to remove. If None, removes all blobs.
        """
        async with BlobServiceClient(
            account_url=self.endpoint, credential=self.credential
        ) as service_client, service_client.get_container_client(self.container) as container_client:
            if not await container_client.exists():
                return
                
            if path is None:
                prefix = None
                blobs = container_client.list_blob_names()
            else:
                prefix = os.path.splitext(os.path.basename(path))[0]
                blobs = container_client.list_blob_names(name_starts_with=os.path.splitext(os.path.basename(prefix))[0])
                
            async for blob_path in blobs:
                if (prefix is not None and not (re.match(rf"{prefix}-\d+\.pdf", blob_path) or 
                    re.match(rf"{prefix}-\d+\.png", blob_path))) or \
                    (path is not None and blob_path == os.path.basename(path)):
                    continue
                    
                logger.info("Removing blob %s", blob_path)
                await container_client.delete_blob(blob_path)

    @staticmethod
    def sourcepage_from_file_page(filename: str, page: int = 0) -> str:
        """Generate a source page reference from a filename and page number."""
        if os.path.splitext(filename)[1].lower() == ".pdf":
            return f"{os.path.basename(filename)}#page={page+1}"
        return os.path.basename(filename)

    @staticmethod
    def blob_image_name_from_file_page(filename: str, page: int = 0) -> str:
        """Generate a blob name for a page image from a filename and page number."""
        return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".png"

    @staticmethod
    def blob_name_from_file_name(filename: str) -> str:
        """Generate a blob name from a filename."""
        return os.path.basename(filename)