from fastapi import APIRouter
from ..db import connect, row_to_dict

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get('/targeting-data')
def targeting_data(limit: int = 200):
    conn = connect()
    try:
        cur = conn.cursor()
        out = {'fact_funnel': [], 'fact_marketing': []}
        try:
            cur.execute('SELECT * FROM fact_funnel ORDER BY date_key DESC LIMIT ?', (limit,))
            rows = cur.fetchall()
            out['fact_funnel'] = [row_to_dict(cur, r) for r in rows]
        except Exception:
            out['fact_funnel'] = []
        try:
            cur.execute('SELECT * FROM fact_marketing ORDER BY date_key DESC LIMIT ?', (limit,))
            rows2 = cur.fetchall()
            out['fact_marketing'] = [row_to_dict(cur, r) for r in rows2]
        except Exception:
            out['fact_marketing'] = []
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass
