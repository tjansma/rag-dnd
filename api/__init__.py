from fastapi import FastAPI

from config import Config
from log import setup_logging

from .routes import router

setup_logging(Config())

app = FastAPI()
app.include_router(router)
