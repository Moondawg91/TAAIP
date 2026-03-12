
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from ..db import connect
from .. import org_utils
from .rbac import require_perm

router = APIRouter(prefix="/v2/org", tags=["v2_org"])


@router.get('/node')
def node(unit_rsid: str = 'USAREC', user: dict = Depends(require_perm('dashboards.view'))):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, rsid, name, type, parent_id FROM org_unit WHERE rsid = ? OR upper(rsid)=? LIMIT 1', (unit_rsid, unit_rsid.upper()))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='Org unit not found')
        r = dict(row)
        cid = r.get('id')
        cur.execute('SELECT COUNT(1) as cnt FROM org_unit WHERE parent_id = ? AND record_status != "deleted"', (cid,))
        cnt = cur.fetchone()
        cntv = dict(cnt).get('cnt') if cnt else 0
        return {
            'unit_rsid': r.get('rsid'),
            'unit_name': r.get('name'),
            'echelon': r.get('type'),
            'parent_id': r.get('parent_id'),
            'children_count': cntv
        }
    finally:
        conn.close()


@router.get('/children')
def children(unit_rsid: str = 'USAREC', user: dict = Depends(require_perm('dashboards.view'))):
    conn = connect()
    try:
        kids = org_utils.get_children(conn, unit_rsid)
        return {'unit_rsid': unit_rsid, 'children': kids}
    finally:
        conn.close()


@router.get('/descendants')
def descendants(unit_rsid: str = 'USAREC', depth: int = 50, user: dict = Depends(require_perm('dashboards.view'))):
    conn = connect()
    try:
        rs = org_utils.get_descendant_units(conn, unit_rsid, max_depth=depth)
        return {'unit_rsid': unit_rsid, 'descendants': rs}
    finally:
        conn.close()


@router.get('/tree')
def tree(unit_rsid: str = 'USAREC', depth: int = 4, user: dict = Depends(require_perm('dashboards.view'))):
    """Return nested tree up to depth (basic nested list)."""
    conn = connect()
    try:
        def build(node_rsid, cur_depth):
            cur = conn.cursor()
            cur.execute('SELECT id, rsid, name, type FROM org_unit WHERE rsid = ? OR upper(rsid)=? LIMIT 1', (node_rsid, node_rsid.upper()))
            rrow = cur.fetchone()
            if not rrow:
                return None
            r = dict(rrow)
            node = {'unit_rsid': r.get('rsid'), 'unit_name': r.get('name'), 'echelon': r.get('type')}
            if cur_depth <= 0:
                return node
            cur.execute('SELECT rsid FROM org_unit WHERE parent_id = (SELECT id FROM org_unit WHERE rsid=? LIMIT 1) AND record_status != "deleted"', (r.get('rsid'),))
            children = [dict(c).get('rsid') for c in cur.fetchall() if dict(c).get('rsid')]
            node['children'] = []
            for c in children:
                child_node = build(c, cur_depth-1)
                if child_node:
                    node['children'].append(child_node)
            return node

        root = build(unit_rsid, depth)
        return {'unit_rsid': unit_rsid, 'tree': root}
    finally:
        conn.close()


