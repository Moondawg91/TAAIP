import os
import sqlite3
import fcntl
import threading
from datetime import datetime
from typing import Optional
import time
from time import sleep

# When running under the test harness we may want to force use of a
# specific DB-API connection so raw sqlite3 callers and SQLAlchemy
# sessions operate on the same underlying connection/transaction.
_test_raw_conn = None
_test_raw_conn_path = None
_advisory_lock_fd = None
_advisory_lock_lock = threading.Lock()


def set_test_raw_conn(conn):
    """Set a DB-API connection to be returned by connect() during tests."""
    global _test_raw_conn
    # Accept either a direct sqlite3.Connection or a SQLAlchemy wrapper
    # that exposes the underlying DB-API connection as `connection` or
    # `dbapi_connection`.
    if conn is None:
        _test_raw_conn = None
        try:
            global _test_raw_conn_path
            _test_raw_conn_path = None
        except Exception:
            pass
        # If we previously patched sqlite3.connect, restore the original.
        try:
            orig = getattr(sqlite3, '_orig_connect', None)
            if orig is not None:
                sqlite3.connect = orig
                try:
                    delattr(sqlite3, '_orig_connect')
                except Exception:
                    pass
        except Exception:
            pass
        return
    try:
        if isinstance(conn, sqlite3.Connection):
            _test_raw_conn = conn
            # Attempt to determine the underlying DB file path for this
            # sqlite3 connection so callers of `connect()` can validate
            # whether reusing this connection matches the requested
            # `TAAIP_DB_PATH` file. Use `PRAGMA database_list` which returns
            # the attached database file path.
            try:
                cur = conn.cursor()
                cur.execute("PRAGMA database_list;")
                rows = cur.fetchall()
                if rows and len(rows[0]) >= 3:
                    _test_raw_conn_path = rows[0][2]
            except Exception:
                _test_raw_conn_path = None
            return
        # common SQLAlchemy wrappers expose the underlying DBAPI
        maybe = getattr(conn, 'connection', None) or getattr(conn, 'dbapi_connection', None)
        if isinstance(maybe, sqlite3.Connection):
            _test_raw_conn = maybe
            # If tests provided a raw connection, patch sqlite3.connect so
            # subsequent callers that request the same DB path will reuse
            # the test-provided connection. We only patch calls that target
            # the configured `TAAIP_DB_PATH` to avoid interfering with other
            # independent DB files used by scripts.
            try:
                # preserve original connect if not already preserved
                if not hasattr(sqlite3, '_orig_connect'):
                    setattr(sqlite3, '_orig_connect', sqlite3.connect)

                orig_connect = getattr(sqlite3, '_orig_connect')

                def _patched_connect(path=None, *args, **kwargs):
                    try:
                        # If the caller requested the same DB path used by
                        # the application/tests, return our connect() which
                        # will reuse the test raw connection.
                        if path is None or str(path) == str(get_db_path()):
                            return connect()
                    except Exception:
                        pass
                    # Otherwise delegate to the original sqlite3.connect.
                    return orig_connect(path, *args, **kwargs)

                sqlite3.connect = _patched_connect
            except Exception:
                pass
            return
    except Exception:
        pass
    # If we couldn't unwrap, store the provided object as a last resort.
    _test_raw_conn = conn

def get_db_path() -> str:
    """Return path to the SQLite DB file.

    Reads `TAAIP_DB_PATH` environment variable. Falls back to
    `./data/taaip.sqlite3` to match test expectations and CI.
    """
    return os.getenv("TAAIP_DB_PATH", "./data/taaip.sqlite3")


def get_documents_path() -> str:
    """Return path to the documents storage directory. Created if missing."""
    p = os.getenv('TAAIP_DOCUMENTS_PATH', './data/documents')
    _ensure_db_dir(p + '/placeholder')
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)
    return p


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
    # Use sqlite3.Row so callers can access rows by index and by column name.
    _row_factory = sqlite3.Row
    # If tests set a dedicated raw DB-API connection, return that so all
    # callers operate on the same physical connection/transaction.
    global _test_raw_conn
    if _test_raw_conn is not None:
        # ensure the helper row factory is available before assignment
        def _dict_row_factory(cursor, row):
            # return a plain dict for each row so callers can safely do dict(row)
            try:
                return {d[0]: row[i] for i, d in enumerate(cursor.description)}
            except Exception:
                return row

        # Only reuse the test-provided raw connection when the path
        # requested by `get_db_path()` matches the DB file path of the
        # stored connection. This avoids accidentally reusing a
        # connection bound to a different file when tests change
        # `TAAIP_DB_PATH` per-test.
        try:
            global _test_raw_conn_path
            requested = str(get_db_path())
            if _test_raw_conn_path and os.path.abspath(_test_raw_conn_path) != os.path.abspath(requested):
                # Do not reuse; fall through to open a new connection
                pass
            else:
                # Avoid returning the same sqlite3.Connection object across
                # multiple threads. Reusing a single Connection instance from
                # different threads can produce 'database is locked' errors even
                # when `check_same_thread=False` is used. Instead, open a new
                # connection to the same DB file so each caller gets its own
                # connection object while still targeting the same underlying
                # database file (this preserves test isolation semantics).
                try:
                    # Create a fresh sqlite3 connection to the requested path
                    new_conn = sqlite3.connect(requested, check_same_thread=False, timeout=30)
                    new_conn.row_factory = _row_factory
                    cur = new_conn.cursor()
                    cur.executescript("""
                    PRAGMA foreign_keys=ON;
                    PRAGMA journal_mode=WAL;
                    PRAGMA synchronous=NORMAL;
                    PRAGMA busy_timeout=20000;
                    """)
                    try:
                        print(f"connect: opened new sqlite3 conn (from test_raw_conn) for path={path}")
                    except Exception:
                        pass
                    return new_conn
                except Exception:
                    # Fall back to trying to reuse the provided connection
                    try:
                        _test_raw_conn.row_factory = _row_factory
                        _test_raw_conn.cursor()
                        try:
                            print(f"connect: reusing test_raw_conn for path={path}")
                        except Exception:
                            pass
                        return _test_raw_conn
                    except Exception:
                        try:
                            _test_raw_conn.close()
                        except Exception:
                            pass
        except Exception:
            # fall through to normal behavior
            pass

    # Attempt to reload the SQLAlchemy engine if the application needs it.
    try:
        from services.api.app import database as _database
        try:
            _database.reload_engine_if_needed()
        except Exception:
            pass
    except Exception:
        pass

    # Use a plain sqlite3 connection for predictable DB-API behavior.
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    conn.row_factory = _row_factory
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys=ON;
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    PRAGMA busy_timeout=20000;
    """)
    conn.commit()
    try:
        print(f"connect: opened new sqlite3 conn for path={path}")
    except Exception:
        pass
    return conn


def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        return column in cols
    except Exception:
        return False


def _add_column_if_missing(cur: sqlite3.Cursor, table: str, column: str, ddl: str) -> None:
    if not _column_exists(cur, table, column):
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        except Exception:
            # best-effort, non-fatal
            pass


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Public helper: return True if `column` exists on `table`.

    Uses PRAGMA table_info and is safe to call repeatedly.
    """
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        return column in cols
    except Exception:
        return False


