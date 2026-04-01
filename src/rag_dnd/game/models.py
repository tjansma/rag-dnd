"""Data models for the game."""
from datetime import datetime
import logging
from pathlib import Path
from typing import Any

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..core import ORMBase, CampaignMetadata

from .enums import *

logger = logging.getLogger(__name__)


class Player(ORMBase):
    """Player model."""
    __tablename__ = "players"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True,
                                            comment="Player ID")
    name: orm.Mapped[str] = orm.mapped_column(sa.String,
                                              nullable=False,
                                              unique=True,
                                              comment="Player name")
    player_type: orm.Mapped[PlayerType] = orm.mapped_column(
                                              sa.Enum(PlayerType),
                                              nullable=False,
                                              comment="Player type"
                                          )
    ai_model: orm.Mapped[str | None] = orm.mapped_column(sa.String,
                                                         nullable=True,
                                                         comment="AI model")


class GameCharacter(ORMBase):
    """Game character model."""
    __tablename__ = "game_characters"

    __table_args__ = (
        sa.UniqueConstraint("name", 
                            "campaign_id", 
                            name="uniq_charactername_per_campaign"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Character ID")
    name: orm.Mapped[str] = orm.mapped_column(sa.String, 
                                              comment="Character name")
    category: orm.Mapped[CharacterType] = orm.mapped_column(
        sa.Enum(CharacterType), 
        comment="Character category")
    race: orm.Mapped[str | None] = orm.mapped_column(sa.String, 
                                                      nullable=True, 
                                                      comment="Character race")
    gender: orm.Mapped[str | None] = orm.mapped_column(sa.String, 
                                         nullable=True, 
                                         comment="Character gender")
    age: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, 
                                                    nullable=True, 
                                                    comment="Character age")
    sexual_orientation: orm.Mapped[str | None] = orm.mapped_column(sa.String,
        nullable=True,
        comment="Character sexual orientation")
    alignment: orm.Mapped[str | None] = orm.mapped_column(sa.String,
                                            nullable=True,
                                            comment="Character alignment")
    occupation: orm.Mapped[str | None] = orm.mapped_column(sa.String,
                                            nullable=True,
                                            comment="Character occupation")
    is_active: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, 
                                      default=True, 
                                      comment="Character is active")
    is_alive: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, 
                                      default=True, 
                                      comment="Character is alive")
    location: orm.Mapped[str | None] = orm.mapped_column(sa.String,
                                            nullable=True,
                                            comment="Character location")
    faction: orm.Mapped[str | None] = orm.mapped_column(sa.String,
                                            nullable=True,
                                            comment="Character faction")
    disposition: orm.Mapped[Disposition | None] = orm.mapped_column(
        sa.Enum(Disposition), nullable=True,
        comment="Character disposition")
    known_by_party: orm.Mapped[bool] = orm.mapped_column(sa.Boolean,
        default=False,
        comment="Character is known by party")
    description: orm.Mapped[str | None] = orm.mapped_column(sa.String,
        nullable=True,
        comment="Character description")
    data: orm.Mapped[Any | None] = orm.mapped_column(sa.JSON, nullable=True,
                                                     comment="Character data")
    campaign_id: orm.Mapped[int] = orm.mapped_column(
                                        sa.Integer,
                                        sa.ForeignKey("campaign_metadata.id"),
                                        nullable=False,
                                        comment="Campaign ID"
                                    )

    campaign: orm.Mapped[CampaignMetadata] = \
        orm.relationship("CampaignMetadata", backref="characters")


class CharacterRelationship(ORMBase):
    """Character relationship model."""
    __tablename__ = "character_relationships"

    __table_args__ = (
        sa.UniqueConstraint("from_character_id", 
                            "to_character_id", 
                            "relationship_type",
                            name="uniq_relationship_type_among_characters"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Relationship ID")
    
    # The character who has the relationship
    from_character_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_characters.id"),
        comment="The character who has the relationship")
    # The character who is the target of the relationship
    to_character_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_characters.id"),
        comment="The character who is the target of the relationship")
    
    # The type of relationship
    relationship_type: orm.Mapped[RelationshipType] = orm.mapped_column(
        sa.Enum(RelationshipType), comment="The type of relationship")
    # A description of the relationship
    description: orm.Mapped[str | None] = orm.mapped_column(sa.String,
        nullable=True,
        comment="A description of the relationship")

    from_character: orm.Mapped[GameCharacter] = orm.relationship(
        "GameCharacter",
        foreign_keys=[from_character_id],
        backref="from_relationships"
    )
    to_character: orm.Mapped[GameCharacter] = orm.relationship(
        "GameCharacter",
        foreign_keys=[to_character_id],
        backref="to_relationships"
    )


class PlayerCharacter(ORMBase):
    """Player character model."""
    __tablename__ = "player_characters"

    __table_args__ = (
        sa.UniqueConstraint("player_id", 
                            "character_id", 
                            "session_id",
                            name="uniq_player_character_session"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Player character ID")
    player_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("players.id"),
        comment="Player ID")
    character_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_characters.id"),
        comment="Character ID")
    session_id: orm.Mapped[int | None] = orm.mapped_column(
        sa.ForeignKey("game_sessions.id"), 
        nullable=True,
        comment="Session ID, NULL for default campaign character, "
                "not NULL for session-specific character")

    player: orm.Mapped[Player] = orm.relationship(
        "Player",
        backref="player_characters"
    )
    character: orm.Mapped[GameCharacter] = orm.relationship(
        "GameCharacter",
        backref="player_characters"
    )
    session: orm.Mapped["GameSession"] = orm.relationship(
        "GameSession",
        backref="player_characters"
    )


