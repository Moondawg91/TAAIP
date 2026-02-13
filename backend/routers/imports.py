from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from typing import Optional, Dict, Any, List, Tuple
import os, json, hashlib, sqlite3, re
from datetime import datetime, timezone

import pandas as pd
from redis import Redis
from rq import Queue
import traceback

router = APIRouter()

def _db_path() -> str:
    return os.getenv("DB_PATH") or "/app/recruiting.db"

def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _new_id(prefix: str) -> str:
    return f"{prefix}_{hashlib.sha1(os.urandom(16)).hexdigest()[:10]}"

def _connect():
    return sqlite3.connect(_db_path())

# -------------------------
# RSID / STN parsing utils
# -------------------------
RSID_RE = re.compile(r"([0-9A-Z]{4})")

def parse_rsid(stn_value: str) -> Dict[str, Optional[str]]:
    """
    Accepts:
      - '3J3H'
      - '3J3H - WAKE FOREST'
      - '3J3H WAKE FOREST'
    Returns:
      cmd/bde/bn/co/rsid (bde=1 char, bn=2, co=3, rsid=4)
    """
    if stn_value is None:
        return {"bde": None, "bn": None, "co": None, "rsid": None, "name": None}
    s = str(stn_value).strip().upper()
    m = RSID_RE.search(s)
    code = m.group(1) if m else None
    name = None
    if "-" in s:
        parts = [p.strip() for p in s.split("-", 1)]
        if len(parts) == 2 and parts[1]:
            name = parts[1]
    return {
        "bde": code[:1] if code else None,
        "bn":  code[:2] if code else None,
        "co":  code[:3] if code else None,
        "rsid": code[:4] if code else None,
        "name": name
    }

# -------------------------
# Profile registry (USAREC first)
# -------------------------
PROFILES = {
  "USAREC_MARKET_CONTRACTS_SHARE": {
    "required": {"FY","STN","ZIP","CONTR","SHARE"},
    "optional": {"COMP","MKT","BDE","BN","CO","PER","TOTCONTR","TOTPOP"},
  },
  "USAREC_ZIP_CATEGORY": {
    "required": {"STN","ZIP","CAT1","CAT2","CAT3","CAT4","CAT5","CAT6","CAT7","CAT8","CAT9"},
    "optional": set(),
  },
  "DOD_ORG_HIERARCHY": {
    "required": {"CMD","BDE","BN","CO","STN"},
    "optional": set(),
  }
}

SYNONYMS = {
  "STN": {"STN","STATION","RSID"},
  "ZIP": {"ZIP","ZIPCODE","ZIP_CODE"},
  "FY": {"FY","FISCAL_YEAR"},
  "PER": {"PER","PERIOD"},
  "CONTR": {"CONTR","CONTRACTS","CNTR"},
  "SHARE": {"SHARE","MARKET_SHARE","SHARE_PCT","SHARE%","PCT_SHARE"},
  "TOTCONTR": {"TOTCONTR","TOTAL_CONTRACTS","TOTALCONTR"},
  "TOTPOP": {"TOTPOP","TOTAL_POP","TOTALPOP"},
}

import re
from typing import List, Optional, Tuple

def normalize_col(c: str) -> str:
    c = str(c).strip().upper()
    c = re.sub(r"\s+", "", c)
    c = c.replace("%","")
    return c

def canonicalize_columns(cols: List[str]) -> Tuple[List[str], Dict[str,str]]:
    orig_to_can = {}
    canonical = []
    for c in cols:
        n = normalize_col(c)
        mapped = None
        for can, syns in SYNONYMS.items():
            if n in {normalize_col(x) for x in syns}:
                mapped = can
                break
        mapped = mapped or n
        orig_to_can[c] = mapped
        canonical.append(mapped)
    return canonical, orig_to_can

