from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
import json
import os
import re
from ..routers import rbac
from ..db import connect
import sqlite3
from .. import database as _dbmod
from ..services import adaptive_update_engine

router = APIRouter(prefix="/v2/admin", tags=["admin"])


def _is_safe_select_sql(sql: str) -> bool:
    if not isinstance(sql, str):
        return False
    s = sql.strip().rstrip(';').strip()
    if not s:
        return False
    if not s.lower().startswith('select'):
        return False
    # Block obvious mutation or multi-statement patterns.
    banned = [
        r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|vacuum|pragma|reindex)\b",
        r";",
        r"--",
        r"/\*",
    ]
    return not any(re.search(p, s, flags=re.IGNORECASE) for p in banned)


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


@router.get('/controlled-learning/proposals')
def list_controlled_learning_proposals(
    scope_type: str = 'USAREC',
    scope_value: str = 'USAREC',
    approval_state: str = '',
    limit: int = 200,
    current_user: Dict = Depends(require_admin_manage),
):
    db = next(_dbmod.get_db())
    try:
        return adaptive_update_engine.list_proposals(
            db,
            scope_type=scope_type,
            scope_value=scope_value,
            approval_state=(approval_state or None),
            limit=limit,
        )
    finally:
        try:
            if _dbmod._shared_session is None:
                db.close()
        except Exception:
            pass


@router.put('/controlled-learning/proposals/{proposal_id}/state')
def update_controlled_learning_proposal_state(
    proposal_id: str,
    payload: Dict[str, Any],
    current_user: Dict = Depends(require_admin_manage),
):
    new_state = str(payload.get('approval_state') or '').strip().lower()
    if not new_state:
        raise HTTPException(status_code=400, detail='approval_state required')

    db = next(_dbmod.get_db())
    try:
        result = adaptive_update_engine.update_proposal_state(db, proposal_id, new_state)
        if result.get('status') == 'invalid':
            raise HTTPException(status_code=400, detail=result.get('message') or 'invalid state')
        if result.get('status') == 'no_data':
            raise HTTPException(status_code=404, detail=result.get('message') or 'proposal not found')
        return result
    finally:
        try:
            if _dbmod._shared_session is None:
                db.close()
        except Exception:
            pass


@router.get('/users')
def list_users(current_user: Dict = Depends(require_admin_manage)):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT id, username, display_name, email, created_at, record_status FROM users ORDER BY username')
        except sqlite3.OperationalError:
            # test environments may use an empty/temp DB; surface empty user list instead of error
            return {'users': []}
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
    raw = file.file.read()
    try:
        s = raw.decode('utf-8', errors='ignore')
    except Exception:
        s = ''
    if os.getenv('ALLOW_SIMULATION_IMPORTS') != '1':
        import re
        sim_pat = re.compile(r"\bSIM_|\bsim-|\bdemo-|\bdemo_", re.IGNORECASE)
        if sim_pat.search(s):
            raise HTTPException(status_code=400, detail='Import rejected: contains simulation/demo markers. Set ALLOW_SIMULATION_IMPORTS=1 to override.')
    data = s
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


