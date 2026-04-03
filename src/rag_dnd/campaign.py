"""Campaign  class containing all services for a campaign."""
import logging
from pathlib import Path
from typing import Self, Any

from .core import get_session, CampaignMetadata
from .game import Player
from .rag import manager
from .rag.exceptions import DocumentExistsError
from .rag.models import QueryResult

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
        self.default_collection = \
            manager.ensure_collection(metadata.get_default_collection_name(),
                                      metadata.id)

    # --- Class methods ---
    @classmethod
    def create(cls,
               full_name:str,
               short_name: str,
               roleplay_system: str,
               language: str,
               active_summary_file: str | None,
               session_log_file: str | None,
               extensions: dict[str, Any] | None) -> Self:
        """Create a new campaign.
        
        Args:
            full_name (str): The full name of the campaign.
            short_name (str): The short name of the campaign.
            roleplay_system (str): The roleplay system of the campaign.
            language (str): The language of the campaign.
            active_summary_file (str | None): The active summary file of the campaign.
            session_log_file (str | None): The session log file of the campaign.
            extensions (dict[str, Any] | None): The extensions of the campaign.
            
        Returns:
            Self: The campaign.
        """
        with get_session() as session:
            campaign_metadata = CampaignMetadata(
                full_name=full_name,
                short_name=short_name,
                system=roleplay_system,
                language=language,
                active_summary_file=active_summary_file,
                session_log_file=session_log_file,
                extensions=extensions
            )
            session.add(campaign_metadata)
            session.commit()
            session.expunge_all()
        
        return cls(campaign_metadata)

    @classmethod
    def list_all(cls) -> list[Self]:
        """List all campaigns.
        
        Returns:
            list[Self]: The list of campaigns.
        """
        with get_session() as session:
            campaign_metadata = session.query(CampaignMetadata).all()
            session.expunge_all()
            
        return [cls(metadata) for metadata in campaign_metadata]


    @classmethod
    def from_db_by_short_name(cls, short_name: str) -> Self:
        """Load campaign metadata by short name.
        
        Args:
            short_name (str): The short name of the campaign.
            
        Returns:
            Self: The campaign.
        """
        return cls(CampaignMetadata.load_by_short_name(short_name))

    @classmethod
    def from_db_by_id(cls, id: int) -> Self:
        """Load campaign metadata by id.
        
        Args:
            id (int): The id of the campaign.
            
        Returns:
            Self: The campaign.
        """
        return cls(CampaignMetadata.load_by_id(id))
    
    # --- Methods ---
    def query_rag(self, prompt: str, collection_name: str | None = None, max_results: int = 5) -> list[QueryResult]:
        """Query the RAG system.
        
        Args:
            prompt (str): The prompt to query.
            collection_name (str | None): The collection name to use.
                                          If None, the default campaign 
                                          collection will be used.
            max_results (int): The maximum number of results to return.
                               Defaults to 5.
            
        Returns:
            list[QueryResult]: The query results.

        Raises:
            ValueError: If the collection name is not found or does not belong to the campaign.
        """
        if collection_name is None:
            collection_name = self.metadata.get_default_collection_name()
        
        with get_session() as session:
            collection = manager.get_collection(session, collection_name)
            if collection.campaign_id != self.metadata.id:
                logger.error(f"Campaign.query_rag: Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
                raise ValueError(f"Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
        
            return manager.query(prompt, collection, session, limit=max_results)

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

    def delete_document(self, filename: str, collection_name: str | None = None) -> None:
        """
        Delete a document from the database.
        
        Args:
            filename (str): The name of the document to delete.
            collection_name (str | None): The collection name to use.
                                          If None, the default campaign 
                                          collection will be used.
            
        Returns:
            None

        Raises:
            ValueError: If the collection name is not found or does not belong to the campaign.
            DocumentNotFoundError: If the document is not found.
        """
        if collection_name is None:
            collection = self.default_collection
        else:
            with get_session() as session:
                collection = manager.get_collection(session, collection_name)
                if collection.campaign_id != self.metadata.id:
                    logger.error(f"Campaign.delete_document: Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
                    raise ValueError(f"Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")

        with get_session() as session:
            manager.delete_document(collection, filename, session)
