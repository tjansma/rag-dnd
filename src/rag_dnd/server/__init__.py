from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..config import Config
from ..core import init_db
from ..log import setup_logging

# Load config and set env vars BEFORE importing routes/transformers
setup_logging(Config.load())

from .routes_v2 import router_v2

from ..core.database import _get_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan of the application."""
    init_db()
    
    yield
    
    # Graceful shutdown: Disposes of the SQLAlchemy connection pool.
    # For SQLite, this closes the active connections, triggering a WAL flush.
    engine = _get_engine()
    if engine:
        engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(router_v2)
