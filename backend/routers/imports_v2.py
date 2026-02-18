from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form
from typing import Optional, List, Any, Dict
import os, uuid, sqlite3, hashlib, json
import pandas as pd
from datetime import datetime, timezone
import importlib

try:
    from backend.datasets.registry import DatasetRegistry
except Exception:
    DatasetRegistry = None

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
        load_usarec_sama,
        load_usarec_market,
        load_usarec_zip_category,
        load_dod_org_hierarchy,
    )
except Exception:
    load_table_from_file = None
    canonicalize_columns = None
    classify_profile = None
    ensure_fact_tables = None
    load_usarec_sama = None
    load_usarec_market = None
    load_usarec_zip_category = None
    load_dod_org_hierarchy = None

router = APIRouter(prefix="/api/v2/imports", tags=["imports"])

# Prefer repository-root DB and uploads directory for local development
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB = os.getenv("DB_PATH") or os.path.join(ROOT, "recruiting.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR") or os.path.join(ROOT, "uploads")
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


def _ensure_batches_columns(con: sqlite3.Connection):
    """Ensure legacy columns exist on raw_import_batches to avoid manual ALTERs."""
    try:
        cur = con.cursor()
        cur.execute("PRAGMA table_info(raw_import_batches)")
        cols = {r[1] for r in cur.fetchall()}
        if "raw_rows_inserted" not in cols:
            cur.execute("ALTER TABLE raw_import_batches ADD COLUMN raw_rows_inserted INTEGER DEFAULT 0;")
        if "inserted_rows" not in cols:
            cur.execute("ALTER TABLE raw_import_batches ADD COLUMN inserted_rows INTEGER DEFAULT 0;")
        con.commit()
    except Exception:
        # best-effort: ignore errors to avoid crashing startup
        try:
            con.rollback()
        except Exception:
            pass


def _get_batch(con: sqlite3.Connection, batch_id: str) -> Optional[Dict[str, Any]]:
    cur = con.cursor()
    cur.execute("SELECT * FROM raw_import_batches WHERE batch_id=? LIMIT 1", (batch_id,))
    row = cur.fetchone()
    return dict(row) if row else None


_REGISTRY = None


def _get_registry() -> Optional[DatasetRegistry]:
    global _REGISTRY
    if _REGISTRY is None:
        try:
            if DatasetRegistry:
                _REGISTRY = DatasetRegistry.load(os.path.join(os.path.dirname(__file__), "..", "datasets", "datasets.yaml"))
        except Exception:
            _REGISTRY = None
    return _REGISTRY


def _import_loader(path: str):
    """
    Import loader function given a path. Supports both 'module.fn' and 'module:fn' styles.
    """
    if not path:
        raise ImportError("No loader path provided")
    if ":" in path:
        mod_path, fn = path.split(":", 1)
    else:
        mod_path, fn = path.rsplit(".", 1)
    mod = importlib.import_module(mod_path)
    return getattr(mod, fn)


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


def _insert_raw_rows(con: sqlite3.Connection, batch_id: str, df) -> int:
    """Insert all rows from a pandas DataFrame into raw_import_rows as JSON.
    Returns number of rows inserted.
    """
    cur = con.cursor()
    import json as _json
    rows = []
    for idx, (_, r) in enumerate(df.iterrows()):
        try:
            # convert Series to plain dict (cast numpy types)
            row_obj = {str(k): (None if pd.isna(v) else v) for k, v in r.items()}
        except Exception:
            # fallback: coerce via to_dict
            try:
                row_obj = r.to_dict()
            except Exception:
                row_obj = {}
        payload = _json.dumps(row_obj, default=str)
        rows.append((batch_id, int(idx) + 1, payload))

    if not rows:
        return 0

    try:
        cur.executemany("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?,?,?)", rows)
        con.commit()
        return len(rows)
    except Exception:
        # try inserting one-by-one to avoid failure on large payloads
        inserted = 0
        for r in rows:
            try:
                cur.execute("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?,?,?)", r)
                inserted += 1
            except Exception:
                continue
        con.commit()
        return inserted


