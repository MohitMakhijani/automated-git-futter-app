from fastapi import FastAPI, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from . import models, schemas, crud, database
from typing import List
from uuid import UUID
from fastapi.responses import RedirectResponse
from . import auth
from fastapi.security import OAuth2PasswordBearer
from fastapi import Security
import hmac
import hashlib
from . import config
from . import ai_agents
from . import github as github_utils
from . import notifications
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all origins for local testing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"msg": "Backend is running"}

# User endpoints
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[schemas.User])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip, limit)

# Repository endpoints
@app.post("/repositories/", response_model=schemas.Repository)
def create_repository(repo: schemas.RepositoryCreate, db: Session = Depends(get_db)):
    return crud.create_repository(db, repo)

@app.get("/repositories/{repo_id}", response_model=schemas.Repository)
def get_repository(repo_id: str, db: Session = Depends(get_db)):
    repo = crud.get_repository(db, UUID(repo_id))
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@app.get("/repositories/", response_model=List[schemas.Repository])
def list_repositories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_repositories(db, skip, limit)

# Commit endpoints
@app.post("/commits/", response_model=schemas.Commit)
def create_commit(commit: schemas.CommitCreate, db: Session = Depends(get_db)):
    return crud.create_commit(db, commit)

@app.get("/commits/{commit_id}", response_model=schemas.Commit)
def get_commit(commit_id: str, db: Session = Depends(get_db)):
    commit = crud.get_commit(db, UUID(commit_id))
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    return commit

@app.get("/commits/", response_model=List[schemas.Commit])
def list_commits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_commits(db, skip, limit)

# Developer endpoints
@app.post("/developers/", response_model=schemas.Developer)
def create_developer(developer: schemas.Developer, db: Session = Depends(get_db)):
    return crud.create_developer(db, developer)

