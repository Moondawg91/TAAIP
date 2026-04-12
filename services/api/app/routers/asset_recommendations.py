from fastapi import APIRouter, Query
from datetime import datetime, date
from services.api.app.routers.analytics import get_dashboard
from services.api.app.routers.funnel import funnel_metrics as get_funnel_metrics
from services.api.app.routers.market_core import market_core_top_stations, market_core_data_quality
from fastapi.testclient import TestClient
from services.api.app.data.asset_registry import get_assets_by_category, list_assets, get_asset_by_id

router = APIRouter()


def build_recommendation_context(dashboard: dict, metrics: dict, stations: list, quality: dict, overrides: dict = None) -> dict:
    from services.api.app.data.context_provider import get_operational_context
    ctx = get_operational_context()
    funnel = (dashboard or {}).get("funnel", {}) or {}
    lead_to_app_rate = (metrics or {}).get("lead_to_applicant_rate", 0) or 0
    app_to_dep_rate = (metrics or {}).get("applicant_to_dep_rate", 0) or 0

    # Merge funnel/market data into the authoritative operational context
    ctx.update({
        "funnel": funnel,
        "lead_to_app_rate": lead_to_app_rate,
        "app_to_dep_rate": app_to_dep_rate,
        "market_population": stations[0].get("recruiting_age_total", 0) if stations else 0,
        "market_partial_rate": (quality or {}).get("partial_rate", 0) or 0,
        "top_stations": stations or [],
        "today": date.today().isoformat(),
        "funnel_lead_count": funnel.get('lead') or 0,
        "funnel_applicant_count": funnel.get('applicant') or 0,
        "funnel_dep_count": funnel.get('dep') or 0,
        "funnel_ship_count": funnel.get('ship') or 0,
    })

    if overrides:
        ctx.update(overrides)

    # normalize convenience flags
    ctx['emm_available'] = ctx.get('emm_available', True) or ('EMM' in (ctx.get('available_systems') or []))
    ctx['emm_portal_available'] = ctx.get('emm_portal_available', True) or ('EMM_PORTAL' in (ctx.get('available_systems') or []))

    return ctx


def asset_is_eligible(asset: dict, context: dict) -> dict:
    blocking = []
    warnings = []

    # base executability
    if asset.get("executable") is False:
        blocking.append("asset_marked_non_executable")

    # request system availability (explicit reasons)
    if asset.get('requires_emm') and not context.get('emm_available'):
        blocking.append('emm_required')
    if asset.get('requires_emm_portal') and not context.get('emm_portal_available'):
        blocking.append('emm_portal_required')

    # funding
    funding = asset.get('funding_source')
    if not funding or funding == 'unknown':
        blocking.append('funding_not_available')
    else:
        if funding not in context.get('funding_available', []):
            blocking.append(f'funding_not_available:{funding}')

    # command/approval
    allowed_cmds = asset.get('command_level') or asset.get('command_level', [])
    if allowed_cmds:
        if context.get('command_scope') not in allowed_cmds:
            blocking.append('command_scope_too_low')

    # geography
    geo_scope = asset.get('geography_scope')
    if geo_scope and geo_scope != 'flexible':
        ctx_geo = context.get('geography_scope') or context.get('geography') or context.get('command_scope')
        if ctx_geo and geo_scope != ctx_geo and geo_scope != 'flexible':
            blocking.append('geography_mismatch')

    # event lead time
    min_days = asset.get('minimum_lead_days') or 0
    rec_days = asset.get('recommended_lead_days') or min_days
    days_until = context.get('days_until_event') or context.get('days_until') or context.get('days_until_event')
    if days_until is not None:
        try:
            d = int(days_until)
            if d < min_days:
                blocking.append(f'insufficient_lead_time:{d}<{min_days}')
            elif d < rec_days:
                warnings.append(f'below_recommended_lead_time:{d}<{rec_days}')
        except Exception:
            warnings.append('invalid_days_until_event')
    else:
        if any([asset.get('requires_mac'), asset.get('requires_branding_review'), asset.get('requires_contracting'), asset.get('requires_vendor_coordination')]):
            warnings.append('target_event_date_not_provided')

    # operational requirements
    if asset.get('requires_mac'):
        if days_until is None:
            warnings.append('mac_required_but_no_event_date')
        else:
            try:
                if int(days_until) < min_days:
                    blocking.append('mac_timeline_insufficient')
            except Exception:
                warnings.append('invalid_days_until_event')

    if asset.get('requires_branding_review'):
        try:
            if days_until is None or int(days_until) < asset.get('recommended_lead_days', 0):
                warnings.append('branding_review_time_likely_insufficient')
        except Exception:
            warnings.append('invalid_days_until_event')

    if asset.get('requires_contracting'):
        try:
            if days_until is None:
                warnings.append('contracting_timeline_insufficient')
            elif int(days_until) < asset.get('minimum_lead_days', 0):
                blocking.append('contracting_timeline_insufficient')
        except Exception:
            warnings.append('invalid_days_until_event')

    # required documents presence
    req_docs = asset.get("required_documents") or []
    if not req_docs and any([asset.get("requires_contracting"), asset.get("requires_vendor_coordination"), asset.get("requires_branding_review")] ):
        warnings.append("required_documents_missing")

    return {"eligible": len(blocking) == 0, "blocking_reasons": blocking, "warning_reasons": warnings}


