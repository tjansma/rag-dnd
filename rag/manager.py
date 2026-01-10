"""
Manager for coordinating the storage of documents, chunks, and sentences.
"""
import os
from hashlib import sha256
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from config import Config

from .database import get_session, init_db
from .embeddings import Embedding
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
    session.add(document)
    logger.debug(f"Adding chunks to database.")
    session.add_all(chunks)
    session.commit()

    logger.debug(f"Connecting to embeddings model: {config.embeddings_model}")
    embedder = Embedding(config.embeddings_model)
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
    embedder = Embedding(config.embeddings_model)
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
    session.close()
    
    logger.info(f"Retrieved {len(chunks)} relevant chunks.")
    return chunks
