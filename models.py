from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint, CheckConstraint, func, DateTime

import enum

Base = declarative_base()

class TimeStampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)

    tasks = relationship("Task", back_populates="assigned_user")
    user_projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")
    
    friendships = relationship("Friendship", foreign_keys="Friendship.user_id", back_populates="user")
    frien_of = relationship("Friendship", foreign_keys="Friendship.friend_id", back_populates="friend")

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

class FriendStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    blocked = "blocked"

class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id"),
        CheckConstraint("user_id != friend_id", name="check_not_self_friend")
        )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(FriendStatus), default=FriendStatus.pending, nullable=False )

    user = relationship("User", back_populates="friendships", foreign_keys=[user_id])
    friend = relationship("User", back_populates="friendships", foreign_keys=[friend_id])



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