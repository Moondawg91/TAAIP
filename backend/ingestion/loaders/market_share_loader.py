import os
import pandas as pd
import sqlite3
from typing import Optional

# reuse helpers from imports for normalization and rsid parsing
from backend.routers.imports import normalize_col, parse_rsid


def load_market_share(con: sqlite3.Connection, path: str, batch_id: str) -> None:
    """Load market-share/contract dataset into `fact_market_share_contracts`.

    Attempts to use the canonical loader in `backend.routers.imports` when
    possible. If that fails, performs tolerant column discovery and best-effort
    inserts into the fact table.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xls', '.xlsx'):
        df = pd.read_excel(path, engine='openpyxl')
    else:
        df = pd.read_csv(path)

    # try shared loader first (higher fidelity)
    try:
        from backend.routers.imports import load_usarec_market
        load_usarec_market(con, df, batch_id)
        return
    except Exception:
        pass

    # tolerant mapping
    df_local = df.copy()
    norm_map = {normalize_col(c): c for c in df_local.columns}

    def pick(*cands):
        for cand in cands:
            nc = normalize_col(cand)
            if nc in norm_map:
                return norm_map[nc]
        # substring fallback
        for nc, orig in norm_map.items():
            for cand in cands:
                if normalize_col(cand) in nc or nc in normalize_col(cand):
                    return orig
        return None

    fy_col = pick('FY', 'FISCAL_YEAR', 'FISCALYEAR', 'RY')
    per_col = pick('PER', 'RQ', 'QTR', 'QUARTER')
    service_col = pick('SERVICE', 'MKT', 'MARKET')
    comp_col = pick('COMP', 'COMPANY')
    contr_col = pick('SUM OF CONTRACTS', 'SUMOFCONTRACTS', 'CONTRACTS', 'CONTR', 'AMOUNT', 'TOTAL')
    share_col = pick('SHARE', 'MARKET_SHARE', 'SHARE_PCT', 'PCT_SHARE', 'SHARE%')
    totcontr_col = pick('TOTCONTR', 'TOTAL_CONTRACTS', 'TOTALCONTR', 'TOTAL')
    totpop_col = pick('TOTPOP', 'TOTAL_POP', 'TOTALPOP')
    zip_col = pick('ZIP', 'ZIPCODE', 'ZIP_CODE', 'POSTALCODE')
    stn_col = pick('STATION', 'STN', 'RSID', 'STATIONNAME')

    imported_at = _now = __import__('datetime').datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    cur = con.cursor()
    rows = []
    for _, r in df_local.iterrows():
        try:
            fy = int(r.get(fy_col)) if fy_col and pd.notna(r.get(fy_col)) else None
        except Exception:
            fy = None
        per = str(r.get(per_col)).strip() if per_col and pd.notna(r.get(per_col)) else None
        comp = str(r.get(comp_col)).strip() if comp_col and pd.notna(r.get(comp_col)) else None
        mkt = str(r.get(service_col)).strip() if service_col and pd.notna(r.get(service_col)) else None

        stn_val = r.get(stn_col) if stn_col else None
        rs = parse_rsid(stn_val) if stn_val is not None else {"bde": None, "bn": None, "co": None, "rsid": None}

        zipv = str(r.get(zip_col)).strip() if zip_col and pd.notna(r.get(zip_col)) else None

        try:
            contracts = float(str(r.get(contr_col)).replace(",", "")) if contr_col and pd.notna(r.get(contr_col)) else None
        except Exception:
            contracts = None

        try:
            share = None
            if share_col and pd.notna(r.get(share_col)):
                s = str(r.get(share_col)).strip().replace('%', '').replace(',', '')
                share = float(s)
        except Exception:
            share = None

        try:
            totcontr = float(str(r.get(totcontr_col)).replace(",", "")) if totcontr_col and pd.notna(r.get(totcontr_col)) else None
        except Exception:
            totcontr = None

        try:
            totpop = float(str(r.get(totpop_col)).replace(",", "")) if totpop_col and pd.notna(r.get(totpop_col)) else None
        except Exception:
            totpop = None

        # derive share if missing and totcontr available
        if share is None and contracts is not None and totcontr:
            try:
                share = (float(contracts) / float(totcontr)) * 100.0
            except Exception:
                pass

        rows.append((batch_id, fy, per, comp, mkt, rs.get('bde'), rs.get('bn'), rs.get('co'), rs.get('rsid'), zipv, contracts, share, totcontr, totpop, imported_at))

    if rows:
        cur.executemany(
            """INSERT INTO fact_market_share_contracts
            (batch_id, fy, per, comp, mkt, bde, bn, co, rsid, zip, contracts, share, totcontracts, totpop, imported_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows
        )
        con.commit()
