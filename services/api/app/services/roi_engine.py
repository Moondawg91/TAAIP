# services/api/app/services/roi_engine.py
#
# Authoritative ROI / Event Effectiveness Engine for TAAIP 420T capability.
#
# Data sources (in priority order):
#   1. emm_event     — normalized event hub (unit_rsid, zip, cost_total)
#   2. event_fact    — factual events (unit_rsid, no zip)
#   3. spend_fact    — authoritative cost by event_id
#   4. lead_journey_fact — leads and contracts by event_id
#   5. roi_thresholds    — seeded CPL/CPC benchmark targets
#
# Scoring formula (deterministic):
#   roi_score = 0.35 * contract_outcome
#             + 0.25 * lead_outcome
#             + 0.20 * cost_efficiency
#             + 0.10 * market_alignment
#             + 0.10 * targeting_alignment
#
# Each sub-score is 0–100.  Overall bands: high ≥ 70, moderate 40–69, low < 40.

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from starlette.exceptions import HTTPException

from services.api.app.services import market_engine, targeting_engine

# ---------------------------------------------------------------------------
# Scoring weights (authoritative — do not change without updating docs)
# ---------------------------------------------------------------------------
WEIGHT_CONTRACT_OUTCOME = 0.35
WEIGHT_LEAD_OUTCOME = 0.25
WEIGHT_COST_EFFICIENCY = 0.20
WEIGHT_MARKET_ALIGNMENT = 0.10
WEIGHT_TARGETING_ALIGNMENT = 0.10

HIGH_BAND_THRESHOLD = 70.0
MODERATE_BAND_THRESHOLD = 40.0

_CPL_TARGET_DEFAULT = 100.0
_CPC_TARGET_DEFAULT = 2500.0


# ---------------------------------------------------------------------------
# Scope utilities (shared pattern across all engines)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Sub-score computations (exported for use in automation/engine.py)
# ---------------------------------------------------------------------------

def compute_contract_outcome_score(contracts: int, cost: float, cpc_target: float) -> float:
    """Score 0-100 based on cost-per-contract vs benchmark."""
    if contracts == 0:
        return 0.0
    if cost <= 0.0:
        return 75.0  # contracts generated with no tracked cost — partial credit
    cpc = cost / contracts
    if cpc <= cpc_target:
        return 100.0
    if cpc <= cpc_target * 1.5:
        return 70.0
    if cpc <= cpc_target * 2.0:
        return 40.0
    return 10.0


def compute_lead_outcome_score(leads: int, cost: float, cpl_target: float) -> float:
    """Score 0-100 based on cost-per-lead vs benchmark."""
    if leads == 0:
        return 0.0
    if cost <= 0.0:
        return 60.0  # leads generated with no tracked cost — partial credit
    cpl = cost / leads
    if cpl <= cpl_target:
        return 100.0
    if cpl <= cpl_target * 1.5:
        return 70.0
    if cpl <= cpl_target * 2.0:
        return 40.0
    return 10.0


def compute_cost_efficiency_score(leads: int, contracts: int) -> float:
    """Score 0-100 based on lead-to-contract conversion rate."""
    if leads == 0:
        return 50.0  # neutral — no leads to convert
    rate = contracts / leads
    if rate >= 0.15:
        return 100.0
    if rate >= 0.10:
        return 80.0
    if rate >= 0.05:
        return 60.0
    if rate >= 0.01:
        return 30.0
    return 10.0


def compute_roi_score(
    contract_outcome: float,
    lead_outcome: float,
    cost_efficiency: float,
    market_alignment: float,
    targeting_alignment: float,
) -> float:
    """Deterministic composite ROI score (0-100)."""
    return round(
        WEIGHT_CONTRACT_OUTCOME * contract_outcome
        + WEIGHT_LEAD_OUTCOME * lead_outcome
        + WEIGHT_COST_EFFICIENCY * cost_efficiency
        + WEIGHT_MARKET_ALIGNMENT * market_alignment
        + WEIGHT_TARGETING_ALIGNMENT * targeting_alignment,
        4,
    )


def effectiveness_band(score: float) -> str:
    if score >= HIGH_BAND_THRESHOLD:
        return "high"
    if score >= MODERATE_BAND_THRESHOLD:
        return "moderate"
    return "low"


# ---------------------------------------------------------------------------
# Data loading helpers (load entire table then filter in Python to avoid
# SQLAlchemy IN-parameter complexity with SQLite)
# ---------------------------------------------------------------------------

