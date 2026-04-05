"""Campaign  class containing all services for a campaign."""
import logging
from pathlib import Path
from typing import Self, Any

from sqlalchemy.orm import Session

from .core import CampaignMetadata
from .rag import manager
from .rag.exceptions import DocumentExistsError
from .rag.models import QueryResult, Collection

logger = logging.getLogger(__name__)

class Campaign:
    """Class to represent a campaign."""
    # --- Constructor ---
    def __init__(self, 
                 metadata: CampaignMetadata,
                 database_session: Session) -> None:
        """Initialize the campaign.
        
        Args:
            metadata (CampaignMetadata): The campaign metadata.
            
        Returns:
            None
        """
        self.metadata: CampaignMetadata = metadata
        self._db_session: Session = database_session
        self.default_collection: Collection = \
            manager.ensure_collection(database_session,
                                      metadata.get_default_collection_name(),
                                      metadata.id)

    # --- Class methods ---
    @classmethod
    def create(cls,
               database_session: Session,
               full_name:str,
               short_name: str,
               roleplay_system: str,
               language: str,
               active_summary_file: str | None,
               session_log_file: str | None,
               extensions: dict[str, Any] | None) -> Self:
        """Create a new campaign.
        
        Args:
            database_session (Session): The database session.
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
        campaign_metadata = CampaignMetadata(
            full_name=full_name,
            short_name=short_name,
            system=roleplay_system,
            language=language,
            active_summary_file=active_summary_file,
            session_log_file=session_log_file,
            extensions=extensions
        )
        database_session.add(campaign_metadata)
        database_session.flush()

        return cls(campaign_metadata, database_session)

    @classmethod
    def list_all(cls, database_session: Session) -> list[Self]:
        """List all campaigns.
        
        Args:
            database_session (Session): The database session.
            
        Returns:
            list[Self]: The list of campaigns.
        """
        campaign_metadata = database_session.query(CampaignMetadata).all()
            
        return [cls(metadata, database_session) for metadata in campaign_metadata]


    @classmethod
    def from_db_by_short_name(cls,
                              database_session: Session,
                              short_name: str) -> Self:
        """Load campaign metadata by short name.
        
        Args:
            database_session (Session): The database session.
            short_name (str): The short name of the campaign.
            
        Returns:
            Self: The campaign.
        """
        campaign_metadata = CampaignMetadata.load_by_short_name(
            database_session, 
            short_name
        )
        return cls(campaign_metadata, database_session)

    @classmethod
    def from_db_by_id(cls, database_session: Session, id: int) -> Self:
        """Load campaign metadata by id.
        
        Args:
            database_session (Session): The database session.
            id (int): The id of the campaign.
            
        Returns:
            Self: The campaign.
        """
        campaign_metadata = CampaignMetadata.load_by_id(database_session, id)
        return cls(campaign_metadata, database_session)
    
    # --- Methods ---
    def query_rag(self, prompt: str,
                  collection_name: str | None = None,
                  max_results: int = 5) -> list[QueryResult]:
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
        
        collection = manager.get_collection(self._db_session, collection_name)
        if collection.campaign_id != self.metadata.id:
            logger.error(f"Campaign.query_rag: Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
            raise ValueError(f"Collection '{collection_name}' does not belong to campaign '{self.metadata.short_name}'.")
        
        return manager.query(prompt, collection, self._db_session, limit=max_results)

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
            collection = manager.get_collection(self._db_session,
                                                collection_name)
            if collection.campaign_id != self.metadata.id:
                logger.error(f"Campaign.store_document: Collection "
                             f"'{collection_name}' does not belong to campaign "
                             f"'{self.metadata.short_name}'.")
                raise ValueError(f"Collection '{collection_name}' does not "
                                 f"belong to campaign "
                                 f"'{self.metadata.short_name}'.")

        try:
            manager.store_document(collection,
                                   filename,
                                   self._db_session,
                                   custom_filename=custom_filename)
        except DocumentExistsError:
            manager.update_document(collection,
                                    filename,
                                    self._db_session,
                                    custom_filename=custom_filename)

    def delete_document(self,
                        filename: str,
                        collection_name: str | None = None) -> None:
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
            collection = manager.get_collection(self._db_session,
                                                collection_name)
            if collection.campaign_id != self.metadata.id:
                logger.error(f"Campaign.delete_document: Collection "
                             f"'{collection_name}' does not belong to campaign "
                             f"'{self.metadata.short_name}'.")
                raise ValueError(f"Collection '{collection_name}' does not "
                                 f"belong to campaign "
                                 f"'{self.metadata.short_name}'.")

        manager.delete_document(collection,
                                filename,
                                self._db_session)
