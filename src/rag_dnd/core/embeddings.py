"""
Embeddings for markdown text.
"""
import logging
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings
import torch

from ..config import Config

from .models import Chunk

logger = logging.getLogger(__name__)

embedding_instance = None

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

        if model_name is None:
            logger.debug("No model name provided, using default from config")
            model_name = config.embeddings_model
        logger.debug(f"Initializing embeddings with model: {model_name}")

        self.embedding_provider = config.embeddings_provider
        self.embedding_model = model_name
        
        # Set device and validate availability
        if config.embedding_device == "cuda":
            logger.debug("Requested GPU for embeddings")
            if torch.cuda.is_available():
                logger.debug("GPU available for embeddings")
                self.embedding_device = "cuda"
            else:
                logger.debug("GPU not available for embeddings, using CPU")
                self.embedding_device = "cpu"
        else:
            logger.debug("Requested CPU for embeddings")
            self.embedding_device = "cpu"
        logger.info(f"Using device: {self.embedding_device}")
        
        model_kwargs: dict[str, Any] = {}
        encode_kwargs: dict[str, Any] = {}
        self.passage_prefix = ""
        self.query_prefix = ""
        if "e5" in self.embedding_model.lower():
            self.passage_prefix = "passage: "
            self.query_prefix = "query: "
            model_kwargs["device"] = self.embedding_device
            encode_kwargs["normalize_embeddings"] = True
        elif "jina" in self.embedding_model.lower():
            model_kwargs["device"] = self.embedding_device
            model_kwargs["trust_remote_code"] = True
            encode_kwargs["normalize_embeddings"] = True
        else:
            logger.error(f"Unknown embedding model: {self.embedding_model}")
            raise ValueError(f"Unknown embedding model: {self.embedding_model}")
        logger.info(f"Using model: {self.embedding_model}, {model_kwargs=}, {encode_kwargs=}")

        if self.embedding_provider == "HuggingFace":
            try:
                self.embedding = HuggingFaceEmbeddings(
                    model_name=self.embedding_model,
                    model_kwargs=model_kwargs,
                    encode_kwargs=encode_kwargs)
                logger.info(f"Initialized embeddings with model: {self.embedding_model}")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
                raise
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
            texts = [self.passage_prefix + "\n".join([chunk.sentences[0].text, chunk.sentences[1].text])]
            for i in range(1, len(chunk.sentences) - 1):
                texts.append(self.passage_prefix + "\n".join([chunk.sentences[i-1].text, chunk.sentences[i].text, chunk.sentences[i+1].text]))
            texts.append(self.passage_prefix + "\n".join([chunk.sentences[-2].text, chunk.sentences[-1].text]))
        else:
            texts = [self.passage_prefix + chunk.sentences[0].text]
        
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
        logger.debug(f"Invoking embedding for query: '{self.query_prefix}{query}'")
        return self.embedding.embed_query(f"{self.query_prefix}{query}")


def get_embedding_instance() -> Embedding:
    """
    Get the default embedding instance as specified in the config.
    
    Returns:
        Embedding: The embedding instance.
    """
    global embedding_instance
    logger.debug("Getting embedding instance")
    if embedding_instance is None:
        logger.debug("Initializing embedding instance")
        try:
            embedding_instance = Embedding()
        except Exception as e:
            logger.error(f"Failed to initialize embedding instance: {e}")
            raise
    else:
        logger.debug("Using existing embedding instance")
    return embedding_instance
