"""
Simple ingestion classifier + header detection utilities.
This is a lightweight rules-first classifier for USAREC dataset types.
"""
from typing import List, Dict, Any, Optional
import csv
import re
import json
import os
import pandas as pd

# known header tokens to boost header detection
_KNOWN_TOKENS = {"zip", "zip code", "zipcode", "share", "market share", "contr", "contract", "contracts", "sum of contracts", "service", "ry", "rq", "fy", "stn", "rsid"}

def detect_header_csv(path: str, max_rows: int = 60) -> Optional[int]:
    # Read up to max_rows rows and score each row similar to XLSX heuristic
    rows = []
    with open(path, newline='') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= max_rows - 1:
                break

    best_idx = None
    best_score = -1.0
    for i, row in enumerate(rows[:max_rows]):
        # join row into lowercase combined string to filter metadata rows
        row_text = " ".join(["" if v is None else str(v) for v in row])
        low = row_text.strip().lower()
        if not low:
            continue
        if 'applied filters' in low or 'applied filter' in low or ('included' in low and 'not' in low):
            continue

        nonempty = sum(1 for v in row if v is not None and str(v).strip() != "")
        text_like = 0
        token_bonus = 0
        for v in row:
            if v is None:
                continue
            s = str(v).strip()
            if s == "":
                continue
            # numeric check
            try:
                float(s.replace(',', ''))
                # numeric values are less likely headers
            except Exception:
                text_like += 1
                if normalize_col(s) in _KNOWN_TOKENS:
                    token_bonus += 1

        score = text_like + (nonempty * 0.05) + (token_bonus * 0.5)
        if score > best_score:
            best_score = score
            best_idx = i

    # require at least some textual signal to accept a header
    if best_score >= 1.0:
        return best_idx
    # fallback: if first row has several non-empty cells and non-numeric entries, use it
    if rows:
        first = rows[0]
        nonempty = sum(1 for v in first if v and str(v).strip())
        text_like = 0
        for v in first:
            if v is None:
                continue
            s = str(v).strip()
            try:
                float(s.replace(',', ''))
            except Exception:
                if s:
                    text_like += 1
        if nonempty >= 3 and text_like >= 2:
            return 0
    return None

def normalize_col(c: Any) -> str:
    if c is None:
        return ''
    s = str(c).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def classify_columns(cols: List[str]) -> Dict[str, Any]:
    """Return a simple classification dict with dataset_type and score."""
    colset = set(cols)
    def any_in(opts):
        return any(o in colset for o in opts)

    dataset = 'unknown'
    if any_in(['zip', 'zip code', 'zipcode']) and any_in(['share', 'market share']) and any_in(['contr', 'contracts', 'contract']):
        dataset = 'market_share_contracts'
    elif any_in(['zip', 'zip code', 'zipcode']) and any_in(['category', 'cat']):
        dataset = 'zip_by_category'
    elif any_in(['rsid', 'stn', 'stn', 'station']) and any_in(['act', 'res', 'vol', 'volume']):
        dataset = 'station_volume'

    # determine grain
    grain = None
    if any_in(['rsid', 'stn', 'station']):
        grain = 'STN'
    elif any_in(['bn', 'battalion']):
        grain = 'BN'
    elif any_in(['zip', 'zipcode']):
        grain = 'ZIP'

    return {
        'dataset_type': dataset,
        'grain': grain,
        'columns': cols,
        'confidence': 0.9 if dataset != 'unknown' else 0.3,
    }

def inspect_csv(path: str) -> Dict[str, Any]:
    header_row = detect_header_csv(path)
    header = []
    if header_row is not None:
        with open(path, newline='') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == header_row:
                    header = [normalize_col(c) for c in row]
                    break
    else:
        # try to read first row as header fallback
        try:
            with open(path, newline='') as f:
                reader = csv.reader(f)
                first = next(reader, None)
                if first:
                    header = [normalize_col(c) for c in first]
        except Exception:
            header = []

    return {
        'header_row': header_row,
        'columns': header,
        'classification': classify_columns(header)
    }


def inspect_xlsx(path: str, max_scan: int = 60) -> Dict[str, Any]:
    """Inspect an Excel workbook for the best header row and return columns.
    Scans the first sheet top `max_scan` rows (no header) and heuristically chooses
    a header row, ignoring common metadata lines like 'Applied filters'.
    """
    info = {"header_row": None, "columns": [], "classification": None}
    try:
        xls = pd.ExcelFile(path)
        sheet = xls.sheet_names[0]
        raw = pd.read_excel(path, sheet_name=sheet, header=None, nrows=max_scan, engine="openpyxl")

        best_row = None
        best_score = -1.0
        for idx, row in raw.iterrows():
            # join row into lowercase combined string to filter metadata rows
            row_text = " ".join(["" if pd.isna(x) else str(x) for x in row])
            low = row_text.strip().lower()
            if not low:
                continue
            if 'applied filters' in low or 'applied filter' in low or ('included' in low and 'not' in low):
                continue

            # count non-empty cells and token matches
            nonempty = sum(1 for v in row if not pd.isna(v) and str(v).strip() != "")
            text_like = 0
            token_bonus = 0
            for v in row:
                if pd.isna(v):
                    continue
                s = str(v).strip()
                # numeric check
                try:
                    float(s)
                    # numeric values are less likely header
                except Exception:
                    text_like += 1
                    if s.lower() in _KNOWN_TOKENS:
                        token_bonus += 1

            score = text_like + (nonempty * 0.05) + (token_bonus * 0.5)
            if score > best_score:
                best_score = score
                best_row = idx

        if best_row is not None:
            df = pd.read_excel(path, sheet_name=sheet, header=best_row, engine="openpyxl")
            cols = [normalize_col(c) for c in df.columns if str(c).strip() != ""]
            info['header_row'] = int(best_row)
            info['columns'] = cols
            info['classification'] = classify_columns(cols)
        else:
            # fallback: try default read
            df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", nrows=20)
            cols = [normalize_col(c) for c in df.columns if str(c).strip() != ""]
            info['columns'] = cols
            info['classification'] = classify_columns(cols)
    except Exception:
        pass
    return info


def inspect_file(path: str) -> Dict[str, Any]:
    """Unified inspector: chooses CSV or XLSX inspection based on extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        return inspect_xlsx(path)
    else:
        return inspect_csv(path)
