from fastapi import APIRouter
from ..db import connect

router = APIRouter(prefix="/v2/org", tags=["org"])


def _rows_to_list(rows):
    return [dict(r) for r in rows]


def _build_tree(rows):
    # rows: list of dicts with id, name, type, parent_id, rsid
    by_id = {r['id']: dict(r, children=[]) for r in rows}
    roots = []
    for r in by_id.values():
        pid = r.get('parent_id')
        if pid and pid in by_id:
            by_id[pid]['children'].append(r)
        else:
            roots.append(r)
    return roots


def _first_station_rsid(node):
    # DFS to find a station rsid in subtree
    if node.get('rsid'):
        return node['rsid']
    for c in node.get('children', []):
        v = _first_station_rsid(c)
        if v:
            return v
    return None


def _canonical_unit_key(rsid, echelon_hint=None):
    """Return a canonical unit_key for the UI while preserving the original rsid.

    - For brigade rsids that are simple integers (e.g. '1'), return 'B001'.
    - If rsid already looks canonical (starts with 'B' followed by digits), return as-is.
    - Otherwise return the rsid unchanged.
    """
    if not rsid:
        return None
    s = str(rsid).upper()
    # already canonical brigade form like B001
    if s.startswith('B') and s[1:].isdigit():
        return s
    # if echelon explicitly BDE, and rsid is numeric, format as B###
    if echelon_hint and echelon_hint.upper() == 'BDE' and s.isdigit():
        return f"B{int(s):03d}"
    # fallback: if rsid is a single digit and likely a brigade, format it
    if s.isdigit() and len(s) <= 2:
        return f"B{int(s):03d}"
    return s


@router.get('/units-summary')
def units_summary():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, display_name, type, echelon, parent_id, parent_rsid, rsid FROM org_unit')
        rows = cur.fetchall()
        data = _rows_to_list(rows)
        tree = _build_tree(data)

        brigades = []
        battalions = []
        companies = []
        stations = []
        root = None

        # flatten and categorize by rsid-derived prefixes when possible
        for node in data:
            # prefer explicit `echelon` column, fall back to legacy `type`
            t = (node.get('echelon') or node.get('type') or '').upper()
            rsid = node.get('rsid')
            # prefer display_name when present
            label = node.get('display_name') or node.get('name') or (rsid or str(node.get('id')))
            # compute a canonical unit_key for UI while preserving original rsid
            unit_key = _canonical_unit_key(rsid, t) or f"id:{node.get('id')}"
            parent_key = node.get('parent_rsid') or None
            echelon_type = None
            # Detect root (command-level) explicitly and keep it out of other lists
            if t == 'CMD' or (rsid and str(rsid).upper() == 'USAREC'):
                echelon_type = 'CMD'
                root = {'id': node['id'], 'unit_key': unit_key, 'rsid': rsid, 'display_name': label, 'echelon_type': echelon_type, 'parent_key': parent_key}
                # don't append to other category lists
                continue

            if t.startswith('BRIG') or t == 'BDE' or (rsid and rsid.startswith('B')):
                echelon_type = 'BDE'
                brigades.append({'id': node['id'], 'unit_key': unit_key, 'rsid': rsid, 'display_name': label, 'echelon_type': echelon_type, 'parent_key': parent_key})
            elif t.startswith('BATT') or t == 'BN' or (rsid and len(rsid) >= 2 and rsid[1].isdigit()):
                echelon_type = 'BN'
                battalions.append({'id': node['id'], 'unit_key': unit_key, 'rsid': rsid, 'display_name': label, 'echelon_type': echelon_type, 'parent_key': parent_key})
            elif t.startswith('COMP') or t == 'CO' or (rsid and len(rsid) >= 3 and rsid[2].isdigit()):
                    echelon_type = 'CO'
                    companies.append({'id': node['id'], 'unit_key': unit_key, 'rsid': rsid, 'display_name': label, 'echelon_type': echelon_type, 'parent_key': parent_key})
            else:
                # Treat explicit STN/Station echelon as stations; otherwise default to station
                if t.startswith('STN') or t == 'STN':
                    echelon_type = 'STN'
                    stations.append({'id': node['id'], 'unit_key': unit_key, 'rsid': rsid, 'display_name': label, 'echelon_type': echelon_type, 'parent_key': parent_key})
                else:
                    # fallback: treat as station if nothing else matches, but ensure USAREC was handled above
                    echelon_type = 'STN'
                    stations.append({'id': node['id'], 'unit_key': unit_key, 'rsid': rsid, 'display_name': label, 'echelon_type': echelon_type, 'parent_key': parent_key})

        # dedupe and filter None scopes
        def uniq_by_unitkey(lst):
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
        # normalize `root` to an rsid string for subsequent queries
        if isinstance(root, dict):
            root_rsid = root.get('rsid')
        else:
            root_rsid = root
        if not root_rsid:
            root_rsid = 'USAREC'

        cur.execute('SELECT rsid, display_name, echelon, parent_rsid, unit_key FROM org_unit WHERE rsid = ? LIMIT 1', (root_rsid,))
        r = cur.fetchone()
        if not r:
            return {"status": "error", "message": f"root {root_rsid} not found"}
        root_node = dict(r)

        # fetch direct children of the root (likely BDEs)
        cur.execute('SELECT rsid, display_name, echelon, parent_rsid, unit_key, id FROM org_unit WHERE parent_rsid = ? ORDER BY id ASC', (root_rsid,))
        children = [dict(x) for x in cur.fetchall()]

        # heuristics for BDE detection similar to units_summary
        def is_bde(node):
            t = (node.get('echelon') or '').upper()
            rsid = node.get('rsid') or ''
            return t == 'BDE' or t.startswith('BRIG') or (rsid and rsid.isdigit()) or (rsid and rsid.upper().startswith('B'))

        bdes = [ { 'rsid': c.get('rsid'), 'unit_key': c.get('unit_key'), 'display_name': c.get('display_name'), 'echelon': c.get('echelon'), 'parent_rsid': c.get('parent_rsid') } for c in children if is_bde(c) ]

        # sort BDEs by numeric part of unit_key if present, else by rsid
        def bde_sort_key(x):
            uk = (x.get('unit_key') or '').upper()
            if uk.startswith('B') and uk[1:].isdigit():
                return int(uk[1:])
            try:
                return int(x.get('rsid'))
            except Exception:
                return x.get('rsid') or ''

        bdes = sorted(bdes, key=bde_sort_key)

        resp = {
            'status': 'ok',
            'data': {
                'root': { 'rsid': root_node.get('rsid'), 'display_name': root_node.get('display_name'), 'echelon': root_node.get('echelon') },
                'levels': { 'bde': bdes, 'bn': [], 'co': [], 'stn': [] },
                'selected': { 'root_rsid': root_node.get('rsid'), 'bde_rsid': None, 'bn_rsid': None, 'co_rsid': None, 'stn_rsid': None }
            }
        }
        return resp
    finally:
        conn.close()