def classify_profile(canonical_cols: set) -> Tuple[Optional[str], float]:
    # Deterministic profile detection: prefer explicit token checks
    cols = set(canonical_cols)

    # SAMA: ZIP + STATION + SAMA/SCORE token
    if (any(x in cols for x in ("ZIP", "ZIPCODE")) and
        any(x in cols for x in ("STN", "STATION", "RSID")) and
        any(x in cols for x in ("SAMA", "SAMASCORE", "SAMA_SCORE", "SCORE"))):
        return "USAREC_SAMA", 1.0

    # ZIP by category
    if (any(x in cols for x in ("ZIP", "ZIPCODE")) and any(x in cols for x in ("CAT", "CATEGORY", "CAT1"))):
        return "USAREC_ZIP_CATEGORY", 1.0

    # Productivity / recruiter metrics
    if ("RECRUITER" in cols and any(x in cols for x in ("PRODUCTIVITY", "PRODUCTIVITYRATE"))):
        return "USAREC_PRODUCTIVITY", 1.0

    # Market share / contracts (fallback to previous heuristic)
    best = (None, 0.0)
    for name, meta in PROFILES.items():
        req = meta["required"]
        hit = len(req.intersection(canonical_cols))
        score = hit / max(1, len(req))
        if score > best[1]:
            best = (name, score)
    if best[1] >= 0.8:
        return best[0], best[1]

    # Other generic detectors
    if any(x in cols for x in ("MISSIONCATEGORY", "MISSION")):
        return "MISSION_CATEGORY", 1.0
    if any(x in cols for x in ("TESTSCORE", "TEST_SCORE", "TEST", "SCORE")):
        return "TEST_SCORE_AVG", 1.0
    if ("CBSA" in cols and any(x in cols for x in ("URBANICITY", "URBANICITYPERCENT"))):
        return "URBANICITY_CBSA", 1.0

    return None, 0.0

# -------------------------
# Header row detection (Excel-like)
# -------------------------
def detect_header_row(df_raw: pd.DataFrame, max_scan_rows: int = 30) -> int:
    best_row = 0
    best_score = 0.0
    scan = min(max_scan_rows, len(df_raw))
    for i in range(scan):
        row = df_raw.iloc[i].tolist()
        row = [x for x in row if str(x).strip() not in ("", "nan", "None")]
        if len(row) < 3:
            continue
        canon, _ = canonicalize_columns([str(x) for x in row])
        profile, score = classify_profile(set(canon))
        if score > best_score:
            best_score = score
            best_row = i
    return best_row

def load_table_from_file(path: str) -> Tuple[pd.DataFrame, Dict[str,Any]]:
    meta: Dict[str,Any] = {}
    if path.lower().endswith(".csv"):
        df = pd.read_csv(path)
        meta["sheet_name"] = None
        meta["header_row_index"] = 0
        return df, meta

    xls = pd.ExcelFile(path)
    sheet = xls.sheet_names[0]
    df_raw = pd.read_excel(path, sheet_name=sheet, header=None)
    header_row = detect_header_row(df_raw)
    df = pd.read_excel(path, sheet_name=sheet, header=header_row)
    meta["sheet_name"] = sheet
    meta["header_row_index"] = header_row
    return df, meta

