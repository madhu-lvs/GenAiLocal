"""
Module for handling image processing and conversion in the chat interface.

This module provides utilities for working with images in the chat application,
including downloading blob images and converting them to base64 format for display.
It also includes type definitions for image URL handling and detail level specification.

Note: This is a core module that maintains strict backwards compatibility for
system-wide image management.
"""

import base64
import logging
import os
from typing import Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import ContainerClient
from typing_extensions import Literal, Required, TypedDict

from approaches.approach import Document


class ImageURL(TypedDict, total=False):
    """
    Type definition for image URL configuration and detail level.

    Attributes:
        url (Required[str]): URL of the image or base64 encoded image data.
            Required field that must contain either a valid URL or base64 string.
        
        detail (Literal["auto", "low", "high"]): Specifies the detail level for
            image processing. Optional field defaulting to "auto" if not specified.
    """
    url: Required[str]
    """Either a URL of the image or the base64 encoded image data."""

    detail: Literal["auto", "low", "high"]
    """Specifies the detail level of the image."""


async def download_blob_as_base64(blob_container_client: ContainerClient, file_path: str) -> Optional[str]:
    """
    Downloads an image blob and converts it to a base64-encoded data URL.

    Downloads a PNG image from blob storage corresponding to the given file path.
    The function assumes the image has the same base name as the file but with
    a .png extension.

    Args:
        blob_container_client (ContainerClient): Azure Blob Container client for
            accessing the storage container.
        file_path (str): Path to the file whose corresponding image should be
            downloaded.

    Returns:
        Optional[str]: Base64 encoded data URL of the image with proper PNG mime type,
            or None if the image blob cannot be found or accessed.

    Notes:
        - Converts the file extension to .png when searching for the image
        - Returns data in format: "data:image/png;base64,{encoded_data}"
        - Logs a warning if the blob doesn't exist
    """
    base_name, _ = os.path.splitext(file_path)
    image_filename = base_name + ".png"
    try:
        blob = await blob_container_client.get_blob_client(image_filename).download_blob()
        if not blob.properties:
            logging.warning(f"No blob exists for {image_filename}")
            return None
        img = base64.b64encode(await blob.readall()).decode("utf-8")
        return f"data:image/png;base64,{img}"
    except ResourceNotFoundError:
        logging.warning(f"No blob exists for {image_filename}")
        return None


async def fetch_image(blob_container_client: ContainerClient, result: Document) -> Optional[ImageURL]:
    """
    Fetches and prepares an image for display in the chat interface.

    Attempts to download and convert an image associated with a document result
    to a format suitable for display. The image is identified using the document's
    sourcepage attribute.

    Args:
        blob_container_client (ContainerClient): Azure Blob Container client for
            accessing the storage container.
        result (Document): Document object containing metadata about the associated
            image, particularly the sourcepage attribute.

    Returns:
        Optional[ImageURL]: Dictionary containing the image URL (as base64 data URL)
            and detail level if successful, None if no image is found or accessible.

    Notes:
        - Always sets detail level to "auto" for found images
        - Returns None if sourcepage is not set or image cannot be retrieved
    """
    if result.sourcepage:
        img = await download_blob_as_base64(blob_container_client, result.sourcepage)
        if img:
            return {"url": img, "detail": "auto"}
        else:
            return None
    return None