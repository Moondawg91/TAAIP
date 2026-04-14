from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import text
from starlette.exceptions import HTTPException

from services.api.app import models
from services.api.app.services import market_qma_contract


def _clamp01(v: Optional[float]) -> float:
    try:
        if v is None:
            return 0.0
        f = float(v)
    except Exception:
        return 0.0
    if f < 0:
        return 0.0
    if f > 1:
        return 1.0
    return f


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


def enforce_scope(
    actor_scope_type: str,
    actor_scope_value: str,
    request_scope_type: str,
    request_scope_value: str,
) -> None:
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


def _source_table(db) -> Optional[str]:
    # Prefer the richer local market table if present and populated.
    for table_name in ("market_zip_metrics", "market_zip_fact", "mi_zip_fact", "station_zip_coverage"):
        if not _safe_table_exists(db, table_name):
            continue
        row = db.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1")).first()
        if row:
            return table_name
    return None


def _table_columns(db, table_name: str) -> List[str]:
    rows = db.execute(text(f"PRAGMA table_info('{table_name}')")).mappings().all()
    return [str(r.get("name")) for r in rows]


def _pick(row: Dict, names: Iterable[str], default=None):
    for n in names:
        if n in row and row.get(n) is not None:
            return row.get(n)
    return default


def _load_market_rows(db, scope_type: str, scope_value: str) -> Tuple[str, List[Dict], str, str]:
    table_name = _source_table(db)
    if not table_name:
        return "no_active_dataset", [], "", ""

    if table_name == "station_zip_coverage":
        prefix = _scope_prefix(scope_type, scope_value)
        if prefix:
            src_rows = db.execute(
                text("SELECT station_rsid, zip_code, market_category, created_at FROM station_zip_coverage WHERE station_rsid LIKE :pfx"),
                {"pfx": f"{prefix}%"},
            ).mappings().all()
        else:
            src_rows = db.execute(
                text("SELECT station_rsid, zip_code, market_category, created_at FROM station_zip_coverage")
            ).mappings().all()

        if not src_rows:
            return "no_active_dataset", [], "", ""

        out: List[Dict] = []
        as_of_values: List[str] = []
        for r in src_rows:
            station = str(r.get("station_rsid") or "")
            if not station:
                continue

            contracts_row = db.execute(
                text("SELECT SUM(COALESCE(contracts, 0)) AS cv FROM fact_enlistments WHERE unit_rsid = :u"),
                {"u": station},
            ).mappings().first() if _safe_table_exists(db, "fact_enlistments") else None
            contracts_actual = float((contracts_row or {}).get("cv") or 0.0)

            prod_row = db.execute(
                text(
                    """
                    SELECT SUM(COALESCE(metric_value, 0.0)) AS pv
                    FROM fact_production
                    WHERE (record_status IS NULL OR record_status = 'active')
                      AND org_unit_id = :org
                    """
                ),
                {"org": station},
            ).mappings().first() if _safe_table_exists(db, "fact_production") else None
            production_actual = float((prod_row or {}).get("pv") or contracts_actual)

            data_as_of = str(r.get("created_at") or "")
            if data_as_of:
                as_of_values.append(data_as_of)

            out.append(
                {
                    "zip_code": str(r.get("zip_code") or ""),
                    "station_rsid": station,
                    "company_prefix": station[:3],
                    "battalion_prefix": station[:2],
                    "brigade_prefix": station[:1],
                    "qma_population": 1.0,
                    "qma_density": 0.5,
                    "market_population": 1.0,
                    "market_category": str(r.get("market_category") or "UNK"),
                    "production_actual": production_actual,
                    "contracts_actual": contracts_actual,
                    "write_rate_actual": 0.0,
                    "reporting_period": "",
                    "data_as_of": data_as_of,
                    "source_dataset_name": table_name,
                }
            )

        latest_as_of = max(as_of_values) if as_of_values else ""
        return "ok", out, latest_as_of, ""

    cols = _table_columns(db, table_name)
    valid, schema_errors = market_qma_contract.validate_schema_columns(cols)
    if not valid:
        return "invalid_dataset_schema", [], "", "; ".join(schema_errors)

    prefix = _scope_prefix(scope_type, scope_value)
    if "station_rsid" in cols:
        where_col = "station_rsid"
    elif "rsid_prefix" in cols:
        where_col = "rsid_prefix"
    else:
        where_col = None

    if prefix and where_col:
        sql = text(f"SELECT * FROM {table_name} WHERE {where_col} LIKE :pfx")
        src_rows = db.execute(sql, {"pfx": f"{prefix}%"}).mappings().all()
    else:
        sql = text(f"SELECT * FROM {table_name}")
        src_rows = db.execute(sql).mappings().all()

    if not src_rows:
        return "no_active_dataset", [], "", ""

    out: List[Dict] = []
    as_of_values: List[str] = []
    for r in src_rows:
        station = str(_pick(r, ["station_rsid", "rsid_prefix"], ""))
        if not station:
            continue

        qma_population = float(_pick(r, ["qma_population", "fqma", "population", "army_potential"], 0.0) or 0.0)
        market_population = float(_pick(r, ["market_population", "population", "fqma", "army_potential"], qma_population) or qma_population)

        contracts_actual = float(_pick(r, ["contracts_actual", "contracts_vol", "contracts", "contracts_ga"], 0.0) or 0.0)
        write_rate_actual = float(_pick(r, ["write_rate_actual", "p2p_value", "p2p"], 0.0) or 0.0)

        # Pull production from fact_production by station when available.
        prod_row = db.execute(
            text(
                """
                SELECT SUM(COALESCE(metric_value, 0.0)) AS pv
                FROM fact_production
                WHERE (record_status IS NULL OR record_status = 'active')
                  AND org_unit_id = :org
                """
            ),
            {"org": station},
        ).mappings().first() if _safe_table_exists(db, "fact_production") else None
        production_actual = float((prod_row or {}).get("pv") or contracts_actual)

        data_as_of = str(_pick(r, ["data_as_of", "ingested_at", "updated_at", "created_at"], ""))
        if data_as_of:
            as_of_values.append(data_as_of)

        out.append(
            {
                "zip_code": str(_pick(r, ["zip_code", "zip5", "zip"], "")),
                "station_rsid": station,
                "company_prefix": station[:3],
                "battalion_prefix": station[:2],
                "brigade_prefix": station[:1],
                "qma_population": qma_population,
                "qma_density": float(_pick(r, ["qma_density", "opportunity_score", "army_share_of_potential", "army_share"], 0.0) or 0.0),
                "market_population": market_population,
                "market_category": str(_pick(r, ["market_category", "zip_category"], "UNK")),
                "production_actual": production_actual,
                "contracts_actual": contracts_actual,
                "write_rate_actual": write_rate_actual,
                "reporting_period": f"{_pick(r, ['fy'], '')}-{_pick(r, ['qtr', 'period_date'], '')}",
                "data_as_of": data_as_of,
                "source_dataset_name": table_name,
            }
        )

    ok, errors, normalized = market_qma_contract.validate_rows(out)
    if not ok:
        return "invalid_dataset_schema", [], "", "; ".join(errors[:10])

    latest_as_of = max(as_of_values) if as_of_values else ""
    return "ok", normalized, latest_as_of, ""


