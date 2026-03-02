import json
import logging
from . import db

_log = logging.getLogger("seed_rbac")

# Permissions and roles as requested
PERMISSIONS = [
    ("dashboards.read", "Read Dashboards", "Can view dashboards and pages."),
    ("export.any", "Export Data", "Can export dashboards and data (rendered/table/raw where available)."),
    ("master.access", "Master Access", "Full access override (owner/master)."),

    ("cmd.view", "Command Center View", "View Command Center summary and command intelligence."),
    ("cmd.alerts.manage", "Manage Alerts", "Create/edit alert thresholds and alert content."),
    ("cmd.recommendations.manage", "Manage Recommendations", "Create/edit command recommendations content."),

    ("market.view", "Market Intelligence View", "View market intelligence dashboards."),
    ("market.edit", "Market Intelligence Edit", "Edit market intel notes/overlays (if enabled)."),

    ("ops.funnel.view", "Funnel View", "View funnel metrics and conversion."),
    ("ops.productivity.view", "Productivity View", "View activity/productivity metrics."),
    ("ops.processing.view", "Processing View", "View processing/attrition/conversion metrics."),
    ("ops.edit", "Operations Edit", "Edit operations annotations/settings (if enabled)."),

    ("roi.overview.view", "ROI Overview View", "View ROI overview dashboards."),
    ("roi.events.view", "Event ROI View", "View event ROI list and details."),
    ("roi.events.edit", "Event ROI Edit", "Edit event ROI inputs/notes (if enabled)."),
    ("roi.marketing.view", "Marketing ROI View", "View marketing/advertising ROI."),
    ("roi.marketing.edit", "Marketing ROI Edit", "Edit marketing ROI config (if enabled)."),
    ("roi.mac.view", "MAC ROI View", "View MAC utilization and ROI."),
    ("roi.mac.edit", "MAC ROI Edit", "Edit MAC utilization records (if enabled)."),

    ("planning.qtr.view", "QTR Plan View", "View quarterly plan."),
    ("planning.qtr.edit", "QTR Plan Edit", "Create/update quarterly plan."),
    ("planning.calendar.view", "Calendar View", "View planning calendar."),
    ("planning.calendar.edit", "Calendar Edit", "Edit planning calendar entries."),
    ("planning.twg.view", "TWG View", "View TWG/Fusion issues/actions."),
    ("planning.twg.edit", "TWG Edit", "Create/edit TWG issues/actions."),

    ("schools.view", "Schools Overview View", "View school recruiting overview."),
    ("schools.contacts.view", "School Contacts View", "View school contacts and coverage."),
    ("schools.contacts.edit", "School Contacts Edit", "Edit school contacts and coverage (if enabled)."),
    ("schools.alrl.view", "ALRL View", "View ALRL outcomes."),
    ("schools.roi.view", "Schools ROI View", "View school ROI."),

    ("budget.view", "Budget View", "View budget overview."),
    ("budget.execution.view", "Budget Execution View", "View execution/burn rate."),
    ("budget.execution.edit", "Budget Execution Edit", "Edit execution/burn inputs (if enabled)."),
    ("budget.roi.view", "Budget ROI View", "View spend-to-ROI mapping."),

    ("datahub.view", "Data Hub View", "View Data Hub pages."),
    ("datahub.upload", "Data Hub Upload", "Upload datasets into Data Hub."),
    ("datahub.registry.manage", "Manage Dataset Registry", "Manage dataset registry formats/specs."),
    ("datahub.runs.view", "View Import Runs", "View import run history and errors."),
    ("datahub.storage.view", "View Data Storage", "View historical storage inventory."),

    ("resources.view", "Resources View", "View resources library."),
    ("training.view", "Training View", "View training modules."),
    ("training.manage", "Training Manage", "Create/edit training modules (if enabled)."),

    ("helpdesk.create", "Helpdesk Create", "Create support tickets."),
    ("helpdesk.view_own", "Helpdesk View Own", "View own ticket status."),
    ("helpdesk.manage", "Helpdesk Manage", "Admin/support can manage all tickets."),
    ("system.status.view", "System Status View", "View system status page."),
    ("system.updates.manage", "System Updates Manage", "Post/modify system updates."),

    ("admin.view", "Admin View", "View admin section."),
    ("admin.users.manage", "Manage Users", "Create/update users and role assignments."),
    ("admin.roles.manage", "Manage Roles", "Create/edit roles and role-permission mapping."),
    ("admin.permissions.manage", "Manage Permissions", "Manage permissions catalog (system-only in practice)."),
    ("admin.audit.view", "Audit View", "View audit logs."),
]

