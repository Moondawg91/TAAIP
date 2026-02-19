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


@router.get('/units-summary')
def units_summary():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, type, parent_id, rsid FROM org_unit')
        rows = cur.fetchall()
        data = _rows_to_list(rows)
        tree = _build_tree(data)

        brigades = []
        battalions = []
        companies = []
        stations = []

        # flatten and categorize by rsid-derived prefixes when possible
        for node in data:
            t = (node.get('type') or '').upper()
            rsid = node.get('rsid')
            label = node.get('name') or (rsid or str(node.get('id')))
            if rsid and len(rsid) >= 1:
                bde = rsid[0]
            else:
                bde = None
            if rsid and len(rsid) >= 2:
                bn = rsid[:2]
            else:
                bn = None
            if rsid and len(rsid) >= 3:
                co = rsid[:3]
            else:
                co = None

            if t.startswith('BRIG') or (bde and t == 'ORG'):
                brigades.append({'id': node['id'], 'label': label, 'scope': f'BDE_{bde}' if bde else None})
            elif t.startswith('BATT') or (bn and t == 'ORG'):
                battalions.append({'id': node['id'], 'label': label, 'scope': f'BN_{bn}' if bn else None})
            elif t.startswith('COMP') or (co and t == 'ORG'):
                companies.append({'id': node['id'], 'label': label, 'scope': f'CO_{co}' if co else None})
            elif t.startswith('STAT') or rsid:
                stations.append({'id': node['id'], 'label': label, 'scope': f'STN_{rsid}' if rsid else None})

        # dedupe and filter None scopes
        def uniq_filtered(lst):
            seen = set()
            out = []
            for x in lst:
                s = x.get('scope')
                if not s: continue
                if s in seen: continue
                seen.add(s)
                out.append(x)
            return out

        return {"status": "ok", "data": {"usarec": True, "brigades": uniq_filtered(brigades), "battalions": uniq_filtered(battalions), "companies": uniq_filtered(companies), "stations": uniq_filtered(stations)}}
    finally:
        conn.close()
