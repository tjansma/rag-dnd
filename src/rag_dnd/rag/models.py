"""Models for the database."""
from __future__ import annotations
from typing import Optional, Any, Self
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..config import Config
from .database import get_session

class ORMBase(orm.DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Collection(ORMBase):
    """Class to represent a collection of documents."""
    __tablename__ = "collections"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sa.String)
    campaign_id: orm.Mapped[int | None] = \
        orm.mapped_column(sa.Integer, sa.ForeignKey("campaign_metadata.id"))

    campaign: orm.Mapped["CampaignMetadata"] = orm.relationship(
        back_populates="collections")
    documents: orm.Mapped[list["Document"]] = \
        orm.relationship(back_populates="collection")

class Document(ORMBase):
    """Class to represent a document."""
    __tablename__ = "documents"
    __table_args__ = (
        sa.UniqueConstraint("collection_id", "file_hash",
                            name="uq_collection_file_hash"),
        sa.UniqueConstraint("collection_id", "custom_filename",
                            name="uq_collection_custom_filename"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    file_name: orm.Mapped[str] = orm.mapped_column(sa.String)
    file_hash: orm.Mapped[str] = orm.mapped_column(sa.String, index=True)
    custom_filename: orm.Mapped[str] = orm.mapped_column(sa.String, index=True)
    collection_id: orm.Mapped[int] = \
        orm.mapped_column(sa.Integer, sa.ForeignKey("collections.id"))
    
    collection: orm.Mapped["Collection"] = orm.relationship(
        back_populates="documents")
    chunks: orm.Mapped[list["Chunk"]] = orm.relationship(
        back_populates="parent_document",
        cascade="all, delete-orphan"
    )


@dataclass
class Sentence:
    """Class to represent a sentence."""
    chunk: "Chunk"
    text: str
    embedding_vector: Optional[list[float]] = None


class Chunk(ORMBase):
    """Class to represent a chunk of a document."""
    __tablename__ = "chunks"
    __allow_unmapped__ = True

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    document_id: orm.Mapped[int] = \
        orm.mapped_column(sa.Integer, sa.ForeignKey("documents.id"))
    text: orm.Mapped[str] = orm.mapped_column(sa.String)
    chunk_hash: orm.Mapped[str] = orm.mapped_column(sa.String, unique=True)
    
    parent_document: orm.Mapped["Document"] = \
        orm.relationship(back_populates="chunks")

    # This is not a mapped column, but a list of sentences
    sentences: list["Sentence"]

    def __str__(self) -> str:
        """
        Return a string representation of the chunk.

        Returns:
            str: The text of the chunk.
        """
        return self.text


@dataclass
class QueryResult:
    """Class to represent a query result."""
    text: str
    source_document: str


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
    
    collections: orm.Mapped[list["Collection"]] = orm.relationship(
        back_populates="campaign")

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
        if "!" in value:
            raise ValueError("Short name cannot contain '!'")
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
        return f"{self.short_name}!{config.embeddings_model}"
