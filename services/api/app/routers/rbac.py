from fastapi import APIRouter, Depends, HTTPException
import os
from typing import Optional, Dict, Any
from ..db import connect
from fastapi import Depends

router = APIRouter(prefix="/rbac", tags=["rbac"])


def get_current_user(username: Optional[str] = None) -> str:
    """Simple development-friendly current user resolver.

    - If `LOCAL_DEV_AUTH_BYPASS` is set, returns the provided username or 'dev.user'.
    - Otherwise, raises 401 to force proper auth integration.
    """
    if os.getenv("LOCAL_DEV_AUTH_BYPASS"):
        return username or os.getenv("DEV_USER", "dev.user")
    raise HTTPException(status_code=401, detail="authentication required")


def require_role(role_name: str):
    def _dep(user: str = Depends(get_current_user)):
        # lightweight check against DB roles; allow if bypass enabled and no roles present
        conn = connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id=r.id JOIN users u ON u.id=ur.user_id WHERE u.username=? LIMIT 1", (user,))
            row = cur.fetchone()
            if not row:
                # allow admin bypass when LOCAL_DEV_AUTH_BYPASS and DEV_ADMIN set
                if os.getenv("LOCAL_DEV_AUTH_BYPASS"):
                    return user
                raise HTTPException(status_code=403, detail="insufficient role")
            if row[0] != role_name and os.getenv("LOCAL_DEV_AUTH_BYPASS") is None:
                raise HTTPException(status_code=403, detail="insufficient role")
            return user
        finally:
            conn.close()

    return _dep


def get_user_scopes(username: str) -> list:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=?', (username,))
        u = cur.fetchone()
        if not u:
            return []
        uid = u[0]
        cur.execute('SELECT org_unit_id, scope_level FROM user_scope WHERE user_id=?', (uid,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_allowed_org_units(username: str = Depends(get_current_user)) -> Optional[list]:
    """Return list of allowed org_unit ids for the current user; None means unrestricted."""
    # dev bypass => allow all
    if os.getenv('LOCAL_DEV_AUTH_BYPASS'):
        return None
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=?', (username,))
        u = cur.fetchone()
        if not u:
            return []
        uid = u[0]
        cur.execute('SELECT org_unit_id, scope_level FROM user_scope WHERE user_id=?', (uid,))
        rows = cur.fetchall()
        # rows contain tuples (org_unit_id, scope_level)
        orgs = [(r[0], r[1]) for r in rows]
        # expand each org to its subtree using recursive CTE
        allowed = set()
        for oid, _scope in orgs:
            try:
                cur.execute("WITH RECURSIVE subtree(id) AS (SELECT id FROM org_unit WHERE id=? UNION ALL SELECT o.id FROM org_unit o JOIN subtree s ON o.parent_id = s.id) SELECT id FROM subtree", (oid,))
                subs = cur.fetchall()
                for s in subs:
                    allowed.add(s[0])
            except Exception:
                # fallback: include the single id
                allowed.add(oid)
        return list(allowed)
    finally:
        conn.close()


SCOPE_ORDER = {
    'USAREC': 0,
    'BDE': 1,
    'BN': 2,
    'CO': 3,
    'STATION': 4
}


def require_scope(min_level: str = 'STATION'):
    """Dependency factory that returns allowed org_unit ids for the current user

    - If LOCAL_DEV_AUTH_BYPASS is set, returns None (unrestricted).
    - Otherwise, returns a list of org_unit ids that the user may access, or [] if none.
    - `min_level` indicates the granularity required by the endpoint; users with broader
      scopes (e.g. USAREC) are allowed.
    """
    def _dep(username: str = Depends(get_current_user)) -> Optional[list]:
        if os.getenv('LOCAL_DEV_AUTH_BYPASS'):
            return None
        conn = connect()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id FROM users WHERE username=?', (username,))
            u = cur.fetchone()
            if not u:
                return []
            uid = u[0]
            cur.execute('SELECT org_unit_id, scope_level FROM user_scope WHERE user_id=?', (uid,))
            rows = cur.fetchall()
            allowed = set()
            for oid, scope_level in rows:
                # allow if user's scope level is broader or equal to required min_level
                try:
                    if SCOPE_ORDER.get(scope_level, 999) <= SCOPE_ORDER.get(min_level, 999):
                        # expand subtree
                        try:
                            cur.execute("WITH RECURSIVE subtree(id) AS (SELECT id FROM org_unit WHERE id=? UNION ALL SELECT o.id FROM org_unit o JOIN subtree s ON o.parent_id = s.id) SELECT id FROM subtree", (oid,))
                            subs = cur.fetchall()
                            for s in subs:
                                allowed.add(s[0])
                        except Exception:
                            allowed.add(oid)
                except Exception:
                    # if scope parsing fails, be conservative: skip
                    continue
            return list(allowed)
        finally:
            conn.close()

    return _dep


@router.post("/users", summary="Create or ensure user exists")
def create_user(payload: Dict[str, Any], current_user: str = Depends(get_current_user)):
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
def list_roles():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM roles ORDER BY name")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post("/roles", summary="Create role")
def create_role(payload: Dict[str, Any], current_user: str = Depends(get_current_user)):
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
def assign_role(payload: Dict[str, Any], current_user: str = Depends(get_current_user)):
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
