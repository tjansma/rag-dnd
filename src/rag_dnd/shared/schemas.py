from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ConfigDict

from .enums import PlayerType, CharacterType, Disposition


# ===========================================================================
# Player schemas
# ===========================================================================
# Player create schemas
# ---------------------------------------------------------------------------
class PlayerCreateBase(BaseModel):
    """
    Base schema for creating a player.

    Attributes:
        name: Player name
    """
    name: str = Field(..., description="Player name")

    model_config = ConfigDict(extra="forbid")


class HumanPlayerCreate(PlayerCreateBase):
    """
    Schema for creating a human player.

    Attributes:
        player_type: Player type
        email: Human player email
        age: Human player age
        gender: Human player gender
        availability: Human player availability
        notes: Human player notes
    """
    player_type: Literal[PlayerType.HUMAN] = Field(PlayerType.HUMAN, frozen=True)
    email: str = Field(..., description="Human player email")
    age: int | None = Field(None, description="Human player age")
    gender: str | None = Field(None, description="Human player gender")
    availability: str | None = Field(None,
        description="Human player availability")
    notes: str | None = Field(None, description="Human player notes")


class AIPlayerCreate(PlayerCreateBase):
    """
    Schema for creating an AI player.

    Attributes:
        player_type: Player type
        ai_provider: AI provider
        ai_model: AI model
        system_prompt: System prompt
        temperature: AI Temperature (controls randomness of AI responses)
    """
    player_type: Literal[PlayerType.AI] = Field(PlayerType.AI, frozen=True)
    ai_provider: str = Field(..., description="AI provider")
    ai_model: str = Field(..., description="AI model")
    system_prompt: str | None = Field(None, description="System prompt")
    temperature: float | None = Field(None,
        description="AI Temperature (controls randomness of AI responses)")


PlayerCreateSchema = Annotated[
    HumanPlayerCreate | AIPlayerCreate,
    Field(discriminator="player_type")
]


# ---------------------------------------------------------------------------
# Player response schemas
# ---------------------------------------------------------------------------
class PlayerResponseBase(BaseModel):
    """
    Base schema for player response.

    Attributes:
        id: Player ID
        name: Player name
    """
    id: int = Field(..., description="Player ID")
    name: str = Field(..., description="Player name")
    
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class HumanPlayerResponse(PlayerResponseBase):
    """
    Schema for human player response.

    Attributes:
        player_type: Player type
        email: Human player email
        age: Human player age
        gender: Human player gender
        availability: Human player availability
        notes: Human player notes
    """
    player_type: Literal[PlayerType.HUMAN] = Field(PlayerType.HUMAN, frozen=True)
    email: str = Field(..., description="Human player email")
    age: int | None = Field(None, description="Human player age")
    gender: str | None = Field(None, description="Human player gender")
    availability: str | None = Field(None,
        description="Human player availability")
    notes: str | None = Field(None, description="Human player notes")


class AIPlayerResponse(PlayerResponseBase):
    """
    Schema for AI player response.

    Attributes:
        player_type: Player type
        ai_provider: AI provider
        ai_model: AI model
        system_prompt: System prompt
        temperature: AI Temperature (controls randomness of AI responses)
    """
    player_type: Literal[PlayerType.AI] = Field(PlayerType.AI, frozen=True)
    ai_provider: str = Field(..., description="AI provider")
    ai_model: str = Field(..., description="AI model")
    system_prompt: str | None = Field(None, description="System prompt")
    temperature: float | None = Field(None,
        description="AI Temperature (controls randomness of AI responses)")


PlayerResponseSchema = Annotated[
    HumanPlayerResponse | AIPlayerResponse,
    Field(discriminator="player_type")
]

# ---------------------------------------------------------------------------
# Campaign schemas
# ---------------------------------------------------------------------------