# -------------------------
# Loaders (facts/dims)
# -------------------------
def ensure_fact_tables(con: sqlite3.Connection):
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fact_market_share_contracts (
      batch_id TEXT,
      fy INTEGER,
      per TEXT,
      comp TEXT,
      mkt TEXT,
      bde TEXT,
      bn TEXT,
      co TEXT,
      rsid TEXT,
      zip TEXT,
      contracts REAL,
      share REAL,
      totcontracts REAL,
      totpop REAL,
      imported_at TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fact_zip_category (
      batch_id TEXT,
      rsid TEXT,
      zip TEXT,
      cat1 REAL, cat2 REAL, cat3 REAL, cat4 REAL, cat5 REAL, cat6 REAL, cat7 REAL, cat8 REAL, cat9 REAL,
      imported_at TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dim_org_unit (
      cmd TEXT,
      bde TEXT,
      bn TEXT,
      co TEXT,
      rsid TEXT,
      name TEXT,
      source_system TEXT,
      imported_at TEXT,
      PRIMARY KEY (cmd, bde, bn, co, rsid)
    );
    """)

    con.commit()


def load_usarec_sama(con: sqlite3.Connection, df: pd.DataFrame, batch_id: str):
    """Load SAMA dataset from DataFrame into `sama_data` table.

    The function tolerates messy column names by normalizing and locating
    ZIP, STATION, and SAMA score-like columns.
    """
    df_local = df.copy()
    # build normalized column map: normalized -> original
    norm_map = {normalize_col(c): c for c in df_local.columns}

    def pick_col(cands):
        for cand in cands:
            nc = normalize_col(cand)
            for ncol in norm_map:
                if cand == ncol or cand in ncol or ncol in cand:
                    return norm_map[ncol]
        # try substring matching
        for ncol, orig in norm_map.items():
            for cand in cands:
                if cand in ncol:
                    return orig
        return None

    zip_col = pick_col(("ZIP", "ZIPCODE", "ZIP_CODE"))
    station_col = pick_col(("STN", "STATION", "RSID", "STATIONNAME"))
    sama_col = pick_col(("SAMA", "SAMASCORE", "SAMA_SCORE", "SCORE"))

    if not (zip_col and station_col and sama_col):
        raise ValueError(f"Missing required SAMA columns; available: {list(df_local.columns)}")

    cur = con.cursor()
    imported_at = _utc_now()
    rows = []
    for _, r in df_local.iterrows():
        try:
            zipv = r.get(zip_col)
            stn = r.get(station_col)
            scorev = r.get(sama_col)
        except Exception:
            zipv = None; stn = None; scorev = None
        rows.append((zipv, stn, float(scorev) if pd.notna(scorev) else None, batch_id, imported_at))

    cur.executemany("INSERT INTO sama_data(zip_code, station, sama_score, batch_id, created_at) VALUES (?,?,?,?,?)", rows)
    con.commit()

def load_usarec_market(con: sqlite3.Connection, df: pd.DataFrame, batch_id: str):
    df = df.copy()
    df.columns = [normalize_col(c) for c in df.columns]
    rename = {}
    for c in df.columns:
        for can, syns in SYNONYMS.items():
            if c in {normalize_col(x) for x in syns}:
                rename[c] = can
    df = df.rename(columns=rename)

    required = PROFILES["USAREC_MARKET_CONTRACTS_SHARE"]["required"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    imported_at = _utc_now()
    rows = []
    for _, r in df.iterrows():
        rs = parse_rsid(r.get("STN"))
        rows.append((
            batch_id,
            int(r.get("FY")) if pd.notna(r.get("FY")) else None,
            str(r.get("PER")) if pd.notna(r.get("PER")) else None,
            str(r.get("COMP")) if "COMP" in df.columns and pd.notna(r.get("COMP")) else None,
            str(r.get("MKT")) if "MKT" in df.columns and pd.notna(r.get("MKT")) else None,
            rs["bde"], rs["bn"], rs["co"], rs["rsid"],
            str(r.get("ZIP")) if pd.notna(r.get("ZIP")) else None,
            float(r.get("CONTR")) if pd.notna(r.get("CONTR")) else None,
            float(r.get("SHARE")) if pd.notna(r.get("SHARE")) else None,
            float(r.get("TOTCONTR")) if "TOTCONTR" in df.columns and pd.notna(r.get("TOTCONTR")) else None,
            float(r.get("TOTPOP")) if "TOTPOP" in df.columns and pd.notna(r.get("TOTPOP")) else None,
            imported_at
        ))

    cur = con.cursor()
    cur.executemany("""
      INSERT INTO fact_market_share_contracts
      (batch_id, fy, per, comp, mkt, bde, bn, co, rsid, zip, contracts, share, totcontracts, totpop, imported_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    con.commit()

def load_usarec_zip_category(con: sqlite3.Connection, df: pd.DataFrame, batch_id: str):
    df = df.copy()
    df.columns = [normalize_col(c) for c in df.columns]
    rename = {}
    for c in df.columns:
        for can, syns in SYNONYMS.items():
            if c in {normalize_col(x) for x in syns}:
                rename[c] = can
    df = df.rename(columns=rename)

    required = PROFILES["USAREC_ZIP_CATEGORY"]["required"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    imported_at = _utc_now()
    rows = []
    for _, r in df.iterrows():
        rs = parse_rsid(r.get("STN"))
        rows.append((
            batch_id, rs["rsid"],
            str(r.get("ZIP")) if pd.notna(r.get("ZIP")) else None,
            float(r.get("CAT1")) if pd.notna(r.get("CAT1")) else None,
            float(r.get("CAT2")) if pd.notna(r.get("CAT2")) else None,
            float(r.get("CAT3")) if pd.notna(r.get("CAT3")) else None,
            float(r.get("CAT4")) if pd.notna(r.get("CAT4")) else None,
            float(r.get("CAT5")) if pd.notna(r.get("CAT5")) else None,
            float(r.get("CAT6")) if pd.notna(r.get("CAT6")) else None,
            float(r.get("CAT7")) if pd.notna(r.get("CAT7")) else None,
            float(r.get("CAT8")) if pd.notna(r.get("CAT8")) else None,
            float(r.get("CAT9")) if pd.notna(r.get("CAT9")) else None,
            imported_at
        ))

    cur = con.cursor()
    cur.executemany("""
      INSERT INTO fact_zip_category
      (batch_id, rsid, zip, cat1,cat2,cat3,cat4,cat5,cat6,cat7,cat8,cat9, imported_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    con.commit()

def load_dod_org_hierarchy(con: sqlite3.Connection, df: pd.DataFrame, batch_id: str):
    df = df.copy()
    df.columns = [normalize_col(c) for c in df.columns]
    required = PROFILES["DOD_ORG_HIERARCHY"]["required"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    imported_at = _utc_now()
    cur = con.cursor()
    for _, r in df.iterrows():
        stn = r.get("STN")
        rs = parse_rsid(stn)
        cur.execute("""
          INSERT OR REPLACE INTO dim_org_unit (cmd,bde,bn,co,rsid,name,source_system,imported_at)
          VALUES (?,?,?,?,?,?,?,?)
        """, (
          str(r.get("CMD")) if pd.notna(r.get("CMD")) else None,
          str(r.get("BDE")) if pd.notna(r.get("BDE")) else rs["bde"],
          str(r.get("BN")) if pd.notna(r.get("BN")) else rs["bn"],
          str(r.get("CO")) if pd.notna(r.get("CO")) else rs["co"],
          rs["rsid"],
          rs["name"],
          "DOD",
          imported_at
        ))
    con.commit()

# -------------------------
# API endpoints
# -------------------------
@router.post("/import/upload")
def import_upload(
    file: UploadFile = File(...),
    source_system: str = Form("USAREC"),
    authorization: Optional[str] = Header(None)
):
    upload_dir = "/app/uploads"
    _ensure_dir(upload_dir)

    batch_id = _new_id("batch")
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", file.filename or "upload")
    stored_path = os.path.join(upload_dir, f"{batch_id}__{safe_name}")

    with open(stored_path, "wb") as f:
        f.write(file.file.read())

    file_hash = _sha256_file(stored_path)
    imported_at = _utc_now()

    df, meta = load_table_from_file(stored_path)
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    canonical_cols, orig_map = canonicalize_columns(list(df.columns))
    profile, score = classify_profile(set(canonical_cols))

    con = _connect()
    cur = con.cursor()

    # insert batch metadata (status 'received')
    cur.execute("""
      INSERT INTO raw_import_batches
      (batch_id, source_system, filename, stored_path, file_hash, imported_at, detected_profile, status, notes)
      VALUES (?,?,?,?,?,?,?,?,?)
    """, (batch_id, source_system, safe_name, stored_path, file_hash, imported_at, profile, "received", f"classify_score={score:.2f}"))

    preview = df.head(5).to_dict(orient="records")
    cur.execute("""
      INSERT INTO raw_import_tables
      (batch_id, sheet_name, table_index, header_row_index, detected_profile, column_map_json, row_count, preview_json)
      VALUES (?,?,?,?,?,?,?,?)
    """, (
      batch_id,
      meta.get("sheet_name"),
      0,
      meta.get("header_row_index"),
      profile,
      json.dumps(orig_map),
      int(len(df)),
      json.dumps(preview)
    ))
    con.commit()
    con.close()


@router.get('/import/batches')
def list_batches(limit: int = 50):
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT batch_id, source_system, filename, imported_at, status, detected_profile, notes FROM raw_import_batches ORDER BY imported_at DESC LIMIT ?", (limit,))
    rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
    con.close()
    return {"batches": rows}


@router.get('/import/batches/{batch_id}')
def get_batch(batch_id: str):
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT batch_id, source_system, filename, stored_path, imported_at, status, detected_profile, notes FROM raw_import_batches WHERE batch_id=?", (batch_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="batch not found")
    batch = dict(zip([c[0] for c in cur.description], row))
    cur.execute("SELECT table_index, sheet_name, header_row_index, detected_profile, column_map_json, row_count, preview_json FROM raw_import_tables WHERE batch_id=? ORDER BY table_index", (batch_id,))
    tables = []
    for r in cur.fetchall():
        tables.append(dict(zip([c[0] for c in cur.description], r)))
    con.close()
    batch["tables"] = tables
    return batch

    # enqueue background job via RQ
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        redis_conn = Redis.from_url(redis_url)
        q = Queue('default', connection=redis_conn)
        q.enqueue('backend.worker.process_import', batch_id, stored_path)
        return {"batch_id": batch_id, "filename": safe_name, "stored_path": stored_path, "status": "queued"}
    except Exception:
        traceback.print_exc()
        # fallback: mark as error
        con = _connect()
        cur = con.cursor()
        cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("error", "enqueue_failed", batch_id))
        con.commit()
        con.close()
        raise HTTPException(status_code=500, detail="Failed to enqueue background job")

    return {
      "status": "ok",
      "batch_id": batch_id,
      "source_system": source_system,
      "detected_profile": profile,
      "detected_score": round(score, 3),
      "sheet_name": meta.get("sheet_name"),
      "header_row_index": meta.get("header_row_index"),
      "row_count": int(len(df)),
      "preview": preview
    }
