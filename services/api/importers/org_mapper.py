from .. import db
import json
import re

def ensure_org_lookup_tables():
    # noop: assume org_unit table exists
    return

def map_row_to_unit(row: dict) -> dict:
    """
    Attempt to map row to unit_key using rsid, stn, co, bn, bde, display_name
    Returns mapping dict: { mapped_unit_key, mapped_echelon_type, mapped_parent_key, mapping_confidence, mapping_method }
    """
    conn = db.connect()
    try:
        cur = conn.cursor()
        # priority: rsid
        rsid = row.get('rsid') or row.get('RSID') or row.get('stn')
        if rsid:
            cur.execute('SELECT unit_key, echelon_type, parent_key FROM org_unit WHERE rsid=? LIMIT 1', (str(rsid).strip(),))
            r = cur.fetchone()
            if r:
                return {'mapped_unit_key': r['unit_key'] if 'unit_key' in r.keys() else r[0], 'mapped_echelon_type': r.get('echelon_type') if 'echelon_type' in r.keys() else r[1], 'mapped_parent_key': r.get('parent_key') if 'parent_key' in r.keys() else r[2], 'mapping_confidence':1.0, 'mapping_method':'RSID_EXACT'}

        # try bn/co/bde exact rsid match
        for key in ('stn','co','bn','bde','unit','unit_name'):
            val = row.get(key)
            if val:
                v = str(val).strip()
                cur.execute('SELECT unit_key, echelon_type, parent_key FROM org_unit WHERE rsid=? OR unit_key=? OR display_name=? LIMIT 1', (v,v,v))
                r = cur.fetchone()
                if r:
                    return {'mapped_unit_key': r['unit_key'] if 'unit_key' in r.keys() else r[0], 'mapped_echelon_type': r.get('echelon_type') if 'echelon_type' in r.keys() else r[1], 'mapped_parent_key': r.get('parent_key') if 'parent_key' in r.keys() else r[2], 'mapping_confidence':0.9, 'mapping_method':'DISPLAY_NAME_MATCH'}

        # fallback: try display_name like match
        name = row.get('unit_name') or row.get('unit')
        if name:
            v = re.sub(r'\s+', ' ', str(name).strip())
            cur.execute("SELECT unit_key, echelon_type, parent_key FROM org_unit WHERE replace(display_name,'  ',' ') LIKE ? LIMIT 2", (v,))
            r = cur.fetchone()
            if r:
                return {'mapped_unit_key': r['unit_key'] if 'unit_key' in r.keys() else r[0], 'mapped_echelon_type': r.get('echelon_type') if 'echelon_type' in r.keys() else r[1], 'mapped_parent_key': r.get('parent_key') if 'parent_key' in r.keys() else r[2], 'mapping_confidence':0.7, 'mapping_method':'DISPLAY_NAME_LIKE'}

        return {'mapped_unit_key': None, 'mapped_echelon_type': None, 'mapped_parent_key': None, 'mapping_confidence':0.0, 'mapping_method':'UNMAPPED'}
    finally:
        conn.close()
