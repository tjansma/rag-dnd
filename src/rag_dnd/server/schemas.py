"""
FastAPI schemas for API requests and responses.
"""
from typing import Any

from pydantic import BaseModel

class StoreRequest(BaseModel):
    file_path: str

class QueryRequest(BaseModel):
    query: str
    max_results: int = 5
    collection_name: str | None = None

class UpdateRequest(BaseModel):
    file_path: str

class DeleteRequest(BaseModel):
    file_path: str

class QueryResponse(BaseModel):
    text: str
    source_document: str

class LLMMessage(BaseModel):
    role: str
    content: str

class ExpandQueryRequest(BaseModel):
    query: str
    extra_context: str

class SuccessResult(BaseModel):
    message: str
    status_code: int

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
