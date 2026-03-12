import json
from typing import List, Tuple, Dict, Any


def detect_dataset(filename: str, sheet_names: List[str], headers: List[str], registry_rows: List[Dict[str, Any]], hint: str = None) -> Tuple[str, float, str]:
    """Return (dataset_key, confidence, matched_on)
    registry_rows: list of dicts from dataset_registry table
    """
    # if hint provided and matches an enabled registry entry, prefer it
    if hint:
        for r in registry_rows:
            if r.get('dataset_key') == hint and int(r.get('enabled', 1)) == 1:
                return hint, 1.0, 'hint'

    # Special-case: USAREC org hierarchy by exact headers or filename
    try:
        hdrs_norm = [h.strip().upper() for h in (headers or []) if isinstance(h, str)]
        if set(['CMD', 'BDE', 'BN', 'CO', 'STN']).issubset(set(hdrs_norm)):
            return 'USAREC_ORG_HIERARCHY', 1000.0, 'headers:usarec_org'
    except Exception:
        pass
    try:
        fname = (filename or '').lower()
        if 'rsid' in fname and 'usarec' in fname:
            return 'USAREC_ORG_HIERARCHY', 1000.0, 'filename:usarec_rsid'
    except Exception:
        pass

    fname = (filename or '').lower()
    stext = ' '.join([s.lower() for s in (sheet_names or [])])
    headers_text = ' '.join([h.lower() for h in (headers or [])])

    best = (None, 0.0, '')
    # lower-case header blob for special-case checks
    headers_blob = headers_text
    for r in registry_rows:
        if int(r.get('enabled', 1)) != 1:
            continue
        keywords = []
        try:
            keywords = json.loads(r.get('detection_keywords') or '[]')
        except Exception:
            pass
        score = 0.0
        for kw in keywords:
            k = kw.lower()
            if k in fname:
                score += 3.0
            if k in stext:
                score += 2.0
            if k in headers_blob:
                score += 1.5
        # header matches for required columns (weighted)
        try:
            required = json.loads(r.get('required_columns') or '[]')
        except Exception:
            required = []
        req_found = 0
        for req in required:
            if req.lower() in headers_blob:
                req_found += 1
        if required:
            score += (float(req_found) / max(1.0, len(required))) * 5.0

        # Special-case priority: when battalion-like header tokens present, boost BN datasets
        if ('lu_battalion' in headers_blob or 'lu_battalion_name' in headers_blob or "'demographic data'" in headers_blob or 'battalion' in headers_blob):
            dk = (r.get('dataset_key') or '').upper()
            if dk.find('_BN') >= 0 or 'bn' in (','.join(keywords)).lower() or 'battalion' in (','.join(keywords)).lower():
                score += 2.0

        conf = min(1.0, score / 8.0)
        if conf > best[1]:
            best = (r.get('dataset_key'), conf, 'keywords')

    if best[0]:
        return best
    return None, 0.0, ''
