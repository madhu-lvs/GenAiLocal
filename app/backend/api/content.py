
import io
import mimetypes
from typing import Any, Dict, Union
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import ContainerClient
from azure.storage.blob.aio import StorageStreamDownloader as BlobDownloader
from azure.storage.filedatalake.aio import FileSystemClient
from azure.storage.filedatalake.aio import StorageStreamDownloader as DatalakeDownloader
from quart import (
    Blueprint,
    abort,
    current_app,
    send_file,
)
from config import (
    CONFIG_BLOB_CONTAINER_CLIENT,
    CONFIG_USER_BLOB_CONTAINER_CLIENT
)

from decorators import authenticated_path

bp = Blueprint('content', __name__)

@bp.route("/content/<path>")
@authenticated_path
async def content_file(path: str, auth_claims: Dict[str, Any]):
    """
    Serve content files from blob storage from within the app to keep the example self-contained.
    *** NOTE *** if you are using app services authentication, this route will return unauthorized to all users that are not logged in
    if AZURE_ENFORCE_ACCESS_CONTROL is not set or false, logged in users can access all files regardless of access control
    if AZURE_ENFORCE_ACCESS_CONTROL is set to true, logged in users can only access files they have access to
    This is also slow and memory hungry.
    """
    # Remove page number from path, filename-1.txt -> filename.txt
    # This shouldn't typically be necessary as browsers don't send hash fragments to servers
    if path.find("#page=") > 0:
        path_parts = path.rsplit("#page=", 1)
        path = path_parts[0]
    current_app.logger.info("Opening file %s", path)
    blob_container_client: ContainerClient = current_app.config[CONFIG_BLOB_CONTAINER_CLIENT]
    blob: Union[BlobDownloader, DatalakeDownloader]
    try:
        blob = await blob_container_client.get_blob_client(path).download_blob()
    except ResourceNotFoundError:
        current_app.logger.info("Path not found in general Blob container: %s", path)
        try:
            user_oid = auth_claims["oid"]
            user_blob_container_client = current_app.config[CONFIG_USER_BLOB_CONTAINER_CLIENT]
            user_directory_client: FileSystemClient = user_blob_container_client.get_directory_client(user_oid)
            file_client = user_directory_client.get_file_client(path)
            blob = await file_client.download_file()
        except ResourceNotFoundError:
            current_app.logger.exception("Path not found in DataLake: %s", path)
            abort(404)
    if not blob.properties or not blob.properties.has_key("content_settings"):
        abort(404)
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    await blob.readinto(blob_file)
    blob_file.seek(0)
    return await send_file(blob_file, mimetype=mime_type, as_attachment=False, attachment_filename=path)