def _load_thresholds(db) -> Tuple[float, float]:
    """Load CPL/CPC targets from roi_thresholds table."""
    try:
        rows = db.execute(text("SELECT metric_key, value FROM roi_thresholds")).fetchall()
        th = {str(r[0]): float(r[1]) for r in rows if r[1] is not None}
        return (
            float(th.get("cpl_target") or _CPL_TARGET_DEFAULT),
            float(th.get("cpc_target") or _CPC_TARGET_DEFAULT),
        )
    except Exception:
        return _CPL_TARGET_DEFAULT, _CPC_TARGET_DEFAULT


def _load_events_emm(db, prefix: str) -> List[Dict]:
    """Load events from emm_event table, filtered by unit_rsid prefix."""
    try:
        rows = db.execute(text(
            "SELECT event_id, unit_rsid, event_name, event_type, "
            "start_date, end_date, zip, cbsa_code, cost_total "
            "FROM emm_event"
        )).fetchall()
        if not rows:
            return []
        result = []
        for r in rows:
            unit_rsid = str(r[1] or "").upper()
            if prefix and not unit_rsid.startswith(prefix):
                continue
            result.append({
                "event_id": str(r[0] or ""),
                "unit_rsid": unit_rsid,
                "event_name": str(r[2] or ""),
                "event_type": str(r[3] or ""),
                "start_dt": str(r[4] or ""),
                "end_dt": str(r[5] or ""),
                "zip": str(r[6] or ""),
                "cbsa_code": str(r[7] or ""),
                "cost_total_emm": float(r[8] or 0.0),
                "_source": "emm_event",
            })
        return result
    except Exception:
        return []


def _load_events_fact(db, prefix: str) -> List[Dict]:
    """Load events from event_fact table as secondary source."""
    try:
        rows = db.execute(text(
            "SELECT event_id, unit_rsid, event_name, event_type, start_dt, end_dt "
            "FROM event_fact"
        )).fetchall()
        if not rows:
            return []
        result = []
        for r in rows:
            unit_rsid = str(r[1] or "").upper()
            if prefix and not unit_rsid.startswith(prefix):
                continue
            result.append({
                "event_id": str(r[0] or ""),
                "unit_rsid": unit_rsid,
                "event_name": str(r[2] or ""),
                "event_type": str(r[3] or ""),
                "start_dt": str(r[4] or ""),
                "end_dt": str(r[5] or ""),
                "zip": "",
                "cbsa_code": "",
                "cost_total_emm": 0.0,
                "_source": "event_fact",
            })
        return result
    except Exception:
        return []


def _load_spend_by_event(db) -> Dict[str, float]:
    """Load all spend_fact totals keyed by event_id."""
    try:
        rows = db.execute(text(
            "SELECT event_id, SUM(amount) as total FROM spend_fact "
            "WHERE event_id IS NOT NULL GROUP BY event_id"
        )).fetchall()
        return {str(r[0]): float(r[1] or 0.0) for r in rows}
    except Exception:
        return {}