class GameCharacterOnCampaignCreate(BaseModel):
    """
    Schema for creating a game character.

    Attributes:
        name: Character name
        category: Character category
        race (optional): Character race
        gender (optional): Character gender
        age (optional): Character age
        sexual_orientation (optional): Character sexual orientation
        alignment (optional): Character alignment
        occupation (optional): Character occupation
        is_active (optional): Character is active
        is_alive (optional): Character is alive
        location (optional): Character location
        faction (optional): Character faction
        disposition (optional): Character disposition
        known_by_party (optional): Character is known by party
        description (optional): Character description
        data (optional): Character data
    """
    name: str = Field(..., description="Character name")
    category: CharacterType = Field(..., description="Character category")
    race: str | None = Field(None, description="Character race")
    gender: str | None = Field(None, description="Character gender")
    age: int | None = Field(None, description="Character age")
    sexual_orientation: str | None = Field(None,
        description="Character sexual orientation")
    alignment: str | None = Field(None, description="Character alignment")
    occupation: str | None = Field(None, description="Character occupation")
    is_active: bool = Field(True, description="Character is active")
    is_alive: bool = Field(True, description="Character is alive")
    location: str | None = Field(None, description="Character location")
    faction: str | None = Field(None, description="Character faction")
    disposition: Disposition | None = Field(None,
        description="Character disposition")
    known_by_party: bool = Field(False, description="Character is known by party")
    description: str | None = Field(None, description="Character description")
    data: Any | None = Field(None, description="Character data")

    model_config = ConfigDict(extra="forbid")


class GameCharacterOnCampaignUpdate(BaseModel):
    """
    Schema for updating a game character.

    Attributes:
        category (optional): Character category
        race (optional): Character race
        gender (optional): Character gender
        age (optional): Character age
        sexual_orientation (optional): Character sexual orientation
        alignment (optional): Character alignment
        occupation (optional): Character occupation
        is_active (optional): Character is active
        is_alive (optional): Character is alive
        location (optional): Character location
        faction (optional): Character faction
        disposition (optional): Character disposition
        known_by_party (optional): Character is known by party
        description (optional): Character description
        data (optional): Character data
    """
    category: CharacterType | None = Field(None, description="Character category")
    race: str | None = Field(None, description="Character race")
    gender: str | None = Field(None, description="Character gender")
    age: int | None = Field(None, description="Character age")
    sexual_orientation: str | None = Field(None,
        description="Character sexual orientation")
    alignment: str | None = Field(None, description="Character alignment")
    occupation: str | None = Field(None, description="Character occupation")
    is_active: bool | None = Field(None, description="Character is active")
    is_alive: bool | None = Field(None, description="Character is alive")
    location: str | None = Field(None, description="Character location")
    faction: str | None = Field(None, description="Character faction")
    disposition: Disposition | None = Field(None,
        description="Character disposition")
    known_by_party: bool | None = Field(None, description="Character is known by party")
    description: str | None = Field(None, description="Character description")
    data: Any | None = Field(None, description="Character data")

    model_config = ConfigDict(extra="forbid")


class GameCharacterOnCampaignResponse(BaseModel):
    """
    Schema for game character response.

    Attributes:
        id: Character ID
        name: Character name
        category: Character category
        race: Character race
        gender: Character gender
        age: Character age
        sexual_orientation: Character sexual orientation
        alignment: Character alignment
        occupation: Character occupation
        is_active: Character is active
        is_alive: Character is alive
        location: Character location
        faction: Character faction
        disposition: Character disposition
        known_by_party: Character is known by party
        description: Character description
        data: Character data
        campaign_id: Campaign ID
    """
    id: int = Field(..., description="Character ID")
    name: str = Field(..., description="Character name")
    category: CharacterType = Field(..., description="Character category")
    race: str | None = Field(None, description="Character race")
    gender: str | None = Field(None, description="Character gender")
    age: int | None = Field(None, description="Character age")
    sexual_orientation: str | None = Field(None,
        description="Character sexual orientation")
    alignment: str | None = Field(None, description="Character alignment")
    occupation: str | None = Field(None, description="Character occupation")
    is_active: bool = Field(True, description="Character is active")
    is_alive: bool = Field(True, description="Character is alive")
    location: str | None = Field(None, description="Character location")
    faction: str | None = Field(None, description="Character faction")
    disposition: Disposition | None = Field(None,
        description="Character disposition")
    known_by_party: bool = Field(False, description="Character is known by party")
    description: str | None = Field(None, description="Character description")
    data: Any | None = Field(None, description="Character data")
    campaign_id: int = Field(..., description="Campaign ID")

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# ===========================================================================
# RAG schemas
# ===========================================================================
# RAG query result schemas
# ---------------------------------------------------------------------------
@dataclass
class QueryResult:
    """Class to represent a query result."""
    text: str
    source_document: str
