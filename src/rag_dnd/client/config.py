"""
Configuration for the RAG clients.
"""
from typing import Self
from typing import Any
from dataclasses import dataclass, fields
import os
from platformdirs import user_config_dir
import tomllib


@dataclass
class ClientConfig:
    base_url: str = "http://localhost:8001"
    transcript_database: str = "data/transcript.db"
    logbook_path: str = "data/LMoP_ToD_TimJansma_Log.md"
    summary_prompt_file: str = "prompts/session_summary.txt"
    query_expansion: bool = True

    @classmethod
    def load(cls, overrides: dict[str, Any] | None = None) -> Self:
        # Start with defaults
        defaults = {f.name: f.default for f in fields(cls)}
        actual_config = defaults.copy()

        # Load config file from user config directory
        # e.g. ~/.config/rag-dnd/config.toml on Linux or macOS
        # e.g. %APPDATA%/rag-dnd/config.toml on Windows
        config_dir = user_config_dir("rag-dnd")
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

        # Create the config file if it doesn't exist
        if not os.path.exists(config_file):
            os.makedirs(config_dir, exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                f.write("# RAG D&D Client Configuration\n")
                f.write("# Base URL for the RAG server\n")
                f.write(f"base_url = \"{actual_config['base_url']}\"\n")
                f.write("# Path to the transcript database\n")
                f.write(f"transcript_database = \"{actual_config['transcript_database']}\"\n")
                f.write("# Path to the session log\n")
                f.write(f"logbook_path = \"{actual_config['logbook_path']}\"\n")
                f.write("# Path to the summary prompt file\n")
                f.write(f"summary_prompt_file = \"{actual_config['summary_prompt_file']}\"\n")
                f.write("# Enable query expansion\n")
                f.write(f"query_expansion = {actual_config['query_expansion']}\n")

        # Check runtime override
        if overrides:
            actual_config.update(overrides)

        return cls(**actual_config)  # type: ignore
