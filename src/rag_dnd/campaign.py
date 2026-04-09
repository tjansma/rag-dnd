"""Campaign  class containing all services for a campaign."""
import logging
from pathlib import Path
from typing import Self, Any

from sqlalchemy.exc import DatabaseError, InvalidRequestError
from sqlalchemy.orm import Session

from .core import CampaignMetadata
from .game import GameCharacter
from .rag import manager, Collection
from .shared import DocumentExistsError, DuplicateGameCharacterError, \
    GameCharacterOnCampaignCreate, QueryResult, GameCharacterOnCampaignUpdate, \
    GameCharacterNotFoundError

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

    # ==================================================================
    # Game character methods
    # ==================================================================
    def add_gamecharacter(self, 
                          game_character_data: GameCharacterOnCampaignCreate
                         ) -> GameCharacter:
        """
        Add a game character to the campaign.
        
        Args:
            game_character_data (GameCharacterOnCampaignCreate): The game
                character to add.
            
        Returns:
            GameCharacter: The new game character.
        """
        new_character = GameCharacter(campaign_id=self.metadata.id,
                                      **game_character_data.model_dump())
        
        try:
            with self._db_session.begin_nested():
                self._db_session.add(new_character)
                self._db_session.flush()
        except (DatabaseError, InvalidRequestError) as e:
            logger.error(f"Campaign.add_gamecharacter: Error adding game "
                         f"character: {game_character_data.name} in campaign: "
                         f"{self.metadata.short_name}")
            raise DuplicateGameCharacterError(
                f"Game character '{game_character_data.name}' already exists in "
                f"campaign '{self.metadata.short_name}'.")
        
        return new_character

    def get_gamecharacters(self, exclude_inactive: bool = True) -> list[GameCharacter]:
        """
        Get all game characters in the campaign.
        
        Args:
            exclude_inactive (bool): Whether to exclude inactive game characters.
            
        Returns:
            list[GameCharacter]: The game characters.
        """
        if exclude_inactive:
            return [gamechar 
                    for gamechar in self.metadata.characters 
                    if gamechar.is_active]
        else:
            return list(self.metadata.characters)

    def get_gamecharacter_by_name(self, character_name: str, exclude_inactive: bool = True) \
            -> GameCharacter | None:
        """
        Get a game character by name.
        
        Args:
            character_name (str): The name of the game character to get.
            exclude_inactive (bool): Whether to exclude inactive game characters.
            
        Returns:
            GameCharacter | None: The game character, or None if not found.
        """
        for gamechar in self.metadata.characters:
            if gamechar.name == character_name:
                if exclude_inactive and not gamechar.is_active:
                    return None
                return gamechar
        return None

    def get_gamecharacter_by_id(self,
                                character_id: int,
                                exclude_inactive: bool = True) \
            -> GameCharacter | None:
        """
        Get a game character by ID.
        
        Args:
            character_id (int): The ID of the game character to get.
            exclude_inactive (bool): Whether to exclude inactive game characters.
            
        Returns:
            GameCharacter | None: The game character, or None if not found.
        """
        for gamechar in self.metadata.characters:
            if gamechar.id == character_id:
                if exclude_inactive and not gamechar.is_active:
                    return None
                return gamechar
        return None

    def update_gamecharacter(self, 
                             character_id: int,
                             game_character_data: GameCharacterOnCampaignUpdate
                            ) -> GameCharacter:
        """
        Update a game character in the campaign.
        
        Args:
            character_id (int): The ID of the game character to update.
            game_character_data (GameCharacterOnCampaignUpdate): The game
                character data to update.
            
        Returns:
            GameCharacter: The updated game character.
        """
        gamechar = self.get_gamecharacter_by_id(character_id)
        if gamechar is None:
            raise GameCharacterNotFoundError(
                f"Game character with ID '{character_id}' not found in campaign "
                f"'{self.metadata.short_name}'.")
        
        for key, value in game_character_data.model_dump(
            exclude_unset=True
        ).items():
            setattr(gamechar, key, value)
        
        with self._db_session.begin_nested():
            self._db_session.add(gamechar)
            self._db_session.flush()
        
        return gamechar

    def delete_gamecharacter(self, character_id: int) -> None:
        """
        Delete a game character from the campaign.
        
        Args:
            character_id (int): The ID of the game character to delete.
            
        Returns:
            None
        """
        gamechar = self.get_gamecharacter_by_id(character_id, exclude_inactive=False)
        if gamechar is None:
            raise GameCharacterNotFoundError(
                f"Game character with ID '{character_id}' not found in campaign "
                f"'{self.metadata.short_name}'.")

        if not gamechar.is_active:
            return

        with self._db_session.begin_nested():
            gamechar.is_active = False
            self._db_session.flush()
