"""RDBMS related functions."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import Config
from .models import ORMBase

logger = logging.getLogger(__name__)

def _get_engine():
    """
    Get the engine.
    
    Returns:
        Engine: The engine.
    """
    config = Config()

    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Connecting to database: {config.content_database_url}")
    return create_engine(url=config.content_database_url)


def init_db():
    """
    Initialize the database.
    
    Returns:
        None
    """
    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Initializing database: {Config().content_database_url}")
    engine = _get_engine()

    ORMBase.metadata.create_all(engine)


def get_session() -> Session:
    """
    Get a session.
    
    Returns:
        Session: A session.
    """
    # INFO potential risk of logging sensitive information (password in URL)
    logger.debug(f"Getting session from database: {Config().content_database_url}")
    engine = _get_engine()
    return sessionmaker(bind=engine)()
