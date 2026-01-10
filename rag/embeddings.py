"""
Embeddings for markdown text.
"""
import logging

from langchain_huggingface import HuggingFaceEmbeddings

from config import Config

from . import Chunk

logger = logging.getLogger(__name__)

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
        logger.debug(f"Initializing embeddings with model: {model_name}")

        self.embedding_provider = config.embeddings_provider
        self.embedding_model = model_name or config.embeddings_model
        
        if self.embedding_provider == "HuggingFace":
            self.embedding = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={"device": None},
                encode_kwargs={"normalize_embeddings": True})
            logger.info(f"Initialized embeddings with model: {self.embedding_model}")
        else:
            logger.error(f"Unknown embedding provider: {self.embedding_provider}")
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
        logger.debug(f"Embedding chunk: {chunk.id} - Sentences count: {len(chunk.sentences)}")
        # 1. Gather texts, with a sliding window of 3 sentences.
        if len(chunk.sentences) > 1:
            texts = ["passage: " + "\n".join([chunk.sentences[0].text, chunk.sentences[1].text])]
            for i in range(1, len(chunk.sentences) - 1):
                texts.append("passage: " + "\n".join([chunk.sentences[i-1].text, chunk.sentences[i].text, chunk.sentences[i+1].text]))
            texts.append("passage: " + "\n".join([chunk.sentences[-2].text, chunk.sentences[-1].text]))
        else:
            texts = ["passage: " + chunk.sentences[0].text]
        
        # 2. Batch embedding (Much faster!)
        logger.debug(f"Embedding {len(texts)} texts.")
        embeddings = self.embedding.embed_documents(texts)
        
        # 3. Assign results
        logger.debug(f"Assigning results to chunk: {chunk.id}")
        for i, sentence in enumerate(chunk.sentences):
            sentence.embedding_vector = embeddings[i]

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a query.
        
        Args:
            query (str): The query to embed.
            
        Returns:
            list[float]: The embedding of the query.
        """
        logger.debug(f"Invoking embedding for query: 'query: {query}'")
        return self.embedding.embed_query(f"query: {query}")
