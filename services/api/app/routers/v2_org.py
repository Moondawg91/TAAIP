
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from ..db import connect
from .. import org_utils
from ..services.org_unit_resolver import resolve_subordinate_units
# fallback static hierarchy when DB lacks full USAREC entries
from database import rsid_hierarchy
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
def children(unit_rsid: str = 'USAREC', parent_rsid: Optional[str] = None, echelon: Optional[str] = None, user: dict = Depends(require_perm('dashboards.view'))):
    conn = connect()
    try:
        # accept either `unit_rsid` (legacy) or `parent_rsid` (frontend callers)
        rsid = parent_rsid or unit_rsid or 'USAREC'
        kids = org_utils.get_children(conn, rsid)
        # apply echelon filter if provided
        try:
            if echelon and kids:
                kids = [k for k in (kids or []) if (str(k.get('echelon') or k.get('type') or '').upper() == str(echelon).upper())]
        except Exception:
            pass
        # normalize child objects to include a `display_name` field used by older frontends
        try:
            norm = []
            for k in (kids or []):
                dk = dict(k)
                dk['display_name'] = dk.get('display_name') or dk.get('unit_name') or dk.get('name') or dk.get('rsid') or dk.get('unit_key')
                norm.append(dk)
            kids = norm
        except Exception:
            pass
        # If DB has no children for this node, provide a static fallback
        if not kids:
            try:
                # use the resolved rsid (may be from parent_rsid or unit_rsid)
                resolved = str(rsid)
                # helper: if a battalion id (e.g., '1BN') is supplied, resolve its brigade
                def _find_brigade_for_battalion(bn_id):
                    try:
                        for bkey, bdata in rsid_hierarchy.USAREC_HIERARCHY['USAREC']['brigades'].items():
                            if isinstance(bdata.get('battalions'), dict) and bn_id in bdata.get('battalions'):
                                return bkey
                    except Exception:
                        pass
                    return None
                # if resolved looks like a battalion id, map to brigade-bn
                if resolved.endswith('BN'):
                    br_for_bn = _find_brigade_for_battalion(resolved)
                    if br_for_bn:
                        resolved = f"{br_for_bn}-{resolved}"
                # Top-level USAREC -> brigades
                if (not echelon and resolved.upper() == 'USAREC') or (echelon and str(echelon).upper() == 'BDE' and resolved.upper() == 'USAREC'):
                    brs = rsid_hierarchy.get_all_brigades()
                    kids = [ { 'unit_rsid': b, 'unit_name': rsid_hierarchy.USAREC_HIERARCHY['USAREC']['brigades'][b]['name'], 'display_name': rsid_hierarchy.USAREC_HIERARCHY['USAREC']['brigades'][b]['name'], 'echelon': 'BDE' } for b in brs ]
                else:
                    parts = resolved.split('-')
                    # brigade -> battalions
                    if (not echelon and len(parts) == 1) or (echelon and str(echelon).upper() == 'BN' and len(parts) == 1):
                        bds = rsid_hierarchy.get_battalions_for_brigade(resolved)
                        kids = [ { 'unit_rsid': bn, 'unit_name': rsid_hierarchy.USAREC_HIERARCHY['USAREC']['brigades'].get(resolved, {}).get('battalions', {}).get(bn, {}).get('name') or bn, 'display_name': rsid_hierarchy.USAREC_HIERARCHY['USAREC']['brigades'].get(resolved, {}).get('battalions', {}).get(bn, {}).get('name') or bn, 'echelon': 'BN' } for bn in bds ]
                    # battalion -> companies (synthesized) OR battalion -> stations when asked for STN
                    elif len(parts) == 2:
                        brigade = parts[0]
                        bn = parts[1]
                        # if caller requested CO, synthesize a single 'All Companies' CO
                        if echelon and str(echelon).upper() == 'CO':
                            kids = [ { 'unit_rsid': f"{brigade}-{bn}-CO", 'unit_name': 'All Companies', 'display_name': 'All Companies', 'echelon': 'CO' } ]
                        else:
                            # return stations for the battalion
                            sts = rsid_hierarchy.get_stations_for_battalion(brigade, bn)
                            kids = [ { 'unit_rsid': f"{brigade}-{bn}-{s}", 'unit_name': f"Station {s}", 'display_name': f"Station {s}", 'echelon': 'STN' } for s in sts ]
                    # synthetic CO node -> stations
                    elif len(parts) >= 3 and str(parts[2]).upper().startswith('CO'):
                        brigade = parts[0]
                        bn = parts[1]
                        sts = rsid_hierarchy.get_stations_for_battalion(brigade, bn)
                        kids = [ { 'unit_rsid': f"{brigade}-{bn}-{s}", 'unit_name': f"Station {s}", 'display_name': f"Station {s}", 'echelon': 'STN' } for s in sts ]
            except Exception:
                # keep kids as empty list on any error
                kids = kids or []
        # normalize children to include `rsid`, `display_name`, and `echelon` keys expected by frontend
        try:
            norm = []
            for k in (kids or []):
                dk = dict(k)
                # ensure rsid exists for frontend components
                dk['rsid'] = dk.get('rsid') or dk.get('unit_rsid') or dk.get('unit_key') or dk.get('unitKey')
                dk['display_name'] = dk.get('display_name') or dk.get('unit_name') or dk.get('name') or dk.get('rsid')
                dk['echelon'] = dk.get('echelon') or dk.get('type') or dk.get('echelon_type')
                norm.append(dk)
            kids = norm
        except Exception:
            pass

        # finally, if an echelon was requested, try to ensure returned items match that echelon
        try:
            if echelon:
                kids = [k for k in (kids or []) if (not k.get('echelon')) or (str(k.get('echelon')).upper() == str(echelon).upper())]
        except Exception:
            pass

        return {'unit_rsid': rsid, 'children': kids}
    finally:
        conn.close()


