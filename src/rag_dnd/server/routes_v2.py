"""FastAPI routes for API requests."""
from sqlalchemy.exc import DatabaseError
import logging

from fastapi import APIRouter, UploadFile, HTTPException

from ..config import Config
from .. import core as rag
from .upload import temporary_upload

logger = logging.getLogger(__name__)

router_v2 = APIRouter(prefix="/v2")

@router_v2.post("/document", status_code=201)
def store_document(file: UploadFile, collection: str | None = None):
    """
    Store a document in the database.
    
    Args:
        file (UploadFile): The file to store.
        collection (str | None): The collection to store the document in.
                                 Defaults to None, which uses the default 
                                 collection name from the config.
    """
    config = Config.load()

    # Check if a collection was provided, if not use the default collection name from the config
    if collection is None:
        collection = config.collection_name
    logger.debug(f"Storing document: {file.filename} in collection: {collection}")

    # Receive the file
    try:
        with temporary_upload(file) as file_path:
            try:
                logger.debug(f"Adding document to database: {file.filename}")
                rag.store_document(str(file_path), 
                                   custom_filename=file.filename, 
                                   config=config)
                logger.debug(f"Document added to database successfully: {file.filename}")
            except DatabaseError as e:
                logger.error(f"Error adding document to database: {e}")
                raise HTTPException(status_code=409, detail="Document already exists")
    except OSError as e:
        logger.error(f"Error receiving document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router_v2.put("/document", status_code=200)
def update_document(file: UploadFile, collection: str | None = None):
    """
    Update a document in the database.
    
    Args:
        file (UploadFile): The file to update.
        collection (str | None): The collection to update the document in.
                                 Defaults to None, which uses the default 
                                 collection name from the config.
    """
    config = Config.load()

    # Check if a collection was provided, if not use the default collection name from the config
    if collection is None:
        collection = config.collection_name
    logger.debug(f"Updating document: {file.filename} in collection: {collection}")

    # Receive the file
    logger.debug(f"Updating document in database: {file.filename}")
    try:
        with temporary_upload(file) as file_path:
            try:
                rag.update_document(str(file_path), 
                                    custom_filename=file.filename, 
                                    config=config)
            except FileNotFoundError as e:
                logger.error(f"Error updating document in database: {e}")
                raise HTTPException(status_code=404, detail="Document does not exist")
            except DatabaseError as e:
                logger.error(f"Error updating document in database: {e}")
                raise HTTPException(status_code=500, detail="Unexpected database error")
    except OSError as e:
        logger.error(f"Error updating document in database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"Document updated in database: {file.filename}")
