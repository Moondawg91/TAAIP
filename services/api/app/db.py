import os
import sqlite3
from datetime import datetime
from typing import Optional
import time
from time import sleep

# When running under the test harness we may want to force use of a
# specific DB-API connection so raw sqlite3 callers and SQLAlchemy
# sessions operate on the same underlying connection/transaction.
_test_raw_conn = None


def set_test_raw_conn(conn):
    """Set a DB-API connection to be returned by connect() during tests."""
    global _test_raw_conn
    _test_raw_conn = conn

def get_db_path() -> str:
    """Return path to the SQLite DB file.

    Reads `TAAIP_DB_PATH` environment variable. Falls back to
    `./data/taaip.sqlite3` to match test expectations and CI.
    """
    return os.getenv("TAAIP_DB_PATH", "./data/taaip.sqlite3")


def _ensure_db_dir(path: str) -> None:
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)


def connect() -> sqlite3.Connection:
    """Open a sqlite3 connection with reasonable pragmas for local dev."""
    # Prefer SQLAlchemy engine's raw_connection when available to avoid
    # mixing independent sqlite3 connections (which can hold locks)
    path = get_db_path()
    _ensure_db_dir(path)
    # If tests set a dedicated raw DB-API connection, return that so all
    # callers operate on the same physical connection/transaction.
    global _test_raw_conn
    if _test_raw_conn is not None:
        try:
            _test_raw_conn.row_factory = _dict_row_factory
            return _test_raw_conn
        except Exception:
            # fall through to normal behavior
            pass
    def _dict_row_factory(cursor, row):
        # return a plain dict for each row so callers can safely do dict(row)
        try:
            return {d[0]: row[i] for i, d in enumerate(cursor.description)}
        except Exception:
            return row

    try:
        from services.api.app import database as _database
        # Ensure database engine/session match current env (tests may change it)
        try:
            _database.reload_engine_if_needed()
        except Exception:
            pass
        # Debug: print engine url when opening raw_connection
        try:
            print(f"db.connect using engine: {_database.engine.url}")
        except Exception:
            pass
        from services.api.app.database import engine
        raw = engine.raw_connection()
        # raw_connection() returns a DB-API connection (sqlite3.Connection)
        raw.row_factory = _dict_row_factory
        try:
            cur = raw.cursor()
            cur.executescript("""
            PRAGMA foreign_keys=ON;
            PRAGMA synchronous=NORMAL;
            PRAGMA busy_timeout=10000;
            """)
            raw.commit()
        except Exception:
            pass
        return raw
    except Exception:
        conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
        conn.row_factory = _dict_row_factory
        cur = conn.cursor()
        cur.executescript("""
        PRAGMA foreign_keys=ON;
        PRAGMA synchronous=NORMAL;
        PRAGMA busy_timeout=10000;
        """)
        conn.commit()
        return conn


def get_db_conn() -> sqlite3.Connection:
    """Backward-compatible alias used across the codebase."""
    return connect()


