from fastapi import FastAPI
from db import engine
from models import *
from routers.home import router as home_router

app = FastAPI()

app.include_router(home_router)

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

