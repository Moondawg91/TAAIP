from fastapi import APIRouter
from ..db import connect, row_to_dict

router = APIRouter(prefix="/planning", tags=["planning"])


@router.get('/projects-events')
def projects_events_list():
    conn = connect()
    try:
        cur = conn.cursor()
        out = {'projects': [], 'events': []}
        try:
            cur.execute('SELECT * FROM projects ORDER BY created_at DESC LIMIT 500')
            rows = cur.fetchall()
            out['projects'] = [row_to_dict(cur, r) for r in rows]
        except Exception:
            out['projects'] = []
        try:
            cur.execute('SELECT * FROM event ORDER BY start_dt DESC LIMIT 500')
            rows2 = cur.fetchall()
            out['events'] = [row_to_dict(cur, r) for r in rows2]
        except Exception:
            out['events'] = []
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass
