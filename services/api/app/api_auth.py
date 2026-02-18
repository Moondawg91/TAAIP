from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import database, models, auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    scope: str = None


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter_by(username=payload.username).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")
    token = auth.create_token_for_user(user)
    return LoginResponse(token=token, username=user.username, role=user.role.name, scope=user.scope)