@router.get('/roots')
def roots():
    """Return top-level roots (units without a parent)."""
    def _compute_sort_order(r: dict):
        # Best-effort sort order: prefer explicit sort_order, then numeric id, then rsid
        try:
            if r is None:
                return 0
            if isinstance(r.get('sort_order'), int):
                return r.get('sort_order')
            if r.get('id') is not None:
                try:
                    return int(r.get('id'))
                except Exception:
                    pass
            # fallback to rsid string sort weight
            return 0
        except Exception:
            return 0
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT rsid, display_name, echelon, parent_rsid, unit_key, id FROM org_unit WHERE parent_rsid IS NULL OR parent_rsid = '' ORDER BY id ASC")
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            # Fallback for legacy schema: use `name` as `display_name` when column missing
            try:
                # legacy fallback: use parent_id NULL check and map `name` -> `display_name`
                cur.execute("SELECT rsid, name as display_name, type as echelon, parent_id as parent_rsid, unit_key, id FROM org_unit WHERE parent_id IS NULL ORDER BY id ASC")
                rows = [dict(r) for r in cur.fetchall()]
            except Exception:
                rows = []

        for r in rows:
            r['sort_order'] = _compute_sort_order(r)

        rows_sorted = sorted(rows, key=lambda x: (0, x.get('sort_order')) if isinstance(x.get('sort_order'), int) else (1, str(x.get('sort_order'))))

        items = [ { 'rsid': r.get('rsid'), 'unit_key': r.get('unit_key'), 'display_name': r.get('display_name'), 'echelon': r.get('echelon'), 'parent_key': r.get('parent_rsid'), 'sort_order': r.get('sort_order') } for r in rows_sorted ]
        return { 'status': 'ok', 'roots': items }
    finally:
        conn.close()


@router.get('/path')
def path(rsid: str = None, unit_key: str = None):
    conn = connect()
    try:
        cur = conn.cursor()
        # if caller provided unit_key, resolve to rsid
        if unit_key and not rsid:
            cur.execute('SELECT rsid FROM org_unit WHERE unit_key = ? LIMIT 1', (unit_key,))
            p = cur.fetchone()
            if p:
                rsid = dict(p).get('rsid')

        if not rsid:
            return { 'status': 'error', 'message': 'missing rsid or unit_key' }

        cur.execute('SELECT rsid, display_name, echelon, parent_rsid, unit_key FROM org_unit WHERE rsid = ?', (rsid,))
        row = cur.fetchone()
        if not row:
            return { 'status': 'error', 'message': f'node {rsid} not found' }
        node = dict(row)
        path = []
        cur_rsid = node.get('parent_rsid')
        # walk up until no parent
        while cur_rsid:
            cur.execute('SELECT rsid, display_name, echelon, parent_rsid, unit_key FROM org_unit WHERE rsid = ?', (cur_rsid,))
            p = cur.fetchone()
            if not p:
                break
            pd = dict(p)
            path.append(pd)
            cur_rsid = pd.get('parent_rsid')

        # reverse path to root-first
        path = list(reversed(path))
        # include the node itself at the end
        full_path = [ { 'rsid': p.get('rsid'), 'display_name': p.get('display_name'), 'echelon': p.get('echelon') } for p in path ] + [ { 'rsid': node.get('rsid'), 'display_name': node.get('display_name'), 'echelon': node.get('echelon') } ]
        return { 'status': 'ok', 'node': { 'rsid': node.get('rsid'), 'display_name': node.get('display_name'), 'echelon': node.get('echelon') }, 'path': full_path }
    finally:
        conn.close()


