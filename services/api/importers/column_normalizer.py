import re

_synonyms = {
    'brigade': 'bde', 'bde': 'bde',
    'battalion': 'bn', 'bn': 'bn',
    'company': 'co', 'co': 'co',
    'station': 'stn', 'stn': 'stn',
    'rsid': 'rsid', 'unit': 'unit', 'unit name': 'unit_name',
    'enlistment': 'enlistments', 'enlistments': 'enlistments',
    'zip code': 'zip', 'zipcode': 'zip', 'zip': 'zip', 'zip5': 'zip', 'cbsa': 'cbsa',
    'urbanicity %': 'urbanicity_pct',
    # event/date fields
    'event_name': 'event_name', 'event title': 'event_name', 'title': 'event_name', 'activity title': 'event_name',
    'start_date': 'start_date', 'start date': 'start_date', 'begin_date': 'start_date', 'begin date': 'start_date',
    'end_date': 'end_date', 'end date': 'end_date',
    # school fields
    'school_name': 'school_name', 'school': 'school_name', 'school id': 'school_id', 'school_id': 'school_id',
    # lead/source/market/mission
    'lead_source': 'lead_source', 'source': 'lead_source', 'market': 'market', 'mission_month': 'mission_month', 'fiscal_year': 'fiscal_year', 'fy': 'fiscal_year',
    # person name fields
    'first_name': 'first_name', 'firstname': 'first_name', 'last_name': 'last_name', 'lastname': 'last_name', 'full_name': 'full_name',
    # rates / population
    'grad_rate': 'grad_rate', 'graduation_rate': 'grad_rate', 'senior_rate': 'senior_rate', 'population': 'population'
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
