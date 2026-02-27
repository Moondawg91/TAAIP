from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import json
from ..routers import rbac
from ..db import connect

router = APIRouter(prefix="/api/v2/admin", tags=["admin"])


def _is_admin_user(user: Dict[str, Any]) -> bool:
    # allow wildcard perms or system_admin role
    if not isinstance(user, dict):
        return False
    perms = user.get('permissions') or []
    roles = [r.lower() for r in (user.get('roles') or [])]
    if '*' in perms:
        return True
    if 'system_admin' in roles:
        return True
    # if token carried admin.permissions.manage
    if 'admin.permissions.manage' in perms:
        return True
    # else fallback to DB check using username
    try:
        conn = connect()
        cur = conn.cursor()
        uname = user.get('username')
        cur.execute('SELECT id FROM users WHERE username=?', (uname,))
        u = cur.fetchone()
        if not u:
            return False
        uid = u[0]
        cur.execute('SELECT COUNT(*) FROM user_permission WHERE user_id=? AND permission_key=? AND granted=1', (uid, 'admin.permissions.manage'))
        c = cur.fetchone()
        return bool(c and c[0] > 0)
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def require_admin_manage(user: Dict = Depends(rbac.get_current_user)):
    if not _is_admin_user(user):
        raise HTTPException(status_code=403, detail='admin.permissions.manage required')
    return user


