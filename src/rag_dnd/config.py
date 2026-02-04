"""Configuration for the server-side of the RAG D&D application."""
from typing import Self, Any
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import tempfile

import dotenv

dotenv.load_dotenv()

# ==================================================================
# Default configuration values
# ==================================================================
_DEFAULTS = {
    "data_dir": None,
#    "session_log": "session_log.txt",
    "transcript_database": "db/relational/transcript.db",
    "api_ip": "127.0.0.1",
    "api_port": 8001,
    "embeddings_model": "intfloat/multilingual-e5-small",
    "embeddings_provider": "HuggingFace",
    "embedding_device": "cpu",
    "vector_database": "db/vector",
    "relevance_threshold": 0.5,
    "content_database": "db/relational/content.db",
    "collection_name": "rag_dnd",
    "log_level": "WARNING",
    "log_file": "log/app.log",
    "upload_dir": Path("uploads"),
    "query_expansion_enabled": True,
    "query_expansion_model": "",
    "query_expansion_provider": "",
    "query_expansion_device": "cpu",
    "query_expansion_system_prompt": "",
    "api_auto_reload": False,
}

def _is_writable(path: Path) -> bool:
    """
    Check if a path is writable.

    Args:
        path (Path): The path to check.

    Returns:
        bool: True if the path is writable, False otherwise.
    """
    # Check if the path is writable by creating a temporary file in the directory
    # This is a cross-platform way to check for writability
    # If the path doesn't exist, check if the parent directory is writable
    # If neither is writable, catch the exception to return False
    try:
        target = path if path.exists() else path.parent
        with tempfile.NamedTemporaryFile(dir=target) as f:
            f.write(b"test")
        return True
    except:
        return False

def _get_default_data_dir() -> Path:
    """
    Get the default data directory for the application.

    Returns:
        Path: The default data directory for the application.
    """
    if sys.platform == "win32":
        # Try to use C:/ProgramData/rag_dnd
        data_dir = Path("C:/ProgramData/rag_dnd")
        if not _is_writable(data_dir):
            # Try to use $APPDATA/rag_dnd
            data_dir = Path(f"{os.getenv("APPDATA")}/rag_dnd").resolve(strict=False)
            if not _is_writable(data_dir):
                raise RuntimeError("Cannot write to data directory")
        return data_dir
    elif sys.platform == "linux":
        # Try to use /var/lib/rag_dnd
        data_dir = Path("/var/lib/rag_dnd")
        if not _is_writable(data_dir):
            # Try to use $HOME/.local/share/rag_dnd
            data_dir = Path(f"{os.getenv("HOME")}/.local/share/rag_dnd").resolve(strict=False)
            if not _is_writable(data_dir):
                raise RuntimeError("Cannot write to data directory")
        return data_dir
    elif sys.platform == "darwin":
        # Try to use /Library/Application Support/rag_dnd
        data_dir = Path("/Library/Application Support/rag_dnd")
        if not _is_writable(data_dir):
            # Try to use $HOME/Library/Application Support/rag_dnd
            data_dir = Path(f"{os.getenv("HOME")}/Library/Application Support/rag_dnd").resolve(strict=False)
            if not _is_writable(data_dir):
                raise RuntimeError("Cannot write to data directory")
        return data_dir
    else:
        raise RuntimeError("Unsupported operating system")

@dataclass
class Config:
    """Configuration for the server application."""
    data_dir: Path