@router.get('/descendants')
def descendants(unit_rsid: str = 'USAREC', depth: int = 50, user: dict = Depends(require_perm('dashboards.view'))):
    rs = resolve_subordinate_units(unit_rsid)
    return {'unit_rsid': unit_rsid, 'descendants': rs}



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


@router.get('/root')
def root_compat():
    """Compatibility endpoint for older UI expecting `/api/v2/org/root`.

    Returns: { brigades: [...] } or minimal shape the frontend expects.
    """
    try:
        r = roots() or {}
        # roots() returns { 'status':'ok', 'roots': [...] }
        items = r.get('roots') if isinstance(r, dict) and 'roots' in r else (r if isinstance(r, list) else [])
        # if DB returned no roots, provide static USAREC brigade list
        if not items:
            try:
                brs = rsid_hierarchy.get_all_brigades()
                items = [ { 'rsid': b, 'unit_key': b, 'display_name': rsid_hierarchy.USAREC_HIERARCHY['USAREC']['brigades'][b]['name'], 'echelon': 'BDE' } for b in brs ]
            except Exception:
                items = []
        return { 'brigades': items }
    except Exception:
        return { 'brigades': [] }


@router.get('/units')
def units_compat(parent_key: str = None, echelon: str = None):
    """Compatibility endpoint for `/api/v2/org/units?parent_key=...&echelon=...` used by the UI.

    Returns: { units: [...] }
    """
    try:
        # prefer children() which returns {'unit_rsid':..., 'children': [...]}
        pk = parent_key or None
        if not pk:
            # no parent specified: return top-level roots as units
            r = roots() or {}
            items = r.get('roots') if isinstance(r, dict) and 'roots' in r else (r if isinstance(r, list) else [])
            return { 'units': items }
        else:
            resp = children(unit_rsid=pk)
            kids = resp.get('children') if isinstance(resp, dict) and 'children' in resp else (resp or [])
            # apply echelon filter if provided
            if echelon:
                kids = [k for k in kids if (k.get('echelon') or '').upper() == str(echelon).upper()]
            # normalize to units array with rsid/unit_key/display_name fields
            out = []
            for k in kids:
                item = {}
                # prefer unit_key/display_name fields if present
                item['rsid'] = k.get('rsid') or k.get('unit_rsid')
                item['unit_key'] = item['rsid']
                item['display_name'] = k.get('display_name') or k.get('unit_name') or k.get('name') or item['rsid']
                item['echelon'] = k.get('echelon') or k.get('type')
                out.append(item)
            return { 'units': out }
    except Exception:
        return { 'units': [] }
