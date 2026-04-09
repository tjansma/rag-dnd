class RAGDNDException(Exception):
    """Base exception for RAGDND errors."""
    pass

class RAGException(RAGDNDException):
    """Base exception for RAG errors."""
    pass

class DocumentExistsError(RAGException):
    """Exception raised when a document already exists."""
    pass

class DocumentNotFoundError(RAGException):
    """Exception raised when a document is not found."""
    pass

class CampaignNotFoundError(RAGDNDException):
    """Exception raised when a campaign is not found."""
    pass

class PlayerExistsError(RAGDNDException):
    """Exception raised when a player already exists."""
    pass

class PlayerNotFoundError(RAGDNDException):
    """Exception raised when a player is not found."""
    pass

class DuplicateGameCharacterError(RAGDNDException):
    """Exception raised when a game character already exists."""
    pass

class GameCharacterNotFoundError(RAGDNDException):
    """Exception raised when a game character is not found."""
    pass