def _load_leads_by_event(db) -> Dict[str, Dict]:
    """Load leads/contracts totals from lead_journey_fact keyed by event_id."""
    try:
        rows = db.execute(text(
            "SELECT event_id, "
            "COUNT(DISTINCT lead_id) as leads_count, "
            "SUM(CASE WHEN contract_flag=1 THEN 1 ELSE 0 END) as contracts_count "
            "FROM lead_journey_fact "
            "WHERE event_id IS NOT NULL "
            "GROUP BY event_id"
        )).fetchall()
        return {
            str(r[0]): {
                "leads_count": int(r[1] or 0),
                "contracts_count": int(r[2] or 0),
            }
            for r in rows
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Recommendation builders
# ---------------------------------------------------------------------------

def _event_recommendations(
    contract_s: float,
    lead_s: float,
    cost_eff_s: float,
    market_s: float,
    targeting_s: float,
) -> List[str]:
    recs = []
    if contract_s < MODERATE_BAND_THRESHOLD:
        recs.append(
            "Increase conversion activities targeting contract-ready prospects; "
            "review contract close rate and follow-up cadence for this event type."
        )
    if lead_s < MODERATE_BAND_THRESHOLD:
        recs.append(
            "Expand lead generation activities; review cost-per-lead against "
            f"CPL threshold. Current performance below {MODERATE_BAND_THRESHOLD:.0f}/100."
        )
    if cost_eff_s < MODERATE_BAND_THRESHOLD:
        recs.append(
            "Improve lead-to-contract conversion funnel for this event. "
            "Evaluate station follow-up quality after events."
        )
    if market_s < MODERATE_BAND_THRESHOLD:
        recs.append(
            "Reposition future events in this type toward higher market-opportunity zip codes identified by market engine."
        )
    if targeting_s < MODERATE_BAND_THRESHOLD:
        recs.append(
            "Align event placement with targeting engine high-priority zip codes to improve prospect alignment."
        )
    if not recs:
        recs.append(
            "Event achieving strong ROI. Maintain approach and apply this event model to lower-performing stations."
        )
    return recs


def _command_recommendations(
    events: List[Dict],
    scope_type: str,
    scope_value: str,
) -> List[Dict]:
    low_events = [e for e in events if e.get("effectiveness_band") == "low"]
    high_events = [e for e in events if e.get("effectiveness_band") == "high"]
    owner = (scope_type or "usarec").lower()

    recs: List[Dict] = []

    if low_events:
        worst = sorted(low_events, key=lambda x: float(x.get("roi_score") or 0.0))[:3]
        names = "; ".join(
            (e.get("event_name") or e.get("event_id") or "unknown")[:40]
            for e in worst
        )
        recs.append({
            "recommendation_id": "roi-rec-low-performers",
            "owner_level": owner,
            "action": (
                f"Review and restructure {len(low_events)} low-ROI event(s). "
                f"Priority: {names}. Evaluate cost allocation, lead sourcing, "
                "and event format against high-performing benchmarks."
            ),
            "expected_effect": "Reduce wasted event spend; shift resources toward higher-yield event types.",
            "time_horizon": "next 30 days",
            "rationale": (
                f"{len(low_events)} events scored below {MODERATE_BAND_THRESHOLD:.0f}/100 "
                "in ROI effectiveness (contract_outcome + lead_outcome dominant signals)."
            ),
            "trace_id": f"roi-engine:{scope_type}:{scope_value}:low_performance",
        })

    if high_events:
        best = sorted(high_events, key=lambda x: -float(x.get("roi_score") or 0.0))[:2]
        names = "; ".join(
            (e.get("event_name") or e.get("event_id") or "unknown")[:40]
            for e in best
        )
        recs.append({
            "recommendation_id": "roi-rec-scale-winners",
            "owner_level": owner,
            "action": (
                f"Scale high-ROI event formats from top performers: {names}. "
                "Replicate event model, location selection, and staffing approach across battalion."
            ),
            "expected_effect": "Multiply contract yield from proven event formats.",
            "time_horizon": "next 60 days",
            "rationale": (
                f"{len(high_events)} events scored above {HIGH_BAND_THRESHOLD:.0f}/100; "
                "strong cost efficiency and contract outcome observed."
            ),
            "trace_id": f"roi-engine:{scope_type}:{scope_value}:high_performance",
        })

    if not recs:
        recs.append({
            "recommendation_id": "roi-rec-data-gap",
            "owner_level": owner,
            "action": (
                "Increase event data capture fidelity: ensure event costs are logged to "
                "spend_fact by event_id, and leads are linked to events in lead_journey_fact."
            ),
            "expected_effect": "Enable meaningful ROI analysis and event effectiveness scoring.",
            "time_horizon": "next 14 days",
            "rationale": (
                "Insufficient event-level cost and lead linkage data prevents full ROI scoring. "
                "Market and targeting alignment scores defaulting to neutral (50)."
            ),
            "trace_id": f"roi-engine:{scope_type}:{scope_value}:data_gap",
        })

    return recs


# ---------------------------------------------------------------------------
# Event type performance rollup
# ---------------------------------------------------------------------------

def _event_type_performance(events: List[Dict]) -> List[Dict]:
    by_type: Dict[str, List[Dict]] = {}
    for e in events:
        t = str(e.get("event_type") or "unknown")
        by_type.setdefault(t, []).append(e)

    result = []
    for etype, rows in sorted(by_type.items()):
        scores = [float(r.get("roi_score") or 0.0) for r in rows]
        costs = [float(r.get("total_cost") or 0.0) for r in rows]
        contracts = [int(r.get("contracts_count") or 0) for r in rows]
        total_contracts = sum(contracts)
        total_cost = sum(costs)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_cpc = (total_cost / total_contracts) if total_contracts > 0 else None
        result.append({
            "event_type": etype,
            "event_count": len(rows),
            "avg_roi_score": round(avg_score, 2),
            "avg_cost_per_contract": round(avg_cpc, 2) if avg_cpc is not None else None,
            "effectiveness_band": effectiveness_band(avg_score),
        })

    # Deterministic sort: avg_roi_score DESC, event_type ASC
    result.sort(key=lambda x: (-float(x.get("avg_roi_score") or 0.0), str(x.get("event_type") or "")))
    return result


# ---------------------------------------------------------------------------
# Main engine entry point
# ---------------------------------------------------------------------------

def summarize_roi_engine(
    db,
    scope_type: str,
    scope_value: str,
    actor_scope_type: str = "USAREC",
    actor_scope_value: str = "USAREC",
    top_n: int = 20,
) -> Dict:
    """Return ROI / event effectiveness summary for the given scope.

    Returns a dict with keys:
      status: "ok" | "no_data"
      roi_engine: { summary, prioritized_events, event_type_performance,
                    roi_recommendations, data_as_of, source_tables }
    """
    enforce_scope(actor_scope_type, actor_scope_value, scope_type, scope_value)

    prefix = _scope_prefix(scope_type, scope_value)

    # --- Load events (primary: emm_event, secondary: event_fact) ---
    events = _load_events_emm(db, prefix)
    if not events:
        events = _load_events_fact(db, prefix)

    if not events:
        return {
            "status": "no_data",
            "roi_engine": {
                "summary": {
                    "total_events_scored": 0,
                    "high_effectiveness_count": 0,
                    "moderate_effectiveness_count": 0,
                    "low_effectiveness_count": 0,
                    "avg_roi_score": None,
                    "avg_cost_per_lead": None,
                    "avg_cost_per_contract": None,
                    "total_spend": 0.0,
                    "total_leads": 0,
                    "total_contracts": 0,
                    "scoring_formula": _scoring_formula_doc(),
                },
                "prioritized_events": [],
                "event_type_performance": [],
                "roi_recommendations": [],
                "data_as_of": None,
                "source_tables": ["emm_event", "event_fact", "spend_fact", "lead_journey_fact"],
            },
        }

    # --- Load cost and lead data (full tables, filter by event_id in Python) ---
    event_ids = {e["event_id"] for e in events if e["event_id"]}
    spend_map = _load_spend_by_event(db)
    leads_map = _load_leads_by_event(db)
    cpl_target, cpc_target = _load_thresholds(db)

    # --- Load market and targeting alignment lookup maps ---
    market_zip_lookup: Dict[str, float] = {}
    targeting_zip_lookup: Dict[str, float] = {}
    try:
        mkt = market_engine.summarize_market_engine(
            db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=200
        )
        for row in (mkt.get("market_engine") or {}).get("prioritized_market_zip") or []:
            z = str(row.get("zip") or "")
            if z:
                market_zip_lookup[z] = float(row.get("market_capability_score") or 50.0)
    except Exception:
        pass

    try:
        tgt = targeting_engine.summarize_targeting_engine(
            db, scope_type, scope_value, actor_scope_type, actor_scope_value, top_n=200
        )
        for row in (tgt.get("targeting_engine") or {}).get("prioritized_targets") or []:
            z = str(row.get("zip") or "")
            if z:
                # priority_score is 0-1, scale to 0-100
                targeting_zip_lookup[z] = float(row.get("priority_score") or 0.5) * 100.0
    except Exception:
        pass

    # --- Score each event ---
    scored: List[Dict] = []
    for ev in events:
        eid = ev["event_id"]
        cost_from_spend = spend_map.get(eid, 0.0)
        cost_emm = ev.get("cost_total_emm") or 0.0
        # spend_fact is authoritative; fall back to emm_event.cost_total
        total_cost = cost_from_spend if cost_from_spend > 0.0 else cost_emm

        lead_data = leads_map.get(eid, {"leads_count": 0, "contracts_count": 0})
        leads = lead_data["leads_count"]
        contracts = lead_data["contracts_count"]

        zip_code = str(ev.get("zip") or "")

        contract_s = compute_contract_outcome_score(contracts, total_cost, cpc_target)
        lead_s = compute_lead_outcome_score(leads, total_cost, cpl_target)
        cost_eff_s = compute_cost_efficiency_score(leads, contracts)
        market_s = market_zip_lookup.get(zip_code, 50.0) if zip_code else 50.0
        targeting_s = targeting_zip_lookup.get(zip_code, 50.0) if zip_code else 50.0

        score = compute_roi_score(contract_s, lead_s, cost_eff_s, market_s, targeting_s)
        band = effectiveness_band(score)

        cpl_val = (total_cost / leads) if leads > 0 else None
        cpc_val = (total_cost / contracts) if contracts > 0 else None

        scored.append({
            "event_id": eid,
            "event_name": ev["event_name"],
            "event_type": ev["event_type"],
            "unit_rsid": ev["unit_rsid"],
            "start_dt": ev["start_dt"],
            "end_dt": ev["end_dt"],
            "zip": zip_code,
            "total_cost": round(total_cost, 2),
            "leads_count": leads,
            "contracts_count": contracts,
            "cost_per_lead": round(cpl_val, 2) if cpl_val is not None else None,
            "cost_per_contract": round(cpc_val, 2) if cpc_val is not None else None,
            "contract_outcome_score": round(contract_s, 2),
            "lead_outcome_score": round(lead_s, 2),
            "cost_efficiency_score": round(cost_eff_s, 2),
            "market_alignment_score": round(market_s, 2),
            "targeting_alignment_score": round(targeting_s, 2),
            "roi_score": score,
            "effectiveness_band": band,
            "recommendations": _event_recommendations(
                contract_s, lead_s, cost_eff_s, market_s, targeting_s
            ),
            "trace_id": f"roi-engine:{ev['unit_rsid']}:{eid}",
        })

    # --- Deterministic sort: roi_score DESC, event_id ASC ---
    scored.sort(key=lambda x: (-float(x.get("roi_score") or 0.0), str(x.get("event_id") or "")))

    # --- Summary aggregates ---
    total_spend = sum(float(e.get("total_cost") or 0.0) for e in scored)
    total_leads = sum(int(e.get("leads_count") or 0) for e in scored)
    total_contracts = sum(int(e.get("contracts_count") or 0) for e in scored)
    all_scores = [float(e.get("roi_score") or 0.0) for e in scored]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else None
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else None
    avg_cpc = (total_spend / total_contracts) if total_contracts > 0 else None

    high_count = sum(1 for e in scored if e.get("effectiveness_band") == "high")
    moderate_count = sum(1 for e in scored if e.get("effectiveness_band") == "moderate")
    low_count = sum(1 for e in scored if e.get("effectiveness_band") == "low")

    # --- data_as_of: latest start_dt across all scored events ---
    data_as_of = None
    try:
        date_candidates = []
        for e in scored:
            s = str(e.get("start_dt") or "")
            if s:
                try:
                    date_candidates.append(datetime.fromisoformat(s.replace("Z", "")))
                except Exception:
                    pass
        if date_candidates:
            data_as_of = max(date_candidates).isoformat() + "Z"
    except Exception:
        pass

    return {
        "status": "ok",
        "roi_engine": {
            "summary": {
                "total_events_scored": len(scored),
                "high_effectiveness_count": high_count,
                "moderate_effectiveness_count": moderate_count,
                "low_effectiveness_count": low_count,
                "avg_roi_score": round(avg_score, 2) if avg_score is not None else None,
                "avg_cost_per_lead": round(avg_cpl, 2) if avg_cpl is not None else None,
                "avg_cost_per_contract": round(avg_cpc, 2) if avg_cpc is not None else None,
                "total_spend": round(total_spend, 2),
                "total_leads": total_leads,
                "total_contracts": total_contracts,
                "scoring_formula": _scoring_formula_doc(),
            },
            "prioritized_events": scored[:top_n],
            "event_type_performance": _event_type_performance(scored),
            "roi_recommendations": _command_recommendations(scored, scope_type, scope_value),
            "data_as_of": data_as_of,
            "source_tables": ["emm_event", "event_fact", "spend_fact", "lead_journey_fact"],
        },
    }


def _scoring_formula_doc() -> Dict:
    return {
        "roi_score": (
            "0.35*contract_outcome + 0.25*lead_outcome + 0.20*cost_efficiency "
            "+ 0.10*market_alignment + 0.10*targeting_alignment"
        ),
        "weights": {
            "contract_outcome": WEIGHT_CONTRACT_OUTCOME,
            "lead_outcome": WEIGHT_LEAD_OUTCOME,
            "cost_efficiency": WEIGHT_COST_EFFICIENCY,
            "market_alignment": WEIGHT_MARKET_ALIGNMENT,
            "targeting_alignment": WEIGHT_TARGETING_ALIGNMENT,
        },
        "bands": {
            "high": f">= {HIGH_BAND_THRESHOLD}",
            "moderate": f"{MODERATE_BAND_THRESHOLD} – {HIGH_BAND_THRESHOLD - 1}",
            "low": f"< {MODERATE_BAND_THRESHOLD}",
        },
    }
