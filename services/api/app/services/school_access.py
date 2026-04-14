import glob
import os
import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from starlette.exceptions import HTTPException

from services.api.app.services import school_access_contract


def _scope_prefix(scope_type: str, scope_value: str) -> str:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip()
    if st == "USAREC":
        return ""
    if st == "BDE":
        return sv[:1]
    if st == "BN":
        return sv[:2]
    if st == "CO":
        return sv[:3]
    if st == "STN":
        return sv[:4]
    return sv


def enforce_scope(actor_scope_type: str, actor_scope_value: str, request_scope_type: str, request_scope_value: str) -> None:
    a_type = (actor_scope_type or "USAREC").upper().strip()
    r_type = (request_scope_type or "USAREC").upper().strip()
    a_val = (actor_scope_value or "USAREC").strip()
    r_val = (request_scope_value or "USAREC").strip()
    if a_type == "USAREC":
        return
    if r_type == "USAREC":
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")
    a_prefix = _scope_prefix(a_type, a_val)
    r_prefix = _scope_prefix(r_type, r_val)
    if a_prefix and not r_prefix.startswith(a_prefix):
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")


def _safe_table_exists(db, table_name: str) -> bool:
    q = text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n")
    return bool(db.execute(q, {"n": table_name}).first())


def _table_columns(db, table_name: str) -> List[str]:
    rows = db.execute(text(f"PRAGMA table_info('{table_name}')")).mappings().all()
    return [str(r.get("name")) for r in rows]


def _pick(row: Dict, names: Iterable[str], default=None):
    for n in names:
        if n in row and row.get(n) is not None:
            return row.get(n)
    return default


