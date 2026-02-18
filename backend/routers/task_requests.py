"""
Task Requests API Router
Stores general action/task requests separate from the helpdesk workflow.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import random

router = APIRouter()


class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = 'medium'
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    actions: Optional[str] = None
    submitted_by: Optional[str] = 'web.dashboard'
    submitted_at: Optional[str] = None


@router.get("/task_requests")
async def get_task_requests(status: Optional[str] = None, submitted_by: Optional[str] = None):
    try:
        conn = sqlite3.connect("recruiting.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_requests (
                request_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT,
                assignee TEXT,
                due_date TEXT,
                actions TEXT,
                status TEXT DEFAULT 'open',
                submitted_by TEXT,
                submitted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        query = "SELECT * FROM task_requests WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if submitted_by:
            query += " AND submitted_by = ?"
            params.append(submitted_by)
        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        return {"status": "ok", "requests": rows, "total": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task_requests")
async def create_task_request(req: TaskRequest):
    try:
        conn = sqlite3.connect("recruiting.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_requests (
                request_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT,
                assignee TEXT,
                due_date TEXT,
                actions TEXT,
                status TEXT DEFAULT 'open',
                submitted_by TEXT,
                submitted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        request_id = f"treq_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"
        submitted_at = req.submitted_at or datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO task_requests (
                request_id, title, description, priority, assignee, due_date, actions, status, submitted_by, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id, req.title, req.description, req.priority, req.assignee, req.due_date, req.actions, 'open', req.submitted_by, submitted_at
        ))

        conn.commit()
        conn.close()

        return {"status": "ok", "message": "Task request created", "request_id": request_id, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
