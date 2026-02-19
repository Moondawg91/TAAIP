from fastapi import APIRouter
from typing import Dict
from ..db import connect

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get('/summary')
def budget_summary() -> Dict:
    conn = connect()
    try:
        cur = conn.cursor()
        planned = 0.0
        actual = 0.0
        try:
            cur.execute('SELECT SUM(amount) as s FROM budget_line_item')
            r = cur.fetchone()
            planned = float(r['s']) if r and r['s'] is not None else 0.0
        except Exception:
            planned = 0.0
        try:
            cur.execute('SELECT SUM(COALESCE(cost,0)) as s FROM marketing_activities')
            r2 = cur.fetchone()
            actual = float(r2['s']) if r2 and r2['s'] is not None else 0.0
        except Exception:
            actual = 0.0
        remaining = planned - actual
        return { 'planned': planned, 'actual': actual, 'remaining': remaining }
    finally:
        try:
            conn.close()
        except Exception:
            pass
