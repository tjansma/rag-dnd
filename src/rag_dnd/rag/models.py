"""Models for the database."""
from __future__ import annotations
import logging
from typing import Optional, Self
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..core import ORMBase, CampaignMetadata

from .exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class Collection(ORMBase):
    """Class to represent a collection of documents."""
    __tablename__ = "collections"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sa.String)
    campaign_id: orm.Mapped[int] = \
        orm.mapped_column(sa.Integer, sa.ForeignKey("campaign_metadata.id"))

    campaign: orm.Mapped[CampaignMetadata] = orm.relationship(
        backref="collections")
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

    @classmethod
    def load_by_custom_filename(cls, custom_filename: str, collection_id: int, session: orm.Session) -> Self:
        """
        Load document by custom filename.

        Args:
            custom_filename (str): The custom filename of the document to load.
            collection_id (int): The id of the collection to load the document from.
            session (orm.Session): The session to use.

        Returns:
            Self: The document.
        """
        document = session.query(cls).filter_by(custom_filename=custom_filename,
                                                collection_id=collection_id).first()
        if document is None:
            logger.error(f"Document {custom_filename} not found in database.")
            raise DocumentNotFoundError(f"Document {custom_filename} not found in database.")
        return document

@dataclass
class Sentence:
    """Class to represent a sentence."""
    chunk: "Chunk"
    text: str
    embedding_vector: Optional[list[float]] = None


class Chunk(ORMBase):
    """Class to represent a chunk of a document."""
    __tablename__ = "chunks"
    # INFO: This is required because we are adding the 'sentences' attribute 
    # after the class definition. Conscious decision to not use SA2.x features 
    # yet.
    __allow_unmapped__ = True

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    document_id: orm.Mapped[int] = \
        orm.mapped_column(sa.Integer, sa.ForeignKey("documents.id"))
    text: orm.Mapped[str] = orm.mapped_column(sa.String)
    chunk_hash: orm.Mapped[str] = orm.mapped_column(sa.String)
    
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
