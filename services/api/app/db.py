import os
import sqlite3
from datetime import datetime
from typing import Optional


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
    try:
        from services.api.app.database import engine
        raw = engine.raw_connection()
        # raw_connection() returns a DB-API connection (sqlite3.Connection)
        raw.row_factory = sqlite3.Row
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
        conn.row_factory = sqlite3.Row
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
    # Prefer using the SQLAlchemy engine's raw DB-API connection when
    # available so DDL is executed through the same connection pool
    # the tests/ORM use. This reduces file-lock conflicts caused by
    # mixing direct sqlite3 connections with SQLAlchemy-managed ones.
    try:
        from services.api.app.database import engine
        raw_conn = engine.raw_connection()
        cur = raw_conn.cursor()
        conn = raw_conn
        using_raw_engine = True
    except Exception:
        # Fallback for environments where SQLAlchemy isn't configured
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
            CREATE INDEX IF NOT EXISTS ix_fact_production_import ON fact_production(import_job_id);
            CREATE INDEX IF NOT EXISTS ix_fact_funnel_org_date ON fact_funnel(org_unit_id, date_key);
            CREATE INDEX IF NOT EXISTS ix_fact_funnel_import ON fact_funnel(import_job_id);
            CREATE INDEX IF NOT EXISTS ix_fact_marketing_org_date ON fact_marketing(org_unit_id, date_key);
            CREATE INDEX IF NOT EXISTS ix_fact_marketing_import ON fact_marketing(import_job_id);

            """
        )

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
    init_schema()
    return get_db_path()


# Backwards compatibility: expose names expected elsewhere in the codebase
__all__ = ["get_db_path", "connect", "get_db_conn", "init_schema", "init_db"]
