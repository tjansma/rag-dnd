"""
Manager for coordinating the storage of documents, chunks, and sentences.
"""
import os
from hashlib import sha256
import logging

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
    # Check if the collection already exists in the local database
    collection = session.query(Collection).filter_by(name=collection_name).first()
    
    if collection is None:
        # If not, create a new collection entry
        logger.debug(f"Collection {collection_name} does not exist. Creating...")
        collection = Collection(name=collection_name)
        session.add(collection)
        session.commit()

    return collection


def store_document(filename: str, custom_filename: str | None = None, 
                   config: Config | None = None) -> None:
    """
    Store a document in the database.
    
    Args:
        filename (str): The path to the document.
        custom_filename (str | None): The custom filename to use.
        config (Config): The configuration.

    Raises:
        FileNotFoundError: If the source file does not exist.
        DocumentExistsError: If the document already exists in the database.
        DatabaseError: If any other database error occurs.
    """
    if config is None:
        config = Config.load()

    logger.info(f"Storing document: {filename}")
    # Check if the source file exists
    if not os.path.exists(filename):
        logger.error(f"File {filename} not found.")
        raise FileNotFoundError(f"File {filename} not found.")
    
    # If no custom filename is provided, use the filename from the source file
    if custom_filename is None:
        custom_filename = os.path.basename(filename)
    
    # Calculate SHA256 hash to detect changes and avoid duplicate processing
    file_hash = sha256(open(filename).read().encode()).hexdigest()
    
    # Initialize DB connection and ensure the target collection exists
    init_db()
    session = get_session()
    collection = ensure_collection(session, config.collection_name)
    
    # Create the Document object. 
    # Important: 'custom_filename' is the persistent identifier in the DB, 
    # even if 'filename' is a temporary uploaded file path.
    document = Document(file_name=filename, file_hash=file_hash, custom_filename=custom_filename, collection_id=collection.id)

    # Chunk the document
    logger.debug(f"Chunking document with strategy: heading2")
    chunker = Chunker(strategy="heading2")
    chunks = chunker.chunk(document)
    logger.debug(f"Chunked document into {len(chunks)} chunks.")

    # Add the document and chunks to the database
    logger.debug(f"Adding document to database.")
    try:
        # Add the parent document first
        session.add(document)

        # Add all generated chunks (children)
        logger.debug(f"Adding chunks to database.")
        session.add_all(chunks)
        
        # Commit transaction to persist Parent (Document) and Children (Chunks) in SQLite
        session.commit()
    except DatabaseError as e:
        logger.error(f"Error adding '{filename}' to database: {e}")
        session.rollback()
        raise DocumentExistsError(f"Document '{filename}' already exists.")

    # Connect to embeddings model and vector store
    logger.debug(f"Connecting to embeddings model: {config.embeddings_model}")
    embedder = get_embedding_instance()
    logger.debug(f"Connecting to vector store: {config.vector_database}")
    vector_store = get_vector_store(config)

    logger.debug(f"Adding chunks to vector store: {config.vector_database}.")
    for chunk in chunks:
        # Embed each chunk (calculate vector) using the configured model
        logger.debug(f"Embedding chunk: {chunk.id}")
        embedder.embed(chunk)
        
        # Add the chunk with its embedding to the Vector Store (ChromaDB)
        logger.debug(f"Adding chunk to vector store: {chunk.id}")
        vector_store.add_chunk(chunk)
    
    # Rebuild Vector Store BM25 index
    logger.debug(f"Rebuilding Vector Store BM25 index.")
    vector_store.rebuild_bm25_index()

    # Close the session after all operations are complete
    session.close()
    logger.info(f"Stored document: {filename} with {len(chunks)} chunks.")

