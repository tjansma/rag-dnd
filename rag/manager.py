"""
Manager for coordinating the storage of documents, chunks, and sentences.
"""
import os
from hashlib import sha256
from pathlib import Path

from sqlalchemy.orm import Session

from config import Config

from .database import get_session, init_db
from .embeddings import Embedding
from .models import Document, Collection
from .store import VectorStore
from .chunker import Chunker

def ensure_collection(session: Session, collection_name: str) -> Collection:
    """Ensure a collection exists."""
    collection = session.query(Collection).filter_by(name=collection_name).first()
    if collection is None:
        collection = Collection(name=collection_name)
        session.add(collection)
        session.commit()
    return collection


def store_document(filename: str, config: Config=Config()) -> None:
    """
    Store a document in the database.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")
    
    file_hash = sha256(open(filename).read().encode()).hexdigest()
    
    init_db()
    session = get_session()
    collection = ensure_collection(session, config.collection_name)
    document = Document(file_name=filename, file_hash=file_hash, collection_id=collection.id)

    chunker = Chunker(strategy="heading2")
    chunks = chunker.chunk(document)

    session.add(document)
    session.add_all(chunks)
    session.commit()

    embedder = Embedding()
    vector_store = VectorStore(config)

    for chunk in chunks:
        embedder.embed(chunk)
        vector_store.add_chunk(chunk)
    
    session.close()
