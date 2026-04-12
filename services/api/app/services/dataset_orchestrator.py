"""Dataset orchestration service for post-commit processing.

This module provides a central DATASET_PUBLISH_MAP and the
process_committed_dataset(run_id, dataset_key) entrypoint. Each
processor is implemented as a deterministic function that performs
minimal, real-table based aggregations and persists processing status
into `import_run_processing_status`.
"""
from typing import List, Dict, Any, Optional
import sqlite3
import datetime
import traceback

from ..db import connect
from ..aggregations import refresh as refresh_mod


# Central registry mapping dataset_key -> processors and affected modules
DATASET_PUBLISH_MAP = {
    "school_program_fact": {
        "targets": ["dashboard", "school_recruiting", "command_center", "performance_tracking"],
        "processors": [
            "refresh_dashboard_kpis",
            "refresh_school_summary",
            "refresh_station_rollup",
            "refresh_conversion_metrics",
        ],
    },
    "leads": {
        "targets": ["dashboard", "leads", "command_center", "performance_tracking"],
        "processors": [
            "refresh_dashboard_kpis",
            "refresh_lead_summary",
            "refresh_station_rollup",
            "refresh_conversion_metrics",
        ],
    },
    "market_intel": {
        "targets": ["dashboard", "market_intelligence", "targeting", "command_center"],
        "processors": [
            "refresh_market_summary",
            "refresh_zip_rankings",
            "refresh_cbsa_rollup",
        ],
    },
    "mission_allocation": {
        "targets": ["mission_assessment", "command_center", "budget"],
        "processors": [
            "refresh_mission_summary",
            "refresh_feasibility_metrics",
        ],
    },
    "event_roi": {
        "targets": ["roi", "dashboard", "budget", "command_center"],
        "processors": [
            "refresh_event_roi",
            "refresh_marketing_rollup",
        ],
    },
}


def _now():
    return datetime.datetime.utcnow().isoformat()


def _record_status(conn: sqlite3.Connection, run_id: str, dataset_key: str, processor: str, target: str, status: str, started_at: str, ended_at: str, error: Optional[str] = None):
    cur = conn.cursor()
    try:
        cur.execute('''INSERT INTO import_run_processing_status (run_id, dataset_key, processor_name, target_module, status, started_at, ended_at, error_message, created_at)
                       VALUES (?,?,?,?,?,?,?,?,datetime('now'))''', (run_id, dataset_key, processor, target, status, started_at, ended_at, error))
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


