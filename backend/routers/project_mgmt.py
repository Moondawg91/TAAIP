"""
Project Management API Router (MVP)
Provides lightweight project tables, lessons/AARs, scope, budget transactions,
participants, ROI records and a simple EMM mapping table. Includes a migration
endpoint to create necessary tables and basic CRUD endpoints for projects,
lessons and budget transactions with an ROI calculation helper.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import sqlite3
import os
import uuid
import asyncio
import json
from fastapi.responses import StreamingResponse

router = APIRouter()


def get_db():
    # Resolve DB path: prefer environment `DB_FILE`, then common container paths, then local repo path
    db_path = os.environ.get('DB_FILE') or '/app/recruiting.db' or '/root/TAAIP/data/recruiting.db' or '/Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def run_migrations():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript(r"""
    CREATE TABLE IF NOT EXISTS projects_pm (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        start_date TEXT,
        end_date TEXT,
        total_budget REAL DEFAULT 0,
        estimated_benefit REAL DEFAULT 0,
        units TEXT,
        metadata TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS project_lessons (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        created_at TEXT,
        author TEXT,
        lesson TEXT
    );

    CREATE TABLE IF NOT EXISTS project_aars (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        created_at TEXT,
        summary TEXT
    );

    CREATE TABLE IF NOT EXISTS project_scope (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        scope_text TEXT,
        milestones TEXT
    );

    CREATE TABLE IF NOT EXISTS budget_transactions (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        date TEXT,
        type TEXT,
        description TEXT,
        amount REAL,
        category TEXT
    );

    CREATE TABLE IF NOT EXISTS participants (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        person_id TEXT,
        role TEXT,
        unit TEXT,
        attendance INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS roi_records (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        calculated_at TEXT,
        cost_total REAL,
        benefit_est REAL,
        roi REAL
    );

    CREATE TABLE IF NOT EXISTS emm_mappings (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        emm_event_id TEXT,
        raw_payload TEXT
    );
    """)

    conn.commit()
    conn.close()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ''
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_budget: Optional[float] = 0.0
    estimated_benefit: Optional[float] = 0.0
    units: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post('/init_migrations')
def init_migrations():
    try:
        run_migrations()
        return {'status': 'ok', 'message': 'migrations applied'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/projects')
def create_project(payload: ProjectCreate):
    conn = get_db()
    cursor = conn.cursor()
    pid = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO projects_pm (id, name, description, start_date, end_date, total_budget, estimated_benefit, units, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (pid, payload.name, payload.description, payload.start_date, payload.end_date, payload.total_budget, payload.estimated_benefit, payload.units, str(payload.metadata) if payload.metadata else None, created_at)
    )
    conn.commit()
    conn.close()
    return {'status': 'ok', 'project_id': pid}


@router.get('/projects')
def list_projects(limit: int = 100, offset: int = 0):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects_pm ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {'status': 'ok', 'projects': rows}


@router.get('/projects/{project_id}')
def get_project(project_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM projects_pm WHERE id = ?', (project_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='project not found')

    project = dict(row)
    # Aggregate budget transactions
    cursor.execute('SELECT SUM(amount) as total_spent FROM budget_transactions WHERE project_id = ?', (project_id,))
    srow = cursor.fetchone()
    total_spent = srow['total_spent'] if srow and srow['total_spent'] is not None else 0.0

    # Latest ROI
    cursor.execute('SELECT * FROM roi_records WHERE project_id = ? ORDER BY calculated_at DESC LIMIT 1', (project_id,))
    roi_row = cursor.fetchone()
    roi = dict(roi_row) if roi_row else None

    conn.close()
    project['total_spent'] = total_spent
    project['latest_roi'] = roi
    return {'status': 'ok', 'project': project}


@router.post('/projects/{project_id}/budget/transaction')
def add_budget_transaction(project_id: str, type: str, description: str, amount: float, category: Optional[str] = 'other'):
    conn = get_db()
    cursor = conn.cursor()
    # ensure project exists
    cursor.execute('SELECT 1 FROM projects_pm WHERE id = ?', (project_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='project not found')

    tid = str(uuid.uuid4())
    date = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO budget_transactions (id, project_id, date, type, description, amount, category) VALUES (?, ?, ?, ?, ?, ?, ?)', (tid, project_id, date, type, description, amount, category))
    conn.commit()

    # update ROI record (simple calc)
    cursor.execute('SELECT SUM(amount) as cost_total FROM budget_transactions WHERE project_id = ?', (project_id,))
    crow = cursor.fetchone()
    cost_total = crow['cost_total'] if crow and crow['cost_total'] is not None else 0.0

    # fetch estimated benefit from project
    cursor.execute('SELECT estimated_benefit FROM projects_pm WHERE id = ?', (project_id,))
    prow = cursor.fetchone()
    benefit_est = prow['estimated_benefit'] if prow and prow['estimated_benefit'] is not None else 0.0

    roi_value = None
    if cost_total and cost_total > 0:
        try:
            roi_value = (benefit_est - cost_total) / cost_total
        except Exception:
            roi_value = None

    rid = str(uuid.uuid4())
    calculated_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO roi_records (id, project_id, calculated_at, cost_total, benefit_est, roi) VALUES (?, ?, ?, ?, ?, ?)', (rid, project_id, calculated_at, cost_total, benefit_est, roi_value))
    conn.commit()
    conn.close()

    # publish budget update to any SSE subscribers
    try:
        msg = {
            'project_id': project_id,
            'transaction_id': tid,
            'type': type,
            'description': description,
            'amount': amount,
            'category': category,
            'calculated_at': calculated_at,
            'roi': roi_value
        }
        # schedule publish in event loop
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(_publish_budget_update, msg)
        except RuntimeError:
            # no event loop in this thread — best-effort publish
            _publish_budget_update(msg)
    except Exception:
        pass

    return {'status': 'ok', 'transaction_id': tid, 'roi': roi_value}


@router.post('/projects/{project_id}/lessons')
def add_lesson(project_id: str, author: Optional[str] = 'unknown', lesson: str = ''):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM projects_pm WHERE id = ?', (project_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='project not found')

    lid = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO project_lessons (id, project_id, created_at, author, lesson) VALUES (?, ?, ?, ?, ?)', (lid, project_id, created_at, author, lesson))
    conn.commit()
    conn.close()
    return {'status': 'ok', 'lesson_id': lid}


@router.get('/projects/{project_id}/lessons')
def list_lessons(project_id: str, limit: int = 100):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM project_lessons WHERE project_id = ? ORDER BY created_at DESC LIMIT ?', (project_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {'status': 'ok', 'lessons': rows}


# --- AARs (After Action Reports) ---
@router.post('/projects/{project_id}/aars')
def add_aar(project_id: str, summary: str = ''):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM projects_pm WHERE id = ?', (project_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='project not found')

    aid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cur.execute('INSERT INTO project_aars (id, project_id, created_at, summary) VALUES (?, ?, ?, ?)', (aid, project_id, now, summary))
    conn.commit()
    conn.close()
    return {'status': 'ok', 'aar_id': aid}


@router.get('/projects/{project_id}/aars')
def list_aars(project_id: str, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM project_aars WHERE project_id = ? ORDER BY created_at DESC LIMIT ?', (project_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {'status': 'ok', 'aars': rows}


# --- Scope endpoints ---
@router.post('/projects/{project_id}/scope')
def set_scope(project_id: str, scope_text: str = '', milestones: Optional[str] = None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM projects_pm WHERE id = ?', (project_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='project not found')

    sid = str(uuid.uuid4())
    cur.execute('INSERT INTO project_scope (id, project_id, scope_text, milestones) VALUES (?, ?, ?, ?)', (sid, project_id, scope_text, milestones))
    conn.commit()
    conn.close()
    return {'status': 'ok', 'scope_id': sid}


@router.get('/projects/{project_id}/scope')
def get_scope(project_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM project_scope WHERE project_id = ? ORDER BY id DESC LIMIT 1', (project_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {'status': 'ok', 'scope': None}
    return {'status': 'ok', 'scope': dict(row)}


# --- Participants endpoints ---
@router.post('/projects/{project_id}/participants')
def add_participant(project_id: str, person_id: str, role: Optional[str] = None, unit: Optional[str] = None, attendance: int = 0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM projects_pm WHERE id = ?', (project_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='project not found')

    pid = str(uuid.uuid4())
    cur.execute('INSERT INTO participants (id, project_id, person_id, role, unit, attendance) VALUES (?, ?, ?, ?, ?, ?)', (pid, project_id, person_id, role, unit, attendance))
    conn.commit()
    conn.close()
    return {'status': 'ok', 'participant_id': pid}


@router.get('/projects/{project_id}/participants')
def list_participants(project_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM participants WHERE project_id = ?', (project_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {'status': 'ok', 'participants': rows}


# --- SSE / PubSub for budget updates ---
_budget_subscribers: List[asyncio.Queue] = []


def _publish_budget_update(msg: Dict[str, Any]):
    # best-effort: put into all subscriber queues
    for q in list(_budget_subscribers):
        try:
            q.put_nowait(msg)
        except Exception:
            try:
                _budget_subscribers.remove(q)
            except Exception:
                pass


@router.get('/budget/stream')
async def budget_stream():
    q: asyncio.Queue = asyncio.Queue()
    _budget_subscribers.append(q)

    async def event_generator():
        try:
            while True:
                msg = await q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        finally:
            try:
                _budget_subscribers.remove(q)
            except Exception:
                pass

    return StreamingResponse(event_generator(), media_type='text/event-stream')

