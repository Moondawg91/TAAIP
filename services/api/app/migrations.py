"""Safe, idempotent runtime migrations for local/dev SQLite.
This module performs non-destructive schema adjustments on startup.
"""
from typing import Any
import json
import sqlite3
import time


def _table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    try:
        cur.execute(f"PRAGMA table_info({table});")
        cols = [r[1] for r in cur.fetchall()]
        return column in cols
    except Exception:
        return False


def apply_migrations(conn: sqlite3.Connection):
    cur = conn.cursor()
    # Ensure dataset_registry
    if not _table_exists(cur, 'dataset_registry'):
        cur.executescript('''
        CREATE TABLE dataset_registry (
            dataset_key TEXT PRIMARY KEY,
            display_name TEXT,
            source_system TEXT,
            file_types TEXT,
            required_columns TEXT,
            optional_columns TEXT,
            detection_keywords TEXT,
            target_tables TEXT,
            enabled INTEGER DEFAULT 1,
            version INTEGER DEFAULT 1
        );
        ''')

    # Ensure import_run_v2
    if not _table_exists(cur, 'import_run_v2'):
        cur.executescript('''
        CREATE TABLE import_run_v2 (
            run_id TEXT PRIMARY KEY,
            dataset_key TEXT,
            filename TEXT,
            uploaded_by TEXT,
            status TEXT,
            detected_confidence REAL,
            rows_in INTEGER,
            rows_loaded INTEGER,
            warnings INTEGER DEFAULT 0,
            error_summary TEXT,
            storage_path TEXT,
            created_at TEXT,
            started_at TEXT,
            ended_at TEXT,
            scope_unit_rsid TEXT,
            scope_fy INTEGER,
            scope_qtr INTEGER
        );
        ''')

    # Ensure import_run_error_v2
    if not _table_exists(cur, 'import_run_error_v2'):
        cur.executescript('''
        CREATE TABLE import_run_error_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            row_num INTEGER,
            column_name TEXT,
            error_code TEXT,
            message TEXT
        );
        ''')

    # Ensure raw_file_storage table
    if not _table_exists(cur, 'raw_file_storage'):
        cur.executescript('''
        CREATE TABLE raw_file_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            original_filename TEXT,
            storage_path TEXT,
            content_type TEXT,
            size_bytes INTEGER,
            created_at TEXT
        );
        ''')

    # Ensure canonical fact tables (minimal schemas)
    if not _table_exists(cur, 'fact_enlistments'):
        cur.executescript('''
        CREATE TABLE fact_enlistments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_rsid TEXT,
            echelon TEXT,
            period_date TEXT,
            contracts INTEGER,
            source_system TEXT,
            dataset_key TEXT
        );
        ''')

    if not _table_exists(cur, 'fact_enlistments_bn'):
        cur.executescript('''
        CREATE TABLE fact_enlistments_bn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            as_of_date TEXT,
            bn_name TEXT,
            rsid TEXT,
            enlistments INTEGER,
            source_run_id TEXT,
            source_system TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_fact_enlistments_bn_rsid ON fact_enlistments_bn(rsid);
        CREATE INDEX IF NOT EXISTS idx_fact_enlistments_bn_as_of ON fact_enlistments_bn(as_of_date);
        ''')

    if not _table_exists(cur, 'dim_school_contact'):
        cur.executescript('''
        CREATE TABLE dim_school_contact (
            school_id TEXT PRIMARY KEY,
            school_name TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            unit_rsid TEXT,
            source_system TEXT
        );
        ''')

    if not _table_exists(cur, 'fact_alrl_outcomes'):
        cur.executescript('''
        CREATE TABLE fact_alrl_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_rsid TEXT,
            zip TEXT,
            category TEXT,
            value REAL,
            period_date TEXT,
            source_system TEXT
        );
        ''')

    if not _table_exists(cur, 'fact_emm_events'):
        cur.executescript('''
        CREATE TABLE fact_emm_events (
            event_id TEXT PRIMARY KEY,
            unit_rsid TEXT,
            event_dt TEXT,
            event_type TEXT,
            mecs_requested INTEGER,
            mecs_assigned INTEGER,
            cost_event REAL,
            cost_marketing REAL,
            cost_travel REAL,
            leads INTEGER,
            contacts INTEGER,
            contracts INTEGER,
            source_system TEXT
        );
        ''')

    if not _table_exists(cur, 'fact_emm_activity'):
        cur.executescript('''
        CREATE TABLE fact_emm_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id TEXT,
            rsid TEXT,
            unit_name TEXT,
            mac TEXT,
            title TEXT,
            where_text TEXT,
            activity_type TEXT,
            activity_status TEXT,
            fy INTEGER,
            begin_date TEXT,
            end_date TEXT,
            aar_due TEXT,
            controlling_account TEXT,
            source_run_id TEXT,
            source_system TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_fact_emm_activity_rsid ON fact_emm_activity(rsid);
        CREATE INDEX IF NOT EXISTS idx_fact_emm_activity_fy ON fact_emm_activity(fy);
        CREATE INDEX IF NOT EXISTS idx_fact_emm_activity_begin ON fact_emm_activity(begin_date);
        ''')

    if not _table_exists(cur, 'fact_lead_journey'):
        cur.executescript('''
        CREATE TABLE fact_lead_journey (
            lead_id TEXT PRIMARY KEY,
            unit_rsid TEXT,
            created_dt TEXT,
            first_contact_dt TEXT,
            contract_dt TEXT,
            stage TEXT,
            source_channel TEXT,
            contract_flag INTEGER,
            hq_flag INTEGER,
            source_system TEXT
        );
        ''')

    # Ensure 'fy' columns exist where referenced historically
    # mission_target, market_capacity, recruiter_strength handled earlier elsewhere
    for tbl in ('mission_target', 'market_capacity', 'recruiter_strength'):
        if _table_exists(cur, tbl) and not _column_exists(cur, tbl, 'fy'):
            try:
                cur.execute(f"ALTER TABLE {tbl} ADD COLUMN fy INTEGER;")
            except Exception:
                pass

    # mission_feasibility_narrative table to store generated narratives
    if not _table_exists(cur, 'mission_feasibility_narrative'):
        cur.executescript('''
        CREATE TABLE mission_feasibility_narrative (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_rsid TEXT,
            fy INTEGER,
            payload TEXT,
            created_at TEXT
        );
        ''')

    conn.commit()


