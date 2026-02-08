from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Optional, List, Any, Dict
import os, uuid, sqlite3, hashlib
import pandas as pd
from datetime import datetime, timezone

# Reuse existing helpers when available
try:
    from backend.ingestion.classifier import inspect_file
except Exception:
    inspect_file = None


def _inspect_table_fallback(path: str) -> dict:
    """Simple fallback inspector that supports CSV and Excel files using pandas.
    Returns {header_row, columns} similar to inspect_csv.
    """
    info = {"header_row": None, "columns": []}
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xls", ".xlsx"):
            # Read a block without header to detect header row heuristically
            raw = pd.read_excel(path, sheet_name=0, engine="openpyxl", header=None, nrows=80)
            # Score each row: prefer rows with many text-like non-empty cells
            best_row = None
            best_score = -1
            for idx, row in raw.iterrows():
                non_null = row.notna()
                cnt = int(non_null.sum())
                # prefer rows with at least 2 non-empty cells
                if cnt < 2:
                    continue
                text_like = 0
                for v in row:
                    try:
                        # numeric values reduce score
                        float(str(v))
                    except Exception:
                        if v is not None and str(v).strip() != "":
                            text_like += 1
                score = text_like + (cnt * 0.1)
                if score > best_score:
                    best_score = score
                    best_row = idx

            if best_row is not None:
                # read again with header at best_row
                df = pd.read_excel(path, sheet_name=0, engine="openpyxl", header=best_row)
                cols = [str(c).strip() for c in df.columns if str(c).strip() != ""]
                info["columns"] = cols
                info["header_row"] = int(best_row)
            else:
                # fallback to simple read
                df = pd.read_excel(path, sheet_name=0, engine="openpyxl", nrows=50)
                cols = [str(c).strip() for c in df.columns if str(c).strip() != ""]
                info["columns"] = cols
                info["header_row"] = 0 if cols else None
        else:
            df = pd.read_csv(path, nrows=50)
            cols = [str(c).strip() for c in df.columns if str(c).strip() != ""]
            info["columns"] = cols
            info["header_row"] = 0 if cols else None
    except Exception:
        pass
    return info

try:
    from backend.ingestion.dataset_registry import classify
except Exception:
    classify = None

try:
    from backend.worker import process_import
except Exception:
    process_import = None

try:
    # reuse loader helpers from existing imports router
    from backend.routers.imports import (
        load_table_from_file,
        canonicalize_columns,
        classify_profile,
        ensure_fact_tables,
        load_usarec_market,
        load_usarec_zip_category,
        load_dod_org_hierarchy,
    )
except Exception:
    load_table_from_file = None
    canonicalize_columns = None
    classify_profile = None
    ensure_fact_tables = None
    load_usarec_market = None
    load_usarec_zip_category = None
    load_dod_org_hierarchy = None

router = APIRouter(prefix="/api/v2/imports", tags=["imports"])

