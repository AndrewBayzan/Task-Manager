from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)

    tasks = relationship("Task", back_populates="assigned_user")
    user_projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")
    
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    project = relationship("Project", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks")
    
class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(20), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    user_projects = relationship("UserProject", back_populates="project", cascade="all, delete-orphan")

class RoleEnum(enum.Enum):
    admin = "admin"
    member = "member"

class UserProject(Base):
    __tablename__ = 'user_project'
    __table_args__ = (UniqueConstraint("user_id", "project_id"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(Enum(RoleEnum), nullable=False)

    user = relationship("User", back_populates="user_projects")
    project = relationship("Project", back_populates="user_projects")



# users:
# - id
# - name

# projects:
# - id
# - project_name

# tasks:
# - id
# - title
# - user_id
# - project_id

# user_projects:
# - user_id
# - project_id
# - role