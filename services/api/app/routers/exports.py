from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional
import json, os, uuid, csv, zipfile
from datetime import datetime
from ..db import connect, get_db_path
from .rbac import require_perm

router = APIRouter(prefix="/v2/exports", tags=["exports"])

EXPORT_STORAGE_DIR = os.getenv('EXPORT_STORAGE_DIR', './data/exports')

def now_iso():
    return datetime.utcnow().isoformat()

def _ensure_export_dir(export_id: str) -> str:
    path = os.path.join(EXPORT_STORAGE_DIR, export_id)
    os.makedirs(path, exist_ok=True)
    return path

def _write_csv(path: str, rows: list, columns: Optional[list] = None):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        if not columns and rows and isinstance(rows[0], dict):
            columns = list(rows[0].keys())
        writer = csv.writer(fh)
        if columns:
            writer.writerow(columns)
            for r in rows:
                writer.writerow([r.get(c, '') if isinstance(r, dict) else r for c in columns])
        else:
            # write raw rows
            for r in rows:
                if isinstance(r, (list, tuple)):
                    writer.writerow(r)
                else:
                    writer.writerow([str(r)])

def _record_file(conn, file_id, export_id, kind, fmt, filename, storage_path, size_bytes):
    cur = conn.cursor()
    cur.execute('INSERT INTO export_file(id, export_id, kind, format, filename, storage_path, size_bytes, created_at) VALUES (?,?,?,?,?,?,?,?)', (
        file_id, export_id, kind, fmt, filename, storage_path, size_bytes, now_iso()
    ))
    conn.commit()

def _audit(conn, export_id, event, message=''):
    cur = conn.cursor()
    cur.execute('INSERT INTO export_audit(export_id, event, message, created_at) VALUES (?,?,?,?)', (export_id, event, message, now_iso()))
    conn.commit()

def _fetch_table_rows(query_key: str, limit: int = 1000):
    # Best-effort: if query_key matches a table name, select * from it
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute(f'SELECT * FROM {query_key} LIMIT ?', (limit,))
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = [dict(r) for r in cur.fetchall()]
            return cols, rows
        except Exception:
            return [], []
    finally:
        conn.close()

