
import io
from quart import Blueprint, current_app, jsonify, request
from decorators import roles_required
from config import CONFIG_BLOB_CONTAINER_CLIENT, CONFIG_INGESTER
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import ContainerClient

bp = Blueprint('upload', __name__)

# Async function to list blobs with pagination
async def list_blobs_with_pagination(container_client: ContainerClient):
    """
        list blobs
    """
    blobs = []
    # List blobs with pagination
    tag_filter = "UploadedBy = 'ADMIN'"

    # Print the names of the filtered blobs
    async for blob in container_client.find_blobs_by_tags(tag_filter):
        blobs.append(blob['name'])

    return blobs

@bp.post("/upload")
@roles_required(['Admin'])
async def upload():
    request_files = await request.files
    if "file" not in request_files:
        # If no files were included in the request, return an error response
        return jsonify({"message": "No file part in the request", "status": "failed"}), 400

    file = request_files.getlist("file")[0]
    blob_container_client: ContainerClient = current_app.config[CONFIG_BLOB_CONTAINER_CLIENT]
    file_client = blob_container_client
    file_io = file
    file_io.name = file.filename
    file_io = io.BufferedReader(file_io)
    await file_client.upload_blob(file.filename, file_io, overwrite=True, tags={"UploadedBy": "ADMIN"})
    file_io.seek(0)
    
    return jsonify({"message": "File uploaded successfully"}), 200


@bp.post("/delete_uploaded")
@roles_required(['Admin'])
async def delete_uploaded():
    request_json = await request.get_json()
    filename = request_json.get("filename")
    blob_container_client: ContainerClient = current_app.config[CONFIG_BLOB_CONTAINER_CLIENT]
    await blob_container_client.delete_blob(filename)
    ingester = current_app.config[CONFIG_INGESTER]
    await ingester.remove_file(filename)
    return jsonify({"message": f"File {filename} deleted successfully"}), 200


@bp.get("/list_uploaded")
@roles_required(['Admin'])
async def list_uploaded():
    blob_container_client: ContainerClient = current_app.config[CONFIG_BLOB_CONTAINER_CLIENT]
    files = []
    try:
        # Call the async function to list blobs
        blobs = await list_blobs_with_pagination(blob_container_client)

        # Return paginated response
        return jsonify({
            'blobs': blobs,
        })
    except ResourceNotFoundError as error:
        if error.status_code != 404:
            current_app.logger.exception("Error listing uploaded files", error)
    return jsonify(files), 200