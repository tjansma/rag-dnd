"""Configuration for the RAG clients."""
from typing import Self
from typing import Any
from dataclasses import dataclass
import os
from platformdirs import user_config_dir

import tomllib
import tomlkit

_DEFAULTS = {
    "base_url": "http://localhost:8001",
    "transcript_database": "data/transcript.db",
    "logbook_path": "data/LMoP_ToD_TimJansma_Log.md",
    "summary_prompt_file": "prompts/session_summary.txt",
    "query_expansion": True,
    "campaign": "",
    "collection": "",
}

@dataclass
class ClientConfig:
    """Configuration for the RAG clients."""
    base_url: str
    _transcript_database: str
    _logbook_path: str
    _summary_prompt_file: str
    query_expansion: bool
    campaign: str
    collection: str
    config_dir: str = ""

    @property
    def transcript_database(self) -> str:
        return self._resolve_path(self._transcript_database)

    @property
    def logbook_path(self) -> str:
        return self._resolve_path(self._logbook_path)

    @property
    def summary_prompt_file(self) -> str:
        return self._resolve_path(self._summary_prompt_file)

    def _resolve_path(self, path: str) -> str:
        """
        Resolve a path to an absolute path.

        Args:
            path (str): The path to resolve.

        Returns:
            str: The resolved path.

        Raises:
            ValueError: If the campaign is not set and the path is not absolute.
        """
        if os.path.isabs(path):
            resolved = path
        else:
            if not self.campaign:
                raise ValueError("Campaign must be set to resolve paths.")
            resolved = os.path.join(self.config_dir, "campaigns", self.campaign, path)
            
        # Ensure that the intermediate subdirectories always exist (for SQLite etc.)
        parent_dir = os.path.dirname(resolved)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        return resolved

    @classmethod
    def load(cls, overrides: dict[str, Any] | None = None) -> Self:
        """
        Load configuration from defaults, config file, and environment
        variables.

        Args:
            overrides: Dictionary of overrides to apply to the configuration.

        Returns:
            ClientConfig: The configuration for the RAG clients.
        """
        # Start with defaults
        actual_config: dict[str, Any] = _DEFAULTS.copy()

        # Load config file from user config directory
        # e.g. ~/.config/rag-dnd/config.toml on Linux or macOS
        # e.g. %APPDATA%/rag-dnd/config.toml on Windows
        config_dir = user_config_dir("rag-dnd", appauthor=False)
        config_file = os.path.join(config_dir, "config.toml")
        if os.path.exists(config_file):
            with open(config_file, "rb") as f:
                config_data = tomllib.load(f)
                actual_config.update(config_data)
        
        # Check environment variables for overrides
        if os.getenv("RAG_DND_BASE_URL"):
            actual_config["base_url"] = os.getenv("RAG_DND_BASE_URL")
        if os.getenv("RAG_DND_TRANSCRIPT_DB"):
            actual_config["transcript_database"] = \
                os.getenv("RAG_DND_TRANSCRIPT_DB")
        if os.getenv("RAG_DND_SESSION_LOG"):
            actual_config["logbook_path"] = os.getenv("RAG_DND_SESSION_LOG")
        if os.getenv("RAG_DND_SUMMARY_PROMPT_FILE"):
            actual_config["summary_prompt_file"] = \
                os.getenv("RAG_DND_SUMMARY_PROMPT_FILE")
        if os.getenv("RAG_DND_QUERY_EXPANSION_ENABLED"):
            query_expansion_enabled = \
                str(os.getenv("RAG_DND_QUERY_EXPANSION_ENABLED"))
            actual_config["query_expansion"] = \
                query_expansion_enabled.lower() == "true" or \
                query_expansion_enabled == "1"
        if os.getenv("RAG_DND_CAMPAIGN"):
            actual_config["campaign"] = os.getenv("RAG_DND_CAMPAIGN")
        if os.getenv("RAG_DND_COLLECTION"):
            actual_config["collection"] = os.getenv("RAG_DND_COLLECTION")

        # Create the config file if it doesn't exist
        if not os.path.exists(config_file):
            os.makedirs(config_dir, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                doc = tomlkit.document()
                for key, value in actual_config.items():
                    doc.add(key, value)
                f.write(tomlkit.dumps(doc))

        # Check runtime override
        if overrides:
            actual_config.update(overrides)

        if not actual_config["campaign"]:
            raise ValueError("No campaign configured. Set RAG_DND_CAMPAIGN "
                             f"environment variable or add 'campaign = "
                             f"<campaign>' to {config_file}.")

        actual_config["_transcript_database"] = actual_config.pop("transcript_database")
        actual_config["_logbook_path"] = actual_config.pop("logbook_path")
        actual_config["_summary_prompt_file"] = actual_config.pop("summary_prompt_file")
        actual_config["config_dir"] = config_dir

        return cls(**actual_config)  # type: ignore
