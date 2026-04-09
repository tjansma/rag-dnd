"""
Manager for coordinating the storage of documents, chunks, and sentences.
"""
import os
from hashlib import sha256
import logging
from pathlib import Path

from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, joinedload

from ..config import Config
from ..shared import DocumentExistsError, QueryResult

from .embeddings import get_embedding_instance
from .llm import get_llm
from .models import RAGDocument, Collection, Chunk
from .store import get_vector_store
from .chunker import Chunker

logger = logging.getLogger(__name__)


def ensure_collection(database_session: Session,
                      collection_name: str,
                      campaign_id: int) -> Collection:
    """
    Ensure a collection exists.
    
    Args:
        database_session (Session): The database session.
        collection_name (str): The name of the collection.
        campaign_id (int): The id of the campaign to which the collection belongs.
                
    Returns:
        Collection: The collection.
    """
    logger.debug(f"Ensuring collection: {collection_name}")
    collection = database_session.query(Collection).filter_by(name=collection_name).first()
    logger.debug(f"Collection {collection_name} found: {collection is not None}")
    if collection is None:
        logger.debug(f"Collection {collection_name} does not exist. Creating...")
        collection = Collection(name=collection_name, campaign_id=campaign_id)
        database_session.add(collection)
        database_session.flush()
        logger.debug(f"Collection {collection_name} created.")
    logger.debug(f"Collection {collection_name} returned.")
    return collection


def get_collection(database_session: Session,
                   collection_name: str) -> Collection:
    """
    Get a collection.
    
    Args:
        database_session (Session): The database session.
        collection_name (str): The name of the collection.
        
    Returns:
        Collection: The collection.

    Raises:
        ValueError: If the collection does not exist.
    """
    logger.debug(f"Getting collection: {collection_name}")
    collection = database_session.query(Collection).filter_by(name=collection_name).first()
    if collection is None:
        raise ValueError(f"Collection '{collection_name}' not found.")
    return collection


def store_document(collection: Collection,
                   file: Path,
                   database_session: Session,
                   custom_filename: str | None = None,
                   config: Config | None = None) -> None:
    """Store a document in the database.

    Args:
        collection (Collection): The collection to store the document in.
        file (Path): The path to the document.
        database_session (Session): The database session.
        custom_filename (str | None): The custom filename to use.
        config (Config): The configuration.

    Raises:
        FileNotFoundError: If the source file does not exist.
        DocumentExistsError: If the document already exists in the database.
    """
    logger.info(f"manager.store_document: Storing document: {file}")
    if not file.exists():
        logger.error(f"manager.store_document: File {file} not found.")
        raise FileNotFoundError(f"File {file} not found.")

    if config is None:
        config = Config.load()

    if custom_filename is None:
        custom_filename = file.name

    # Calculate SHA256 hash to detect changes and avoid duplicate processing
    with open(file, "rb") as f:
        file_hash = sha256(f.read()).hexdigest()

    # Create the Document object.
    # Important: 'custom_filename' is the persistent identifier in the DB,
    # even if 'filename' is a temporary uploaded file path.
    document = RAGDocument(file_hash=file_hash,
                        custom_filename=custom_filename,
                        collection_id=collection.id)

    # Chunk the document
    logger.debug(f"Chunking document with strategy: heading2")
    chunker = Chunker(strategy="heading2")
    chunks = chunker.chunk(document, file)
    logger.debug(f"Chunked document into {len(chunks)} chunks.")

    # Add the document and chunks to the database
    logger.debug(f"Adding document to database.")
    try:
        database_session.add(document)
        database_session.add_all(chunks)
        database_session.flush()
    except DatabaseError as e:
        logger.error(f"Error adding '{file.name}' to database: {e}")
        raise DocumentExistsError(f"Document '{file.name}' already exists.")

    # ChromaDB operations (outside session — SQLite is source of truth)
    logger.debug(f"Connecting to embeddings model: {config.embeddings_model}")
    embedder = get_embedding_instance()
    logger.debug(f"Connecting to vector store: {config.vector_database}")
    vector_store = get_vector_store(collection.name,config)

    logger.debug(f"Adding chunks to vector store: {config.vector_database}.")
    for chunk in chunks:
        logger.debug(f"Embedding chunk: {chunk.id}")
        embedder.embed(chunk)
        logger.debug(f"Adding chunk to vector store: {chunk.id}")
        vector_store.add_chunk(chunk)

    # Rebuild Vector Store BM25 index
    logger.debug(f"Rebuilding Vector Store BM25 index.")
    vector_store.rebuild_bm25_index()
    logger.info(f"Stored document: {file.name} with {len(chunks)} chunks.")