def query(query: str,
          limit: int = 5,
          config: Config | None = None) -> list[QueryResult]:
    """
    Query the vector store.
    
    Args:
        query (str): The query to perform.
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
    vector_store = get_vector_store(config)
    logger.debug(f"Querying vector store for relevant chunks.")
    relevant_chunk_ids = vector_store.hybrid_search(query, query_embedding, limit)

    # 3. Retrieve the relevant chunks
    # We query the SQLite DB to get the full text content for the IDs returned by the Vector Store
    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Retrieving relevant chunks from database: {config.content_database_url}")
    session = get_session()
    chunks = session.query(Chunk)\
        .options(joinedload(Chunk.parent_document))\
        .filter(Chunk.id.in_(relevant_chunk_ids))\
        .all()
    
    # Detach objects from session so they can be used after session.close()
    session.expunge_all()
    
    logger.info(f"Retrieved {len(chunks)} relevant chunks.")

    # Convert internal Chunk objects to cleaner QueryResult objects
    results = []
    for chunk in chunks:
        results.append(
            QueryResult(
                text=chunk.text, 
                source_document=chunk.parent_document.file_name
            )
        )
    return results

def delete_document(filename: str,
                    custom_filename: str | None = None,
                    config: Config | None = None) -> None:
    """
    Delete a document from the database.
    
    Args:
        filename (str): The path to the document.
        custom_filename (str | None): The custom filename to use.
        config (Config): The configuration to use.

    Raises:
        DocumentNotFoundError: If the document does not exist in the database.
    """
    if config is None:
        config = Config.load()

    logger.info(f"Deleting document: {custom_filename}")
    # If no custom filename is provided, use the filename from the source file
    if custom_filename is None:
        custom_filename = os.path.basename(filename)
    
    # Connect to SQLite database
    session = get_session()
    
    # Query the document by custom_filename
    document = session.query(Document).filter_by(custom_filename=custom_filename).first()
    if document is None:
        logger.error(f"Delete failed: Document {custom_filename} not found in DB.")
        raise DocumentNotFoundError(f"Delete failed: Document {custom_filename} not found in DB.")
    
    # Connect to vector store
    vector_store = get_vector_store(config)
    
    # 1. Clean up Vector Store (Child) first
    # We retrieve all Chunk IDs associated with this Document from SQLite
    chunk_ids = tuple(chunk.id for chunk in document.chunks)
    
    # Then we delete these specific chunks from the Vector Store/ChromaDB
    # This ensures no orphaned vectors remain after the SQLite deletion
    vector_store.delete_chunks_by_id(chunk_ids)

    # 2. Clean up SQLite (Parent)
    # INFO: Chunks in SQLite are automatically deleted via
    # 'cascade="all, delete-orphan"' 
    # configured in the SQL Alchemy model when the parent Document is deleted.
    logger.debug(f"Deleting document: {document}")
    session.delete(document)
    session.commit()
    session.close()
    logger.info(f"Deleted document: {custom_filename}")

    # 3. Rebuild Vector Store BM25 index
    logger.debug(f"Rebuilding Vector Store BM25 index.")
    vector_store.rebuild_bm25_index()


def update_document(filename: str,
                    custom_filename: str | None = None,
                    config: Config | None = None) -> None:
    """
    Update a document in the database.
    
    Args:
        filename (str): The path to the document.
        custom_filename (str | None): The custom filename to use.
        config (Config): The configuration to use.

    Raises:
        FileNotFoundError: If the source file does not exist.
        DocumentNotFoundError: If the document does not exist in the database.
    """
    if config is None:
        config = Config.load()

    logger.info(f"Updating document: {filename}")
    # Check if source file exists
    if not os.path.exists(filename):
        logger.error(f"Update failed: File {filename} not found on server FS.")
        raise FileNotFoundError(f"Update failed: File {filename} not found on server FS.")
    
    # If no custom filename is provided, use the filename from the source file
    if custom_filename is None:
        custom_filename = os.path.basename(filename)
    
    # Calculate file hash, to check if the file has changed
    file_hash = sha256(open(filename).read().encode()).hexdigest()
    
    # Connect to SQLite database
    session = get_session()
    
    # Query the document by custom_filename
    document = session.query(Document).filter_by(custom_filename=custom_filename).first()
    if document is None:
        logger.error(f"Document {filename} not found in database.")
        raise DocumentNotFoundError(f"Document {filename} not found in database.")
    
    # Check if the file has changed
    if document.file_hash == file_hash:
        # If the file has not changed, do nothing
        logger.warning(f"Document {filename} is already up to date.")
        return
    
    # Close the read-only session before starting write operations
    session.close()

    # Perform a full "Delete & Replace" cycle
    # This is safer than partial updates as it ensures no stale chunks or vectors remain
    # if the document content has changed significantly.
    logger.debug(f"Deleting document: {filename}")
    delete_document(filename, custom_filename=custom_filename, config=config)
    
    logger.debug(f"Storing document: {filename}")
    store_document(filename, custom_filename=custom_filename, config=config)

    logger.info(f"Updated document: {filename}")

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
    system_prompt = open(config.query_expansion_system_prompt).read()
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
