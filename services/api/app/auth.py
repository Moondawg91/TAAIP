import os
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Header
import jwt
from . import models
from .database import SessionLocal
from sqlalchemy.orm import Session

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGO = "HS256"
JWT_EXP_MINUTES = 60 * 24

# Local dev auth bypass
LOCAL_DEV_AUTH_BYPASS = os.getenv("LOCAL_DEV_AUTH_BYPASS", "0") in ("1", "true", "True")
if LOCAL_DEV_AUTH_BYPASS:
    logging.warning("LOCAL_DEV_AUTH_BYPASS enabled: JWT validation will be bypassed for local development")


def create_token_for_user(user: models.User):
    payload = {
        "sub": user.username,
        "role": user.role.name,
        "scope": user.scope,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class _MockRole:
    def __init__(self, name="admin"):
        self.name = name


class _MockUser:
    def __init__(self, username="dev", role_name="admin", scope="USAREC"):
        self.username = username
        self.role = _MockRole(role_name)
        self.scope = scope
        self.id = "dev"


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> models.User:
    # If an Authorization header is present, always attempt to resolve the
    # user from the token. Only when no Authorization header is provided do
    # we fall back to the local dev bypass mock user.
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token)
        username = payload.get("sub")
        user = db.query(models.User).filter_by(username=username).one_or_none()
    else:
        # Local dev bypass (only when no Authorization header)
        if os.getenv("LOCAL_DEV_AUTH_BYPASS", "0").lower() in ("1", "true", "True"):
            return _MockUser()
        raise HTTPException(status_code=401, detail="Authorization header required")
    # debug: write a small trace to /tmp for test runs
    try:
        with open('/tmp/auth_debug.log', 'a') as f:
            f.write(f"get_current_user header_present={bool(authorization)} token_sub={username} resolved_user={(user.username if user else None)} role={(getattr(user.role,'name',None) if user else None)}\n")
    except Exception:
        pass
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
