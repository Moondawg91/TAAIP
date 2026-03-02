from typing import List, Dict, Any


def validate_headers(df_headers: List[str], required: List[str], optional: List[str]) -> List[Dict[str, Any]]:
    errors = []
    hdrs = [h.lower().strip() for h in df_headers]
    for r in required:
        if r.lower().strip() not in hdrs:
            errors.append({'row_num': 0, 'column_name': r, 'error_code': 'MISSING_COLUMN', 'message': f'Missing required column: {r}'})
    return errors


def validate_rows(df, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    # placeholder: no per-row validation for now
    return []
