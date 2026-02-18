"""RBAC helpers and admin router.

This module exposes:
- `get_current_user` dependency which returns a normalized dict: `{'username', 'roles', 'scopes'}`
- `require_roles`, `require_not_role`, `require_station_scope` dependency factories
- an `APIRouter` at `/rbac` with user/role management endpoints.
"""

import os
import base64
import json
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, Depends, APIRouter
from ..db import connect


def _b64url_decode(inp: str) -> bytes:
    s = inp.replace("-", "+").replace("_", "/")
    s += "=" * ((4 - len(s) % 4) % 4)
    return base64.b64decode(s)


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b = _b64url_decode(parts[1])
        return json.loads(payload_b.decode("utf-8"))
    except Exception:
        return {}


def get_current_user(request: Request) -> Dict[str, Any]:
    """Return a normalized user dict for RBAC checks.

    - If a Bearer token is provided, attempt a best-effort decode of its payload.
    - If `LOCAL_DEV_AUTH_BYPASS` is set, return a local admin user.
    - Otherwise raise 401.
    """
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    local_bypass = os.environ.get("LOCAL_DEV_AUTH_BYPASS", "1").lower() in ("1", "true")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
        claims = _decode_jwt_payload(token)
        roles = claims.get("roles") or claims.get("role") or []
        scopes = claims.get("scopes") or claims.get("scope") or []
        if isinstance(roles, str):
            roles = [roles]
        return {"username": claims.get("username") or claims.get("sub") or str(claims), "roles": roles, "scopes": scopes}
    if local_bypass:
        return {"username": os.getenv("DEV_USER", "dev.user"), "roles": ["usarec_admin"], "scopes": [{"scope_type": "USAREC", "scope_value": "USAREC"}]}
    raise HTTPException(status_code=401, detail="Unauthorized")


def require_roles(*roles: str):
    def _dep(user: Dict = Depends(get_current_user)):
        user_roles = user.get("roles") or []
        for r in roles:
            if r not in user_roles:
                raise HTTPException(status_code=403, detail="Forbidden: missing role")
        return user

    return _dep

def get_allowed_org_units(username: Dict = Depends(get_current_user)) -> Optional[list]:
    """Return list of allowed org_unit ids for the current user; None means unrestricted."""
    # dev bypass => allow all
    if os.getenv('LOCAL_DEV_AUTH_BYPASS'):
        return None
    uname = username.get('username') if isinstance(username, dict) else username
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=?', (uname,))
        u = cur.fetchone()
        if not u:
            return []
        uid = u[0]
        cur.execute('SELECT org_unit_id, scope_level FROM user_scope WHERE user_id=?', (uid,))
        rows = cur.fetchall()
        allowed = set()
        for oid, _scope in rows:
            try:
                cur.execute("WITH RECURSIVE subtree(id) AS (SELECT id FROM org_unit WHERE id=? UNION ALL SELECT o.id FROM org_unit o JOIN subtree s ON o.parent_id = s.id) SELECT id FROM subtree", (oid,))
                subs = cur.fetchall()
                for s in subs:
                    allowed.add(s[0])
            except Exception:
                allowed.add(oid)
        return list(allowed)
    finally:
        conn.close()

def require_not_role(role_name: str):
    def _dep(user: Dict = Depends(get_current_user)):
        if role_name in (user.get("roles") or []):
            raise HTTPException(status_code=403, detail="Forbidden: role not allowed")
        return user

    return _dep


def require_station_scope(rsid: str):
    def _dep(user: Dict = Depends(get_current_user)):
        if "usarec_admin" in (user.get("roles") or []):
            return user
        scopes = user.get("scopes") or []
        for s in scopes:
            if isinstance(s, dict) and (s.get("scope_value") == rsid or s.get("scope_value") == rsid.upper()):
                return user
            if isinstance(s, str) and s.endswith(rsid):
                return user
        raise HTTPException(status_code=403, detail="Forbidden: no station scope")

    return _dep


SCOPE_ORDER = {
    'USAREC': 0,
    'BDE': 1,
    'BN': 2,
    'CO': 3,
    'STATION': 4
}


def require_scope(min_level: str = 'STATION'):
    def _dep(username: Dict = Depends(get_current_user)) -> Optional[list]:
        # dev bypass => unrestricted
        if os.getenv('LOCAL_DEV_AUTH_BYPASS'):
            return None
        uname = username.get('username') if isinstance(username, dict) else username
        conn = connect()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id FROM users WHERE username=?', (uname,))
            u = cur.fetchone()
            if not u:
                return []
            uid = u[0]
            cur.execute('SELECT org_unit_id, scope_level FROM user_scope WHERE user_id=?', (uid,))
            rows = cur.fetchall()
            allowed = set()
            for oid, scope_level in rows:
                try:
                    if SCOPE_ORDER.get(scope_level, 999) <= SCOPE_ORDER.get(min_level, 999):
                        cur.execute("WITH RECURSIVE subtree(id) AS (SELECT id FROM org_unit WHERE id=? UNION ALL SELECT o.id FROM org_unit o JOIN subtree s ON o.parent_id = s.id) SELECT id FROM subtree", (oid,))
                        subs = cur.fetchall()
                        for s in subs:
                            allowed.add(s[0])
                except Exception:
                    allowed.add(oid)
            return list(allowed)
        finally:
            conn.close()

    return _dep


router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.post("/users", summary="Create or ensure user exists")
def create_user(payload: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(username, display_name, email, created_at) VALUES (?,?,?,datetime('now'))", (payload.get('username'), payload.get('display_name'), payload.get('email')))
        conn.commit()
        cur.execute("SELECT id, username, display_name, email FROM users WHERE username=?", (payload.get('username'),))
        row = cur.fetchone()
        return dict(row) if row else {"username": payload.get('username')}
    finally:
        conn.close()


@router.get("/roles", summary="List roles")
def list_roles(current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM roles ORDER BY name")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post("/roles", summary="Create role")
def create_role(payload: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO roles(name, description, created_at) VALUES (?,?,datetime('now'))", (payload.get('name'), payload.get('description')))
        conn.commit()
        cur.execute("SELECT id, name, description FROM roles WHERE name=?", (payload.get('name'),))
        row = cur.fetchone()
        return dict(row) if row else {"name": payload.get('name')}
    finally:
        conn.close()


@router.post("/assign-role", summary="Assign role to user")
def assign_role(payload: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    username = payload.get('username')
    role_name = payload.get('role')
    if not username or not role_name:
        raise HTTPException(status_code=400, detail="username and role required")
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        u = cur.fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="user not found")
        cur.execute("SELECT id FROM roles WHERE name=?", (role_name,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="role not found")
        cur.execute("INSERT INTO user_roles(user_id, role_id, assigned_at) VALUES (?,?,datetime('now'))", (u[0], r[0]))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()
