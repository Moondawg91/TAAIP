from datetime import datetime
from typing import Dict, Iterable, List, Tuple

REQUIRED_FIELDS = {
    "school_id",
    "school_name",
    "station_rsid",
    "zip_code",
    "enrollment",
    "market_opportunity",
    "contacts_count",
    "events_count",
    "contracts_count",
    "school_zone_valid",
    "data_as_of",
    "source_dataset_name",
}


def _safe_str(v, default: str = "") -> str:
    if v is None:
        return default
    return str(v)


def _safe_float(v, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _safe_int(v, default: int = 0) -> int:
    try:
        if v is None:
            return default
        return int(float(v))
    except Exception:
        return default


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
    enrollment = _safe_int(row.get("enrollment"), 0)
    market_opportunity = _safe_float(row.get("market_opportunity"), 0.0)
    if market_opportunity == 0 and enrollment > 0:
        market_opportunity = float(enrollment)

    return {
        "school_id": _safe_str(row.get("school_id")),
        "school_name": _safe_str(row.get("school_name")),
        "station_rsid": _safe_str(row.get("station_rsid")),
        "zip_code": _safe_str(row.get("zip_code")),
        "enrollment": enrollment,
        "market_opportunity": market_opportunity,
        "contacts_count": _safe_int(row.get("contacts_count"), 0),
        "events_count": _safe_int(row.get("events_count"), 0),
        "contracts_count": _safe_int(row.get("contracts_count"), 0),
        "school_zone_valid": bool(row.get("school_zone_valid")),
        "dod_access_ratio": _safe_float(row.get("dod_access_ratio"), 0.0),
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
        if not n["school_id"]:
            errors.append(f"row[{idx}] missing school_id")
            continue
        if not n["station_rsid"]:
            errors.append(f"row[{idx}] missing station_rsid")
            continue
        normalized.append(n)

    return len(errors) == 0, errors, normalized


def validate_schema_columns(columns: Iterable[str]) -> Tuple[bool, List[str]]:
    cols = {str(c) for c in columns}
    school_ok = "school_id" in cols or "id" in cols
    station_ok = "station_rsid" in cols or "org_unit_id" in cols
    name_ok = "school_name" in cols or "name" in cols
    if not school_ok:
        return False, ["missing school identifier column (school_id/id)"]
    if not station_ok:
        return False, ["missing station scope column (station_rsid/org_unit_id)"]
    if not name_ok:
        return False, ["missing school name column (school_name/name)"]
    return True, []
