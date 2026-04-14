import glob
import os
import re
import warnings
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
from starlette.exceptions import HTTPException

from services.api.app.services import funnel_engine_contract

HEALTHY_LEAD_TO_CONTRACT_MIN = 0.18
WATCH_LEAD_TO_CONTRACT_MIN = 0.08
HEALTHY_INTERVIEW_TO_CONTRACT_MIN = 0.35
WATCH_INTERVIEW_TO_CONTRACT_MIN = 0.20
SEVERE_DROPOFF_RATIO = 0.50


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


def _resolve_funnel_dataset_path() -> Optional[str]:
    env_path = os.getenv("TAAIP_FUNNEL_DATASET_PATH")
    if env_path is not None:
        return env_path if os.path.exists(env_path) else None

    candidates = [
        "./data/dev_datasets/Recruiting Funnel Enriched.csv",
        "./uploads/Recruiting Funnel Enriched.csv",
        "./data/uploads/Recruiting Funnel Enriched.csv",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p

    globbed = sorted(glob.glob("./**/*Recruiting*Funnel*Enriched*.csv", recursive=True))
    if globbed:
        return globbed[-1]
    return None


def _safe_div(n: float, d: float) -> float:
    if d <= 0:
        return 0.0
    return float(n) / float(d)


def _to_datetime(val) -> Optional[datetime]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return None

    if re.fullmatch(r"\d{12,14}", s):
        try:
            return datetime.fromtimestamp(int(s) / 1000.0, tz=timezone.utc)
        except Exception:
            return None

    if not re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}([ T].*)?|\d{1,2}/\d{1,2}/\d{2,4}", s):
        return None

    try:
        ts = pd.to_datetime(s, errors="coerce", utc=True)
        if pd.isna(ts):
            return None
        return ts.to_pydatetime()
    except Exception:
        return None


def _score_station_column(s: pd.Series) -> float:
    v = s.astype(str).str.strip().str.upper()
    ratio = v.str.match(r"^[A-Z0-9]{4}$", na=False).mean()
    return float(ratio)


def _score_zip_column(s: pd.Series) -> float:
    v = s.astype(str).str.strip()
    ratio = v.str.match(r"^\d{5}$", na=False).mean()
    return float(ratio)


def _score_date_column(s: pd.Series) -> float:
    v = s.astype(str).str.strip()
    candidate = v.str.match(
        r"^(\d{4}-\d{1,2}-\d{1,2}([ T].*)?|\d{1,2}/\d{1,2}/\d{2,4}|\d{12,14})$",
        na=False,
    )
    if not bool(candidate.any()):
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        dt = pd.to_datetime(v.where(candidate), errors="coerce", utc=True)
    return float(dt.notna().mean())


def _score_stage_column(s: pd.Series) -> float:
    tokens = s.astype(str).str.upper().str.strip()
    if tokens.empty:
        return 0.0

    any_stage = tokens.str.contains(
        r"LEAD|PROSPECT|APPLICANT|INTERVIEW|PROCESS|CONTRACT|ENLIST|SHIPPED|DEP",
        regex=True,
        na=False,
    ).mean()
    has_sequence = tokens.str.contains(r",", regex=True, na=False).mean()
    begins_with_stage = tokens.str.match(
        r"^(LEAD|PROSPECT|APPLICANT|INTERVIEW|PROCESS|CONTRACT|SHIPPED|DELAYED ENTRY PROGRAM)",
        na=False,
    ).mean()
    return float(0.55 * any_stage + 0.25 * has_sequence + 0.20 * begins_with_stage)


