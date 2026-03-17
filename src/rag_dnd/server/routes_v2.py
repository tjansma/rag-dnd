"""FastAPI routes for API requests."""
import logging

from fastapi import APIRouter, UploadFile, HTTPException

from .. import rag
from .upload import temporary_upload

logger = logging.getLogger(__name__)

router_v2 = APIRouter(prefix="/v2")

@router_v2.put("/document", status_code=200)
def update_document(file: UploadFile, campaign_short_name: str, collection_name: str | None = None):
    """
    Store or update a document in the database.
    
    Args:
        file (UploadFile): The file to update.
        campaign_short_name (str): The short name of the campaign to update
                                   the document in.
        collection_name (str | None): The name of the collection to update
                                     the document in.
    """
    try:
        campaign = rag.Campaign.from_db_by_short_name(campaign_short_name)
    except ValueError as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=404, detail="Campaign not found")

    if collection_name is None:
        collection_name = campaign.metadata.get_default_collection_name()

    logger.debug(f"Updating document: {file.filename} in collection: {collection_name}")

    # Receive the file
    logger.debug(f"Updating document in database: {file.filename}")
    try:
        with temporary_upload(file) as file_path:
            try:
                campaign.store_document(file_path, 
                                        custom_filename=file.filename, 
                                        collection_name=collection_name)
            except FileNotFoundError as e:
                logger.error(f"Error updating document in database: {e}")
                raise HTTPException(status_code=404, detail="Document does not exist on file system")
    except OSError as e:
        logger.error(f"Error updating document in database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"Document updated in database: {file.filename}")
