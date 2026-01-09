"""Coordinating the storage of documents, chunks, and sentences."""
import chromadb

from config import Config

from .models import Chunk

class VectorStore:
    """Vector store for chunks."""
    def __init__(self, config: Config) -> None:
        """
        Initialize the vector store.
        
        Args:
            config (Config): The configuration.
        """
        self.config = config

        self.client = chromadb.PersistentClient(config.vector_database)
        self.collection = self.client.get_or_create_collection(name=config.collection_name)

    def add_chunk(self, chunk: Chunk) -> None:
        """Add a chunk to the vector store."""
        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for index, sentence in enumerate(chunk.sentences):
            if not sentence.stored:
                if sentence.embedding_vector is None:
                    raise ValueError("Sentence embedding vector is None.")
                
                ids.append(f"{chunk.id}_{index}")
                texts.append(sentence.text)
                metadatas.append({"chunk_id": chunk.id})
                embeddings.append(sentence.embedding_vector)    # type: ignore

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )

        for sentence in chunk.sentences:
            sentence.stored = True