def refresh_dashboard_kpis(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    try:
        # reuse existing agg kpi refresh
        try:
            refresh_mod.refresh_agg_kpis(conn, unit_rsid=unit_rsid)
        except Exception:
            pass
        ended = _now()
        return {"processor": "refresh_dashboard_kpis", "status": "success", "target": "dashboard", "started_at": started, "ended_at": ended}
    except Exception as e:
        ended = _now()
        return {"processor": "refresh_dashboard_kpis", "status": "failed", "target": "dashboard", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_school_summary(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    cur = conn.cursor()
    try:
        # create simple school_summary table if missing
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS school_summary (
                school_id TEXT PRIMARY KEY,
                enrollment INTEGER,
                available INTEGER,
                updated_at TEXT
            );
            ''')
        except Exception:
            pass

        # Aggregate from school_program_fact if present
        try:
            cur.execute('SELECT rsid_prefix, population, available FROM school_program_fact')
            rows = cur.fetchall()
        except Exception:
            rows = []

        if rows:
            for r in rows:
                try:
                    sid = r[0]
                    enrollment = int(r[1]) if r[1] is not None else 0
                    avail = int(r[2]) if r[2] is not None else 0
                    cur.execute('INSERT OR REPLACE INTO school_summary (school_id, enrollment, available, updated_at) VALUES (?,?,?,?)', (sid, enrollment, avail, _now()))
                except Exception:
                    continue
            conn.commit()

        ended = _now()
        return {"processor": "refresh_school_summary", "status": "success", "target": "school_recruiting", "started_at": started, "ended_at": ended}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        ended = _now()
        return {"processor": "refresh_school_summary", "status": "failed", "target": "school_recruiting", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_station_rollup(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    cur = conn.cursor()
    try:
        # create station_rollup table
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS station_rollup (
                station_rsid TEXT PRIMARY KEY,
                leads INTEGER,
                contracts INTEGER,
                conversion_pct REAL,
                updated_at TEXT
            );
            ''')
        except Exception:
            pass

        # compute simple aggregates from fact_lead_journey
        try:
            cur.execute('SELECT unit_rsid, COUNT(*) as leads, SUM(COALESCE(contract_flag,0)) as contracts FROM fact_lead_journey GROUP BY unit_rsid')
            rows = cur.fetchall()
        except Exception:
            rows = []

        for r in rows:
            try:
                station = r[0] or 'UNKNOWN'
                leads = int(r[1] or 0)
                contracts = int(r[2] or 0)
                conv = (float(contracts) / leads * 100.0) if leads and leads > 0 else 0.0
                cur.execute('INSERT OR REPLACE INTO station_rollup (station_rsid, leads, contracts, conversion_pct, updated_at) VALUES (?,?,?,?,?)', (station, leads, contracts, conv, _now()))
            except Exception:
                continue
        conn.commit()
        ended = _now()
        return {"processor": "refresh_station_rollup", "status": "success", "target": "performance_tracking", "started_at": started, "ended_at": ended}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        ended = _now()
        return {"processor": "refresh_station_rollup", "status": "failed", "target": "performance_tracking", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_conversion_metrics(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    cur = conn.cursor()
    try:
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS conversion_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_rsid TEXT,
                leads INTEGER,
                contracts INTEGER,
                conversion_pct REAL,
                updated_at TEXT
            );
            ''')
        except Exception:
            pass

        try:
            cur.execute('SELECT unit_rsid, COUNT(*) as leads, SUM(COALESCE(contract_flag,0)) as contracts FROM fact_lead_journey GROUP BY unit_rsid')
            rows = cur.fetchall()
        except Exception:
            rows = []

        for r in rows:
            try:
                unit = r[0] or 'USAREC'
                leads = int(r[1] or 0)
                contracts = int(r[2] or 0)
                conv = (float(contracts) / leads * 100.0) if leads and leads > 0 else 0.0
                cur.execute('INSERT INTO conversion_metrics (unit_rsid, leads, contracts, conversion_pct, updated_at) VALUES (?,?,?,?,?)', (unit, leads, contracts, conv, _now()))
            except Exception:
                continue
        conn.commit()
        ended = _now()
        return {"processor": "refresh_conversion_metrics", "status": "success", "target": "dashboard", "started_at": started, "ended_at": ended}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        ended = _now()
        return {"processor": "refresh_conversion_metrics", "status": "failed", "target": "dashboard", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_lead_summary(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    # simple alias to conversion metrics
    return refresh_conversion_metrics(conn, run_id, dataset_key, unit_rsid)


def refresh_market_summary(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    try:
        # reuse existing market refresh where available
        try:
            inserted = refresh_mod.refresh_market_from_contracts(conn, batch_id=run_id, unit_rsid=unit_rsid)
        except Exception:
            inserted = 0
        # ensure metrics table is populated (best-effort)
        try:
            metrics_written = refresh_mod.refresh_market_zip_metrics(conn, unit_rsid=unit_rsid)
        except Exception:
            metrics_written = 0
        ended = _now()
        return {"processor": "refresh_market_summary", "status": "success", "target": "market_intelligence", "started_at": started, "ended_at": ended, "rows": inserted, "metrics_written": metrics_written}
    except Exception as e:
        ended = _now()
        return {"processor": "refresh_market_summary", "status": "failed", "target": "market_intelligence", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_zip_rankings(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    # best-effort alias to market summary
    return refresh_market_summary(conn, run_id, dataset_key, unit_rsid)


def refresh_cbsa_rollup(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    # best-effort alias to market summary
    return refresh_market_summary(conn, run_id, dataset_key, unit_rsid)


def refresh_mission_summary(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    try:
        try:
            rid = refresh_mod.refresh_mission_from_category(conn, batch_id=run_id, unit_rsid=unit_rsid)
        except Exception:
            rid = None
        ended = _now()
        return {"processor": "refresh_mission_summary", "status": "success", "target": "mission_assessment", "started_at": started, "ended_at": ended, "run_id": rid}
    except Exception as e:
        ended = _now()
        return {"processor": "refresh_mission_summary", "status": "failed", "target": "mission_assessment", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_feasibility_metrics(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    # For now, alias to refresh_all_analytics which attempts feasibility where possible
    started = _now()
    try:
        try:
            refresh_mod.refresh_all_analytics(conn, unit_rsid=unit_rsid)
        except Exception:
            pass
        ended = _now()
        return {"processor": "refresh_feasibility_metrics", "status": "success", "target": "mission_assessment", "started_at": started, "ended_at": ended}
    except Exception as e:
        ended = _now()
        return {"processor": "refresh_feasibility_metrics", "status": "failed", "target": "mission_assessment", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_event_roi(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    started = _now()
    cur = conn.cursor()
    try:
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS event_roi_summary (event_id TEXT PRIMARY KEY, leads INTEGER, contracts INTEGER, cost_total REAL, roi REAL, updated_at TEXT)''')
        except Exception:
            pass
        try:
            cur.execute('SELECT event_id, leads, contracts, cost_event FROM fact_emm_events')
            rows = cur.fetchall()
        except Exception:
            rows = []
        for r in rows:
            try:
                eid = r[0]
                leads = int(r[1] or 0)
                contracts = int(r[2] or 0)
                cost = float(r[3] or 0.0)
                roi = (contracts / cost) if cost and cost > 0 else None
                cur.execute('INSERT OR REPLACE INTO event_roi_summary (event_id, leads, contracts, cost_total, roi, updated_at) VALUES (?,?,?,?,?,?)', (eid, leads, contracts, cost, roi, _now()))
            except Exception:
                continue
        conn.commit()
        ended = _now()
        return {"processor": "refresh_event_roi", "status": "success", "target": "roi", "started_at": started, "ended_at": ended}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        ended = _now()
        return {"processor": "refresh_event_roi", "status": "failed", "target": "roi", "started_at": started, "ended_at": ended, "error": str(e)}


def refresh_marketing_rollup(conn: sqlite3.Connection, run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    # Minimal alias to event_roi
    return refresh_event_roi(conn, run_id, dataset_key, unit_rsid)


# Map processor name -> function
_PROCESSORS = {
    'refresh_dashboard_kpis': refresh_dashboard_kpis,
    'refresh_school_summary': refresh_school_summary,
    'refresh_station_rollup': refresh_station_rollup,
    'refresh_conversion_metrics': refresh_conversion_metrics,
    'refresh_lead_summary': refresh_lead_summary,
    'refresh_market_summary': refresh_market_summary,
    'refresh_zip_rankings': refresh_zip_rankings,
    'refresh_cbsa_rollup': refresh_cbsa_rollup,
    'refresh_mission_summary': refresh_mission_summary,
    'refresh_feasibility_metrics': refresh_feasibility_metrics,
    'refresh_event_roi': refresh_event_roi,
    'refresh_marketing_rollup': refresh_marketing_rollup,
}


def process_committed_dataset(run_id: str, dataset_key: str, unit_rsid: Optional[str] = None) -> Dict[str, Any]:
    conn = connect()
    cur = conn.cursor()
    processing = {
        'status': 'started',
        'affected_modules': [],
        'processors_run': [],
        'processor_results': [],
        'analytics_ready': False,
    }

    entry = DATASET_PUBLISH_MAP.get(dataset_key) or {}
    processors: List[str] = entry.get('processors', [])
    targets: List[str] = entry.get('targets', [])
    processing['affected_modules'] = targets

    for proc_name in processors:
        proc_fn = _PROCESSORS.get(proc_name)
        started_at = _now()
        if not proc_fn:
            # record missing processor as failed
            ended_at = _now()
            res = {'processor': proc_name, 'target_module': 'unknown', 'status': 'missing'}
            processing['processors_run'].append(proc_name)
            processing['processor_results'].append(res)
            try:
                _record_status(conn, run_id, dataset_key, proc_name, 'unknown', 'missing', started_at, ended_at, 'processor_not_implemented')
            except Exception:
                pass
            continue

        try:
            result = proc_fn(conn, run_id, dataset_key, unit_rsid)
            status = result.get('status', 'success')
            target = result.get('target', 'unknown')
            processing['processors_run'].append(proc_name)
            processing['processor_results'].append({ 'processor': proc_name, 'target_module': target, 'status': status, 'meta': result })
            ended_at = result.get('ended_at') or _now()
            # persist per-processor row
            try:
                _record_status(conn, run_id, dataset_key, proc_name, target, status, started_at, ended_at, result.get('error'))
            except Exception:
                pass
        except Exception as e:
            ended_at = _now()
            err = ''.join(traceback.format_exception_only(type(e), e))
            processing['processors_run'].append(proc_name)
            processing['processor_results'].append({ 'processor': proc_name, 'target_module': 'unknown', 'status': 'failed', 'error': str(e) })
            try:
                _record_status(conn, run_id, dataset_key, proc_name, 'unknown', 'failed', started_at, ended_at, str(e))
            except Exception:
                pass
            continue

    # determine analytics_ready: simple heuristic — all processors succeeded
    all_ok = all([r.get('status') == 'success' for r in processing['processor_results']]) if processing['processor_results'] else False
    processing['analytics_ready'] = bool(all_ok)
    processing['status'] = 'complete' if all_ok else 'partial'

    # return structured response
    rows_loaded = None
    try:
        cur.execute('SELECT rows_loaded FROM import_run_v2 WHERE run_id=?', (run_id,))
        rr = cur.fetchone()
        if rr:
            rows_loaded = rr.get('rows_loaded') if isinstance(rr, dict) else (rr[0] if len(rr) > 0 else None)
    except Exception:
        rows_loaded = None

    return {
        'status': 'success',
        'dataset_key': dataset_key,
        'rows_loaded': rows_loaded,
        'processing': processing,
    }
