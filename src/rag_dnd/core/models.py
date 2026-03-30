import logging
from typing import Any, Self

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..config import Config

from .database import get_session
from .exceptions import CampaignNotFoundError

logger = logging.getLogger(__name__)

class ORMBase(orm.DeclarativeBase):
    """Base class for all ORM models."""
    pass


class CampaignMetadata(ORMBase):
    """Class to represent a campaign."""
    __tablename__ = "campaign_metadata"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    full_name: orm.Mapped[str] = orm.mapped_column(sa.String)
    short_name: orm.Mapped[str] = orm.mapped_column(sa.String, unique=True)
    system: orm.Mapped[str] = orm.mapped_column(sa.String)
    language: orm.Mapped[str] = orm.mapped_column(sa.String)
    active_summary_file: orm.Mapped[str | None] = orm.mapped_column(sa.String)
    session_log_file: orm.Mapped[str | None] = orm.mapped_column(sa.String)
    extensions: orm.Mapped[dict[str, Any] | None] = orm.mapped_column(sa.JSON)
    
    @classmethod
    def load_by_id(cls, id: int) -> Self:
        """
        Load campaign metadata by id.

        Args:
            id (int): The id of the campaign metadata to load.

        Returns:
            Self: The campaign metadata.
        """
        with get_session() as session:
            metadata = session.query(cls).filter(cls.id == id).first()
            if metadata is None:
                raise CampaignNotFoundError(f"Campaign with id {id} not found.")

            session.expunge_all()
            return metadata

    @classmethod
    def load_by_short_name(cls, name: str) -> Self:
        """
        Load campaign metadata by name.

        Args:
            name (str): The name of the campaign metadata to load.

        Returns:
            Self: The campaign metadata.
        """
        with get_session() as session:
            metadata = session.query(cls).filter(cls.short_name == name).first()
            if metadata is None:
                raise CampaignNotFoundError(f"Campaign '{name}' not found.")

            session.expunge_all()
            return metadata

    @orm.validates("short_name")
    def validate_short_name(self, key, value) -> str:
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
