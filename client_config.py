"""
Configuration for the RAG clients.
"""

from dataclasses import dataclass

@dataclass
class ClientConfig:
    base_url: str = "http://localhost:8001"
    transcript_database: str = "data/transcript.db"
    logbook_path: str = "data/LMoP_ToD_TimJansma_Log.md"
    summary_prompt_file: str = "prompts/session_summary.txt"
