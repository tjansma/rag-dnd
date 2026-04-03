from ..core.exceptions import RAGDNDException

class PlayerExistsError(RAGDNDException):
    """Exception raised when a player already exists."""
    pass

class PlayerNotFoundError(RAGDNDException):
    """Exception raised when a player is not found."""
    pass
