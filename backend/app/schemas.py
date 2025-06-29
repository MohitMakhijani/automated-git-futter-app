from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    github_id: str
    fcm_token: Optional[str] = None

class UserCreate(UserBase):
    access_token: str

class User(UserBase):
    id: UUID
    class Config:
        orm_mode = True

class RepositoryBase(BaseModel):
    github_repo_id: str

class RepositoryCreate(RepositoryBase):
    owner_id: UUID

class Repository(RepositoryBase):
    id: UUID
    owner_id: UUID
    class Config:
        orm_mode = True

class CommitBase(BaseModel):
    commit_hash: str
    summary: Any
    efficiency: float

class CommitCreate(CommitBase):
    repo_id: UUID

class Commit(CommitBase):
    id: UUID
    repo_id: UUID
    class Config:
        orm_mode = True

class Developer(BaseModel):
    github_id: str
    average_efficiency: float
    class Config:
        orm_mode = True

class ProjectProgressImage(BaseModel):
    id: UUID
    repository_id: UUID
    image_url: str
    class Config:
        orm_mode = True

class PullRequestBase(BaseModel):
    repository_id: UUID
    commit_hash: str
    pr_url: str
    status: str = "open"

class PullRequestCreate(PullRequestBase):
    pass

class PullRequest(PullRequestBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True

class ProjectProgressReportBase(BaseModel):
    repository_id: UUID
    report: str

class ProjectProgressReportCreate(ProjectProgressReportBase):
    pass

class ProjectProgressReport(ProjectProgressReportBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True 