#    session_log: str
    transcript_database: str
    api_ip: str
    api_port: int
    embeddings_model: str
    embeddings_provider: str
    embedding_device: str
    vector_database: str
    relevance_threshold: float
    content_database_url: str
    collection_name: str
    log_level: str
    log_file: str
    upload_dir: Path
    query_expansion_enabled: bool
    query_expansion_model: str
    query_expansion_provider: str
    query_expansion_device: str
    query_expansion_system_prompt: str
    api_auto_reload: bool

    @classmethod
    def load(cls, overrides: dict[str, Any] | None = None) -> Self:
        """
        Load configuration from defaults, config file, and environment variables.

        Args:
            overrides: Dictionary of overrides to apply to the configuration.

        Returns:
            Config: The configuration for the server application.
        """
        # ------------------------------------------------------------------
        # Start with defaults
        # ------------------------------------------------------------------
        actual_config: dict[str, Any] = _DEFAULTS.copy()

        # ==================================================================
        # Override from environment variable, if set
        # ------------------------------------------------------------------
        # Data storage top location.
        # In this directory, we will create subdirectories for each
        # campaign.
        # All other data storage locations are relative to the campaign
        # directories, and will be created for each campaign.
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_DATA_DIR"):
            actual_config["data_dir"] = Path(str(os.getenv("RAG_DND_DATA_DIR"))
                                            ).resolve(strict=False)
        else:
            actual_config["data_dir"] = _get_default_data_dir()
        
        # ------------------------------------------------------------------
        # Per-campaign data storage locations
        # ------------------------------------------------------------------
        # if os.getenv("RAG_DND_SESSION_LOG"):
        #     actual_config["session_log"] = os.getenv("RAG_DND_SESSION_LOG")
        
        if os.getenv("RAG_DND_TRANSCRIPT_DB"):
            actual_config["transcript_database"] = os.getenv("RAG_DND_TRANSCRIPT_DB")

        if os.getenv("RAG_DND_VECTORDB"):
            actual_config["vector_database"] = os.getenv("RAG_DND_VECTORDB")

        if os.getenv("RAG_DND_LOG_FILE"):
            actual_config["log_file"] = os.getenv("RAG_DND_LOG_FILE")

        if os.getenv("RAG_DND_UPLOAD_DIR"):
            actual_config["upload_dir"] = os.getenv("RAG_DND_UPLOAD_DIR")

        # ------------------------------------------------------------------
        # API
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_API_IP"):
            actual_config["api_ip"] = os.getenv("RAG_DND_API_IP")
        if os.getenv("RAG_DND_API_PORT"):
            actual_config["api_port"] = int(str(os.getenv("RAG_DND_API_PORT")))
        if os.getenv("RAG_DND_API_AUTO_RELOAD"):
            actual_config["api_auto_reload"] = bool(str(os.getenv("RAG_DND_API_AUTO_RELOAD")))
        
        # ------------------------------------------------------------------
        # Embeddings
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_EMBEDDINGS_MODEL"):
            actual_config["embeddings_model"] = os.getenv("RAG_DND_EMBEDDINGS_MODEL")
        if os.getenv("RAG_DND_EMBEDDINGS_PROVIDER"):
            actual_config["embeddings_provider"] = os.getenv("RAG_DND_EMBEDDINGS_PROVIDER")
        if os.getenv("RAG_DND_EMBEDDINGS_DEVICE"):
            actual_config["embedding_device"] = os.getenv("RAG_DND_EMBEDDINGS_DEVICE")
        
        # ------------------------------------------------------------------
        # Vector database and search parameters
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_RELEVANCE_THRESHOLD"):
            actual_config["relevance_threshold"] = float(
                str(os.getenv("RAG_DND_RELEVANCE_THRESHOLD")))
        if os.getenv("RAG_DND_QUERY_EXPANSION_ENABLED"):
            expansion_enabled = str(os.getenv("RAG_DND_QUERY_EXPANSION_ENABLED")).upper()
            actual_config["query_expansion_enabled"] = \
                expansion_enabled == "TRUE" or expansion_enabled == "1"

        # ------------------------------------------------------------------
        # Content database
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_CONTENTDB"):
            actual_config["content_database"] = os.getenv("RAG_DND_CONTENTDB")
        
        if os.getenv("RAG_DND_COLLECTION_PREFIX"):
            model_name_slug = str(actual_config["embeddings_model"]).replace("/", "_")
            actual_config["collection_name"] = \
                f'{os.getenv("RAG_DND_COLLECTION_PREFIX")}_{model_name_slug}'
        else:
            model_name_slug = str(actual_config["embeddings_model"]).replace("/", "_")
            actual_config["collection_name"] = \
                f'rag_dnd_{model_name_slug}'

        # ------------------------------------------------------------------
        # Logging and debug settings
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_LOG_LEVEL"):
            actual_config["log_level"] = os.getenv("RAG_DND_LOG_LEVEL")
        if os.getenv("RAG_DND_API_AUTO_RELOAD"):
            api_auto_reload = str(os.getenv("RAG_DND_API_AUTO_RELOAD")).upper()
            actual_config["api_auto_reload"] = \
                api_auto_reload == "TRUE" or api_auto_reload == "1"

        # ------------------------------------------------------------------
        # Query expansion
        # ------------------------------------------------------------------
        if os.getenv("RAG_DND_QUERY_EXPANSION_MODEL"):
            actual_config["query_expansion_model"] = os.getenv("RAG_DND_QUERY_EXPANSION_MODEL")
        if os.getenv("RAG_DND_QUERY_EXPANSION_PROVIDER"):
            actual_config["query_expansion_provider"] = os.getenv("RAG_DND_QUERY_EXPANSION_PROVIDER")
        if os.getenv("RAG_DND_QUERY_EXPANSION_DEVICE"):
            actual_config["query_expansion_device"] = os.getenv("RAG_DND_QUERY_EXPANSION_DEVICE")
        if os.getenv("RAG_DND_QUERY_EXPANSION_SYSTEM_PROMPT"):
            actual_config["query_expansion_system_prompt"] = os.getenv("RAG_DND_QUERY_EXPANSION_SYSTEM_PROMPT")
        
        # ------------------------------------------------------------------
        # Overrides from arguments
        # ------------------------------------------------------------------
        if overrides:
            actual_config.update(overrides)

        # ------------------------------------------------------------------
        # Return the configuration
        # ------------------------------------------------------------------
        return cls(**actual_config)

    def __repr__(self) -> str:
        """Return a string representation of the configuration."""
        return f"Config(data_dir={self.data_dir}, api_ip={self.api_ip}, api_port={self.api_port}, embeddings_model={self.embeddings_model}, embeddings_provider={self.embeddings_provider}, vector_database={self.vector_database}, content_database_url={self.content_database_url}, collection_name={self.collection_name}, log_level={self.log_level}, log_file={self.log_file})"
