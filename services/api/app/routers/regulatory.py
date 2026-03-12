from fastapi import APIRouter, Query
from ..db import connect
from typing import Optional

router = APIRouter()


@router.get('/resources/regulatory')
def list_regulatory(search: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    q = "SELECT id, code, title, description, category, authority_level, created_at FROM regulatory_references WHERE 1=1"
    params = []
    if search:
        q += " AND (code LIKE ? OR title LIKE ? OR description LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    if category:
        q += " AND category = ?"
        params.append(category)
    q += " ORDER BY code"
    try:
        cur.execute(q, params)
        rows = cur.fetchall()
        items = [{'id': r[0], 'code': r[1], 'title': r[2], 'description': r[3], 'category': r[4], 'authority_level': r[5], 'created_at': r[6]} for r in rows]
        return {'status':'ok', 'items': items}
    except Exception:
        return {'status':'ok', 'items': []}


@router.get('/resources/regulatory/{item_id}')
def get_regulatory(item_id: str):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, code, title, description, category, authority_level, created_at FROM regulatory_references WHERE id=?', (item_id,))
        r = cur.fetchone()
        if not r:
            return {'status':'not_found'}
        return {'status':'ok', 'item': {'id': r[0], 'code': r[1], 'title': r[2], 'description': r[3], 'category': r[4], 'authority_level': r[5], 'created_at': r[6]}}
    except Exception:
        return {'status':'ok', 'item': None}


@router.get('/regulatory/references')
def api_regulatory_references(q: Optional[str] = Query(None), category: Optional[str] = Query(None), authority_level: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    qsql = "SELECT id, code, title, description, category, authority_level, source_system FROM regulatory_references WHERE 1=1"
    params = []
    if q:
        qsql += " AND (code LIKE ? OR title LIKE ? OR description LIKE ?)"
        s = f"%{q}%"
        params.extend([s, s, s])
    if category:
        qsql += " AND category = ?"
        params.append(category)
    if authority_level:
        qsql += " AND authority_level = ?"
        params.append(authority_level)
    qsql += " ORDER BY code"
    try:
        cur.execute(qsql, params)
        rows = cur.fetchall()
        refs = [{'id': r[0], 'code': r[1], 'title': r[2], 'description': r[3], 'category': r[4], 'authority_level': r[5], 'source_system': r[6]} for r in rows]
        return {'status':'ok', 'count': len(refs), 'references': refs}
    except Exception:
        return {'status':'ok', 'count':0, 'references': []}


@router.get('/regulatory/traceability')
def api_regulatory_traceability(module_key: Optional[str] = Query(None), route: Optional[str] = Query(None), metric_key: Optional[str] = Query(None), reference_code: Optional[str] = Query(None)):
    conn = connect()
    cur = conn.cursor()
    qsql = "SELECT id, reference_id, module_key, page_route, metric_key, decision_supported, tor_enclosure, notes FROM regulatory_traceability WHERE 1=1"
    params = []
    if module_key:
        qsql += " AND module_key = ?"
        params.append(module_key)
    if route:
        qsql += " AND page_route = ?"
        params.append(route)
    if metric_key:
        qsql += " AND metric_key = ?"
        params.append(metric_key)
    if reference_code:
        # join by reference code
        qsql = "SELECT t.id, t.reference_id, t.module_key, t.page_route, t.metric_key, t.decision_supported, t.tor_enclosure, t.notes, r.code, r.title FROM regulatory_traceability t LEFT JOIN regulatory_references r ON r.id=t.reference_id WHERE 1=1"
        params = []
        qsql += " AND r.code = ?"
        params.append(reference_code)
    try:
        cur.execute(qsql, params)
        rows = cur.fetchall()
        links = []
        for r in rows:
            if len(r) >= 9:
                links.append({'id': r[0], 'reference': {'id': r[1], 'code': r[8], 'title': r[9]}, 'module_key': r[2], 'page_route': r[3], 'metric_key': r[4], 'decision_supported': r[5], 'tor_enclosure': r[6], 'notes': r[7]})
            else:
                links.append({'id': r[0], 'reference': {'id': r[1]}, 'module_key': r[2], 'page_route': r[3], 'metric_key': r[4], 'decision_supported': r[5], 'tor_enclosure': r[6], 'notes': r[7]})
        return {'status':'ok', 'count': len(links), 'links': links}
    except Exception:
        return {'status':'ok', 'count': 0, 'links': []}


@router.get('/regulatory/modules')
def api_regulatory_modules():
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT module_key, display_name, description, owner_role FROM module_registry ORDER BY display_name")
        rows = cur.fetchall()
        mods = [{'module_key': r[0], 'display_name': r[1], 'description': r[2], 'owner_role': r[3]} for r in rows]
        return {'status':'ok', 'modules': mods}
    except Exception:
        return {'status':'ok', 'modules': []}
