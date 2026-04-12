"""In-memory store for commander intent ingestion (minimal persistence).

This is deliberately simple and process-local. Later we will persist to DB.
"""

CURRENT_ROP = {}
CURRENT_SCHOOL_PLAN = {}


def save_rop(payload: dict):
    global CURRENT_ROP
    # store a shallow copy to avoid external mutation
    CURRENT_ROP = dict(payload or {})
    return CURRENT_ROP


def save_school_plan(payload: dict):
    global CURRENT_SCHOOL_PLAN
    CURRENT_SCHOOL_PLAN = dict(payload or {})
    return CURRENT_SCHOOL_PLAN


def _unique_list(a):
    if not a:
        return []
    seen = set()
    out = []
    for v in a:
        if v is None:
            continue
        key = str(v).strip()
        if not key:
            continue
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def get_current_intent():
    rop = dict(CURRENT_ROP or {})
    school = dict(CURRENT_SCHOOL_PLAN or {})

    merged = {
        'loes': _unique_list((rop.get('loes') or []) + (school.get('loes') or [])),
        'priorities': _unique_list((rop.get('priorities') or []) + (school.get('priorities') or [])),
        'focus_markets': _unique_list((rop.get('focus_markets') or []) + (school.get('focus_markets') or [])),
        'target_population': _unique_list((rop.get('target_population') or []) + (school.get('target_population') or [])),
    }

    return {
        'commander_intent_loaded': bool(rop or school),
        'fy': rop.get('fy') or school.get('fy'),
        'rop': rop,
        'school_plan': school,
        'merged': merged,
    }