@app.get("/developers/{github_id}", response_model=schemas.Developer)
def get_developer(github_id: str, db: Session = Depends(get_db)):
    dev = crud.get_developer(db, github_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    return dev

@app.get("/developers/", response_model=List[schemas.Developer])
def list_developers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_developers(db, skip, limit)

# ProjectProgressImage endpoints
@app.post("/progress-images/", response_model=schemas.ProjectProgressImage)
def create_progress_image(image: schemas.ProjectProgressImage, db: Session = Depends(get_db)):
    return crud.create_progress_image(db, image)

@app.get("/progress-images/{image_id}", response_model=schemas.ProjectProgressImage)
def get_progress_image(image_id: str, db: Session = Depends(get_db)):
    img = crud.get_progress_image(db, UUID(image_id))
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    return img

@app.get("/progress-images/", response_model=List[schemas.ProjectProgressImage])
def list_progress_images(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_progress_images(db, skip, limit)

@app.get("/compare-efficiency/")
def compare_efficiency(dev1: str, dev2: str, db: Session = Depends(get_db)):
    eff1, eff2 = crud.compare_efficiency(db, dev1, dev2)
    if eff1 is None or eff2 is None:
        raise HTTPException(status_code=404, detail="One or both developers not found")
    return {"developer_1": dev1, "efficiency_1": eff1, "developer_2": dev2, "efficiency_2": eff2}

@app.get("/analyze-commit/{commit_hash}")
def analyze_commit(commit_hash: str, db: Session = Depends(get_db)):
    result = crud.analyze_commit(db, commit_hash)
    if not result:
        raise HTTPException(status_code=404, detail="Commit not found")
    return result

@app.post("/analyze")
async def analyze_commit_ai(request: dict = Body(...)):
    """Analyze a commit using AI"""
    try:
        repo = request.get("repo")
        commit_hash = request.get("commit_hash")
        diff = request.get("diff")
        
        if not all([repo, commit_hash, diff]):
            raise HTTPException(status_code=400, detail="Missing required fields: repo, commit_hash, diff")
        
        # Ensure all values are strings
        repo = str(repo)
        commit_hash = str(commit_hash)
        diff = str(diff)
        
        # Use the AI agent to analyze the commit
        result = await ai_agents.analyze_commit_ai(repo, commit_hash, diff)
        return {
            "repo": repo,
            "commit_hash": commit_hash,
            "summary": result.get("summary", "No summary available"),
            "efficiency": result.get("efficiency", 0.0),
            "flagged": result.get("flagged", False),
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@app.get("/auth/github/login")
def github_login():
    url = auth.get_github_oauth_url()
    return RedirectResponse(url)

@app.get("/auth/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    access_token = auth.exchange_code_for_token(code)
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")
    user_info = auth.get_github_user(access_token)
    github_id = str(user_info["id"])
    # Check if user exists, else create
    user = crud.get_developer(db, github_id)
    if not user:
        user = crud.create_developer(db, schemas.Developer(github_id=github_id, average_efficiency=0.0))
    # Store access_token in Users table if you want (not in Developer)
    # Issue JWT
    jwt_token = auth.create_jwt_token({"sub": github_id})
    return {"access_token": jwt_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth.verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@app.get("/protected")
def protected_route(user=Depends(get_current_user)):
    return {"msg": f"Hello, user {user['sub']}! This is a protected route."}

# Helper to verify GitHub webhook signature
def verify_github_signature(request: Request, body: bytes):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return False
    secret = config.GITHUB_CLIENT_SECRET.encode()
    mac = hmac.new(secret, msg=body, digestmod=hashlib.sha256)
    expected = f"sha256={mac.hexdigest()}"
    return hmac.compare_digest(signature, expected)

@app.post("/webhook/github")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    if not verify_github_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid signature")
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    if event == "push":
        repo_id = payload["repository"]["id"]
        repo_name = payload["repository"]["full_name"]
        for commit in payload.get("commits", []):
            commit_hash = commit["id"]
            # Fetch the real diff from GitHub
            try:
                diff = github_utils.get_commit_diff(repo_name, commit_hash)
            except Exception as e:
                print(f"Error fetching diff: {e}")
                diff = ""
            # Call the OpenAI-based commit analysis via FastAPI endpoint
            async with httpx.AsyncClient() as client:
                ai_response = await client.post(
                    "http://localhost:8000/analyze",
                    json={"repo": repo_name, "commit_hash": commit_hash, "diff": diff}
                )
                ai_result = ai_response.json()
            db_commit = schemas.CommitCreate(
                repo_id=repo_id,
                commit_hash=commit_hash,
                summary=ai_result["summary"],
                efficiency=ai_result["efficiency"]
            )
            crud.create_commit(db, db_commit)
            # If flagged, create a PR and store info, then notify owner
            if ai_result.get("flagged"):
                try:
                    pr_url = github_utils.create_pull_request_for_commit(repo_name, commit_hash, message="AI flagged this commit for review.")
                    print(f"PR created: {pr_url}")
                    pr_data = schemas.PullRequestCreate(
                        repository_id=repo_id,
                        commit_hash=commit_hash,
                        pr_url=pr_url,
                        status="open"
                    )
                    crud.create_pull_request(db, pr_data)
                    # Notify repo owner if they have an FCM token
                    repo = crud.get_repository(db, repo_id)
                    if repo and repo.owner and repo.owner.fcm_token:
                        notifications.send_push_notification(
                            repo.owner.fcm_token,
                            title="AI-Flagged Commit: PR Created",
                            body=f"A PR was created for flagged commit {commit_hash[:7]} in {repo_name}.",
                            data={"pr_url": pr_url}
                        )
                except Exception as e:
                    print(f"Error creating PR or sending notification: {e}")
    return {"msg": "Webhook received"}

@app.post("/repositories/{repo_id}/progress-report", response_model=schemas.ProjectProgressReport)
def create_progress_report(repo_id: str, report: str = Body(...), db: Session = Depends(get_db)):
    report_data = schemas.ProjectProgressReportCreate(repository_id=UUID(repo_id), report=report)
    return crud.create_project_progress_report(db, report_data)

@app.get("/repositories/{repo_id}/progress-report", response_model=schemas.ProjectProgressReport)
def get_latest_progress_report(repo_id: str, db: Session = Depends(get_db)):
    report = crud.get_latest_project_progress_report(db, UUID(repo_id))
    if not report:
        raise HTTPException(status_code=404, detail="No progress report found")
    return report

@app.get("/repositories/{repo_id}/progress-reports", response_model=List[schemas.ProjectProgressReport])
def list_progress_reports(repo_id: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_project_progress_reports(db, UUID(repo_id), skip, limit)

@app.get("/analytics/developer/{github_id}/efficiency-trend")
def get_efficiency_trend_developer(github_id: str, days: int = 30, db: Session = Depends(get_db)):
    data = crud.efficiency_trend_for_developer(db, github_id, days)
    return [{"date": d, "avg_efficiency": float(e) if e is not None else None} for d, e in data]

@app.get("/analytics/repository/{repo_id}/efficiency-trend")
def get_efficiency_trend_repo(repo_id: str, days: int = 30, db: Session = Depends(get_db)):
    data = crud.efficiency_trend_for_repo(db, UUID(repo_id), days)
    return [{"date": d, "avg_efficiency": float(e) if e is not None else None} for d, e in data]

@app.get("/analytics/repository/{repo_id}/flagged-commits-count")
def get_flagged_commits_count(repo_id: str, db: Session = Depends(get_db)):
    count = crud.flagged_commits_count(db, repo_id=UUID(repo_id))
    return {"flagged_commits": count}

@app.get("/analytics/developer/{github_id}/flagged-commits-count")
def get_flagged_commits_count_developer(github_id: str, db: Session = Depends(get_db)):
    count = crud.flagged_commits_count(db, github_id=github_id)
    return {"flagged_commits": count}

@app.get("/analytics/repository/{repo_id}/flagged-prs-count")
def get_flagged_prs_count(repo_id: str, db: Session = Depends(get_db)):
    count = crud.flagged_prs_count(db, repo_id=UUID(repo_id))
    return {"flagged_prs": count} 