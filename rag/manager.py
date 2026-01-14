"""
Manager for coordinating the storage of documents, chunks, and sentences.
"""
import os
from hashlib import sha256
import logging
from pathlib import Path
from sqlite3 import DatabaseError

from sqlalchemy.orm import Session

from config import Config

from .database import get_session, init_db
from .embeddings import get_embedding_instance
from .models import Document, Collection, Chunk
from .store import VectorStore
from .chunker import Chunker

logger = logging.getLogger(__name__)


def ensure_collection(session: Session, collection_name: str) -> Collection:
    """
    Ensure a collection exists.
    
    Args:
        session (Session): The database session.
        collection_name (str): The name of the collection.
        
    Returns:
        Collection: The collection.
    """
    logger.debug(f"Ensuring collection: {collection_name}")
    collection = session.query(Collection).filter_by(name=collection_name).first()
    if collection is None:
        logger.debug(f"Collection {collection_name} does not exist. Creating...")
        collection = Collection(name=collection_name)
        session.add(collection)
        session.commit()
    return collection


def store_document(filename: str, config: Config=Config()) -> None:
    """
    Store a document in the database.
    
    Args:
        filename (str): The path to the document.
        config (Config): The configuration.
    """
    logger.info(f"Storing document: {filename}")
    if not os.path.exists(filename):
        logger.error(f"File {filename} not found.")
        raise FileNotFoundError(f"File {filename} not found.")
    
    file_hash = sha256(open(filename).read().encode()).hexdigest()
    
    init_db()
    session = get_session()
    collection = ensure_collection(session, config.collection_name)
    document = Document(file_name=filename, file_hash=file_hash, collection_id=collection.id)

    logger.debug(f"Chunking document with strategy: heading2")
    chunker = Chunker(strategy="heading2")
    chunks = chunker.chunk(document)
    logger.debug(f"Chunked document into {len(chunks)} chunks.")

    logger.debug(f"Adding document to database.")
    try:
        session.add(document)

        logger.debug(f"Adding chunks to database.")
        session.add_all(chunks)
        session.commit()
    except Exception as e:
        logger.error(f"Error adding '{filename}' to database: {e}")
        session.rollback()
        raise

    logger.debug(f"Connecting to embeddings model: {config.embeddings_model}")
    embedder = get_embedding_instance()
    logger.debug(f"Connecting to vector store: {config.vector_database}")
    vector_store = VectorStore(config)

    logger.debug(f"Adding chunks to vector store: {config.vector_database}.")
    for chunk in chunks:
        logger.debug(f"Embedding chunk: {chunk.id}")
        embedder.embed(chunk)
        logger.debug(f"Adding chunk to vector store: {chunk.id}")
        vector_store.add_chunk(chunk)
    
    session.close()
    logger.info(f"Stored document: {filename} with {len(chunks)} chunks.")

def query(query: str, config: Config=Config()) -> list[Chunk]:
    """
    Query the vector store.
    
    Args:
        query (str): The query to perform.
        config (Config): The configuration to use.
        
    Returns:
        list[Chunk]: The relevant chunks.
    """
    logger.info(f"Querying vector store for: {query}")
    # 1. Embed the query
    logger.debug(f"Connecting to embeddings model: {config.embeddings_model}")
    embedder = get_embedding_instance()
    logger.debug(f"Embedding query: {query}")
    query_embedding = embedder.embed_query(query)

    # 2. Query the vector store
    logger.debug(f"Connecting to vector store: {config.vector_database}")
    vector_store = VectorStore(config)
    logger.debug(f"Querying vector store for relevant chunks.")
    relevant_chunk_ids = vector_store.query_chunk_ids(query_embedding)

    # 3. Retrieve the relevant chunks
    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Retrieving relevant chunks from database: {config.content_database_url}")
    session = get_session()
    chunks = session.query(Chunk).filter(Chunk.id.in_(relevant_chunk_ids)).all()
    # Detach objects from session so they can be used after close()
    # WARNING: Lazy-loaded relationships (like chunk.parent_document) will FAIL 
    # if accessed after this point. Use joinedload() in the query if needed.
    session.expunge_all()
    session.close()
    
    logger.info(f"Retrieved {len(chunks)} relevant chunks.")
    return chunks

def delete_document(filename: str, config: Config=Config()) -> None:
    """
    Delete a document from the database.
    
    Args:
        filename (str): The path to the document.
        config (Config): The configuration to use.
    """
    logger.info(f"Deleting document: {filename}")
    session = get_session()
    document = session.query(Document).filter_by(file_name=filename).first()
    if document is None:
        logger.error(f"Document {filename} not found.")
        raise FileNotFoundError(f"Document {filename} not found.")

    vector_store = VectorStore(config)
    chunk_ids = tuple(chunk.id for chunk in document.chunks)
    vector_store.delete_chunks_by_id(chunk_ids)

    # INFO: Chunks are deleted by cascade
    logger.debug(f"Deleting document: {document}")
    session.delete(document)
    session.commit()
    session.close()
    logger.info(f"Deleted document: {filename}")


def update_document(filename: str, config: Config=Config()) -> None:
    """
    Update a document in the database.
    
    Args:
        filename (str): The path to the document.
        config (Config): The configuration to use.
    """
    logger.info(f"Updating document: {filename}")
    if not os.path.exists(filename):
        logger.error(f"File {filename} not found.")
        raise FileNotFoundError(f"File {filename} not found.")
    
    file_hash = sha256(open(filename).read().encode()).hexdigest()
    
    session = get_session()
    document = session.query(Document).filter_by(file_name=filename).first()
    if document is None:
        logger.error(f"Document {filename} not found in database.")
        raise FileNotFoundError(f"Document {filename} not found in database.")
    
    if document.file_hash == file_hash:
        logger.warning(f"Document {filename} is already up to date.")
        return
    
    session.close()

    logger.debug(f"Deleting document: {filename}")
    delete_document(filename, config)
    logger.debug(f"Storing document: {filename}")
    store_document(filename, config)

    logger.info(f"Updated document: {filename}")
