from datetime import datetime
from typing import Dict, Iterable, List, Tuple

REQUIRED_FIELDS = {
    "zip_code",
    "station_rsid",
    "company_prefix",
    "battalion_prefix",
    "brigade_prefix",
    "qma_population",
    "qma_density",
    "market_population",
    "market_category",
    "production_actual",
    "contracts_actual",
    "write_rate_actual",
    "reporting_period",
    "data_as_of",
    "source_dataset_name",
}


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_str(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _safe_iso(value) -> str:
    if value is None:
        return ""
    s = str(value)
    # Keep this permissive: if parse fails we still return the original string.
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return s
    return s


def normalize_row(row: Dict) -> Dict:
    station = _safe_str(row.get("station_rsid"))
    company = _safe_str(row.get("company_prefix") or station[:3])
    battalion = _safe_str(row.get("battalion_prefix") or station[:2])
    brigade = _safe_str(row.get("brigade_prefix") or station[:1])

    qma_population = _safe_float(row.get("qma_population"), 0.0)
    market_population = _safe_float(row.get("market_population"), qma_population)
    contracts_actual = _safe_float(row.get("contracts_actual"), 0.0)
    production_actual = _safe_float(row.get("production_actual"), contracts_actual)

    qma_density = _safe_float(row.get("qma_density"), 0.0)
    if qma_density < 0:
        qma_density = 0.0

    write_rate_actual = _safe_float(row.get("write_rate_actual"), 0.0)
    if qma_population > 0 and write_rate_actual == 0.0:
        write_rate_actual = contracts_actual / qma_population

    return {
        "zip_code": _safe_str(row.get("zip_code")),
        "station_rsid": station,
        "company_prefix": company,
        "battalion_prefix": battalion,
        "brigade_prefix": brigade,
        "qma_population": qma_population,
        "qma_density": qma_density,
        "market_population": market_population,
        "market_category": _safe_str(row.get("market_category") or "UNK"),
        "production_actual": production_actual,
        "contracts_actual": contracts_actual,
        "write_rate_actual": write_rate_actual,
        "reporting_period": _safe_str(row.get("reporting_period")),
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
        if not n["zip_code"]:
            errors.append(f"row[{idx}] missing zip_code")
            continue
        if not n["station_rsid"]:
            errors.append(f"row[{idx}] missing station_rsid")
            continue
        if n["qma_population"] < 0 or n["market_population"] < 0:
            errors.append(f"row[{idx}] has negative population values")
            continue
        normalized.append(n)

    return len(errors) == 0, errors, normalized


def validate_schema_columns(columns: Iterable[str]) -> Tuple[bool, List[str]]:
    cols = {str(c) for c in columns}
    # Accept any source schema that can be mapped into the contract.
    minimal = {"market_category"}
    zip_ok = "zip_code" in cols or "zip5" in cols or "zip" in cols
    pop_ok = "qma_population" in cols or "fqma" in cols or "population" in cols
    station_ok = "station_rsid" in cols or "rsid_prefix" in cols
    if not zip_ok:
        return False, ["missing zip identifier column (zip_code/zip5/zip)"]
    if not pop_ok:
        return False, ["missing qma population column (qma_population/fqma/population)"]
    if not station_ok:
        return False, ["missing station identifier column (station_rsid/rsid_prefix)"]
    missing_min = sorted([c for c in minimal if c not in cols])
    if missing_min:
        return False, [f"missing required columns: {','.join(missing_min)}"]
    return True, []
