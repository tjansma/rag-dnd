from ..core.exceptions import RAGDNDException

class RAGException(RAGDNDException):
    """Base exception for RAG errors."""
    pass

class DocumentExistsError(RAGException):
    """Exception raised when a document already exists."""
    pass

class DocumentNotFoundError(RAGException):
    """Exception raised when a document is not found."""
    pass
