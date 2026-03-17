"""
FastAPI schemas for API requests and responses.
"""
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
