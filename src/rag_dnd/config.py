"""Configuration for the server-side of the RAG D&D application."""
from typing import Optional, Self, Any
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import tempfile

import dotenv
from sqlalchemy.engine.url import URL

# ------------------------------------------------------------------
# Global configuration instance
# ------------------------------------------------------------------
_config_instance: Optional["Config"] = None

dotenv.load_dotenv()

# ==================================================================
# Default configuration values
# ==================================================================
_DEFAULTS = {
    "custom_data_dir": None,
    "transcript_database": Path("db/relational/transcript.db"),
    "api_ip": "127.0.0.1",
    "api_port": 8001,
    "embeddings_model": "jinaai/jina-embeddings-v3",
    "embeddings_provider": "HuggingFace",
    "embeddings_device": "cpu",
    "vector_database": Path("db/vector"),
    "relevance_threshold": 0.75,
    "bm25_threshold": 2.0,
    "content_database_driver": "sqlite",
    "content_database_host": None,
    "content_database_port": None,
    "content_database_user": None,
    "content_database_password": None,
    "content_database_name": "content.db",
    "log_level": "WARNING",
    "log_file": Path("log/app.log"),
    "upload_dir": Path("uploads"),
    "query_expansion_enabled": True,
    "query_expansion_model": "Qwen/Qwen3-1.7B",
    "query_expansion_provider": "HuggingFace",
    "query_expansion_device": "cpu",
    "query_expansion_system_prompt": "prompts/qry_expansion_system_prompt.txt",
    "query_expansion_max_new_tokens": 8192,
    "api_auto_reload": False,
    "auto_update_ai_models": True,
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
    custom_data_dir: Path | None
    transcript_database: Path
    api_ip: str
    api_port: int
    embeddings_model: str
    embeddings_provider: str
    embeddings_device: str
    vector_database: Path
    relevance_threshold: float
    bm25_threshold: float
    content_database_driver: str
    content_database_host: str
    content_database_port: str
    content_database_user: str
    content_database_password: str
    content_database_name: str
    log_level: str
    log_file: Path
    upload_dir: Path
    query_expansion_enabled: bool
    query_expansion_model: str
    query_expansion_provider: str
    query_expansion_device: str
    query_expansion_system_prompt: str
    query_expansion_max_new_tokens: int
    api_auto_reload: bool
    auto_update_ai_models: bool

    @property
    def data_dir(self) -> Path:
        """
        Get the data directory.
        
        Returns:
            Path: The data directory.
        """
        if self.custom_data_dir is not None:
            return self.custom_data_dir
        return _get_default_data_dir()

    @property
    def content_database_url(self) -> str:
        """
        Get the content database URL.
        
        Returns:
            str: The content database URL.
        """
        if self.content_database_driver.lower() == "sqlite":
            if not Path(self.content_database_name).is_absolute():
                db_full_name = self.data_dir / self.content_database_name
            else:
                db_full_name = Path(self.content_database_name)

            os.makedirs(db_full_name.parent, exist_ok=True)
        else:
            db_full_name = self.content_database_name

        return str(URL.create(
            drivername=self.content_database_driver,
            username=self.content_database_user,
            password=self.content_database_password,
            host=self.content_database_host,
            port=self.content_database_port,
            database=str(db_full_name.as_posix()),
        ))

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
        _env_override(actual_config,
                      "custom_data_dir", "RAG_DND_DATA_DIR",
                      Path)
        
        # ------------------------------------------------------------------
        # Resolve active data directory
        # ------------------------------------------------------------------
        active_data_dir = Path(actual_config["custom_data_dir"] or \
                               _get_default_data_dir()).resolve()
        
        # ------------------------------------------------------------------
        # Global settings
        # ------------------------------------------------------------------
        _env_override(actual_config,
                      "auto_update_ai_models", "RAG_DND_AUTO_UPDATE_AI_MODELS", bool)

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
                      "bm25_threshold", "RAG_DND_BM25_THRESHOLD",
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
        _env_override(actual_config,
                      "query_expansion_max_new_tokens", "RAG_DND_QUERY_EXPANSION_MAX_NEW_TOKENS",
                      int)

        # ------------------------------------------------------------------
        # Content database
        # ------------------------------------------------------------------
        _env_override(actual_config,
                      "content_database_driver", "RAG_DND_CONTENTDB_DRIVER")
        _env_override(actual_config,
                      "content_database_host", "RAG_DND_CONTENTDB_HOST")
        _env_override(actual_config,
                      "content_database_port", "RAG_DND_CONTENTDB_PORT")
        _env_override(actual_config,
                      "content_database_user", "RAG_DND_CONTENTDB_USER")
        _env_override(actual_config,
                      "content_database_password", "RAG_DND_CONTENTDB_PASSWORD")
        _env_override(actual_config,
                      "content_database_name", "RAG_DND_CONTENTDB_NAME")

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
        # Resolve and create paths
        # ------------------------------------------------------------------
        os.makedirs(active_data_dir, exist_ok=True)
        path_keys = [
            "transcript_database",
            "vector_database",
            "log_file",
            "upload_dir"
        ]
        for current_path in path_keys:
            if not actual_config[current_path].is_absolute():
                actual_config[current_path] = \
                    (active_data_dir / actual_config[current_path]).resolve()
            os.makedirs(actual_config[current_path].parent, exist_ok=True)

        # ------------------------------------------------------------------
        # Apply global settings to environment
        # ------------------------------------------------------------------
        if actual_config["auto_update_ai_models"]:
            os.environ.pop("HF_HUB_OFFLINE", None)
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"

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
