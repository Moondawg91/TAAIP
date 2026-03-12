from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import database, models, auth

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.get('/me')
def auth_me(effective=Depends(auth.get_effective_user)):
    # Mirror the /api/me response shape for compatibility
    try:
        # reuse the helpers from routers.me by constructing the same shape
        from .routers import me as me_router
        return me_router.me(effective)
    except Exception:
        # Fallback: return the effective user claims as-is
        return {'user': {'id': effective.get('sub'), 'name': effective.get('name')}, 'permissions': {p: True for p in (effective.get('permissions') or [])}, 'is_admin': ('*' in (effective.get('permissions') or []) )}
