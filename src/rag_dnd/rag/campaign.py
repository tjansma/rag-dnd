"""Campaign  class containing all services for a campaign."""

from typing import Self

from . import manager
from .models import CampaignMetadata, QueryResult

class Campaign:
    """Class to represent a campaign."""
    # --- Constructor ---
    def __init__(self, metadata: CampaignMetadata):
        """Initialize the campaign.
        
        Args:
            metadata (CampaignMetadata): The campaign metadata.
            
        Returns:
            None
        """
        self.metadata = metadata

    # --- Class methods ---
    @classmethod
    def from_db_by_short_name(cls, short_name: str) -> Self:
        """Load campaign metadata by short name.
        
        Args:
            short_name (str): The short name of the campaign.
            
        Returns:
            Self: The campaign.
        """
        metadata = CampaignMetadata.load_by_short_name(short_name)

        if metadata is None:
            raise ValueError(f"Campaign '{short_name}' not found.")

        return cls(metadata)

    @classmethod
    def from_db_by_id(cls, id: int) -> Self:
        """Load campaign metadata by id.
        
        Args:
            id (int): The id of the campaign.
            
        Returns:
            Self: The campaign.
        """
        metadata = CampaignMetadata.load_by_id(id)

        if metadata is None:
            raise ValueError(f"Campaign '{id}' not found.")

        return cls(metadata)
    
    # --- Methods ---
    def query_rag(self, prompt: str) -> list[QueryResult]:
        """Query the RAG system.
        
        Args:
            prompt (str): The prompt to query.
            
        Returns:
            list[QueryResult]: The query results.
        """
        return manager.query(prompt)
