from fastapi import APIRouter, Depends
from .. import auth
from ..db import connect

router = APIRouter()


@router.get("/me")
def me(effective=Depends(auth.get_effective_user)):
    # Normalize into the requested shape: { user: {...}, permissions: {...}, is_admin: bool }
    user_claim = {
        'id': effective.get('sub'),
        'name': effective.get('name') or '',
    }
    perms_list = effective.get('permissions') or []
    # Start with token-provided permissions as True
    perms_map = {p: True for p in perms_list}
    # attempt to enrich from DB if token subject maps to an internal user id
    try:
        conn = connect()
        cur = conn.cursor()
        uname = effective.get('sub')
        cur.execute('SELECT id, username, display_name, email, tier FROM users WHERE username=?', (uname,))
        row = cur.fetchone()
        if row:
            user_claim = {'id': row['id'], 'username': row['username'], 'display_name': row['display_name'], 'email': row['email'], 'tier': row.get('tier')}
            uid = row['id']
            # start with role_template permissions
            try:
                cur.execute('SELECT role_key FROM user_role_template WHERE user_id=?', (uid,))
                role_keys = [r[0] for r in cur.fetchall()]
                for rk in role_keys:
                    cur.execute('SELECT permission_key, granted FROM role_template_permission WHERE role_key=?', (rk,))
                    for pk, g in cur.fetchall():
                        perms_map[pk] = bool(g)
            except Exception:
                pass
            # apply explicit user_permission overrides
            try:
                cur.execute('SELECT permission_key, granted FROM user_permission WHERE user_id=?', (uid,))
                for pk, g in cur.fetchall():
                    perms_map[pk] = bool(g)
            except Exception:
                pass
            # ensure default perms for all users
            perms_map.setdefault('dashboards.view', True)
            perms_map.setdefault('dashboards.export', True)
            # also expose uppercase canonical aliases for frontend convenience
            if perms_map.get('dashboards.view'):
                perms_map.setdefault('DASHBOARDS_READ', True)
            if perms_map.get('dashboards.export'):
                perms_map.setdefault('EXPORT_DATA', True)
            # datahub aliases
            if perms_map.get('datahub.upload'):
                perms_map.setdefault('DATAHUB_UPLOAD', True)
            if perms_map.get('datahub.view_registry') or perms_map.get('datahub.view_runs'):
                perms_map.setdefault('DATAHUB_READ', True)
            # frontend-friendly canonical aliases (legacy frontend constants)
            if perms_map.get('dashboards.view'):
                perms_map.setdefault('DASHBOARD_READ', True)
            if perms_map.get('dashboards.export'):
                perms_map.setdefault('DASHBOARD_EXPORT', True)
            if perms_map.get('datahub.upload'):
                perms_map.setdefault('DATA_UPLOAD', True)
            if perms_map.get('helpdesk.submit'):
                perms_map.setdefault('HELP_TICKET_CREATE', True)
            if perms_map.get('helpdesk.view_unit') or perms_map.get('helpdesk.view_own'):
                perms_map.setdefault('HELP_TICKET_READ', True)
            if perms_map.get('admin.users.manage'):
                perms_map.setdefault('ADMIN_USERS', True)
            if perms_map.get('admin.audit.view'):
                perms_map.setdefault('ADMIN_AUDIT', True)
            if perms_map.get('admin.thresholds.manage'):
                perms_map.setdefault('ADMIN_THRESHOLDS', True)
            if perms_map.get('admin.datasets.manage'):
                perms_map.setdefault('ADMIN_DATASETS', True)
            if perms_map.get('planning.edit'):
                perms_map.setdefault('PLANNING_EDIT', True)
            if perms_map.get('roi.edit_costs'):
                perms_map.setdefault('ROI_EDIT', True)
            # ROI/planning aliases
            if perms_map.get('roi.view'):
                perms_map.setdefault('ROI_READ', True)
            if perms_map.get('roi.edit_costs'):
                perms_map.setdefault('ROI_EDIT', True)
            if perms_map.get('planning.view'):
                perms_map.setdefault('PLANNING_READ', True)
            if perms_map.get('planning.edit'):
                perms_map.setdefault('PLANNING_EDIT', True)
            if perms_map.get('twg.view'):
                perms_map.setdefault('TWG_READ', True)
            if perms_map.get('twg.edit'):
                perms_map.setdefault('TWG_EDIT', True)
            if perms_map.get('schools.view'):
                perms_map.setdefault('SCHOOLS_READ', True)
            if perms_map.get('schools.edit_contacts'):
                perms_map.setdefault('SCHOOLS_EDIT', True)
            if perms_map.get('budget.view'):
                perms_map.setdefault('BUDGET_READ', True)
            if perms_map.get('budget.write'):
                perms_map.setdefault('BUDGET_EDIT', True)
            if perms_map.get('helpdesk.view_unit') or perms_map.get('helpdesk.view_own'):
                perms_map.setdefault('HELPDESK_READ', True)
            if perms_map.get('helpdesk.submit'):
                perms_map.setdefault('HELPDESK_CREATE_TICKET', True)
            if perms_map.get('helpdesk.manage'):
                perms_map.setdefault('HELPDESK_ADMIN', True)
            if perms_map.get('admin.users.manage'):
                perms_map.setdefault('ADMIN_MANAGE_USERS', True)
            if perms_map.get('admin.permissions.manage'):
                perms_map.setdefault('ADMIN_MANAGE_ROLES', True)
            if perms_map.get('admin.audit.view'):
                perms_map.setdefault('ADMIN_AUDIT_READ', True)
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    is_admin = bool(perms_map.get('admin.permissions.manage') or ('*' in (perms_list or [])))
    # If the effective user provided permissions as a list (master/dev modes),
    # preserve that shape for compatibility with older frontend expectations
    # and specific tests that assert a list is returned.
    perms_out = perms_map
    if isinstance(effective.get('permissions'), list):
        perms_out = effective.get('permissions')

    result = {'user': user_claim, 'permissions': perms_out, 'is_admin': is_admin}
    # include explicit roles when available (used by some tests)
    if effective.get('roles'):
        result['roles'] = effective.get('roles')
    return result
