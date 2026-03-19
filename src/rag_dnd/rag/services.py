"""Module-wide services."""
import logging
from pathlib import Path


logger = logging.getLogger(__name__)

def load_document_text(source_file: Path) -> str:
    """
    Load the text of a text-document.
    
    Args:
        source_file (Path): The path to the document file.
        
    Returns:
        str: The text of the document.
    """
    logger.debug(f"Loading document text: {source_file}")
    with open(source_file, "r") as f:
        return f.read()
