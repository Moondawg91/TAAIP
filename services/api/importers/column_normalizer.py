import re

_synonyms = {
    'brigade': 'bde', 'bde': 'bde',
    'battalion': 'bn', 'bn': 'bn',
    'company': 'co', 'co': 'co',
    'station': 'stn', 'stn': 'stn',
    'rsid': 'rsid', 'unit': 'unit', 'unit name': 'unit_name',
    'enlistment': 'enlistments', 'enlistments': 'enlistments',
    'zip code': 'zip', 'cbsa': 'cbsa',
    'urbanicity %': 'urbanicity_pct'
}

def normalize_col_name(s: str) -> str:
    if s is None: return ''
    v = str(s)
    v = v.replace('\n', ' ')
    v = v.strip().lower()
    v = re.sub(r"[\.,:;()\[\]{}\"']", '', v)
    v = re.sub(r"\s+", ' ', v)
    v = v.replace('&', ' and ')
    # keep %, /, +, -
    if v in _synonyms:
        return _synonyms[v]
    # map word tokens to synonyms if present within
    for k, target in _synonyms.items():
        if k in v.split():
            return target
    return v
