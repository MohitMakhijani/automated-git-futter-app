from github import Github
import os

def get_commit_diff(repo_full_name: str, commit_sha: str) -> str:
    token = os.getenv("GITHUB_BOT_TOKEN")
    if not token:
        raise Exception("GITHUB_BOT_TOKEN not set")
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    commit = repo.get_commit(commit_sha)
    # Get the raw diff
    files = commit.files
    diff = "\n".join([f.patch for f in files if hasattr(f, 'patch') and f.patch])
    return diff

def create_pull_request_for_commit(repo_full_name: str, commit_sha: str, message: str = "Automated PR for flagged commit") -> str:
    token = os.getenv("GITHUB_BOT_TOKEN")
    if not token:
        raise Exception("GITHUB_BOT_TOKEN not set")
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    commit = repo.get_commit(commit_sha)
    default_branch = repo.default_branch
    pr_branch = f"ai-flagged-{commit_sha[:7]}"
    # Create a new branch from the flagged commit
    ref = repo.create_git_ref(ref=f"refs/heads/{pr_branch}", sha=commit_sha)
    # Create the PR
    pr = repo.create_pull(
        title="AI-Flagged Commit: Review Required",
        body=message,
        head=pr_branch,
        base=default_branch
    )
    return pr.html_url 