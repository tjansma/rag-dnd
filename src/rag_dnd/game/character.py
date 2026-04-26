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
    """
    Represents a game character.
    
    Attributes:
        data (GameCharacter): The character data.
        _database_session (Session): The database session.
    """
    
    def __init__(self, data: GameCharacter, database_session: Session) -> None:
        """
        Create a Character instance.
        
        Args:
            data (GameCharacter): The character data.
            database_session (Session): The database session.
        """
        self.data = data
        self._database_session = database_session

    @property
    def id(self) -> int:
        """
        Get the character ID.
        
        Returns:
            int: The character ID.
        """
        return self.data.id

    @property
    def campaign_id(self) -> int:
        """
        Get the campaign ID.
        
        Returns:
            int: The campaign ID.
        """
        return self.data.campaign_id

    @property
    def all_relationships(self) -> list[CharacterRelationship]:
        """
        Get all relationships for the character.
        
        Returns:
            list[CharacterRelationship]: List of all unique relationships for
                                         the character
        """
        seen = set()
        result = []

        for rel in self.data.from_relationships + self.data.to_relationships:
            if rel.id not in seen:
                seen.add(rel.id)
                result.append(rel)

        return result

    @classmethod
    def from_db_by_id(cls,
                      character_id: int,
                      database_session: Session
                     ) -> Self:
        """
        Create a Character instance from the database by character ID.
        
        Args:
            character_id (int): The ID of the character to retrieve.
            database_session (Session): The database session.
            
        Returns:
            Self: A Character instance.

        Raises:
            GameCharacterNotFoundError: If the character is not found.
        """
        character_data = database_session.get(GameCharacter, character_id)
        if character_data is None:
            raise GameCharacterNotFoundError(
                f"Character with ID {character_id} not found."
            )

        logger.debug(
            f"Character with ID {character_id} retrieved: {character_data.name}"
        )

        return cls(character_data, database_session)

    def add_relationship(self,
                         new_relationship_data: CharacterRelationshipCreate
                        ) -> None:
        """
        Add a relationship to the character.
        
        Args:
            new_relationship_data (CharacterRelationshipCreate): The 
                relationship to add.
            
        Returns:
            None

        Raises:
            DuplicateCharacterRelationshipError: If the relationship already
                exists.
            IllegalCharacterRelationshipError: If the to_character is not in
                the same campaign as the character or the to_character is
                the same as the character.
            GameCharacterNotFoundError: If the to_character is not found.
        """
        to_character = Character.from_db_by_id(
            new_relationship_data.to_character_id,
            self._database_session
        )
        logger.debug(
            f"from={self.data.name} (ID: {self.data.id}), "
            f"to={to_character.data.name} (ID: {to_character.data.id}), "
            f"relationship type={new_relationship_data.relationship_type}"
        )

        if to_character.campaign_id != self.campaign_id:
            raise IllegalCharacterRelationshipError(
                f"Character with ID {to_character.id} does not belong to "
                f"campaign {self.campaign_id}."
            )

        if to_character.id == self.id:
            raise IllegalCharacterRelationshipError(
                f"Character with ID {to_character.id} "
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
            logger.info(
                f"Relationship between {self.data.name} and "
                f"{to_character.data.name} added successfully."
            )
        except IntegrityError as e:
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

        Raises:
            CharacterRelationshipNotFoundError: If the relationship is not found.
            DuplicateCharacterRelationshipError: If the relationship already exists.
        """
        relationship_to_update = next(
            (relationship for relationship in self.data.from_relationships
             if relationship.id == relationship_data.id), 
            None
        )

        if relationship_to_update is None:
            raise CharacterRelationshipNotFoundError(
                f"Relationship with ID {relationship_data.id} not found or doesn't "
                "belong to this character."
            )

        if (
            relationship_data.relationship_type is None 
            and relationship_data.description is None
        ):
            logger.debug(
                f"No data provided to update for "
                f"relationship with ID {relationship_data.id}."
            )
            return
        
        try:
            with self._database_session.begin_nested():
                if relationship_data.relationship_type is not None:
                    relationship_to_update.relationship_type = \
                        relationship_data.relationship_type
                if relationship_data.description is not None:
                    # Replace empty string with None
                    relationship_to_update.description = \
                        relationship_data.description or None
                self._database_session.flush()
            logger.info(
                f"Relationship with ID "
                f"{relationship_data.id} updated successfully."
            )
        except IntegrityError as e:
            raise DuplicateCharacterRelationshipError(
                f"Relationship between {self.data.name} and "
                f"{relationship_to_update.to_character.name} already exists."
            ) from e

    def delete_relationship(self, relationship_id: int) -> None:
        """
        Delete a relationship.
        
        Args:
            relationship_id (int): The ID of the relationship to delete.
            
        Returns:
            None
        """
        relationship_to_delete = next(
            (relationship for relationship in self.data.from_relationships
             if relationship.id == relationship_id), 
            None
        )
        if relationship_to_delete is None:
            raise CharacterRelationshipNotFoundError(
                f"Relationship with ID {relationship_id} not found or doesn't "
                f"belong to character {self.data.name}."
            )
        
        with self._database_session.begin_nested():
            self._database_session.delete(relationship_to_delete)
            self._database_session.flush()

        logger.info(
            f"Relationship with ID {relationship_id} "
            f"deleted successfully."
        )
