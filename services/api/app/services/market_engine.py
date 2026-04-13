import glob
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
from starlette.exceptions import HTTPException

from services.api.app.services import market_engine_contract

WEIGHT_POPULATION = 0.50
WEIGHT_EDUCATION = 0.30
WEIGHT_INCOME = 0.20

STRONG_THRESHOLD = 70.0
MODERATE_THRESHOLD = 40.0


def _scope_prefix(scope_type: str, scope_value: str) -> str:
    st = (scope_type or "").upper().strip()
    sv = (scope_value or "").strip().upper()
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
    a_val = (actor_scope_value or "USAREC").strip().upper()
    r_val = (request_scope_value or "USAREC").strip().upper()

    if a_type == "USAREC":
        return
    if r_type == "USAREC":
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")

    a_prefix = _scope_prefix(a_type, a_val)
    r_prefix = _scope_prefix(r_type, r_val)
    if a_prefix and not r_prefix.startswith(a_prefix):
        raise HTTPException(status_code=403, detail="requested scope outside user permissions")


def _resolve_market_core_path() -> Optional[str]:
    env_path = os.getenv("TAAIP_MARKET_CORE_PATH")
    if env_path is not None:
        return env_path if os.path.exists(env_path) else None

    candidates = [
        "./uploads/6L MARKET CORE.csv",
        "./data/uploads/6L MARKET CORE.csv",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p

    globbed = sorted(glob.glob("./data/uploads/**/*6L MARKET CORE.csv", recursive=True))
    if globbed:
        return globbed[-1]

    globbed = sorted(glob.glob("./**/*6L MARKET CORE.csv", recursive=True))
    if globbed:
        return globbed[-1]

    return None


def _safe_min_max_norm(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    s = pd.to_numeric(series, errors="coerce").fillna(0.0)
    s_min = float(s.min())
    s_max = float(s.max())
    if s_max <= s_min:
        return pd.Series([0.0 if x <= 0 else 1.0 for x in s], index=s.index)
    return (s - s_min) / (s_max - s_min)


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return pd.Series([0.0] * len(df), index=df.index, dtype="float64")


def _opportunity_band(score: float) -> str:
    if score >= STRONG_THRESHOLD:
        return "strong"
    if score >= MODERATE_THRESHOLD:
        return "moderate"
    return "weak"


def _overall_status(weighted_score: float) -> str:
    if weighted_score >= STRONG_THRESHOLD:
        return "strong"
    if weighted_score >= MODERATE_THRESHOLD:
        return "moderate"
    return "weak"


def _extract_rsid_code(v, default: str = "") -> str:
    s = "" if v is None else str(v).strip().upper()
    if not s:
        return default
    if re.fullmatch(r"[A-Z0-9]{2,4}", s) and s != "USA":
        return s
    m = re.search(r"\(([A-Z0-9]{2,4})\)", s)
    if m:
        code = m.group(1)
        if code != "USA":
            return code
    paren_codes = re.findall(r"\(([A-Z0-9]{2,4})\)", s)
    if paren_codes:
        for code in reversed(paren_codes):
            if code != "USA":
                return code
    return default


def _rationale(row: pd.Series) -> str:
    pop = float(row.get("total_recruiting_age_population", 0.0) or 0.0)
    band = str(row.get("opportunity_band") or "weak")
    completeness = float(row.get("supporting_completeness", 0.0) or 0.0)

    if completeness < 0.75:
        return "Large potential market with incomplete supporting fields; validate source data"
    if band == "strong" and pop > 0:
        return "High recruiting-age population with strong education support"
    if band == "moderate":
        return "Moderate population but favorable education and income conditions"
    return "Lower-capability market based on current recruiting-age, education, and income signals"


def _build_by_scope(rows: pd.DataFrame, key_col: str, out_key: str) -> List[Dict]:
    grouped = rows.groupby(key_col, dropna=False)
    out: List[Dict] = []
    for key, g in grouped:
        val = "" if pd.isna(key) else str(key)
        if not val:
            continue
        score = float(g["market_capability_score"].mean()) if len(g) else 0.0
        pop = float(g["total_recruiting_age_population"].sum()) if len(g) else 0.0
        strong = int((g["opportunity_band"] == "strong").sum())
        moderate = int((g["opportunity_band"] == "moderate").sum())
        weak = int((g["opportunity_band"] == "weak").sum())
        out.append(
            {
                out_key: val,
                "zip_count": int(len(g)),
                "market_capability_score": round(score, 2),
                "overall_market_status": _overall_status(score),
                "total_recruiting_age_population": round(pop, 2),
                "strong_zip_count": strong,
                "moderate_zip_count": moderate,
                "weak_zip_count": weak,
            }
        )
    out.sort(key=lambda x: (-float(x.get("market_capability_score") or 0.0), str(x.get(out_key) or "")))
    return out


def summarize_market_engine(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 25,
) -> Dict:
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    dataset_path = _resolve_market_core_path()
    if not dataset_path:
        return {
            "status": "no_active_dataset",
            "market_engine": {
                "summary": {
                    "overall_market_status": "unknown",
                    "market_capability_score": None,
                    "high_opportunity_zip_count": 0,
                    "moderate_opportunity_zip_count": 0,
                    "weak_opportunity_zip_count": 0,
                    "total_recruiting_age_population": 0.0,
                    "station_count": 0,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "prioritized_market_zip": [],
                "top_market_gaps": [],
                "data_as_of": None,
                "last_refresh": None,
                "source_dataset_name": None,
            },
        }

    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        return {
            "status": "invalid_dataset_schema",
            "market_engine": {
                "summary": {
                    "overall_market_status": "unknown",
                    "market_capability_score": None,
                    "high_opportunity_zip_count": 0,
                    "moderate_opportunity_zip_count": 0,
                    "weak_opportunity_zip_count": 0,
                    "total_recruiting_age_population": 0.0,
                    "station_count": 0,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "prioritized_market_zip": [],
                "top_market_gaps": [],
                "data_as_of": None,
                "last_refresh": None,
                "source_dataset_name": os.path.basename(dataset_path),
                "schema_error": f"failed to read dataset: {e}",
            },
        }

    valid, schema = market_engine_contract.validate_schema_columns(df.columns)
    if not valid:
        return {
            "status": "invalid_dataset_schema",
            "market_engine": {
                "summary": {
                    "overall_market_status": "unknown",
                    "market_capability_score": None,
                    "high_opportunity_zip_count": 0,
                    "moderate_opportunity_zip_count": 0,
                    "weak_opportunity_zip_count": 0,
                    "total_recruiting_age_population": 0.0,
                    "station_count": 0,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "prioritized_market_zip": [],
                "top_market_gaps": [],
                "data_as_of": None,
                "last_refresh": None,
                "source_dataset_name": os.path.basename(dataset_path),
                "schema_error": market_engine_contract.summarize_missing(schema),
            },
        }

    work = df.copy()
    work["zip"] = work["zip"].apply(market_engine_contract.normalize_zip)
    work["station_rsid"] = work["rsid_enlisted_station"].apply(lambda x: _extract_rsid_code(x, ""))

    if "rsid_enlisted_company" in work.columns:
        work["company_rsid"] = work["rsid_enlisted_company"].apply(lambda x: _extract_rsid_code(x, ""))
    else:
        work["company_rsid"] = ""
    if "rsid_enlisted_battalion" in work.columns:
        work["battalion_rsid"] = work["rsid_enlisted_battalion"].apply(lambda x: _extract_rsid_code(x, ""))
    else:
        work["battalion_rsid"] = ""
    if "rsid_enlisted_brigade" in work.columns:
        work["brigade_rsid"] = work["rsid_enlisted_brigade"].apply(lambda x: _extract_rsid_code(x, ""))
    else:
        work["brigade_rsid"] = ""

    for c in [
        "tot_male_18_19_b01001_007e",
        "tot_male_20_b01001_008e",
        "tot_male_21_b01001_009e",
        "tot_male_22_24_b01001_010e",
        "tot_female_18_19_b01001_031e",
        "tot_female_20_b01001_032e",
        "tot_female_21_b01001_033e",
        "tot_female_22_24_b01001_034e",
    ]:
        work[c] = pd.to_numeric(work[c], errors="coerce").fillna(0.0)

    work = work[(work["zip"] != "") & (work["station_rsid"] != "")]

    prefix = _scope_prefix(scope_type, scope_value)
    if prefix:
        if (scope_type or "").upper() == "BDE":
            filtered = work[work["brigade_rsid"].str.startswith(prefix, na=False)]
        elif (scope_type or "").upper() == "BN":
            filtered = work[work["battalion_rsid"].str.startswith(prefix, na=False)]
        elif (scope_type or "").upper() == "CO":
            filtered = work[work["company_rsid"].str.startswith(prefix, na=False)]
        else:
            filtered = work[work["station_rsid"].str.startswith(prefix, na=False)]
    else:
        filtered = work

    if filtered.empty:
        return {
            "status": "no_active_dataset",
            "market_engine": {
                "summary": {
                    "overall_market_status": "unknown",
                    "market_capability_score": None,
                    "high_opportunity_zip_count": 0,
                    "moderate_opportunity_zip_count": 0,
                    "weak_opportunity_zip_count": 0,
                    "total_recruiting_age_population": 0.0,
                    "station_count": 0,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "prioritized_market_zip": [],
                "top_market_gaps": [],
                "data_as_of": None,
                "last_refresh": datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z",
                "source_dataset_name": os.path.basename(dataset_path),
            },
        }

    filtered = filtered.copy()

    filtered["recruiting_age_male"] = (
        filtered["tot_male_18_19_b01001_007e"]
        + filtered["tot_male_20_b01001_008e"]
        + filtered["tot_male_21_b01001_009e"]
        + filtered["tot_male_22_24_b01001_010e"]
    )
    filtered["recruiting_age_female"] = (
        filtered["tot_female_18_19_b01001_031e"]
        + filtered["tot_female_20_b01001_032e"]
        + filtered["tot_female_21_b01001_033e"]
        + filtered["tot_female_22_24_b01001_034e"]
    )
    filtered["total_recruiting_age_population"] = filtered["recruiting_age_male"] + filtered["recruiting_age_female"]

    edu_total = _numeric_series(filtered, "tot_nonvet_education_twenty_five_over_b21003_007e")
    edu_hs = _numeric_series(filtered, "tot_nonvet_edu_high_school_b21003_009e")
    edu_some = _numeric_series(filtered, "tot_nonvet_edu_some_college_or_assoc_degree_b21003_010e")
    edu_bach = _numeric_series(filtered, "tot_nonvet_edu_bachelors_or_higher_b21003_011e")

    filtered["education_quality_score"] = 0.0
    valid_edu = edu_total > 0
    filtered.loc[valid_edu, "education_quality_score"] = (
        0.40 * (edu_hs[valid_edu] / edu_total[valid_edu])
        + 0.70 * (edu_some[valid_edu] / edu_total[valid_edu])
        + 1.00 * (edu_bach[valid_edu] / edu_total[valid_edu])
    ) * 100.0

    income_fields = [
        "tot_median_income_vet_b21004_002e",
        "tot_median_income_nonvet_b21004_005e",
        "tot_median_income_nonvet_male_b21004_006e",
        "tot_median_income_nonvet_female_b21004_007e",
    ]
    income_df = pd.DataFrame(index=filtered.index)
    for f in income_fields:
        income_df[f] = _numeric_series(filtered, f)
    filtered["income_raw"] = income_df.mean(axis=1, skipna=True).fillna(0.0)

    pop_norm = _safe_min_max_norm(filtered["total_recruiting_age_population"])
    edu_norm = _safe_min_max_norm(filtered["education_quality_score"])
    income_norm = _safe_min_max_norm(filtered["income_raw"])

    filtered["normalized_recruiting_age_population"] = pop_norm
    filtered["normalized_education_quality_score"] = edu_norm
    filtered["normalized_income_access_score"] = income_norm

    filtered["income_access_score"] = income_norm * 100.0

    filtered["market_capability_score"] = (
        WEIGHT_POPULATION * filtered["normalized_recruiting_age_population"]
        + WEIGHT_EDUCATION * filtered["normalized_education_quality_score"]
        + WEIGHT_INCOME * filtered["normalized_income_access_score"]
    ) * 100.0

    has_income = income_df.notna().any(axis=1).astype(float)
    has_edu = (edu_total > 0).astype(float)
    filtered["supporting_completeness"] = 0.5 * has_edu + 0.5 * has_income

    filtered["opportunity_band"] = filtered["market_capability_score"].apply(_opportunity_band)
    filtered["rationale"] = filtered.apply(_rationale, axis=1)

    filtered["trace_id"] = filtered.apply(
        lambda r: f"market-engine:{r.get('station_rsid')}:{r.get('zip')}",
        axis=1,
    )

    prioritized = filtered.sort_values(
        by=["market_capability_score", "total_recruiting_age_population", "zip"],
        ascending=[False, False, True],
    ).head(top_n)

    gaps = filtered[
        (
            (filtered["normalized_recruiting_age_population"] >= 0.60)
            & (
                (filtered["opportunity_band"] != "strong")
                | (filtered["supporting_completeness"] < 0.85)
            )
        )
    ].sort_values(
        by=["normalized_recruiting_age_population", "market_capability_score", "zip"],
        ascending=[False, True, True],
    ).head(top_n)

    score = float(filtered["market_capability_score"].mean()) if len(filtered) else 0.0
    overall = _overall_status(score)

    data_as_of = None
    date_candidates = []
    for date_col in ["enlisted_end_effective_date", "enlisted_begin_effective_date"]:
        if date_col in filtered.columns:
            parsed = pd.to_datetime(filtered[date_col], errors="coerce")
            if parsed.notna().any():
                date_candidates.append(parsed.max().to_pydatetime())
    if date_candidates:
        data_as_of = max(date_candidates).isoformat() + "Z"

    source_name = os.path.basename(dataset_path)
    last_refresh = datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z"

    completeness_avg = float(filtered["supporting_completeness"].mean()) if len(filtered) else 0.0
    confidence_note = "High confidence from complete population, education, and income fields."
    if completeness_avg < 0.85:
        confidence_note = "Reduced confidence: some education/income fields are incomplete in source rows."

    return {
        "status": "ok",
        "market_engine": {
            "summary": {
                "overall_market_status": overall,
                "market_capability_score": round(score, 2),
                "high_opportunity_zip_count": int((filtered["opportunity_band"] == "strong").sum()),
                "moderate_opportunity_zip_count": int((filtered["opportunity_band"] == "moderate").sum()),
                "weak_opportunity_zip_count": int((filtered["opportunity_band"] == "weak").sum()),
                "total_recruiting_age_population": float(filtered["total_recruiting_age_population"].sum()),
                "station_count": int(filtered["station_rsid"].nunique()),
                "confidence_note": confidence_note,
            },
            "by_scope": {
                "bde": _build_by_scope(filtered, "brigade_rsid", "brigade_rsid"),
                "bn": _build_by_scope(filtered, "battalion_rsid", "battalion_rsid"),
                "company": _build_by_scope(filtered, "company_rsid", "company_rsid"),
                "station": _build_by_scope(filtered, "station_rsid", "station_rsid"),
            },
            "prioritized_market_zip": [
                {
                    "zip": str(r.get("zip") or ""),
                    "station_rsid": str(r.get("station_rsid") or ""),
                    "company_rsid": str(r.get("company_rsid") or ""),
                    "battalion_rsid": str(r.get("battalion_rsid") or ""),
                    "brigade_rsid": str(r.get("brigade_rsid") or ""),
                    "total_recruiting_age_population": round(float(r.get("total_recruiting_age_population") or 0.0), 2),
                    "market_capability_score": round(float(r.get("market_capability_score") or 0.0), 2),
                    "opportunity_band": str(r.get("opportunity_band") or "weak"),
                    "rationale": str(r.get("rationale") or ""),
                    "trace_id": str(r.get("trace_id") or ""),
                }
                for _, r in prioritized.iterrows()
            ],
            "top_market_gaps": [
                {
                    "zip": str(r.get("zip") or ""),
                    "station_rsid": str(r.get("station_rsid") or ""),
                    "total_recruiting_age_population": round(float(r.get("total_recruiting_age_population") or 0.0), 2),
                    "market_capability_score": round(float(r.get("market_capability_score") or 0.0), 2),
                    "opportunity_band": str(r.get("opportunity_band") or "weak"),
                    "supporting_completeness": round(float(r.get("supporting_completeness") or 0.0), 4),
                    "rationale": str(r.get("rationale") or ""),
                    "trace_id": str(r.get("trace_id") or ""),
                }
                for _, r in gaps.iterrows()
            ],
            "data_as_of": data_as_of,
            "last_refresh": last_refresh,
            "source_dataset_name": source_name,
        },
    }