@router.get('/kpi-thresholds')
def get_kpi_thresholds(current_user: Dict = Depends(require_admin_manage)):
    """Get all KPI threshold settings from roi_thresholds table."""
    conn = connect()
    try:
        cur = conn.cursor()
        thresholds: Dict[str, Any] = {}
        
        # Check if roi_thresholds table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roi_thresholds'")
        if not cur.fetchone():
            return {'status': 'ok', 'thresholds': {}}
        
        # Fetch all thresholds
        cur.execute("SELECT metric_key, value FROM roi_thresholds ORDER BY metric_key ASC")
        for row in cur.fetchall():
            thresholds[str(row[0])] = {
                'metric_key': str(row[0]),
                'value': float(row[1] or 0),
                'description': _threshold_description(str(row[0]))
            }
        
        return {'status': 'ok', 'thresholds': thresholds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put('/kpi-thresholds/{metric_key}')
def update_kpi_threshold(metric_key: str, payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    """Update a KPI threshold value."""
    new_value = payload.get('value')
    if new_value is None:
        raise HTTPException(status_code=400, detail='value required')
    
    try:
        new_value = float(new_value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail='value must be numeric')
    
    # Sanitize metric_key to prevent injection
    metric_key = str(metric_key).strip()
    if not metric_key or not all(c.isalnum() or c in '_-' for c in metric_key):
        raise HTTPException(status_code=400, detail='invalid metric_key')
    
    conn = connect()
    try:
        cur = conn.cursor()
        
        # Check if roi_thresholds table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roi_thresholds'")
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail='roi_thresholds table not found')
        
        # Update or insert threshold
        cur.execute(
            "INSERT OR REPLACE INTO roi_thresholds(metric_key, value) VALUES (?, ?)",
            (metric_key, new_value)
        )
        conn.commit()
        
        return {
            'status': 'ok',
            'metric_key': metric_key,
            'value': new_value,
            'updated_by': current_user.get('username', 'system'),
            'updated_at': __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


def _threshold_description(metric_key: str) -> str:
    """Return user-friendly description for a metric key."""
    descriptions = {
        'cpl_target': 'Cost Per Lead (CPL) target threshold in dollars',
        'cpc_target': 'Cost Per Contract (CPC) target threshold in dollars',
        'ctr_minimum': 'Minimum Click-Through Rate (CTR) target as percentage',
        'engagement_rate_minimum': 'Minimum Engagement Rate target as percentage',
        'conversion_rate_minimum': 'Minimum Conversion Rate target as percentage',
        'roi_minimum': 'Minimum ROI target as decimal (e.g., 0.2 = 20%)',
        'flash_to_bang_days': 'Target days from lead to enlistment',
    }
    return descriptions.get(metric_key, f'Threshold for {metric_key}')


@router.get('/audit-logs')
def get_audit_logs(
    start_at: Optional[str] = None,
    end_at: Optional[str] = None,
    user: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: Dict = Depends(require_admin_manage),
):
    """Retrieve audit logs for governance visibility with filtering."""
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)

    conn = connect()
    try:
        cur = conn.cursor()

        # Detect which audit table is available and map field names.
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        has_audit_log = cur.fetchone() is not None
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        has_audit_logs = cur.fetchone() is not None

        if not has_audit_log and not has_audit_logs:
            return {'status': 'ok', 'items': [], 'total': 0, 'source_table': None}

        if has_audit_log:
            table = 'audit_log'
            cur.execute("PRAGMA table_info('audit_log')")
            cols = {str(r[1]) for r in cur.fetchall()}

            actor_col = 'who' if 'who' in cols else ('username' if 'username' in cols else "''")
            action_col = 'action' if 'action' in cols else "''"
            created_col = 'created_at' if 'created_at' in cols else "''"
            entity_type_col = 'entity' if 'entity' in cols else ('resource' if 'resource' in cols else "''")
            entity_id_col = 'entity_id' if 'entity_id' in cols else "''"
            detail_col = 'meta_json' if 'meta_json' in cols else ('detail' if 'detail' in cols else "''")

            select_sql = (
                f"SELECT id, {actor_col} AS actor, {action_col} AS action, "
                f"{entity_type_col} AS entity_type, CAST({entity_id_col} AS TEXT) AS entity_id, "
                f"{detail_col} AS detail_json, {created_col} AS created_at"
            )
        else:
            table = 'audit_logs'
            actor_col = 'actor'
            action_col = 'action'
            created_col = 'created_at'
            select_sql = "SELECT id, actor, action, entity_type, entity_id, COALESCE(after_json, before_json) AS detail_json, created_at"

        where_parts = []
        params = []

        if start_at:
            where_parts.append(f"{created_col} >= ?")
            params.append(start_at)
        if end_at:
            where_parts.append(f"{created_col} <= ?")
            params.append(end_at)
        if user:
            where_parts.append(f"lower(COALESCE({actor_col}, '')) LIKE lower(?)")
            params.append(f"%{user}%")
        if action:
            where_parts.append(f"lower(COALESCE({action_col}, '')) LIKE lower(?)")
            params.append(f"%{action}%")

        where_sql = f" WHERE {' AND '.join(where_parts)}" if where_parts else ''

        cur.execute(f"SELECT COUNT(1) FROM {table}{where_sql}", tuple(params))
        total = int((cur.fetchone() or [0])[0] or 0)

        query = (
            f"{select_sql} FROM {table}{where_sql} "
            f"ORDER BY COALESCE({created_col}, '') DESC LIMIT ? OFFSET ?"
        )
        query_params = params + [limit, offset]
        cur.execute(query, tuple(query_params))

        items = []
        for r in cur.fetchall():
            detail_obj = None
            detail_json = r[5]
            if detail_json:
                try:
                    detail_obj = json.loads(detail_json)
                except Exception:
                    detail_obj = {'raw': str(detail_json)}

            items.append({
                'id': r[0],
                'actor': r[1],
                'action': r[2],
                'entity_type': r[3],
                'entity_id': r[4],
                'detail': detail_obj,
                'created_at': r[6],
            })

        return {
            'status': 'ok',
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset,
            'source_table': table,
        }
    finally:
        conn.close()


@router.post('/query')
def admin_query(payload: Dict[str, Any], current_user: Dict = Depends(require_admin_manage)):
    sql = (payload.get('sql') or '').strip()
    limit = payload.get('limit', 100)

    try:
        limit = int(limit)
    except Exception:
        limit = 100
    limit = max(1, min(limit, 1000))

    if not _is_safe_select_sql(sql):
        raise HTTPException(status_code=400, detail='Only single SELECT statements are allowed')

    conn = connect()
    try:
        cur = conn.cursor()
        wrapped_sql = f"SELECT * FROM ({sql}) LIMIT ?"
        cur.execute(wrapped_sql, (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]
        result_rows = [dict(r) if hasattr(r, 'keys') else {cols[i]: r[i] for i in range(len(cols))} for r in rows]
        return {'status': 'ok', 'query': sql, 'columns': cols, 'rows': result_rows, 'count': len(result_rows)}
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f'SQL error: {str(e)}')
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