class ChunkCharacter(ORMBase):
    __tablename__ = "chunk_characters"

    __table_args__ = (
        sa.UniqueConstraint("chunk_id", 
                            "character_id",
                            name="uniq_chunk_character"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Chunk character ID")
    chunk_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("chunks.id"),
        comment="Chunk ID")
    character_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_characters.id"),
        comment="Character ID")
    
    chunk: orm.Mapped["Chunk"] = orm.relationship(
        "Chunk",
        backref="chunk_characters"
    )
    character: orm.Mapped[GameCharacter] = orm.relationship(
        "GameCharacter",
        backref="chunk_characters"
    )


class GameSession(ORMBase):
    __tablename__ = "game_sessions"

    __table_args__ = (
        sa.UniqueConstraint("campaign_id", 
                            "campaign_session",
                            name="uniq_campaign_session"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Session ID")
    campaign_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("campaign_metadata.id"),
        comment="Campaign ID")
    campaign_session: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, 
        comment="Session number within the campaign")
    guid: orm.Mapped[str] = orm.mapped_column(sa.String,
        unique=True,
        comment="Session GUID")
    session_date: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        comment="Session date")
    title: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Session title")
    summary: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Session summary in markdown format")

    campaign: orm.Mapped[CampaignMetadata] = orm.relationship(
        "CampaignMetadata",
        backref="sessions",
        foreign_keys=[campaign_id]
    )


class Turn(ORMBase):
    __tablename__ = "turns"

    __table_args__ = (
        sa.UniqueConstraint("session_id", 
                            "turn_number",
                            name="uniq_session_turn"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Turn ID")
    session_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_sessions.id"),
        comment="Session ID")
    turn_number: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, 
        comment="Turn number within the session")
    timestamp: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        comment="Turn timestamp")
    player_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("players.id"),
        comment="Player ID")
    content: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        comment="Turn content")
    
    session: orm.Mapped[GameSession] = orm.relationship(
        "GameSession",
        backref="turns"
    )
    player: orm.Mapped[Player] = orm.relationship(
        "Player",
        backref="turns"
    )


class TurnCharacter(ORMBase):
    __tablename__ = "turn_characters"

    __table_args__ = (
        sa.UniqueConstraint("turn_id", 
                            "character_id",
                                "role",
                            name="uniq_turn_character_role"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Turn character ID")
    turn_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("turns.id"),
        comment="Turn ID")
    character_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_characters.id"),
        comment="Character ID")
    role: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        comment="Character role in the turn")
    description: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Description of the character's actions in the turn")

    turn: orm.Mapped[Turn] = orm.relationship(
        "Turn",
        backref="turn_characters"
    )
    character: orm.Mapped[GameCharacter] = orm.relationship(
        "GameCharacter",
        backref="turn_characters"
    )

class Asset(ORMBase):
    __tablename__ = "assets"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Asset ID")
    title: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        comment="Asset title")
    uri: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        comment="Asset URI (server filesystem path or URL)")
    asset_type: orm.Mapped[AssetType] = orm.mapped_column(
        sa.Enum(AssetType),
        comment="Asset type")
    mime_type: orm.Mapped[str] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Asset mime type")
    description: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Asset description")
    tags: orm.Mapped[list[str] | None] = orm.mapped_column(
        sa.JSON,
        nullable=True,
        comment="Asset tags")
    created: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        comment="Asset creation date")
    last_updated: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
        comment="Asset last updated date")


class CampaignAsset(ORMBase):
    __tablename__ = "campaign_assets"

    __table_args__ = (
        sa.UniqueConstraint("campaign_id", 
                            "asset_id",
                            name="uniq_campaign_asset"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Campaign asset ID")
    campaign_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("campaign_metadata.id"),
        comment="Campaign ID")
    asset_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("assets.id"),
        comment="Asset ID")
    description: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Description of the asset in the campaign")
    
    campaign: orm.Mapped[CampaignMetadata] = orm.relationship(
        "CampaignMetadata",
        backref="campaign_assets"
    )
    asset: orm.Mapped[Asset] = orm.relationship(
        "Asset",
        backref="campaign_assets"
    )


class SessionAsset(ORMBase):
    __tablename__ = "session_assets"

    __table_args__ = (
        sa.UniqueConstraint("session_id", 
                            "asset_id",
                            name="uniq_session_asset"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Session asset ID")
    session_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_sessions.id"),
        comment="Session ID")
    asset_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("assets.id"),
        comment="Asset ID")
    description: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Description of the asset in the session")
    
    session: orm.Mapped[GameSession] = orm.relationship(
        "GameSession",
        backref="session_assets"
    )
    asset: orm.Mapped[Asset] = orm.relationship(
        "Asset",
        backref="session_assets"
    )


class CharacterAsset(ORMBase):
    __tablename__ = "character_assets"

    __table_args__ = (
        sa.UniqueConstraint("character_id", 
                            "asset_id",
                            name="uniq_character_asset"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
                                            primary_key=True, 
                                            comment="Character asset ID")
    character_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("game_characters.id"),
        comment="Character ID")
    asset_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("assets.id"),
        comment="Asset ID")
    description: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Description of the asset for the character")
    
    character: orm.Mapped[GameCharacter] = orm.relationship(
        "GameCharacter",
        backref="character_assets"
    )
    asset: orm.Mapped[Asset] = orm.relationship(
        "Asset",
        backref="character_assets"
    )
