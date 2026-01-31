from fastapi import FastAPI

from ..config import Config
from ..log import setup_logging

from .routes import router
from .routes_v2 import router_v2

setup_logging(Config())

app = FastAPI()
app.include_router(router)
app.include_router(router_v2)
