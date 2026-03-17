"""Campaign  class containing all services for a campaign."""
import logging
from pathlib import Path
from typing import Self

from . import manager
from .database import get_session
from .exceptions import DocumentExistsError
from .models import CampaignMetadata, QueryResult

logger = logging.getLogger(__name__)

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
        with get_session() as session:
            self.default_collection = \
                manager.ensure_collection(session,
                                          metadata.get_default_collection_name(),
                                          metadata.id)

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
    def query_rag(self, prompt: str, collection_name: str | None = None) -> list[QueryResult]:
        """Query the RAG system.
        
        Args:
            prompt (str): The prompt to query.
                collection_name (str | None): The collection name to use.
                                          If None, the default campaign 
                                          collection will be used.
            
        Returns:
            list[QueryResult]: The query results.
        """
        if collection_name is None:
            collection_name = self.metadata.get_default_collection_name()
        
        with get_session() as session:
            collection = manager.get_collection(session, collection_name)
            if collection.campaign_id != self.metadata.id:
                logger.error(f"Campaign.query_rag: Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
                raise ValueError(f"Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
        
            return manager.query(prompt, collection, session)

    def store_document(self,
                       filename: Path,
                       custom_filename: str | None = None,
                       collection_name: str | None = None) -> None:
        """
        Store a document in the database.
        
        Args:
            filename (Path): The path to the document.
            custom_filename (str | None): The custom filename to use. 
                                          If None, the filename will be used.
            collection_name (str | None): The collection name to use.
                                          If None, the default campaign 
                                          collection will be used.
            
        Returns:
            None
        """
        if not filename.exists():
            logger.error(f"Campaign.store_document: File '{filename}' not found.")
            raise FileNotFoundError(f"File '{filename}' not found.")

        if custom_filename is None:
            custom_filename = filename.name

        if collection_name is None:
            collection = self.default_collection
        else:
            with get_session() as session:
                collection = manager.get_collection(session, collection_name)
                if collection.campaign_id != self.metadata.id:
                    logger.error(f"Campaign.store_document: Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
                    raise ValueError(f"Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")

        with get_session() as session:
            try:
                manager.store_document(collection, filename, session, custom_filename=custom_filename)
            except DocumentExistsError:
                manager.update_document(collection, filename, session, custom_filename=custom_filename)
