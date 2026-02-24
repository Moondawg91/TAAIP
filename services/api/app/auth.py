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

# Master mode (single-user full permissions override for local/dev)
TAAIP_MASTER_MODE = os.getenv('TAAIP_MASTER_MODE', '0') in ('1', 'true', 'True')
if TAAIP_MASTER_MODE:
    logging.warning("TAAIP_MASTER_MODE enabled: granting master permissions to local user")

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
        # emulate list of roles/permissions for compatibility
        self.roles = [role_name]
        self.permissions = ['*']


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
        # Master mode override: return a master user without requiring header
        if os.getenv('TAAIP_MASTER_MODE', '0').lower() in ('1', 'true', 'True'):
            mu = _MockUser(username=os.getenv('DEV_USER', 'dev.user'), role_name='system_admin')
            mu.roles = ['system_admin', 'usarec_admin', '420t_admin']
            mu.permissions = ['*']
            return mu
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


def get_effective_user(authorization: str = Header(None)) -> dict:
    """Return a normalized effective user dict for frontend consumption.

    If `LOCAL_DEV_AUTH_BYPASS` or `TAAIP_MASTER_MODE` is enabled, return a
    master dev user with wildcard permissions. Otherwise attempt to decode
    the Bearer token and return claims (roles/permissions normalized).
    """
    # Master/mode dev bypass: prefer explicit master env
    if os.getenv('TAAIP_MASTER_MODE', '0').lower() in ('1', 'true', 'True') or os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true', 'True'):
        return {
            "sub": "local-dev",
            "name": "Amber (Local Dev)",
            "roles": ["system_admin", "usarec_admin", "420t_admin"],
            "permissions": ["*"],
            "org": {"level": "USAREC", "rsid_prefix": ""}
        }

    # If an authorization header is present, attempt to decode JWT payload
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        # normalize into expected dict shape
        roles = payload.get('roles') or payload.get('role') or []
        if isinstance(roles, str):
            roles = [roles]
        permissions = payload.get('permissions') or payload.get('perms') or []
        if isinstance(permissions, str):
            permissions = [permissions]
        return {
            "sub": payload.get('sub') or payload.get('username'),
            "name": payload.get('name') or payload.get('sub') or '',
            "roles": roles,
            "permissions": permissions,
            "org": {"level": payload.get('org_level') or '', "rsid_prefix": payload.get('rsid_prefix') or ''}
        }

    raise HTTPException(status_code=401, detail="Authorization required")
