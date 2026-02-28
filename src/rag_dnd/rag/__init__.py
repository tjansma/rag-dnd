from .manager import store_document, ensure_collection, query, \
    delete_document, update_document, prompt_llm, expand_query
from .models import QueryResult
from .exceptions import RAGException, DocumentExistsError, DocumentNotFoundError

__all__ = [
    "store_document",
    "ensure_collection",
    "query",
    "delete_document",
    "update_document",
    "prompt_llm",
    "expand_query",
    "QueryResult",
    "RAGException",
    "DocumentExistsError",
    "DocumentNotFoundError",
]

from .database import init_db

init_db()
