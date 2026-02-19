from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional
from ..db import connect
import datetime, json
from .. import db
from .rbac import require_roles

# Allowed tables for maintenance purge (whitelist to prevent SQL injection)
ALLOWED_MAINTENANCE_TABLES = [
    'fact_production', 'fact_marketing', 'fact_funnel',
    'projects', 'tasks', 'meeting_minutes', 'action_items', 'doc_library',
    'marketing_activities', 'budgets'
]

def record_run(conn, schedule_id, run_type, params, result, started_at, finished_at):
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO maintenance_runs(schedule_id, run_type, params_json, result_json, started_at, finished_at) VALUES (?,?,?,?,?,?)', (
            schedule_id, run_type, json.dumps(params or {}), json.dumps(result or {}), started_at, finished_at
        ))
        conn.commit()
    except Exception:
        pass

router = APIRouter()


def now_iso():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


@router.post('/admin/deduplicate', summary='Deduplicate business-key records')
def deduplicate_business_keys(current_user: dict = Depends(require_roles('usarec_admin'))):
    """Find duplicate business-key records and archive older ones.

    This is a safe, idempotent operation: it will mark duplicates as archived
    (set `record_status='archived'` and `archived_at`) while keeping one
    active row per business key.
    """
    conn = connect()
    try:
        cur = conn.cursor()
        results = {}
        # fact_production: keep newest by created_at for (org_unit_id,date_key,metric_key)
        cur.execute("SELECT org_unit_id, date_key, metric_key, COUNT(*) as c FROM fact_production GROUP BY org_unit_id, date_key, metric_key HAVING c>1")
        dupes = cur.fetchall()
        prod_archived = 0
        for d in dupes:
            org, datek, metric = d[0], d[1], d[2]
            cur.execute('SELECT id, created_at FROM fact_production WHERE org_unit_id=? AND date_key=? AND metric_key=? ORDER BY datetime(created_at) DESC', (org, datek, metric))
            rows = cur.fetchall()
            keep = rows[0][0] if rows else None
            for r in rows[1:]:
                try:
                    cur.execute('UPDATE fact_production SET record_status=?, archived_at=? WHERE id=?', ('archived', now_iso(), r[0]))
                    prod_archived += 1
                except Exception:
                    pass
        results['fact_production_archived'] = prod_archived

        # fact_marketing: dedupe by org/date/campaign/channel
        cur.execute("SELECT org_unit_id, date_key, campaign, channel, COUNT(*) as c FROM fact_marketing GROUP BY org_unit_id, date_key, campaign, channel HAVING c>1")
        dup2 = cur.fetchall()
        mark_archived = 0
        for d in dup2:
            org, datek, camp, chan = d[0], d[1], d[2], d[3]
            cur.execute('SELECT id, created_at FROM fact_marketing WHERE org_unit_id=? AND date_key=? AND campaign=? AND channel=? ORDER BY datetime(created_at) DESC', (org, datek, camp, chan))
            rows = cur.fetchall()
            for r in rows[1:]:
                try:
                    cur.execute('UPDATE fact_marketing SET record_status=?, archived_at=? WHERE id=?', ('archived', now_iso(), r[0]))
                    mark_archived += 1
                except Exception:
                    pass
        results['fact_marketing_archived'] = mark_archived

        # projects: dedupe by title + owner (keep newest)
        cur.execute("SELECT title, owner, COUNT(*) as c FROM projects GROUP BY title, owner HAVING c>1")
        dup_p = cur.fetchall()
        proj_archived = 0
        for d in dup_p:
            title, owner = d[0], d[1]
            cur.execute('SELECT project_id, created_at FROM projects WHERE title=? AND owner=? ORDER BY datetime(created_at) DESC', (title, owner))
            rows = cur.fetchall()
            for r in rows[1:]:
                try:
                    cur.execute("UPDATE projects SET record_status=?, archived_at=? WHERE project_id=?", ('archived', now_iso(), r[0]))
                    proj_archived += 1
                except Exception:
                    pass
        results['projects_archived'] = proj_archived

        # tasks: dedupe by project_id + title + owner
        cur.execute("SELECT project_id, title, owner, COUNT(*) as c FROM tasks GROUP BY project_id, title, owner HAVING c>1")
        dup_t = cur.fetchall()
        task_archived = 0
        for d in dup_t:
            projid, title, owner = d[0], d[1], d[2]
            cur.execute('SELECT task_id, created_at FROM tasks WHERE project_id=? AND title=? AND owner=? ORDER BY datetime(created_at) DESC', (projid, title, owner))
            rows = cur.fetchall()
            for r in rows[1:]:
                try:
                    cur.execute("UPDATE tasks SET record_status=?, archived_at=? WHERE task_id=?", ('archived', now_iso(), r[0]))
                    task_archived += 1
                except Exception:
                    pass
        results['tasks_archived'] = task_archived

        # meeting_minutes: dedupe by project_id + occurred_at
        cur.execute("SELECT project_id, occurred_at, COUNT(*) as c FROM meeting_minutes GROUP BY project_id, occurred_at HAVING c>1")
        dup_m = cur.fetchall()
        mm_archived = 0
        for d in dup_m:
            projid, occ = d[0], d[1]
            cur.execute('SELECT minute_id, created_at FROM meeting_minutes WHERE project_id=? AND occurred_at=? ORDER BY datetime(created_at) DESC', (projid, occ))
            rows = cur.fetchall()
            for r in rows[1:]:
                try:
                    cur.execute("UPDATE meeting_minutes SET record_status=?, archived_at=? WHERE minute_id=?", ('archived', now_iso(), r[0]))
                    mm_archived += 1
                except Exception:
                    pass
        results['meeting_minutes_archived'] = mm_archived

        # action_items: dedupe by minute_id + title + owner
        cur.execute("SELECT minute_id, title, owner, COUNT(*) as c FROM action_items GROUP BY minute_id, title, owner HAVING c>1")
        dup_a = cur.fetchall()
        ai_archived = 0
        for d in dup_a:
            minute_id, title, owner = d[0], d[1], d[2]
            cur.execute('SELECT action_id, created_at FROM action_items WHERE minute_id=? AND title=? AND owner=? ORDER BY datetime(created_at) DESC', (minute_id, title, owner))
            rows = cur.fetchall()
            for r in rows[1:]:
                try:
                    cur.execute("UPDATE action_items SET record_status=?, archived_at=? WHERE action_id=?", ('archived', now_iso(), r[0]))
                    ai_archived += 1
                except Exception:
                    pass
        results['action_items_archived'] = ai_archived

        # doc_library: dedupe by url (or title+uploaded_at)
        cur.execute("SELECT url, COUNT(*) as c FROM doc_library WHERE url IS NOT NULL GROUP BY url HAVING c>1")
        dup_d = cur.fetchall()
        doc_archived = 0
        for d in dup_d:
            url = d[0]
            cur.execute('SELECT doc_id, uploaded_at FROM doc_library WHERE url=? ORDER BY datetime(uploaded_at) DESC', (url,))
            rows = cur.fetchall()
            for r in rows[1:]:
                try:
                    cur.execute("UPDATE doc_library SET record_status=?, archived_at=? WHERE doc_id=?", ('archived', now_iso(), r[0]))
                    doc_archived += 1
                except Exception:
                    pass
        results['doc_library_archived'] = doc_archived

        conn.commit()
        return {'status':'ok', 'results': results}
    finally:
        conn.close()


