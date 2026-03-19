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

from .database import get_session, init_db
from .embeddings import get_embedding_instance
from .exceptions import DocumentExistsError, DocumentNotFoundError
from .llm import get_llm
from .models import Document, Collection, Chunk, QueryResult
from .store import get_vector_store
from .chunker import Chunker

logger = logging.getLogger(__name__)


def ensure_collection(collection_name, campaign_id) -> Collection:
    """
    Ensure a collection exists.
    
    Args:
        collection_name (str): The name of the collection.
        campaign_id (int): The id of the campaign to which the collection belongs.
                
    Returns:
        Collection: The collection.
    """
    logger.debug(f"Ensuring collection: {collection_name}")
    with get_session() as session:
        collection = session.query(Collection).filter_by(name=collection_name).first()
        logger.debug(f"Collection {collection_name} found: {collection is not None}")
        if collection is None:
            logger.debug(f"Collection {collection_name} does not exist. Creating...")
            collection = Collection(name=collection_name, campaign_id=campaign_id)
            session.add(collection)
            session.commit()
            logger.debug(f"Collection {collection_name} created.")
        session.expunge_all()
        logger.debug(f"Collection {collection_name} returned.")
    return collection


def get_collection(session: Session, collection_name: str) -> Collection:
    """
    Get a collection.
    
    Args:
        session (Session): The database session.
        collection_name (str): The name of the collection.
        
    Returns:
        Collection: The collection.

    Raises:
        ValueError: If the collection does not exist.
    """
    logger.debug(f"Getting collection: {collection_name}")
    collection = session.query(Collection).filter_by(name=collection_name).first()
    if collection is None:
        raise ValueError(f"Collection '{collection_name}' not found.")
    return collection


