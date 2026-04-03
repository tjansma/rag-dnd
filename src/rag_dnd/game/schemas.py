from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, ConfigDict

from .enums import PlayerType


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
    temperature: float = Field(0.7,
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
    temperature: float = Field(0.7,
        description="AI Temperature (controls randomness of AI responses)")


PlayerResponseSchema = Annotated[
    HumanPlayerResponse | AIPlayerResponse,
    Field(discriminator="player_type")
]