def _process_export(export_id: str, payload: Dict[str, Any]):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE export_job SET status=?, started_at=?, updated_at=? WHERE id=?', ('running', now_iso(), now_iso(), export_id))
        conn.commit()
        _audit(conn, export_id, 'STARTED', 'Export worker started')
        exp_dir = _ensure_export_dir(export_id)
        files = []
        fmt = payload.get('format', {})
        includes = fmt.get('include', [])
        limit = payload.get('options', {}).get('limit', 50000)

        query_key = payload.get('source', {}).get('query_key') or payload.get('source', {}).get('dashboard_key')

        # Table export
        if 'table' in includes:
            cols, rows = _fetch_table_rows(query_key or 'import_run', limit)
            fname = 'table.csv'
            fpath = os.path.join(exp_dir, fname)
            _write_csv(fpath, rows, cols)
            size = os.path.getsize(fpath)
            file_id = f'file_{uuid.uuid4().hex}'
            _record_file(conn, file_id, export_id, 'table', 'csv', fname, fpath, size)
            _audit(conn, export_id, 'WROTE_TABLE', fname)
            files.append(fpath)

        # Underlying export (attempt same as table)
        if 'underlying' in includes:
            cols, rows = _fetch_table_rows(query_key or 'import_run', limit)
            fname = 'underlying.csv'
            fpath = os.path.join(exp_dir, fname)
            _write_csv(fpath, rows, cols)
            size = os.path.getsize(fpath)
            file_id = f'file_{uuid.uuid4().hex}'
            _record_file(conn, file_id, export_id, 'underlying', 'csv', fname, fpath, size)
            _audit(conn, export_id, 'WROTE_UNDERLYING', fname)
            files.append(fpath)

        # Raw export (requires datahub.view_runs) — best-effort from import_run and stg_raw_dataset
        if 'raw' in includes:
            # attempt to read stg_raw_dataset rows
            cols, rows = _fetch_table_rows('stg_raw_dataset', limit)
            fname = 'raw.csv'
            fpath = os.path.join(exp_dir, fname)
            _write_csv(fpath, rows, cols)
            size = os.path.getsize(fpath)
            file_id = f'file_{uuid.uuid4().hex}'
            _record_file(conn, file_id, export_id, 'raw', 'csv', fname, fpath, size)
            _audit(conn, export_id, 'WROTE_RAW', fname)
            files.append(fpath)

        # Manifest
        manifest = {
            'export_id': export_id,
            'requested': payload.get('requested_at'),
            'source': payload.get('source'),
            'scope': payload.get('scope'),
            'format': payload.get('format'),
            'options': payload.get('options'),
            'dataset_versions': {'note': 'best-effort; unknown'},
            'kpi_version': os.getenv('KPI_VERSION', 'dev'),
            'created_at': now_iso()
        }
        mfname = 'manifest.json'
        mpath = os.path.join(exp_dir, mfname)
        with open(mpath, 'w', encoding='utf-8') as fh:
            json.dump(manifest, fh, indent=2)
        size = os.path.getsize(mpath)
        file_id = f'file_{uuid.uuid4().hex}'
        _record_file(conn, file_id, export_id, 'manifest', 'json', mfname, mpath, size)
        _audit(conn, export_id, 'WROTE_MANIFEST', mfname)
        files.append(mpath)

        # Bundle zip
        if fmt.get('bundle'):
            zname = f'{export_id}.zip'
            zpath = os.path.join(exp_dir, zname)
            with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in files:
                    zf.write(p, arcname=os.path.basename(p))
            size = os.path.getsize(zpath)
            file_id = f'file_{uuid.uuid4().hex}'
            _record_file(conn, file_id, export_id, 'bundle', 'zip', zname, zpath, size)
            _audit(conn, export_id, 'WROTE_BUNDLE', zname)

        # finalize
        cur.execute('UPDATE export_job SET status=?, ended_at=?, updated_at=? WHERE id=?', ('success', now_iso(), now_iso(), export_id))
        conn.commit()
        _audit(conn, export_id, 'COMPLETED', 'Export completed successfully')
    except Exception as e:
        try:
            cur.execute('UPDATE export_job SET status=?, error_summary=?, updated_at=? WHERE id=?', ('failed', str(e), now_iso(), export_id))
            conn.commit()
            _audit(conn, export_id, 'FAILED', str(e))
        except Exception:
            pass
    finally:
        conn.close()


def _render_with_playwright(export_id: str, render_payload: Dict[str, Any]):
    conn = connect()
    try:
        _audit(conn, export_id, 'RENDER_STARTED', 'Playwright render started')
        exp_dir = _ensure_export_dir(export_id)
        url = render_payload.get('url') or render_payload.get('page_url')
        if not url:
            _audit(conn, export_id, 'RENDER_FAILED', 'no url provided')
            return
        # import locally to avoid hard dependency at module import time
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            _audit(conn, export_id, 'RENDER_FAILED', f'playwright import error: {e}')
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='networkidle')
            # produce PDF if requested
            if render_payload.get('pdf', True):
                pdf_path = os.path.join(exp_dir, 'render.pdf')
                page.pdf(path=pdf_path)
                size = os.path.getsize(pdf_path)
                file_id = f'file_{uuid.uuid4().hex}'
                _record_file(conn, file_id, export_id, 'render', 'pdf', 'render.pdf', pdf_path, size)
                _audit(conn, export_id, 'WROTE_RENDER_PDF', 'render.pdf')
            # produce PNG screenshot if requested
            if render_payload.get('png', False):
                png_path = os.path.join(exp_dir, 'render.png')
                page.screenshot(path=png_path, full_page=True)
                size = os.path.getsize(png_path)
                file_id = f'file_{uuid.uuid4().hex}'
                _record_file(conn, file_id, export_id, 'render', 'png', 'render.png', png_path, size)
                _audit(conn, export_id, 'WROTE_RENDER_PNG', 'render.png')
            browser.close()
        _audit(conn, export_id, 'RENDER_COMPLETED', 'Playwright render completed')
    except Exception as e:
        _audit(conn, export_id, 'RENDER_FAILED', str(e))
    finally:
        conn.close()


