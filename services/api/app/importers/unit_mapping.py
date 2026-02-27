"""Unit mapping helpers for Data Hub importer pipeline.

Attempts to resolve a unit RSID from common row fields. Uses a sequence
of heuristics: direct RSID, station fields, CBSA match, ZIP match, and
finally a fuzzy match against `org_unit.name`.
"""
from typing import Tuple, Any, Optional
import difflib
from .. import db as _db


# simple in-memory cache to avoid querying org_unit repeatedly
_ORG_UNIT_NAME_CACHE = None


def _build_org_unit_cache():
    global _ORG_UNIT_NAME_CACHE
    if _ORG_UNIT_NAME_CACHE is not None:
        return _ORG_UNIT_NAME_CACHE
    conn = _db.connect()
    cur = conn.cursor()
    cur.execute("SELECT rsid, name, cbsa, location_zip FROM org_unit WHERE rsid IS NOT NULL")
    rows = cur.fetchall()
    mapping = {'by_name': {}, 'names': [], 'by_cbsa': {}, 'by_zip': {}}
    for r in rows:
        rsid = r.get('rsid')
        name = (r.get('name') or '').strip()
        cbsa = r.get('cbsa')
        zipc = r.get('location_zip')
        if name:
            mapping['by_name'][name.lower()] = rsid
            mapping['names'].append(name)
        if cbsa:
            mapping['by_cbsa'].setdefault(str(cbsa).strip(), []).append(rsid)
        if zipc:
            mapping['by_zip'].setdefault(str(zipc).strip(), []).append(rsid)
    _ORG_UNIT_NAME_CACHE = mapping
    return mapping


def map_unit_rsid(row: dict) -> Tuple[Optional[str], float, str]:
    """Return (unit_rsid or None, confidence 0.0-1.0, reason)

    Heuristics applied in order with decreasing confidence:
    - direct 'rsid' / 'unit_rsid' / 'station_rsid'
    - CBSA code exact match to org_unit.cbsa
    - ZIP exact match to org_unit.location_zip
    - fuzzy match on org_unit.name using difflib
    """
    # 1) direct keys
    for key in ('rsid', 'unit_rsid', 'station_rsid', 'station'):
        v = row.get(key)
        if v:
            return (str(v).strip(), 1.0, f'direct:{key}')

    # build cache once
    cache = _build_org_unit_cache()

    # 2) cbsa
    for key in ('cbsa', 'cbsa_code'):
        v = row.get(key)
        if v:
            vstr = str(v).strip()
            rsids = cache['by_cbsa'].get(vstr)
            if rsids:
                return (rsids[0], 0.9, f'cbsa:{vstr}')

    # 3) zip
    for key in ('zip', 'zipcode', 'postalcode'):
        v = row.get(key)
        if v:
            vstr = str(v).strip()
            rsids = cache['by_zip'].get(vstr)
            if rsids:
                return (rsids[0], 0.75, f'zip:{vstr}')

    # 4) try bde/bn/company names (explicit short names)
    names = []
    for key in ('bde', 'bn', 'company', 'co', 'unit', 'station_name'):
        v = row.get(key)
        if v:
            names.append(str(v).strip())
    if names:
        for n in names:
            # direct LIKE match via SQL as fallback
            conn = _db.connect()
            cur = conn.cursor()
            try:
                cur.execute("SELECT rsid FROM org_unit WHERE lower(name) LIKE ? LIMIT 1", (f"%{n.lower()}%",))
                r = cur.fetchone()
                if r and r.get('rsid'):
                    return (r['rsid'], 0.8, f'name_like:{n}')
            except Exception:
                pass

    # 5) fuzzy name match against cache names (use difflib)
    candidates = cache.get('names', [])
    if candidates:
        # create lower-cased mapping for matching
        lower_to_orig = {c.lower(): c for c in candidates}
        # create a single searchable string list
        keys = list(lower_to_orig.keys())
        # look at likely fields in row
        search_texts = []
        for k in ('organization', 'org', 'name', 'unit_name', 'station'):
            v = row.get(k)
            if v:
                search_texts.append(str(v).strip().lower())
        # include joined bde/bn if present
        search_text = ' '.join(search_texts)
        if search_text:
            matches = difflib.get_close_matches(search_text, keys, n=3, cutoff=0.65)
            if matches:
                best = matches[0]
                orig = lower_to_orig.get(best)
                rsid = cache['by_name'].get(best)
                if rsid:
                    # confidence scaled from similarity
                    sim = difflib.SequenceMatcher(None, search_text, best).ratio()
                    conf = max(0.5, min(0.9, sim))
                    return (rsid, conf, f'fuzzy_name:{orig}:{sim:.2f}')

    return (None, 0.0, 'unmapped')
