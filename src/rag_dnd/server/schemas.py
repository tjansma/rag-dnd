"""
FastAPI schemas for API requests and responses.
"""
from typing import Any

from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    max_results: int = 5
    collection_name: str | None = None

class LLMMessage(BaseModel):
    role: str
    content: str

class ExpandQueryRequest(BaseModel):
    query: str
    extra_context: str

class CreateCampaignRequest(BaseModel):
    full_name: str
    short_name: str
    roleplay_system: str
    language: str
    active_summary_file: str | None = None
    session_log_file: str | None = None
    extensions: dict[str, Any] | None = None

class CampaignResponse(BaseModel):
    id: int
    full_name: str
    short_name: str
    roleplay_system: str
    language: str
    active_summary_file: str | None = None
    session_log_file: str | None = None
    extensions: dict[str, Any] | None = None
