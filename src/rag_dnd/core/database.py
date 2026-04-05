"""RDBMS related functions."""
from contextlib import contextmanager
from typing import Generator
import logging

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import Config

logger = logging.getLogger(__name__)

_engine: Engine | None = None

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
        
        # SQLite requires check_same_thread=False for multi-threaded access
        if config.content_database_driver.lower() == "sqlite":
            connect_args = {
                "check_same_thread": False
            }
        else:
            connect_args = {}
        
        _engine = create_engine(url=config.content_database_url,
                                connect_args=connect_args)
        
        # Set PRAGMA for SQLite
        if config.content_database_driver.lower() == "sqlite":
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;") 
                cursor.close()

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


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a session and close it after use.

    Yields:
        Session: A session.
    """
    # INFO potential risk of logging sensitive information (password in URL)
    engine = _get_engine()

    logger.debug(f"Getting session from database: {engine}")
    try:
        session = sessionmaker(bind=engine, expire_on_commit=True)()
        yield session
    finally:
        logger.debug(f"Closing session: {session}")
        session.close()