def _resolve_school_contacts_dataset_path() -> Optional[str]:
    env_path = os.getenv("TAAIP_SCHOOL_CONTACTS_DATASET_PATH")
    if env_path is not None:
        return env_path if os.path.exists(env_path) else None

    candidates = [
        "./data/dev_datasets/school contacts.xlsx",
        "./uploads/school contacts.xlsx",
        "./data/uploads/school contacts.xlsx",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p

    matches: List[str] = []
    for pattern in ["./**/*school*contacts*.xlsx", "./**/*school*contacts*.xls"]:
        matches.extend(glob.glob(pattern, recursive=True))
    matches = sorted({m for m in matches if os.path.isfile(m)})
    return matches[-1] if matches else None


def _clean_school_name(raw_value) -> str:
    s = str(raw_value or "").strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return ""
    return re.sub(r"\s*\([A-Z0-9]{3,6}\)\s*$", "", s).strip()


def _to_int(value, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def _load_from_contacts_workbook(scope_type: str, scope_value: str) -> Tuple[str, List[Dict], str, str]:
    dataset_path = _resolve_school_contacts_dataset_path()
    if not dataset_path:
        return "no_active_dataset", [], "", ""

    try:
        raw = pd.read_excel(dataset_path, header=None)
    except Exception as exc:
        return "invalid_dataset_schema", [], "", f"unable to read school contacts workbook: {exc}"

    if raw.empty:
        return "no_active_dataset", [], "", ""

    header_idx = None
    for idx in range(min(len(raw), 10)):
        vals = [str(v).strip().lower() for v in raw.iloc[idx].tolist() if str(v).strip() and str(v).strip().lower() not in {"nan", "none"}]
        if any(v == "rsid" for v in vals) and any("school name" in v for v in vals):
            header_idx = idx
            break

    if header_idx is None:
        return "invalid_dataset_schema", [], "", "school contacts workbook header row not found"

    columns = []
    for idx, value in enumerate(raw.iloc[header_idx].tolist()):
        label = str(value).strip()
        if not label or label.lower() in {"nan", "none"}:
            label = f"column_{idx}"
        columns.append(label)

    df = raw.iloc[header_idx + 1 :].copy()
    df.columns = columns
    df = df.dropna(how="all")
    if df.empty:
        return "no_active_dataset", [], "", ""

    def _find_column(predicate):
        for col in df.columns:
            try:
                if predicate(str(col).lower()):
                    return col
            except Exception:
                continue
        return None

    station_col = _find_column(lambda c: "rsid" in c)
    name_col = _find_column(lambda c: "school" in c and "name" in c)
    population_col = _find_column(lambda c: c == "population" or "population" in c)
    available_col = _find_column(lambda c: "available" in c and "student" in c)
    contacted_col = _find_column(lambda c: "contacted students" in c and "365" not in c and "%" not in c)

    if station_col is None or name_col is None:
        return "invalid_dataset_schema", [], "", "school contacts workbook missing RSID or school name columns"

    prefix = _scope_prefix(scope_type, scope_value)
    data_as_of = datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z"

    out: List[Dict] = []
    for _, row in df.iterrows():
        station = str(row.get(station_col) or "").strip().upper()
        if not station:
            continue
        if prefix and not station.startswith(prefix):
            continue

        raw_name = str(row.get(name_col) or "").strip()
        if not raw_name or raw_name.lower() in {"nan", "none", "null"}:
            continue

        school_name = _clean_school_name(raw_name) or raw_name
        population = _to_int(row.get(population_col), 0) if population_col else 0
        available = _to_int(row.get(available_col), 0) if available_col else 0
        contacts = _to_int(row.get(contacted_col), 0) if contacted_col else 0
        opportunity = float(available or population or 0)
        dod_access_ratio = float(contacts) / float(max(1, available or population or 1))

        out.append(
            {
                "school_id": raw_name,
                "school_name": school_name,
                "station_rsid": station,
                "zip_code": "",
                "enrollment": population,
                "market_opportunity": opportunity,
                "contacts_count": contacts,
                "events_count": 0,
                "contracts_count": 0,
                "school_zone_valid": True,
                "dod_access_ratio": round(dod_access_ratio, 4),
                "data_as_of": data_as_of,
                "source_dataset_name": os.path.basename(dataset_path),
            }
        )

    if not out:
        return "no_active_dataset", [], "", ""

    ok, errors, normalized = school_access_contract.validate_rows(out)
    if not ok:
        return "invalid_dataset_schema", [], "", "; ".join(errors[:10])

    normalized.sort(key=lambda x: (str(x.get("station_rsid") or ""), str(x.get("school_name") or ""), str(x.get("school_id") or "")))
    return "ok", normalized, data_as_of, ""


def _load_school_rows(db, scope_type: str, scope_value: str) -> Tuple[str, List[Dict], str, str]:
    if not _safe_table_exists(db, "schools"):
        workbook_status, workbook_rows, workbook_as_of, workbook_error = _load_from_contacts_workbook(scope_type, scope_value)
        if workbook_status == "ok" and workbook_rows:
            return workbook_status, workbook_rows, workbook_as_of, workbook_error
        if not _safe_table_exists(db, "fact_school_contacts"):
            return workbook_status, workbook_rows, workbook_as_of, workbook_error
        contact_count = db.execute(text("SELECT COUNT(1) AS c FROM fact_school_contacts")).mappings().first()
        if int((contact_count or {}).get("c") or 0) <= 0:
            return workbook_status, workbook_rows, workbook_as_of, workbook_error
        return _load_from_contacts_fallback(db, scope_type, scope_value)

    cols = _table_columns(db, "schools")
    valid, schema_errors = school_access_contract.validate_schema_columns(cols)
    if not valid:
        workbook_status, workbook_rows, workbook_as_of, workbook_error = _load_from_contacts_workbook(scope_type, scope_value)
        if workbook_status == "ok" and workbook_rows:
            return workbook_status, workbook_rows, workbook_as_of, workbook_error
        if _safe_table_exists(db, "fact_school_contacts"):
            contact_count = db.execute(text("SELECT COUNT(1) AS c FROM fact_school_contacts")).mappings().first()
            if int((contact_count or {}).get("c") or 0) > 0:
                return _load_from_contacts_fallback(db, scope_type, scope_value)
        return "invalid_dataset_schema", [], "", "; ".join(schema_errors)

    prefix = _scope_prefix(scope_type, scope_value)
    station_col = "station_rsid" if "station_rsid" in cols else "org_unit_id"

    if prefix:
        sql = text(f"SELECT * FROM schools WHERE {station_col} LIKE :pfx")
        src_rows = db.execute(sql, {"pfx": f"{prefix}%"}).mappings().all()
    else:
        sql = text("SELECT * FROM schools")
        src_rows = db.execute(sql).mappings().all()

    if not src_rows:
        workbook_status, workbook_rows, workbook_as_of, workbook_error = _load_from_contacts_workbook(scope_type, scope_value)
        if workbook_status == "ok" and workbook_rows:
            return workbook_status, workbook_rows, workbook_as_of, workbook_error
        if _safe_table_exists(db, "fact_school_contacts"):
            contact_count = db.execute(text("SELECT COUNT(1) AS c FROM fact_school_contacts")).mappings().first()
            if int((contact_count or {}).get("c") or 0) > 0:
                return _load_from_contacts_fallback(db, scope_type, scope_value)
        return workbook_status, workbook_rows, workbook_as_of, workbook_error

    out: List[Dict] = []
    as_of_values: List[str] = []

    has_milestones = _safe_table_exists(db, "school_milestones")
    has_school_contracts = _safe_table_exists(db, "fact_school_contracts")
    has_event_table = _safe_table_exists(db, "event")

    for r in src_rows:
        school_id = str(_pick(r, ["school_id", "id"], ""))
        station = str(_pick(r, ["station_rsid", "org_unit_id"], ""))
        if not school_id or not station:
            continue

        contacts = 0
        events = 0
        contracts = 0

        if has_milestones:
            try:
                c_row = db.execute(
                    text("SELECT COUNT(1) AS c FROM school_milestones WHERE school_id = :sid"),
                    {"sid": school_id},
                ).mappings().first()
                contacts = int((c_row or {}).get("c") or 0)
            except Exception:
                contacts = 0

        if has_event_table:
            try:
                e_row = db.execute(
                    text("SELECT COUNT(1) AS c FROM event WHERE org_unit_id = :sid"),
                    {"sid": school_id},
                ).mappings().first()
                events = int((e_row or {}).get("c") or 0)
            except Exception:
                events = 0

        if has_school_contracts:
            try:
                k_row = db.execute(
                    text("SELECT COUNT(1) AS c FROM fact_school_contracts WHERE school_id = :sid"),
                    {"sid": school_id},
                ).mappings().first()
                contracts = int((k_row or {}).get("c") or 0)
            except Exception:
                contracts = 0

        data_as_of = str(_pick(r, ["data_as_of", "updated_at", "created_at", "ingested_at"], ""))
        if data_as_of:
            as_of_values.append(data_as_of)

        enrollment = int(float(_pick(r, ["enrollment", "population"], 0) or 0))

        out.append(
            {
                "school_id": school_id,
                "school_name": str(_pick(r, ["school_name", "name"], "")),
                "station_rsid": station,
                "zip_code": str(_pick(r, ["zip_code", "zip", "postal_code"], "")),
                "enrollment": enrollment,
                "market_opportunity": float(enrollment),
                "contacts_count": contacts,
                "events_count": events,
                "contracts_count": contracts,
                "school_zone_valid": bool(_pick(r, ["zone_valid", "school_zone_valid"], True)),
                "dod_access_ratio": float(_pick(r, ["dod_access_ratio", "dod_share", "dod_rate"], 0.0) or 0.0),
                "data_as_of": data_as_of,
                "source_dataset_name": "schools",
            }
        )

    if not out:
        workbook_status, workbook_rows, workbook_as_of, workbook_error = _load_from_contacts_workbook(scope_type, scope_value)
        if workbook_status == "ok" and workbook_rows:
            return workbook_status, workbook_rows, workbook_as_of, workbook_error
        return "no_active_dataset", [], "", ""

    ok, errors, normalized = school_access_contract.validate_rows(out)
    if not ok:
        return "invalid_dataset_schema", [], "", "; ".join(errors[:10])

    latest_as_of = max(as_of_values) if as_of_values else ""
    return "ok", normalized, latest_as_of, ""


def _load_from_contacts_fallback(db, scope_type: str, scope_value: str) -> Tuple[str, List[Dict], str, str]:
    prefix = _scope_prefix(scope_type, scope_value)
    if prefix:
        rows = db.execute(
            text(
                """
                SELECT COALESCE(school_id, school_name) AS sid,
                       school_name,
                       unit_rsid,
                       zip,
                       COUNT(1) AS contacts_count
                FROM fact_school_contacts
                WHERE unit_rsid LIKE :pfx OR unit_rsid IS NULL OR unit_rsid = ''
                GROUP BY COALESCE(school_id, school_name), school_name, unit_rsid, zip
                """
            ),
            {"pfx": f"{prefix}%"},
        ).mappings().all()
    else:
        rows = db.execute(
            text(
                """
                SELECT COALESCE(school_id, school_name) AS sid,
                       school_name,
                       unit_rsid,
                       zip,
                       COUNT(1) AS contacts_count
                FROM fact_school_contacts
                GROUP BY COALESCE(school_id, school_name), school_name, unit_rsid, zip
                """
            )
        ).mappings().all()

    if not rows:
        return "no_active_dataset", [], "", ""

    out: List[Dict] = []
    for r in rows:
        school_id = str(r.get("sid") or "")
        if not school_id:
            continue
        station = str(r.get("unit_rsid") or "")
        if not station:
            station = (scope_value or "")[:4] if (scope_type or "").upper() == "STN" else "UNKN"

        contracts = 0
        if _safe_table_exists(db, "fact_school_contracts"):
            c_row = db.execute(
                text(
                    """
                    SELECT COUNT(1) AS c
                    FROM fact_school_contracts
                    WHERE (school_id = :sid OR school_name = :sname)
                    """
                ),
                {"sid": school_id, "sname": r.get("school_name")},
            ).mappings().first()
            contracts = int((c_row or {}).get("c") or 0)

        out.append(
            {
                "school_id": school_id,
                "school_name": str(r.get("school_name") or school_id),
                "station_rsid": station,
                "zip_code": str(r.get("zip") or ""),
                "enrollment": 0,
                "market_opportunity": 0.0,
                "contacts_count": int(r.get("contacts_count") or 0),
                "events_count": 0,
                "contracts_count": contracts,
                "school_zone_valid": True,
                "dod_access_ratio": 0.0,
                "data_as_of": "",
                "source_dataset_name": "fact_school_contacts",
            }
        )

    ok, errors, normalized = school_access_contract.validate_rows(out)
    if not ok:
        return "invalid_dataset_schema", [], "", "; ".join(errors[:10])

    return "ok", normalized, "", ""


def _rollup(rows: List[Dict], key_name: str, key_fn) -> List[Dict]:
    groups: Dict[str, List[Dict]] = {}
    for row in rows:
        k = key_fn(row)
        groups.setdefault(k, []).append(row)

    out: List[Dict] = []
    for k, vals in groups.items():
        if not k:
            continue
        opp = sum(float(v.get("market_opportunity") or 0.0) for v in vals)
        prod = sum(float(v.get("contracts_count") or 0.0) for v in vals)
        contacts = sum(int(v.get("contacts_count") or 0) for v in vals)
        coverage = sum(1 for v in vals if int(v.get("contacts_count") or 0) > 0)
        total = len(vals)
        penetration = (coverage / total) if total else 0.0
        out.append(
            {
                key_name: k,
                "school_count": total,
                "coverage_school_count": coverage,
                "penetration_rate": round(penetration, 4),
                "school_production": prod,
                "school_opportunity": opp,
                "access_status": "access_constrained" if penetration < 0.5 else "accessing_market",
                "contacts_count": contacts,
            }
        )
    out.sort(key=lambda x: x.get("penetration_rate", 0.0))
    return out


def summarize_school_access(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 25,
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    status, rows, data_as_of, schema_error = _load_school_rows(db, scope_type, scope_value)
    if status != "ok":
        return {
            "status": status,
            "school_access": {
                "summary": {
                    "overall_access_status": status,
                    "penetration_rate": 0.0,
                    "access_gap_count": 0,
                    "high_value_uncovered_school_count": 0,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "top_access_gaps": [],
                "data_as_of": data_as_of or None,
                "last_refresh": datetime.utcnow().isoformat() + "Z",
                "source_dataset_name": None,
                "schema_error": schema_error or None,
            },
        }

    total = len(rows)
    covered = sum(1 for r in rows if int(r.get("contacts_count") or 0) > 0)
    penetration = (covered / total) if total else 0.0
    max_opp = max([float(r.get("market_opportunity") or 0.0) for r in rows] or [1.0])
    if max_opp <= 0:
        max_opp = 1.0

    gaps = []
    for r in rows:
        opp = float(r.get("market_opportunity") or 0.0)
        contacts = int(r.get("contacts_count") or 0)
        contracts = int(r.get("contracts_count") or 0)
        uncovered = contacts == 0
        opp_norm = opp / max_opp
        gap_score = round(100.0 * (0.7 * opp_norm + 0.3 * (1.0 if uncovered else 0.0)), 2)
        if uncovered or contracts == 0:
            gaps.append(
                {
                    "school_id": r.get("school_id"),
                    "school_name": r.get("school_name"),
                    "station_rsid": r.get("station_rsid"),
                    "zip_code": r.get("zip_code"),
                    "market_opportunity": opp,
                    "contacts_count": contacts,
                    "contracts_count": contracts,
                    "access_gap_score": gap_score,
                    "school_zone_valid": bool(r.get("school_zone_valid")),
                    "access_classification": "access_constrained" if uncovered else "underpenetrated",
                }
            )

    gaps.sort(key=lambda x: x.get("access_gap_score", 0.0), reverse=True)

    high_value_uncovered = [
        g for g in gaps if float(g.get("market_opportunity") or 0.0) >= 0.7 * max_opp and int(g.get("contacts_count") or 0) == 0
    ]

    source_dataset_name = rows[0].get("source_dataset_name") if rows else None

    by_scope = {
        "bde": _rollup(rows, "brigade_prefix", lambda r: str(r.get("station_rsid") or "")[:1]),
        "bn": _rollup(rows, "battalion_prefix", lambda r: str(r.get("station_rsid") or "")[:2]),
        "company": _rollup(rows, "company_prefix", lambda r: str(r.get("station_rsid") or "")[:3]),
        "station": _rollup(rows, "station_rsid", lambda r: str(r.get("station_rsid") or "")),
    }

    overall = "accessing_market" if penetration >= 0.6 else "access_constrained"

    return {
        "status": "ok",
        "school_access": {
            "summary": {
                "overall_access_status": overall,
                "penetration_rate": round(penetration, 4),
                "access_gap_count": len(gaps),
                "high_value_uncovered_school_count": len(high_value_uncovered),
            },
            "by_scope": by_scope,
            "top_access_gaps": gaps[:top_n],
            "data_as_of": data_as_of or None,
            "last_refresh": datetime.utcnow().isoformat() + "Z",
            "source_dataset_name": source_dataset_name,
        },
    }
