import httpx
from jose import jwt, JWTError
from datetime import datetime, timedelta
from . import config

# GitHub OAuth URLs
auth_base = "https://github.com/login/oauth/authorize"
token_url = "https://github.com/login/oauth/access_token"
user_api = "https://api.github.com/user"

# Get GitHub OAuth URL
def get_github_oauth_url():
    return f"{auth_base}?client_id={config.GITHUB_CLIENT_ID}&redirect_uri={config.GITHUB_OAUTH_CALLBACK_URL}&scope=repo,user"

# Exchange code for access token
def exchange_code_for_token(code: str):
    data = {
        "client_id": config.GITHUB_CLIENT_ID,
        "client_secret": config.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": config.GITHUB_OAUTH_CALLBACK_URL,
    }
    headers = {"Accept": "application/json"}
    with httpx.Client() as client:
        resp = client.post(token_url, data=data, headers=headers)
        resp.raise_for_status()
        return resp.json().get("access_token")

# Get user info from GitHub
def get_github_user(access_token: str):
    headers = {"Authorization": f"token {access_token}"}
    with httpx.Client() as client:
        resp = client.get(user_api, headers=headers)
        resp.raise_for_status()
        return resp.json()

# JWT creation
def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=config.JWT_EXPIRATION_SECONDS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

# JWT verification
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None 