def _load_weights(db) -> Dict[str, float]:
    out = {}
    try:
        rows = db.query(models.MarketCategoryWeights).all()
        for r in rows:
            k = r.category.name if hasattr(r.category, "name") else str(r.category)
            out[k] = float(r.weight)
        if out:
            return out
    except Exception:
        pass

    try:
        cols = {str(r.get("name")) for r in db.execute(text("PRAGMA table_info('market_category_weights')")).mappings().all()}
        if not {"category", "weight"}.issubset(cols):
            return out
        rows = db.execute(text("SELECT category, weight FROM market_category_weights")).mappings().all()
        for r in rows:
            k = str(r.get("category") or "")
            if not k:
                continue
            out[k] = float(r.get("weight") or 0.0)
    except Exception:
        return out
    return out


def _scope_rollup(rows: List[Dict], key_name: str, scope_key: str) -> List[Dict]:
    grouped: Dict[str, List[Dict]] = {}
    for r in rows:
        grouped.setdefault(str(r.get(scope_key) or ""), []).append(r)

    out: List[Dict] = []
    for key, items in grouped.items():
        if not key:
            continue
        opp = [float(i.get("opportunity_score") or 0.0) for i in items]
        outp = [float(i.get("output_score") or 0.0) for i in items]
        gap = [float(i.get("opportunity_gap") or 0.0) for i in items]
        out.append(
            {
                key_name: key,
                "zip_count": len(items),
                "avg_opportunity_score": round(sum(opp) / len(opp), 4) if opp else 0.0,
                "avg_output_score": round(sum(outp) / len(outp), 4) if outp else 0.0,
                "avg_opportunity_gap": round(sum(gap) / len(gap), 4) if gap else 0.0,
                "market_status": "market_capable" if (sum(opp) / len(opp) if opp else 0.0) >= 0.5 else "market_constrained",
            }
        )
    out.sort(key=lambda x: x.get("avg_opportunity_gap", 0.0), reverse=True)
    return out


