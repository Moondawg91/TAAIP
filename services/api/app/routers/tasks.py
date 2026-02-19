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

        now = __import__('datetime').datetime.utcnow().isoformat()
        # adapt to existing schema: only insert columns that exist
        cur.execute("PRAGMA table_info(task)")
        task_cols = [r[1] for r in cur.fetchall()]
        insert_cols = ['project_id','title','owner','status','percent_complete','created_at','updated_at']
        cols_to_insert = [c for c in insert_cols if c in task_cols]
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
            elif c == 'percent_complete':
                params.append(0)
            elif c == 'created_at' or c == 'updated_at':
                params.append(now)
        placeholders = ','.join(['?'] * len(cols_to_insert))
        sql = f"INSERT INTO task({', '.join(cols_to_insert)}) VALUES ({placeholders})"
        cur.execute(sql, tuple(params))
        conn.commit()
        tid = cur.lastrowid
        cur.execute('SELECT * FROM task WHERE id=?', (tid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.get("/", summary="List tasks")
def list_tasks(project_id: Optional[int] = None, owner: Optional[str] = None, limit: int = 200, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM task WHERE 1=1'
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
                sql = f"SELECT t.* FROM task t JOIN project p ON p.id=t.project_id WHERE p.org_unit_id IN ({placeholders})"
                params = list(allowed_orgs)
        if owner:
            sql += ' AND owner=?'; params.append(owner)
        sql += ' ORDER BY id DESC LIMIT ?'; params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        return [row_to_dict(cur, r) for r in rows]
    finally:
        conn.close()



@router.patch("/{task_id}", summary="Update a task")
def update_task(task_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT project_id FROM task WHERE id=?', (task_id,))
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
        cur.execute("PRAGMA table_info(task)")
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
        sql = 'UPDATE task SET ' + ','.join(fields) + ' WHERE id=?'
        cur.execute(sql, tuple(params))
        conn.commit()
        cur.execute('SELECT * FROM task WHERE id=?', (task_id,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()


@router.delete("/{task_id}", summary="Delete a task")
def delete_task(task_id: int, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT project_id FROM task WHERE id=?', (task_id,))
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
        cur.execute('DELETE FROM task WHERE id=?', (task_id,))
        conn.commit()
        return {'deleted': task_id}
    finally:
        conn.close()


@router.post("/{task_id}/comments", summary="Add a comment to a task")
def add_task_comment(task_id: int, payload: dict, allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT project_id FROM task WHERE id=?', (task_id,))
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
        cur.execute('SELECT project_id FROM task WHERE id=?', (task_id,))
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
        cur.execute('INSERT INTO task_assignment(task_id, assignee, assigned_at, percent_expected) VALUES (?,?,?,?)', (task_id, assignee, now, percent_expected))
        conn.commit()
        aid = cur.lastrowid
        cur.execute('SELECT * FROM task_assignment WHERE id=?', (aid,))
        return row_to_dict(cur, cur.fetchone())
    finally:
        conn.close()