ROLES = [
    ("BASELINE", "Baseline", "Default for all users: dashboards.read + export.any"),
    ("ANALYST", "Analyst", "Read access across TOR dashboards."),
    ("PLANNING_EDITOR", "Planning Editor", "Can edit planning + TWG + calendar."),
    ("ROI_EDITOR", "ROI Editor", "Can edit ROI marketing/MAC/events (if enabled)."),
    ("DATA_MANAGER", "Data Manager", "Can upload and view import runs/storage."),
    ("ADMIN", "Admin", "Can manage users/roles/permissions and helpdesk."),
    ("OWNER_MASTER", "Owner/Master", "Full access override."),
]

ROLE_PERMS = {
    "BASELINE": ["dashboards.read", "export.any"],
    "ANALYST": [
        "cmd.view", "market.view", "ops.funnel.view", "ops.productivity.view", "ops.processing.view",
        "roi.overview.view", "roi.events.view", "roi.marketing.view", "roi.mac.view",
        "planning.qtr.view", "planning.calendar.view", "planning.twg.view", "schools.view",
        "schools.contacts.view", "schools.alrl.view", "schools.roi.view", "budget.view",
        "budget.execution.view", "budget.roi.view", "resources.view", "training.view",
        "helpdesk.create", "helpdesk.view_own", "system.status.view", "datahub.view",
    ],
    "PLANNING_EDITOR": ["planning.qtr.edit", "planning.calendar.edit", "planning.twg.edit"],
    "ROI_EDITOR": ["roi.events.edit", "roi.marketing.edit", "roi.mac.edit"],
    "DATA_MANAGER": ["datahub.upload", "datahub.runs.view", "datahub.storage.view"],
    "ADMIN": ["admin.view", "admin.users.manage", "admin.roles.manage", "admin.permissions.manage", "admin.audit.view", "helpdesk.manage", "system.updates.manage", "datahub.registry.manage"],
    "OWNER_MASTER": ["master.access"],
}


