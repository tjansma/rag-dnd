"""Module-wide services."""
import logging

from sqlalchemy.orm import Session

from .models import Document, Collection


logger = logging.getLogger(__name__)

def load_document_text(document: Document) -> str:
    """
    Load the text of a text-document.
    
    Args:
        document (Document): The document to load.
        
    Returns:
        str: The text of the document.
    """
    logger.debug(f"Loading document text: {document.file_name}")
    with open(document.file_name, "r") as f:
        return f.read()
