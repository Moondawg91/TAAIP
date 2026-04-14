from datetime import datetime
from typing import Dict, Iterable, List, Tuple

REQUIRED_FIELDS = {
    "lead_key",
    "station_rsid",
    "flash_to_bang_days",
    "avg_stage_age_days",
    "stall_flag",
    "processing_bottleneck_flag",
    "data_as_of",
    "source_dataset_name",
}


def _safe_float(v, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _safe_str(v, default: str = "") -> str:
    if v is None:
        return default
    return str(v)


def _safe_iso(v) -> str:
    if v is None:
        return ""
    s = str(v)
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return s
    return s


def normalize_row(row: Dict) -> Dict:
    return {
        "lead_key": _safe_str(row.get("lead_key")),
        "station_rsid": _safe_str(row.get("station_rsid")),
        "flash_to_bang_days": _safe_float(row.get("flash_to_bang_days"), 0.0),
        "avg_stage_age_days": _safe_float(row.get("avg_stage_age_days"), 0.0),
        "stall_flag": bool(row.get("stall_flag")),
        "processing_bottleneck_flag": bool(row.get("processing_bottleneck_flag")),
        "prospecting_problem": bool(row.get("prospecting_problem")),
        "engagement_problem": bool(row.get("engagement_problem")),
        "processing_problem": bool(row.get("processing_problem")),
        "future_soldier_management_problem": bool(row.get("future_soldier_management_problem")),
        "data_as_of": _safe_iso(row.get("data_as_of")),
        "source_dataset_name": _safe_str(row.get("source_dataset_name")),
    }


def validate_rows(rows: Iterable[Dict]) -> Tuple[bool, List[str], List[Dict]]:
    errors: List[str] = []
    normalized: List[Dict] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row[{idx}] is not an object")
            continue
        n = normalize_row(row)
        missing = [k for k in REQUIRED_FIELDS if k not in n]
        if missing:
            errors.append(f"row[{idx}] missing fields: {','.join(sorted(missing))}")
            continue
        if not n["lead_key"]:
            errors.append(f"row[{idx}] missing lead_key")
            continue
        if not n["station_rsid"]:
            errors.append(f"row[{idx}] missing station_rsid")
            continue
        normalized.append(n)

    return len(errors) == 0, errors, normalized


def validate_schema_columns(columns: Iterable[str]) -> Tuple[bool, List[str]]:
    cols = {str(c) for c in columns}
    lead_ok = "lead_key" in cols
    station_ok = "station_rsid" in cols
    transitioned_ok = "transitioned_at" in cols or "created_at" in cols
    if not lead_ok:
        return False, ["missing lead key column (lead_key)"]
    if not station_ok:
        return False, ["missing station scope column (station_rsid)"]
    if not transitioned_ok:
        return False, ["missing transition timestamp column (transitioned_at/created_at)"]
    return True, []