@router.get('/admin/maintenance_runs')
def list_runs(limit: int = 100):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM maintenance_runs ORDER BY started_at DESC LIMIT ?', (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@router.get('/admin/schedules')
def list_schedules(current_user: dict = Depends(require_roles('usarec_admin'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM maintenance_schedules ORDER BY id')
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@router.post('/admin/schedules')
def create_schedule(payload: dict = Body(...), current_user: dict = Depends(require_roles('usarec_admin'))):
    name = payload.get('name')
    interval = int(payload.get('interval_minutes') or 0)
    enabled = 1 if payload.get('enabled') else 0
    params = json.dumps(payload.get('params') or {})
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO maintenance_schedules(name, enabled, interval_minutes, params_json, created_at) VALUES (?,?,?,?,?)', (name, enabled, interval, params, now_iso()))
        conn.commit()
        return {'status':'ok', 'id': cur.lastrowid}
    finally:
        conn.close()


@router.put('/admin/schedules/{schedule_id}')
def update_schedule(schedule_id: int, payload: dict = Body(...), current_user: dict = Depends(require_roles('usarec_admin'))):
    conn = connect()
    try:
        cur = conn.cursor()
        if 'enabled' in payload:
            cur.execute('UPDATE maintenance_schedules SET enabled=? WHERE id=?', (1 if payload.get('enabled') else 0, schedule_id))
        if 'interval_minutes' in payload:
            cur.execute('UPDATE maintenance_schedules SET interval_minutes=? WHERE id=?', (int(payload.get('interval_minutes') or 0), schedule_id))
        if 'params' in payload:
            cur.execute('UPDATE maintenance_schedules SET params_json=? WHERE id=?', (json.dumps(payload.get('params') or {}), schedule_id))
        conn.commit()
        return {'status':'ok'}
    finally:
        conn.close()


@router.post('/admin/schedules/{schedule_id}/trigger')
def trigger_schedule(schedule_id: int, current_user: dict = Depends(require_roles('usarec_admin'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, params_json FROM maintenance_schedules WHERE id=? LIMIT 1', (schedule_id,))
        s = cur.fetchone()
        if not s:
            raise HTTPException(status_code=404, detail='schedule not found')
        # Support both mapping-like rows (sqlite3.Row / dict) and simple tuples
        try:
            if hasattr(s, 'keys'):
                raw_params = s.get('params_json')
            else:
                # selected columns: id, name, params_json -> index 2
                raw_params = s[2] if len(s) > 2 else None
            params = json.loads(raw_params or '{}')
        except Exception:
            params = {}
        # run tasks defined in params or default dedupe
        tasks = params.get('tasks') or ['dedupe']
        results = []
        for t in tasks:
            started = now_iso()
            try:
                if t == 'dedupe':
                    r = deduplicate_business_keys()
                elif t == 'purge':
                    # normalize params when called programmatically (Body() defaults may appear)
                    pdays = None
                    ptables = None
                    if isinstance(params, dict):
                        pdays = params.get('days')
                        ptables = params.get('tables')
                    try:
                        r = purge_archived(pdays, ptables)
                    except TypeError:
                        # fallback to calling without args
                        r = purge_archived()
                else:
                    r = {'error':'unknown task'}
            except Exception as e:
                r = {'error': str(e)}
            finished = now_iso()
            try:
                record_run(conn, schedule_id, t, params, r, started, finished)
            except Exception:
                pass
            results.append({'task': t, 'result': r})
        return {'status':'ok', 'results': results}
    finally:
        conn.close()


@router.post('/admin/purge_archived', summary='Purge archived records older than X days')
def purge_archived(days: Optional[int] = Body(90), tables: Optional[list] = Body(None), dry_run: Optional[bool] = Body(False), current_user: dict = Depends(require_roles('usarec_admin'))):
    """Purge archived records older than `days`. Defaults to 90.

    `tables` can be provided to restrict which tables to purge; otherwise a
    conservative default set is used.
    """
    # normalize days when called programmatically (avoid FastAPI Body sentinel objects)
    try:
        days_val = int(days) if days is not None and not hasattr(days, '__iter__') else int(days)
    except Exception:
        try:
            days_val = int(days) if days is not None else 90
        except Exception:
            days_val = 90
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=int(days_val or 90))
    cutoff_iso = cutoff.strftime('%Y-%m-%dT%H:%M:%SZ')
    conn = connect()
    try:
        cur = conn.cursor()
        # normalize tables: if tables is a list use it; otherwise use conservative default
        default_tables = ['fact_production', 'fact_marketing', 'fact_funnel', 'projects', 'tasks', 'meeting_minutes', 'action_items', 'doc_library', 'marketing_activities', 'budgets']
        if isinstance(tables, (list, tuple)):
            # validate each requested table against an allowlist to avoid SQL injection
            to_check = [t for t in tables if t in default_tables]
            invalid = [t for t in tables if t not in default_tables]
            if invalid:
                # report invalid table names but continue with valid ones
                for t in invalid:
                    results[t] = 'invalid_table'
        else:
            to_check = default_tables
        results = {}
        now_iso = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        for t in to_check:
            try:
                # purge rows where either archived_at < cutoff OR keep_until < now
                # keep_until is optional per-row override; it should be ISO timestamp
                # For safety, support dry-run mode which only reports counts and does not delete.
                if dry_run:
                    # condition A count
                    cur.execute(f"SELECT COUNT(*) as c FROM {t} WHERE record_status='archived' AND archived_at IS NOT NULL AND archived_at<?", (cutoff_iso,))
                    deleted_a = cur.fetchone()[0]
                    # condition B count
                    try:
                        cur.execute(f"SELECT COUNT(*) as c FROM {t} WHERE keep_until IS NOT NULL AND keep_until<?", (now_iso,))
                        deleted_b = cur.fetchone()[0]
                    except Exception:
                        deleted_b = 0
                    results[t] = {'archived_deleted': int(deleted_a), 'keep_until_deleted': int(deleted_b), 'dry_run': True}
                else:
                    # perform deletes
                    cur.execute(f"DELETE FROM {t} WHERE record_status='archived' AND archived_at IS NOT NULL AND archived_at<?", (cutoff_iso,))
                    deleted_a = cur.rowcount
                    try:
                        cur.execute(f"DELETE FROM {t} WHERE keep_until IS NOT NULL AND keep_until<?", (now_iso,))
                        deleted_b = cur.rowcount
                    except Exception:
                        deleted_b = 0
                    results[t] = {'archived_deleted': deleted_a, 'keep_until_deleted': deleted_b}
            except Exception:
                results[t] = 'error'
        conn.commit()
        return {'status':'ok', 'purged': results, 'cutoff': cutoff_iso}
    finally:
        conn.close()


if __name__ == '__main__':
    # simple CLI invocation
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--purge-days', type=int, default=None)
    p.add_argument('--dedupe', action='store_true')
    args = p.parse_args()
    if args.dedupe:
        print(deduplicate_business_keys())
    elif args.purge_days is not None:
        print(purge_archived(args.purge_days))
    else:
        print('no-op')
