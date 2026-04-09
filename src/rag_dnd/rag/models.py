"""Models for the database."""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Self
import logging
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..core import ORMBase, CampaignMetadata
from ..shared import DocumentNotFoundError

logger = logging.getLogger(__name__)


class Collection(ORMBase):
    """Class to represent a collection of documents."""
    __tablename__ = "collections"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
        primary_key=True, 
        comment="Collection ID")
    name: orm.Mapped[str] = orm.mapped_column(sa.String, 
        comment="Collection name")
    campaign_id: orm.Mapped[int] = \
        orm.mapped_column(sa.Integer, 
                          sa.ForeignKey("campaign_metadata.id"), 
                          comment="Campaign ID")

    campaign: orm.Mapped[CampaignMetadata] = orm.relationship(
        backref="collections")
    rag_documents: orm.Mapped[list["RAGDocument"]] = \
        orm.relationship(back_populates="collection")

class RAGDocument(ORMBase):
    """Class to represent a document."""
    __tablename__ = "rag_documents"
    __table_args__ = (
        sa.UniqueConstraint("collection_id", "file_hash",
                            name="uq_collection_file_hash"),
        sa.UniqueConstraint("collection_id", "custom_filename",
                            name="uq_collection_custom_filename"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
        primary_key=True, 
        comment="RAG Document ID")
    file_hash: orm.Mapped[str] = orm.mapped_column(sa.String, 
        index=True,
        comment="File hash")
    custom_filename: orm.Mapped[str] = orm.mapped_column(
        sa.String, 
        index=True,
        comment="Custom filename")
    collection_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, 
        sa.ForeignKey("collections.id"),
        comment="Collection ID")
    
    collection: orm.Mapped["Collection"] = orm.relationship(
        back_populates="rag_documents")
    chunks: orm.Mapped[list["Chunk"]] = orm.relationship(
        back_populates="parent_rag_document",
        cascade="all, delete-orphan"
    )

    @classmethod
    def load_by_custom_filename(cls,
                                custom_filename: str,
                                collection_id: int,
                                session: orm.Session) -> Self:
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


class GameCharacterRAGDocument(ORMBase):
    """Class to represent a game character RAG document."""
    __tablename__ = "game_character_rag_documents"
    __table_args__ = (
        sa.UniqueConstraint("character_id", "rag_document_id",
                            name="uq_character_rag_document"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    character_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("game_characters.id"),
        comment="Character ID")
    rag_document_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("rag_documents.id"),
        comment="RAG Document ID")
    description: orm.Mapped[str | None] = orm.mapped_column(sa.String,
        nullable=True,
        comment="Description")
    
    # pyrefly: ignore[unknown-name]
    character: orm.Mapped["GameCharacter"] = \
        orm.relationship(backref="rag_document_links")  
    rag_document: orm.Mapped["RAGDocument"] = \
        orm.relationship(backref="character_links")


class GameSessionRAGDocument(ORMBase):
    """Class to represent a game session RAG document."""
    __tablename__ = "game_session_rag_documents"
    __table_args__ = (
        sa.UniqueConstraint("session_id", "rag_document_id",
                            name="uq_session_rag_document"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    session_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("game_sessions.id"),
        comment="Session ID")
    rag_document_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("rag_documents.id"),
        comment="RAG Document ID")
    description: orm.Mapped[str | None] = orm.mapped_column(sa.String,
        nullable=True,
        comment="Description")
    
    # pyrefly: ignore[unknown-name]
    session: orm.Mapped["GameSession"] = \
        orm.relationship(backref="rag_document_links")  
    rag_document: orm.Mapped["RAGDocument"] = \
        orm.relationship(backref="session_links")


class AssetRAGDocument(ORMBase):
    """Class to represent an asset RAG document."""
    __tablename__ = "asset_rag_documents"
    __table_args__ = (
        sa.UniqueConstraint("asset_id", "rag_document_id",
                            name="uq_asset_rag_document"),
    )

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    asset_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("assets.id"),
        comment="Asset ID")
    rag_document_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("rag_documents.id"),
        comment="RAG Document ID")
    description: orm.Mapped[str | None] = orm.mapped_column(sa.String,
        nullable=True,
        comment="Description")
    
    # pyrefly: ignore[unknown-name]
    asset: orm.Mapped["Asset"] = \
        orm.relationship(backref="rag_document_links")  
    rag_document: orm.Mapped["RAGDocument"] = \
        orm.relationship(backref="asset_links")


class Chunk(ORMBase):
    """Class to represent a chunk of a document."""
    __tablename__ = "chunks"
    # INFO: This is required because we are adding the 'sentences' attribute 
    # after the class definition. Conscious decision to not use SA2.x features 
    # yet.
    __allow_unmapped__ = True

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        primary_key=True,
        comment="Chunk ID")
    document_id: orm.Mapped[int] = orm.mapped_column(sa.Integer,
        sa.ForeignKey("rag_documents.id"),
        comment="Document ID")
    text: orm.Mapped[str] = orm.mapped_column(sa.String,
        comment="Text")
    chunk_hash: orm.Mapped[str] = orm.mapped_column(sa.String,
        comment="Chunk hash")
    
    parent_rag_document: orm.Mapped["RAGDocument"] = \
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