def summarize_market_qma(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 25,
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    status, rows, data_as_of, schema_error = _load_market_rows(db, scope_type, scope_value)
    if status != "ok":
        return {
            "status": status,
            "market_qma": {
                "summary": {
                    "market_capability_score": None,
                    "overall_market_status": status,
                    "high_opportunity_zip_count": 0,
                    "underperforming_market_count": 0,
                    "overperforming_market_count": 0,
                    "market_supports_mission": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "prioritized_market_zip": [],
                "top_market_gaps": [],
                "data_as_of": data_as_of or None,
                "last_refresh": datetime.utcnow().isoformat() + "Z",
                "source_dataset_name": None,
                "schema_error": schema_error or None,
            },
        }

    weights = _load_weights(db)
    max_weight = max(weights.values()) if weights else 1.0
    if max_weight <= 0:
        max_weight = 1.0

    max_qma = max([float(r.get("qma_population") or 0.0) for r in rows] or [1.0])
    if max_qma <= 0:
        max_qma = 1.0

    evaluated: List[Dict] = []
    for r in rows:
        cat = str(r.get("market_category") or "UNK")
        cat_weight = _clamp01(float(weights.get(cat, 1.0)) / max_weight)
        qma_density = _clamp01(float(r.get("qma_population") or 0.0) / max_qma)

        output_score = _clamp01(float(r.get("write_rate_actual") or 0.0))
        if output_score == 0.0:
            qma = float(r.get("qma_population") or 0.0)
            contracts = float(r.get("contracts_actual") or 0.0)
            output_score = _clamp01((contracts / qma) if qma > 0 else 0.0)

        opportunity_score = _clamp01(0.60 * qma_density + 0.40 * cat_weight)
        capability_score = _clamp01(0.55 * opportunity_score + 0.45 * output_score)
        opportunity_gap = max(0.0, opportunity_score - output_score)

        classification = "market_capable" if opportunity_score >= 0.5 else "market_constrained"
        perf = "balanced"
        if opportunity_gap >= 0.20:
            perf = "underperforming"
        elif output_score >= opportunity_score + 0.10:
            perf = "overperforming"

        evaluated.append(
            {
                **r,
                "qma_density": round(qma_density, 4),
                "opportunity_score": round(opportunity_score, 4),
                "output_score": round(output_score, 4),
                "capability_score": round(capability_score, 4),
                "opportunity_gap": round(opportunity_gap, 4),
                "market_classification": classification,
                "performance_status": perf,
            }
        )

    evaluated.sort(key=lambda x: (x.get("opportunity_gap", 0.0), x.get("qma_density", 0.0)), reverse=True)

    high_opp_low_output = [
        x
        for x in evaluated
        if float(x.get("opportunity_score") or 0.0) >= 0.65 and float(x.get("output_score") or 0.0) <= 0.35
    ]

    underperforming = [x for x in evaluated if x.get("performance_status") == "underperforming"]
    overperforming = [x for x in evaluated if x.get("performance_status") == "overperforming"]

    market_capability_score = round(
        (sum([float(x.get("capability_score") or 0.0) for x in evaluated]) / len(evaluated)) * 100.0,
        2,
    ) if evaluated else 0.0

    market_supports_mission = market_capability_score >= 55.0
    overall_market_status = "market_supportive" if market_supports_mission else "market_constrained"

    top_market_gaps = [
        {
            "zip_code": x.get("zip_code"),
            "station_rsid": x.get("station_rsid"),
            "opportunity_gap": x.get("opportunity_gap"),
            "qma_density": x.get("qma_density"),
            "output_score": x.get("output_score"),
            "market_classification": x.get("market_classification"),
        }
        for x in evaluated[:top_n]
        if float(x.get("opportunity_gap") or 0.0) > 0
    ]

    prioritized_market_zip = [
        {
            "zip_code": x.get("zip_code"),
            "station_rsid": x.get("station_rsid"),
            "priority_rank_score": round(100.0 * (0.70 * float(x.get("opportunity_gap") or 0.0) + 0.30 * float(x.get("qma_density") or 0.0)), 2),
            "reason_codes": ["high_qma_low_output"] if x in high_opp_low_output else ["market_supports_shift"],
            "market_classification": x.get("market_classification"),
        }
        for x in (high_opp_low_output[:top_n] if high_opp_low_output else evaluated[:top_n])
    ]

    source_dataset_name = evaluated[0].get("source_dataset_name") if evaluated else None

    return {
        "status": "ok",
        "market_qma": {
            "summary": {
                "market_capability_score": market_capability_score,
                "overall_market_status": overall_market_status,
                "high_opportunity_zip_count": len(high_opp_low_output),
                "underperforming_market_count": len(underperforming),
                "overperforming_market_count": len(overperforming),
                "market_supports_mission": market_supports_mission,
            },
            "by_scope": {
                "bde": _scope_rollup(evaluated, "brigade_prefix", "brigade_prefix"),
                "bn": _scope_rollup(evaluated, "battalion_prefix", "battalion_prefix"),
                "company": _scope_rollup(evaluated, "company_prefix", "company_prefix"),
                "station": _scope_rollup(evaluated, "station_rsid", "station_rsid"),
            },
            "prioritized_market_zip": prioritized_market_zip,
            "top_market_gaps": top_market_gaps,
            "data_as_of": data_as_of or None,
            "last_refresh": datetime.utcnow().isoformat() + "Z",
            "source_dataset_name": source_dataset_name,
        },
    }
