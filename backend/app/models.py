from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(String, unique=True, index=True)
    access_token = Column(String)
    fcm_token = Column(String, nullable=True)
    repositories = relationship("Repository", back_populates="owner")

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_repo_id = Column(String, unique=True, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    owner = relationship("User", back_populates="repositories")
    commits = relationship("Commit", back_populates="repository")
    progress_images = relationship("ProjectProgressImage", back_populates="repository")

class Commit(Base):
    __tablename__ = "commits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    commit_hash = Column(String, index=True)
    summary = Column(JSON)
    efficiency = Column(Float)
    repository = relationship("Repository", back_populates="commits")

class Developer(Base):
    __tablename__ = "developers"
    github_id = Column(String, primary_key=True)
    average_efficiency = Column(Float)

class ProjectProgressImage(Base):
    __tablename__ = "project_progress_images"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    image_url = Column(String)
    repository = relationship("Repository", back_populates="progress_images")

class PullRequest(Base):
    __tablename__ = "pull_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    commit_hash = Column(String)
    pr_url = Column(String)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    repository = relationship("Repository")

class ProjectProgressReport(Base):
    __tablename__ = "project_progress_reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    report = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    repository = relationship("Repository") 