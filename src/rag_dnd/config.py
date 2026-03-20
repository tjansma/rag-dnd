"""Configuration for the server-side of the RAG D&D application."""
from typing import Optional, Self, Any
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import tempfile

import dotenv

# ------------------------------------------------------------------
# Global configuration instance
# ------------------------------------------------------------------
_config_instance: Optional["Config"] = None

dotenv.load_dotenv()

# ==================================================================
# Default configuration values
# ==================================================================
_DEFAULTS = {
    "data_dir": None,
    "transcript_database": Path("db/relational/transcript.db"),
    "api_ip": "127.0.0.1",
    "api_port": 8001,
    "embeddings_model": "jinaai/jina-embeddings-v3",
    "embeddings_provider": "HuggingFace",
    "embeddings_device": "cpu",
    "vector_database": Path("db/vector"),
    "relevance_threshold": 0.5,
    "content_database_url": "sqlite:///db/relational/content.db",
    "log_level": "WARNING",
    "log_file": Path("log/app.log"),
    "upload_dir": Path("uploads"),
    "query_expansion_enabled": True,
    "query_expansion_model": "",
    "query_expansion_provider": "",
    "query_expansion_device": "cpu",
    "query_expansion_system_prompt": "",
    "api_auto_reload": False,
}

def _env_override(config: dict, key: str, env_var: str, cast=str) -> bool:
    """
    Override a configuration value with an environment variable.

    Args:
        config (dict): The configuration dictionary.
        key (str): The key to override.
        env_var (str): The environment variable to use.
        cast (callable): The type to cast the value to.

    Returns:
        bool: True if the value was overridden, False otherwise.
    """
    val = os.getenv(env_var)
    if val is None:
        return False
    
    # Handle boolean overrides to convert "true", "1", "yes" to True
    # and everything else to False
    if cast == bool:
        config[key] = val.lower() in ("true", "1", "yes")
        return True

    # Handle all other types
    config[key] = cast(val)
    return True

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
    except OSError:
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
    transcript_database: Path
    api_ip: str
    api_port: int
    embeddings_model: str
    embeddings_provider: str
    embeddings_device: str
    vector_database: Path
    relevance_threshold: float
    content_database_url: str
    log_level: str
    log_file: Path
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

        The configuration is loaded in the following order:
        1. Defaults
        2. Config file
        3. Environment variables
        4. Overrides

        BEWARE: Overrides are applied permanently to the config instance.
        If you want to use a different configuration, you must create a new
        config instance.

        Args:
            overrides (dict[str, Any] | None): Dictionary of overrides to apply 
                                               to the configuration.

        Returns:
            Config: The configuration for the server application.
        """
        # If we have already loaded the config and there are no overrides,
        # return the cached config.
        global _config_instance
        if overrides is None and _config_instance is not None:
            return _config_instance

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
        if not _env_override(actual_config,
                             "data_dir", "RAG_DND_DATA_DIR",
                             Path):
            actual_config["data_dir"] = _get_default_data_dir()
        
        # ------------------------------------------------------------------
        # Per-campaign data storage locations
        # ------------------------------------------------------------------
        _env_override(actual_config,
                      "transcript_database", "RAG_DND_TRANSCRIPT_DB", Path)
        _env_override(actual_config,
                      "vector_database", "RAG_DND_VECTORDB", Path)
        _env_override(actual_config,
                      "log_file", "RAG_DND_LOG_FILE", Path)
        _env_override(actual_config,
                      "upload_dir", "RAG_DND_UPLOAD_DIR", Path)

        # ------------------------------------------------------------------
        # API
        # ------------------------------------------------------------------
        _env_override(actual_config, "api_ip", "RAG_DND_API_IP")
        _env_override(actual_config,
                      "api_port", "RAG_DND_API_PORT",
                      int)
        
        # ------------------------------------------------------------------
        # Embeddings
        # ------------------------------------------------------------------
        _env_override(actual_config,
                      "embeddings_model", "RAG_DND_EMBEDDINGS_MODEL")
        _env_override(actual_config,
                      "embeddings_provider", "RAG_DND_EMBEDDINGS_PROVIDER")
        _env_override(actual_config,
                      "embeddings_device", "RAG_DND_EMBEDDINGS_DEVICE")
        
        # ------------------------------------------------------------------
        # Vector database and search parameters
        # ------------------------------------------------------------------
        _env_override(actual_config,
                      "relevance_threshold", "RAG_DND_RELEVANCE_THRESHOLD",
                      float)
        _env_override(actual_config,
                      "query_expansion_enabled", 
                      "RAG_DND_QUERY_EXPANSION_ENABLED",
                      bool)
        _env_override(actual_config,
                      "query_expansion_model", "RAG_DND_QUERY_EXPANSION_MODEL")
        _env_override(actual_config,
                      "query_expansion_provider", "RAG_DND_QUERY_EXPANSION_PROVIDER")
        _env_override(actual_config,
                      "query_expansion_device", "RAG_DND_QUERY_EXPANSION_DEVICE")
        _env_override(actual_config,
                      "query_expansion_system_prompt", "RAG_DND_QUERY_EXPANSION_SYSTEM_PROMPT")

        # ------------------------------------------------------------------
        # Content database
        # ------------------------------------------------------------------
        if _env_override(actual_config,
                         "content_database_url", "RAG_DND_CONTENTDB"):
            db_path = actual_config["content_database_url"]
            if "://" not in db_path:
                actual_config["content_database_url"] = f"sqlite:///{db_path}"

        # ------------------------------------------------------------------
        # Logging and debug settings
        # ------------------------------------------------------------------
        _env_override(actual_config,
                      "log_level", "RAG_DND_LOG_LEVEL")
        _env_override(actual_config,
                      "api_auto_reload", "RAG_DND_API_AUTO_RELOAD",
                      bool)

        # ------------------------------------------------------------------
        # Overrides from arguments
        # ------------------------------------------------------------------
        if overrides:
            actual_config.update(overrides)

        # ------------------------------------------------------------------
        # Store and return the configuration
        # ------------------------------------------------------------------
        _config_instance = cls(**actual_config)
        return _config_instance

    @staticmethod
    def clear() -> None:
        """
        Clear the cached configuration instance.

        This is useful for testing purposes, as it allows you to create a new
        configuration instance without having to restart the application.

        Returns:
            None
        """
        global _config_instance
        _config_instance = None

    def __repr__(self) -> str:
        """
        Return a string representation of the configuration.

        This is useful for debugging purposes, as it allows you to see the
        current configuration settings.

        Returns:
            str: A string representation of the configuration.
        """
        return f"Config(data_dir={self.data_dir}, api_ip={self.api_ip}, api_port={self.api_port}, embeddings_model={self.embeddings_model}, embeddings_provider={self.embeddings_provider}, vector_database={self.vector_database}, content_database_url={self.content_database_url}, log_level={self.log_level}, log_file={self.log_file})"
