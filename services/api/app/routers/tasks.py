from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from ..db import connect, row_to_dict
from .rbac import require_scope

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", summary="Create a task")
def create_task(payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        # detect whether legacy singular `task` or plural `tasks` table exists
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task','tasks')")
            trow = cur.fetchone()
            table_name = trow[0] if trow else 'task'
        except Exception:
            table_name = 'task'
        project_id = payload.get('project_id')
        title = payload.get('title')
        owner = payload.get('owner')
        status = payload.get('status') or 'open'
        if not project_id or not title:
            raise HTTPException(status_code=400, detail='missing_fields')
        # ensure project exists and within scope
        cur.execute('SELECT org_unit_id FROM project WHERE id=?', (project_id,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(status_code=404, detail='project_not_found')
        p = row_to_dict(cur, p)
        if allowed_orgs is not None and p.get('org_unit_id') not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        import uuid
        now = __import__('datetime').datetime.utcnow().isoformat()
        # adapt to existing schema: only insert columns that exist
        cur.execute(f"PRAGMA table_info({table_name})")
        task_cols = [r[1] for r in cur.fetchall()]
        insert_cols = ['project_id','title','owner','status','percent_complete','created_at','updated_at']
        cols_to_insert = [c for c in insert_cols if c in task_cols]
        # If no insertable columns discovered, ensure legacy/modern task tables exist
        if not cols_to_insert:
            try:
                cur.executescript('''
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
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS task (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    title TEXT,
                    owner TEXT,
                    status TEXT,
                    percent_complete REAL DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
                ''')
            except Exception:
                pass
            cur.execute(f"PRAGMA table_info({table_name})")
            task_cols = [r[1] for r in cur.fetchall()]
            cols_to_insert = [c for c in insert_cols if c in task_cols]
        # If the table uses `task_id` as primary key, ensure we generate one
        generated_task_id = None
        if 'task_id' in task_cols and 'task_id' not in cols_to_insert:
            generated_task_id = 'task_' + uuid.uuid4().hex[:10]
            cols_to_insert.insert(0, 'task_id')
        params = []
        for c in cols_to_insert:
            if c == 'project_id':
                params.append(project_id)
            elif c == 'title':
                params.append(title)
            elif c == 'owner':
                params.append(owner)
            elif c == 'status':
                params.append(status)
            elif c == 'task_id':
                params.append(generated_task_id)
            elif c == 'percent_complete':
                params.append(0)
            elif c == 'created_at' or c == 'updated_at':
                params.append(now)
        placeholders = ','.join(['?'] * len(cols_to_insert))
        sql = f"INSERT INTO {table_name}({', '.join(cols_to_insert)}) VALUES ({placeholders})"
        cur.execute(sql, tuple(params))
        conn.commit()
        tid = cur.lastrowid
        # pick PK for select
        pk_col = 'id' if 'id' in task_cols else ('task_id' if 'task_id' in task_cols else None)
        if pk_col == 'task_id' and generated_task_id:
            cur.execute(f'SELECT rowid as id, * FROM {table_name} WHERE task_id=?', (generated_task_id,))
        elif pk_col == 'id' and tid:
            cur.execute(f'SELECT rowid as id, * FROM {table_name} WHERE id=?', (tid,))
        else:
            # fallback to last row by rowid
            cur.execute(f'SELECT rowid as id, * FROM {table_name} ORDER BY rowid DESC LIMIT 1')
        res = row_to_dict(cur, cur.fetchone())
        # normalize numeric ids to ints when possible for test comparisons
        try:
            if res and 'project_id' in res and isinstance(res.get('project_id'), str) and res.get('project_id').isdigit():
                res['project_id'] = int(res['project_id'])
        except Exception:
            pass
        return res
    finally:
        conn.close()


@router.get("/", summary="List tasks")
def list_tasks(project_id: Optional[int] = None, owner: Optional[str] = None, limit: int = 200, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        # resolve table name to tolerate legacy vs modern schema
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task','tasks')")
            trow = cur.fetchone()
            table_name = trow[0] if trow else 'task'
        except Exception:
            table_name = 'task'
        sql = f'SELECT * FROM {table_name} WHERE 1=1'
        params: List = []
        if project_id is not None:
            # verify scope via project org
            cur.execute('SELECT org_unit_id FROM project WHERE id=?', (project_id,))
            p = cur.fetchone()
            if not p:
                return []
            p = row_to_dict(cur, p)
            if allowed_orgs is not None and p.get('org_unit_id') not in allowed_orgs:
                return []
            sql += ' AND project_id=?'; params.append(project_id)
        else:
            # no project filter: if allowed_orgs provided, join via project
            if allowed_orgs is not None:
                placeholders = ','.join(['?'] * len(allowed_orgs)) if allowed_orgs else 'NULL'
                sql = f"SELECT t.* FROM {table_name} t JOIN project p ON p.id=t.project_id WHERE p.org_unit_id IN ({placeholders})"
                params = list(allowed_orgs)
        if owner:
            sql += ' AND owner=?'; params.append(owner)
        # determine ordering column: prefer integer `id` when present, else use rowid
        try:
            cur.execute(f"PRAGMA table_info({table_name})")
            cols_info = [r for r in cur.fetchall()]
            cols_present = [c[1] for c in cols_info]
        except Exception:
            cols_present = []
        # If table doesn't have integer `id`, include rowid as `id` in the select so callers always see `id`.
        if 'id' not in cols_present:
            sql = sql.replace('SELECT ', 'SELECT rowid as id, ', 1)
            sql += ' ORDER BY rowid DESC LIMIT ?'; params.append(limit)
        else:
            sql += ' ORDER BY id DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        results = [row_to_dict(cur, r) for r in rows]
        # normalize numeric ids when possible
        for res in results:
            try:
                if res and 'project_id' in res and isinstance(res.get('project_id'), str) and res.get('project_id').isdigit():
                    res['project_id'] = int(res['project_id'])
            except Exception:
                pass
        return results
    finally:
        conn.close()



@router.patch("/{task_id}", summary="Update a task")
def update_task(task_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task','tasks')")
            trow = cur.fetchone()
            table_name = trow[0] if trow else 'task'
        except Exception:
            table_name = 'task'
        # determine whether to query by `id` or by `rowid`
        try:
            cur.execute(f"PRAGMA table_info({table_name})")
            task_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            task_cols = []
        where_col = 'id' if 'id' in task_cols else 'rowid'
        cur.execute(f'SELECT project_id FROM {table_name} WHERE {where_col}=?', (task_id,))
        t = cur.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail='task_not_found')
        t = row_to_dict(cur, t)
        cur.execute('SELECT org_unit_id FROM project WHERE id=?', (t.get('project_id'),))
        p = cur.fetchone()
        if p:
            p = row_to_dict(cur, p)
        if allowed_orgs is not None and p and p.get('org_unit_id') not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')

        title = payload.get('title') if isinstance(payload, dict) else None
        owner = payload.get('owner') if isinstance(payload, dict) else None
        status = payload.get('status') if isinstance(payload, dict) else None
        percent_complete = payload.get('percent_complete') if isinstance(payload, dict) else None
        # ensure we only update columns that exist in the DB
        cur.execute(f"PRAGMA table_info({table_name})")
        task_cols = [r[1] for r in cur.fetchall()]
        fields = []
        params = []
        if title is not None and 'title' in task_cols:
            fields.append('title=?'); params.append(title)
        if owner is not None and 'owner' in task_cols:
            fields.append('owner=?'); params.append(owner)
        if status is not None and 'status' in task_cols:
            fields.append('status=?'); params.append(status)
        if percent_complete is not None and 'percent_complete' in task_cols:
            fields.append('percent_complete=?'); params.append(percent_complete)
        if not fields:
            return {}
        # append updated_at if available
        if 'updated_at' in task_cols:
            fields.append('updated_at=?')
            params.append(__import__('datetime').datetime.utcnow().isoformat())
        params.append(task_id)
        sql = f'UPDATE {table_name} SET ' + ','.join(fields) + f' WHERE {where_col}=?'
        cur.execute(sql, tuple(params))
        conn.commit()
        # return updated row; include rowid as id when necessary
        if 'id' in task_cols:
            cur.execute(f'SELECT * FROM {table_name} WHERE id=?', (task_id,))
        else:
            cur.execute(f'SELECT rowid as id, * FROM {table_name} WHERE rowid=?', (task_id,))
        res = row_to_dict(cur, cur.fetchone())
        try:
            if res and 'project_id' in res and isinstance(res.get('project_id'), str) and res.get('project_id').isdigit():
                res['project_id'] = int(res['project_id'])
        except Exception:
            pass
        return res
    finally:
        conn.close()


@router.delete("/{task_id}", summary="Delete a task")
def delete_task(task_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task','tasks')")
            trow = cur.fetchone()
            table_name = trow[0] if trow else 'task'
        except Exception:
            table_name = 'task'
        try:
            cur.execute(f"PRAGMA table_info({table_name})")
            task_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            task_cols = []
        where_col = 'id' if 'id' in task_cols else 'rowid'
        cur.execute(f'SELECT project_id FROM {table_name} WHERE {where_col}=?', (task_id,))
        t = cur.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail='task_not_found')
        t = row_to_dict(cur, t)
        cur.execute('SELECT org_unit_id FROM project WHERE id=?', (t.get('project_id'),))
        p = cur.fetchone()
        if p:
            p = row_to_dict(cur, p)
        if allowed_orgs is not None and p and p.get('org_unit_id') not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        cur.execute(f'DELETE FROM {table_name} WHERE {where_col}=?', (task_id,))
        conn.commit()
        return {'deleted': task_id}
    finally:
        conn.close()


@router.post("/{task_id}/comments", summary="Add a comment to a task")
def add_task_comment(task_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task','tasks')")
            trow = cur.fetchone()
            table_name = trow[0] if trow else 'task'
        except Exception:
            table_name = 'task'
        try:
            cur.execute(f"PRAGMA table_info({table_name})")
            task_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            task_cols = []
        where_col = 'id' if 'id' in task_cols else 'rowid'
        cur.execute(f'SELECT project_id FROM {table_name} WHERE {where_col}=?', (task_id,))
        t = cur.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail='task_not_found')
        t = row_to_dict(cur, t)
        cur.execute('SELECT org_unit_id FROM project WHERE id=?', (t.get('project_id'),))
        p = cur.fetchone()
        if p:
            p = row_to_dict(cur, p)
        if allowed_orgs is not None and p and p.get('org_unit_id') not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        commenter = payload.get('commenter') if isinstance(payload, dict) else None
        comment = payload.get('comment') if isinstance(payload, dict) else None
        now = __import__('datetime').datetime.utcnow().isoformat()
        # ensure task_comment exists
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS task_comment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                commenter TEXT,
                comment TEXT,
                created_at TEXT
            );
            ''')
        except Exception:
            pass
        cur.execute('INSERT INTO task_comment(task_id, commenter, comment, created_at) VALUES (?,?,?,?)', (task_id, commenter, comment, now))
        conn.commit()
        cid = cur.lastrowid
        cur.execute('SELECT * FROM task_comment WHERE id=?', (cid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.post("/{task_id}/assign", summary="Assign a task")
def assign_task(task_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('task','tasks')")
            trow = cur.fetchone()
            table_name = trow[0] if trow else 'task'
        except Exception:
            table_name = 'task'
        # determine whether table exposes an `id` column or we must use `rowid`
        try:
            cur.execute(f"PRAGMA table_info({table_name})")
            task_cols = [r[1] for r in cur.fetchall()]
        except Exception:
            task_cols = []
        where_col = 'id' if 'id' in task_cols else 'rowid'
        cur.execute(f'SELECT project_id FROM {table_name} WHERE {where_col}=?', (task_id,))
        t = cur.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail='task_not_found')
        t = row_to_dict(cur, t)
        cur.execute('SELECT org_unit_id FROM project WHERE id=?', (t.get('project_id'),))
        p = cur.fetchone()
        if p:
            p = row_to_dict(cur, p)
        if allowed_orgs is not None and p and p.get('org_unit_id') not in allowed_orgs:
            raise HTTPException(status_code=403, detail='forbidden')
        assignee = payload.get('assignee') if isinstance(payload, dict) else None
        percent_expected = payload.get('percent_expected') if isinstance(payload, dict) else None
        now = __import__('datetime').datetime.utcnow().isoformat()
        # ensure task_assignment exists
        try:
            cur.executescript('''
            CREATE TABLE IF NOT EXISTS task_assignment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                assignee TEXT,
                assigned_at TEXT,
                percent_expected INTEGER
            );
            ''')
        except Exception:
            pass
        cur.execute('INSERT INTO task_assignment(task_id, assignee, assigned_at, percent_expected) VALUES (?,?,?,?)', (task_id, assignee, now, percent_expected))
        conn.commit()
        aid = cur.lastrowid
        cur.execute('SELECT * FROM task_assignment WHERE id=?', (aid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()