def query(query: str, 
          collection: Collection,
          database_session: Session,
          limit: int = 5,
          config: Config | None = None) -> list[QueryResult]:
    """
    Query the vector store.
    
    Args:
        query (str): The query to perform.
        collection (Collection): The collection to query.
        database_session (Session): The database session.
        limit (int): The number of chunks to return. Defaults to 5.
        config (Config): The configuration to use. Defaults to Config.load().
        
    Returns:
        list[QueryResult]: The relevant chunks.
    """
    if config is None:
        config = Config.load()

    logger.info(f"Querying vector store for: {query}")
    # 1. Embed the query
    logger.debug(f"Connecting to embeddings model: {config.embeddings_model}")
    embedder = get_embedding_instance()
    logger.debug(f"Embedding query: {query}")
    query_embedding = embedder.embed_query(query)

    # 2. Query the vector store
    logger.debug(f"Connecting to vector store: {config.vector_database}")
    vector_store = get_vector_store(collection.name, config)
    logger.debug(f"Querying vector store for relevant chunks.")
    relevant_chunk_ids = vector_store.hybrid_search(query, query_embedding, limit)

    # 3. Retrieve the relevant chunks
    # We query the SQLite DB to get the full text content for the IDs returned by the Vector Store
    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Retrieving relevant chunks from database: {config.content_database_url}")
    results = []
    chunks = database_session.query(Chunk)\
        .options(joinedload(Chunk.parent_rag_document))\
        .filter(Chunk.id.in_(relevant_chunk_ids))\
        .all()
    chunks.sort(key=lambda c: relevant_chunk_ids.index(c.id))    
    logger.info(f"Retrieved {len(chunks)} relevant chunks.")


    # Convert internal Chunk objects to cleaner QueryResult objects
    for chunk in chunks:
        results.append(
            QueryResult(
                text=chunk.text, 
                source_document=chunk.parent_rag_document.custom_filename
            )
        )

    return results


def delete_document(collection: Collection,
                    filename: str,
                    database_session: Session,
                    custom_filename: str | None = None,
                    config: Config | None = None) -> None:
    """Delete a document from the database.

    Public API that manages its own session. For internal use with a shared
    session, see _delete_impl.

    Args:
        collection (Collection): The collection to delete the document from.
        filename (str): The path to the document.
        database_session (Session): The database session.
        custom_filename (str | None): The custom filename to use.
        config (Config): The configuration to use.

    Raises:
        DocumentNotFoundError: If the document does not exist in the database.
    """
    if config is None:
        config = Config.load()

    logger.info(f"Deleting document: {custom_filename}")
    if custom_filename is None:
        custom_filename = os.path.basename(filename)

    # Query the document by custom_filename
    document = RAGDocument.load_by_custom_filename(custom_filename,
                                                collection.id,
                                                database_session)

    # 1. Clean up Vector Store (Child) first
    vector_store = get_vector_store(collection.name, config)
    chunk_ids = tuple(chunk.id for chunk in document.chunks)
    vector_store.delete_chunks_by_id(chunk_ids)

    # 2. Clean up SQLite (Parent)
    # Chunks in SQLite are automatically deleted via cascade="all, delete-orphan"
    try:
        logger.debug(f"Deleting document: {document}")
        database_session.delete(document)
        database_session.flush()
    except DatabaseError as e:
        logger.error(f"Error deleting document: {e}")
        raise

    # 3. Rebuild Vector Store BM25 index
    logger.debug(f"Rebuilding Vector Store BM25 index.")
    vector_store.rebuild_bm25_index()
    logger.info(f"Deleted document: {custom_filename}")


def update_document(collection: Collection,
                    file: Path,
                    database_session: Session,
                    custom_filename: str | None = None,
                    config: Config | None = None) -> None:
    """Update a document in the database.

    Performs a full delete-and-replace cycle using a single shared session.
    If the file content has not changed (same SHA256 hash), this is a no-op.

    Args:
        collection (Collection): The collection to update the document in.
        file (Path): The path to the document.
        database_session (Session): The database session.
        custom_filename (str | None): The custom filename to use.
        config (Config): The configuration to use.

    Raises:
        FileNotFoundError: If the source file does not exist.
        DocumentNotFoundError: If the document does not exist in the database.
    """
    if config is None:
        config = Config.load()

    logger.info(f"Updating document: {file}")
    if not file.exists():
        logger.error(f"Update failed: File {file} not found on server FS.")
        raise FileNotFoundError(f"Update failed: File {file} not found on server FS.")

    if custom_filename is None:
        custom_filename = file.name

    # Check if the document exists
    document = RAGDocument.load_by_custom_filename(custom_filename,
                                                collection.id,
                                                database_session)
    
    # Calculate file hash to check if the file has changed
    with open(file, "rb") as f:
        file_hash = sha256(f.read()).hexdigest()

    # Check if the file has changed
    if document.file_hash == file_hash:
        logger.warning(f"Document {custom_filename} is already up to date.")
        return

    # Perform a full "Delete & Replace" cycle using the shared session
    logger.debug(f"Deleting document: {custom_filename}")
    delete_document(collection, custom_filename, database_session, config=config)

    logger.debug(f"Storing document: {custom_filename}")
    store_document(collection, file, database_session, custom_filename, config=config)

    logger.info(f"Updated document: {custom_filename}")
