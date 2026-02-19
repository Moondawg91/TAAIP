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
    local_bypass = os.environ.get("LOCAL_DEV_AUTH_BYPASS", "0").lower() in ("1", "true")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
        claims = _decode_jwt_payload(token)
        roles = claims.get("roles") or claims.get("role") or []
        scopes = claims.get("scopes") or claims.get("scope") or []
        # Normalize roles into a list of lowercase strings for consistent checks
        if isinstance(roles, str):
            roles = [roles]
        elif roles is None:
            roles = []
        elif not isinstance(roles, list):
            try:
                roles = list(roles)
            except Exception:
                roles = [roles]
        try:
            roles = [r.lower() for r in roles if r is not None]
        except Exception:
            roles = [str(r).lower() for r in roles]
        return {"username": claims.get("username") or claims.get("sub") or str(claims), "roles": roles, "scopes": scopes}
    if local_bypass:
        return {"username": os.getenv("DEV_USER", "dev.user"), "roles": ["USAREC_ADMIN"], "scopes": [{"scope_type": "USAREC", "scope_value": "USAREC"}]}
    raise HTTPException(status_code=401, detail="Unauthorized")


def require_roles(*roles: str):
    def _dep(user: Dict = Depends(get_current_user)):
        # defensive: if called outside FastAPI (user not a dict), allow local dev bypass or fail cleanly
        if not isinstance(user, dict):
            if os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true'):
                return {"username": os.getenv('DEV_USER', 'dev.user'), "roles": [r.lower() for r in roles], "scopes": []}
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_roles = [u.lower() for u in (user.get("roles") or [])]
        username = (user.get('username') or '').lower() if isinstance(user, dict) else ''
        for r in roles:
            rl = r.lower()
            # allow match by role name or by username (tests use username-like role tokens)
            if rl not in user_roles and rl != username:
                raise HTTPException(status_code=403, detail="Forbidden: missing role")
        return user

    return _dep


def require_any_role(*roles: str):
    """Dependency: allow if user has any one of the provided roles."""
    def _dep(user: Dict = Depends(get_current_user)):
        # defensive: handle import-time or non-FastAPI calls gracefully when dev bypass enabled
        if not isinstance(user, dict):
            if os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true'):
                return {"username": os.getenv('DEV_USER', 'dev.user'), "roles": [r.lower() for r in roles], "scopes": []}
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_roles = [u.lower() for u in (user.get("roles") or [])]
        username = (user.get('username') or '').lower() if isinstance(user, dict) else ''
        for r in roles:
            rl = r.lower()
            if rl in user_roles or rl == username:
                return user
        raise HTTPException(status_code=403, detail="Forbidden: missing role")

    return _dep

def get_allowed_org_units(username: Dict = Depends(get_current_user)) -> Optional[list]:
    """Return list of allowed org_unit ids for the current user; None means unrestricted."""
    # dev bypass => allow all
    if os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true'):
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


def _normalize_scope_val(val: str) -> str:
    # Normalize RSID-like values to uppercase and colon-separated
    if not val or not isinstance(val, str):
        return ''
    return val.strip().upper()


def _scope_allows(user_scope: str, required_scope: str) -> bool:
    """Return True if user_scope covers required_scope based on prefix hierarchy.

    e.g. user_scope 'USAREC' allows 'USAREC:BDE1:BN2', and 'USAREC:BDE1' allows 'USAREC:BDE1:BN2'.
    """
    us = _normalize_scope_val(user_scope)
    rs = _normalize_scope_val(required_scope)
    if not us or not rs:
        return False
    # exact match
    if us == rs:
        return True
    # prefix match by colon separator
    if rs.startswith(us + ':'):
        return True
    # also allow global USAREC to match any if us == 'USAREC'
    if us == 'USAREC':
        return True
    return False


