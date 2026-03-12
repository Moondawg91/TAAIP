from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from ..db import connect
import csv
import io
import datetime
import json
import uuid

router = APIRouter(prefix="/phonetics", tags=["phonetics"])


def _now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


@router.get("/readiness")
def phonetics_readiness():
    conn = connect()
    cur = conn.cursor()
    dataset = {'dataset_key': 'phonetic_map', 'table': 'phonetic_map', 'display_name': 'Phonetic Map'}
    if not conn:
        return {'status':'partial', 'datasets':[dataset], 'blocking':['phonetic_map']}
    try:
        cur.execute("SELECT COUNT(1) FROM phonetic_map")
        rc = cur.fetchone()[0] or 0
    except Exception:
        rc = 0
    dataset['row_count'] = rc
    dataset['loaded'] = bool(rc > 0)
    dataset['missing_columns'] = []
    status = 'ok' if dataset['loaded'] else 'partial'
    return {'status': status, 'datasets': [dataset], 'blocking': [] if dataset['loaded'] else ['phonetic_map']}


@router.get("/search")
def phonetics_search(query: str = Query(...), type: str = Query(None), limit: int = Query(100)):
    conn = connect()
    cur = conn.cursor()
    q = "SELECT id, term, phonetic, type, created_at FROM phonetic_map WHERE (term LIKE ? OR phonetic LIKE ?)"
    params = [f"%{query}%", f"%{query}%"]
    if type:
        q += " AND type = ?"
        params.append(type)
    q += " ORDER BY term LIMIT ?"
    params.append(int(limit))
    try:
        cur.execute(q, params)
        rows = cur.fetchall()
        results = [{'id': r[0], 'term': r[1], 'phonetic': r[2], 'type': r[3], 'created_at': r[4]} for r in rows]
        return {'status': 'ok', 'results': results}
    except Exception:
        raise HTTPException(status_code=500, detail='search failed')


@router.get("/export.csv")
def phonetics_export_csv(type: str = Query(None)):
    conn = connect()
    cur = conn.cursor()
    headers = ['id', 'term', 'phonetic', 'type', 'created_at', 'updated_at']
    q = "SELECT id, term, phonetic, type, created_at, updated_at FROM phonetic_map"
    params = []
    if type:
        q += " WHERE type = ?"
        params.append(type)
    q += " ORDER BY term"
    try:
        cur.execute(q, params)
        rows = cur.fetchall()
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r[0], r[1], r[2], r[3] or '', r[4] or '', r[5] or ''])
        return Response(content=out.getvalue(), media_type='text/csv')
    except Exception:
        return Response(content=','.join(headers)+"\n", media_type='text/csv')


def _parse_csv_text(csv_text: str):
    f = io.StringIO(csv_text)
    try:
        reader = csv.DictReader(f)
    except Exception:
        raise HTTPException(status_code=400, detail='invalid CSV')
    rows = []
    for i, r in enumerate(reader):
        # Normalize keys to lower-case
        nr = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
        rows.append(nr)
    return rows


@router.post("/import/preview")
def phonetics_import_preview(payload: dict):
    csv_text = payload.get('csv_text')
    if not csv_text:
        raise HTTPException(status_code=400, detail='csv_text required')
    rows = _parse_csv_text(csv_text)
    preview = []
    errors = []
    for i, r in enumerate(rows):
        term = r.get('term') or r.get('name')
        phonetic = r.get('phonetic') or r.get('phone')
        ptype = r.get('type') or 'other'
        if not term or not phonetic:
            errors.append({'row': i+1, 'error': 'term and phonetic required'})
            continue
        preview.append({'row': i+1, 'term': term, 'phonetic': phonetic, 'type': ptype})
    return {'status': 'ok', 'preview': preview, 'errors': errors}


@router.post("/import/commit")
def phonetics_import_commit(payload: dict):
    csv_text = payload.get('csv_text')
    if not csv_text:
        raise HTTPException(status_code=400, detail='csv_text required')
    rows = _parse_csv_text(csv_text)
    conn = connect()
    cur = conn.cursor()
    inserted = 0
    errors = []
    now = _now_iso()
    for i, r in enumerate(rows):
        term = r.get('term') or r.get('name')
        phonetic = r.get('phonetic') or r.get('phone')
        ptype = r.get('type') or 'other'
        if not term or not phonetic:
            errors.append({'row': i+1, 'error': 'term and phonetic required'})
            continue
        # id: use provided id if present, else deterministic uuid5 from term+type
        rid = r.get('id') or str(uuid.uuid5(uuid.NAMESPACE_URL, f"{term}|{ptype}"))
        try:
            cur.execute("INSERT OR REPLACE INTO phonetic_map(id, term, phonetic, type, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                        (rid, term, phonetic, ptype, now, now))
            inserted += 1
        except Exception as e:
            errors.append({'row': i+1, 'error': str(e)})
    try:
        conn.commit()
    except Exception:
        pass
    # upsert registry
    try:
        cur.execute("INSERT OR REPLACE INTO phonetic_dataset_registry(dataset_key, as_of, row_count, last_loaded_at, status) VALUES (?,?,?,?,?)",
                    ('phonetic_map', now, inserted, now, 'loaded' if inserted>0 else 'empty'))
        conn.commit()
    except Exception:
        pass
    return {'status': 'ok', 'inserted': inserted, 'errors': errors}
