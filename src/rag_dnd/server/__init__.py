from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..config import Config
from ..core import init_db
from ..log import setup_logging

# Load config and set env vars BEFORE importing routes/transformers
setup_logging(Config.load())

from .routes_v2 import router_v2

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan of the application."""
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router_v2)
