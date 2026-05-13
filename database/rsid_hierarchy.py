"""Canonical USAREC RSID hierarchy loaded from the provided master sheet."""

import csv
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_CSV_PATH = REPO_ROOT / "services" / "api" / ".data" / "usarec_master_units.csv"


def _split_code_name(value: str) -> Tuple[str, str]:
    text = (value or "").strip()
    if not text:
        return "", ""
    if " - " in text:
        code, name = text.split(" - ", 1)
        return code.strip(), name.strip()
    return text, text


def _require_csv() -> Path:
    if not CANONICAL_CSV_PATH.exists():
        raise FileNotFoundError(f"Canonical RSID CSV not found: {CANONICAL_CSV_PATH}")
    return CANONICAL_CSV_PATH


@lru_cache(maxsize=1)
def _load_rows() -> List[Dict[str, str]]:
    csv_path = _require_csv()
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"CMD", "BDE", "BN", "CO", "STN"}
        headers = set(reader.fieldnames or [])
        missing = sorted(required - headers)
        if missing:
            raise ValueError(f"Canonical RSID CSV missing columns: {missing}")
        rows = []
        for raw in reader:
            row = {key: (raw.get(key) or "").strip() for key in required}
            if all(row.values()):
                rows.append(row)
        return rows


@lru_cache(maxsize=1)
def _build_hierarchy() -> Dict[str, Dict[str, object]]:
    rows = _load_rows()
    hierarchy: Dict[str, Dict[str, object]] = {
        "USAREC": {
            "name": "USAREC",
            "level": "CMD",
            "brigades": {},
        }
    }

    brigades = hierarchy["USAREC"]["brigades"]
    for row in rows:
        command_code = row["CMD"]
        if command_code != "USAREC":
            raise ValueError(f"Unexpected command code in canonical RSID CSV: {command_code}")

        brigade_rsid = row["BDE"]
        battalion_rsid, battalion_name = _split_code_name(row["BN"])
        company_rsid, company_name = _split_code_name(row["CO"])
        station_rsid, station_name = _split_code_name(row["STN"])

        brigade = brigades.setdefault(
            brigade_rsid,
            {
                "name": brigade_rsid,
                "battalions": {},
            },
        )
        battalion = brigade["battalions"].setdefault(
            battalion_rsid,
            {
                "name": battalion_name or battalion_rsid,
                "companies": {},
            },
        )
        company = battalion["companies"].setdefault(
            company_rsid,
            {
                "name": company_name or company_rsid,
                "stations": [],
            },
        )
        if station_rsid not in company["stations"]:
            company["stations"].append(station_rsid)
        company.setdefault("station_names", {})[station_rsid] = station_name or station_rsid

    return hierarchy


def _seed_rows() -> List[Dict[str, Optional[str]]]:
    hierarchy = _build_hierarchy()
    rows: List[Dict[str, Optional[str]]] = [
        {
            "display_name": "USAREC",
            "echelon": "CMD",
            "rsid": "USAREC",
            "parent_rsid": None,
            "uic": None,
        }
    ]
    for brigade_rsid, brigade in hierarchy["USAREC"]["brigades"].items():
        rows.append(
            {
                "display_name": brigade["name"],
                "echelon": "BDE",
                "rsid": brigade_rsid,
                "parent_rsid": "USAREC",
                "uic": None,
            }
        )
        battalions = brigade["battalions"]
        for battalion_rsid, battalion in battalions.items():
            rows.append(
                {
                    "display_name": battalion["name"],
                    "echelon": "BN",
                    "rsid": battalion_rsid,
                    "parent_rsid": brigade_rsid,
                    "uic": None,
                }
            )
            companies = battalion["companies"]
            for company_rsid, company in companies.items():
                rows.append(
                    {
                        "display_name": company["name"],
                        "echelon": "CO",
                        "rsid": company_rsid,
                        "parent_rsid": battalion_rsid,
                        "uic": None,
                    }
                )
                for station_rsid in company["stations"]:
                    rows.append(
                        {
                            "display_name": company["station_names"][station_rsid],
                            "echelon": "STN",
                            "rsid": station_rsid,
                            "parent_rsid": company_rsid,
                            "uic": None,
                        }
                    )
    return rows


