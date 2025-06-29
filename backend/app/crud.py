from sqlalchemy.orm import Session
from . import models, schemas
from uuid import UUID
from sqlalchemy import func
from datetime import datetime, timedelta

# User CRUD

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

# Repository CRUD

def create_repository(db: Session, repo: schemas.RepositoryCreate):
    db_repo = models.Repository(**repo.dict())
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo

def get_repository(db: Session, repo_id: UUID):
    return db.query(models.Repository).filter(models.Repository.id == repo_id).first()

def get_repositories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Repository).offset(skip).limit(limit).all()

# Commit CRUD

def create_commit(db: Session, commit: schemas.CommitCreate):
    db_commit = models.Commit(**commit.dict())
    db.add(db_commit)
    db.commit()
    db.refresh(db_commit)
    return db_commit

def get_commit(db: Session, commit_id: UUID):
    return db.query(models.Commit).filter(models.Commit.id == commit_id).first()

def get_commits(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Commit).offset(skip).limit(limit).all()

# Developer CRUD

def create_developer(db: Session, developer: schemas.Developer):
    db_dev = models.Developer(**developer.dict())
    db.add(db_dev)
    db.commit()
    db.refresh(db_dev)
    return db_dev

def get_developer(db: Session, github_id: str):
    return db.query(models.Developer).filter(models.Developer.github_id == github_id).first()

def get_developers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Developer).offset(skip).limit(limit).all()

# ProjectProgressImage CRUD

def create_progress_image(db: Session, image: schemas.ProjectProgressImage):
    db_img = models.ProjectProgressImage(**image.dict())
    db.add(db_img)
    db.commit()
    db.refresh(db_img)
    return db_img

def get_progress_image(db: Session, image_id: UUID):
    return db.query(models.ProjectProgressImage).filter(models.ProjectProgressImage.id == image_id).first()

def get_progress_images(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ProjectProgressImage).offset(skip).limit(limit).all()

def compare_efficiency(db: Session, github_id_1: str, github_id_2: str):
    dev1 = get_developer(db, github_id_1)
    dev2 = get_developer(db, github_id_2)
    if not dev1 or not dev2:
        return None, None
    return dev1.average_efficiency, dev2.average_efficiency

# Mock commit analysis (replace with AI logic later)
def analyze_commit(db: Session, commit_hash: str):
    commit = db.query(models.Commit).filter(models.Commit.commit_hash == commit_hash).first()
    if not commit:
        return None
    # Mock summary/efficiency/flag
    summary = commit.summary or {"summary": "No summary available."}
    efficiency = commit.efficiency or 0.0
    flag = efficiency < 0.5  # Example: flag if efficiency is low
    return {"commit_hash": commit_hash, "summary": summary, "efficiency": efficiency, "flagged": flag}

# PullRequest CRUD

def create_pull_request(db: Session, pr: schemas.PullRequestCreate):
    db_pr = models.PullRequest(**pr.dict())
    db.add(db_pr)
    db.commit()
    db.refresh(db_pr)
    return db_pr

def get_pull_request_by_commit(db: Session, commit_hash: str):
    return db.query(models.PullRequest).filter(models.PullRequest.commit_hash == commit_hash).first()

def get_pull_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PullRequest).offset(skip).limit(limit).all()

# ProjectProgressReport CRUD

def create_project_progress_report(db: Session, report: schemas.ProjectProgressReportCreate):
    db_report = models.ProjectProgressReport(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_latest_project_progress_report(db: Session, repository_id):
    return db.query(models.ProjectProgressReport).filter(models.ProjectProgressReport.repository_id == repository_id).order_by(models.ProjectProgressReport.created_at.desc()).first()

def get_project_progress_reports(db: Session, repository_id, skip: int = 0, limit: int = 10):
    return db.query(models.ProjectProgressReport).filter(models.ProjectProgressReport.repository_id == repository_id).order_by(models.ProjectProgressReport.created_at.desc()).offset(skip).limit(limit).all()

def efficiency_trend_for_developer(db: Session, github_id: str, days: int = 30):
    # Returns list of (date, avg_efficiency) for the last N days
    since = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(
            func.date(models.Commit.summary["date"].astext),
            func.avg(models.Commit.efficiency)
        )
        .join(models.Repository, models.Commit.repo_id == models.Repository.id)
        .join(models.User, models.Repository.owner_id == models.User.id)
        .filter(models.User.github_id == github_id)
        .filter(models.Commit.summary["date"].astext != None)
        .filter(models.Commit.summary["date"].astext >= since.strftime('%Y-%m-%d'))
        .group_by(func.date(models.Commit.summary["date"].astext))
        .order_by(func.date(models.Commit.summary["date"].astext))
        .all()
    )

def efficiency_trend_for_repo(db: Session, repo_id, days: int = 30):
    since = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(
            func.date(models.Commit.summary["date"].astext),
            func.avg(models.Commit.efficiency)
        )
        .filter(models.Commit.repo_id == repo_id)
        .filter(models.Commit.summary["date"].astext != None)
        .filter(models.Commit.summary["date"].astext >= since.strftime('%Y-%m-%d'))
        .group_by(func.date(models.Commit.summary["date"].astext))
        .order_by(func.date(models.Commit.summary["date"].astext))
        .all()
    )

def flagged_commits_count(db: Session, repo_id=None, github_id=None):
    q = db.query(models.Commit).filter(models.Commit.efficiency < 0.5)
    if repo_id:
        q = q.filter(models.Commit.repo_id == repo_id)
    if github_id:
        q = q.join(models.Repository, models.Commit.repo_id == models.Repository.id)
        q = q.join(models.User, models.Repository.owner_id == models.User.id)
        q = q.filter(models.User.github_id == github_id)
    return q.count()

def flagged_prs_count(db: Session, repo_id=None):
    q = db.query(models.PullRequest)
    if repo_id:
        q = q.filter(models.PullRequest.repository_id == repo_id)
    return q.count() 