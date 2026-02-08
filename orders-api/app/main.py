from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import Base, engine
from . import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
