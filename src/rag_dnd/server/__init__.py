from fastapi import FastAPI

from ..config import Config
from ..log import setup_logging

# Load config and set env vars BEFORE importing routes/transformers
setup_logging(Config.load())

from .routes_v2 import router_v2

app = FastAPI()
app.include_router(router_v2)
