"""Database helpers for lightweight dev SQLite storage.

Provides connection helpers and schema initialization for a lightweight
SQLite development database. All SQL uses plain queries (no ORM) and is idempotent.
"""
from typing import Optional
import os
import sqlite3
from datetime import datetime


def get_db_path() -> str:
    """Return path to the SQLite DB file.

    Reads `TAAIP_DB_PATH` environment variable. Falls back to
    `./taaip_dev.db` relative to repository root.
    """
    return os.getenv("TAAIP_DB_PATH", "./taaip_dev.db")


def connect() -> sqlite3.Connection:
    """Open a sqlite3 connection with safe pragmas for local dev.

    Returns a connection with `row_factory=sqlite3.Row` and executes
    WAL/journal pragmas and a reasonable busy timeout.
    """
    path = get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    PRAGMA busy_timeout=10000;
    """)
    conn.commit()
    return conn


def init_schema() -> None:
    """Create the locked, operational SQLite schema for TAAIP.

    This function is idempotent and will create the full set of tables
    required by the system along with recommended indexes.
    """

    sql = """
    -- org_unit
    CREATE TABLE IF NOT EXISTS org_unit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT,
        parent_id INTEGER,
        uic TEXT,
        location_city TEXT,
        location_state TEXT,
        location_zip TEXT,
        cbsa TEXT
    );

    -- fiscal year budgets
    CREATE TABLE IF NOT EXISTS fy_budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER NOT NULL,
        fy INTEGER NOT NULL,
        total_allocated REAL DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS fy_budget_qtr (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fy_budget_id INTEGER NOT NULL,
        qtr INTEGER NOT NULL,
        allocated_amount REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS budget_line_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fy_budget_id INTEGER NOT NULL,
        qtr INTEGER,
        event_id INTEGER,
        category TEXT,
        vendor TEXT,
        description TEXT,
        amount REAL DEFAULT 0,
        status TEXT,
        obligation_date TEXT,
        notes TEXT
    );

    -- events and related
    CREATE TABLE IF NOT EXISTS event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER,
        name TEXT,
        event_type TEXT,
        start_dt TEXT,
        end_dt TEXT,
        location_name TEXT,
        location_city TEXT,
        location_state TEXT,
        location_zip TEXT,
        cbsa TEXT,
        loe REAL,
        objective TEXT,
        status TEXT,
        poc TEXT,
        risk_level TEXT,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS event_asset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        quantity INTEGER DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS event_asset_allocation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        asset_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS event_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        impressions INTEGER DEFAULT 0,
        engagements INTEGER DEFAULT 0,
        leads INTEGER DEFAULT 0,
        appts_made INTEGER DEFAULT 0,
        appts_conducted INTEGER DEFAULT 0,
        contracts INTEGER DEFAULT 0,
        accessions INTEGER DEFAULT 0,
        other_json TEXT,
        captured_at TEXT
    );

    CREATE TABLE IF NOT EXISTS event_roi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        total_cost REAL,
        cpl REAL,
        cpe REAL,
        cost_per_appt REAL,
        cost_per_contract REAL,
        cost_per_accession REAL,
        roi_value REAL,
        opportunity_cost_value REAL,
        computed_at TEXT,
        method_version TEXT
    );

    -- LOE, projects, tasks, scope changes
    CREATE TABLE IF NOT EXISTS loe (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER,
        fy INTEGER,
        qtr INTEGER,
        name TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS project (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER,
        loe_id INTEGER,
        event_id INTEGER,
        name TEXT,
        description TEXT,
        status TEXT,
        start_dt TEXT,
        end_dt TEXT,
        roi_target REAL,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS task (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        event_id INTEGER,
        title TEXT,
        owner TEXT,
        status TEXT,
        start_dt TEXT,
        due_dt TEXT,
        percent_complete REAL DEFAULT 0,
        blockers TEXT,
        scope_change_flag INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS scope_change (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        task_id INTEGER,
        change_dt TEXT,
        description TEXT,
        impact_cost REAL,
        impact_schedule TEXT,
        approved_by TEXT,
        decision TEXT
    );

    -- meetings, agenda, minutes, decisions, action items
    CREATE TABLE IF NOT EXISTS meeting (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER,
        title TEXT,
        meeting_type TEXT,
        start_dt TEXT,
        end_dt TEXT,
        location TEXT,
        qtr INTEGER,
        fy INTEGER,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS agenda_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        seq INTEGER,
        title TEXT,
        owner TEXT,
        time_alloc_min INTEGER
    );

    CREATE TABLE IF NOT EXISTS minutes_entry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        seq INTEGER,
        text TEXT,
        tags_json TEXT
    );

    CREATE TABLE IF NOT EXISTS decision (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        text TEXT,
        decision_dt TEXT,
        owner TEXT
    );

    CREATE TABLE IF NOT EXISTS action_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        title TEXT,
        owner TEXT,
        due_dt TEXT,
        status TEXT,
        linked_project_id INTEGER,
        linked_event_id INTEGER,
        linked_task_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS lesson_learned (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER,
        fy INTEGER,
        qtr INTEGER,
        event_id INTEGER,
        project_id INTEGER,
        observation TEXT,
        recommendation TEXT,
        impact TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS ai_recommendation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scope_type TEXT,
        scope_id INTEGER,
        fy INTEGER,
        qtr INTEGER,
        prompt_hash TEXT,
        output_json TEXT,
        created_at TEXT
    );

    -- Import job / rows
    CREATE TABLE IF NOT EXISTS import_job (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        source_system TEXT,
        filename TEXT,
        file_hash TEXT,
        stored_path TEXT,
        status TEXT,
        preview_json TEXT,
        mapping_json TEXT,
        commit_result_json TEXT
    );

    CREATE TABLE IF NOT EXISTS import_row (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        row_json TEXT
    );

        -- Supplemental import tables used by Import Center
        CREATE TABLE IF NOT EXISTS import_job_preview (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_job_id INTEGER,
            preview_json TEXT,
            columns_json TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS import_job_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_job_id INTEGER,
            level TEXT,
            message TEXT,
            row_number INTEGER,
            field_name TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS import_mapping_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            target_domain TEXT,
            mapping_json TEXT,
            created_by TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS imported_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_job_id INTEGER,
            target_domain TEXT,
            row_json TEXT,
            created_at TEXT
        );

    -- indexes for common filters

    -- lightweight analytics tables kept for backward compatibility
    CREATE TABLE IF NOT EXISTS kpi_snapshot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scope TEXT NOT NULL,
        as_of TEXT NOT NULL,
        metric_key TEXT NOT NULL,
        metric_value REAL,
        source TEXT,
        notes TEXT
    );

    """

    conn = connect()
    try:
        cur = conn.cursor()
        # Split table creation from index creation to avoid failures when
        # existing tables lack columns (we'll attempt indexes and ignore
        # index creation errors to keep init idempotent on evolving schemas).
        cur.executescript(sql)

        # Attempt to create indexes where possible; ignore operational errors
        # that arise from mismatched existing schemas.
        index_statements = [
            "CREATE INDEX IF NOT EXISTS ix_org_unit_parent_id ON org_unit(parent_id);",
            "CREATE INDEX IF NOT EXISTS ix_fy_budget_org_unit_id ON fy_budget(org_unit_id);",
            "CREATE INDEX IF NOT EXISTS ix_budget_line_item_fy_budget_id ON budget_line_item(fy_budget_id);",
            "CREATE INDEX IF NOT EXISTS ix_budget_line_item_event_id ON budget_line_item(event_id);",
            "CREATE INDEX IF NOT EXISTS ix_event_org_unit_id ON event(org_unit_id);",
            "CREATE INDEX IF NOT EXISTS ix_event_metrics_event_id ON event_metrics(event_id);",
            "CREATE INDEX IF NOT EXISTS ix_event_roi_event_id ON event_roi(event_id);",
            "CREATE INDEX IF NOT EXISTS ix_loe_org_unit_id ON loe(org_unit_id);",
            "CREATE INDEX IF NOT EXISTS ix_project_org_unit_id ON project(org_unit_id);",
            "CREATE INDEX IF NOT EXISTS ix_project_event_id ON project(event_id);",
            "CREATE INDEX IF NOT EXISTS ix_task_project_id ON task(project_id);",
            "CREATE INDEX IF NOT EXISTS ix_task_event_id ON task(event_id);",
            "CREATE INDEX IF NOT EXISTS ix_meeting_org_unit_id ON meeting(org_unit_id);",
            "CREATE INDEX IF NOT EXISTS ix_fy_qtr ON fy_budget(fy, id);",
            "CREATE INDEX IF NOT EXISTS ix_event_id ON event(id);",
            "CREATE INDEX IF NOT EXISTS ix_project_id ON project(id);",
            "CREATE INDEX IF NOT EXISTS ix_task_id ON task(id);",
        ]
        for stmt in index_statements:
            try:
                cur.execute(stmt)
            except Exception:
                # ignore index creation errors on older/dbs with different schema
                pass

        # Additional core operational tables (users/roles/audit/raw files/etc.)
        sql_more = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            display_name TEXT,
            email TEXT,
            password_hash TEXT,
            created_at TEXT,
            updated_at TEXT,
            record_status TEXT DEFAULT 'active',
            keep_until TEXT
        );

        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role_id INTEGER,
            assigned_at TEXT
        );

        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER,
            permission_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS user_scope (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            org_unit_id INTEGER,
            scope_level TEXT,
            assigned_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            who TEXT,
            action TEXT,
            entity TEXT,
            entity_id INTEGER,
            meta_json TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS raw_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT,
            file_size INTEGER,
            sha256 TEXT,
            org_scope TEXT
        );

        CREATE TABLE IF NOT EXISTS raw_file_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_file_id INTEGER,
            version INTEGER,
            stored_path TEXT,
            sha256 TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS mapping_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            target_table TEXT,
            field_map_json TEXT,
            transforms_json TEXT,
            org_scope TEXT,
            created_by TEXT,
            created_at TEXT
        );

        CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS ix_roles_name ON roles(name);
        CREATE INDEX IF NOT EXISTS ix_audit_log_entity ON audit_log(entity, entity_id);
        
        -- Additional fact/dimension and domain tables required by TAAIP
        CREATE TABLE IF NOT EXISTS fact_metric (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_key TEXT NOT NULL,
            metric_value REAL,
            unit TEXT,
            org_unit_id INTEGER,
            recorded_at TEXT,
            source TEXT,
            import_job_id INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS dim_stage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS fact_funnel_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_unit_id INTEGER,
            stage_id INTEGER,
            metric_key TEXT,
            metric_value REAL,
            as_of TEXT,
            import_job_id INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS fact_production_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            org_unit_id INTEGER,
            metric_key TEXT,
            metric_value REAL,
            as_of TEXT,
            import_job_id INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS event_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            proposal_json TEXT,
            staffing_json TEXT,
            schedule_json TEXT,
            estimated_cost REAL,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS event_shift (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            shift_name TEXT,
            start_dt TEXT,
            end_dt TEXT,
            staff_json TEXT
        );

        CREATE TABLE IF NOT EXISTS event_cost (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            category TEXT,
            vendor TEXT,
            amount REAL,
            incurred_at TEXT
        );

        CREATE TABLE IF NOT EXISTS event_outcome (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            outcome_json TEXT,
            recorded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS event_roi_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            snapshot_at TEXT,
            roi_json TEXT,
            method_version TEXT
        );

        CREATE TABLE IF NOT EXISTS task_comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            commenter TEXT,
            comment TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS task_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            assignee TEXT,
            assigned_at TEXT,
            percent_expected REAL
        );

        CREATE TABLE IF NOT EXISTS working_group (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_unit_id INTEGER,
            name TEXT,
            wg_type TEXT,
            description TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS attachment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_table TEXT,
            parent_id INTEGER,
            filename TEXT,
            stored_path TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT,
            file_size INTEGER
        );

        CREATE TABLE IF NOT EXISTS board (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            org_unit_id INTEGER,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS board_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER,
            fy INTEGER,
            qtr INTEGER,
            session_dt TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS board_artifact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_session_id INTEGER,
            title TEXT,
            artifact_json TEXT
        );

        CREATE TABLE IF NOT EXISTS board_metric_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_session_id INTEGER,
            metric_key TEXT,
            metric_value REAL,
            captured_at TEXT
        );

        CREATE TABLE IF NOT EXISTS doc_library_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            owner_org_unit INTEGER,
            created_by TEXT,
            created_at TEXT,
            record_status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS doc_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            version INTEGER,
            filename TEXT,
            stored_path TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS doc_tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            tag TEXT
        );

        CREATE TABLE IF NOT EXISTS doc_permission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            role_id INTEGER,
            granted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS policy_doc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            doc_type TEXT,
            reference TEXT,
            text_extract TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS policy_pack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS policy_pack_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER,
            policy_doc_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS policy_change_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_doc_id INTEGER,
            changed_by TEXT,
            change_summary TEXT,
            changed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS training_course (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS training_module (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            seq INTEGER
        );

        CREATE TABLE IF NOT EXISTS training_lesson (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER,
            title TEXT,
            content TEXT
        );

        CREATE TABLE IF NOT EXISTS training_attachment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER,
            filename TEXT,
            stored_path TEXT
        );

        CREATE TABLE IF NOT EXISTS training_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            assigned_to TEXT,
            assigned_at TEXT,
            due_dt TEXT
        );

        CREATE TABLE IF NOT EXISTS training_completion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER,
            completed_by TEXT,
            completed_at TEXT,
            score REAL
        );

        CREATE TABLE IF NOT EXISTS playbook_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            parameters_json TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS automation_run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            started_at TEXT,
            finished_at TEXT,
            status TEXT,
            output_json TEXT
        );

        CREATE TABLE IF NOT EXISTS automation_setting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            value TEXT,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS ix_fact_metric_key ON fact_metric(metric_key);
        CREATE INDEX IF NOT EXISTS ix_fact_funnel_event_stage ON fact_funnel_event(stage_id);
        CREATE INDEX IF NOT EXISTS ix_fact_production_event_event ON fact_production_event(event_id);
        """
        try:
            cur.executescript(sql_more)
        except Exception:
            pass
        conn.commit()

        # Run safe migrations for evolving tables
        try:
            migrate_org_unit_add_columns()
        except Exception:
            pass
        try:
            migrate_project_add_columns()
        except Exception:
            pass
        try:
            migrate_imports_schema()
        except Exception:
            pass
    finally:
        conn.close()


def migrate_org_unit_add_columns():
    """Add missing org_unit columns safely when upgrading schema.

    This will not remove existing columns. It preserves existing data by
    copying `type` into `unit_type` when possible.
    """
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(org_unit)")
        cols = [r[1] for r in cur.fetchall()]
        # add unit_type (copy from type if present)
        if 'unit_type' not in cols:
            try:
                cur.execute('ALTER TABLE org_unit ADD COLUMN unit_type TEXT')
            except Exception:
                pass
            if 'type' in cols:
                try:
                    cur.execute("UPDATE org_unit SET unit_type=type WHERE unit_type IS NULL OR unit_type=''")
                except Exception:
                    pass
        # add rsid, lat, lon
        if 'rsid' not in cols:
            try:
                cur.execute('ALTER TABLE org_unit ADD COLUMN rsid TEXT')
            except Exception:
                pass
        if 'lat' not in cols:
            try:
                cur.execute('ALTER TABLE org_unit ADD COLUMN lat REAL')
            except Exception:
                pass
        if 'lon' not in cols:
            try:
                cur.execute('ALTER TABLE org_unit ADD COLUMN lon REAL')
            except Exception:
                pass
        conn.commit()
        # create indexes
        try:
            cur.execute('CREATE INDEX IF NOT EXISTS ix_org_unit_parent_id ON org_unit(parent_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS ix_org_unit_unit_type ON org_unit(unit_type)')
            cur.execute('CREATE INDEX IF NOT EXISTS ix_org_unit_uic ON org_unit(uic)')
            cur.execute('CREATE INDEX IF NOT EXISTS ix_org_unit_rsid ON org_unit(rsid)')
            cur.execute('CREATE INDEX IF NOT EXISTS ix_org_unit_zip ON org_unit(location_zip)')
            cur.execute('CREATE INDEX IF NOT EXISTS ix_org_unit_cbsa ON org_unit(cbsa)')
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()
    

def migrate_project_add_columns():
    """Add missing project columns safely and copy legacy start_date/end_date.

    Preserves existing data; does not drop legacy columns.
    """
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(project)")
        cols = [r[1] for r in cur.fetchall()]
        # add org_unit_id
        if 'org_unit_id' not in cols:
            try:
                cur.execute('ALTER TABLE project ADD COLUMN org_unit_id INTEGER')
            except Exception:
                pass
        # add event_id
        if 'event_id' not in cols:
            try:
                cur.execute('ALTER TABLE project ADD COLUMN event_id INTEGER')
            except Exception:
                pass
        # add start_dt/end_dt and copy from start_date/end_date if present
        if 'start_dt' not in cols:
            try:
                cur.execute('ALTER TABLE project ADD COLUMN start_dt TEXT')
            except Exception:
                pass
            if 'start_date' in cols:
                try:
                    cur.execute("UPDATE project SET start_dt = start_date WHERE (start_dt IS NULL OR start_dt = '') AND (start_date IS NOT NULL AND start_date != '')")
                except Exception:
                    pass
        if 'end_dt' not in cols:
            try:
                cur.execute('ALTER TABLE project ADD COLUMN end_dt TEXT')
            except Exception:
                pass
            if 'end_date' in cols:
                try:
                    cur.execute("UPDATE project SET end_dt = end_date WHERE (end_dt IS NULL OR end_dt = '') AND (end_date IS NOT NULL AND end_date != '')")
                except Exception:
                    pass
        # add roi_target
        if 'roi_target' not in cols:
            try:
                cur.execute('ALTER TABLE project ADD COLUMN roi_target REAL')
            except Exception:
                pass

        # create helpful indexes
        try:
            cur.execute('CREATE INDEX IF NOT EXISTS ix_project_org_unit_id ON project(org_unit_id)')
            cur.execute('CREATE INDEX IF NOT EXISTS ix_project_event_id ON project(event_id)')
            conn.commit()
        except Exception:
            pass
    finally:
        conn.close()


def migrate_imports_schema():
    """Ensure import_job has expected columns for import center and create helper tables."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(import_job)")
        cols = [r[1] for r in cur.fetchall()]
        extras = [
            ('filename_original', 'TEXT'),
            ('file_type', 'TEXT'),
            ('file_size_bytes', 'INTEGER'),
            ('sha256_hash', 'TEXT'),
            ('uploaded_by_user_id', 'INTEGER'),
            ('uploaded_at', 'TEXT'),
            ('target_domain', 'TEXT'),
            ('updated_at', 'TEXT'),
            ('row_count_detected', 'INTEGER'),
            ('error_count', 'INTEGER'),
            ('warnings_count', 'INTEGER'),
            ('row_count_imported', 'INTEGER'),
            ('notes', 'TEXT')
        ]
        for name, typ in extras:
            if name not in cols:
                try:
                    cur.execute(f'ALTER TABLE import_job ADD COLUMN {name} {typ}')
                except Exception:
                    pass
        conn.commit()
    finally:
        conn.close()
    

