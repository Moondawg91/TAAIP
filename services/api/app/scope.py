from datetime import date, datetime
from typing import Dict, List, Any


def compute_current_fy(today: date) -> int:
    # FY starts Oct 1. If month >= Oct -> FY = year+1? Actually Oct-Dec belong to FY of next calendar year.
    # Example: 2025-10 -> FY 2026
    if today.month >= 10:
        return today.year + 1
    return today.year


def compute_current_qtr_num(today: date) -> int:
    m = today.month
    if m >= 10 or m <= 12:
        # Oct-Dec -> Q1
        if m >= 10 and m <= 12:
            return 1
    if 1 <= m <= 3:
        return 2
    if 4 <= m <= 6:
        return 3
    return 4


def compute_current_rsm_month(today: date) -> str:
    return f"{today.year:04d}-{today.month:02d}"


def qtr_months(fy: int, qtr_num: int) -> List[str]:
    # FY-based quarters: Q1 = Oct-Dec of previous calendar year, Q2 = Jan-Mar of FY, Q3 = Apr-Jun, Q4 = Jul-Sep
    if qtr_num == 1:
        year = fy - 1
        months = [f"{year:04d}-10", f"{year:04d}-11", f"{year:04d}-12"]
    elif qtr_num == 2:
        year = fy
        months = [f"{year:04d}-01", f"{year:04d}-02", f"{year:04d}-03"]
    elif qtr_num == 3:
        year = fy
        months = [f"{year:04d}-04", f"{year:04d}-05", f"{year:04d}-06"]
    else:
        year = fy
        months = [f"{year:04d}-07", f"{year:04d}-08", f"{year:04d}-09"]
    return months


def _parse_ym(s: str) -> str:
    # Accept YYYY-MM or YYYY/MM or YYYYMM or YYYY-M
    if not s:
        return None
    try:
        s = str(s).strip()
        if '-' in s:
            parts = s.split('-')
        elif '/' in s:
            parts = s.split('/')
        else:
            # YYYYMM
            if len(s) == 6:
                return f"{s[0:4]}-{s[4:6]}"
            return None
        if len(parts) >= 2:
            y = int(parts[0])
            m = int(parts[1])
            return f"{y:04d}-{m:02d}"
    except Exception:
        return None
    return None


def _qtr_from_month_str(ym: str) -> int:
    try:
        parts = ym.split('-')
        y = int(parts[0]); m = int(parts[1])
        if m >= 10 or m <= 12:
            return 1
        if 1 <= m <= 3:
            return 2
        if 4 <= m <= 6:
            return 3
        return 4
    except Exception:
        return None


def normalize_unit(unit_rsid: Any) -> str:
    if not unit_rsid:
        return 'USAREC'
    return str(unit_rsid)


def parse_scope_params(query) -> Dict[str, Any]:
    """
    Accepts a dict-like of query params (e.g., FastAPI Request.query_params) and returns parsed scope.
    Returns keys: unit_rsid, fy, qtr_num, rsm_month, rollup
    """
    today = date.today()
    unit = normalize_unit(query.get('unit_rsid') if hasattr(query, 'get') else query.get('unit_rsid') if isinstance(query, dict) else None)
    # fy
    fy = None
    try:
        if hasattr(query, 'get'):
            v = query.get('fy')
        else:
            v = query.get('fy')
        if v is not None and v != '':
            fy = int(v)
    except Exception:
        fy = None
    if fy is None:
        fy = compute_current_fy(today)

    # qtr_num
    qtr = None
    try:
        if hasattr(query, 'get'):
            v = query.get('qtr_num') or query.get('qtr')
        else:
            v = query.get('qtr_num') or query.get('qtr')
        if v is not None and v != '':
            qtr = int(v)
    except Exception:
        qtr = None
    if qtr is None:
        qtr = compute_current_qtr_num(today)

    # rsm_month (alias month)
    rsm = None
    try:
        if hasattr(query, 'get'):
            v = query.get('rsm_month') or query.get('month')
        else:
            v = query.get('rsm_month') or query.get('month')
        rsm = _parse_ym(v) if v else None
    except Exception:
        rsm = None
    if rsm is None:
        rsm = compute_current_rsm_month(today)

    # rollup default
    roll = 1 if unit == 'USAREC' else 0
    try:
        if hasattr(query, 'get'):
            v = query.get('rollup')
        else:
            v = query.get('rollup')
        if v is not None and v != '':
            rv = int(v)
            roll = 1 if rv else 0
    except Exception:
        pass

    return {'unit_rsid': unit, 'fy': fy, 'qtr_num': qtr, 'rsm_month': rsm, 'rollup': roll}