def safe_add_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> bool:
    """Idempotently add a column to a table.

    Returns True if column was added or already existed, False on error.
    This will not drop or modify existing data.
    """
    try:
        cur = conn.cursor()
        if column in [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]:
            return True
        cur.execute("BEGIN")
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def _migrate_mission_feasibility_schema(conn: sqlite3.Connection) -> None:
    """Ensure canonical columns exist for mission feasibility and backfill from legacy columns.

    This function is idempotent and safe to run on every startup.
    """
    try:
        cur = conn.cursor()

        # mission_target: ensure annual_contract_mission, fy, unit_rsid
        _add_column_if_missing(cur, 'mission_target', 'annual_contract_mission', 'INTEGER')
        _add_column_if_missing(cur, 'mission_target', 'fy', 'INTEGER')
        _add_column_if_missing(cur, 'mission_target', 'unit_rsid', 'TEXT')
        # backfill mission_contracts -> annual_contract_mission
        try:
            cur.execute("UPDATE mission_target SET annual_contract_mission = mission_contracts WHERE annual_contract_mission IS NULL AND mission_contracts IS NOT NULL")
        except Exception:
            pass
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mission_target_unit_fy ON mission_target(unit_rsid, fy)")
        except Exception:
            pass

        # recruiter_strength: ensure recruiters_assigned, recruiters_available, month, unit_rsid
        _add_column_if_missing(cur, 'recruiter_strength', 'recruiters_assigned', 'INTEGER')
        _add_column_if_missing(cur, 'recruiter_strength', 'recruiters_available', 'INTEGER')
        _add_column_if_missing(cur, 'recruiter_strength', 'month', 'TEXT')
        _add_column_if_missing(cur, 'recruiter_strength', 'unit_rsid', 'TEXT')
        # backfill producers_available -> recruiters_available
        try:
            cur.execute("UPDATE recruiter_strength SET recruiters_available = producers_available WHERE recruiters_available IS NULL AND producers_available IS NOT NULL")
        except Exception:
            pass
        # backfill assigned_strength if exists
        try:
            cur.execute("UPDATE recruiter_strength SET recruiters_assigned = assigned_strength WHERE recruiters_assigned IS NULL AND assigned_strength IS NOT NULL")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_recruiter_strength_unit_month ON recruiter_strength(unit_rsid, month)")
        except Exception:
            pass

        # market_capacity: ensure baseline_contract_capacity, market_burden_factor, fy, unit_rsid
        _add_column_if_missing(cur, 'market_capacity', 'baseline_contract_capacity', 'INTEGER')
        _add_column_if_missing(cur, 'market_capacity', 'market_burden_factor', 'REAL DEFAULT 1.0')
        _add_column_if_missing(cur, 'market_capacity', 'fy', 'INTEGER')
        _add_column_if_missing(cur, 'market_capacity', 'unit_rsid', 'TEXT')
        # backfill market_index -> baseline_contract_capacity
        try:
            cur.execute("UPDATE market_capacity SET baseline_contract_capacity = CAST(market_index AS INTEGER) WHERE baseline_contract_capacity IS NULL AND market_index IS NOT NULL")
        except Exception:
            pass
        # ensure market_burden_factor has defaults
        try:
            cur.execute("UPDATE market_capacity SET market_burden_factor = 1.0 WHERE market_burden_factor IS NULL")
        except Exception:
            pass
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_market_capacity_unit_fy ON market_capacity(unit_rsid, fy)")
        except Exception:
            pass

        try:
            conn.commit()
        except Exception:
            pass
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return
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
        # Debug trace: show which DB path we're initializing and whether
        # a test raw connection is present and its path.
        try:
            global _test_raw_conn_path
            print(f"init_schema: requested_path={get_db_path()}, test_raw_conn_path={_test_raw_conn_path}")
        except Exception:
            pass
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

            -- Canonical unit table: represent all echelons as nodes
            CREATE TABLE IF NOT EXISTS unit (
                unit_code TEXT PRIMARY KEY,
                echelon TEXT NOT NULL CHECK (echelon IN ('MACOM','BDE','BN','CO','STN')),
                unit_name TEXT NOT NULL,
                parent_code TEXT NULL REFERENCES unit(unit_code),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_unit_parent ON unit(parent_code);
            CREATE INDEX IF NOT EXISTS idx_unit_echelon ON unit(echelon);

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

            -- Minimal org tables matching SQLAlchemy models used in tests
            CREATE TABLE IF NOT EXISTS brigades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brigade_prefix TEXT NOT NULL,
                display TEXT,
                command_id INTEGER,
                created_at TEXT,
                UNIQUE (brigade_prefix, command_id)
            );

            CREATE TABLE IF NOT EXISTS battalions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battalion_prefix TEXT NOT NULL,
                display TEXT,
                brigade_id INTEGER,
                created_at TEXT,
                UNIQUE (battalion_prefix, brigade_id)
            );

            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_prefix TEXT NOT NULL,
                display TEXT,
                battalion_id INTEGER,
                created_at TEXT,
                UNIQUE (company_prefix, battalion_id)
            );

            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rsid TEXT NOT NULL UNIQUE,
                display TEXT,
                company_id INTEGER,
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

            CREATE TABLE IF NOT EXISTS import_job_preview (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_job_id TEXT NOT NULL,
                preview_json TEXT,
                columns_json TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS imported_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_job_id INTEGER,
                target_domain TEXT,
                row_json TEXT,
                created_at TEXT
            );

            -- Ingest pipeline tables (new)
            CREATE TABLE IF NOT EXISTS ingest_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_system TEXT,
                original_filename TEXT,
                stored_path TEXT,
                file_hash TEXT,
                uploaded_by TEXT,
                uploaded_at TEXT
            );

            CREATE TABLE IF NOT EXISTS ingest_run (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_file_id INTEGER,
                importer_id TEXT,
                started_at TEXT,
                finished_at TEXT,
                status TEXT,
                row_count_in INTEGER DEFAULT 0,
                row_count_loaded INTEGER DEFAULT 0,
                errors_json TEXT
            );

            CREATE TABLE IF NOT EXISTS ingest_row_error (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_run_id INTEGER,
                row_number INTEGER,
                error_code TEXT,
                error_message TEXT,
                row_json TEXT
            );

            CREATE TABLE IF NOT EXISTS stg_raw_dataset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_run_id INTEGER,
                row_number INTEGER,
                row_json TEXT
            );

            CREATE TABLE IF NOT EXISTS stg_raw_dataset_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingest_file_id INTEGER,
                columns_json TEXT,
                sample_json TEXT,
                detected_source_hint TEXT
            );

            -- Data Hub import tables (canonical names used by Data Hub APIs)
            CREATE TABLE IF NOT EXISTS import_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha256 TEXT UNIQUE,
                original_filename TEXT,
                stored_path TEXT,
                content_type TEXT,
                byte_size INTEGER,
                uploaded_at TEXT
            );

            CREATE TABLE IF NOT EXISTS import_run (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_file_id INTEGER,
                source_system TEXT,
                dataset_key TEXT,
                status TEXT,
                started_at TEXT,
                finished_at TEXT,
                rows_in INTEGER DEFAULT 0,
                rows_inserted INTEGER DEFAULT 0,
                rows_updated INTEGER DEFAULT 0,
                rows_rejected INTEGER DEFAULT 0,
                warnings_json TEXT,
                errors_json TEXT,
                detected_signature_json TEXT,
                dry_run INTEGER DEFAULT 0,
                initiated_by TEXT
            );

            CREATE TABLE IF NOT EXISTS import_row_error (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_run_id INTEGER,
                row_number INTEGER,
                severity TEXT,
                message TEXT,
                raw_row_json TEXT
            );

            -- DEP Loss fact table (station-level)
            CREATE TABLE IF NOT EXISTS fact_dep_loss (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- joins
                station_rsid TEXT NOT NULL,

                -- dimensions
                time_period TEXT NOT NULL,
                cmpnt_cd TEXT NOT NULL,
                loss_bucket TEXT NOT NULL,

                -- measures
                dep_losses INTEGER NOT NULL DEFAULT 0,
                cancellation_rcm_number TEXT NULL,

                -- traceability
                source_primary_key TEXT NULL,
                ingested_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_dep_loss_station ON fact_dep_loss(station_rsid);
            CREATE INDEX IF NOT EXISTS idx_dep_loss_station_tp ON fact_dep_loss(station_rsid, time_period);
            CREATE INDEX IF NOT EXISTS idx_dep_loss_station_tp_cmpnt ON fact_dep_loss(station_rsid, time_period, cmpnt_cd);

            -- Normalized Data Hub tables
            CREATE TABLE IF NOT EXISTS emm_event (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                mac_id TEXT,
                event_name TEXT,
                event_type TEXT,
                start_date TEXT,
                end_date TEXT,
                location_name TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                cbsa_code TEXT,
                unit_rsid TEXT,
                cost_total REAL,
                notes TEXT,
                source_import_run_id INTEGER,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS emm_mac (
                mac_id TEXT PRIMARY KEY,
                mac_name TEXT,
                mac_type TEXT,
                unit_rsid TEXT,
                status TEXT,
                source_import_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS g2_market_metric (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_key TEXT,
                value_real REAL,
                value_text TEXT,
                as_of_date TEXT,
                cbsa_code TEXT,
                zip TEXT,
                unit_rsid TEXT,
                echelon TEXT,
                unit_display TEXT,
                source_import_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS alrl_school (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id TEXT,
                school_name TEXT,
                district TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                unit_rsid TEXT,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                contract_status TEXT,
                contract_date TEXT,
                source_import_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fstsm_metric (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_key TEXT,
                value_real REAL,
                value_text TEXT,
                as_of_date TEXT,
                unit_rsid TEXT,
                source_import_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS aie_lead_stub (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aie_person_key TEXT,
                created_at TEXT,
                lead_source TEXT,
                unit_rsid TEXT,
                cbsa_code TEXT,
                source_import_run_id INTEGER
            );

            -- Assets master list tables
            CREATE TABLE IF NOT EXISTS asset_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT UNIQUE,
                asset_name TEXT,
                asset_type TEXT,
                category TEXT,
                supported_objectives TEXT,
                supported_tactics TEXT,
                description TEXT,
                constraints TEXT,
                requires_approval_level TEXT,
                enabled INTEGER DEFAULT 1,
                version INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS asset_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id TEXT UNIQUE,
                asset_id TEXT,
                owning_unit_rsid TEXT,
                holding_unit_rsid TEXT,
                status TEXT,
                available_from_dt TEXT,
                available_to_dt TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS asset_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE,
                unit_rsid TEXT,
                event_id TEXT,
                requested_asset_type TEXT,
                requested_asset_ids TEXT,
                priority TEXT,
                needed_start_dt TEXT,
                needed_end_dt TEXT,
                justification TEXT,
                approval_status TEXT,
                approval_chain TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS asset_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id TEXT UNIQUE,
                request_id TEXT,
                asset_id TEXT,
                assigned_unit_rsid TEXT,
                assigned_start_dt TEXT,
                assigned_end_dt TEXT,
                assignment_status TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS asset_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT,
                capability_key TEXT,
                weight REAL DEFAULT 1.0
            );

            -- Fact tables required by the importer registry
            CREATE TABLE IF NOT EXISTS fact_enlistments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                grain TEXT,
                period_start TEXT,
                period_end TEXT,
                metric_name TEXT,
                metric_value REAL,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_productivity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                period_start TEXT,
                period_end TEXT,
                metric_name TEXT,
                metric_value REAL,
                recruiter_id TEXT,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_zip_potential (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip TEXT,
                unit_rsid TEXT,
                cbsa_code TEXT,
                category TEXT,
                metric_name TEXT,
                metric_value REAL,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_school_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                school_id TEXT,
                school_name TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                contact_name TEXT,
                contact_type TEXT,
                email TEXT,
                phone TEXT,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_school_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                school_id TEXT,
                school_name TEXT,
                contract_type TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_alrl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                period_start TEXT,
                period_end TEXT,
                metric_name TEXT,
                metric_value REAL,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_mission_category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                period_start TEXT,
                period_end TEXT,
                mission_category TEXT,
                metric_name TEXT,
                metric_value REAL,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS fact_emm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                period_start TEXT,
                period_end TEXT,
                metric_name TEXT,
                metric_value REAL,
                source_system TEXT,
                ingest_run_id INTEGER
            );

            -- Ensure provenance columns exist for processed state (safe to run repeatedly)
            -- Older DB files may not have these columns; attempt to add them if missing.
            PRAGMA user_version;

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                who TEXT,
                action TEXT,
                entity TEXT,
                entity_id INTEGER,
                meta_json TEXT,
                created_at TEXT
            );

            -- Mission Feasibility tables
            CREATE TABLE IF NOT EXISTS mission_target (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT NOT NULL,
                fy INTEGER NOT NULL,
                annual_contract_mission INTEGER NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(unit_rsid, fy)
            );

            CREATE TABLE IF NOT EXISTS recruiter_strength (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT NOT NULL,
                month TEXT NOT NULL,
                recruiters_assigned INTEGER NOT NULL,
                recruiters_available INTEGER NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(unit_rsid, month)
            );

            CREATE INDEX IF NOT EXISTS idx_recruiter_strength_unit_month ON recruiter_strength(unit_rsid, month);

            CREATE TABLE IF NOT EXISTS market_capacity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT NOT NULL,
                fy INTEGER NOT NULL,
                baseline_contract_capacity INTEGER NOT NULL,
                market_burden_factor REAL NOT NULL DEFAULT 1.0,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(unit_rsid, fy)
            );

            CREATE INDEX IF NOT EXISTS idx_market_capacity_unit_fy ON market_capacity(unit_rsid, fy);

            CREATE TABLE IF NOT EXISTS feasibility_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT NOT NULL,
                fy INTEGER NOT NULL,
                generated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(unit_rsid, fy)
            );

            -- RBAC permission tables
            CREATE TABLE IF NOT EXISTS permission (
                key TEXT PRIMARY KEY,
                description TEXT,
                category TEXT
            );

            CREATE TABLE IF NOT EXISTS user_permission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                permission_key TEXT,
                granted INTEGER DEFAULT 1,
                granted_by TEXT,
                granted_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(permission_key) REFERENCES permission(key)
            );

            CREATE TABLE IF NOT EXISTS role_template (
                key TEXT PRIMARY KEY,
                name TEXT,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS role_template_permission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_key TEXT,
                permission_key TEXT,
                granted INTEGER DEFAULT 1,
                FOREIGN KEY(role_key) REFERENCES role_template(key),
                FOREIGN KEY(permission_key) REFERENCES permission(key)
            );

            -- Additional RBAC tables per TOR: user_account, role, role_permission, user_role, user_permission_override
            CREATE TABLE IF NOT EXISTS user_account (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS role (
                role_key TEXT PRIMARY KEY,
                display_name TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS role_permission (
                role_key TEXT,
                permission_key TEXT,
                granted INTEGER DEFAULT 1,
                PRIMARY KEY(role_key, permission_key),
                FOREIGN KEY(role_key) REFERENCES role(role_key),
                FOREIGN KEY(permission_key) REFERENCES permission(key)
            );

            CREATE TABLE IF NOT EXISTS user_role (
                user_id TEXT,
                role_key TEXT,
                PRIMARY KEY(user_id, role_key),
                FOREIGN KEY(user_id) REFERENCES user_account(id),
                FOREIGN KEY(role_key) REFERENCES role(role_key)
            );

            CREATE TABLE IF NOT EXISTS user_permission_override (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                permission_key TEXT,
                granted INTEGER,
                reason TEXT,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES user_account(id),
                FOREIGN KEY(permission_key) REFERENCES permission(key)
            );

            -- Data Hub registry and storage tables (canonical)
            CREATE TABLE IF NOT EXISTS dataset_registry (
                dataset_key TEXT PRIMARY KEY,
                source_system TEXT,
                display_name TEXT,
                enabled INTEGER DEFAULT 1,
                file_types TEXT,
                sheet_hints TEXT,
                detection_keywords TEXT,
                required_columns TEXT,
                optional_columns TEXT,
                primary_date_column TEXT,
                unit_columns TEXT,
                target_table TEXT,
                normalizer_key TEXT,
                version INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );

            -- Seed dataset_registry with common USAREC datasets (idempotent)
            INSERT OR IGNORE INTO dataset_registry (dataset_key, source_system, display_name, enabled, file_types, sheet_hints, detection_keywords, required_columns, optional_columns, primary_date_column, unit_columns, target_table, normalizer_key, version, created_at, updated_at) VALUES
            ('EMM_PORTAL_EVENTS','EMM','EMM Portal - Events',1,'["xlsx","csv"]','["events","mac"]','["emm","events","mac"]','["event_name","start_date","end_date"]','[]',NULL,'["unit_rsid","bde","bn","co","stn"]','emm_event','emm_events_normalizer',1, datetime('now'), datetime('now')),
            ('EMM_MAC_ASSIGNMENTS','EMM','EMM MAC Assignments',1,'["xlsx","csv"]','["macs","assignments"]','["mac","assignment"]','["mac_id","mac_name"]','[]',NULL,'["unit_rsid"]','emm_mac','emm_macs_normalizer',1, datetime('now'), datetime('now')),
            ('USAREC_G2_ENLISTMENTS_BY_BDE','USAREC_G2','USAREC G2 - Enlistments by BDE',1,'["xlsx","csv"]','["enlistments","bde"]','["g2","enlist","bde"]','["bde","enlistments"]','[]',NULL,'["bde","bn"]','fact_enlistments','g2_enlistments_normalizer',1, datetime('now'), datetime('now')),
            ('USAREC_G2_ENLISTMENTS_BY_BN','USAREC_G2','USAREC G2 - Enlistments by BN',1,'["xlsx","csv"]','["enlistments","bn"]','["g2","enlist","bn"]','["bn","enlistments"]','[]',NULL,'["bn","co"]','fact_enlistments','g2_enlistments_normalizer',1, datetime('now'), datetime('now')),
            ('USAREC_G2_ENLISTMENTS_BY_CBSA','USAREC_G2','USAREC G2 - Enlistments by CBSA',1,'["xlsx","csv"]','["cbsa","enlist"]','["g2","cbsa","enlist"]','["cbsa","enlistments"]','[]',NULL,'["cbsa"]','fact_enlistments','g2_cbsa_normalizer',1, datetime('now'), datetime('now')),
            ('USAREC_G2_URBANICITY_BY_CBSA','USAREC_G2','USAREC G2 - Urbanicity by CBSA',1,'["xlsx","csv"]','["urbanicity","cbsa"]','["urbanicity","cbsa"]','["cbsa","urbanicity"]','[]',NULL,'["cbsa"]','g2_market_metric','g2_urbanicity_normalizer',1, datetime('now'), datetime('now')),
            ('ALRL_ZIP_CATEGORY_REPORT','ALRL','ALRL - ZIP Category Report',1,'["xlsx","csv"]','["zip","category","sama"]','["alrl","zip","sama"]','["zip","zip_category"]','[]',NULL,'["zip"]','alrl_school','alrl_zip_normalizer',1, datetime('now'), datetime('now')),
            ('ALRL_SAMA_ZIP_REPORT','ALRL','ALRL - SAMA ZIP Report',1,'["xlsx","csv"]','["sama","zip"]','["alrl","sama","zip"]','["zip","sama_category"]','[]',NULL,'["zip"]','alrl_school','alrl_sama_normalizer',1, datetime('now'), datetime('now')),
            ('SCHOOL_CONTACTS','ALRL','School Contacts',1,'["xlsx","csv"]','["schools","contacts"]','["school","contact","email"]','["school_name","contact_name","email"]','[]',NULL,'["unit_rsid"]','fact_school_contacts','school_contacts_normalizer',1, datetime('now'), datetime('now')),
            ('SCHOOL_CONTRACTS','ALRL','School Contracts',1,'["xlsx","csv"]','["contracts","schools"]','["contract","school"]','["school_id","contract_date"]','[]',NULL,'["unit_rsid"]','fact_school_contracts','school_contracts_normalizer',1, datetime('now'), datetime('now')),
            ('FSTS_DASHBOARD_EXPORT','FSTS','FSTS Dashboard Export',1,'["csv"]','[]','["fsts","dashboard"]','[]','[]',NULL,'[]','fstsm_metric','fsts_normalizer',1, datetime('now'), datetime('now')),
            ('VANTAGE_THOR_LEADS_EXPORT','VANTAGE','Vantage Thor Leads',1,'["csv","xlsx"]','[]','["vantage","thor","leads"]','["lead_id","created_at"]','[]',NULL,'["unit_rsid"]','lead_journey_fact','vantage_normalizer',1, datetime('now'), datetime('now')),
            ('AIE_LEADS_EXPORT','AIE','AIE Leads Export',1,'["csv","xlsx"]','[]','["aie","leads","person"]','["person_key","lead_created_dt"]','[]',NULL,'["unit_rsid"]','lead_journey_fact','aie_normalizer',1, datetime('now'), datetime('now'));
            -- Ensure USAREC org hierarchy dataset is present (idempotent)
            INSERT OR IGNORE INTO dataset_registry (dataset_key, source_system, display_name, enabled, file_types, sheet_hints, detection_keywords, required_columns, optional_columns, primary_date_column, unit_columns, target_table, normalizer_key, version, created_at, updated_at) VALUES
            ('USAREC_ORG_HIERARCHY','USAREC','USAREC Org Hierarchy (RSID Tree)',1,'["xlsx"]','["org","hierarchy"]','["rsid","cmd","bde","bn","co","stn","usarec"]','["CMD","BDE","BN","CO","STN"]','[]',NULL,'["unit_rsid"]','org_unit','usarec_org_normalizer',1, datetime('now'), datetime('now'));

            -- Verification SQL (run manually):
            -- SELECT dataset_key, display_name, enabled FROM dataset_registry WHERE dataset_key='USAREC_ORG_HIERARCHY';

            CREATE TABLE IF NOT EXISTS raw_file_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                storage_path TEXT,
                sha256 TEXT,
                bytes INTEGER,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS import_run_v2 (
                run_id TEXT PRIMARY KEY,
                dataset_key TEXT,
                filename TEXT,
                uploaded_by TEXT,
                status TEXT,
                detected_confidence REAL,
                detected_notes TEXT,
                rows_in INTEGER DEFAULT 0,
                rows_loaded INTEGER DEFAULT 0,
                warnings_count INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                started_at TEXT,
                ended_at TEXT
            );

            CREATE TABLE IF NOT EXISTS import_run_error_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                row_num INTEGER,
                column_name TEXT,
                error_code TEXT,
                message TEXT
            );

            -- Mission Feasibility tables
            CREATE TABLE IF NOT EXISTS mission_target (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                fy INTEGER,
                qtr INTEGER,
                month TEXT,
                mission_contracts INTEGER,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS recruiter_strength (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                month TEXT,
                recruiters_assigned INTEGER,
                producers_available INTEGER,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_capacity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                cbsa TEXT,
                zip TEXT,
                market_index REAL,
                urbanicity TEXT,
                snapshot_month TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS agg_mission_feasibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                start_date TEXT,
                end_date TEXT,
                fy INTEGER,
                compare_mode TEXT,
                mission_annual INTEGER,
                recruiters_avg REAL,
                wr_required REAL,
                wr_actual REAL,
                market_capacity_est REAL,
                market_support_index REAL,
                market_burden_ratio REAL,
                recruiters_needed REAL,
                recruiter_delta REAL,
                status TEXT,
                drivers TEXT,
                narrative TEXT,
                recommendations TEXT,
                computed_at TEXT
            );

            -- user-role mapping by role template key (string)
            CREATE TABLE IF NOT EXISTS user_role_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role_key TEXT,
                assigned_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(role_key) REFERENCES role_template(key)
            );

            -- Seed permission registry (idempotent)
            INSERT OR IGNORE INTO permission(key, description, category) VALUES
            ('pages.command_center.view','View Command Center pages','pages'),
            ('pages.market_intel.view','View Market Intelligence pages','pages'),
            ('pages.operations.view','View Operations pages','pages'),
            ('pages.roi.view','View ROI pages','pages'),
            ('pages.planning.view','View Planning pages','pages'),
            ('pages.schools.view','View Schools pages','pages'),
            ('pages.budget.view','View Budget pages','pages'),
            ('pages.datahub.view','View Data Hub pages','pages'),
            ('pages.resources.view','View Resources pages','pages'),
            ('pages.training.view','View Training pages','pages'),
            ('pages.helpdesk.view','View Helpdesk pages','pages'),
            ('pages.system_status.view','View System Status','pages'),
            ('pages.admin.view','View Admin pages','pages'),

            ('dashboards.view','View dashboards','dashboards'),
            ('dashboards.export','Export dashboards','dashboards'),
            ('dashboards.share','Share dashboards','dashboards'),
            ('dashboards.configure','Configure dashboards','dashboards'),

            ('datahub.upload','Upload to Data Hub','datahub'),
            ('datahub.view_registry','View Data Hub registry','datahub'),
            ('datahub.view_runs','View Data Hub runs','datahub'),
            ('datahub.manage_registry','Manage Data Hub registry','datahub'),
            ('datahub.delete_run','Delete Data Hub run','datahub'),

            ('planning.view','View planning','planning'),
            ('planning.edit','Edit planning','planning'),
            ('planning.publish','Publish planning','planning'),
            ('twg.view','TWG view','planning'),
            ('twg.edit','TWG edit','planning'),
            ('twg.close_issue','TWG close issue','planning'),

            ('roi.view','View ROI','roi'),
            ('roi.edit_costs','Edit ROI costs','roi'),
            ('roi.edit_notes','Edit ROI notes','roi'),
            ('roi.edit_attribution_rules','Edit ROI attribution rules','roi'),

            ('schools.view','View schools','schools'),
            ('schools.edit_contacts','Edit school contacts','schools'),
            ('schools.edit_engagements','Edit school engagements','schools'),
            ('schools.edit_notes','Edit school notes','schools'),

            ('helpdesk.submit','Submit helpdesk tickets','helpdesk'),
            ('helpdesk.view_own','View own tickets','helpdesk'),
            ('helpdesk.view_unit','View unit tickets','helpdesk'),
            ('helpdesk.manage','Manage helpdesk','helpdesk'),

            ('admin.users.manage','Manage users (admin)','admin'),
            ('admin.permissions.manage','Manage permissions (admin)','admin'),
            ('admin.thresholds.manage','Manage thresholds (admin)','admin'),
            ('admin.datasets.manage','Manage datasets (admin)','admin'),
            ('admin.audit.view','View audit logs','admin');

            -- Additional canonical keys requested by product RBAC spec
            INSERT OR IGNORE INTO permission(key, description, category) VALUES
            ('app.read','Baseline: read access to the app (alias)','baseline'),
            ('app.export','Baseline: export capability (alias)','baseline'),
            ('datahub.view','View Data Hub (alternate alias)','datahub'),
            ('datahub.upload_raw','Upload raw data to Data Hub (alias)','datahub'),
            ('datahub.manage_registry','Manage Data Hub registry (alias)','datahub');

            -- Also insert canonical uppercase permission keys for frontend/backend mapping
            INSERT OR IGNORE INTO permission(key, description, category) VALUES
            ('DASHBOARDS_READ','Read dashboards (alias for dashboards.view)','dashboards'),
            ('EXPORT_DATA','Export dashboards/data (alias for dashboards.export)','dashboards'),
            ('DATAHUB_READ','Read Data Hub (alias for datahub.view_registry)','datahub'),
            ('DATAHUB_UPLOAD','Upload to Data Hub (alias for datahub.upload)','datahub'),
            ('ROI_READ','Read ROI data (alias for roi.view)','roi'),
            ('ROI_EDIT','Edit ROI data (alias for roi.edit_costs)','roi'),
            ('PLANNING_READ','Read planning (alias for planning.view)','planning'),
            ('PLANNING_EDIT','Edit planning (alias for planning.edit)','planning'),
            ('TWG_READ','Read TWG (alias for twg.view)','planning'),
            ('TWG_EDIT','Edit TWG (alias for twg.edit)','planning'),
            ('SCHOOLS_READ','Read schools (alias for schools.view)','schools'),
            ('SCHOOLS_EDIT','Edit schools (alias for schools.edit_contacts)','schools'),
            ('BUDGET_READ','Read budgets (alias for budget.view)','budget'),
            ('BUDGET_EDIT','Edit budgets (alias for budget.write)','budget'),
            ('HELPDESK_READ','Read helpdesk (alias for helpdesk.view_unit)','helpdesk'),
            ('HELPDESK_CREATE_TICKET','Create helpdesk ticket (alias for helpdesk.submit)','helpdesk'),
            ('HELPDESK_ADMIN','Manage helpdesk (alias for helpdesk.manage)','helpdesk'),
            ('ADMIN_READ','Read admin (alias for admin.users.manage)','admin'),
            ('ADMIN_MANAGE_USERS','Manage users (alias for admin.users.manage)','admin'),
            ('ADMIN_MANAGE_ROLES','Manage roles (alias for admin.permissions.manage)','admin'),
            ('ADMIN_AUDIT_READ','Read audit logs (alias for admin.audit.view)','admin');

            -- Seed role templates (idempotent)
            INSERT OR IGNORE INTO role_template(key, name, description) VALUES
            ('ADMIN','Administrator','Full system administrator'),
            ('TECH','Technical','Technical operator with write access'),
            ('COMMAND','Command','Command-level user with read access'),
            ('READONLY','Read Only','Read-only user'),
            ('420T_FULL','420T Full','Full 420T non-admin access (exports + uploads)'),
            ('COMMAND_READONLY','Command Readonly','Command-level readonly (view + export)'),
            ('STAFF_PLANNER','Staff Planner','Planning and Events editors (planning.events.assets edit)'),
            ('STAFF_ANALYST','Staff Analyst','Analytics focused: view + export'),
            ('USER','User','Baseline user: read + export');

            -- Invite tokens for onboarding flow
            CREATE TABLE IF NOT EXISTS invite_token (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                email TEXT,
                created_by TEXT,
                created_at TEXT,
                used_at TEXT,
                expires_at TEXT
            );

            -- Export job tables
            CREATE TABLE IF NOT EXISTS export_job (
                id TEXT PRIMARY KEY,
                requested_by INTEGER,
                status TEXT,
                source_page TEXT,
                dashboard_key TEXT,
                widget_key TEXT,
                query_key TEXT,
                scope_json TEXT,
                filters_json TEXT,
                render_json TEXT,
                format_json TEXT,
                error_summary TEXT,
                created_at TEXT,
                started_at TEXT,
                ended_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS export_file (
                id TEXT PRIMARY KEY,
                export_id TEXT,
                kind TEXT,
                format TEXT,
                filename TEXT,
                storage_path TEXT,
                size_bytes INTEGER,
                created_at TEXT,
                FOREIGN KEY(export_id) REFERENCES export_job(id)
            );

            CREATE TABLE IF NOT EXISTS export_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                export_id TEXT,
                event TEXT,
                message TEXT,
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

            -- Operations Market Intelligence tables (Phase 13)
            CREATE TABLE IF NOT EXISTS market_zip_metrics (
                id TEXT PRIMARY KEY,
                as_of_date TEXT,
                component TEXT,
                echelon_type TEXT,
                unit_value TEXT,
                station_rsid TEXT,
                zip TEXT,
                zip_category TEXT,
                cbsa_code TEXT,
                dma_name TEXT,
                army_potential INTEGER,
                dod_potential INTEGER,
                dod_wtd_avg INTEGER,
                army_share_of_potential REAL,
                contracts_ga INTEGER,
                contracts_sa INTEGER,
                contracts_vol INTEGER,
                potential_remaining INTEGER,
                p2p_band TEXT,
                p2p_value REAL,
                ingested_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_cbsa_metrics (
                id TEXT PRIMARY KEY,
                as_of_date TEXT,
                component TEXT,
                echelon_type TEXT,
                unit_value TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                plot_parameter TEXT,
                segment_code TEXT,
                total_population INTEGER,
                total_potential INTEGER,
                potential_remaining INTEGER,
                contracts_total INTEGER,
                army_share_of_potential REAL,
                p2p_band TEXT,
                p2p_value REAL,
                ingested_at TEXT NOT NULL
            );

            -- School recruiting canonical tables
            CREATE TABLE IF NOT EXISTS schools (
                id TEXT PRIMARY KEY,
                school_name TEXT,
                school_type TEXT,
                district TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                latitude REAL,
                longitude REAL,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_accounts (
                id TEXT PRIMARY KEY,
                school_id TEXT,
                assigned_station_rsid TEXT,
                assigned_company_prefix TEXT,
                assigned_battalion_prefix TEXT,
                assigned_brigade_prefix TEXT,
                last_contacted_at TEXT,
                status TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_contacts (
                id TEXT PRIMARY KEY,
                school_id TEXT,
                contact_name TEXT,
                contact_role TEXT,
                email TEXT,
                phone TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_activities (
                id TEXT PRIMARY KEY,
                school_id TEXT,
                station_rsid TEXT,
                activity_type TEXT,
                activity_date TEXT,
                outcome TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_milestones (
                id TEXT PRIMARY KEY,
                school_id TEXT,
                milestone_type TEXT,
                milestone_date TEXT,
                linked_event_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_program_leads (
                id TEXT PRIMARY KEY,
                lead_id TEXT,
                school_id TEXT,
                source_tag TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_demographics (
                id TEXT PRIMARY KEY,
                as_of_date TEXT,
                component TEXT,
                echelon_type TEXT,
                unit_value TEXT,
                geo_level TEXT,
                geo_value TEXT,
                race_ethnicity TEXT,
                gender TEXT,
                fqma_population INTEGER,
                youth_population INTEGER,
                enlistments INTEGER,
                p2p_value REAL,
                ingested_at TEXT NOT NULL
            );
            -- Data Hub canonical tables and ROI facts
            CREATE TABLE IF NOT EXISTS data_upload (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_key TEXT,
                source_system TEXT,
                filename TEXT,
                file_hash TEXT,
                uploaded_by TEXT,
                uploaded_at TEXT,
                status TEXT DEFAULT 'received',
                row_count INTEGER DEFAULT 0,
                error_json TEXT
            );

            CREATE TABLE IF NOT EXISTS lead_journey_fact (
                lead_id TEXT PRIMARY KEY,
                person_key TEXT,
                unit_rsid TEXT,
                source_type TEXT,
                source_detail TEXT,
                event_id TEXT,
                mac_id TEXT,
                lead_created_dt TEXT,
                contact_made_dt TEXT,
                appointment_dt TEXT,
                applicant_dt TEXT,
                contract_dt TEXT,
                contract_flag INTEGER DEFAULT 0,
                contract_type TEXT,
                mos TEXT,
                afqt_tier TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS event_fact (
                event_id TEXT PRIMARY KEY,
                unit_rsid TEXT,
                event_name TEXT,
                event_type TEXT,
                start_dt TEXT,
                end_dt TEXT,
                location TEXT,
                mac_id TEXT,
                requested_macs INTEGER,
                assigned_macs INTEGER,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS spend_fact (
                spend_id TEXT PRIMARY KEY,
                unit_rsid TEXT,
                event_id TEXT,
                spend_type TEXT,
                amount REAL,
                spend_dt TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS roi_thresholds (
                metric_key TEXT PRIMARY KEY,
                value REAL
            );

            -- Seed default thresholds if missing (idempotent)
            INSERT OR IGNORE INTO roi_thresholds(metric_key, value) VALUES ('cpl_target', 100.0);
            INSERT OR IGNORE INTO roi_thresholds(metric_key, value) VALUES ('cpc_target', 2500.0);
            CREATE TABLE IF NOT EXISTS geo_target_zones (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                zone_type TEXT,
                echelon_type TEXT,
                unit_value TEXT,
                component TEXT,
                status TEXT,
                geometry_json TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS geo_target_zone_members (
                id TEXT PRIMARY KEY,
                zone_id TEXT NOT NULL,
                member_type TEXT,
                member_value TEXT,
                created_at TEXT NOT NULL
            );

            -- Additional Market Intelligence fact and dimension tables (Phase 13A)
            CREATE TABLE IF NOT EXISTS market_sama_zip_fact (
                id TEXT PRIMARY KEY,
                as_of_date TEXT,
                fy INTEGER,
                qtr TEXT,
                month INTEGER,
                component TEXT,
                echelon_type TEXT,
                unit_value TEXT,
                rsid_prefix TEXT,
                station_rsid TEXT,
                zip_code TEXT,
                zip_category TEXT,
                targeted INTEGER DEFAULT 0,
                army_potential INTEGER,
                dod_potential INTEGER,
                dod_wtd_avg REAL,
                army_share_of_potential REAL,
                army_ga_ach INTEGER,
                army_sa_ach INTEGER,
                army_vol_ach INTEGER,
                contracts INTEGER,
                potential_remaining INTEGER,
                p2p REAL,
                created_at TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_cbsa_fact (
                id TEXT PRIMARY KEY,
                as_of_date TEXT,
                fy INTEGER,
                qtr TEXT,
                month INTEGER,
                component TEXT,
                echelon_type TEXT,
                unit_value TEXT,
                rsid_prefix TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                dma_name TEXT,
                plot_parameter TEXT,
                value REAL,
                p2p REAL,
                market_category TEXT,
                created_at TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_demographics_fact (
                id TEXT PRIMARY KEY,
                as_of_date TEXT,
                fy INTEGER,
                component TEXT,
                geo_type TEXT,
                geo_id TEXT,
                race_ethnicity TEXT,
                gender TEXT,
                population_type TEXT,
                population_value REAL,
                production_value REAL,
                p2p REAL,
                created_at TEXT,
                ingested_at TEXT
            );
            -- New Phase: Operations fact tables for Market Intelligence, Schools, CEP, Geo campaigns
            CREATE TABLE IF NOT EXISTS market_zip_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                month INTEGER,
                rsid_prefix TEXT,
                zip5 TEXT,
                cbsa_code TEXT,
                market_category TEXT,
                youth_pop INTEGER,
                fqma INTEGER,
                army_accessions INTEGER,
                army_share REAL,
                potential_remaining INTEGER,
                p2p REAL,
                must_keep INTEGER DEFAULT 0,
                must_win INTEGER DEFAULT 0,
                market_of_opportunity INTEGER DEFAULT 0,
                supplemental_market INTEGER DEFAULT 0,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_cbsa_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                youth_pop INTEGER,
                fqma INTEGER,
                army_accessions INTEGER,
                army_share REAL,
                potential_remaining INTEGER,
                p2p REAL,
                market_category_rollup TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                school_id TEXT,
                school_name TEXT,
                school_type TEXT,
                enrollment INTEGER,
                fqma_est INTEGER,
                access_level TEXT,
                last_visit_at TEXT,
                visits_ytd INTEGER,
                engagements_ytd INTEGER,
                leads_ytd INTEGER,
                contracts_ytd INTEGER,
                ingested_at TEXT
            );

            -- Canonical schools and supporting tables for School Recruiting feature
            CREATE TABLE IF NOT EXISTS schools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                school_type TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                cbsa_code TEXT,
                enrollment INTEGER,
                created_at TEXT,
                updated_at TEXT,
                record_status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS school_zone_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id TEXT NOT NULL,
                zone_id TEXT NOT NULL,
                created_at TEXT,
                UNIQUE(school_id, zone_id)
            );

            CREATE TABLE IF NOT EXISTS school_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id TEXT NOT NULL,
                name TEXT,
                role TEXT,
                email TEXT,
                phone TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS school_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id TEXT NOT NULL,
                milestone_type TEXT,
                milestone_date TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS cep_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                school_id TEXT,
                asvab_tests INTEGER,
                asvab_high_score INTEGER,
                cep_events INTEGER,
                cep_participants INTEGER,
                leads_from_cep INTEGER,
                contracts_from_cep INTEGER,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS geo_campaign_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                campaign_id TEXT,
                campaign_name TEXT,
                geo_type TEXT,
                area_label TEXT,
                spend REAL,
                impressions INTEGER,
                engagements INTEGER,
                activations INTEGER,
                leads INTEGER,
                contracts INTEGER,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_geotarget_zone (
                id TEXT PRIMARY KEY,
                name TEXT,
                zone_type TEXT,
                rsid_prefix TEXT,
                component TEXT,
                market_category TEXT,
                targeted INTEGER DEFAULT 0,
                geojson TEXT,
                zip_list TEXT,
                cbsa_list TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_category_rule (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                rule_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            -- Phase 13: Market Intelligence operational tables (idempotent)
            CREATE TABLE IF NOT EXISTS market_target_list (
                id TEXT PRIMARY KEY,
                fy INTEGER NOT NULL,
                qtr TEXT NOT NULL,
                rsid_prefix TEXT NOT NULL,
                target_type TEXT NOT NULL,
                zip5 TEXT,
                cbsa_code TEXT,
                rationale TEXT,
                created_at TEXT NOT NULL
            );

            -- Market Intelligence dataset registry and import templates (Phase 14)
            CREATE TABLE IF NOT EXISTS mi_dataset_registry (
                dataset_key TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                table_name TEXT NOT NULL,
                required_columns_json TEXT NOT NULL,
                optional_columns_json TEXT NOT NULL,
                last_seen_at TEXT
            );

            CREATE TABLE IF NOT EXISTS mi_import_template (
                template_key TEXT PRIMARY KEY,
                dataset_key TEXT NOT NULL,
                description TEXT,
                columns_json TEXT NOT NULL,
                mapping_hints_json TEXT NOT NULL,
                validation_rules_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            -- Regulatory references registry (static doctrine/regulations)
            CREATE TABLE IF NOT EXISTS regulatory_references (
                id TEXT PRIMARY KEY,
                code TEXT,
                title TEXT,
                description TEXT,
                category TEXT,
                authority_level TEXT,
                created_at TEXT
            );

            -- Regulatory traceability and module registry (Phase 17)
            CREATE TABLE IF NOT EXISTS regulatory_traceability (
                id TEXT PRIMARY KEY,
                reference_id TEXT NOT NULL,
                module_key TEXT NOT NULL,
                page_route TEXT,
                metric_key TEXT,
                decision_supported TEXT,
                tor_enclosure TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS module_registry (
                id TEXT PRIMARY KEY,
                module_key TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                owner_role TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Seed regulatory references (INSERT OR IGNORE to be idempotent)
            INSERT OR IGNORE INTO regulatory_references (id, code, title, description, category, authority_level, created_at) VALUES
                ('um-3-0','UM 3-0','Unified Manual 3-0','Doctrine reference: Operations','Operations','Manual', datetime('now')),
                ('um-3-29','UM 3-29','Unified Manual 3-29','Doctrine reference: Recruiting and retention','Operations','Manual', datetime('now')),
                ('um-3-30','UM 3-30','Unified Manual 3-30','Doctrine reference','Operations','Manual', datetime('now')),
                ('um-3-31','UM 3-31','Unified Manual 3-31','Doctrine reference','Operations','Manual', datetime('now')),
                ('um-3-32','UM 3-32','Unified Manual 3-32','Doctrine reference','Operations','Manual', datetime('now')),
                ('ur-601-73','UR 601-73','Unit Reference 601-73','Personnel processing regs','Processing','Regulation', datetime('now')),
                ('ur-601-210','UR 601-210','Unit Reference 601-210','Personnel assignment regs','Processing','Regulation', datetime('now')),
                ('ur-601-106','UR 601-106','Unit Reference 601-106','Personnel procedures','Processing','Regulation', datetime('now')),
                ('ur-10-1','UR 10-1','Unit Reference 10-1','Logistics and sustainment','Operations','Regulation', datetime('now')),
                ('ur-27-4','UR 27-4','Unit Reference 27-4','Training and readiness','Training','Regulation', datetime('now')),
                ('ur-350-1','UR 350-1','Unit Reference 350-1','Training doctrine','Training','Regulation', datetime('now')),
                ('ur-350-13','UR 350-13','Unit Reference 350-13','Field training guidance','Training','Regulation', datetime('now')),
                ('utp-3-10-2','UTP 3-10.2','Unit Training Publication 3-10.2','Tactical training publication','Training','Publication', datetime('now')),
                ('420t-tor-2026','420T TOR 2026','420T Terms of Reference 2026','420T program Terms of Reference 2026','Governance','Directive', datetime('now'));

            -- Seed module_registry entries if empty
            INSERT OR IGNORE INTO module_registry (id, module_key, display_name, owner_role, description, created_at, updated_at) VALUES
                ('m-op-mi','operations.market_intel','Market Intelligence Engine','420T','Market intelligence rollups and targets', datetime('now'), datetime('now')),
                ('m-op-target','operations.targeting','Targeting Board','420T','Targeting and prioritization workflows', datetime('now'), datetime('now')),
                ('m-school-prog','school.program','School Recruiting Program','USAREC','School recruiting program rollups', datetime('now'), datetime('now')),
                ('m-cmd-420t','command.420t','420T Command Center','420T','Command center workspace', datetime('now'), datetime('now')),
                ('m-cmd-mdmp','command.mdmp','MDMP Workspace','420T','MDMP planning workspace', datetime('now'), datetime('now')),
                ('m-tac-events','tactical.events_roi','Event ROI','Operations','Event ROI analysis', datetime('now'), datetime('now')),
                ('m-tac-marketing','tactical.marketing','Marketing Performance','Operations','Marketing performance and attribution', datetime('now'), datetime('now')),
                ('m-tac-funnel','tactical.funnel','Funnel Analysis','Operations','Funnel and pipeline metrics', datetime('now'), datetime('now')),
                ('m-budget-res','budget.resource_management','Budget & Resource Management','Finance','Budget and resource management', datetime('now'), datetime('now')),
                ('m-proc-health','processing.health','Processing Health','Operations','Processing and ingestion health', datetime('now'), datetime('now')),
                ('m-train-res','training.resources','Training & Resources','Training','Training resources and modules', datetime('now'), datetime('now')),
                ('m-sys-gov','system.governance','System Governance','Governance','System governance and policy', datetime('now'), datetime('now'));

            -- Foundation MI + School tables (Phase 16)
            CREATE TABLE IF NOT EXISTS mi_zip_fact (
                id TEXT PRIMARY KEY,
                fy TEXT,
                qtr TEXT,
                component TEXT,
                rsid_prefix TEXT,
                zip5 TEXT,
                station_name TEXT,
                market_category TEXT,
                army_potential REAL,
                dod_potential REAL,
                army_share_of_potential REAL,
                potential_remaining REAL,
                contracts_ga INTEGER,
                contracts_sa INTEGER,
                contracts_vol INTEGER,
                p2p REAL,
                as_of_date TEXT,
                ingested_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mi_cbsa_fact (
                id TEXT PRIMARY KEY,
                fy TEXT,
                qtr TEXT,
                component TEXT,
                rsid_prefix TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                market_category TEXT,
                army_potential REAL,
                dod_potential REAL,
                army_share_of_potential REAL,
                potential_remaining REAL,
                contracts_ga INTEGER,
                contracts_sa INTEGER,
                contracts_vol INTEGER,
                p2p REAL,
                as_of_date TEXT,
                ingested_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mi_mission_category_ref (
                id TEXT PRIMARY KEY,
                mission_category TEXT,
                education_tier TEXT,
                pct_gt_enlistments REAL,
                pct_enlistments REAL,
                ingested_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mi_enlistments_bde (
                id TEXT PRIMARY KEY,
                bde TEXT,
                enlistments INTEGER,
                fy TEXT,
                as_of_date TEXT,
                ingested_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mi_enlistments_bn (
                id TEXT PRIMARY KEY,
                battalion_name TEXT,
                rsid_prefix TEXT,
                enlistments INTEGER,
                fy TEXT,
                as_of_date TEXT,
                ingested_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS school_program_fact (
                id TEXT PRIMARY KEY,
                bde TEXT,
                bn TEXT,
                co TEXT,
                rsid_prefix TEXT,
                population INTEGER,
                available INTEGER,
                attempted_students INTEGER,
                attempted_students_pct REAL,
                contacted_students INTEGER,
                contacted_students_pct REAL,
                fy TEXT,
                qtr TEXT,
                as_of_date TEXT,
                ingested_at TEXT NOT NULL
            );

            -- Documents storage registry (for uploaded manuals, regulations, datasets)
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                content_type TEXT,
                size INTEGER,
                uploaded_by TEXT,
                uploaded_at TEXT NOT NULL,
                description TEXT,
                tags TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);

            -- Ensure registry has operational fields (add columns if missing)
            -- mi_dataset_registry earlier schema may differ; add loaded/row_count/last_ingested_at/notes if missing
            BEGIN;
            CREATE TEMP TABLE IF NOT EXISTS __mi_registry_cols(colname TEXT);
            INSERT INTO __mi_registry_cols
            SELECT name FROM pragma_table_info('mi_dataset_registry');
            -- Add columns conditionally by attempting to add if not present
            -- Use dynamic SQL: check count of column rows
            COMMIT;

            -- Phonetics module tables (Phase 15C)
            CREATE TABLE IF NOT EXISTS phonetic_map (
                id TEXT PRIMARY KEY,
                term TEXT NOT NULL,
                phonetic TEXT NOT NULL,
                type TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS phonetic_dataset_registry (
                dataset_key TEXT PRIMARY KEY,
                as_of TEXT,
                row_count INTEGER DEFAULT 0,
                last_loaded_at TEXT,
                status TEXT
            );

            -- Home feed tables for awareness portal (Phase 15C)
            CREATE TABLE IF NOT EXISTS home_flash_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                source TEXT,
                effective_date TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT
            );

            CREATE TABLE IF NOT EXISTS home_messages (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT
            );

            CREATE TABLE IF NOT EXISTS home_recognition (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                person_name TEXT,
                unit TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT
            );

            CREATE TABLE IF NOT EXISTS home_upcoming (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT,
                event_date TEXT,
                tag TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT
            );

            CREATE TABLE IF NOT EXISTS home_reference_rails (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                target TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_taxonomy (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS geo_planning_container (
                id TEXT PRIMARY KEY,
                fy INTEGER NOT NULL,
                qtr TEXT NOT NULL,
                rsid_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                geo_type TEXT NOT NULL,
                area_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            -- Ensure required MI columns exist for compatibility with Phase-13 APIs.
            -- Add missing columns to market_zip_fact if they do not exist.
            PRAGMA foreign_keys=OFF;
            -- Collect existing columns and add any missing ones.
            -- Note: SQLite does not support ALTER COLUMN; we only add missing columns.
            -- market_zip_fact expected additional columns (if missing):
            -- youth_pop_17_24, fqma, market_potential, army_share_pct,
            -- contracts_total, leads_total, activations_total
            BEGIN;
            CREATE TEMP TABLE IF NOT EXISTS __tbl_info_tmp(colname TEXT);
            INSERT INTO __tbl_info_tmp
            SELECT name FROM pragma_table_info('market_zip_fact');
            -- Add columns only if missing
            SELECT 1;
            COMMIT;
            

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

            -- Mapping templates saved by the import UI (used by import map/commit flow)
            CREATE TABLE IF NOT EXISTS import_mapping_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_domain TEXT,
                mapping_json TEXT,
                created_by TEXT,
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
                loe_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                target_value REAL,
                warn_threshold REAL,
                fail_threshold REAL,
                reported_at TEXT,
                ingested_at TEXT,
                current_value REAL,
                status TEXT,
                rationale TEXT,
                last_evaluated_at TEXT,
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
        # Seed minimal demo data for Mission Feasibility (idempotent)
        try:
            try:
                cur.execute("SELECT COUNT(1) as c FROM mission_target WHERE unit_rsid=? AND fy=?", ('USAREC', 2025))
                r = cur.fetchone()
                c = 0
                try:
                    # sqlite3.Row may return mapping-like rows
                    c = int(r['c'])
                except Exception:
                    try:
                        c = int(r[0])
                    except Exception:
                        c = 0
                if c == 0:
                    now = datetime.utcnow().isoformat()
                    # Insert an annual mission target for demo
                    cur.execute('INSERT INTO mission_target (unit_rsid, fy, qtr, month, mission_contracts, created_at) VALUES (?,?,?,?,?,?)', ('USAREC', 2025, None, None, 1200, now))
                    # Populate a 12-month recruiter strength history (simple demo values)
                    months = [f"2024-{m:02d}-01" for m in range(1,13)]
                    for m in months:
                        cur.execute('INSERT INTO recruiter_strength (unit_rsid, month, recruiters_assigned, producers_available, created_at) VALUES (?,?,?,?,?)', ('USAREC', m, 50, 45, now))
                    # Add a simple market capacity estimate row
                    cur.execute('INSERT INTO market_capacity (unit_rsid, cbsa, zip, market_index, urbanicity, snapshot_month, created_at) VALUES (?,?,?,?,?,?,?)', ('USAREC', None, None, 1000.0, 'mixed', '2024-01-01', now))
                    # Add a handful of demo contracts to lead_journey_fact to allow WR_actual computation
                    for i in range(1,51):
                        lead_id = f"demo-usarec-lead-{i}"
                        contract_dt = f"2024-{((i-1)%12)+1:02d}-15"
                        try:
                            cur.execute('INSERT OR IGNORE INTO lead_journey_fact (lead_id, person_key, unit_rsid, contract_flag, contract_dt, created_at) VALUES (?,?,?,?,?,?)', (lead_id, f"person-{i}", 'USAREC', 1, contract_dt, now))
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass
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

        # Seed role_template_permission defaults based on the permission registry
        try:
            # ensure role_template rows exist (created earlier via INSERT OR IGNORE)
            cur.execute("SELECT key FROM role_template")
            existing_roles = [r[0] for r in cur.fetchall()]
            # load permission keys
            cur.execute('SELECT key FROM permission')
            perms = [r[0] for r in cur.fetchall()]
            now = datetime.utcnow().isoformat()
            # ADMIN: grant all known permissions
            if 'ADMIN' in existing_roles:
                for p in perms:
                    try:
                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('ADMIN', p))
                        # Also insert any canonical/alias permission keys that reference this dotted key
                        try:
                            cur.execute('SELECT key FROM permission WHERE description LIKE ?', (f"%{p}%",))
                            for ar in cur.fetchall():
                                ak = ar[0]
                                try:
                                    cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('ADMIN', ak))
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    except Exception:
                        pass
            # READONLY: dashboards.view/export only
            readonly_perms = ['dashboards.view', 'dashboards.export']
            if 'READONLY' in existing_roles:
                for p in readonly_perms:
                    if p in perms:
                        try:
                            cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('READONLY', p))
                            try:
                                cur.execute('SELECT key FROM permission WHERE description LIKE ?', (f"%{p}%",))
                                for ar in cur.fetchall():
                                    ak = ar[0]
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('READONLY', ak))
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        except Exception:
                            pass
            # COMMAND: read-only across core features
            command_perms = ['dashboards.view', 'dashboards.export', 'planning.view', 'roi.view', 'events.view', 'schools.view', 'budget.view']
            if 'COMMAND' in existing_roles:
                for p in command_perms:
                    if p in perms:
                        try:
                            cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('COMMAND', p))
                            try:
                                cur.execute('SELECT key FROM permission WHERE description LIKE ?', (f"%{p}%",))
                                for ar in cur.fetchall():
                                    ak = ar[0]
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('COMMAND', ak))
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        except Exception:
                            pass
            # TECH: broader write privileges (no admin.manage_users)
            tech_perms = ['dashboards.view','dashboards.export','planning.view','planning.edit','roi.view','roi.edit_costs','events.view','events.write','schools.view','schools.edit_contacts','budget.view','budget.write','datahub.upload']
            if 'TECH' in existing_roles:
                for p in tech_perms:
                    if p in perms:
                        try:
                            cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('TECH', p))
                            try:
                                cur.execute('SELECT key FROM permission WHERE description LIKE ?', (f"%{p}%",))
                                for ar in cur.fetchall():
                                    ak = ar[0]
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('TECH', ak))
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        except Exception:
                            pass
            # Seed new role templates per product RBAC specification
            # 420T_FULL: all non-admin permissions + datahub.upload
                        if '420T_FULL' in existing_roles:
                            for p in perms:
                                # skip admin.* permissions
                                if p.startswith('admin.'):
                                    continue
                                try:
                                    cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('420T_FULL', p))
                                except Exception:
                                    pass

                        # COMMAND_READONLY: view + export only (core pages + dashboards)
                        if 'COMMAND_READONLY' in existing_roles:
                            cr_perms = ['dashboards.view', 'dashboards.export', 'pages.command_center.view', 'pages.market_intel.view', 'pages.operations.view', 'pages.roi.view']
                            for p in cr_perms:
                                if p in perms:
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('COMMAND_READONLY', p))
                                    except Exception:
                                        pass

                        # STAFF_PLANNER: planning/events/assets edit; rest view
                        if 'STAFF_PLANNER' in existing_roles:
                            sp_perms = ['planning.view','planning.edit','events.view','events.edit','asset_catalog','asset_inventory']
                            for p in sp_perms:
                                # map friendly alias names where applicable
                                if p in perms:
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('STAFF_PLANNER', p))
                                    except Exception:
                                        pass

                        # STAFF_ANALYST: analytics/roi view; can export
                        if 'STAFF_ANALYST' in existing_roles:
                            sa_perms = ['dashboards.view','dashboards.export','roi.view','pages.market_intel.view','pages.operations.view']
                            for p in sa_perms:
                                if p in perms:
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('STAFF_ANALYST', p))
                                    except Exception:
                                        pass

                        # USER: baseline read + export only
                        if 'USER' in existing_roles:
                            user_perms = ['dashboards.view','dashboards.export','pages.system_status.view']
                            for p in user_perms:
                                if p in perms:
                                    try:
                                        cur.execute('INSERT OR IGNORE INTO role_template_permission(role_key, permission_key, granted) VALUES (?,?,1)', ('USER', p))
                                    except Exception:
                                        pass
            conn.commit()
        except Exception:
            try:
                conn.rollback()
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

        # Ensure burden_inputs contains reporting_date column (idempotent)
        try:
            bcols = table_columns('burden_inputs')
            if 'reporting_date' not in bcols:
                try:
                    cur.execute("ALTER TABLE burden_inputs ADD COLUMN reporting_date TEXT")
                except Exception:
                    # Fallback: perform safe table rewrite to add missing column
                    try:
                        cur.executescript('''
                        PRAGMA foreign_keys=OFF;
                        CREATE TABLE IF NOT EXISTS burden_inputs_new (
                            id TEXT PRIMARY KEY,
                            scope_type TEXT,
                            scope_value TEXT,
                            mission_requirement TEXT,
                            recruiter_strength INTEGER,
                            reporting_date TEXT,
                            created_at TEXT
                        );
                        INSERT INTO burden_inputs_new (id, scope_type, scope_value, mission_requirement, recruiter_strength, reporting_date, created_at)
                            SELECT id, scope_type, scope_value, mission_requirement, recruiter_strength, NULL AS reporting_date, created_at FROM burden_inputs;
                        DROP TABLE IF EXISTS burden_inputs;
                        ALTER TABLE burden_inputs_new RENAME TO burden_inputs;
                        PRAGMA foreign_keys=ON;
                        ''')
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

        # Ensure MI fact tables have the expected columns for Phase-13 APIs.
        try:
            try:
                cur.execute("PRAGMA table_info('market_zip_fact')")
                existing = [c[1] for c in cur.fetchall()]
            except Exception:
                existing = []
            zip_expected = {
                'youth_pop_17_24': 'INTEGER',
                'fqma': 'INTEGER',
                'market_potential': 'INTEGER',
                'army_share_pct': 'REAL',
                'contracts_total': 'INTEGER',
                'leads_total': 'INTEGER',
                'activations_total': 'INTEGER'
            }
            for col, typ in zip_expected.items():
                if col not in existing:
                    try:
                        cur.execute(f"ALTER TABLE market_zip_fact ADD COLUMN {col} {typ}")
                    except Exception:
                        pass

            try:
                cur.execute("PRAGMA table_info('market_cbsa_fact')")
                existing_cbsa = [c[1] for c in cur.fetchall()]
            except Exception:
                existing_cbsa = []
            cbsa_expected = {
                'youth_pop_17_24': 'INTEGER',
                'market_potential': 'INTEGER',
                'army_share_pct': 'REAL',
                'contracts_total': 'INTEGER',
                'p2p': 'REAL'
            }
            for col, typ in cbsa_expected.items():
                if col not in existing_cbsa:
                    try:
                        cur.execute(f"ALTER TABLE market_cbsa_fact ADD COLUMN {col} {typ}")
                    except Exception:
                        pass
        except Exception:
            pass

        # Ensure canonical Phase-13 tables exist (market_zip_fact, market_cbsa_fact canonical schema, market_targets, market_rules)
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS market_zip_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                zip TEXT,
                cbsa_code TEXT,
                market_category TEXT,
                fqma INTEGER,
                population_17_24 INTEGER,
                contracts INTEGER,
                army_share REAL,
                potential_remaining INTEGER,
                p2p REAL,
                demo_json TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_cbsa_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                market_category TEXT,
                fqma INTEGER,
                contracts INTEGER,
                army_share REAL,
                potential_remaining INTEGER,
                demo_json TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_targets (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                target_type TEXT,
                zip TEXT,
                cbsa_code TEXT,
                rationale TEXT,
                score REAL,
                created_at TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS market_rules (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );
            ''')
            conn.commit()
        except Exception:
            pass

        # Canonical Market Intelligence tables (Phase 15): mi_*
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS mi_zip_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                zip5 TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                station_name TEXT,
                component TEXT,
                market_category TEXT,
                army_potential INTEGER,
                dod_potential INTEGER,
                army_share_of_potential REAL,
                potential_remaining INTEGER,
                contracts_ga INTEGER,
                contracts_sa INTEGER,
                contracts_vol INTEGER,
                p2p REAL,
                as_of_date TEXT,
                created_at TEXT,
                updated_at TEXT,
                demo_json TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS mi_cbsa_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                station_name TEXT,
                component TEXT,
                market_category TEXT,
                army_potential INTEGER,
                dod_potential INTEGER,
                army_share_of_potential REAL,
                potential_remaining INTEGER,
                contracts_ga INTEGER,
                contracts_sa INTEGER,
                contracts_vol INTEGER,
                p2p REAL,
                as_of_date TEXT,
                created_at TEXT,
                updated_at TEXT,
                demo_json TEXT,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS mi_demo_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                component TEXT,
                geo_type TEXT,
                geo_id TEXT,
                attribute_key TEXT,
                attribute_value REAL,
                ingested_at TEXT
            );

            CREATE TABLE IF NOT EXISTS mi_school_fact (
                id TEXT PRIMARY KEY,
                fy INTEGER,
                qtr TEXT,
                rsid_prefix TEXT,
                school_id TEXT,
                school_name TEXT,
                enrollment INTEGER,
                fqma_est INTEGER,
                ingested_at TEXT
            );
            ''')
            conn.commit()
        except Exception:
            pass

        # Ensure `event` table contains school-related and planning columns used by new APIs.
        try:
            cur.execute("PRAGMA table_info('event')")
            existing_event_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            existing_event_cols = []
        event_expected = {
            'event_category': 'TEXT',
            'school_id': 'TEXT',
            'planned_cost': 'REAL',
            'funding_line': 'TEXT',
            'planned_outcomes_json': 'TEXT',
            'actual_outcomes_json': 'TEXT'
        }
        try:
            for col, typ in event_expected.items():
                if col not in existing_event_cols:
                    try:
                        cur.execute(f"ALTER TABLE event ADD COLUMN {col} {typ}")
                    except Exception:
                        pass
        except Exception:
            pass

            conn.commit()
            # Minor migration: add processed columns to imported_rows if they don't exist
            try:
                cur.execute("PRAGMA table_info(imported_rows)")
                cols = [c[1] for c in cur.fetchall()]
                if 'processed' not in cols:
                    try:
                        cur.execute("ALTER TABLE imported_rows ADD COLUMN processed INTEGER DEFAULT 0")
                    except Exception:
                        pass
                if 'processed_at' not in cols:
                    try:
                        cur.execute("ALTER TABLE imported_rows ADD COLUMN processed_at TEXT")
                    except Exception:
                        pass
                if 'processed_by' not in cols:
                    try:
                        cur.execute("ALTER TABLE imported_rows ADD COLUMN processed_by TEXT")
                    except Exception:
                        pass
                conn.commit()
            except Exception:
                pass
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

        # PHASE-12: Ensure system tables for change proposals and api errors
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS change_proposals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                rationale TEXT,
                impact_area TEXT,
                risk_level TEXT,
                status TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                reviewed_by TEXT,
                reviewed_at TEXT,
                decision_note TEXT
            );

            CREATE TABLE IF NOT EXISTS api_error_log (
                id TEXT PRIMARY KEY,
                endpoint TEXT,
                message TEXT,
                created_at TEXT NOT NULL
            );
            ''')
        except Exception:
            pass
        # Ensure maintenance_flags table exists (idempotent)
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS maintenance_flags (
                id TEXT PRIMARY KEY,
                active INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                starts_at TEXT,
                ends_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            ''')
        except Exception:
            pass

        # Backfill/compat: ensure import_job_v3 contains completion and summary fields
        try:
            cols = table_columns('import_job_v3')
            if 'completed_at' not in cols:
                try:
                    cur.execute("ALTER TABLE import_job_v3 ADD COLUMN completed_at TEXT")
                except Exception:
                    pass
            if 'summary_json' not in cols:
                try:
                    cur.execute("ALTER TABLE import_job_v3 ADD COLUMN summary_json TEXT")
                except Exception:
                    pass
        except Exception:
            pass

        # Create plural audit_logs table (SQLAlchemy models expect this name)
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                scope_type TEXT,
                scope_value TEXT,
                before_json TEXT,
                after_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            ''')
        except Exception:
            pass

        # Minimal security/role mapping tables to support RBAC extensions
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS security_roles (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS user_roles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                created_at TEXT,
                UNIQUE(user_id, role_id)
            );
            ''')
        except Exception:
            pass

        # USAREC completion gate records
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS usarec_completion (
                id TEXT PRIMARY KEY,
                scope_type TEXT,
                scope_value TEXT,
                completed_by TEXT,
                completed_at TEXT,
                details_json TEXT,
                created_at TEXT
            );
            ''')
        except Exception:
            pass

        # Ensure change_proposals contains the columns expected by new APIs.
        # Use PRAGMA table_info and ALTER TABLE ADD COLUMN where safe.
        try:
            cur.execute("PRAGMA table_info(change_proposals)")
            existing = [r[1] for r in cur.fetchall()]
            needed = {
                'proposed_changes_json': 'TEXT NOT NULL',
                'submitted_by': 'TEXT',
                'reviewed_by': 'TEXT',
                'reviewed_at': 'TEXT',
                'created_at': 'TEXT NOT NULL',
                'updated_at': 'TEXT NOT NULL',
                'status': 'TEXT NOT NULL'
            }
            for col, coldef in needed.items():
                if col not in existing:
                    try:
                        cur.execute(f"ALTER TABLE change_proposals ADD COLUMN {col} {coldef}")
                    except Exception:
                        # best-effort; non-fatal if ALTER fails
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
    # Ensure SQLAlchemy engine used by the application points at the same DB
    # path so tests and API handlers operate on the same database file.
    try:
        from services.api.app import database as _database
        try:
            os.environ['DATABASE_URL'] = f"sqlite:///{get_db_path()}"
            if hasattr(_database, 'reload_engine_if_needed'):
                _database.reload_engine_if_needed()
        except Exception:
            pass
    except Exception:
        pass
    
    # Run mission-feasibility migrations to align legacy DB schemas to canonical columns
    try:
        conn = connect()
        try:
            _migrate_mission_feasibility_schema(conn)
        except Exception:
            pass
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        # mission_target
        cur.execute('INSERT OR IGNORE INTO mission_target(unit_rsid,fy,annual_contract_mission,created_at) VALUES(?,?,?,?)', ('USAREC', 2026, 60000, now))
        cur.execute('UPDATE mission_target SET annual_contract_mission = ?, updated_at = ? WHERE unit_rsid = ? AND fy = ?', (60000, now, 'USAREC', 2026))

        # recruiter_strength: 12 months for FY2026
        for m in range(1, 13):
            month = f'2026-{m:02d}'
            cur.execute('INSERT OR REPLACE INTO recruiter_strength(unit_rsid, month, recruiters_assigned, recruiters_available, created_at, updated_at) VALUES(?,?,?,?,?,?)', ('USAREC', month, 50, 45, now, now))

        # market_capacity
        cur.execute('INSERT OR IGNORE INTO market_capacity(unit_rsid, fy, baseline_contract_capacity, market_burden_factor, created_at) VALUES(?,?,?,?,?)', ('USAREC', 2026, 58000, 1.05, now))
        cur.execute('UPDATE market_capacity SET baseline_contract_capacity = ?, market_burden_factor = ?, updated_at = ? WHERE unit_rsid = ? AND fy = ?', (58000, 1.05, now, 'USAREC', 2026))

        conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

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

            # Attempt to acquire an advisory file lock on the DB path
            try:
                dbpath = get_db_path()
                lock_path = f"{dbpath}.lock"
                start = time.time()
                acquired = False
                # Use a threading lock to avoid hammering the same process
                with _advisory_lock_lock:
                    try:
                        fd = open(lock_path, 'w+')
                        # try non-blocking first, then loop until timeout
                        while time.time() - start < max(1.0, delay * 5):
                            try:
                                fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                                acquired = True
                                break
                            except BlockingIOError:
                                sleep(0.05)
                        if not acquired:
                            try:
                                fd.close()
                            except Exception:
                                pass
                        else:
                            # release immediately; presence of lock reduces contention
                            try:
                                fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
                            except Exception:
                                pass
                            try:
                                fd.close()
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            sleep(delay)
            delay = min(delay * 2, 2.0)


# Backwards compatibility: expose names expected elsewhere in the codebase
def table_has_cols(table_name: str, cols) -> bool:
    """Return True if the given table exists and contains all columns in `cols`.

    `cols` may be a string for a single column or an iterable of column names.
    This is a lightweight helper used by routers that need runtime
    compatibility checks against the sqlite schema.
    """
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        existing = [r[1] for r in cur.fetchall()]
        if isinstance(cols, str):
            return cols in existing
        # treat cols as iterable of names
        for c in cols:
            if c not in existing:
                return False
        return True
    except Exception:
        return False


# Backwards compatibility: expose names expected elsewhere in the codebase
__all__ = ["get_db_path", "connect", "get_db_conn", "init_schema", "init_db", "execute_with_retry", "table_has_cols"]
