import threading
import time
import json
import datetime
from .db import connect

_stop = threading.Event()


def now_iso():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def load_schedules(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, name, enabled, interval_minutes, last_run_at, next_run_at, params_json FROM maintenance_schedules WHERE enabled=1')
    return [dict(r) for r in cur.fetchall()]


def log_run(conn, schedule_id, run_type, params, result, started_at, finished_at):
    cur = conn.cursor()
    cur.execute('INSERT INTO maintenance_runs(schedule_id, run_type, params_json, result_json, started_at, finished_at) VALUES (?,?,?,?,?,?)', (
        schedule_id, run_type, json.dumps(params or {}), json.dumps(result or {}), started_at, finished_at
    ))
    conn.commit()


def run_task_by_name(conn, task_name, params=None):
    # simple router to maintenance functions
    from .routers import maintenance as mrouter
    started = now_iso()
    try:
        if task_name == 'dedupe':
            res = mrouter.deduplicate_business_keys()
        elif task_name == 'purge':
            res = mrouter.purge_archived(params.get('days') if params else None)
        else:
            res = {'error': 'unknown task'}
    except Exception as e:
        res = {'error': str(e)}
    finished = now_iso()
    return res, started, finished


def scheduler_loop(poll_interval=60):
    # Poll schedules and execute due tasks. Runs until _stop is set.
    while not _stop.is_set():
        try:
            conn = connect()
            schedules = load_schedules(conn)
            now = datetime.datetime.utcnow()
            for s in schedules:
                try:
                    interval = int(s.get('interval_minutes') or 0)
                    last = s.get('last_run_at')
                    next_run = None
                    if last:
                        try:
                            lr = datetime.datetime.strptime(last, '%Y-%m-%dT%H:%M:%SZ')
                            next_run = lr + datetime.timedelta(minutes=interval)
                        except Exception:
                            next_run = None
                    if next_run is None:
                        # never run — schedule now
                        due = True
                    else:
                        due = now >= next_run
                    if due:
                        # execute default tasks: dedupe then purge if configured
                        params = json.loads(s.get('params_json') or '{}')
                        # task sequence
                        tasks = params.get('tasks') or ['dedupe']
                        for t in tasks:
                            result, started, finished = run_task_by_name(conn, t, params)
                            log_run(conn, s['id'], t, params, result, started, finished)
                        # update last_run_at and next_run_at
                        cur = conn.cursor()
                        cur.execute('UPDATE maintenance_schedules SET last_run_at=?, next_run_at=? WHERE id=?', (now_iso(), (now + datetime.timedelta(minutes=interval)).strftime('%Y-%m-%dT%H:%M:%SZ') if interval else None, s['id']))
                        conn.commit()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
        _stop.wait(poll_interval)


_thread = None


def start_scheduler(poll_interval=60):
    global _thread
    if _thread and _thread.is_alive():
        return
    _thread = threading.Thread(target=scheduler_loop, args=(poll_interval,), daemon=True)
    _thread.start()


def stop_scheduler():
    _stop.set()
    global _thread
    if _thread:
        _thread.join(timeout=5)
