"""
api/auth.py
===========
JWT-based authentication helpers for the FastAPI backend.
"""
from __future__ import annotations
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

def _require_env(name: str) -> str:
    """Read a required secret from the environment; refuse to start without it."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and set it, "
            "or pass it as an environment variable."
        )
    return value


SECRET_KEY = _require_env("SECRET_KEY")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
router        = APIRouter(prefix="/api/auth", tags=["auth"])

# Demo user store: two fixed roles with passwords from the environment.
# A real deployment would use a user table with hashed passwords.
USERS = {
    "admin": {
        "username": "admin",
        "password": _require_env("ADMIN_PASSWORD"),
        "role": "admin",
    },
    "manager": {
        "username": "manager",
        "password": _require_env("MANAGER_PASSWORD"),
        "role": "manager",
    },
}


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = USERS.get(username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form_data.username)
    # constant-time comparison so response timing does not leak password contents
    if not user or not secrets.compare_digest(
        user["password"].encode(), form_data.password.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}