def _store_impl(session: Session, file: Path, config: Config,
                custom_filename: str, collection: Collection) -> None:
    """Internal: store a document using an existing session.

    Handles SQLite persistence, embedding, and ChromaDB indexing.
    The caller is responsible for session lifecycle management.

    Args:
        session (Session): An active database session.
        file (Path): The path to the document.
        config (Config): The configuration.
        custom_filename (str): The identifier used in the database.

    Raises:
        DocumentExistsError: If the document already exists in the database.
    """
    # Calculate SHA256 hash to detect changes and avoid duplicate processing
    with open(file, "rb") as f:
        file_hash = sha256(f.read()).hexdigest()

    # Create the Document object.
    # Important: 'custom_filename' is the persistent identifier in the DB,
    # even if 'filename' is a temporary uploaded file path.
    document = Document(file_hash=file_hash,
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
        session.add(document)
        session.add_all(chunks)
        session.commit()
        session.expunge_all()
    except DatabaseError as e:
        logger.error(f"Error adding '{file.name}' to database: {e}")
        session.rollback()
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


def store_document(collection: Collection,
                   file: Path,
                   session: Session,
                   custom_filename: str | None = None,
                   config: Config | None = None) -> None:
    """Store a document in the database.

    Args:
        collection (Collection): The collection to store the document in.
        file (Path): The path to the document.
        session (Session): The database session.
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

    _store_impl(session, file, config, custom_filename, collection)


def query(query: str, 
          collection: Collection,
          session: Session,
          limit: int = 5,
          config: Config | None = None) -> list[QueryResult]:
    """
    Query the vector store.
    
    Args:
        query (str): The query to perform.
        collection (Collection): The collection to query.
        session (Session): The database session.
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
    chunks = session.query(Chunk)\
        .options(joinedload(Chunk.parent_document))\
        .filter(Chunk.id.in_(relevant_chunk_ids))\
        .all()
    
    logger.info(f"Retrieved {len(chunks)} relevant chunks.")

    # Convert internal Chunk objects to cleaner QueryResult objects
    for chunk in chunks:
        results.append(
            QueryResult(
                text=chunk.text, 
                source_document=chunk.parent_document.custom_filename
            )
        )

    return results

def _delete_impl(session: Session, custom_filename: str,
                 config: Config, collection: Collection) -> None:
    """Internal: delete a document using an existing session.

    Handles ChromaDB cleanup and SQLite deletion.
    The caller is responsible for session lifecycle management.

    Args:
        session (Session): An active database session.
        custom_filename (str): The identifier used in the database.
        config (Config): The configuration.

    Raises:
        DocumentNotFoundError: If the document does not exist in the database.
    """
    # Query the document by custom_filename
    document = session.query(Document).filter_by(custom_filename=custom_filename).first()
    if document is None:
        logger.error(f"Delete failed: Document {custom_filename} not found in DB.")
        raise DocumentNotFoundError(f"Delete failed: Document {custom_filename} not found in DB.")

    # 1. Clean up Vector Store (Child) first
    vector_store = get_vector_store(collection.name, config)
    chunk_ids = tuple(chunk.id for chunk in document.chunks)
    vector_store.delete_chunks_by_id(chunk_ids)

    # 2. Clean up SQLite (Parent)
    # Chunks in SQLite are automatically deleted via cascade="all, delete-orphan"
    try:
        logger.debug(f"Deleting document: {document}")
        session.delete(document)
        session.commit()
    except DatabaseError as e:
        logger.error(f"Error deleting document: {e}")
        session.rollback()
        raise

    # 3. Rebuild Vector Store BM25 index
    logger.debug(f"Rebuilding Vector Store BM25 index.")
    vector_store.rebuild_bm25_index()
    logger.info(f"Deleted document: {custom_filename}")


def delete_document(collection: Collection,
                    filename: str,
                    session: Session,
                    custom_filename: str | None = None,
                    config: Config | None = None) -> None:
    """Delete a document from the database.

    Public API that manages its own session. For internal use with a shared
    session, see _delete_impl.

    Args:
        collection (Collection): The collection to delete the document from.
        filename (str): The path to the document.
        session (Session): The database session.
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

    _delete_impl(session, custom_filename, config, collection)


def update_document(collection: Collection,
                    file: Path,
                    session: Session,
                    custom_filename: str | None = None,
                    config: Config | None = None) -> None:
    """Update a document in the database.

    Performs a full delete-and-replace cycle using a single shared session.
    If the file content has not changed (same SHA256 hash), this is a no-op.

    Args:
        collection (Collection): The collection to update the document in.
        file (Path): The path to the document.
        session (Session): The database session.
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
    document = session.query(Document).filter_by(custom_filename=custom_filename).first()
    if document is None:
        logger.error(f"Document {custom_filename} not found in database.")
        raise DocumentNotFoundError(f"Document {custom_filename} not found in database.")

    # Calculate file hash to check if the file has changed
    with open(file, "rb") as f:
        file_hash = sha256(f.read()).hexdigest()

    # Check if the file has changed
    if document.file_hash == file_hash:
        logger.warning(f"Document {custom_filename} is already up to date.")
        return

    # Perform a full "Delete & Replace" cycle using the shared session
    logger.debug(f"Deleting document: {custom_filename}")
    _delete_impl(session, custom_filename, config, collection)

    logger.debug(f"Storing document: {custom_filename}")
    _store_impl(session, file, config, custom_filename, collection)

    logger.info(f"Updated document: {custom_filename}")

def prompt_llm(prompt: list[dict],
               config: Config | None = None) -> str:
    """
    Prompt the LLM.
    
    Args:
        prompt (list[dict]): The prompt to send to the LLM.
        config (Config): The configuration to use.
        
    Returns:
        str: The response from the LLM.
    """
    if config is None:
        config = Config.load()

    logger.debug(f"Prompting LLM with: {prompt}")
    # Get the LLM instance for the query expansion model
    llm = get_llm(config.query_expansion_model, config.query_expansion_device)
    # Apply the chat template to the prompt to expand it
    text = llm.tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
    # Generate the response from the expanded prompt
    return llm.generate(text)

def expand_query(query_to_expand: str,
                 extra_context: str,
                 config: Config | None = None) -> str:
    """
    Expand a query using the LLM.
    
    Args:
        query_to_expand (str): The query to expand.
        extra_context (str): The extra context to use.
        config (Config): The configuration to use.
        
    Returns:
        str: The expanded query.
    """
    if config is None:
        config = Config.load()
    # Read the system prompt for the query expansion model
    with open(config.query_expansion_system_prompt, "r") as f:
        system_prompt = f.read()
    # Create the user prompt and include the extra context and query to expand
    user_prompt = f"""<context>
    {extra_context}
    </context>

    <query>
    {query_to_expand}
    </query>"""

    logger.debug(f"Expanding query: {query_to_expand}")
    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    # Prompt the LLM with the expanded query
    return prompt_llm(prompt, config)
