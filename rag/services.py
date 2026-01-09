from sqlalchemy.orm import Session

from .models import Document, Collection

def load_document_text(document: Document) -> str:
    """Load the text of a text-document."""
    with open(document.file_name, "r") as f:
        return f.read()


def ensure_collection(session: Session, collection_name: str) -> Collection:
    """Ensure a collection exists."""
    collection = session.query(Collection).filter_by(name=collection_name).first()
    if collection is None:
        collection = Collection(name=collection_name)
        session.add(collection)
        session.commit()
    return collection