def _compute_sort_order(row):
    # Prefer numeric ordering for canonical brigade unit_keys like B001
    uk = (row.get('unit_key') or '').upper()
    rsid = row.get('rsid') or ''
    if uk.startswith('B') and uk[1:].isdigit():
        try:
            return int(uk[1:])
        except Exception:
            pass
    # fallback to numeric rsid if possible
    if rsid.isdigit():
        try:
            return int(rsid)
        except Exception:
            pass
    # final fallback: alphabetical by display_name
    return (row.get('display_name') or '').upper()


@router.get('/children')
def children(parent_key: str = None, parent_rsid: str = None, echelon: str = None):
    """Return children for a given parent. Backwards compatible with `parent_rsid`.

    New preferred parameter is `parent_key` (the canonical `unit_key`). If provided
    we resolve it to the parent's `rsid` and query children by `parent_rsid`.
    Responses include `sort_order` which callers can use for deterministic ordering.
    """
    conn = connect()
    try:
        cur = conn.cursor()

        # resolve parent_rsid if caller provided parent_key
        if parent_key and not parent_rsid:
            cur.execute('SELECT rsid FROM org_unit WHERE unit_key = ? LIMIT 1', (parent_key,))
            p = cur.fetchone()
            if p:
                parent_rsid = dict(p).get('rsid')

        if not parent_rsid:
            return { 'status': 'error', 'message': 'missing parent_key or parent_rsid' }

        try:
            cur.execute('SELECT rsid, display_name, echelon, parent_rsid, unit_key, id FROM org_unit WHERE parent_rsid = ? ORDER BY id ASC', (parent_rsid,))
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            # Fallback for legacy schema where `display_name` or `parent_rsid` column may not exist.
            # Resolve parent_rsid -> parent_id first, then query by parent_id and map `name` -> `display_name`.
            try:
                cur.execute('SELECT id FROM org_unit WHERE rsid = ? LIMIT 1', (parent_rsid,))
                p = cur.fetchone()
                pid = dict(p).get('id') if p else None
                if pid:
                    cur.execute('SELECT rsid, name as display_name, type as echelon, parent_id FROM org_unit WHERE parent_id = ? ORDER BY name COLLATE NOCASE ASC', (pid,))
                    rows = [dict(r) for r in cur.fetchall()]
                else:
                    rows = []
            except Exception:
                rows = []

        # compute sort_order per row and then sort
        for r in rows:
            r['sort_order'] = _compute_sort_order(r)

        # if numeric sort_order present, sort numerically then by display_name
        def sort_key(x):
            so = x.get('sort_order')
            if isinstance(so, int):
                return (0, so, (x.get('display_name') or '').upper())
            return (1, str(so), (x.get('display_name') or '').upper())

        rows_sorted = sorted(rows, key=sort_key)

        items = [ { 'rsid': r.get('rsid'), 'unit_key': r.get('unit_key'), 'display_name': r.get('display_name'), 'echelon': r.get('echelon'), 'parent_key': r.get('parent_rsid'), 'sort_order': r.get('sort_order') } for r in rows_sorted ]
        return { 'status': 'ok', 'parent_key': parent_key or parent_rsid, 'children': items }
    finally:
        conn.close()


@router.get('/roots')
def roots():
    """Return top-level roots (units without a parent)."""
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