def score_asset(asset: dict, context: dict) -> int:
    # preserve existing business scoring logic but adapt to new schema
    score = 0
    if context.get("lead_to_app_rate", 0) < 0.05 and "lead_generation" in (asset.get("supports") or []):
        score += 50
    if context.get("app_to_dep_rate", 0) < 0.3 and "processing" in (asset.get("supports") or []):
        score += 50
    if context.get("market_population", 0) > 5000:
        score += 20
    if context.get("partial_rate", 0) > 0.2:
        score -= 20
    return score


@router.get("/asset_registry")
def asset_registry():
    return {"assets": list_assets()}


@router.get("/asset_recommendations")
def asset_recommendations(
    event_date: str = Query(None, description="ISO date of target event (YYYY-MM-DD)"),
    event_type: str = Query(None, description="Type of event"),
    command_scope: str = Query(None, description="Command scope override"),
    geography_scope: str = Query(None, description="Geography scope override"),
    funding_available: str = Query(None, description="Comma-separated funding sources available")
):
    dashboard = get_dashboard()
    metrics = get_funnel_metrics()
    try:
        from services.api.app.main import app
        client = TestClient(app)
        sts_resp = client.get('/api/market_core_vantage/top_stations?limit=5')
        stations = sts_resp.json() if sts_resp.status_code == 200 else []
        q_resp = client.get('/api/market_core_vantage/data_quality')
        quality = q_resp.json() if q_resp.status_code == 200 else {}
    except Exception:
        stations = []
        quality = {}

    overrides = {}
    if isinstance(event_date, str) and event_date:
        try:
            # normalize ISO date
            td = datetime.fromisoformat(event_date).date()
            overrides['target_event_date'] = td.isoformat()
            today = date.today()
            delta = (td - today).days
            overrides['days_until_event'] = delta
        except Exception:
            overrides['target_event_date'] = event_date
            overrides['days_until_event'] = None
    if isinstance(event_type, str) and event_type:
        overrides['event_type'] = event_type
    if isinstance(command_scope, str) and command_scope:
        overrides['command_scope'] = command_scope
    if isinstance(geography_scope, str) and geography_scope:
        overrides['geography'] = geography_scope
    if isinstance(funding_available, str) and funding_available:
        try:
            parts = funding_available.split(',')
        except Exception:
            parts = [str(funding_available)]
        overrides['funding_available'] = [f.strip() for f in parts if isinstance(f, str) and f.strip()]

    context = build_recommendation_context(dashboard, metrics, stations, quality, overrides=overrides)

    eligible_list = []
    not_actionable = []
    executable_now = []
    executable_with_risk = []
    not_executable_timeline = []

    for asset in list_assets():
        elig = asset_is_eligible(asset, context)
        if not elig.get("eligible"):
            not_actionable.append({
                "asset_id": asset.get("id"),
                "asset": asset.get("name"),
                "blocking_reasons": elig.get("blocking_reasons", [])
            })
            not_executable_timeline.append(asset.get("id"))
            continue

        score = score_asset(asset, context)
        if score <= 0:
            # do not recommend low-or-zero scored assets, but they are eligible
            not_actionable.append({
                "asset_id": asset.get("id"),
                "asset": asset.get("name"),
                "blocking_reasons": ["score_too_low"]
            })
            # treat as executable_with_risk for now (eligible but low score)
            executable_with_risk.append(asset.get("id"))
            continue

        rec = {
            "asset_id": asset.get("id"),
            "asset": asset.get("name"),
            "category": asset.get("category"),
            "priority": asset.get("priority_default") or "MEDIUM",
            "score": score,
            "reason": "Ranked by funnel, market, and data quality",
            "supports": asset.get("supports", []),
            "constraints": asset.get("constraints", []),
            "approval_level": asset.get("approval_level"),
            "funding_source": asset.get("funding_source"),
            "geography_scope": asset.get("geography_scope"),
            "minimum_lead_days": asset.get("minimum_lead_days"),
            "recommended_lead_days": asset.get("recommended_lead_days"),
            "request_system": asset.get("request_system"),
            "required_documents": asset.get("required_documents", []),
            "requires_emm": asset.get("requires_emm", False),
            "requires_emm_portal": asset.get("requires_emm_portal", False),
            "eligible": True,
            "warning_reasons": []
        }

        # determine execution classification based on warnings and lead time
        days_until = context.get('days_until_event')
        min_days = asset.get('minimum_lead_days') or 0
        rec_days = asset.get('recommended_lead_days') or min_days
        if days_until is None:
            # unknown -> mark as executable_with_risk
            executable_with_risk.append(asset.get('id'))
            rec['execution'] = 'executable_with_risk'
        else:
            try:
                d = int(days_until)
                if d >= rec_days:
                    executable_now.append(asset.get('id'))
                    rec['execution'] = 'executable_now'
                elif d >= min_days:
                    executable_with_risk.append(asset.get('id'))
                    rec['execution'] = 'executable_with_risk'
                    rec['warning_reasons'].append(f'days_until_event_below_recommended:{d}<{rec_days}')
                else:
                    not_executable_timeline.append(asset.get('id'))
                    rec['execution'] = 'not_executable_in_timeline'
                    rec['blocking_reasons'] = [f'days_until_event_insufficient:{d}<{min_days}']
            except Exception:
                executable_with_risk.append(asset.get('id'))
                rec['execution'] = 'executable_with_risk'

        eligible_list.append(rec)
        

    # sort descending
    eligible_list.sort(key=lambda r: r.get("score", 0), reverse=True)

    return {"context": context, "recommendations": eligible_list, "not_actionable": not_actionable}


