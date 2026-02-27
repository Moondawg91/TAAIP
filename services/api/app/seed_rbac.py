import json
from .db import connect

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
    conn = connect()
    cur = conn.cursor()
    try:
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
        conn.commit()

        # insert permissions
        for key, name, desc in PERMISSIONS:
            cur.execute('INSERT OR IGNORE INTO permission(permission_key, display_name, description) VALUES (?,?,?)', (key, name, desc))
        conn.commit()

        # insert roles
        for key, name, desc in ROLES:
            cur.execute('INSERT OR IGNORE INTO role(role_key, display_name, description, is_system) VALUES (?,?,?,1)', (key, name, desc))
        conn.commit()

        # map role -> permission
        for rk, perms in ROLE_PERMS.items():
            cur.execute('SELECT id FROM role WHERE role_key=?', (rk,))
            r = cur.fetchone()
            if not r:
                continue
            role_id = r[0]
            for pk in perms:
                cur.execute('SELECT id FROM permission WHERE permission_key=?', (pk,))
                p = cur.fetchone()
                if not p:
                    continue
                perm_id = p[0]
                try:
                    cur.execute('INSERT OR IGNORE INTO role_permission(role_id, permission_id) VALUES (?,?)', (role_id, perm_id))
                except Exception:
                    pass
        conn.commit()

        # ensure BASELINE role assigned to all existing users
        cur.execute('SELECT id FROM role WHERE role_key=?', ('BASELINE',))
        br = cur.fetchone()
        if br:
            baseline_role_id = br[0]
            cur.execute('SELECT id FROM users')
            for row in cur.fetchall():
                uid = row[0]
                try:
                    cur.execute('INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES (?,?)', (uid, baseline_role_id))
                except Exception:
                    pass
        conn.commit()
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