@router.get('/cascade')
def cascade(parent_rsid: str = None, echelon: str = None):
    """Return the parent node and its children (sorted by display_name asc).

    If parent_rsid is omitted or null, treat as root (USAREC).
    """
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            # Preferred schema: rsid, display_name, echelon, parent_rsid
            if not parent_rsid:
                cur.execute("SELECT rsid, display_name, echelon, parent_rsid FROM org_unit WHERE rsid = 'USAREC' LIMIT 1")
                p = cur.fetchone()
                if not p:
                    cur.execute("SELECT rsid, display_name, echelon, parent_rsid FROM org_unit WHERE echelon = 'CMD' LIMIT 1")
                    p = cur.fetchone()
                parent = dict(p) if p else { 'rsid': 'USAREC', 'display_name': 'USAREC', 'echelon': 'CMD', 'parent_rsid': None }
            else:
                cur.execute('SELECT rsid, display_name, echelon, parent_rsid FROM org_unit WHERE rsid = ? LIMIT 1', (parent_rsid,))
                p = cur.fetchone()
                if not p:
                    return { 'ok': False, 'error': f'parent {parent_rsid} not found' }
                parent = dict(p)

            if echelon:
                cur.execute('SELECT rsid, display_name, echelon, parent_rsid FROM org_unit WHERE parent_rsid = ? AND (echelon = ? OR echelon IS NULL) ORDER BY display_name COLLATE NOCASE ASC', (parent.get('rsid'), echelon))
            else:
                cur.execute('SELECT rsid, display_name, echelon, parent_rsid FROM org_unit WHERE parent_rsid = ? ORDER BY display_name COLLATE NOCASE ASC', (parent.get('rsid'),))
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            # Fallback schema: name, type, parent_id -> resolve via joins
            if not parent_rsid:
                cur.execute("SELECT id, rsid, name as display_name, type as echelon FROM org_unit WHERE rsid = 'USAREC' LIMIT 1")
                p = cur.fetchone()
                if not p:
                    cur.execute("SELECT id, rsid, name as display_name, type as echelon FROM org_unit WHERE type = 'CMD' LIMIT 1")
                    p = cur.fetchone()
                parent = dict(p) if p else { 'rsid': 'USAREC', 'display_name': 'USAREC', 'echelon': 'CMD', 'parent_rsid': None, 'id': None }
            else:
                cur.execute('SELECT id, rsid, name as display_name, type as echelon FROM org_unit WHERE rsid = ? LIMIT 1', (parent_rsid,))
                p = cur.fetchone()
                if not p:
                    return { 'ok': False, 'error': f'parent {parent_rsid} not found' }
                parent = dict(p)

            pid = parent.get('id')
            if echelon:
                cur.execute('SELECT rsid, name as display_name, type as echelon, parent_id FROM org_unit WHERE parent_id = ? AND (type = ? OR type IS NULL) ORDER BY name COLLATE NOCASE ASC', (pid, echelon))
            else:
                cur.execute('SELECT rsid, name as display_name, type as echelon, parent_id FROM org_unit WHERE parent_id = ? ORDER BY name COLLATE NOCASE ASC', (pid,))
            rows = [dict(r) for r in cur.fetchall()]

        resp = { 'ok': True, 'data': { 'parent': { 'rsid': parent.get('rsid'), 'display_name': parent.get('display_name'), 'echelon': parent.get('echelon'), 'parent_rsid': parent.get('parent_rsid') if parent.get('parent_rsid') else None }, 'children': rows, 'meta': { 'child_echelon': echelon or (rows[0]['echelon'] if rows else None), 'count': len(rows), 'sort': 'display_name_asc' } } }
        return resp
    finally:
        conn.close()


@router.get('/selection/default')
def selection_default():
    conn = connect()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT rsid, display_name, echelon FROM org_unit WHERE rsid = 'USAREC' LIMIT 1")
            r = cur.fetchone()
            if not r:
                cur.execute("SELECT rsid, display_name, echelon FROM org_unit WHERE echelon = 'CMD' LIMIT 1")
                r = cur.fetchone()
            if not r:
                return { 'ok': False, 'error': 'no root unit found' }
            node = dict(r)
            return { 'ok': True, 'data': { 'rsid': node.get('rsid'), 'display_name': node.get('display_name'), 'echelon': node.get('echelon') } }
        except Exception:
            cur.execute("SELECT rsid, name as display_name, type as echelon FROM org_unit WHERE rsid = 'USAREC' LIMIT 1")
            r = cur.fetchone()
            if not r:
                cur.execute("SELECT rsid, name as display_name, type as echelon FROM org_unit WHERE type = 'CMD' LIMIT 1")
                r = cur.fetchone()
            if not r:
                return { 'ok': False, 'error': 'no root unit found' }
            node = dict(r)
            return { 'ok': True, 'data': { 'rsid': node.get('rsid'), 'display_name': node.get('display_name'), 'echelon': node.get('echelon') } }
    finally:
        conn.close()