def seed_default_registry(conn: sqlite3.Connection):
    """Insert a few helpful registry rows for local development if missing."""
    cur = conn.cursor()
    sample = [
        {
            'dataset_key': 'USAREC_G2_ENLISTMENTS_BY_BN',
            'display_name': 'USAREC G2 Enlistments by BN',
            'source_system': 'USAREC_G2',
            'file_types': json.dumps(['xlsx','csv']),
            'required_columns': json.dumps(['LU_BATTALION_NAME','Enlistments','rsid']),
            'optional_columns': json.dumps([]),
            'detection_keywords': json.dumps(['lu_battalion_name','battalion','bn','enlist','enlistments','measure table']),
            'target_tables': json.dumps(['fact_enlistments_bn']),
            'enabled': 1,
            'version': 1
        },
        {
            'dataset_key': 'ALRL_DATA',
            'display_name': 'ALRL Outcomes',
            'source_system': 'ALRL',
            'file_types': json.dumps(['xlsx','csv']),
            'required_columns': json.dumps(['zip','category','value','period']),
            'optional_columns': json.dumps([]),
            'detection_keywords': json.dumps(['alrl','outcome']),
            'target_tables': json.dumps(['fact_alrl_outcomes']),
            'enabled': 1,
            'version': 1
        },
        {
            'dataset_key': 'EMM_PORTAL_EVENTS',
            'display_name': 'EMM Portal - Events',
            'source_system': 'EMM',
            'file_types': json.dumps(['xlsx']),
            'required_columns': json.dumps(['Activity ID','MAC','RSID','TITLE','Activity Type','Activity Status','Begin Date','End Date','FY']),
            'optional_columns': json.dumps(['Unit','CONTROLLING_ACCOUNT','Where','Activity Req date','AAR_Due','Who']),
            'detection_keywords': json.dumps(['emm','emm portal','activity id','mac','controlling_account','activity type','activity status','who']),
            'target_tables': json.dumps(['fact_emm_activity']),
            'enabled': 1,
            'version': 1
        }
    ]
    for r in sample:
        cur.execute('SELECT dataset_key FROM dataset_registry WHERE dataset_key=?', (r['dataset_key'],))
        if not cur.fetchone():
            cur.execute('''INSERT INTO dataset_registry (dataset_key, display_name, source_system, file_types, required_columns, optional_columns, detection_keywords, target_tables, enabled, version)
                           VALUES (?,?,?,?,?,?,?,?,?,?)''', (r['dataset_key'], r['display_name'], r['source_system'], r['file_types'], r['required_columns'], r['optional_columns'], r['detection_keywords'], r['target_tables'], r['enabled'], r['version']))
    conn.commit()


