"""
FastAPI routes for API requests.
"""
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

import rag

from .schemas import StoreRequest, QueryRequest, UpdateRequest, \
    DeleteRequest, QueryResponse

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
        rag.store_document(request.file_path)
    except:
        raise HTTPException(status_code=409, detail="Document already exists")

@router.put("/document")
async def update_document(request: UpdateRequest):
    try:
        rag.update_document(request.file_path)
    except:
        raise HTTPException(status_code=404, detail="Document not found.")

@router.delete("/document")
async def delete_document(request: DeleteRequest):
    try:
        rag.delete_document(request.file_path)
    except:
        raise HTTPException(status_code=404, detail="Document not found.")

@router.post("/rag_query")
async def query_rag(request: QueryRequest) -> list[QueryResponse]:
    results = rag.query(request.query)
    return [ QueryResponse(text=result.text,
             source_document=result.source_document) for result in results]
