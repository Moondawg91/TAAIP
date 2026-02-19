import os
import json
import time
import glob
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests
import pandas as pd

from backend.datasets.registry import DatasetRegistry

API_BASE = os.environ.get("TAAIP_API", "http://127.0.0.1:8000")
UPLOADS_DIR = os.environ.get("TAAIP_UPLOADS", "uploads")
REG_PATH = os.environ.get("TAAIP_DATASETS", "backend/datasets/datasets.yaml")


def norm_col(s: str) -> str:
    s = str(s).strip().upper()
    s = re.sub(r"[^A-Z0-9]+", "", s)
    return s


def read_headers(path: str) -> List[str]:
    ext = os.path.splitext(path)[1].lower()

    if ext in (".xlsx", ".xls"):
        # Read first sheet with header guess at row 0
        df = pd.read_excel(path, sheet_name=0, header=0, engine="openpyxl")
        cols = [str(c).strip() for c in df.columns if str(c).strip()]
        return cols

    # CSV
    df = pd.read_csv(path, nrows=1)
    cols = [str(c).strip() for c in df.columns if str(c).strip()]
    return cols


def score_match(required_norm: List[str], file_cols: List[str]) -> Tuple[int, int, List[str]]:
    """
    Returns: (hit_count, required_count, missing_required_norm)
    """
    if not required_norm:
        return (0, 0, [])

    file_norm = {norm_col(c) for c in file_cols}
    req_norm = [norm_col(c) for c in required_norm]

    missing = [c for c in req_norm if c not in file_norm]
    hit = len(req_norm) - len(missing)
    return hit, len(req_norm), missing


def choose_dataset_key(reg: DatasetRegistry, file_cols: List[str]) -> Tuple[Optional[str], Dict]:
    """
    Pick the dataset_key with the highest required column coverage.
    """
    best_key = None
    best = (-1, 10**9)  # (hit_count, missing_count)
    best_info = {}

    for key in reg.keys():
        spec = reg.get(key)
        req = spec.required_columns_norm or []
        hit, total, missing = score_match(req, file_cols)

        # prefer: more hits; tie-breaker: fewer missing
        if total == 0:
            continue
        missing_count = len(missing)
        if (hit, -missing_count) > (best[0], -best[1]):
            best_key = key
            best = (hit, missing_count)
            best_info = {
                "hit": hit,
                "total_required": total,
                "missing_required": missing,
                "required_norm": req,
            }

    return best_key, best_info


def upload_file(path: str, dataset_key: str, source_system: str = "USAREC") -> str:
    with open(path, "rb") as f:
        files = {"file": (os.path.basename(path), f)}
        data = {"source_system": source_system, "dataset_key": dataset_key}
        r = requests.post(f"{API_BASE}/api/v2/imports/upload", files=files, data=data, timeout=120)
    r.raise_for_status()
    j = r.json()
    return j["batch_id"]


def process_batch(batch_id: str) -> Dict:
    r = requests.post(f"{API_BASE}/api/v2/imports/batches/{batch_id}/process", timeout=300)
    r.raise_for_status()
    return r.json()


def get_rows(batch_id: str, limit: int = 5) -> Dict:
    r = requests.get(f"{API_BASE}/api/v2/imports/batches/{batch_id}/rows", params={"limit": limit}, timeout=60)
    r.raise_for_status()
    return r.json()


def get_preview(batch_id: str, limit: int = 10) -> Dict:
    r = requests.get(f"{API_BASE}/api/v2/imports/batches/{batch_id}/preview", params={"limit": limit}, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    print(f"API_BASE = {API_BASE}")
    print(f"UPLOADS_DIR = {UPLOADS_DIR}")
    print(f"REG_PATH = {REG_PATH}")
    print()

    reg = DatasetRegistry.load(REG_PATH)
    print(f"Loaded registry datasets: {len(reg.keys())}")
    print()

    paths = []
    paths += glob.glob(os.path.join(UPLOADS_DIR, "*.xlsx"))
    paths += glob.glob(os.path.join(UPLOADS_DIR, "*.xls"))
    paths += glob.glob(os.path.join(UPLOADS_DIR, "*.csv"))

    if not paths:
        print("No files found in uploads/. Put your real XLSX/CSV there first.")
        return

    results = []

    for p in sorted(paths):
        print("=" * 88)
        print(f"FILE: {p}")
        try:
            cols = read_headers(p)
            print(f"Detected columns ({len(cols)}): {cols[:12]}{'...' if len(cols) > 12 else ''}")

            key, info = choose_dataset_key(reg, cols)
            if not key:
                print("❌ No matching dataset_key found based on required_columns_norm.")
                results.append((p, None, "NO_MATCH", info))
                continue

            print(f"✅ Matched dataset_key: {key}  (hits={info.get('hit')}/{info.get('total_required')})")
            if info.get("missing_required"):
                print(f"⚠️ Missing required (normalized): {info['missing_required'][:12]}")

            batch_id = upload_file(p, key, source_system="USAREC")
            print(f"Uploaded → batch_id={batch_id}")

            out = process_batch(batch_id)
            print("Processed →", json.dumps(out, indent=2))

            rows = get_rows(batch_id, limit=5)
            prev = get_preview(batch_id, limit=10)

            raw_count = len(rows.get("rows", [])) if isinstance(rows, dict) else 0
            prev_cols = prev.get("columns", [])
            prev_rows = prev.get("rows", [])

            print(f"Rows endpoint returned: {raw_count} row(s)")
            print(f"Preview columns: {len(prev_cols)} | preview rows: {len(prev_rows)}")

            results.append((p, key, "OK", {"batch_id": batch_id, "process": out}))
        except requests.HTTPError as e:
            try:
                body = e.response.text
            except Exception:
                body = ""
            print(f"❌ HTTP error: {e} \n{body[:1500]}")
            results.append((p, None, "HTTP_ERROR", {"error": str(e), "body": body[:1500]}))
        except Exception as e:
            print(f"❌ Exception: {repr(e)}")
            results.append((p, None, "EXCEPTION", {"error": repr(e)}))

    print("\n\n" + "#" * 88)
    print("SUMMARY")
    ok = [r for r in results if r[2] == "OK"]
    bad = [r for r in results if r[2] != "OK"]
    print(f"OK: {len(ok)}  |  FAIL: {len(bad)}")
    for p, key, status, info in results:
        print(f"- {status:10} | {os.path.basename(p):50} | {key or '-'}")
    print("#" * 88)


if __name__ == "__main__":
    main()
