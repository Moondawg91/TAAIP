import pandas as pd
from typing import Tuple, List, Any


def _choose_header_row(df_raw: pd.DataFrame) -> int:
    """Inspect the first rows of df_raw (header=None) and try to pick a row
    that represents the real header. Returns header row index or None."""
    if df_raw is None or len(df_raw) == 0:
        return None
    max_scan = min(10, len(df_raw))
    for i in range(max_scan):
        row = df_raw.iloc[i].fillna('').astype(str).str.strip()
        non_empty = sum(1 for v in row if v and not v.lower().startswith('unnamed') and 'applied filters' not in v.lower())
        if non_empty >= max(1, int(len(row) * 0.5)):
            return i
    # gentle fallback: pick first row within first 20 that has any alphabetic cell
    max_scan2 = min(20, len(df_raw))
    for i in range(max_scan2):
        row = df_raw.iloc[i].fillna('').astype(str).str.strip()
        has_alpha = any((v and any(c.isalpha() for c in v) and not v.lower().startswith('unnamed') and 'applied filters' not in v.lower()) for v in row)
        if has_alpha:
            return i
    return None


def parse_file(path: str, filename: str) -> Tuple[List[str], List[str], Any]:
    """Return (sheet_names, headers, dataframe_of_first_sheet)
    headers is list of header column names (normalized)
    """
    lower = filename.lower()
    if lower.endswith('.csv'):
        # Read without assuming header so we can detect and skip preface rows
        df_raw = pd.read_csv(path, header=None, dtype=str, encoding='utf-8', engine='python')
        header_row = _choose_header_row(df_raw)
        if header_row is not None:
            df = pd.read_csv(path, header=header_row, dtype=str, encoding='utf-8', engine='python')
        else:
            df = pd.read_csv(path, dtype=str, encoding='utf-8', engine='python')
        headers = list(df.columns)
        return (['sheet1'], headers, df)
    else:
        # excel
        xls = pd.ExcelFile(path, engine='openpyxl')
        sheet_names = xls.sheet_names
        # read first non-empty sheet and attempt to detect header row that may be preceded by preface rows
        for sn in sheet_names:
            # read without header to inspect the first rows
            df_raw = pd.read_excel(xls, sheet_name=sn, header=None, dtype=str)
            if df_raw is None or len(df_raw.columns) == 0:
                continue
            header_row = _choose_header_row(df_raw)
            if header_row is not None:
                df = pd.read_excel(xls, sheet_name=sn, header=header_row, dtype=str)
            else:
                df = pd.read_excel(xls, sheet_name=sn, dtype=str)
            if df is not None and len(df.columns) > 0:
                headers = list(df.columns)
                return (sheet_names, headers, df)
        # fallback
        return (sheet_names, [], pd.DataFrame())
