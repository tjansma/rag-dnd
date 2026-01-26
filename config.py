"""Configuration for the application."""
import os

import dotenv

dotenv.load_dotenv()

class Config:
    def __init__(self):
        """Initialize the configuration."""
        self.session_log: str = os.getenv("RAG_DND_SESSION_LOG") or \
            "data/session_log.txt"
        self.transcript_database: str = os.getenv("RAG_DND_TRANSCRIPT_DB") or \
            "data/transcript.db"
        self.api_ip: str = os.getenv("RAG_DND_API_IP") or "127.0.0.1"
        self.api_port: int = int(os.getenv("RAG_DND_API_PORT") or 8001)
        self.embeddings_model: str = os.getenv("RAG_DND_EMBEDDINGS_MODEL") or \
            "intfloat/multilingual-e5-small"
        self.embeddings_provider: str = \
            os.getenv("RAG_DND_EMBEDDINGS_PROVIDER") or "HuggingFace"
        self.embedding_device: str = os.getenv("RAG_DND_EMBEDDINGS_DEVICE") or \
            "cpu"
        self.vector_database: str = os.getenv("RAG_DND_VECTORDB") or \
            "data/chroma"
        self.relevance_threshold: float = \
            float(os.getenv("RAG_DND_RELEVANCE_THRESHOLD") or 0.5)
        self.content_database_url: str = os.getenv("RAG_DND_CONTENTDB_URL") or \
            "sqlite://"

        model_name_slug = self.embeddings_model.replace("/", "_")
        self.collection_name: str = \
            f'{os.getenv("RAG_DND_COLLECTION_PREFIX") or "rag_dnd"}_{model_name_slug}'
        self.log_level: str = os.getenv("RAG_DND_LOG_LEVEL") or "WARNING"
        self.log_file: str = os.getenv("RAG_DND_LOG_FILE") or "log/app.log"

        # Query expansion settings
        self.query_expansion_enabled: bool = \
            str(os.getenv("RAG_DND_QUERY_EXPANSION_ENABLED", "False")).upper() == "TRUE" or \
            str(os.getenv("RAG_DND_QUERY_EXPANSION_ENABLED", "False")) == "1"
        self.query_expansion_model: str = \
            os.getenv("RAG_DND_QUERY_EXPANSION_MODEL") or ""
        self.query_expansion_provider: str = \
            os.getenv("RAG_DND_QUERY_EXPANSION_PROVIDER") or ""
        self.query_expansion_device: str = \
            os.getenv("RAG_DND_QUERY_EXPANSION_DEVICE") or "cpu"
        self.query_expansion_system_prompt: str = \
            os.getenv("RAG_DND_QUERY_EXPANSION_SYSTEM_PROMPT") or ""

        self.api_auto_reload = False
        api_auto_reload = os.getenv("RAG_DND_API_AUTO_RELOAD")
        if api_auto_reload and \
           (api_auto_reload.upper() == "TRUE" or api_auto_reload == "1"):
            self.api_auto_reload = True

    def __repr__(self) -> str:
        """Return a string representation of the configuration."""
        return f"Config(session_log={self.session_log}, api_ip={self.api_ip}, api_port={self.api_port}, embeddings_model={self.embeddings_model}, embeddings_provider={self.embeddings_provider}, vector_database={self.vector_database}, content_database_url={self.content_database_url}, collection_name={self.collection_name}, log_level={self.log_level}, log_file={self.log_file})"