def seed_org_tree(conn: sqlite3.Connection):
    """Create minimal dev org units if `org_unit` is empty. Idempotent and best-effort."""
    try:
        cur = conn.cursor()
        # Ensure indexes on org_unit for parent lookup and echelon/type
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_org_unit_parent_id ON org_unit(parent_id);")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_org_unit_parent_rsid ON org_unit(parent_id);")
        except Exception:
            pass
        try:
            # some schemas use 'type' as echelon
            cur.execute("CREATE INDEX IF NOT EXISTS idx_org_unit_echelon ON org_unit(type);")
        except Exception:
            pass

        # If table empty, insert small demo tree
        cur.execute("SELECT 1 FROM org_unit LIMIT 1")
        if cur.fetchone():
            return

        # Insert USAREC root
        try:
            cur.execute("INSERT OR IGNORE INTO org_unit (name, type, rsid, created_at) VALUES (?,?,?,datetime('now'))", ('United States Army Recruiting Command','USAREC','USAREC'))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        # helper to insert child by parent rsid
        def ins(rsid, name, etype, parent_rsid=None):
            try:
                if parent_rsid:
                    # resolve parent id
                    cur.execute('SELECT id FROM org_unit WHERE rsid=? LIMIT 1', (parent_rsid,))
                    prow = cur.fetchone()
                    pid = prow.get('id') if prow else None
                else:
                    pid = None
                cur.execute("INSERT OR IGNORE INTO org_unit (name, type, rsid, parent_id, created_at) VALUES (?,?,?,?,datetime('now'))", (name, etype, rsid, pid))
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

        ins('BDE_DEMO_01', 'Demo Brigade 01', 'BDE', 'USAREC')
        ins('BN_DEMO_01', 'Demo Battalion 01', 'BN', 'BDE_DEMO_01')
        ins('CO_DEMO_01', 'Demo Company 01', 'CO', 'BN_DEMO_01')
        ins('STN_DEMO_01', 'Demo Station 01', 'STATION', 'CO_DEMO_01')
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return