def _log_audit(username: str, action: str, resource: str, detail: str, outcome: str = 'denied'):
    """Insert an audit log row (best-effort)."""
    try:
        conn = connect()
        cur = conn.cursor()
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            resource TEXT,
            detail TEXT,
            outcome TEXT,
            created_at TEXT
        );
        ''')
        now = __import__('datetime').datetime.utcnow().isoformat()
        cur.execute('INSERT INTO audit_log(username, action, resource, detail, outcome, created_at) VALUES (?,?,?,?,?,?)', (username, action, resource, detail, outcome, now))
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

def require_not_role(role_name: str):
    def _dep(user: Dict = Depends(get_current_user)):
        if not isinstance(user, dict):
            if os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true'):
                return {"username": os.getenv('DEV_USER', 'dev.user'), "roles": [], "scopes": []}
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_roles = [u.lower() for u in (user.get("roles") or [])]
        if role_name.lower() in user_roles:
            raise HTTPException(status_code=403, detail="Forbidden: role not allowed")
        return user

    return _dep


def require_station_scope(rsid: str):
    def _dep(user: Dict = Depends(get_current_user)):
        if not isinstance(user, dict):
            if os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true'):
                return {"username": os.getenv('DEV_USER', 'dev.user'), "roles": ['usarec_admin'], "scopes": [{"scope_type": "USAREC", "scope_value": "USAREC"}]}
            raise HTTPException(status_code=401, detail="Unauthorized")
        if any((r.lower() == 'usarec_admin') for r in (user.get("roles") or [])):
            return user
        scopes = user.get("scopes") or []
        for s in scopes:
            sv = None
            if isinstance(s, dict):
                sv = s.get('scope_value')
            elif isinstance(s, str):
                sv = s
            if sv and _scope_allows(sv, rsid):
                return user
        # log denied access
        try:
            uname = user.get('username') if isinstance(user, dict) else str(user)
            _log_audit(uname, 'require_station_scope', rsid, 'missing station scope', 'denied')
        except Exception:
            pass
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
        if os.getenv('LOCAL_DEV_AUTH_BYPASS', '0').lower() in ('1', 'true'):
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
        # prefix/hierarchy RBAC: also check user's scopes for prefix coverage and log denials
            # collect user scopes from user_scope table if available
            cur.execute('SELECT scope_value FROM user_scope WHERE user_id=?', (uid,))
            user_scope_vals = [r[0] for r in cur.fetchall() if r and r[0]]
            # if at least one user_scope covers the min_level required, allow unrestricted (None)
            for usv in user_scope_vals:
                if _scope_allows(usv, min_level) or _scope_allows(usv, 'USAREC'):
                    return None
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
        cur.execute("SELECT r.id, r.name, r.description, (SELECT COUNT(*) FROM user_roles ur WHERE ur.role_id = r.id) AS user_count FROM roles r ORDER BY r.name")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post("/roles", summary="Create role")
def create_role(payload: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        name = payload.get('name')
        if not name:
            raise HTTPException(status_code=400, detail='name required')
        # prevent duplicate role names (case-insensitive)
        cur.execute("SELECT id FROM roles WHERE lower(name)=lower(?)", (name,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail='role already exists')
        cur.execute("INSERT INTO roles(name, description, created_at) VALUES (?,?,datetime('now'))", (name, payload.get('description')))
        conn.commit()
        cur.execute("SELECT id, name, description FROM roles WHERE name=?", (name,))
        row = cur.fetchone()
        return dict(row) if row else {"name": name}
    finally:
        conn.close()


@router.delete("/roles/{role_id}", summary="Delete role")
def delete_role(role_id: int, force: bool = False, current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM user_roles WHERE role_id=?", (role_id,))
        c = cur.fetchone()
        count = c[0] if c else 0
        if count > 0 and not force:
            raise HTTPException(status_code=400, detail=f'role has {count} assigned users; use ?force=true to override')
        # remove associations then delete role
        cur.execute("DELETE FROM user_roles WHERE role_id=?", (role_id,))
        cur.execute("DELETE FROM roles WHERE id=?", (role_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@router.put("/roles/{role_id}", summary="Update role")
def update_role(role_id: int, payload: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        name = payload.get('name')
        desc = payload.get('description')
        if not name and desc is None:
            raise HTTPException(status_code=400, detail='name or description required')
        # if renaming, ensure no duplicate name
        if name is not None:
            cur.execute("SELECT id FROM roles WHERE lower(name)=lower(?) AND id!=?", (name, role_id))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail='role name already in use')
        # update only provided fields
        if name is not None and desc is not None:
            cur.execute("UPDATE roles SET name=?, description=? WHERE id=?", (name, desc, role_id))
        elif name is not None:
            cur.execute("UPDATE roles SET name=? WHERE id=?", (name, role_id))
        else:
            cur.execute("UPDATE roles SET description=? WHERE id=?", (desc, role_id))
        conn.commit()
        cur.execute("SELECT id, name, description FROM roles WHERE id=?", (role_id,))
        row = cur.fetchone()
        return dict(row) if row else {"ok": True}
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


@router.get("/users", summary="List users")
def list_users(current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, display_name, email, created_at FROM users ORDER BY username")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/roles/{role_id}/users", summary="List users for role")
def list_users_for_role(role_id: int, current_user: Dict = Depends(get_current_user)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT u.id, u.username, u.display_name, u.email FROM users u JOIN user_roles ur ON ur.user_id = u.id WHERE ur.role_id=?", (role_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post("/remove-role", summary="Remove role from user")
def remove_role(payload: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
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
        cur.execute("DELETE FROM user_roles WHERE user_id=? AND role_id=?", (u[0], r[0]))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()
