"""Coordinating the storage of documents, chunks, and sentences."""
import logging

import chromadb

from config import Config
from .embeddings import Embedding
from .models import Chunk

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for chunks."""
    def __init__(self, config: Config) -> None:
        """
        Initialize the vector store.
        
        Args:
            config (Config): The configuration.
            
        Returns:
            None
        """
        self.config = config

        logger.info(f"Initializing ChromaDB client for: {config.vector_database}")
        self.client = chromadb.PersistentClient(config.vector_database,
                                                settings=chromadb.Settings(
                                                    anonymized_telemetry=False))

        logger.debug(f"Initializing collection: {config.collection_name}")
        self.collection = self.client.get_or_create_collection(name=config.collection_name)

    def add_chunk(self, chunk: Chunk) -> None:
        """
        Add a chunk to the vector store.
        
        Args:
            chunk (Chunk): The chunk to add.
            
        Returns:
            None
        """
        logger.info(f"Adding chunk: {chunk.id}")
        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for index, sentence in enumerate(chunk.sentences):
            logger.debug(f"\tAdding sentence {index}: {sentence.text}")
            if not sentence.stored:
                if sentence.embedding_vector is None:
                    raise ValueError("Sentence embedding vector is None.")
                
                ids.append(f"{chunk.id}_{index}")
                texts.append(sentence.text)
                metadatas.append({"chunk_id": chunk.id})
                embeddings.append(sentence.embedding_vector)    # type: ignore

        logger.debug(f"Adding {len(ids)} sentences to vector store.")
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

        logger.debug(f"Marking {len(ids)} sentences as stored.")
        for sentence in chunk.sentences:
            sentence.stored = True

    def query_chunk_ids(self, query_embedding: list[float], k: int = 5) -> tuple[int, ...]:
        """
        Query the vector store.
        
        Args:
            query_embedding (list[float]): The query embedding.
            k (int): The number of results to return.
            
        Returns:
            tuple[int, ...]: The relevant chunk ids.
        """
        logger.info(f"Querying vector store for {k} results.")
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k
        )
        logger.debug(f"Query results: {results}")

        # TODO Retrieve the relevant chunks from the results
        metadatas = results["metadatas"]
        if not metadatas:
            return tuple(())
        relevant_chunk_ids = []
        for metadata in metadatas:
            for chunk_id in metadata:
                relevant_chunk_ids.append(chunk_id["chunk_id"])
        
        logger.debug(f"Relevant chunk ids: {relevant_chunk_ids}")
        return tuple(set(relevant_chunk_ids))

    def delete_chunks_by_id(self, chunk_ids: tuple[int, ...]):
        """
        Delete chunks from the vector store.
        
        Args:
            chunk_ids (tuple[int, ...]): The ids of the chunks to delete.
            
        Returns:
            None
        """
        logger.debug(f"Deleting chunks: {chunk_ids}")
        for chunk_id in chunk_ids:
            logger.debug(f"\tDeleting chunk: {chunk_id}")
            self.collection.delete(
                where={"chunk_id": chunk_id}
            )
        logger.info(f"Deleted embeddings for {len(chunk_ids)} chunks.")