def init_schema() -> None:
    """Idempotent creation of the core operational schema.

    This function focuses on ensuring the core tables required by tests
    and the application exist. It is safe to call multiple times and
    attempts minor migrations where necessary.
    """
    # Ensure the schema exists for the DB path returned by `get_db_path()`
    # first. Tests and some modules change `TAAIP_DB_PATH` at runtime which
    # can cause the SQLAlchemy `engine` (created at import-time) to point
    # at a different file. To avoid missing-table races, always initialize
    # the file referenced by `TAAIP_DB_PATH` first using the local sqlite3
    # connection, then attempt to run the same DDL through SQLAlchemy's
    # raw connection when available.
    try:
        conn = connect()
        cur = conn.cursor()
        using_raw_engine = False
    except Exception:
        # As a fallback, attempt to use SQLAlchemy engine if connect fails
        try:
            from services.api.app.database import engine
            raw_conn = engine.raw_connection()
            cur = raw_conn.cursor()
            conn = raw_conn
            using_raw_engine = True
        except Exception:
            # Last-resort: open a plain sqlite3 connection to the default path
            conn = connect()
            cur = conn.cursor()
            using_raw_engine = False
    try:

        # Core organizational tree and core tables
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS org_unit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                parent_id INTEGER,
                uic TEXT,
                rsid TEXT,
                location_city TEXT,
                location_state TEXT,
                location_zip TEXT,
                cbsa TEXT,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                display_name TEXT,
                email TEXT,
                password_hash TEXT,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
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

            -- Ensure 'commands' table exists for legacy SQLAlchemy models
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                display TEXT,
                created_at TEXT
            );

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
                commit_result_json TEXT,
                row_count_detected INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS imported_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_job_id INTEGER,
                target_domain TEXT,
                row_json TEXT,
                created_at TEXT
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
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            -- Many-to-many linkage between projects and events (relational link)
            CREATE TABLE IF NOT EXISTS project_event_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                org_unit_id INTEGER,
                created_at TEXT,
                UNIQUE(project_id, event_id)
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

            CREATE TABLE IF NOT EXISTS event_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                org_unit_id INTEGER,
                plan_type TEXT,
                title TEXT,
                description TEXT,
                metadata_json TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS event_risk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                org_unit_id INTEGER,
                title TEXT,
                likelihood TEXT,
                impact TEXT,
                mitigation TEXT,
                metadata_json TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS event_roi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                org_unit_id INTEGER,
                metrics_json TEXT,
                expected_revenue REAL,
                expected_cost REAL,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS event_aar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                org_unit_id INTEGER,
                summary TEXT,
                lessons_json TEXT,
                recommendations TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS marketing_activities (
                activity_id TEXT PRIMARY KEY,
                event_id TEXT,
                activity_type TEXT,
                campaign_name TEXT,
                channel TEXT,
                data_source TEXT,
                impressions INTEGER,
                engagement_count INTEGER,
                awareness_metric REAL,
                activation_conversions INTEGER,
                reporting_date TEXT,
                metadata TEXT,
                cost REAL DEFAULT 0,
                created_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                source TEXT,
                age INTEGER,
                education_level TEXT,
                cbsa_code TEXT,
                campaign_source TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS budgets (
                budget_id TEXT PRIMARY KEY,
                event_id TEXT,
                campaign_name TEXT,
                allocated_amount REAL,
                start_date TEXT,
                end_date TEXT,
                created_at TEXT,
                updated_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            -- Fiscal year budgets and budget line items (Phase-7)
            CREATE TABLE IF NOT EXISTS fy_budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_unit_id INTEGER,
                fy INTEGER,
                total_allocated REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS budget_line_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fy_budget_id INTEGER,
                qtr INTEGER,
                event_id INTEGER,
                category TEXT,
                vendor TEXT,
                description TEXT,
                amount REAL DEFAULT 0,
                -- Phase-10 funding structure additions
                appropriation_type TEXT DEFAULT 'OMA',
                funding_source TEXT,
                sag_code TEXT,
                amsco_code TEXT,
                mdep_code TEXT,
                eor_code TEXT,
                is_under_cr INTEGER DEFAULT 0,
                status TEXT,
                obligation_date TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            -- Legacy/backwards-compatible tables used by older routers
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                location TEXT,
                start_date TEXT,
                end_date TEXT,
                budget REAL,
                team_size INTEGER,
                targeting_principles TEXT,
                org_unit_id TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS funnel_transitions (
                id TEXT PRIMARY KEY,
                lead_id TEXT,
                from_stage TEXT,
                to_stage TEXT,
                transition_reason TEXT,
                created_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id TEXT,
                lead_id TEXT,
                responses_json TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS external_census (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                geography_code TEXT,
                attributes_json TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS external_social (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                handle TEXT,
                signals_json TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS loe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_unit_id INTEGER,
                fy TEXT,
                qtr TEXT,
                name TEXT,
                description TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS loes (
                id TEXT PRIMARY KEY,
                scope_type TEXT,
                scope_value TEXT,
                title TEXT,
                description TEXT,
                created_by TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS command_priorities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_unit_id INTEGER,
                title TEXT,
                description TEXT,
                rank INTEGER,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS priority_loe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                priority_id INTEGER NOT NULL,
                loe_id TEXT NOT NULL,
                created_at TEXT,
                UNIQUE(priority_id, loe_id)
            );

            -- Phase 3 provenance and data warehouse tables (migration-safe additions)
            CREATE TABLE IF NOT EXISTS import_job_v3 (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                created_by TEXT,
                dataset_key TEXT NOT NULL,
                source_system TEXT,
                filename TEXT,
                file_sha256 TEXT,
                status TEXT DEFAULT 'uploaded',
                row_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                updated_at TEXT,
                notes TEXT,
                scope_org_unit_id TEXT
            );

            CREATE TABLE IF NOT EXISTS import_file (
                id TEXT PRIMARY KEY,
                import_job_id TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                content_type TEXT,
                size_bytes INTEGER,
                uploaded_at TEXT
            );

            CREATE TABLE IF NOT EXISTS import_column_map (
                id TEXT PRIMARY KEY,
                import_job_id TEXT NOT NULL,
                mapping_json TEXT NOT NULL,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS import_error (
                id TEXT PRIMARY KEY,
                import_job_id TEXT NOT NULL,
                row_index INTEGER,
                field TEXT,
                message TEXT NOT NULL,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS dim_org_unit (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                parent_id TEXT,
                rsid TEXT,
                uic TEXT,
                state TEXT,
                city TEXT,
                zip TEXT
            );

            CREATE TABLE IF NOT EXISTS dim_time (
                date_key TEXT PRIMARY KEY,
                fy INTEGER,
                qtr INTEGER,
                month INTEGER,
                recruiting_month TEXT,
                week_of_year INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_production (
                id TEXT PRIMARY KEY,
                org_unit_id TEXT NOT NULL,
                date_key TEXT NOT NULL,
                metric_key TEXT NOT NULL,
                metric_value REAL NOT NULL,
                source_system TEXT,
                import_job_id TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active',
                archived_at TEXT
            );

            CREATE TABLE IF NOT EXISTS fact_funnel (
                id TEXT PRIMARY KEY,
                org_unit_id TEXT NOT NULL,
                date_key TEXT NOT NULL,
                lead_id TEXT,
                stage TEXT NOT NULL,
                event_type TEXT,
                count_value REAL NOT NULL,
                source_system TEXT,
                import_job_id TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active',
                archived_at TEXT
            );

            CREATE TABLE IF NOT EXISTS fact_marketing (
                id TEXT PRIMARY KEY,
                org_unit_id TEXT NOT NULL,
                date_key TEXT NOT NULL,
                campaign TEXT,
                channel TEXT,
                impressions REAL DEFAULT 0,
                engagements REAL DEFAULT 0,
                clicks REAL DEFAULT 0,
                conversions REAL DEFAULT 0,
                cost REAL DEFAULT 0,
                source_system TEXT,
                import_job_id TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active',
                archived_at TEXT
            );

            -- Mission assessment snapshots (Phase 7)
            CREATE TABLE IF NOT EXISTS mission_assessments (
                id TEXT PRIMARY KEY,
                period_type TEXT,
                period_value TEXT,
                scope TEXT,
                metrics_json TEXT,
                narrative TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            -- Phase 4 domain tables: projects, tasks, meetings, calendar, documents
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                owner TEXT,
                status TEXT,
                percent_complete REAL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            -- User preferences for multi-user experience (Phase-11)
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                default_scope TEXT,
                sidebar_pinned INTEGER DEFAULT 0,
                saved_filters TEXT,
                created_at TEXT,
                UNIQUE(user_id)
            );

            -- Backwards-compatible singular 'project' table used by older compat routers
            CREATE TABLE IF NOT EXISTS project (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_unit_id INTEGER,
                loe_id TEXT,
                event_id TEXT,
                name TEXT,
                description TEXT,
                status TEXT,
                start_dt TEXT,
                end_dt TEXT,
                roi_target REAL,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                project_id TEXT,
                title TEXT,
                description TEXT,
                owner TEXT,
                status TEXT,
                percent_complete REAL DEFAULT 0,
                due_date TEXT,
                created_at TEXT,
                updated_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS meeting_minutes (
                minute_id TEXT PRIMARY KEY,
                project_id TEXT,
                occurred_at TEXT,
                summary TEXT,
                created_by TEXT,
                created_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS action_items (
                action_id TEXT PRIMARY KEY,
                minute_id TEXT,
                title TEXT,
                owner TEXT,
                due_date TEXT,
                status TEXT,
                created_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            -- Backwards-compatible singular 'task' table and related comment/assignment tables
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT,
                owner TEXT,
                status TEXT,
                percent_complete INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
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
                percent_expected INTEGER
            );

            CREATE TABLE IF NOT EXISTS calendar_events (
                event_id TEXT PRIMARY KEY,
                org_unit_id TEXT,
                title TEXT,
                start_dt TEXT,
                end_dt TEXT,
                location TEXT,
                created_at TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            -- Boards / QBRs
            CREATE TABLE IF NOT EXISTS board (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                org_unit_id INTEGER,
                description TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS board_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER,
                fy INTEGER,
                qtr INTEGER,
                session_dt TEXT,
                notes TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS board_metric_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_session_id INTEGER,
                metric_key TEXT,
                metric_value REAL,
                captured_at TEXT
            );

            -- Legacy single-table calendar schema for older import paths and routers
            CREATE TABLE IF NOT EXISTS calendar_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linked_type TEXT,
                linked_id TEXT,
                org_unit_id TEXT,
                title TEXT,
                start_dt TEXT,
                end_dt TEXT,
                location TEXT,
                notes TEXT,
                status TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                import_job_id TEXT,
                tags TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS doc_library (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                url TEXT,
                uploaded_at TEXT,
                created_by TEXT,
                import_job_id TEXT,
                record_status TEXT DEFAULT 'active'
            );

            -- Simple LMS courses table used by v2 lms endpoints/tests
            CREATE TABLE IF NOT EXISTS lms_courses (
                course_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS lms_enrollments (
                enrollment_id TEXT PRIMARY KEY,
                user_id TEXT,
                course_id TEXT,
                progress_percent INTEGER DEFAULT 0,
                enrolled_at TEXT,
                updated_at TEXT
            );

            -- Home / Announcements / System updates / Resource links (Phase-5)
            CREATE TABLE IF NOT EXISTS announcement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_unit_id INTEGER,
                category TEXT,
                title TEXT,
                body TEXT,
                effective_dt TEXT,
                expires_dt TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS system_update (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT,
                status TEXT,
                message TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS resource_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT,
                title TEXT,
                url TEXT,
                created_at TEXT
            );

            -- Home portal tables (Phase 12 UI wiring)
            CREATE TABLE IF NOT EXISTS home_alerts (
                id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                body TEXT,
                severity TEXT,
                source TEXT,
                effective_at TEXT,
                created_at TEXT,
                acked_at TEXT,
                acked_by TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS home_flashes (
                id TEXT PRIMARY KEY,
                tab TEXT,
                source TEXT,
                title TEXT,
                summary TEXT,
                effective_at TEXT,
                url TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS home_upcoming (
                id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                start_at TEXT,
                end_at TEXT,
                location TEXT,
                url TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS home_recognition (
                id TEXT PRIMARY KEY,
                title TEXT,
                name TEXT,
                unit TEXT,
                citation TEXT,
                month INTEGER,
                year INTEGER,
                created_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS home_references (
                id TEXT PRIMARY KEY,
                key TEXT,
                label TEXT,
                type TEXT,
                path_or_url TEXT,
                available INTEGER DEFAULT 0,
                created_at TEXT
            );

            -- Command Center tables
            CREATE TABLE IF NOT EXISTS loe_metrics (
                id TEXT PRIMARY KEY,
                loe_id TEXT,
                metric_key TEXT,
                metric_label TEXT,
                target_value REAL,
                actual_value REAL,
                status TEXT,
                reported_at TEXT,
                created_at TEXT
            );

            -- legacy/older burden_inputs schema handled by later idempotent definition

            CREATE TABLE IF NOT EXISTS burden_snapshots (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr INTEGER,
                month INTEGER,
                scope_type TEXT,
                scope_value TEXT,
                burden_ratio REAL,
                risk_band TEXT,
                computed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS processing_metrics (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr INTEGER,
                month INTEGER,
                scope_type TEXT,
                scope_value TEXT,
                metric_key TEXT,
                metric_label TEXT,
                value REAL,
                unit TEXT,
                reported_at TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS burden_inputs (
                id TEXT PRIMARY KEY,
                scope_type TEXT,
                scope_value TEXT,
                mission_requirement TEXT,
                recruiter_strength INTEGER,
                reporting_date TEXT,
                created_at TEXT
            );

            -- Documents library items + blobs (Phase-5 storage)
            CREATE TABLE IF NOT EXISTS doc_library_item (
                id TEXT PRIMARY KEY,
                org_unit_id INTEGER,
                title TEXT,
                doc_type TEXT,
                tags_json TEXT,
                version INTEGER DEFAULT 1,
                effective_dt TEXT,
                uploaded_by TEXT,
                created_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS doc_blob (
                id TEXT PRIMARY KEY,
                item_id TEXT,
                filename TEXT,
                content_type TEXT,
                size_bytes INTEGER,
                sha256 TEXT,
                path TEXT,
                created_at TEXT
            );

            -- Automation job skeleton
            CREATE TABLE IF NOT EXISTS automation_job (
                id TEXT PRIMARY KEY,
                job_type TEXT,
                status TEXT,
                input_json TEXT,
                output_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            -- indexes to speed up feed queries
            CREATE INDEX IF NOT EXISTS ix_fact_production_org_date ON fact_production(org_unit_id, date_key);
            CREATE INDEX IF NOT EXISTS ix_fact_production_metric ON fact_production(metric_key);

            -- Migration helpers: canonicalize marketing_activities schema and ensure funnel_transitions has lead_id
            -- This attempts a safe, idempotent migration so older DB variants don't cause runtime failures.
            
            """
        )
        # run lightweight schema migrations
        try:
            # inspect marketing_activities columns
            cur.execute("PRAGMA table_info(marketing_activities)")
            cols = [r[1] for r in cur.fetchall()]
            if 'activity_id' not in cols or cols[0] != 'activity_id':
                try:
                    cur.executescript("""
                    PRAGMA foreign_keys=OFF;
                    CREATE TABLE IF NOT EXISTS marketing_activities_new (
                        activity_id TEXT PRIMARY KEY,
                        event_id TEXT,
                        activity_type TEXT,
                        campaign_name TEXT,
                        channel TEXT,
                        data_source TEXT,
                        impressions INTEGER DEFAULT 0,
                        engagement_count INTEGER DEFAULT 0,
                        awareness_metric REAL,
                        activation_conversions INTEGER DEFAULT 0,
                        reporting_date TEXT,
                        metadata TEXT,
                        cost REAL DEFAULT 0,
                        created_at TEXT,
                        import_job_id TEXT,
                        record_status TEXT DEFAULT 'active'
                    );
                    INSERT OR IGNORE INTO marketing_activities_new(activity_id,event_id,activity_type,campaign_name,channel,data_source,impressions,engagement_count,awareness_metric,activation_conversions,reporting_date,metadata,cost,created_at,import_job_id,record_status)
                        SELECT COALESCE(activity_id, CAST(id AS TEXT)), event_id, activity_type, campaign_name, channel, data_source, impressions, engagement_count, awareness_metric, activation_conversions, reporting_date, metadata, cost, created_at, import_job_id, record_status FROM marketing_activities;
                    DROP TABLE IF EXISTS marketing_activities;
                    ALTER TABLE marketing_activities_new RENAME TO marketing_activities;
                    PRAGMA foreign_keys=ON;
                    """)
                except Exception:
                    # if migration fails, continue — runtime handlers will try fallbacks
                    pass

            # ensure funnel_transitions has lead_id column (older schemas may omit it)
            cur.execute("PRAGMA table_info(funnel_transitions)")
            fcols = [r[1] for r in cur.fetchall()]
            if 'lead_id' not in fcols:
                try:
                    cur.execute("ALTER TABLE funnel_transitions ADD COLUMN lead_id TEXT")
                except Exception:
                    pass
            if 'lead_key' not in fcols:
                try:
                    cur.execute("ALTER TABLE funnel_transitions ADD COLUMN lead_key TEXT")
                except Exception:
                    pass
        except Exception:
            # best-effort migrations; do not block startup on errors
            pass

        

        index_statements = [
            "CREATE INDEX IF NOT EXISTS ix_org_unit_parent_id ON org_unit(parent_id);",
            "CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS ix_event_org_unit_id ON event(org_unit_id);",
            "CREATE INDEX IF NOT EXISTS ix_event_metrics_event_id ON event_metrics(event_id);",
            "CREATE INDEX IF NOT EXISTS ix_marketing_event_id ON marketing_activities(event_id);",
        ]
        for stmt in index_statements:
            try:
                cur.execute(stmt)
            except Exception:
                pass

        # Create uniqueness indexes to support deterministic replace semantics (Phase-4)
        unique_statements = [
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_production_org_date_metric ON fact_production(org_unit_id, date_key, metric_key);",
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_marketing_org_date_campaign_channel ON fact_marketing(org_unit_id, date_key, campaign, channel);",
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_event_metrics_event_captured ON event_metrics(event_id, captured_at);",
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_projects_project_id ON projects(project_id);",
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_tasks_task_id ON tasks(task_id);",
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_marketing_activities_activity ON marketing_activities(activity_id);",
        ]
        for stmt in unique_statements:
            try:
                cur.execute(stmt)
            except Exception:
                # If duplicates exist or DB doesn't support, skip — migrations should be safe
                pass

        # Ensure funnel_stages table exists and seed default stages if empty
        try:
            cur.execute('CREATE TABLE IF NOT EXISTS funnel_stages (id TEXT PRIMARY KEY, name TEXT, rank INTEGER, created_at TEXT)')
            cur.execute('SELECT COUNT(1) FROM funnel_stages')
            cnt = cur.fetchone()
            if not cnt or (isinstance(cnt, (list, tuple)) and cnt[0] == 0) or (cnt[0] == 0):
                now = datetime.utcnow().isoformat()
                defaults = [
                    ('lead', 'Lead', 1),
                    ('prospect', 'Prospect', 2),
                    ('applicant', 'Applicant', 3),
                    ('contract', 'Contract', 4),
                    ('accession', 'Accession', 5),
                ]
                for sid, sname, srank in defaults:
                    try:
                        cur.execute('INSERT OR IGNORE INTO funnel_stages(id,name,rank,created_at) VALUES(?,?,?,?)', (sid, sname, srank, now))
                    except Exception:
                        pass
        except Exception:
            pass

        # Maintenance schedule / run history tables
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS maintenance_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                enabled INTEGER DEFAULT 0,
                interval_minutes INTEGER,
                last_run_at TEXT,
                next_run_at TEXT,
                params_json TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS maintenance_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER,
                run_type TEXT,
                params_json TEXT,
                result_json TEXT,
                started_at TEXT,
                finished_at TEXT
            );
            """
        )

        # Attempt lightweight migrations for new Phase-3 columns and legacy compatibility
        def table_columns(table_name: str):
            try:
                cur.execute(f"PRAGMA table_info({table_name})")
                return [r[1] for r in cur.fetchall()]
            except Exception:
                return []

        cols = table_columns('import_job_v3')
        if 'updated_at' not in cols:
            try:
                cur.execute("ALTER TABLE import_job_v3 ADD COLUMN updated_at TEXT")
            except Exception:
                pass

        # Ensure loes table has updated_at (some tests expect this column)
        try:
            lcols = table_columns('loes')
            if 'updated_at' not in lcols:
                try:
                    cur.execute("ALTER TABLE loes ADD COLUMN updated_at TEXT")
                except Exception:
                    pass
        except Exception:
            pass

        # Idempotent additions for tactical dashboards schema compatibility
        try:
            def ensure_col(tbl, col_def):
                try:
                    cur.execute(f"PRAGMA table_info({tbl})")
                    existing = [r[1] for r in cur.fetchall()]
                    col_name = col_def.split()[0]
                    if col_name not in existing:
                        cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col_def}")
                except Exception:
                    pass

            # event table: planned/actual costs and time/echelon metadata
            ensure_col('event', 'planned_cost REAL DEFAULT 0')
            ensure_col('event', 'actual_cost REAL DEFAULT 0')
            ensure_col('event', 'fy INTEGER')
            ensure_col('event', 'qtr INTEGER')
            ensure_col('event', 'month INTEGER')
            ensure_col('event', 'echelon_type TEXT')
            ensure_col('event', 'unit_value TEXT')
            ensure_col('event', 'funding_line TEXT')

            # legacy events table
            ensure_col('events', 'planned_cost REAL DEFAULT 0')
            ensure_col('events', 'actual_cost REAL DEFAULT 0')
            ensure_col('events', 'fy INTEGER')
            ensure_col('events', 'qtr INTEGER')
            ensure_col('events', 'month INTEGER')
            ensure_col('events', 'echelon_type TEXT')
            ensure_col('events', 'unit_value TEXT')
            ensure_col('events', 'funding_line TEXT')

            # marketing_activities: fiscal/time/echelon/funding metadata
            ensure_col('marketing_activities', 'fy INTEGER')
            ensure_col('marketing_activities', 'qtr INTEGER')
            ensure_col('marketing_activities', 'month INTEGER')
            ensure_col('marketing_activities', 'echelon_type TEXT')
            ensure_col('marketing_activities', 'unit_value TEXT')
            ensure_col('marketing_activities', 'funding_line TEXT')

            # funnel_transitions: time/echelon metadata
            ensure_col('funnel_transitions', 'fy INTEGER')
            ensure_col('funnel_transitions', 'qtr INTEGER')
            ensure_col('funnel_transitions', 'month INTEGER')
            ensure_col('funnel_transitions', 'echelon_type TEXT')
            ensure_col('funnel_transitions', 'unit_value TEXT')

            # projects: planned/actual + metadata
            ensure_col('projects', 'planned_cost REAL DEFAULT 0')
            ensure_col('projects', 'actual_cost REAL DEFAULT 0')
            ensure_col('projects', 'fy INTEGER')
            ensure_col('projects', 'qtr INTEGER')
            ensure_col('projects', 'month INTEGER')
            ensure_col('projects', 'echelon_type TEXT')
            ensure_col('projects', 'unit_value TEXT')
            ensure_col('projects', 'funding_line TEXT')

            # budget_line_item: ensure canonical fields used by dashboards
            ensure_col('budget_line_item', 'fy INTEGER')
            ensure_col('budget_line_item', 'qtr INTEGER')
            ensure_col('budget_line_item', 'month INTEGER')
            ensure_col('budget_line_item', 'echelon_type TEXT')
            ensure_col('budget_line_item', 'unit_value TEXT')
            ensure_col('budget_line_item', 'funding_line TEXT')
            ensure_col('budget_line_item', 'allocated_amount REAL DEFAULT 0')
        except Exception:
            # best-effort; don't block startup on migration errors
            pass

        # Ensure legacy import_job columns exist for older code paths
        legacy_cols = [
            ("filename_original", "TEXT"),
            ("file_type", "TEXT"),
            ("file_size_bytes", "INTEGER"),
            ("sha256_hash", "TEXT"),
            ("uploaded_by_user_id", "TEXT"),
            ("uploaded_at", "TEXT"),
            ("target_domain", "TEXT"),
            ("updated_at", "TEXT")
        ]
        existing = table_columns('import_job')
        for col, typ in legacy_cols:
            if col not in existing:
                try:
                    cur.execute(f"ALTER TABLE import_job ADD COLUMN {col} {typ}")
                except Exception:
                    pass

        # Ensure `users` table has `role` and `scope` columns expected by ORM
        try:
            ucols = table_columns('users')
            if 'role' not in ucols:
                try:
                    cur.execute("ALTER TABLE users ADD COLUMN role TEXT")
                except Exception:
                    pass
            if 'scope' not in ucols:
                try:
                    cur.execute("ALTER TABLE users ADD COLUMN scope TEXT")
                except Exception:
                    pass
        except Exception:
            pass

        # When possible, copy values from newer/older columns into legacy names
        try:
            if 'filename_original' in existing and 'filename' in existing:
                cur.execute("UPDATE import_job SET filename_original=filename WHERE filename_original IS NULL AND filename IS NOT NULL")
        except Exception:
            pass
        try:
            if 'sha256_hash' in existing and 'file_hash' in existing:
                cur.execute("UPDATE import_job SET sha256_hash=file_hash WHERE sha256_hash IS NULL AND file_hash IS NOT NULL")
        except Exception:
            pass

        # Phase-4: ensure domain tables have provenance & archival columns where needed
        phase4_alter = [
            ("fact_production", "record_status", "TEXT DEFAULT 'active'"),
            ("fact_production", "archived_at", "TEXT"),
            ("fact_marketing", "record_status", "TEXT DEFAULT 'active'"),
            ("fact_marketing", "archived_at", "TEXT"),
            ("fact_funnel", "record_status", "TEXT DEFAULT 'active'"),
            ("fact_funnel", "archived_at", "TEXT"),
            ("marketing_activities", "created_at", "TEXT"),
            ("marketing_activities", "import_job_id", "TEXT"),
            ("marketing_activities", "record_status", "TEXT DEFAULT 'active'"),
            ("budgets", "import_job_id", "TEXT"),
            ("budgets", "record_status", "TEXT DEFAULT 'active'"),
            # retention metadata: allow per-row keep-until overrides
            ("fact_production", "keep_until", "TEXT"),
            ("fact_marketing", "keep_until", "TEXT"),
            ("fact_funnel", "keep_until", "TEXT"),
            ("marketing_activities", "keep_until", "TEXT"),
            ("budgets", "keep_until", "TEXT"),
            ("projects", "keep_until", "TEXT"),
            ("tasks", "keep_until", "TEXT"),
            ("meeting_minutes", "keep_until", "TEXT"),
            ("action_items", "keep_until", "TEXT"),
            ("calendar_events", "keep_until", "TEXT"),
            ("doc_library", "keep_until", "TEXT"),
            # ensure archived_at exists for domain tables used by maintenance
            ("projects", "archived_at", "TEXT"),
            ("tasks", "archived_at", "TEXT"),
            ("meeting_minutes", "archived_at", "TEXT"),
            ("action_items", "archived_at", "TEXT"),
            ("doc_library", "archived_at", "TEXT"),
            ("marketing_activities", "archived_at", "TEXT"),
            ("budgets", "archived_at", "TEXT"),
        ]
        for tbl, col, typ in phase4_alter:
            try:
                cols = table_columns(tbl)
                if col not in cols:
                    cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {typ}")
            except Exception:
                pass

        # Ensure projects and event domain tables include financial dimensions
        try:
            # projects (domain 'projects') may need fy,qtr,org_unit_id,station_id,funding_line,category,planned_cost,start_date,end_date
            proj_cols = table_columns('projects')
            proj_add = [
                ('fy', 'INTEGER'), ('qtr', 'INTEGER'), ('org_unit_id', 'INTEGER'), ('station_id', 'TEXT'),
                ('funding_line', 'TEXT'), ('category', 'TEXT'), ('planned_cost', 'REAL'), ('start_date', 'TEXT'), ('end_date', 'TEXT')
            ]
            for col, typ in proj_add:
                if col not in proj_cols:
                    try:
                        cur.execute(f"ALTER TABLE projects ADD COLUMN {col} {typ}")
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            # event table: add project_id, fy, qtr, station_id, funding_line, category, planned_cost
            ev_cols = table_columns('event')
            ev_add = [
                ('project_id', 'INTEGER'), ('fy', 'INTEGER'), ('qtr', 'INTEGER'), ('station_id', 'TEXT'),
                ('funding_line', 'TEXT'), ('category', 'TEXT'), ('planned_cost', 'REAL')
            ]
            for col, typ in ev_add:
                if col not in ev_cols:
                    try:
                        cur.execute(f"ALTER TABLE event ADD COLUMN {col} {typ}")
                    except Exception:
                        pass
        except Exception:
            pass

        # Create expenses table (idempotent)
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                event_id INTEGER,
                fy INTEGER,
                qtr INTEGER,
                org_unit_id INTEGER,
                station_id TEXT,
                funding_line TEXT,
                category TEXT,
                amount REAL DEFAULT 0,
                spent_at TEXT,
                vendor TEXT,
                notes TEXT,
                created_at TEXT
            );
            ''')
        except Exception:
            pass

        # Ensure indexes for fast rollups
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_budget_line_item_fy_org ON budget_line_item(fy_budget_id, qtr)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_budget_line_item_dims ON budget_line_item(qtr,event_id,category,amount)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_budget_line_item_funding_source ON budget_line_item(funding_source)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_budget_line_item_eor ON budget_line_item(eor_code)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_expenses_dims ON expenses(fy,qtr,org_unit_id,station_id,funding_line,category)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_projects_dims ON projects(fy,qtr,org_unit_id,station_id,funding_line,category)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_event_dims ON event(fy,qtr,org_unit_id,station_id,funding_line,category)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_project_event_link_proj ON project_event_link(project_id)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_project_event_link_event ON project_event_link(event_id)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_fy_budget_org_fy ON fy_budget(org_unit_id,fy)")
        except Exception:
            pass

        # Phase-10: ensure budget_line_item contains funding-structure columns
        try:
            bcols = table_columns('budget_line_item')
            budget_cols_to_add = [
                ("appropriation_type", "TEXT DEFAULT 'OMA'"),
                ("funding_source", "TEXT"),
                ("sag_code", "TEXT"),
                ("amsco_code", "TEXT"),
                ("mdep_code", "TEXT"),
                ("eor_code", "TEXT"),
                ("is_under_cr", "INTEGER DEFAULT 0"),
            ]
            for col, typ in budget_cols_to_add:
                if col not in bcols:
                    try:
                        cur.execute(f"ALTER TABLE budget_line_item ADD COLUMN {col} {typ}")
                    except Exception:
                        pass
        except Exception:
            pass

        # PHASE-12: Ensure canonical join keys and minimal fact columns exist
        try:
            # Helper to ensure a list of columns exist on a table
            def ensure_columns(table, cols_with_types):
                existing = table_columns(table)
                for col, typ in cols_with_types:
                    if col not in existing:
                        try:
                            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
                        except Exception:
                            pass

            # Canonical columns applied to fact tables and domain tables
            canonical_cols = [
                ("fy", "INTEGER"),
                ("qtr", "INTEGER"),
                ("scope_type", "TEXT"),
                ("scope_value", "TEXT"),
                ("station_rsid", "TEXT"),
                ("reported_at", "TEXT"),
                ("reporting_date", "TEXT"),
                ("created_at", "TEXT"),
                ("updated_at", "TEXT"),
                ("ingested_at", "TEXT")
            ]

            for tbl in ['fact_production', 'fact_marketing', 'fact_funnel', 'event', 'projects', 'expenses', 'budget_line_item', 'events']:
                try:
                    ensure_columns(tbl, canonical_cols)
                except Exception:
                    pass

            # Ensure marketing_activities has canonical metrics/ids requested
            try:
                mcols = table_columns('marketing_activities')
                extra = [
                    ('activity_id', 'TEXT'), ('event_id', 'TEXT'), ('campaign_id', 'TEXT'),
                    ('channel', 'TEXT'), ('cost', 'REAL DEFAULT 0'), ('impressions', 'INTEGER DEFAULT 0'),
                    ('engagements', 'INTEGER DEFAULT 0'), ('clicks', 'INTEGER DEFAULT 0'), ('conversions', 'INTEGER DEFAULT 0'),
                    ('awareness_metric', 'REAL'), ('reported_at', 'TEXT')
                ]
                for col, typ in extra:
                    if col not in mcols:
                        try:
                            cur.execute(f"ALTER TABLE marketing_activities ADD COLUMN {col} {typ}")
                        except Exception:
                            pass
            except Exception:
                pass

            # Ensure funnel_transitions minimal columns
            try:
                fcols = table_columns('funnel_transitions')
                f_extra = [('lead_id', 'TEXT'), ('from_stage', 'TEXT'), ('to_stage', 'TEXT'), ('transitioned_at', 'TEXT')]
                for col, typ in f_extra:
                    if col not in fcols:
                        try:
                            cur.execute(f"ALTER TABLE funnel_transitions ADD COLUMN {col} {typ}")
                        except Exception:
                            pass
            except Exception:
                pass

            # Create outcomes table (minimal) if missing
            try:
                if 'outcomes' not in [t.lower() for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                    # Use CREATE TABLE IF NOT EXISTS to be idempotent
                    cur.executescript('''
                    CREATE TABLE IF NOT EXISTS outcomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        lead_id TEXT,
                        contract_date TEXT,
                        ship_date TEXT,
                        status TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    );
                    ''')
            except Exception:
                # Fallback: always try create table
                try:
                    cur.executescript('''
                    CREATE TABLE IF NOT EXISTS outcomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        lead_id TEXT,
                        contract_date TEXT,
                        ship_date TEXT,
                        status TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    );
                    ''')
                except Exception:
                    pass

            # Ensure budget_line_item has requested canonical keys and station/project/event ids
            try:
                bli_cols = table_columns('budget_line_item')
                bli_extra = [('fy', 'INTEGER'), ('qtr', 'INTEGER'), ('scope_type', 'TEXT'), ('scope_value', 'TEXT'), ('station_rsid', 'TEXT'), ('project_id', 'TEXT'), ('event_id', 'TEXT'), ('allocated_amount', 'REAL DEFAULT 0'), ('obligated_amount', 'REAL DEFAULT 0'), ('expended_amount', 'REAL DEFAULT 0'), ('category', 'TEXT'), ('reported_at', 'TEXT')]
                for col, typ in bli_extra:
                    if col not in bli_cols:
                        try:
                            cur.execute(f"ALTER TABLE budget_line_item ADD COLUMN {col} {typ}")
                        except Exception:
                            pass
            except Exception:
                pass

            # Create/fill funding_sources lookup (allowed values)
            try:
                cur.executescript('''
                CREATE TABLE IF NOT EXISTS funding_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    label TEXT,
                    created_at TEXT
                );
                ''')
                now = datetime.utcnow().isoformat()
                allowed = ['USAREC', 'BDE', 'BN', 'LOCAL_AMP', 'DIRECT_AMP']
                for a in allowed:
                    try:
                        cur.execute('INSERT OR IGNORE INTO funding_sources(key,label,created_at) VALUES(?,?,?)', (a, a, now))
                    except Exception:
                        pass
            except Exception:
                pass

                # LOE metric mapping table used by tactical rollups to evaluate LOE status
                try:
                    cur.executescript('''
                    CREATE TABLE IF NOT EXISTS loe_metric_map (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        loe_id TEXT,
                        metric_key TEXT,
                        metric_type TEXT,
                        threshold REAL,
                        comparator TEXT,
                        created_at TEXT
                    );
                    ''')
                except Exception:
                    pass

            # Create indexes recommended for rollups
            idxs = [
                "CREATE INDEX IF NOT EXISTS ix_fact_dims ON fact_production(fy,qtr,scope_type,scope_value);",
                "CREATE INDEX IF NOT EXISTS ix_fact_marketing_dims ON fact_marketing(fy,qtr,scope_type,scope_value);",
                "CREATE INDEX IF NOT EXISTS ix_fact_funnel_dims ON fact_funnel(fy,qtr,scope_type,scope_value);",
                "CREATE INDEX IF NOT EXISTS ix_events_event_id ON events(event_id);",
                "CREATE INDEX IF NOT EXISTS ix_budget_line_item_project_id ON budget_line_item(project_id);",
                "CREATE INDEX IF NOT EXISTS ix_budget_line_item_event_id ON budget_line_item(event_id);",
                "CREATE INDEX IF NOT EXISTS ix_outcomes_lead_id ON outcomes(lead_id);",
                "CREATE INDEX IF NOT EXISTS ix_marketing_activity_event_id ON marketing_activities(event_id);",
                "CREATE INDEX IF NOT EXISTS ix_station_rsid ON budget_line_item(station_rsid);",
            ]
            for s in idxs:
                try:
                    cur.execute(s)
                except Exception:
                    pass
        except Exception:
            pass

        # Compatibility patches: some routers expect legacy column names in
        # certain tables (events.event_id, marketing_activities.activity_id,
        # zip_metrics.station_rsid). Add those columns when missing so raw
        # SQL endpoints continue to work alongside SQLAlchemy models.
        try:
            cols = table_columns('events')
            if 'event_id' not in cols:
                cur.execute("ALTER TABLE events ADD COLUMN event_id TEXT")
        except Exception:
            pass

        try:
            cols = table_columns('marketing_activities')
            if 'activity_id' not in cols:
                cur.execute("ALTER TABLE marketing_activities ADD COLUMN activity_id TEXT")
        except Exception:
            pass

        # Ensure `marketing_activities` has an integer `id` primary key for
        # compatibility with some code paths that expect it. If missing,
        # recreate the table with `id` as AUTOINCREMENT and copy existing rows.
        try:
            cols = table_columns('marketing_activities')
            if cols and 'id' not in cols:
                try:
                    cur.executescript("""
                    CREATE TABLE IF NOT EXISTS marketing_activities_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT,
                        event_id TEXT,
                        activity_type TEXT,
                        campaign_name TEXT,
                        channel TEXT,
                        data_source TEXT,
                        impressions INTEGER DEFAULT 0,
                        engagement_count INTEGER DEFAULT 0,
                        awareness_metric REAL,
                        activation_conversions INTEGER,
                        reporting_date TEXT,
                        metadata TEXT,
                        cost REAL DEFAULT 0,
                        created_at TEXT,
                        import_job_id TEXT,
                        record_status TEXT DEFAULT 'active',
                        keep_until TEXT,
                        archived_at TEXT
                    );
                    """)
                    copy_cols = [c for c in ['activity_id','event_id','activity_type','campaign_name','channel','data_source','impressions','engagement_count','awareness_metric','activation_conversions','reporting_date','metadata','cost','created_at','import_job_id','record_status','keep_until','archived_at'] if c in cols]
                    if copy_cols:
                        col_list = ','.join(copy_cols)
                        cur.execute(f"INSERT OR IGNORE INTO marketing_activities_new({col_list}) SELECT {col_list} FROM marketing_activities")
                    cur.execute("DROP TABLE IF EXISTS marketing_activities")
                    cur.execute("ALTER TABLE marketing_activities_new RENAME TO marketing_activities")
                except Exception:
                    pass
        except Exception:
            pass

        # Ensure zip_metrics exists with sensible columns used by compatibility routers
        try:
            cols = table_columns('zip_metrics')
            if not cols:
                cur.executescript("""
                CREATE TABLE IF NOT EXISTS zip_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zip TEXT,
                    metric_key TEXT,
                    metric_value REAL,
                    station_rsid TEXT,
                    scope TEXT,
                    as_of TEXT
                );
                """)
            else:
                # add station_rsid if missing
                if 'station_rsid' not in cols:
                    try:
                        cur.execute("ALTER TABLE zip_metrics ADD COLUMN station_rsid TEXT")
                    except Exception:
                        pass
        except Exception:
            pass
        # Add legacy alias columns expected by older raw SQL routers
        try:
            cols = table_columns('events')
            legacy_event_cols = ['type', 'team_size', 'targeting_principles', 'org_unit_id']
            for c in legacy_event_cols:
                if c not in cols:
                    try:
                        cur.execute(f"ALTER TABLE events ADD COLUMN {c} TEXT")
                    except Exception:
                        pass
        except Exception:
            pass

        # Reconcile legacy `events` table to ensure it includes an integer
        # `id` primary key and compatible columns. SQLite cannot alter a
        # PRIMARY KEY in-place reliably, so recreate a safe table when
        # necessary and copy existing data across. This keeps older raw-SQL
        # routers and newer `event` table semantics working together.
        try:
            cols = table_columns('events')
            if cols and 'id' not in cols:
                try:
                    cur.executescript("""
                    CREATE TABLE IF NOT EXISTS events_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE,
                        name TEXT,
                        type TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        budget REAL,
                        team_size INTEGER,
                        targeting_principles TEXT,
                        org_unit_id TEXT,
                        created_at TEXT
                    );
                    """)
                    # Copy columns that actually exist from old table into new
                    copy_cols = [c for c in ['event_id','name','type','location','start_date','end_date','budget','team_size','targeting_principles','org_unit_id','created_at'] if c in cols]
                    if copy_cols:
                        col_list = ','.join(copy_cols)
                        cur.execute(f"INSERT OR IGNORE INTO events_new({col_list}) SELECT {col_list} FROM events")
                    cur.execute("DROP TABLE IF EXISTS events")
                    cur.execute("ALTER TABLE events_new RENAME TO events")
                except Exception:
                    # Non-fatal; best-effort migration to reduce surprises.
                    pass
        except Exception:
            pass

        try:
            cols = table_columns('marketing_activities')
            legacy_marketing_cols = ['engagement_count', 'awareness_metric', 'activation_conversions', 'metadata']
            for c in legacy_marketing_cols:
                if c not in cols:
                    try:
                        cur.execute(f"ALTER TABLE marketing_activities ADD COLUMN {c} TEXT")
                    except Exception:
                        pass
        except Exception:
            pass

        conn.commit()
        # If SQLAlchemy models are present, try to ensure their tables exist
        try:
            # Import all model modules that register tables on the shared Base
            try:
                from services.api.app import models, models_domain, models_ingest
            except Exception:
                # best-effort: import what we can
                from services.api.app import models
            try:
                from services.api.app import database
                models.Base.metadata.create_all(bind=database.engine)
            except Exception:
                pass
        except Exception:
            pass
    finally:
        try:
            if using_raw_engine:
                # raw_connection() returns a DB-API connection that must be closed
                conn.close()
            else:
                conn.close()
        except Exception:
            pass


def init_db() -> str:
    """Compatibility wrapper used by tests and startup scripts.

    Ensures the schema exists and returns the DB path that was initialized.
    """
    # Keep init_db minimal and non-destructive for tests and dev helpers.
    init_schema()
    return get_db_path()


def row_to_dict(cur, row):
    """Normalize a DB row into a plain dict.

    Works with sqlite3.Row, mapping-like objects, tuples (using cursor.description),
    and returns None for falsy rows.
    """
    if not row:
        return None
    # If it's already a dict-like mapping
    try:
        if isinstance(row, dict):
            return row
        # sqlite3.Row supports keys() and mapping protocol
        if hasattr(row, 'keys'):
            return dict(row)
    except Exception:
        pass
    # If it's a sequence (tuple/list), derive column names from cursor
    try:
        desc = getattr(cur, 'description', None)
        if desc:
            return {desc[i][0]: row[i] for i in range(len(desc))}
    except Exception:
        pass
    # Fallback: attempt to coerce to dict
    try:
        return dict(row)
    except Exception:
        return {"value": row}


def execute_with_retry(cur, sql, params=(), retries: int = 5, backoff: float = 0.05):
    """Execute a SQL statement with retries on transient 'database is locked' errors.

    Args:
        cur: sqlite3 cursor-like object with an `execute` method.
        sql: SQL string or prepared statement.
        params: tuple or dict of parameters for the execute call.
        retries: number of attempts before re-raising the exception.
        backoff: initial backoff in seconds; will double on each retry.
    """
    attempt = 0
    delay = backoff
    while True:
        try:
            if params is None:
                return cur.execute(sql)
            return cur.execute(sql, params)
        except Exception as exc:
            msg = str(exc).lower()
            attempt += 1
            # retry only for sqlite locked errors
            if attempt > retries or 'locked' not in msg:
                raise
            sleep(delay)
            delay = min(delay * 2, 2.0)


# Backwards compatibility: expose names expected elsewhere in the codebase
__all__ = ["get_db_path", "connect", "get_db_conn", "init_schema", "init_db", "execute_with_retry"]