def seed_rbac():
    """Seed RBAC tables idempotently and robustly.

    This function is safe to call multiple times. It uses the `db.connect()`
    helper and will not raise on failure; errors are logged and the server
    startup continues so local-dev remains usable.
    """
    try:
        conn = db.connect()
    except Exception as e:
        _log.exception('seed_rbac: failed to acquire DB connection')
        return

    if conn is None:
        _log.warning('seed_rbac: connect() returned None - skipping RBAC seed until DB available')
        return

    cur = conn.cursor()
    try:
        cur.execute('BEGIN')
        # Migrate legacy `permission` table schema if present but missing expected columns.
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permission'")
            if cur.fetchone():
                cur.execute("PRAGMA table_info(permission);")
                existing_cols = [r[1] for r in cur.fetchall()]
                # Ensure canonical columns exist on permission table
                for needed_col, ddl in (('permission_key','TEXT'), ('display_name','TEXT'), ('description','TEXT')):
                    if needed_col not in existing_cols:
                        try:
                            db.safe_add_column(conn, 'permission', needed_col, ddl)
                        except Exception:
                            _log.exception('seed_rbac: failed to add column %s to permission', needed_col)

                if 'permission_key' not in existing_cols:
                    # Best-effort migration: if legacy table has `key` column, add
                    # `permission_key` and copy values over. Avoid DROP/RENAME to
                    # prevent FK constraint failures.
                    if 'key' in existing_cols:
                        try:
                            try:
                                cur.execute("ALTER TABLE permission ADD COLUMN permission_key TEXT;")
                            except Exception:
                                # older sqlite versions or locked DB may fail; ignore
                                pass
                            try:
                                cur.execute("UPDATE permission SET permission_key = key WHERE permission_key IS NULL AND key IS NOT NULL")
                            except Exception:
                                pass
                            try:
                                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_permission_key ON permission(permission_key)")
                            except Exception:
                                pass
                        except Exception:
                            _log.exception('seed_rbac: failed to migrate legacy permission table via safe ALTER')
                    else:
                        _log.warning('seed_rbac: permission table missing expected columns; manual intervention may be required')
        except Exception:
            _log.exception('seed_rbac: error checking permission table')

        # create tables idempotently
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS user_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            is_active INTEGER DEFAULT 1,
            is_master INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS role (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_key TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            is_system INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS permission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_key TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS role_permission (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, permission_id)
        );

        CREATE TABLE IF NOT EXISTS user_role (
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, role_id)
        );

        CREATE TABLE IF NOT EXISTS user_permission_override (
            user_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            granted INTEGER NOT NULL,
            PRIMARY KEY (user_id, permission_id)
        );
        """)

        # insert permissions (handle both new and legacy permission table schemas)
        try:
            cur.execute("PRAGMA table_info(permission);")
            perm_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            perm_cols = []

        for key, name, desc in PERMISSIONS:
            try:
                # Prefer canonical columns if present
                if all(c in perm_cols for c in ('permission_key', 'display_name', 'description')):
                    cur.execute('INSERT OR IGNORE INTO permission(permission_key, display_name, description) VALUES (?,?,?)', (key, name, desc))
                elif 'key' in perm_cols and 'description' in perm_cols and 'category' in perm_cols:
                    cur.execute('INSERT OR IGNORE INTO permission(key, description, category) VALUES (?,?,?)', (key, desc, ''))
                elif 'key' in perm_cols and 'description' in perm_cols:
                    cur.execute('INSERT OR IGNORE INTO permission(key, description) VALUES (?,?)', (key, desc))
                elif 'permission_key' in perm_cols:
                    # best-effort: insert minimal data
                    try:
                        cur.execute('INSERT OR IGNORE INTO permission(permission_key) VALUES (?)', (key,))
                    except Exception:
                        _log.exception('seed_rbac: failed to insert minimal permission %s', key)
                else:
                    # last-resort: try a generic insert and ignore failures
                    try:
                        cur.execute('INSERT OR IGNORE INTO permission(permission_key, display_name, description) VALUES (?,?,?)', (key, name, desc))
                    except Exception:
                        _log.exception('seed_rbac: failed to insert permission %s with fallback', key)
            except Exception:
                _log.exception('seed_rbac: error inserting permission %s', key)

        # insert roles (tolerant of legacy schemas)
        try:
            cur.execute("PRAGMA table_info(role);")
            role_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            role_cols = []
        has_description = 'description' in role_cols
        has_is_system = 'is_system' in role_cols
        for key, name, desc in ROLES:
            try:
                if has_description and has_is_system:
                    cur.execute('INSERT OR IGNORE INTO role(role_key, display_name, description, is_system) VALUES (?,?,?,1)', (key, name, desc))
                elif has_description:
                    cur.execute('INSERT OR IGNORE INTO role(role_key, display_name, description) VALUES (?,?,?)', (key, name, desc))
                else:
                    try:
                        cur.execute('INSERT OR IGNORE INTO role(role_key, display_name) VALUES (?,?)', (key, name))
                    except Exception:
                        _log.exception('seed_rbac: failed to insert role %s', key)
            except Exception:
                _log.exception('seed_rbac: error inserting role %s', key)

        # map role -> permission (handle legacy role/permission schemas)
        try:
            cur.execute("PRAGMA table_info(role);")
            role_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            role_cols = []
        try:
            cur.execute("PRAGMA table_info(permission);")
            perm_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            perm_cols = []
        role_has_id = 'id' in role_cols
        perm_has_id = 'id' in perm_cols
        for rk, perms in ROLE_PERMS.items():
            try:
                if role_has_id:
                    cur.execute('SELECT id FROM role WHERE role_key=?', (rk,))
                    r = cur.fetchone()
                    if not r:
                        continue
                    role_id = r[0]
                else:
                    role_id = rk
                for pk in perms:
                    try:
                        if perm_has_id and 'permission_key' in perm_cols:
                            cur.execute('SELECT id FROM permission WHERE permission_key=?', (pk,))
                            p = cur.fetchone()
                            if not p:
                                continue
                            perm_id = p[0]
                        else:
                            perm_id = pk
                        if role_has_id and perm_has_id:
                            cur.execute('INSERT OR IGNORE INTO role_permission(role_id, permission_id) VALUES (?,?)', (role_id, perm_id))
                        elif not role_has_id and not perm_has_id:
                            cur.execute('INSERT OR IGNORE INTO role_permission(role_key, permission_key, granted) VALUES (?,?,1)', (role_id, perm_id))
                        elif not role_has_id and perm_has_id:
                            cur.execute('INSERT OR IGNORE INTO role_permission(role_key, permission_id, granted) VALUES (?,?,1)', (role_id, perm_id))
                        elif role_has_id and not perm_has_id:
                            cur.execute('INSERT OR IGNORE INTO role_permission(role_id, permission_key, granted) VALUES (?,?,1)', (role_id, perm_id))
                    except Exception:
                        _log.exception('seed_rbac: failed to map permission %s for role %s', pk, rk)
            except Exception:
                _log.exception('seed_rbac: failed processing role %s', rk)

        # ensure BASELINE role assigned to all existing users (handle legacy schemas)
        try:
            cur.execute("PRAGMA table_info(role);")
            role_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            role_cols = []
        try:
            cur.execute("PRAGMA table_info(user_role);")
            user_role_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            user_role_cols = []
        role_has_id = 'id' in role_cols
        # fetch baseline identifier depending on schema
        if role_has_id:
            cur.execute('SELECT id FROM role WHERE role_key=?', ('BASELINE',))
            br = cur.fetchone()
            if br:
                baseline_role_id = br[0]
            else:
                baseline_role_id = None
        else:
            # legacy uses role_key as identifier
            baseline_role_id = 'BASELINE'
        if baseline_role_id:
            try:
                cur.execute('SELECT id FROM users')
                rows = cur.fetchall()
            except Exception:
                rows = []
            for row in rows:
                uid = row[0]
                try:
                    if role_has_id and 'role_id' in user_role_cols:
                        cur.execute('INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES (?,?)', (uid, baseline_role_id))
                    elif not role_has_id and 'role_key' in user_role_cols:
                        cur.execute('INSERT OR IGNORE INTO user_role(user_id, role_key) VALUES (?,?)', (uid, baseline_role_id))
                    else:
                        try:
                            cur.execute('INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES (?,?)', (uid, baseline_role_id))
                        except Exception:
                            _log.exception('seed_rbac: failed to assign baseline role to user %s', uid)
                except Exception:
                    _log.exception('seed_rbac: error assigning baseline role to user %s', uid)

        cur.execute('COMMIT')
    except Exception:
        try:
            cur.execute('ROLLBACK')
        except Exception:
            pass
        _log.exception('seed_rbac: unexpected error')
    finally:
        try:
            conn.close()
        except Exception:
            pass


def ensure_user_baseline(user_id: int):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id FROM role WHERE role_key=?', ('BASELINE',))
        r = cur.fetchone()
        if not r:
            return
        role_id = r[0]
        cur.execute('INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES (?,?)', (user_id, role_id))
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_effective_permissions_for_user(user_id: int):
    """Return list of permission_key strings effective for the user_id.
    Master/value: if user_account.is_master ==1 or user has OWNER_MASTER role -> return all permissions.
    Otherwise gather role->permission and apply overrides (granted=1 add, granted=0 remove).
    """
    conn = connect()
    cur = conn.cursor()
    try:
        # check is_master flag
        try:
            cur.execute('SELECT is_master FROM user_account WHERE id=?', (user_id,))
            r = cur.fetchone()
            if r and r[0] == 1:
                cur.execute('SELECT permission_key FROM permission')
                return [p[0] for p in cur.fetchall()]
        except Exception:
            pass
        # check OWNER_MASTER role
        cur.execute('SELECT r.id FROM role r JOIN user_role ur ON ur.role_id=r.id WHERE ur.user_id=? AND r.role_key=?', (user_id, 'OWNER_MASTER'))
        if cur.fetchone():
            cur.execute('SELECT permission_key FROM permission')
            return [p[0] for p in cur.fetchall()]
        # gather perms from roles
        cur.execute('SELECT rp.permission_id FROM role_permission rp JOIN user_role ur ON ur.role_id=rp.role_id WHERE ur.user_id=?', (user_id,))
        perm_ids = set([r[0] for r in cur.fetchall()])
        # map ids -> keys
        effective = set()
        if perm_ids:
            cur.execute('SELECT id, permission_key FROM permission WHERE id IN (%s)' % ','.join(['?']*len(perm_ids)), tuple(perm_ids))
            for pid, pkey in cur.fetchall():
                effective.add(pkey)
        # apply overrides
        cur.execute('SELECT permission_id, granted FROM user_permission_override WHERE user_id=?', (user_id,))
        for pid, granted in cur.fetchall():
            cur.execute('SELECT permission_key FROM permission WHERE id=?', (pid,))
            r = cur.fetchone()
            if not r:
                continue
            pkey = r[0]
            if granted == 1:
                effective.add(pkey)
            else:
                effective.discard(pkey)
        return sorted(list(effective))
    finally:
        try:
            conn.close()
        except Exception:
            pass