@router.post('', dependencies=[Depends(require_perm('dashboards.export'))])
def create_export(payload: Dict[str, Any], background: BackgroundTasks, request: Request, user: Dict = Depends(require_perm('dashboards.export'))):
    # validate payload minimally
    export_id = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    payload = payload or {}
    payload.setdefault('requested_at', now_iso())
    # enforce raw-export permission server-side: require `datahub.view_runs` when raw requested
    fmt = payload.get('format') or {}
    includes = fmt.get('include') or []
    if 'raw' in includes:
        try:
            # call the dependency factory with the resolved user to perform the extra permission check
            require_perm('datahub.view_runs')(user)
        except HTTPException:
            raise HTTPException(status_code=403, detail='Forbidden: raw export requires datahub.view_runs permission')
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO export_job(id, requested_by, status, source_page, dashboard_key, widget_key, query_key, scope_json, filters_json, render_json, format_json, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            export_id,
            None,
            'queued',
            json.dumps(payload.get('source', {}).get('page')) if payload.get('source', {}) else None,
            payload.get('source', {}).get('dashboard_key') if payload.get('source') else None,
            payload.get('source', {}).get('widget_key') if payload.get('source') else None,
            payload.get('source', {}).get('query_key') if payload.get('source') else None,
            json.dumps(payload.get('scope')) if payload.get('scope') else None,
            json.dumps(payload.get('options', {}).get('filters')) if payload.get('options') else None,
            json.dumps(payload.get('render')) if payload.get('render') else None,
            json.dumps(payload.get('format')) if payload.get('format') else None,
            now_iso(), now_iso()
        ))
        conn.commit()
        _audit(conn, export_id, 'QUEUED', 'Export queued by API')
    finally:
        conn.close()

    # enqueue background worker
    background.add_task(_process_export, export_id, payload)
    return {'export_id': export_id, 'status': 'queued'}


