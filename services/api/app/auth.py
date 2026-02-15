import os
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Header
import jwt
from . import models
from .database import SessionLocal
from sqlalchemy.orm import Session

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGO = "HS256"
JWT_EXP_MINUTES = 60 * 24


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
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> models.User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    username = payload.get("sub")
    user = db.query(models.User).filter_by(username=username).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
