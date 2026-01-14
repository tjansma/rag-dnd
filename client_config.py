"""
Configuration for the RAG clients.
"""

from dataclasses import dataclass

@dataclass
class ClientConfig:
    base_url: str = "http://localhost:8001"
