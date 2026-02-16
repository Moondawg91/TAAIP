import io
import json
import sqlite3
import re
from typing import Dict, Any, Tuple, List

import pandas as pd
from difflib import get_close_matches

from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "taaip_service.py"


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def detect_table(file_bytes: bytes, filename: str, max_scan_rows: int = 60) -> Dict[str, Any]:
    """Detect header row and table bounds. Returns dict with sheet, header_row, headers, data_df."""
    fname = filename.lower()
    if fname.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_bytes), header=None, dtype=str, keep_default_na=False)
        sheets = {"sheet1": df}
    else:
        xls = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None, dtype=str)
        # pick first sheet
        first = next(iter(xls.keys()))
        sheets = {first: xls[first]}

    best = None
    for sheet_name, df in sheets.items():
        nrows = min(len(df), max_scan_rows)
        for ridx in range(nrows):
            row = df.iloc[ridx].fillna('').astype(str).tolist()
            non_empty = [c for c in row if c and c.strip()]
            non_empty_count = len(non_empty)
            if non_empty_count == 0:
                score = 0
            else:
                strings = sum(0 if _is_number(c.replace(',', '')) else 1 for c in non_empty)
                fraction_strings = strings / non_empty_count
                uniqueness = len(set(non_empty)) / non_empty_count
                score = non_empty_count * 0.4 + fraction_strings * 0.3 + uniqueness * 0.3
            if best is None or score > best[0]:
                best = (score, sheet_name, ridx, df)

    if best is None:
        raise ValueError("No table detected")

    _, sheet_name, header_row, df = best
    # build data frame from header_row+1 onward
    header = df.iloc[header_row].fillna('').astype(str).tolist()
    data = df.iloc[header_row + 1 :].copy()
    data.columns = header
    data = data.reset_index(drop=True)
    return {
        "sheet": sheet_name,
        "header_row": int(header_row),
        "headers": header,
        "data": data,
    }


def normalize_header(h: str) -> str:
    h = (h or '').strip()
    h = re.sub(r"[\r\n\t]", ' ', h)
    h = re.sub(r"[^0-9A-Za-z]+", '_', h)
    h = re.sub(r"_+", '_', h)
    return h.strip('_').lower()


def classify_dataset(headers: List[str]) -> Tuple[str, float]:
    H = [h.upper() for h in headers]
    # Simple deterministic rules first
    if any('ZIP' in h for h in H) and any('CATEGORY' in h for h in H) and any('SHARE' in h for h in H):
        return 'USAREC_ZIP_CATEGORY_REPORT', 0.95
    if any('SERVICE' in h for h in H) and any('STN' in h for h in H) and any('CONTRACT' in h for h in H) and any('SHARE' in h for h in H):
        return 'USAREC_MARKET_CONTRACTS_SHARE', 0.95
    if any('ORG' in h for h in H) and any('STN' in h for h in H) and any('ZIP' in h for h in H) and any('SERVICE' in h for h in H):
        return 'DOD_STN_ZIP_SERVICE_LOOKUP', 0.9
    return 'UNKNOWN', 0.2


def fuzzy_map_headers(headers: List[str], synonyms: Dict[str, List[str]]) -> Dict[str, str]:
    """Return mapping canonical_field -> source_column (or None if not found)"""
    norm_headers = {normalize_header(h): h for h in headers}
    result = {}
    header_keys = list(norm_headers.keys())
    for can_field, syns in synonyms.items():
        # build candidate list lowercased
        candidates = [s.lower() for s in syns]
        # exact match
        match = None
        for hk in header_keys:
            if hk in candidates or hk == can_field.lower() or hk.replace('_', '') == can_field.lower().replace('_', ''):
                match = norm_headers[hk]
                break
        if not match:
            # fuzzy
            best = None
            for hk in header_keys:
                matches = get_close_matches(hk, candidates, n=1, cutoff=0.8)
                if matches:
                    best = hk
                    break
            if best:
                match = norm_headers[best]
        result[can_field] = match
    return result


def save_raw_rows(conn: sqlite3.Connection, batch_id: str, df: pd.DataFrame):
    cur = conn.cursor()
    for idx, row in df.reset_index(drop=True).iterrows():
        cur.execute("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?, ?, ?)",
                    (batch_id, int(idx), json.dumps(row.fillna('').to_dict())))
    conn.commit()