@router.get("/asset_recommendations/decision_support")
def asset_recommendations_decision_support():
    data = asset_recommendations()
    recs = data.get("recommendations", [])
    not_actionable = data.get("not_actionable", [])

    recommended_now = [{"asset_id": r.get("asset_id"), "asset": r.get("asset"), "score": r.get("score")} for r in recs[:5]]
    not_actionable_now = not_actionable[:10]
    # top risks: flatten blocking reasons counts
    risks = {}
    for n in not_actionable:
        for b in n.get("blocking_reasons", []):
            risks[b] = risks.get(b, 0) + 1

    top_risks = sorted([{"risk": k, "count": v} for k, v in risks.items()], key=lambda x: x["count"], reverse=True)[:10]
    return {"recommended_now": recommended_now, "not_actionable_now": not_actionable_now, "top_risks": top_risks}


@router.get("/asset_recommendations/readiness")
def asset_recommendations_readiness():
    assets = list_assets()
    total = len(assets)
    data = asset_recommendations()
    eligible = len(data.get("recommendations", []))
    blocked = len(data.get("not_actionable", []))
    missing_validation = sum(1 for a in assets if (a.get("availability_type") == "unknown" or a.get("executable") is False))
    requires_emm = sum(1 for a in assets if a.get("requires_emm"))
    requires_emm_portal = sum(1 for a in assets if a.get("requires_emm_portal"))

    return {
        "total_assets": total,
        "eligible_assets": eligible,
        "blocked_assets": blocked,
        "assets_missing_rule_validation": missing_validation,
        "assets_requiring_emm": requires_emm,
        "assets_requiring_emm_portal": requires_emm_portal
    }