DB = os.getenv("DB_PATH") or "/app/recruiting.db"
UPLOAD_DIR = os.getenv("UPLOAD_DIR") or ("/uploads" if os.path.isdir("/uploads") else "/tmp/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,))
    return cur.fetchone() is not None


def _get_batch(con: sqlite3.Connection, batch_id: str) -> Optional[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("SELECT * FROM raw_import_batches WHERE batch_id=? LIMIT 1", (batch_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def _insert_raw_row_error(con: sqlite3.Connection, batch_id: str, row_index: int, row_obj: Dict[str, Any], errors: List[str]):
    """Insert a row-level error into raw_import_rows table. Stores a JSON blob with row and errors."""
    import json
    cur = con.cursor()
    payload = json.dumps({"row": row_obj, "errors": errors}, default=str)
    # Attempt to use existing column names (row_index vs row_index)
    try:
        cur.execute("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?,?,?)", (batch_id, row_index, payload))
    except Exception:
        # fallback: try different column name
        try:
            cur.execute("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?,?,?)", (batch_id, row_index, payload))
        except Exception:
            # if insert fails, ignore to avoid blocking processing
            pass
    con.commit()


@router.post("/upload")
async def imports_upload(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    source_system: str = Query("USAREC"),
):
    chosen = files[0] if files else file
    if not chosen:
        raise HTTPException(status_code=400, detail="No file provided")

    data = await chosen.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")

    ext = os.path.splitext(chosen.filename or "")[1] or ""
    safe_name = f"{uuid.uuid4().hex}_{source_system}{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(dest, "wb") as out:
            out.write(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Write failed: {e}")

    header_row = None
    columns: List[str] = []
    dataset_key = None

    # Prefer unified inspector (supports CSV + Excel), else fallback to pandas-based inspector
    try:
        info = None
        if inspect_file:
            try:
                info = inspect_file(dest)
            except Exception:
                info = None

        if not info or not info.get("columns"):
            # fallback to pandas-based inspector
            info = _inspect_table_fallback(dest)

        header_row = info.get("header_row")
        columns = info.get("columns") or []
    except Exception:
        header_row = None
        columns = []

    # attempt to canonicalize column names before classification (improves dataset detection)
    columns_to_classify = columns
    try:
        if canonicalize_columns and columns:
            try:
                canonical_cols, _orig_map = canonicalize_columns(columns)
                columns_to_classify = canonical_cols
            except Exception:
                columns_to_classify = columns
    except Exception:
        columns_to_classify = columns

    if classify and columns_to_classify:
        try:
            dataset_key = classify(columns_to_classify, source_system)
        except Exception:
            dataset_key = None

    dataset_key = dataset_key or "unknown"
    fhash = _file_hash(dest)
    batch_id = uuid.uuid4().hex
    imported_at = _utc_now()

    con = _connect()
    cur = con.cursor()

    cur.execute("PRAGMA table_info(raw_import_batches)")
    cols = [r[1] for r in cur.fetchall()]
    colset = set(cols)

    values = {
        "batch_id": batch_id,
        "source_system": source_system,
        "filename": safe_name,
        "stored_path": dest,
        "file_hash": fhash,
        "imported_at": imported_at,
        "detected_profile": dataset_key,
        "status": "RECEIVED",
        "notes": None,
        "header_row": header_row,
    }

    insert_cols = [k for k in values.keys() if k in colset]
    insert_vals = [values[k] for k in insert_cols]

    if not insert_cols:
        con.close()
        raise HTTPException(status_code=500, detail="raw_import_batches schema not recognized")

    placeholders = ",".join(["?"] * len(insert_cols))
    sql = f"INSERT INTO raw_import_batches({','.join(insert_cols)}) VALUES({placeholders})"
    cur.execute(sql, insert_vals)

    con.commit()
    con.close()

    return {
        "batch_id": batch_id,
        "dataset_key": dataset_key,
        "source_system": source_system,
        "stored_path": dest,
        "filename": safe_name,
        "header_row": header_row,
        "columns": columns,
        "status": "RECEIVED",
        "imported_at": imported_at,
    }


@router.get("/batches")
def list_batches(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
):
    con = _connect()
    cur = con.cursor()

    base = "SELECT * FROM raw_import_batches"
    params: List[Any] = []

    if status:
        base += " WHERE status = ?"
        params.append(status)

    cur.execute("PRAGMA table_info(raw_import_batches)")
    cols = [r[1] for r in cur.fetchall()]
    order_col = "imported_at" if "imported_at" in cols else ("created_at" if "created_at" in cols else "rowid")

    base += f" ORDER BY {order_col} DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(base, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()

    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/batches/{batch_id}")
def batch_detail(batch_id: str, include_errors: bool = Query(True)):
    con = _connect()
    batch = _get_batch(con, batch_id)
    if not batch:
        con.close()
        raise HTTPException(status_code=404, detail="Batch not found")

    out: Dict[str, Any] = {"batch": batch}

    if include_errors:
        if _table_exists(con, "raw_import_rows"):
            cur = con.cursor()
            cur.execute("SELECT * FROM raw_import_rows WHERE batch_id=? ORDER BY row_index ASC LIMIT 500", (batch_id,))
            out["row_errors"] = [dict(r) for r in cur.fetchall()]
        elif _table_exists(con, "import_row_errors"):
            cur = con.cursor()
            cur.execute("SELECT * FROM import_row_errors WHERE batch_id=? ORDER BY rowNumber ASC LIMIT 500", (batch_id,))
            out["row_errors"] = [dict(r) for r in cur.fetchall()]
        else:
            out["row_errors"] = []

    con.close()
    return out


@router.post("/batches/{batch_id}/process")
def process_batch(batch_id: str, sync: bool = Query(True)):
    con = _connect()
    batch = _get_batch(con, batch_id)
    if not batch:
        con.close()
        raise HTTPException(status_code=404, detail="Batch not found")

    stored_path = batch.get("stored_path") or batch.get("storage_path")
    if not stored_path or not os.path.exists(stored_path):
        con.close()
        raise HTTPException(status_code=400, detail=f"Batch stored_path missing or not found: {stored_path}")

    cur = con.cursor()
    if "status" in batch:
        cur.execute("UPDATE raw_import_batches SET status=? WHERE batch_id=?", ("VALIDATING", batch_id))
        con.commit()

    # Try to run in-process validation + load using existing helpers
    try:
        if not load_table_from_file or not canonicalize_columns:
            # Fallback to worker if present
            if process_import:
                try:
                    process_import(batch_id=batch_id, stored_path=stored_path)
                except TypeError:
                    process_import(batch_id, stored_path)
                return {"status": "ok", "batch_id": batch_id, "processed_sync": sync}
            raise HTTPException(status_code=500, detail="No loader/worker available to process batch")

        # Load table (handles CSV and Excel header detection)
        df = None
        meta = {}
        try:
            if load_table_from_file:
                df, meta = load_table_from_file(stored_path)
        except Exception:
            df = None

        # fallback to pandas loader when helper not available or failed
        if df is None:
            try:
                ext = os.path.splitext(stored_path)[1].lower()
                if ext in (".xls", ".xlsx"):
                    df = pd.read_excel(stored_path, sheet_name=0, engine="openpyxl")
                else:
                    df = pd.read_csv(stored_path)
                meta = {"source": "pandas"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to read uploaded file: {e}")
        df = df.dropna(how="all")
        df.columns = [str(c).strip() for c in df.columns]

        # canonicalize and profile detection
        canonical_cols, orig_map = canonicalize_columns(list(df.columns))
        profile, score = (None, 0.0)
        if classify_profile:
            profile, score = classify_profile(set(canonical_cols))

        # validate required columns by delegating to loader which raises on missing
        con_loader = _connect()
        try:
            if ensure_fact_tables:
                ensure_fact_tables(con_loader)

            # Market dataset
            if profile == "USAREC_MARKET_CONTRACTS_SHARE":
                try:
                    load_usarec_market(con_loader, df, batch_id)
                except Exception as e:
                    # record batch-level error
                    # Attempt row-level validation and record errors
                    for idx, r in df.iterrows():
                        row_errs: List[str] = []
                        # FY
                        try:
                            fyv = r.get("FY") if "FY" in df.columns else r.get("fy") if "fy" in df.columns else None
                            if fyv is None or (str(fyv).strip() == ""):
                                row_errs.append("missing FY")
                            else:
                                int(str(fyv).strip())
                        except Exception:
                            row_errs.append(f"invalid FY: {fyv}")
                        # ZIP
                        try:
                            zipv = r.get("ZIP") if "ZIP" in df.columns else r.get("zip") if "zip" in df.columns else None
                            if zipv is None or str(zipv).strip() == "":
                                row_errs.append("missing ZIP")
                            else:
                                z = str(zipv).strip()
                                if not (len(z) == 5 and z.isdigit()):
                                    row_errs.append(f"invalid ZIP: {zipv}")
                        except Exception:
                            row_errs.append(f"invalid ZIP: {zipv}")
                        # Contracts
                        try:
                            contr = r.get("CONTR") if "CONTR" in df.columns else r.get("contr") if "contr" in df.columns else None
                            if contr is None or str(contr).strip() == "":
                                row_errs.append("missing Contracts")
                            else:
                                float(str(contr).replace(",", ""))
                        except Exception:
                            row_errs.append(f"invalid Contracts: {contr}")
                        # Share
                        try:
                            share = r.get("SHARE") if "SHARE" in df.columns else r.get("share") if "share" in df.columns else None
                            if share is None or str(share).strip() == "":
                                row_errs.append("missing Share")
                            else:
                                s = str(share).strip().replace("%", "").replace(",", "")
                                float(s)
                        except Exception:
                            row_errs.append(f"invalid Share: {share}")

                        if row_errs:
                            # insert into raw_import_rows
                            _insert_raw_row_error(con_loader, batch_id, int(idx) + 1, dict(r), row_errs)

                    # update batch-level status and return error
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"Market load failed: {e}")

            # ZIP category -> fact_zip_category
            elif profile == "USAREC_ZIP_CATEGORY":
                try:
                    load_usarec_zip_category(con_loader, df, batch_id)
                except Exception as e:
                    # per-row validation for ZIP category
                    for idx, r in df.iterrows():
                        row_errs: List[str] = []
                        zipv = r.get("ZIP") if "ZIP" in df.columns else r.get("zip") if "zip" in df.columns else None
                        if zipv is None or str(zipv).strip() == "":
                            row_errs.append("missing ZIP")
                        else:
                            z = str(zipv).strip()
                            if not (len(z) == 5 and z.isdigit()):
                                row_errs.append(f"invalid ZIP: {zipv}")
                        if row_errs:
                            _insert_raw_row_error(con_loader, batch_id, int(idx) + 1, dict(r), row_errs)
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"ZIP category load failed: {e}")

            # DOD org hierarchy
            elif profile == "DOD_ORG_HIERARCHY":
                try:
                    load_dod_org_hierarchy(con_loader, df, batch_id)
                except Exception as e:
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"Org hierarchy load failed: {e}")

            else:
                # Productivity loader (simple fallback): create fact_productivity and insert rows
                # normalize columns to lowercase keys
                cols_lc = [c.lower() for c in df.columns]
                # create table if not exists
                cur2 = con_loader.cursor()
                cur2.execute("""
                CREATE TABLE IF NOT EXISTS fact_productivity (
                  batch_id TEXT,
                  org_dim TEXT,
                  fy INTEGER,
                  month TEXT,
                  metric_name TEXT,
                  metric_value REAL,
                  imported_at TEXT
                );
                """)
                con_loader.commit()

                imported_at = _utc_now()
                rows_to_insert = []
                for _, r in df.iterrows():
                    # best-effort mapping
                    org = r.get("stn") or r.get("rsid") or r.get("co") or r.get("bn")
                    fy = r.get("fy") if "fy" in df.columns else None
                    month = r.get("month") if "month" in df.columns else None
                    # assume metric columns are numeric columns not in (stn, rsid, fy, month)
                    for c in df.columns:
                        if c.lower() in ("stn", "rsid", "co", "bn", "fy", "month"):
                            continue
                        try:
                            val = float(r.get(c)) if r.get(c) is not None and str(r.get(c)).strip() != "" else None
                        except Exception:
                            val = None
                        if val is not None:
                            rows_to_insert.append((batch_id, str(org) if org is not None else None, int(fy) if fy else None, str(month) if month else None, c, val, imported_at))

                if rows_to_insert:
                    cur2.executemany("INSERT INTO fact_productivity (batch_id, org_dim, fy, month, metric_name, metric_value, imported_at) VALUES (?,?,?,?,?,?,?)", rows_to_insert)
                    con_loader.commit()

            # mark loaded
            cur_final = con_loader.cursor()
            cur_final.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("LOADED", f"loaded profile={profile} score={score:.2f}", batch_id))
            con_loader.commit()
        finally:
            con_loader.close()

        return {"status": "ok", "batch_id": batch_id, "profile": profile, "score": score}

    except HTTPException:
        # propagate FastAPI errors
        raise
    except Exception as e:
        # set batch to error and record summary
        cur = con.cursor()
        try:
            cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
            con.commit()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
