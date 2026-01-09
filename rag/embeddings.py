"""
Embeddings for markdown text.
"""
from langchain_huggingface import HuggingFaceEmbeddings

from config import Config

from . import Chunk

class Embedding:
    """
    Embeddings for markdown text.
    """
    def __init__(self, model_name: str | None = None,
                 config: Config=Config()) -> None:
        """
        Initialize the Embeddings with a specific strategy.
        
        Args:
            config (Config): The configuration to use for embeddings.
        """
        self._config = config

        self.embedding_provider = config.embeddings_provider
        self.embedding_model = model_name or config.embeddings_model
        
        if self.embedding_provider == "HuggingFace":
            self.embedding = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={"device": None})
        else:
            raise ValueError(
                f"Unknown embedding provider: {self.embedding_provider}")

    def embed(self, chunk: Chunk) -> None:
        """
        Embed a chunk of text and store the embeddings in the chunk.
        
        Args:
            chunk (Chunk): The chunk to embed.
            
        Returns:
            None
        """
        # 1. Verzamel alle teksten
        texts = [s.text for s in chunk.sentences]
        
        # 2. Batch embedding (Veel sneller!)
        embeddings = self.embedding.embed_documents(texts)
        
        # 3. Wijs resultaten toe
        for i, sentence in enumerate(chunk.sentences):
            sentence.embedding_vector = embeddings[i]