USAREC_HIERARCHY = _build_hierarchy()


def get_all_brigades() -> List[str]:
    return list(USAREC_HIERARCHY["USAREC"]["brigades"].keys())


def get_battalions_for_brigade(brigade_rsid: str) -> List[str]:
    brigade = USAREC_HIERARCHY["USAREC"]["brigades"].get(brigade_rsid)
    if not brigade:
        return []
    return list(brigade["battalions"].keys())


def get_stations_for_battalion(brigade_rsid: str, battalion_rsid: str) -> List[str]:
    brigade = USAREC_HIERARCHY["USAREC"]["brigades"].get(brigade_rsid)
    if not brigade:
        return []
    battalion = brigade["battalions"].get(battalion_rsid)
    if not battalion:
        return []
    stations: List[str] = []
    for company in battalion["companies"].values():
        stations.extend(company["stations"])
    return stations


def get_full_hierarchy_path(rsid: str) -> Optional[Dict[str, Optional[str]]]:
    target = (rsid or "").strip()
    if not target:
        return None
    if target == "USAREC":
        return {
            "command": "USAREC",
            "brigade": None,
            "brigade_name": None,
            "battalion": None,
            "battalion_name": None,
            "company": None,
            "company_name": None,
            "station": None,
            "station_name": None,
            "full_path": "USAREC",
        }

    for brigade_rsid, brigade in USAREC_HIERARCHY["USAREC"]["brigades"].items():
        if target == brigade_rsid:
            return {
                "command": "USAREC",
                "brigade": brigade_rsid,
                "brigade_name": brigade["name"],
                "battalion": None,
                "battalion_name": None,
                "company": None,
                "company_name": None,
                "station": None,
                "station_name": None,
                "full_path": f"USAREC > {brigade['name']}",
            }
        for battalion_rsid, battalion in brigade["battalions"].items():
            if target == battalion_rsid:
                return {
                    "command": "USAREC",
                    "brigade": brigade_rsid,
                    "brigade_name": brigade["name"],
                    "battalion": battalion_rsid,
                    "battalion_name": battalion["name"],
                    "company": None,
                    "company_name": None,
                    "station": None,
                    "station_name": None,
                    "full_path": f"USAREC > {brigade['name']} > {battalion['name']}",
                }
            for company_rsid, company in battalion["companies"].items():
                if target == company_rsid:
                    return {
                        "command": "USAREC",
                        "brigade": brigade_rsid,
                        "brigade_name": brigade["name"],
                        "battalion": battalion_rsid,
                        "battalion_name": battalion["name"],
                        "company": company_rsid,
                        "company_name": company["name"],
                        "station": None,
                        "station_name": None,
                        "full_path": f"USAREC > {brigade['name']} > {battalion['name']} > {company['name']}",
                    }
                station_names = company.get("station_names", {})
                if target in station_names:
                    return {
                        "command": "USAREC",
                        "brigade": brigade_rsid,
                        "brigade_name": brigade["name"],
                        "battalion": battalion_rsid,
                        "battalion_name": battalion["name"],
                        "company": company_rsid,
                        "company_name": company["name"],
                        "station": target,
                        "station_name": station_names[target],
                        "full_path": (
                            f"USAREC > {brigade['name']} > {battalion['name']}"
                            f" > {company['name']} > {station_names[target]}"
                        ),
                    }
    return None


def validate_rsid(rsid: str) -> bool:
    return get_full_hierarchy_path(rsid) is not None


def get_org_unit_seed_rows() -> List[Dict[str, Optional[str]]]:
    return list(_seed_rows())
