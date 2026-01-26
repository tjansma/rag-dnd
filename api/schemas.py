"""
FastAPI schemas for API requests and responses.
"""
from pydantic import BaseModel

class StoreRequest(BaseModel):
    file_path: str

class QueryRequest(BaseModel):
    query: str
    limit: int = 5

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
