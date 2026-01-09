"""RDBMS related functions."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config

from .models import ORMBase


def _get_engine():
    """Get the engine."""
    config = Config()
    return create_engine(url=config.content_database_url)


def init_db():
    """Initialize the database."""
    engine = _get_engine()

    ORMBase.metadata.create_all(engine)


def get_session():
    """Get a session."""
    engine = _get_engine()
    return sessionmaker(bind=engine)()
