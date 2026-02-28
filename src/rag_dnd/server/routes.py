"""
FastAPI routes for API requests.
"""
import logging

from fastapi import APIRouter, HTTPException

from .. import rag

from .schemas import StoreRequest, QueryRequest, UpdateRequest, \
    DeleteRequest, QueryResponse, LLMMessage, ExpandQueryRequest

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/document", status_code=201)
async def store_document(request: StoreRequest):
    """
    Store a document in the vector store.
    
    Args:
        request (StoreRequest): The document to store.

    Returns:
        SuccessResult: The result of the operation.
    """
    try:
        logger.info(f"Storing document: {request.file_path}")
        rag.store_document(request.file_path)
    except FileNotFoundError:
        logger.error(f"Store failed: File {request.file_path} not found on server FS.")
        raise HTTPException(status_code=404,
                            detail="Document not found on server FS.")
    except rag.DocumentExistsError:
        logger.error(f"Document already exists in DB: {request.file_path}")
        raise HTTPException(status_code=409,
                            detail="Document already exists in DB.")
    except Exception as e:
        logger.error(f"Error storing document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.put("/document")
async def update_document(request: UpdateRequest):
    try:
        rag.update_document(request.file_path)
    except (FileNotFoundError, rag.DocumentNotFoundError):
        raise HTTPException(status_code=404, detail="Document not found.")
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.delete("/document")
async def delete_document(request: DeleteRequest):
    try:
        rag.delete_document(request.file_path)
    except rag.DocumentNotFoundError:
        raise HTTPException(status_code=404,
                            detail="Document not found in DB.")
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.post("/rag_query")
async def query_rag(request: QueryRequest) -> list[QueryResponse]:
    results = rag.query(request.query, request.limit)
    return [ QueryResponse(text=result.text,
             source_document=result.source_document) for result in results]

@router.post("/llm_generate")
async def generate_llm(request: list[LLMMessage]) -> str:
    messages = [ { "role": message.role, "content": message.content } for message in request ]
    return rag.prompt_llm(messages)

@router.post("/expand_query")
async def expand_query(request: ExpandQueryRequest) -> str:
    return rag.expand_query(request.query, request.extra_context)