def _persist_raw_rows(con: sqlite3.Connection, batch_id: str, df) -> int:
    """Ensure `raw_import_rows` exists, delete any previous rows for this batch,
    then insert every row from `df` as JSON. Update raw_import_batches.raw_rows_inserted.
    Returns number of rows inserted.
    """
    import json as _json
    cur = con.cursor()

    # Ensure table exists (safe)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_import_rows (
      batch_id TEXT NOT NULL,
      row_index INTEGER NOT NULL,
      row_json TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now')),
      PRIMARY KEY (batch_id, row_index)
    );
    """)
    con.commit()

    # Clear any previous raw rows for idempotent re-process
    cur.execute("DELETE FROM raw_import_rows WHERE batch_id = ?", (batch_id,))
    con.commit()

    rows = []
    try:
        recs = df.to_dict(orient="records")
    except Exception:
        # fallback: iterate rows
        recs = []
        for _, r in df.iterrows():
            try:
                recs.append({str(k): (None if pd.isna(v) else v) for k, v in r.items()})
            except Exception:
                try:
                    recs.append(r.to_dict())
                except Exception:
                    recs.append({})

    for i, rec in enumerate(recs):
        try:
            payload = _json.dumps(rec, ensure_ascii=False, default=str)
        except Exception:
            try:
                payload = _json.dumps({k: (None if pd.isna(v) else v) for k, v in rec.items()}, default=str)
            except Exception:
                payload = _json.dumps({}, default=str)
        rows.append((batch_id, int(i), payload))

    inserted = 0
    if rows:
        try:
            cur.executemany("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?,?,?)", rows)
            con.commit()
            inserted = len(rows)
        except Exception:
            # try one-by-one
            for r in rows:
                try:
                    cur.execute("INSERT INTO raw_import_rows (batch_id, row_index, row_json) VALUES (?,?,?)", r)
                    inserted += 1
                except Exception:
                    continue
            con.commit()

    # Best-effort update of batch counter
    try:
        cur.execute("UPDATE raw_import_batches SET raw_rows_inserted = ? WHERE batch_id = ?", (inserted, batch_id))
        con.commit()
    except Exception:
        try:
            con.rollback()
        except Exception:
            pass

    return inserted


@router.post("/upload")
async def imports_upload(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),

    source_system_q: Optional[str] = Query(None, alias="source_system"),
    source_system_f: Optional[str] = Form(None, alias="source_system"),

    dataset_key_q: Optional[str] = Query(None, alias="dataset_key"),
    dataset_key_f: Optional[str] = Form(None, alias="dataset_key"),
):
    chosen = files[0] if files else file
    if not chosen:
        raise HTTPException(status_code=400, detail="No file provided")

    data = await chosen.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")

    ext = os.path.splitext(chosen.filename or "")[1] or ""
    # pick source_system from query or form early so filename is stable
    source_system = source_system_q or source_system_f or "USAREC"
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

    # attempt to canonicalize column names for internal use, but pass
    # the original column strings to the deterministic classifier which
    # expects human-readable tokens (e.g. 'sum of contracts').
    columns_to_classify = columns
    try:
        if canonicalize_columns and columns:
            try:
                canonical_cols, _orig_map = canonicalize_columns(columns)
            except Exception:
                canonical_cols = None
    except Exception:
        canonical_cols = None

    if classify and columns:
        try:
            # pass original (un-canonicalized) columns to registry.classify
            dataset_key = classify(columns, source_system)
        except Exception:
            dataset_key = None

    # allow caller to explicitly override dataset detection (query OR form)
    dataset_key = dataset_key or "unknown"
    final_dataset_key = dataset_key_q or dataset_key_f or dataset_key or "unknown"
    fhash = _file_hash(dest)
    batch_id = uuid.uuid4().hex
    imported_at = _utc_now()

    con = _connect()
    _ensure_batches_columns(con)
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
        "detected_profile": final_dataset_key,
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
        "dataset_key": final_dataset_key,
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


@router.get("/batches/{batch_id}/rows")
def get_batch_rows(batch_id: str, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    con = _connect()
    try:
        if not _table_exists(con, "raw_import_batches"):
            raise HTTPException(status_code=404, detail="Batch not found")
        cur = con.cursor()
        exists = cur.execute("SELECT 1 FROM raw_import_batches WHERE batch_id=? LIMIT 1", (batch_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Batch not found")

        if not _table_exists(con, "raw_import_rows"):
            return {"batch_id": batch_id, "total": 0, "limit": limit, "offset": offset, "rows": []}

        rows = cur.execute("SELECT row_index, row_json FROM raw_import_rows WHERE batch_id=? ORDER BY row_index ASC LIMIT ? OFFSET ?", (batch_id, limit, offset)).fetchall()
        parsed = []
        for r in rows:
            try:
                parsed.append({"row_index": r[0], "row": json.loads(r[1])})
            except Exception:
                parsed.append({"row_index": r[0], "row": r[1]})

        total = cur.execute("SELECT COUNT(*) FROM raw_import_rows WHERE batch_id=?", (batch_id,)).fetchone()[0]
        return {"batch_id": batch_id, "total": total, "limit": limit, "offset": offset, "rows": parsed}
    finally:
        con.close()


@router.get("/batches/{batch_id}/preview")
def get_batch_preview(batch_id: str, limit: int = Query(25, ge=1, le=200)):
    con = _connect()
    try:
        cur = con.cursor()
        exists = cur.execute("SELECT 1 FROM raw_import_batches WHERE batch_id=? LIMIT 1", (batch_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Batch not found")

        if not _table_exists(con, "raw_import_rows"):
            return {"batch_id": batch_id, "columns": [], "rows": []}

        rows = cur.execute("SELECT row_json FROM raw_import_rows WHERE batch_id=? ORDER BY row_index ASC LIMIT ?", (batch_id, limit)).fetchall()
        parsed_rows = []
        for r in rows:
            try:
                parsed_rows.append(json.loads(r[0]))
            except Exception:
                pass

        # derive columns from union of keys
        col_set = []
        seen = set()
        for rr in parsed_rows:
            for k in rr.keys():
                if k not in seen:
                    seen.add(k)
                    col_set.append(k)

        return {"batch_id": batch_id, "columns": col_set, "rows": parsed_rows}
    finally:
        con.close()


@router.post("/batches/{batch_id}/process")
def process_batch(batch_id: str, sync: bool = Query(True)):
    con = _connect()
    _ensure_batches_columns(con)
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

        # Persist raw rows for auditing/UI and update batch metadata
        try:
            raw_count = _persist_raw_rows(con, batch_id, df)
        except Exception:
            raw_count = 0

        # canonicalize and profile detection
        canonical_cols, orig_map = canonicalize_columns(list(df.columns))
        profile, score = (None, 0.0)

        # Registry-first: if a dataset registry spec exists for this batch, use it.
        try:
            REG = _get_registry()
            dataset_key = batch.get("detected_profile")
            dataset_key_effective = dataset_key if dataset_key and dataset_key != "unknown" else None
            spec = REG.get(dataset_key_effective) if REG and dataset_key_effective else None
        except Exception:
            spec = None

        if spec:
            # If XLSX and registry provides sheet/header info, re-read using those hints
            try:
                ext = os.path.splitext(stored_path)[1].lower()
                if ext in (".xls", ".xlsx"):
                    sheet = spec.default_sheet if spec.default_sheet is not None else 0
                    header = int(spec.header_row) if spec.header_row is not None else 0
                    try:
                        df = pd.read_excel(stored_path, sheet_name=sheet, header=header, engine="openpyxl")
                    except Exception:
                        df = pd.read_excel(stored_path, sheet_name=sheet, header=header)
                else:
                    # keep CSV handling as-is
                    df = pd.read_csv(stored_path)
                df = df.dropna(how="all")
                df.columns = [str(c).strip() for c in df.columns]
            except Exception:
                # if re-read fails, keep earlier df and continue
                pass

            # recanonicalize after potential re-read
            try:
                canonical_cols, orig_map = canonicalize_columns(list(df.columns))
            except Exception:
                canonical_cols = [c for c in df.columns]

            # validate required columns (case-insensitive)
            missing = []
            try:
                want = [c.lower() for c in (spec.required_columns_norm or [])]
                have = {c.lower() for c in canonical_cols}
                missing = [c for c in want if c and c not in have]
            except Exception:
                missing = []

            if missing:
                cur_final = con.cursor()
                try:
                    cur_final.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id= ?", ("ERROR", f"Missing required columns: {missing}", batch_id))
                    con.commit()
                except Exception:
                    pass
                raise HTTPException(status_code=400, detail=f"Missing required columns for {spec.dataset_key}: {missing}")

            # call registry-specified loader if present
            if spec.loader:
                try:
                    loader_fn = _import_loader(spec.loader)
                    inserted_rows = 0
                    try:
                        inserted_rows = loader_fn(con_loader, df, batch_id) or 0
                    except TypeError:
                        inserted_rows = loader_fn(con_loader, stored_path, batch_id) or 0

                    # update batch counters and mark loaded
                    cur_final = con_loader.cursor()
                    try:
                        cur_final.execute(
                            "UPDATE raw_import_batches SET status=?, detected_profile=?, inserted_rows=COALESCE(inserted_rows,0)+?, raw_rows_inserted=? WHERE batch_id=?",
                            ("LOADED", spec.dataset_key, int(inserted_rows), int(raw_count), batch_id),
                        )
                        con_loader.commit()
                    except Exception:
                        try:
                            con_loader.commit()
                        except Exception:
                            pass

                    return {
                        "status": "ok",
                        "batch_id": batch_id,
                        "profile": spec.dataset_key,
                        "inserted_rows": int(inserted_rows),
                        "raw_rows_inserted": int(raw_count),
                    }
                except HTTPException:
                    raise
                except Exception as e:
                    cur_err = con_loader.cursor()
                    try:
                        cur_err.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                        con_loader.commit()
                    except Exception:
                        pass
                    raise HTTPException(status_code=400, detail=f"Registry loader failed: {e}")

        # If the batch was pre-classified at upload time, prefer that
        # but map dataset registry keys to the internal profile constants used
        # in this router.
        dataset_key = batch.get("detected_profile")
        DATASET_KEY_TO_PROFILE = {
            "usarec_market_share_contracts": "USAREC_MARKET_CONTRACTS_SHARE",
            "usarec_vol_contracts_by_service": "USAREC_MARKET_CONTRACTS_SHARE",
            "usarec_zip_by_category": "USAREC_ZIP_CATEGORY",
        }
        if dataset_key and dataset_key != "unknown":
            profile = DATASET_KEY_TO_PROFILE.get(dataset_key, dataset_key)
            score = 1.0
        else:
            if classify_profile:
                profile, score = classify_profile(set(canonical_cols))

        # deterministic dataset detection overrides heuristic when possible
        try:
            from backend.ingestion.dataset_registry import detect_dataset
            detected = detect_dataset({c for c in df.columns}, source_system)
            if detected:
                profile = detected
                score = 1.0
        except Exception:
            detected = None

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
                    # try a tolerant fallback loader before failing
                    try:
                        from backend.ingestion.loaders.market_share_loader import load_market_share
                        load_market_share(con_loader, stored_path, batch_id)
                    except Exception:
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

            # Mission category
            elif profile == "MISSION_CATEGORY":
                try:
                    from backend.ingestion.loaders.mission_loader import load_mission
                    inserted = load_mission(con_loader, stored_path, batch_id)
                except Exception as e:
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"Mission load failed: {e}")

            # Test scores
            elif profile == "TEST_SCORE_AVG":
                try:
                    from backend.ingestion.loaders.test_score_loader import load_test_scores
                    inserted = load_test_scores(con_loader, stored_path, batch_id)
                except Exception as e:
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"Test scores load failed: {e}")

            # Urbanicity CBSA
            elif profile == "URBANICITY_CBSA":
                try:
                    from backend.ingestion.loaders.urbanicity_loader import load_urbanicity
                    inserted = load_urbanicity(con_loader, stored_path, batch_id)
                except Exception as e:
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"Urbanicity load failed: {e}")

            # SAMA dataset
            if profile == "USAREC_SAMA":
                try:
                    if load_usarec_sama:
                        load_usarec_sama(con_loader, df, batch_id)
                    else:
                        # try ingestion loader
                        from backend.ingestion.loaders.sama_loader import load_sama as _ls
                        _ls(con_loader, stored_path, batch_id)
                except Exception as e:
                    cur = con_loader.cursor()
                    cur.execute("UPDATE raw_import_batches SET status=?, notes=? WHERE batch_id=?", ("ERROR", str(e), batch_id))
                    con_loader.commit()
                    raise HTTPException(status_code=400, detail=f"SAMA load failed: {e}")

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
