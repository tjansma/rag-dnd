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
                model_kwargs={"device": None},
                encode_kwargs={"normalize_embeddings": True})
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
        # 1. Verzamel alle teksten, met een sliding window met daarin de voor 
        # en na volgende zin.
        if len(chunk.sentences) > 1:
            texts = ["passage: " + "\n".join([chunk.sentences[0].text, chunk.sentences[1].text])]
            for i in range(1, len(chunk.sentences) - 1):
                texts.append("passage: " + "\n".join([chunk.sentences[i-1].text, chunk.sentences[i].text, chunk.sentences[i+1].text]))
            texts.append("passage: " + "\n".join([chunk.sentences[-2].text, chunk.sentences[-1].text]))
        else:
            texts = ["passage: " + chunk.sentences[0].text]
        
        # 2. Batch embedding (Veel sneller!)
        embeddings = self.embedding.embed_documents(texts)
        
        # 3. Wijs resultaten toe
        for i, sentence in enumerate(chunk.sentences):
            sentence.embedding_vector = embeddings[i]