@router.get('/{export_id}')
def get_export(export_id: str, user: Dict = Depends(require_perm('dashboards.export'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM export_job WHERE id=?', (export_id,))
        job = cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail='not found')
        cur.execute('SELECT id, kind, format, filename, storage_path, size_bytes, created_at FROM export_file WHERE export_id=?', (export_id,))
        files = [dict(r) for r in cur.fetchall()]
        return {'job': dict(job), 'files': files}
    finally:
        conn.close()


@router.get('')
def list_exports(mine: Optional[bool] = False, limit: int = 50, user: Dict = Depends(require_perm('dashboards.export'))):
    conn = connect()
    try:
        cur = conn.cursor()
        sql = 'SELECT * FROM export_job ORDER BY created_at DESC LIMIT ?'
        cur.execute(sql, (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()


@router.get('/{export_id}/files/{file_id}')
def download_export_file(export_id: str, file_id: str, user: Dict = Depends(require_perm('dashboards.export'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT filename, storage_path FROM export_file WHERE id=? AND export_id=?', (file_id, export_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='file not found')
        filename, path = row[0], row[1]
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail='file missing')
        return FileResponse(path, media_type='application/octet-stream', filename=filename)
    finally:
        conn.close()


@router.post('/{export_id}/render')
def trigger_render(export_id: str, render_payload: Dict[str, Any], background: BackgroundTasks, user: Dict = Depends(require_perm('dashboards.export'))):
    """Trigger Playwright render for an existing export job. Saves files into the export dir and records export_file rows."""
    # ensure export exists
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id FROM export_job WHERE id=?', (export_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='export job not found')
    finally:
        conn.close()

    # queue render background task
    background.add_task(_render_with_playwright, export_id, render_payload)
    return {'export_id': export_id, 'render': 'queued'}
from fastapi import APIRouter, Header, HTTPException
from ..db import connect
from io import StringIO
import csv
import os

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/activities.csv")
def export_activities(x_api_key: str = Header(None)):
    token = os.environ.get("EXPORT_API_TOKEN", "devtoken123")
    if x_api_key != token:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT activity_id,event_id,activity_type,campaign_name,channel,impressions,engagement_count,awareness_metric,activation_conversions,cost FROM marketing_activities")
        rows = cur.fetchall()
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(["activity_id", "event_id", "activity_type", "campaign_name", "channel", "impressions", "engagement_count", "awareness_metric", "activation_conversions", "cost"])
        for r in rows:
            writer.writerow(list(r))
        return (sio.getvalue(), 200, {"Content-Type": "text/csv"})
    finally:
        conn.close()


@router.get("/facts/metric")
def export_fact_metric():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, metric_key, metric_value, unit, org_unit_id, recorded_at, source, import_job_id FROM fact_metric")
        rows = cur.fetchall()
        return {"rows": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.get('/dashboard')
def export_dashboard(type: str = None, format: str = 'csv', fy: int = None, qtr: int = None, month: int = None, echelon_type: str = None, unit_value: str = None, funding_line: str = None):
    """Export tactical/dashboard data as CSV or JSON. type=events-roi|marketing|funnel|budget"""
    conn = connect()
    try:
        cur = conn.cursor()
        filters = {'fy': fy, 'qtr': qtr, 'month': month, 'echelon_type': echelon_type, 'unit_value': unit_value, 'funding_line': funding_line}
        if type == 'events-roi':
            # reuse simple query: list events with costs and marketing sums
            cur.execute("SELECT id, COALESCE(name,''), COALESCE(planned_cost,0), COALESCE(actual_cost,0), start_dt, end_dt FROM event ORDER BY start_dt DESC LIMIT 100")
            rows = cur.fetchall()
            items = []
            for r in rows:
                eid = str(r[0])
                cur.execute('SELECT COALESCE(SUM(cost),0) FROM marketing_activities WHERE event_id=?', (eid,))
                mcost = (cur.fetchone() or [0])[0] or 0
                items.append({'event_id': eid, 'name': r[1], 'planned_cost': r[2] or 0, 'actual_cost': r[3] or 0, 'marketing_cost': mcost, 'start_date': r[4], 'end_date': r[5]})
            if format == 'json':
                return {'status': 'ok', 'items': items, 'filters': filters}
            # csv
            import csv, io
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(['event_id','name','planned_cost','actual_cost','marketing_cost','start_date','end_date'])
            for it in items:
                w.writerow([it['event_id'], it['name'], it['planned_cost'], it['actual_cost'], it['marketing_cost'], it.get('start_date'), it.get('end_date')])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        if type == 'marketing':
            cur.execute('SELECT channel, COALESCE(SUM(cost),0) as cost, COALESCE(SUM(impressions),0) as impressions, COALESCE(SUM(activation_conversions),0) as activations FROM marketing_activities GROUP BY channel')
            rows = cur.fetchall()
            items = [{'channel': r[0], 'cost': r[1], 'impressions': r[2], 'activations': r[3]} for r in rows]
            if format == 'json':
                return {'status':'ok','by_channel': items, 'filters': filters}
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['channel','cost','impressions','activations'])
            for it in items:
                w.writerow([it['channel'], it['cost'], it['impressions'], it['activations']])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        if type == 'funnel':
            cur.execute('SELECT from_stage, to_stage, COUNT(1) as cnt FROM funnel_transitions GROUP BY from_stage, to_stage')
            rows = cur.fetchall()
            items = [{'from_stage': r[0], 'to_stage': r[1], 'count': r[2]} for r in rows]
            if format == 'json':
                return {'status':'ok','conversions': items, 'filters': filters}
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            w.writerow(['from_stage','to_stage','count'])
            for it in items:
                w.writerow([it['from_stage'], it['to_stage'], it['count']])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        if type == 'budget':
            # delegate to budget dashboard router function if available
            try:
                from .budget_dashboard import budget_dashboard
                data = budget_dashboard(None, fy=fy, qtr=qtr, org_unit_id=None, station_id=None, funding_line=funding_line, funding_source=None, eor_code=None)
            except Exception:
                data = {'status':'ok','totals':{},'by_funding_source':[], 'by_event':[], 'filters': filters}
            if format == 'json':
                return data
            import csv, io
            buf = io.StringIO(); w = csv.writer(buf)
            # write kpis
            kpis = data.get('kpis') or {}
            w.writerow(['metric','value'])
            for k,v in kpis.items():
                w.writerow([k,v])
            return (buf.getvalue(), 200, {'Content-Type': 'text/csv'})

        # unknown type
        return {'status':'error','message':'unknown export type'}
    finally:
        try:
            conn.close()
        except Exception:
            pass
