from typing import Dict, List, Any, Tuple
from datetime import datetime
from ..db import connect


COMMON_FILTER_KEYS = ['fy', 'qtr', 'month', 'echelon_type', 'unit_value', 'funding_line', 'component']


def apply_common_filters(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Return a normalized filters dict containing only recognized keys."""
    filters = {}
    for k in COMMON_FILTER_KEYS:
        v = query_params.get(k)
        if v is not None:
            # try to coerce numeric keys
            try:
                if k in ('fy', 'month'):
                    filters[k] = int(v)
                else:
                    filters[k] = v
            except Exception:
                filters[k] = v
    return filters


def build_empty_rollup_contract(filters: Dict[str, Any], kpi_keys: List[str], breakdown_keys: List[str], trend_keys: List[str]) -> Dict[str, Any]:
    """Construct an empty rollup contract with zeros/empty arrays and missing_data list."""
    kpis = {k: 0 for k in kpi_keys}
    breakdowns = {bk: [] for bk in breakdown_keys}
    trends = {tk: [] for tk in trend_keys}
    return {
        'status': 'ok',
        'data_as_of': None,
        'filters': filters,
        'kpis': kpis,
        'breakdowns': breakdowns,
        'trends': trends,
        'missing_data': []
    }


def safe_table_exists(conn, table_name: str) -> bool:
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        r = cur.fetchone()
        return bool(r)
    except Exception:
        return False


def safe_column_exists(conn, table: str, column: str) -> bool:
    try:
        cur = conn.cursor()
        cur.execute(f'PRAGMA table_info("{table}")')
        rows = cur.fetchall()
        for r in rows:
            # r may be dict-like
            name = r.get('name') if isinstance(r, dict) else r[1]
            if name == column:
                return True
        return False
    except Exception:
        return False
