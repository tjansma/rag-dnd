import logging
from typing import Any, Self

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..config import Config

from .exceptions import CampaignNotFoundError

logger = logging.getLogger(__name__)

class ORMBase(orm.DeclarativeBase):
    """Base class for all ORM models."""
    pass


class CampaignMetadata(ORMBase):
    """Class to represent a campaign."""
    __tablename__ = "campaign_metadata"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        primary_key=True,
        comment="Campaign ID")
    full_name: orm.Mapped[str] = orm.mapped_column(sa.String,
        comment="Campaign full name")
    short_name: orm.Mapped[str] = orm.mapped_column(sa.String,
        unique=True,
        comment="Campaign short name")
    system: orm.Mapped[str] = orm.mapped_column(sa.String,
        comment="Campaign system")
    language: orm.Mapped[str] = orm.mapped_column(sa.String,
        comment="Campaign language")
    active_summary_file: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        comment="Active summary file")
    session_log_file: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        comment="Session log file")
    current_ingame_date: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        nullable=True,
        comment="Current ingame date")
    latest_session_id: orm.Mapped[int | None] = orm.mapped_column(
        sa.ForeignKey("game_sessions.id"),
        nullable=True,
        comment="Latest session id")
    extensions: orm.Mapped[dict[str, Any] | None] = orm.mapped_column(
        sa.JSON,
        comment="Campaign extensions")
    # pyrefly: ignore[unknown-name]
    latest_session: orm.Mapped["GameSession"] = orm.relationship(
        "GameSession",
        foreign_keys=[latest_session_id],
        uselist=False)
    system_prompt_extension: orm.Mapped[str | None] = orm.mapped_column(
        sa.String,
        comment="System prompt extension, added to model's system prompt")
    
    @classmethod
    def load_by_id(cls,
                   database_session: orm.Session,
                   id: int
                  ) -> Self:
        """
        Load campaign metadata by id.

        Args:
            database_session (Session): The database session.
            id (int): The id of the campaign metadata to load.

        Returns:
            Self: The campaign metadata.
        """
        metadata = database_session.query(cls).filter(cls.id == id).first()
        if metadata is None:
            raise CampaignNotFoundError(f"Campaign with id {id} not found.")

        return metadata

    @classmethod
    def load_by_short_name(cls,
                           database_session: orm.Session,
                           name: str
                          ) -> Self:
        """
        Load campaign metadata by name.

        Args:
            database_session (Session): The database session.
            name (str): The name of the campaign metadata to load.

        Returns:
            Self: The campaign metadata.
        """
        metadata = database_session.query(cls).filter(cls.short_name == name).first()
        if metadata is None:
            raise CampaignNotFoundError(f"Campaign '{name}' not found.")

        return metadata

    @orm.validates("short_name")
    def validate_short_name(self, key: str, value: str) -> str:
        """
        Validate the short name.

        Args:
            key (str): The key to validate.
            value (str): The value to validate.

        Returns:
            str: The validated value.
        """
        if "_-_" in value or "/" in value:
            raise ValueError("Short name cannot contain '_-_' or '/'")
        return value

    def get_default_collection_name(self, config: Config | None = None) -> str:
        """
        Get the name of the collection.

        Args:
            config (Config | None): The configuration to use. If None, the
                                    default configuration will be used.

        Returns:
            str: The name of the collection.
        """
        if config is None:
            config = Config.load()
        sanitized_model_name = config.embeddings_model.replace("/", "_")
        return f"{self.short_name}_-_{sanitized_model_name}"