def _looks_like_header_row(row: pd.Series) -> bool:
    vals = [str(v).strip() for v in row.tolist()]
    vals = [v for v in vals if v]
    if not vals:
        return False

    lowered = [v.lower() for v in vals]
    generic_headers = sum(bool(re.fullmatch(r"c\d+|column[_ ]?\d+|unnamed:?\s*\d*", v)) for v in lowered)
    keyword_hits = sum(
        any(k in v for k in [
            "lead",
            "station",
            "zip",
            "created",
            "stage",
            "history",
            "timestamp",
            "contract",
            "appointment",
            "interview",
        ])
        for v in lowered
    )
    numeric_like = sum(bool(re.fullmatch(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", v)) for v in vals)

    return generic_headers >= max(3, len(vals) // 4) or (keyword_hits >= 3 and numeric_like <= max(1, len(vals) // 3))


def _score_history_column(s: pd.Series) -> float:
    v = s.astype(str).str.upper()
    has_comma = v.str.contains(",", na=False).mean()
    has_stage_words = (
        v.str.contains("LEAD|APPLICANT|INTERVIEW|PROCESS|SHIP|CONTRACT|APPOINT", na=False)
    ).mean()
    return float(0.6 * has_comma + 0.4 * has_stage_words)


def _score_timestamp_history_column(s: pd.Series) -> float:
    v = s.astype(str)
    has_comma = v.str.contains(",", na=False).mean()
    has_epoch = v.str.contains(r"\d{12,14}", regex=True, na=False).mean()
    return float(0.5 * has_comma + 0.5 * has_epoch)


def _pick_best_column(rows: pd.DataFrame, scorer, min_score: float) -> Tuple[Optional[int], float]:
    best_idx = None
    best_score = 0.0
    for idx in range(rows.shape[1]):
        try:
            score = float(scorer(rows.iloc[:, idx]))
        except Exception:
            score = 0.0
        if score > best_score:
            best_score = score
            best_idx = idx
    if best_score < min_score:
        return None, best_score
    return best_idx, best_score


def infer_funnel_mapping(rows: pd.DataFrame) -> Dict[str, Dict]:
    mapping: Dict[str, Dict] = {}
    sample = rows.head(min(len(rows), 1000)).copy()

    # Lead ID: high uniqueness, mostly non-null.
    best_lead = (None, 0.0, 0.0)
    for idx in range(sample.shape[1]):
        col = sample.iloc[:, idx].astype(str).str.strip()
        nn_ratio = float((~col.isin(["", "nan", "null", "None"])) .mean())
        if nn_ratio < 0.7:
            continue
        uniq_ratio = float(col.nunique(dropna=True) / max(1, len(col)))
        score = 0.6 * uniq_ratio + 0.4 * nn_ratio
        if score > best_lead[1]:
            best_lead = (idx, score, nn_ratio)
    if best_lead[0] is not None:
        mapping["lead_id"] = {"index": int(best_lead[0]), "confidence": round(best_lead[1], 4)}

    station_idx, station_score = _pick_best_column(sample, _score_station_column, 0.35)
    if station_idx is not None:
        mapping["station_rsid"] = {"index": station_idx, "confidence": round(station_score, 4)}

    zip_idx, zip_score = _pick_best_column(sample, _score_zip_column, 0.30)
    if zip_idx is not None:
        mapping["zip"] = {"index": zip_idx, "confidence": round(zip_score, 4)}

    created_idx, created_score = _pick_best_column(sample, _score_date_column, 0.35)
    if created_idx is not None:
        mapping["lead_created_at"] = {"index": created_idx, "confidence": round(created_score, 4)}

    stage_idx, stage_score = _pick_best_column(sample, _score_stage_column, 0.08)
    if stage_idx is not None:
        mapping["current_stage"] = {"index": stage_idx, "confidence": round(stage_score, 4)}

    hist_idx, hist_score = _pick_best_column(sample, _score_history_column, 0.18)
    if hist_idx is not None:
        mapping["action_history"] = {"index": hist_idx, "confidence": round(hist_score, 4)}

    ts_hist_idx, ts_hist_score = _pick_best_column(sample, _score_timestamp_history_column, 0.18)
    if ts_hist_idx is not None:
        mapping["timestamp_history"] = {"index": ts_hist_idx, "confidence": round(ts_hist_score, 4)}

    # Derive company/battalion from station RSID.
    mapping["company_id"] = {"derived_from": "station_rsid", "confidence": 1.0}
    mapping["battalion_id"] = {"derived_from": "station_rsid", "confidence": 1.0}

    # Date fields are derived from history/current stage with safe fallback.
    mapping["appointment_date"] = {"derived_from": "action_history,timestamp_history,current_stage", "confidence": 0.8}
    mapping["interview_date"] = {"derived_from": "action_history,timestamp_history,current_stage", "confidence": 0.8}
    mapping["contract_date"] = {"derived_from": "action_history,timestamp_history,current_stage", "confidence": 0.8}

    # Outcome status from current stage when explicit status field cannot be inferred.
    mapping["outcome_status"] = {"derived_from": "current_stage", "confidence": 0.7}

    return mapping


def _norm_stage(s: str) -> str:
    t = (s or "").strip().upper()
    if not t:
        return "unknown"

    def classify(token: str) -> str:
        if "CONTRACT" in token or "ENLIST" in token or "SHIP" in token:
            return "contract"
        if "PROCESS" in token or "DEP" in token:
            return "processing"
        if "INTERVIEW" in token or "APPLICANT" in token or "TEST" in token:
            return "interview"
        if "APPOINT" in token:
            return "appointment"
        if "LEAD" in token or "PROSPECT" in token:
            return "lead"
        return "unknown"

    parts = [p.strip() for p in re.split(r"[,;|]+", t) if p.strip()]
    if parts:
        for part in reversed(parts):
            stage = classify(part)
            if stage != "unknown":
                return stage
    return classify(t)


def _is_nonempty(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s not in {"", "nan", "none", "null"}


def _history_events(action_history: str, timestamp_history: str) -> List[Tuple[str, Optional[datetime]]]:
    actions = [x.strip() for x in str(action_history or "").split(",") if x.strip()]
    stamps = [x.strip() for x in str(timestamp_history or "").split(",") if x.strip()]

    out: List[Tuple[str, Optional[datetime]]] = []
    m = max(len(actions), len(stamps))
    for i in range(m):
        action = actions[i] if i < len(actions) else ""
        stamp = stamps[i] if i < len(stamps) else ""
        out.append((action, _to_datetime(stamp)))
    return out


def _infer_stage_dates(row: Dict) -> Dict[str, Optional[datetime]]:
    created = _to_datetime(row.get("lead_created_at"))
    current_stage = _norm_stage(str(row.get("current_stage") or ""))
    events = _history_events(row.get("action_history") or "", row.get("timestamp_history") or "")

    appointment_date = None
    interview_date = None
    processing_date = None
    contract_date = None

    for action, dt in events:
        token = (action or "").upper()
        if appointment_date is None and ("APPOINT" in token or token == "IA"):
            appointment_date = dt
        if interview_date is None and ("INTERVIEW" in token or "APPLICANT" in token or "TEST" in token):
            interview_date = dt
        if processing_date is None and ("PROCESS" in token or "DEP" in token or "DELAYED ENTRY" in token):
            processing_date = dt
        if contract_date is None and ("CONTRACT" in token or "ENLIST" in token or "SHIP" in token):
            contract_date = dt

    # Safe monotonic fallbacks for partial histories.
    if contract_date is not None and processing_date is None:
        processing_date = contract_date
    if processing_date is not None and interview_date is None:
        interview_date = processing_date
    if interview_date is not None and appointment_date is None:
        appointment_date = interview_date

    # Safe stage-based fallbacks for partial histories.
    if current_stage in {"appointment", "interview", "processing", "contract"} and appointment_date is None:
        appointment_date = created
    if current_stage in {"interview", "processing", "contract"} and interview_date is None:
        interview_date = created
    if current_stage in {"processing", "contract"} and processing_date is None:
        processing_date = created
    if current_stage in {"contract"} and contract_date is None:
        contract_date = created

    return {
        "appointment_date": appointment_date,
        "interview_date": interview_date,
        "processing_date": processing_date,
        "contract_date": contract_date,
    }


def _summarize_counts(df: pd.DataFrame) -> Dict[str, int]:
    return {
        "total_leads": int(len(df)),
        "total_appointments": int(df["appointment_date"].notna().sum()),
        "total_interviews": int(df["interview_date"].notna().sum()),
        "total_contracts": int(df["contract_date"].notna().sum()),
    }


def _rates(counts: Dict[str, int]) -> Dict[str, float]:
    leads = float(counts["total_leads"])
    appointments = float(counts["total_appointments"])
    interviews = float(counts["total_interviews"])
    contracts = float(counts["total_contracts"])
    return {
        "lead_to_appointment_rate": round(_safe_div(appointments, leads), 4),
        "appointment_to_interview_rate": round(_safe_div(interviews, appointments), 4),
        "interview_to_contract_rate": round(_safe_div(contracts, interviews), 4),
        "lead_to_contract_rate": round(_safe_div(contracts, leads), 4),
    }


def _dropoff(counts: Dict[str, int]) -> Tuple[List[Dict], Optional[str]]:
    flows = [
        ("lead_to_appointment", counts["total_leads"], counts["total_appointments"]),
        ("appointment_to_interview", counts["total_appointments"], counts["total_interviews"]),
        ("interview_to_contract", counts["total_interviews"], counts["total_contracts"]),
    ]
    out = []
    for stage, src, dst in flows:
        drop = max(0, int(src) - int(dst))
        rate = _safe_div(float(dst), float(src))
        out.append(
            {
                "stage": stage,
                "from_count": int(src),
                "to_count": int(dst),
                "dropoff_count": int(drop),
                "conversion_rate": round(rate, 4),
            }
        )

    out.sort(key=lambda x: (-int(x["dropoff_count"]), str(x["stage"])))
    largest = out[0]["stage"] if out else None
    out.sort(key=lambda x: ["lead_to_appointment", "appointment_to_interview", "interview_to_contract"].index(x["stage"]))
    return out, largest


def _status(summary: Dict, dropoff_analysis: List[Dict]) -> str:
    if int(summary.get("total_leads") or 0) <= 0:
        return "unknown"

    l2c = float(summary.get("lead_to_contract_rate") or 0.0)
    i2c = float(summary.get("interview_to_contract_rate") or 0.0)
    severe_dropoff = any(float(x.get("conversion_rate") or 0.0) < (1.0 - SEVERE_DROPOFF_RATIO) for x in dropoff_analysis)

    if l2c >= HEALTHY_LEAD_TO_CONTRACT_MIN and i2c >= HEALTHY_INTERVIEW_TO_CONTRACT_MIN and not severe_dropoff:
        return "healthy"
    if l2c < WATCH_LEAD_TO_CONTRACT_MIN or i2c < WATCH_INTERVIEW_TO_CONTRACT_MIN or severe_dropoff:
        return "critical"
    return "watch"


def _rationale(stage: str, conversion_rate: float, dropoff_count: int) -> str:
    if stage == "lead_to_appointment":
        return "High lead volume but weak appointment conversion"
    if stage == "appointment_to_interview":
        return "Appointment volume exists but interview conversion is lagging"
    if stage == "interview_to_contract":
        return "Interview volume exists but contract conversion is weak"
    return f"Stage weakness detected with dropoff_count={dropoff_count} and conversion_rate={round(conversion_rate, 4)}"


def _scope_metrics(df: pd.DataFrame, key_col: str, out_key: str) -> List[Dict]:
    out: List[Dict] = []
    for key, g in df.groupby(key_col, dropna=False):
        val = "" if pd.isna(key) else str(key)
        if not val:
            continue
        counts = _summarize_counts(g)
        rates = _rates(counts)
        dropoff_analysis, largest = _dropoff(counts)
        row = {
            out_key: val,
            **counts,
            **rates,
            "largest_dropoff_stage": largest,
            "overall_funnel_status": _status({**counts, **rates}, dropoff_analysis),
        }
        out.append(row)

    out.sort(key=lambda x: (-int(x.get("total_leads") or 0), str(x.get(out_key) or "")))
    return out


def _prioritized_gaps(df: pd.DataFrame, top_n: int = 25) -> List[Dict]:
    gap_rows: List[Dict] = []

    def add_gap(scope_type: str, scope_value: str, group_df: pd.DataFrame):
        counts = _summarize_counts(group_df)
        dropoff_analysis, _ = _dropoff(counts)
        if not dropoff_analysis:
            return
        worst = sorted(dropoff_analysis, key=lambda x: (-int(x["dropoff_count"]), float(x["conversion_rate"]), str(x["stage"])))[0]
        dropoff_count = int(worst["dropoff_count"])
        conversion_rate = float(worst["conversion_rate"])
        if dropoff_count <= 0:
            return
        priority_score = round(dropoff_count * (1.0 - conversion_rate), 4)
        gap_rows.append(
            {
                "scope_type": scope_type,
                "scope_value": scope_value,
                "station_rsid": scope_value if scope_type == "STN" else None,
                "stage": str(worst["stage"]),
                "dropoff_count": dropoff_count,
                "conversion_rate": round(conversion_rate, 4),
                "rationale": _rationale(str(worst["stage"]), conversion_rate, dropoff_count),
                "priority_score": priority_score,
                "trace_id": f"funnel-gap:{scope_type}:{scope_value}:{worst['stage']}",
            }
        )

    for stn, g in df.groupby("station_rsid"):
        add_gap("STN", str(stn), g)
    for co, g in df.groupby("company_id"):
        add_gap("CO", str(co), g)
    for bn, g in df.groupby("battalion_id"):
        add_gap("BN", str(bn), g)

    gap_rows.sort(
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("scope_type") or ""),
            str(x.get("scope_value") or ""),
            str(x.get("stage") or ""),
        )
    )
    return gap_rows[:top_n]


def summarize_funnel_engine(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 25,
) -> Dict:
    del db
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    dataset_path = _resolve_funnel_dataset_path()
    if not dataset_path:
        return {
            "status": "no_active_dataset",
            "funnel_engine": {
                "summary": {
                    "overall_funnel_status": "unknown",
                    "total_leads": 0,
                    "total_appointments": 0,
                    "total_interviews": 0,
                    "total_contracts": 0,
                    "lead_to_appointment_rate": 0.0,
                    "appointment_to_interview_rate": 0.0,
                    "interview_to_contract_rate": 0.0,
                    "lead_to_contract_rate": 0.0,
                    "largest_dropoff_stage": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "stage_breakdown": [],
                "dropoff_analysis": [],
                "prioritized_funnel_gaps": [],
                "data_as_of": None,
                "last_refresh": None,
                "source_dataset_name": None,
            },
        }

    try:
        raw = pd.read_csv(dataset_path, header=None)
    except Exception as e:
        return {
            "status": "invalid_dataset_schema",
            "funnel_engine": {
                "summary": {
                    "overall_funnel_status": "unknown",
                    "total_leads": 0,
                    "total_appointments": 0,
                    "total_interviews": 0,
                    "total_contracts": 0,
                    "lead_to_appointment_rate": 0.0,
                    "appointment_to_interview_rate": 0.0,
                    "interview_to_contract_rate": 0.0,
                    "lead_to_contract_rate": 0.0,
                    "largest_dropoff_stage": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "stage_breakdown": [],
                "dropoff_analysis": [],
                "prioritized_funnel_gaps": [],
                "data_as_of": None,
                "last_refresh": None,
                "source_dataset_name": os.path.basename(dataset_path),
                "schema_error": f"failed to read dataset: {e}",
            },
        }

    if len(raw) <= 1:
        return {
            "status": "no_active_dataset",
            "funnel_engine": {
                "summary": {
                    "overall_funnel_status": "unknown",
                    "total_leads": 0,
                    "total_appointments": 0,
                    "total_interviews": 0,
                    "total_contracts": 0,
                    "lead_to_appointment_rate": 0.0,
                    "appointment_to_interview_rate": 0.0,
                    "interview_to_contract_rate": 0.0,
                    "lead_to_contract_rate": 0.0,
                    "largest_dropoff_stage": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "stage_breakdown": [],
                "dropoff_analysis": [],
                "prioritized_funnel_gaps": [],
                "data_as_of": None,
                "last_refresh": datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z",
                "source_dataset_name": os.path.basename(dataset_path),
            },
        }

    first_row = raw.iloc[0] if len(raw.index) else None
    if first_row is not None and _looks_like_header_row(first_row):
        rows = raw.iloc[1:].reset_index(drop=True)
    else:
        rows = raw.reset_index(drop=True)

    mapping = infer_funnel_mapping(rows)
    valid, mapping_check = funnel_engine_contract.validate_inferred_mapping(mapping)
    if not valid:
        return {
            "status": "invalid_dataset_schema",
            "funnel_engine": {
                "summary": {
                    "overall_funnel_status": "unknown",
                    "total_leads": 0,
                    "total_appointments": 0,
                    "total_interviews": 0,
                    "total_contracts": 0,
                    "lead_to_appointment_rate": 0.0,
                    "appointment_to_interview_rate": 0.0,
                    "interview_to_contract_rate": 0.0,
                    "lead_to_contract_rate": 0.0,
                    "largest_dropoff_stage": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "stage_breakdown": [],
                "dropoff_analysis": [],
                "prioritized_funnel_gaps": [],
                "data_as_of": None,
                "last_refresh": datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z",
                "source_dataset_name": os.path.basename(dataset_path),
                "schema_error": funnel_engine_contract.summarize_missing(mapping_check),
                "schema_mapping": mapping,
            },
        }

    def get_value(idx: Optional[int], i: int):
        if idx is None:
            return None
        return rows.iat[i, idx]

    station_idx = (mapping.get("station_rsid") or {}).get("index")
    lead_idx = (mapping.get("lead_id") or {}).get("index")
    zip_idx = (mapping.get("zip") or {}).get("index")
    created_idx = (mapping.get("lead_created_at") or {}).get("index")
    stage_idx = (mapping.get("current_stage") or {}).get("index")
    action_hist_idx = (mapping.get("action_history") or {}).get("index")
    ts_hist_idx = (mapping.get("timestamp_history") or {}).get("index")

    records: List[Dict] = []
    for i in range(len(rows)):
        lead_id = str(get_value(lead_idx, i) or "").strip()
        station_rsid = str(get_value(station_idx, i) or "").strip().upper()
        if not _is_nonempty(lead_id) or not re.fullmatch(r"[A-Z0-9]{4}", station_rsid or ""):
            continue

        lead_created_at = _to_datetime(get_value(created_idx, i))
        action_history = str(get_value(action_hist_idx, i) or "") if action_hist_idx is not None else ""
        timestamp_history = str(get_value(ts_hist_idx, i) or "") if ts_hist_idx is not None else ""
        current_stage_raw = str(get_value(stage_idx, i) or "") if stage_idx is not None else ""
        if not _is_nonempty(current_stage_raw):
            current_stage_raw = action_history

        rec = {
            "lead_id": lead_id,
            "station_rsid": station_rsid,
            "company_id": station_rsid[:3],
            "battalion_id": station_rsid[:2],
            "zip": str(get_value(zip_idx, i) or "").strip()[:5],
            "lead_created_at": lead_created_at,
            "current_stage": _norm_stage(current_stage_raw),
            "outcome_status": current_stage_raw.strip(),
            "action_history": action_history,
            "timestamp_history": timestamp_history,
            "school_id": None,
        }
        rec.update(_infer_stage_dates(rec))
        records.append(rec)

    if not records:
        return {
            "status": "no_active_dataset",
            "funnel_engine": {
                "summary": {
                    "overall_funnel_status": "unknown",
                    "total_leads": 0,
                    "total_appointments": 0,
                    "total_interviews": 0,
                    "total_contracts": 0,
                    "lead_to_appointment_rate": 0.0,
                    "appointment_to_interview_rate": 0.0,
                    "interview_to_contract_rate": 0.0,
                    "lead_to_contract_rate": 0.0,
                    "largest_dropoff_stage": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "stage_breakdown": [],
                "dropoff_analysis": [],
                "prioritized_funnel_gaps": [],
                "data_as_of": None,
                "last_refresh": datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z",
                "source_dataset_name": os.path.basename(dataset_path),
                "schema_mapping": mapping,
            },
        }

    frame = pd.DataFrame(records)

    prefix = _scope_prefix(scope_type, scope_value)
    if prefix:
        if (scope_type or "").upper() == "BDE":
            filtered = frame[frame["station_rsid"].str.startswith(prefix, na=False)]
        elif (scope_type or "").upper() == "BN":
            filtered = frame[frame["battalion_id"].str.startswith(prefix, na=False)]
        elif (scope_type or "").upper() == "CO":
            filtered = frame[frame["company_id"].str.startswith(prefix, na=False)]
        else:
            filtered = frame[frame["station_rsid"].str.startswith(prefix, na=False)]
    else:
        filtered = frame

    if filtered.empty:
        return {
            "status": "no_active_dataset",
            "funnel_engine": {
                "summary": {
                    "overall_funnel_status": "unknown",
                    "total_leads": 0,
                    "total_appointments": 0,
                    "total_interviews": 0,
                    "total_contracts": 0,
                    "lead_to_appointment_rate": 0.0,
                    "appointment_to_interview_rate": 0.0,
                    "interview_to_contract_rate": 0.0,
                    "lead_to_contract_rate": 0.0,
                    "largest_dropoff_stage": None,
                },
                "by_scope": {"bde": [], "bn": [], "company": [], "station": []},
                "stage_breakdown": [],
                "dropoff_analysis": [],
                "prioritized_funnel_gaps": [],
                "data_as_of": None,
                "last_refresh": datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z",
                "source_dataset_name": os.path.basename(dataset_path),
                "schema_mapping": mapping,
            },
        }

    counts = _summarize_counts(filtered)
    rates = _rates(counts)
    dropoff_analysis, largest_dropoff_stage = _dropoff(counts)

    summary = {
        "total_leads": counts["total_leads"],
        "total_appointments": counts["total_appointments"],
        "total_interviews": counts["total_interviews"],
        "total_contracts": counts["total_contracts"],
        "lead_to_appointment_rate": rates["lead_to_appointment_rate"],
        "appointment_to_interview_rate": rates["appointment_to_interview_rate"],
        "interview_to_contract_rate": rates["interview_to_contract_rate"],
        "lead_to_contract_rate": rates["lead_to_contract_rate"],
        "largest_dropoff_stage": largest_dropoff_stage,
    }
    summary["overall_funnel_status"] = _status(summary, dropoff_analysis)

    stage_breakdown = [
        {"stage": "lead", "count": counts["total_leads"]},
        {"stage": "appointment", "count": counts["total_appointments"]},
        {"stage": "interview", "count": counts["total_interviews"]},
        {"stage": "contract", "count": counts["total_contracts"]},
    ]

    by_scope = {
        "bde": _scope_metrics(filtered.assign(bde=filtered["station_rsid"].str[:1]), "bde", "bde_prefix"),
        "bn": _scope_metrics(filtered, "battalion_id", "battalion_id"),
        "company": _scope_metrics(filtered, "company_id", "company_id"),
        "station": _scope_metrics(filtered, "station_rsid", "station_rsid"),
    }

    prioritized_funnel_gaps = _prioritized_gaps(filtered, top_n=top_n)

    date_cols = ["lead_created_at", "appointment_date", "interview_date", "processing_date", "contract_date"]
    data_as_of = None
    for c in date_cols:
        if c in filtered.columns and filtered[c].notna().any():
            m = filtered[c].max()
            if isinstance(m, datetime):
                data_as_of = m.isoformat().replace("+00:00", "Z")

    return {
        "status": "ok",
        "funnel_engine": {
            "summary": summary,
            "by_scope": by_scope,
            "stage_breakdown": stage_breakdown,
            "dropoff_analysis": dropoff_analysis,
            "prioritized_funnel_gaps": prioritized_funnel_gaps,
            "data_as_of": data_as_of,
            "last_refresh": datetime.utcfromtimestamp(os.path.getmtime(dataset_path)).isoformat() + "Z",
            "source_dataset_name": os.path.basename(dataset_path),
            "schema_mapping": mapping,
        },
    }
