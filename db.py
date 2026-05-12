from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DB_URL
from models import User, Task, Project, UserProject, RoleEnum


engine = create_engine(DB_URL)

SessionLocal = sessionmaker(bind=engine)

session = SessionLocal()

