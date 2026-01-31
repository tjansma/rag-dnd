"""Handle file uploads."""
from contextlib import contextmanager
import logging
import os
from pathlib import Path
import shutil

from typing import Iterator

from fastapi import UploadFile

from ..config import Config

logger = logging.getLogger(__name__)

def receive_file(file: UploadFile) -> Path:
    """
    Receive a file and store it in the upload directory.
    
    Args:
        file (UploadFile): The file to receive.
    
    Returns:
        Path: The path to the uploaded file.
    """
    config = Config()

    # Check if a filename was provided
    if file.filename is None:
        logger.error("No filename provided.")
        raise ValueError("No filename provided.")

    # Create the upload directory if it doesn't exist
    try:
        if not config.upload_dir.exists():
            logger.debug(f"Creating upload directory: {config.upload_dir}")
            config.upload_dir.mkdir(parents=True)
    except Exception as e:
        logger.error(f"Error creating upload directory: {e}")
        raise

    # Copy the file to the upload directory
    try:
        file_path = config.upload_dir / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error(f"Error copying document to upload directory: {e}")
        raise

    logger.debug(f"Document uploaded successfully: {file.filename}")

    return Path(file_path)

@contextmanager
def temporary_upload(file: UploadFile) -> Iterator[Path]:
    """
    Receive a file and store it in the upload directory.
    Erase the file when the context manager is exited.
    
    Args:
        file (UploadFile): The file to receive.
    
    Returns:
        Path: The path to the uploaded file.
    """
    path = receive_file(file)
    try:
        yield path
    finally:
        if path.exists():
            os.remove(path)
