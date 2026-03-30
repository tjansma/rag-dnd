class RAGDNDException(Exception):
    """Base exception for RAGDND errors."""
    pass

class CampaignNotFoundError(RAGDNDException):
    """Exception raised when a campaign is not found."""
    pass
