from fastapi import FastAPI
from db import engine
from models import *
from routers.home import router as home_router
from routers.register import router as auth_router
from routers.login import router as login_router

app = FastAPI()

app.include_router(home_router)
app.include_router(auth_router)
app.include_router(login_router)

# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