@router.get('/users')
def list_users(current_user: Dict = Depends(require_admin_manage)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, username, display_name, email, created_at, record_status FROM users ORDER BY username')
        users = []
        for r in cur.fetchall():
            u = dict(r)
            uid = u.get('id')
            # roles from user_role_template
            try:
                cur.execute('SELECT role_key FROM user_role_template WHERE user_id=?', (uid,))
                u['roles'] = [row[0] for row in cur.fetchall()]
            except Exception:
                u['roles'] = []
            # overrides
            try:
                cur.execute('SELECT permission_key, granted FROM user_permission WHERE user_id=?', (uid,))
                overrides = {row[0]: bool(row[1]) for row in cur.fetchall()}
                u['overrides'] = overrides
            except Exception:
                u['overrides'] = {}
            # effective permissions: start with role defaults then apply overrides
            eff = {}
            try:
                # gather role permissions
                for rk in (u.get('roles') or []):
                    cur.execute('SELECT permission_key, granted FROM role_template_permission WHERE role_key=?', (rk,))
                    for pk, g in cur.fetchall():
                        eff[pk] = bool(g)
                # apply overrides
                for pk, val in u['overrides'].items():
                    eff[pk] = bool(val)
            except Exception:
                pass
            u['effective_permissions'] = eff
            users.append(u)
        return {'users': users}
    finally:
        conn.close()


@router.post('/users')
def create_user(payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    username = payload.get('username')
    display_name = payload.get('display_name')
    email = payload.get('email')
    tier = payload.get('tier')
    if not username:
        raise HTTPException(status_code=400, detail='username required')
    conn = connect()
    try:
        cur = conn.cursor()
        # ensure tier column exists
        cols = [c[1] for c in cur.execute("PRAGMA table_info('users')").fetchall()]
        if 'tier' not in cols:
            try:
                cur.execute('ALTER TABLE users ADD COLUMN tier TEXT')
            except Exception:
                pass
        cur.execute('INSERT OR IGNORE INTO users(username, display_name, email, created_at, tier, record_status) VALUES (?,?,?,?,?,?)', (username, display_name, email, tier, 'active'))
        conn.commit()
        cur.execute('SELECT id, username, display_name, email, created_at, tier FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        if row:
            uid = row[0]
            _ensure_default_permissions_for_user(conn, uid, granted_by=(current_user.get('username') or 'system'))
            # also ensure baseline role assignment via new seed helper if available
            try:
                from .. import seed_rbac
                seed_rbac.ensure_user_baseline(uid)
            except Exception:
                pass
            conn.commit()
            return dict(row)
        return {'username': username}
    finally:
        conn.close()



@router.post('/users/invite')
def invite_user(payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    email = payload.get('email')
    name = payload.get('name')
    roles = payload.get('roles') or []
    if not email:
        raise HTTPException(status_code=400, detail='email required')
    conn = connect()
    try:
        cur = conn.cursor()
        # create or ensure user
        cur.execute('INSERT OR IGNORE INTO users(username, display_name, email, created_at, record_status) VALUES (?,?,?,datetime(\'now\'),?)', (email, name, email, 'invited'))
        conn.commit()
        cur.execute('SELECT id FROM users WHERE username=?', (email,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail='failed to create user')
        uid = row[0]
        # assign roles in user_role_template
        try:
            cur.execute('DELETE FROM user_role_template WHERE user_id=?', (uid,))
        except Exception:
            pass
        for rk in roles:
            try:
                cur.execute('INSERT OR IGNORE INTO user_role_template(user_id, role_key, assigned_at) VALUES (?,?,?)', (uid, rk, __import__('datetime').datetime.utcnow().isoformat()))
            except Exception:
                pass
        # create invite token
        import uuid
        token = f"invite_{uuid.uuid4().hex}"
        now = __import__('datetime').datetime.utcnow().isoformat()
        try:
            cur.execute('INSERT OR REPLACE INTO invite_token(token, user_id, email, created_by, created_at) VALUES (?,?,?,?,?)', (token, uid, email, current_user.get('username'), now))
            conn.commit()
        except Exception:
            pass
        return {'user_id': uid, 'status': 'invited', 'invite_token': token, 'invite_link': f'/invite/{token}'}
    finally:
        conn.close()


from fastapi import UploadFile, File


@router.post('/users/import')
def import_users(file: UploadFile = File(...), current_user: Dict = Depends(require_admin_manage)):
    """Import users via CSV multipart file. Columns: email,name,roles (comma-separated)"""
    import csv, io
    data = file.file.read().decode('utf-8')
    sio = io.StringIO(data)
    reader = csv.DictReader(sio)
    created = 0
    updated = 0
    skipped = 0
    errors = []
    conn = connect()
    try:
        cur = conn.cursor()
        now = __import__('datetime').datetime.utcnow().isoformat()
        for i, row in enumerate(reader, start=1):
            try:
                email = (row.get('email') or '').strip()
                name = (row.get('name') or '').strip()
                roles = [r.strip() for r in ((row.get('roles') or '')).split(',') if r.strip()]
                if not email:
                    skipped += 1
                    continue
                # upsert user
                cur.execute('SELECT id FROM users WHERE username=?', (email,))
                existing = cur.fetchone()
                if existing:
                    uid = existing[0]
                    cur.execute('UPDATE users SET display_name=?, email=?, updated_at=? WHERE id=?', (name, email, now, uid))
                    updated += 1
                else:
                    cur.execute('INSERT INTO users(username, display_name, email, created_at, record_status) VALUES (?,?,?,datetime(\'now\'),?)', (email, name, email, 'invited'))
                    uid = cur.lastrowid
                    created += 1
                # assign roles
                try:
                    cur.execute('DELETE FROM user_role_template WHERE user_id=?', (uid,))
                except Exception:
                    pass
                for rk in roles:
                    try:
                        cur.execute('INSERT OR IGNORE INTO user_role_template(user_id, role_key, assigned_at) VALUES (?,?,?)', (uid, rk, now))
                    except Exception:
                        pass
                # ensure default permissions exist for new users
                try:
                    _ensure_default_permissions_for_user(conn, uid, granted_by=(current_user.get('username') or 'system'))
                except Exception:
                    pass
            except Exception as e:
                errors.append({'row': i, 'error': str(e)})
        conn.commit()
    finally:
        conn.close()
    return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors}


@router.put('/users/{user_id}/roles')
def set_user_roles(user_id: int, payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    roles = payload.get('roles') or []
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE id=?', (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='user not found')
        # replace roles
        cur.execute('DELETE FROM user_role_template WHERE user_id=?', (user_id,))
        now = __import__('datetime').datetime.utcnow().isoformat()
        for rk in roles:
            try:
                cur.execute('INSERT INTO user_role_template(user_id, role_key, assigned_at) VALUES (?,?,?)', (user_id, rk, now))
            except Exception:
                pass
        conn.commit()
        # audit
        try:
            cur.execute('INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)', (current_user.get('username'), 'ROLE_ASSIGNED', 'user', user_id, json.dumps({'roles': roles}), now))
            conn.commit()
        except Exception:
            pass
        return {'ok': True}
    finally:
        conn.close()


@router.put('/users/{user_id}/permissions')
def set_user_permission_overrides(user_id: int, payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    overrides = payload.get('overrides') or {}
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE id=?', (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='user not found')
        now = __import__('datetime').datetime.utcnow().isoformat()
        for pk, val in overrides.items():
            try:
                granted = 1 if bool(val) else 0
                cur.execute('INSERT OR REPLACE INTO user_permission(user_id, permission_key, granted, granted_by, granted_at) VALUES (?,?,?,?,?)', (user_id, pk, granted, current_user.get('username'), now))
            except Exception:
                pass
        conn.commit()
        try:
            cur.execute('INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)', (current_user.get('username'), 'PERM_OVERRIDE_SET', 'user', user_id, json.dumps({'overrides': overrides}), now))
            conn.commit()
        except Exception:
            pass
        return {'ok': True}
    finally:
        conn.close()


@router.put('/users/{user_id}/status')
def set_user_status(user_id: int, payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    status = payload.get('status')
    if status not in ('invited', 'active', 'disabled'):
        raise HTTPException(status_code=400, detail='invalid status')
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE users SET record_status=?, updated_at=? WHERE id=?', (status, __import__('datetime').datetime.utcnow().isoformat(), user_id))
        conn.commit()
        try:
            cur.execute('INSERT INTO audit_log(who, action, entity, entity_id, meta_json, created_at) VALUES (?,?,?,?,?,?)', (current_user.get('username'), 'USER_STATUS_CHANGED', 'user', user_id, json.dumps({'status': status}), __import__('datetime').datetime.utcnow().isoformat()))
            conn.commit()
        except Exception:
            pass
        return {'ok': True}
    finally:
        conn.close()


def _ensure_default_permissions_for_user(conn, user_id: int, granted_by: str = 'system'):
    cur = conn.cursor()
    defaults = [
        'dashboards.view', 'dashboards.export', 'pages.command_center.view', 'pages.system_status.view', 'helpdesk.submit', 'helpdesk.view_own'
    ]
    now = __import__('datetime').datetime.utcnow().isoformat()
    for p in defaults:
        cur.execute('INSERT OR IGNORE INTO user_permission(user_id, permission_key, granted, granted_by, granted_at) VALUES (?,?,?,?,?)', (user_id, p, 1, granted_by, now))
    # also insert uppercase canonical aliases for compatibility
    try:
        cur.execute('INSERT OR IGNORE INTO user_permission(user_id, permission_key, granted, granted_by, granted_at) VALUES (?,?,?,?,?)', (user_id, 'DASHBOARDS_READ', 1, granted_by, now))
        cur.execute('INSERT OR IGNORE INTO user_permission(user_id, permission_key, granted, granted_by, granted_at) VALUES (?,?,?,?,?)', (user_id, 'EXPORT_DATA', 1, granted_by, now))
    except Exception:
        pass


@router.get('/permissions/registry')
def list_permission_registry(current_user: Dict = Depends(require_admin_manage)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT key, description, category FROM permission ORDER BY category, key')
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/users/{user_id}/permissions')
def get_user_permissions(user_id: int, current_user: Dict = Depends(require_admin_manage)):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT permission_key, granted, granted_by, granted_at FROM user_permission WHERE user_id=?', (user_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/users/{user_id}/effective-access')
def get_user_effective_access(user_id: int, current_user: Dict = Depends(require_admin_manage)):
    """Return roles and effective permissions for a given user id."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, username, display_name, email FROM users WHERE id=?', (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='user not found')
        user = dict(row)
        # gather role keys
        cur.execute('SELECT r.role_key FROM role r JOIN user_role ur ON ur.role_id=r.id WHERE ur.user_id=?', (user_id,))
        roles = [r[0] for r in cur.fetchall()]
        # use seed helper if available for effective perms
        perms = []
        try:
            from .. import seed_rbac
            perms = seed_rbac.get_effective_permissions_for_user(user_id)
        except Exception:
            # fallback: gather from existing legacy tables
            try:
                cur.execute('SELECT permission_key FROM user_permission WHERE user_id=? AND granted=1', (user_id,))
                perms = [r[0] for r in cur.fetchall()]
            except Exception:
                perms = []
        return {'user': user, 'roles': roles, 'effective_permissions': perms}
    finally:
        conn.close()


@router.post('/users/{user_id}/permissions/grant')
def grant_permission(user_id: int, payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    key = payload.get('permission_key')
    if not key:
        raise HTTPException(status_code=400, detail='permission_key required')
    conn = connect()
    try:
        cur = conn.cursor()
        now = __import__('datetime').datetime.utcnow().isoformat()
        # ensure permission exists
        cur.execute('SELECT key FROM permission WHERE key=?', (key,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='permission not found')
        cur.execute('INSERT OR REPLACE INTO user_permission(user_id, permission_key, granted, granted_by, granted_at) VALUES (?,?,?,?,?)', (user_id, key, 1, current_user.get('username'), now))
        conn.commit()
        return {'ok': True}
    finally:
        conn.close()


@router.post('/users/{user_id}/permissions/revoke')
def revoke_permission(user_id: int, payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    key = payload.get('permission_key')
    if not key:
        raise HTTPException(status_code=400, detail='permission_key required')
    conn = connect()
    try:
        cur = conn.cursor()
        # remove explicit grant rows (we keep it simple: delete)
        cur.execute('DELETE FROM user_permission WHERE user_id=? AND permission_key=?', (user_id, key))
        conn.commit()
        return {'ok': True}
    finally:
        conn.close()