def apply_runtime_migrations(conn: sqlite3.Connection) -> None:
    """Idempotently add missing `fy` columns and backfill from legacy fiscal-year fields.

    This function uses the DB helpers to safely add columns and perform non-destructive
    backfills. It is safe to call repeatedly on startup.
    """
    try:
        # import helpers lazily to avoid cycles during import-time
        from .db import safe_add_column, column_exists
    except Exception:
        # If helpers are not available, best-effort: return silently
        return

    cur = conn.cursor()

    # Map of tables -> list of legacy columns to copy from if present.
    # Order matters: earlier legacy columns have priority when backfilling.
    table_legacy_map = {
        'mission_target': ['fiscal_year', 'year', 'FY', 'fiscalYear'],
        'market_capacity': ['fiscal_year', 'year', 'FY'],
        'recruiter_strength': ['fiscal_year', 'year', 'FY'],
        'fy_budget': ['fiscal_year', 'fiscalyear', 'year'],
        'budget_line_item': ['fiscal_year', 'fiscalyear', 'year'],
        'loe': ['fiscal_year', 'fiscalyear', 'year'],
        'ai_recommendation': ['fiscal_year', 'year'],
        'fact_emm_activity': ['fiscal_year', 'fiscalyear', 'year'],
        'cost_benchmark': ['fiscal_year', 'fiscalyear', 'year']
    }

    # ensure import_run_v2 has scope columns used by upload endpoint
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='import_run_v2'")
        if cur.fetchone():
            # add scope_unit_rsid, scope_fy, scope_qtr if missing
            try:
                safe_add_column(conn, 'import_run_v2', 'scope_unit_rsid', 'TEXT')
            except Exception:
                pass
            try:
                safe_add_column(conn, 'import_run_v2', 'scope_fy', 'INTEGER')
            except Exception:
                pass
            try:
                safe_add_column(conn, 'import_run_v2', 'scope_qtr', 'INTEGER')
            except Exception:
                pass
    except Exception:
        pass

    for tbl, legacy_cols in table_legacy_map.items():
        try:
            # Ensure table exists before operating on it
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
            if not cur.fetchone():
                continue

            # Add canonical 'fy' column if missing
            added = safe_add_column(conn, tbl, 'fy', 'INTEGER')

            # If any legacy column exists, backfill into fy where missing
            for legacy in legacy_cols:
                try:
                    if column_exists(conn, tbl, legacy) and column_exists(conn, tbl, 'fy'):
                        # Use a conservative UPDATE: only set fy where NULL and legacy not NULL
                        cur.execute(f"UPDATE {tbl} SET fy = {legacy} WHERE fy IS NULL AND {legacy} IS NOT NULL")
                        conn.commit()
                        # once backfilled from one legacy col, we can stop for this table
                        break
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    continue
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            continue

    # Final commit to ensure any remaining changes are persisted
    try:
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    # Additional runtime additions: add canonical scope/time columns for EMM and Enlistments BN
    try:
        from .db import safe_add_column, column_exists
        cur = conn.cursor()
        # import_run_v2: add scope_rsm_month
        try:
            safe_add_column(conn, 'import_run_v2', 'scope_rsm_month', 'TEXT')
        except Exception:
            pass

        # fact_enlistments_bn: add unit_rsid, fy, qtr_num, rsm_month
        try:
            safe_add_column(conn, 'fact_enlistments_bn', 'unit_rsid', 'TEXT')
            safe_add_column(conn, 'fact_enlistments_bn', 'fy', 'INTEGER')
            safe_add_column(conn, 'fact_enlistments_bn', 'qtr_num', 'INTEGER')
            safe_add_column(conn, 'fact_enlistments_bn', 'rsm_month', 'TEXT')
            # index
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_enl_bn_unit_fy_qtr_month ON fact_enlistments_bn(unit_rsid, fy, qtr_num, rsm_month)")
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        # fact_emm_activity: add unit_rsid, fy, qtr_num, rsm_month, start_date, end_date
        try:
            safe_add_column(conn, 'fact_emm_activity', 'unit_rsid', 'TEXT')
            safe_add_column(conn, 'fact_emm_activity', 'fy', 'INTEGER')
            safe_add_column(conn, 'fact_emm_activity', 'qtr_num', 'INTEGER')
            safe_add_column(conn, 'fact_emm_activity', 'rsm_month', 'TEXT')
            safe_add_column(conn, 'fact_emm_activity', 'start_date', 'TEXT')
            safe_add_column(conn, 'fact_emm_activity', 'end_date', 'TEXT')
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fact_emm_unit_fy_qtr_month ON fact_emm_activity(unit_rsid, fy, qtr_num, rsm_month)")
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

        # Best-effort backfills using available date columns
        try:
            # import scope helper lazily
            from . import scope as scope_mod
            # backfill fact_emm_activity from begin_date -> fy/qtr/rsm
            if column_exists(conn, 'fact_emm_activity', 'begin_date') and column_exists(conn, 'fact_emm_activity', 'fy'):
                try:
                    rows = cur.execute("SELECT id, begin_date FROM fact_emm_activity WHERE (fy IS NULL OR qtr_num IS NULL OR rsm_month IS NULL) AND begin_date IS NOT NULL").fetchall()
                    for r in rows:
                        bid = r.get('id')
                        bdate = r.get('begin_date')
                        try:
                            dt = None
                            if bdate:
                                dt = datetime.fromisoformat(bdate)
                        except Exception:
                            dt = None
                        if dt:
                            fyv = scope_mod.compute_current_fy(dt.date())
                            qv = scope_mod.compute_current_qtr_num(dt.date())
                            rm = f"{dt.year:04d}-{dt.month:02d}"
                            cur.execute("UPDATE fact_emm_activity SET fy=?, qtr_num=?, rsm_month=? WHERE id=?", (fyv, qv, rm, bid))
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass

            # backfill fact_enlistments_bn from as_of_date -> fy/qtr/rsm
            if column_exists(conn, 'fact_enlistments_bn', 'as_of_date') and column_exists(conn, 'fact_enlistments_bn', 'fy'):
                try:
                    rows = cur.execute("SELECT id, as_of_date FROM fact_enlistments_bn WHERE (fy IS NULL OR qtr_num IS NULL OR rsm_month IS NULL) AND as_of_date IS NOT NULL").fetchall()
                    for r in rows:
                        bid = r.get('id')
                        bdate = r.get('as_of_date')
                        try:
                            dt = None
                            if bdate:
                                dt = datetime.fromisoformat(bdate)
                        except Exception:
                            dt = None
                        if dt:
                            fyv = scope_mod.compute_current_fy(dt.date())
                            qv = scope_mod.compute_current_qtr_num(dt.date())
                            rm = f"{dt.year:04d}-{dt.month:02d}"
                            cur.execute("UPDATE fact_enlistments_bn SET fy=?, qtr_num=?, rsm_month=?, unit_rsid=? WHERE id=?", (fyv, qv, rm, None, bid))
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
        except Exception:
            pass
    except Exception:
        # swallow errors to avoid stopping server startup
        pass

    # Ensure a minimal dev org tree is present (best-effort, idempotent)
    try:
        try:
            seed_org_tree(conn)
        except Exception:
            pass
    except Exception:
        pass

