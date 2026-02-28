"""RDBMS related functions."""
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import Config

logger = logging.getLogger(__name__)

_engine = None

def _get_engine():
    """
    Get the engine.
    
    Returns:
        Engine: The engine.
    """
    global _engine
    
    if _engine is None:
        config = Config.load()
        # INFO potential risk of logging sensitive information (password in URL)
        logger.debug(f"Creating engine for database: {config.content_database_url}")
        _engine = create_engine(url=config.content_database_url)

    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Using database: {_engine}")

    return _engine


def init_db():
    """
    Initialize the database.
    
    Returns:
        None
    """
    from .models import ORMBase

    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Initializing database: {Config.load().content_database_url}")
    engine = _get_engine()

    ORMBase.metadata.create_all(engine)


def get_session() -> Session:
    """
    Get a session.
    
    Returns:
        Session: A session.
    """
    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Getting session from database: {Config.load().content_database_url}")
    engine = _get_engine()
    return sessionmaker(bind=engine)()
