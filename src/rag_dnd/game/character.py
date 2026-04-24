import logging
from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..shared import \
    DuplicateCharacterRelationshipError, \
    CharacterRelationshipNotFoundError, \
    CharacterRelationshipCreate, \
    CharacterRelationshipUpdate, \
    GameCharacterNotFoundError, \
    IllegalCharacterRelationshipError

from .models import GameCharacter, CharacterRelationship

logger = logging.getLogger(__name__)

class Character:
    def __init__(self, data: GameCharacter, database_session: Session):
        self.data = data
        self._database_session = database_session

    @property
    def id(self) -> int:
        return self.data.id

    @property
    def campaign_id(self) -> int:
        return self.data.campaign_id

    @property
    def relationships(self) -> list[CharacterRelationship]:
        return list(set(self.data.from_relationships + self.data.to_relationships))

    @classmethod
    def from_db_by_id(cls, character_id: int, database_session: Session) -> Self:
        """
        Create a Character instance from the database by character ID.
        
        Args:
            character_id (int): The ID of the character to retrieve.
            database_session (Session): The database session.
            
        Returns:
            Self: A Character instance.
        """
        character_data = database_session.query(GameCharacter).get(character_id)
        if character_data is None:
            raise GameCharacterNotFoundError(
                f"Character with ID {character_id} not found."
            )
        return cls(character_data, database_session)

    def add_relationship(self,
                         new_relationship_data: CharacterRelationshipCreate
                        ) -> None:
        """
        Add a relationship to the character.
        
        Args:
            new_relationship_data (CharacterRelationshipCreate): The relationship to add.
            
        Returns:
            None
        """
        logger.info(
            f"Adding relationship between {self.data.name} and "
            f"{new_relationship_data.to_character_id}."
        )
        logger.debug(
            f"Relationship data: {new_relationship_data}"
        )

        to_character = Character.from_db_by_id(
            new_relationship_data.to_character_id,
            self._database_session
        )
        
        if to_character.campaign_id != self.campaign_id:
            logger.error(
                f"Character with ID {new_relationship_data.to_character_id} "
                f"does not belong to campaign {self.campaign_id}."
            )
            raise IllegalCharacterRelationshipError(
                f"Character with ID {new_relationship_data.to_character_id} "
                f"does not belong to campaign {self.campaign_id}."
            )
            
        if to_character.id == self.id:
            logger.error(
                f"Character with ID {new_relationship_data.to_character_id} "
                f"cannot have a relationship with itself."
            )
            raise IllegalCharacterRelationshipError(
                f"Character with ID {new_relationship_data.to_character_id} "
                f"cannot have a relationship with itself."
            )

        new_relationship = CharacterRelationship(
            to_character=to_character.data,
            relationship_type=new_relationship_data.relationship_type,
            description=new_relationship_data.description
        )
        try:
            with self._database_session.begin_nested():
                self.data.from_relationships.append(new_relationship)
                self._database_session.flush()
            logger.debug(
                f"Relationship between {self.data.name} and "
                f"{to_character.data.name} added successfully."
            )
        except IntegrityError as e:
            logger.error(f"Duplicate relationship detected: {e}")
            raise DuplicateCharacterRelationshipError(
                f"Relationship between {self.data.name} and "
                f"{to_character.data.name} already exists."
            ) from e

    def update_relationship(self,
                            relationship_data: CharacterRelationshipUpdate
                            ) -> None:
        """
        Update a relationship.
        
        Args:
            relationship_data (CharacterRelationshipUpdate): The relationship to update.
            
        Returns:
            None
        """
        logger.info(
            f"Updating relationship with ID {relationship_data.id} for character "
            f"{self.data.name}."
        )
        logger.debug(
            f"Relationship data: {relationship_data}"
        )
        relationship_to_update = next(
            (relationship for relationship in self.data.from_relationships
             if relationship.id == relationship_data.id), 
            None
        )
        if relationship_to_update is None:
            logger.error(
                f"Relationship with ID {relationship_data.id} not found."
            )
            raise CharacterRelationshipNotFoundError(
                f"Relationship with ID {relationship_data.id} not found or doesn't "
                "belong to this character."
            )

        if (
            relationship_data.relationship_type is None 
            and relationship_data.description is None
        ):
            logger.debug(
                f"No data provided to update for relationship with ID "
                f"{relationship_data.id}."
            )
            return
        
        try:
            with self._database_session.begin_nested():
                if relationship_data.relationship_type is not None:
                    relationship_to_update.relationship_type = \
                        relationship_data.relationship_type
                if relationship_data.description is not None:
                    relationship_to_update.description = \
                        relationship_data.description or None
                self._database_session.flush()
            logger.debug(
                f"Relationship with ID {relationship_data.id} updated successfully."
            )
        except IntegrityError as e:
            logger.error(
                f"Duplicate relationship detected: {e}"
            )
            raise DuplicateCharacterRelationshipError(
                f"Relationship between {self.data.name} and "
                f"{relationship_to_update.to_character.name} already exists."
            ) from e
        except Exception as e:
            logger.error(
                f"Error updating relationship: {e}"
            )
            raise

    def delete_relationship(self, relationship_id: int) -> None:
        """
        Delete a relationship.
        
        Args:
            relationship_id (int): The ID of the relationship to delete.
            
        Returns:
            None
        """
        logger.info(
            f"Deleting relationship with ID {relationship_id} for character "
            f"{self.data.name}."
        )
        logger.debug(
            f"Relationship ID: {relationship_id}"
        )
        relationship_to_delete = next(
            (relationship for relationship in self.data.from_relationships
             if relationship.id == relationship_id), 
            None
        )
        if relationship_to_delete is None:
            logger.error(
                f"Relationship with ID {relationship_id} not found for character "
                f"{self.data.name}."
            )
            raise CharacterRelationshipNotFoundError(
                f"Relationship with ID {relationship_id} not found or doesn't "
                f"belong to character {self.data.name}."
            )
        
        try:
            with self._database_session.begin_nested():
                self._database_session.delete(relationship_to_delete)
                self._database_session.flush()
            logger.debug(
                f"Relationship with ID {relationship_id} deleted successfully."
            )
        except Exception as e:
            logger.error(
                f"Error deleting relationship: {e}"
            )
            raise
