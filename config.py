"""Configuration for the application."""
import os

import dotenv

dotenv.load_dotenv()

class Config:
    def __init__(self):
        """Initialize the configuration."""
        self.session_log: str = os.getenv("RAG_DND_SESSION_LOG") or \
            "data/session_log.txt"
        self.listen_ip: str = os.getenv("RAG_DND_LISTEN_IP") or "127.0.0.1"
        self.listen_port: int = int(os.getenv("RAG_DND_LISTEN_PORT") or 8000)
        self.embeddings_model: str = os.getenv("RAG_DND_EMBEDDINGS_MODEL") or \
            "text-embedding-ada-002"
        self.embeddings_provider: str = \
            os.getenv("RAG_DND_EMBEDDINGS_PROVIDER") or "HuggingFace"
        self.vector_database: str = os.getenv("RAG_DND_VECTORDB") or \
            "data/chroma"
        self.content_database_url: str = os.getenv("RAG_DND_CONTENTDB_URL") or \
            "sqlite://"
        self.collection_name: str = os.getenv("RAG_DND_COLLECTION_NAME") or \
            "rag_dnd"
        self.log_level: str = os.getenv("RAG_DND_LOG_LEVEL") or "WARNING"
        self.log_file: str = os.getenv("RAG_DND_LOG_FILE") or "log/app.log"

    def __repr__(self) -> str:
        """Return a string representation of the configuration."""
        return f"Config(session_log={self.session_log}, listen_ip={self.listen_ip}, listen_port={self.listen_port}, embeddings_model={self.embeddings_model}, embeddings_provider={self.embeddings_provider}, vector_database={self.vector_database}, content_database_url={self.content_database_url}, collection_name={self.collection_name}, log_level={self.log_level}, log_file={self.log_file})"
