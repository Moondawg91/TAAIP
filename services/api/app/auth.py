import os
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Header
import jwt
from . import models
# Don't import SessionLocal at module import-time — tests replace
# `database.SessionLocal` with a proxy. Resolve it dynamically inside
# `get_db()` so the test harness's shared session is respected.
from sqlalchemy.orm import Session

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGO = "HS256"
JWT_EXP_MINUTES = 60 * 24

# Local dev auth bypass (default enabled to allow unlocked features unless explicitly disabled)
LOCAL_DEV_AUTH_BYPASS = os.getenv("LOCAL_DEV_AUTH_BYPASS", "1") in ("1", "true", "True")
if LOCAL_DEV_AUTH_BYPASS:
    logging.warning("LOCAL_DEV_AUTH_BYPASS enabled: JWT validation will be bypassed for local development")

# Master mode (single-user full permissions override for local/dev)
TAAIP_MASTER_MODE = os.getenv('TAAIP_MASTER_MODE', '1') in ('1', 'true', 'True')
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
    from . import database as _database
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass


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
        if TAAIP_MASTER_MODE:
            mu = _MockUser(username=os.getenv('DEV_USER', 'dev.user'), role_name='system_admin')
            mu.roles = ['system_admin', 'usarec_admin', '420t_admin', 'OWNER_MASTER']
            mu.permissions = ['*']
            return mu
        # Local dev bypass (only when no Authorization header)
        if LOCAL_DEV_AUTH_BYPASS:
            return _MockUser()
        raise HTTPException(status_code=401, detail="Authorization header required")
    # debug: write a small trace to /tmp for test runs
    try:
        with open('/tmp/auth_debug.log', 'a') as f:
            f.write(f"get_current_user header_present={bool(authorization)} token_sub={username} resolved_user={(user.username if user else None)} role={(getattr(user.role,'name',None) if user else None)}\n")
    except Exception:
        pass
    if not user:
        try:
            with open('/tmp/auth_debug.log', 'a') as f:
                from . import database as _db
                f.write(f"get_current_user: user_not_found username={username} header_present={bool(authorization)} engine_url={getattr(_db.engine,'url',None)} shared_session_present={_db._shared_session is not None}\n")
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_effective_user(authorization: str = Header(None)) -> dict:
    """Return a normalized effective user dict for frontend consumption.

    If `LOCAL_DEV_AUTH_BYPASS` or `TAAIP_MASTER_MODE` is enabled, return a
    master dev user with wildcard permissions. Otherwise attempt to decode
    the Bearer token and return claims (roles/permissions normalized).
    """
    # Master/mode dev bypass: prefer explicit master flag
    if TAAIP_MASTER_MODE or LOCAL_DEV_AUTH_BYPASS:
        return {
            "sub": "local-dev",
            "name": "Amber (Local Dev)",
            "roles": ["system_admin", "usarec_admin", "420t_admin", "OWNER_MASTER"],
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
        # If token did not carry permissions, attempt to load permissions from DB
        try:
            if not permissions:
                from .db import connect
                conn = connect()
                try:
                    cur = conn.cursor()
                    username = payload.get('sub') or payload.get('username')
                    cur.execute('SELECT id FROM users WHERE username=?', (username,))
                    u = cur.fetchone()
                    if u:
                        uid = u[0]
                        cur.execute('SELECT permission_key FROM user_permission WHERE user_id=? AND granted=1', (uid,))
                        perms = [r[0] for r in cur.fetchall()]
                        permissions = perms
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Exception:
            # best-effort: ignore DB errors and fall back to token perms
            pass

        return {
            "sub": payload.get('sub') or payload.get('username'),
            "name": payload.get('name') or payload.get('sub') or '',
            "roles": roles,
            "permissions": permissions,
            "org": {"level": payload.get('org_level') or '', "rsid_prefix": payload.get('rsid_prefix') or ''}
        }

    raise HTTPException(status_code=401, detail="Authorization required")
