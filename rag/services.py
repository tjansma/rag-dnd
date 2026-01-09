from sqlalchemy.orm import Session

from .models import Document, Collection

def load_document_text(document: Document) -> str:
    """Load the text of a text-document."""
    with open(document.file_name, "r") as f:
        return f.read()
