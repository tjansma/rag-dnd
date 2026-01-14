"""Models for the database."""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm


class ORMBase(orm.DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Collection(ORMBase):
    """Class to represent a collection of documents."""
    __tablename__ = "collections"
    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sa.String)

    documents: orm.Mapped[list["Document"]] = orm.relationship(back_populates="collection")

class Document(ORMBase):
    """Class to represent a document."""
    __tablename__ = "documents"
    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    file_name: orm.Mapped[str] = orm.mapped_column(sa.String)
    file_hash: orm.Mapped[str] = orm.mapped_column(sa.String, unique=True)
    collection_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("collections.id"))
    
    collection: orm.Mapped["Collection"] = orm.relationship(
        back_populates="documents")
    chunks: orm.Mapped[list["Chunk"]] = orm.relationship(
        back_populates="parent_document",
        cascade="all, delete-orphan"
    )


@dataclass
class Sentence:
    chunk: "Chunk"
    text: str
    embedding_vector: Optional[list[float]] = None


class Chunk(ORMBase):
    """Class to represent a chunk of a document."""
    __tablename__ = "chunks"
    __allow_unmapped__ = True
    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    document_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("documents.id"))
    text: orm.Mapped[str] = orm.mapped_column(sa.String)
    chunk_hash: orm.Mapped[str] = orm.mapped_column(sa.String, unique=True)
    
    parent_document: orm.Mapped["Document"] = orm.relationship(back_populates="chunks")

    # This is not a mapped column, but a list of sentences
    sentences: list["Sentence"]

    def __str__(self) -> str:
        return self.text


@dataclass
class QueryResult:
    text: str
    source_document: str