def load_into_fact_market_share(conn: sqlite3.Connection, batch_id: str, mapping: Dict[str, str], df: pd.DataFrame):
    cur = conn.cursor()
    now = pd.Timestamp.now().isoformat()
    for _, row in df.iterrows():
        rsid = row.get(mapping.get('rsid')) if mapping.get('rsid') else None
        station_code = row.get(mapping.get('stn')) if mapping.get('stn') else None
        zip_code = row.get(mapping.get('zip_code')) if mapping.get('zip_code') else None
        service = row.get(mapping.get('service')) if mapping.get('service') else None
        contracts = row.get(mapping.get('contracts')) if mapping.get('contracts') else None
        try:
            contracts_v = int(str(contracts).replace(',', '')) if contracts and str(contracts).strip() != '' else None
        except Exception:
            contracts_v = None
        try:
            share_v = float(str(row.get(mapping.get('share_pct'))).replace('%', '').replace(',', '')) if mapping.get('share_pct') else None
        except Exception:
            share_v = None
        try:
            fy_v = int(row.get(mapping.get('fy'))) if mapping.get('fy') and str(row.get(mapping.get('fy'))).strip() != '' else None
        except Exception:
            fy_v = None
        cur.execute(
            "INSERT INTO fact_market_share (batch_id, rsid, station_code, zip_code, service, contracts, share_pct, fy, imported_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (batch_id, rsid, station_code, zip_code, service, contracts_v, share_v, fy_v, now),
        )
    conn.commit()


def process_import(db_path: str, file_bytes: bytes, filename: str, source_system: str = 'auto', mapping_profile: Dict[str, Any] = None, batch_id: str = None) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    det = detect_table(file_bytes, filename)
    headers = det['headers']
    data = det['data']
    dataset_type, confidence = classify_dataset(headers)
    # If a profile mapping provided, use it; else attempt best-effort
    mapping = {}
    if mapping_profile:
        mapping = mapping_profile.get('synonyms', {})
        # mapping_profile likely maps canonical->synonym list; convert to best-match
        mapping = fuzzy_map_headers(headers, mapping_profile.get('synonyms', {}))
    else:
        # no mapping profile; try a few known heuristics
        # simple default synonyms
        default_syns = {
            'zip_code': ['zip', 'zip_code', 'zipcode', 'postal_code'],
            'stn': ['stn', 'station', 'station_code'],
            'service': ['service'],
            'contracts': ['contracts', 'contract_count', 'contract'],
            'share_pct': ['share', '% share', 'market_share', 'share_pct'],
            'rsid': ['rsid'],
            'fy': ['fy', 'fiscal_year']
        }
        mapping = fuzzy_map_headers(headers, default_syns)

    # create batch id if not provided
    if not batch_id:
        import uuid
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"

    cur = conn.cursor()
    # Ensure both `filename` (legacy/required NOT NULL) and `file_name` are populated
    cur.execute(
        """
        INSERT OR REPLACE INTO raw_import_batches
        (batch_id, source_system, filename, file_name, stored_path, file_hash, imported_at, detected_sheet, detected_header_row, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch_id,
            source_system,
            filename or 'unknown',    # legacy required column
            filename or 'unknown',    # newer file_name column
            '',                       # stored_path (not used here)
            '',
            pd.Timestamp.now().isoformat(),
            det['sheet'],
            det['header_row'],
            'imported',
            json.dumps({'dataset_type': dataset_type, 'confidence': confidence}),
        ),
    )
    conn.commit()

    # save raw rows for audit
    save_raw_rows(conn, batch_id, data)

    # load into canonical fact table if it looks like market share
    load_summary = {}
    if dataset_type.startswith('USAREC') or dataset_type.startswith('DOD') or True:
        try:
            load_into_fact_market_share(conn, batch_id, mapping, data)
            load_summary['status'] = 'loaded'
            load_summary['rows'] = len(data)
        except Exception as e:
            load_summary['status'] = 'error'
            load_summary['error'] = str(e)

    conn.close()
    return {
        'status': 'ok',
        'batch_id': batch_id,
        'dataset_type': dataset_type,
        'confidence': confidence,
        'rows_read': len(data),
        'mapped_columns': mapping,
        'load_summary': load_summary,
    }
