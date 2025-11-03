import json
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def load_users():
    with open("users.json", "r") as f:
        data = json.load(f)
    return {u["username"]: u for u in data["users"]}

users_db = load_users()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    user = users_db.get(username)

    if not user or not secrets.compare_digest(password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return {
        "username": user["username"],
        "role": user.get("role", "User")
    }