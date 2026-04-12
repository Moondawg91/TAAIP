from fastapi import APIRouter, Query
from ..db import connect
from typing import Optional

router = APIRouter()


def _safe_num(v):
    try:
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


def _score_schools(cur, rsid_prefix: Optional[str] = None):
    """Return list of scored school dicts (same shape as ai_opportunity_schools results)."""
    q = "SELECT id, rsid_prefix, population, available, contacted_students FROM school_program_fact"
    params = ()
    if rsid_prefix:
        q += " WHERE rsid_prefix = ?"
        params = (rsid_prefix,)
    cur.execute(q, params)
    schools = cur.fetchall()
    out = []
    for s in schools:
        sid = s[0]
        sprefix = s[1]
        population = _safe_num(s[2])
        available = _safe_num(s[3])
        contacted = _safe_num(s[4])

        try:
            cur.execute("SELECT SUM(COALESCE(count_value,0)) FROM fact_funnel WHERE org_unit_id = ?", (sid,))
            f1 = cur.fetchone()[0] or 0
            cur.execute("SELECT SUM(COALESCE(count_value,0)) FROM fact_funnel WHERE org_unit_id = ?", (sprefix,))
            f2 = cur.fetchone()[0] or 0
            funnel_leads = float(f1) + float(f2)
        except Exception:
            funnel_leads = 0.0

        pop_norm = min(population / 2000.0, 1.0) if population else 0.0
        avail_rate = (available / population) if population else 0.0
        avail_norm = min(avail_rate, 1.0)
        funnel_norm = min(funnel_leads / 100.0, 1.0)

        w_pop = 0.4
        w_avail = 0.3
        w_funnel = 0.3

        score = round((pop_norm * w_pop + avail_norm * w_avail + funnel_norm * w_funnel) * 100.0, 2)

        components = {
            "population": round(population, 2),
            "population_norm": round(pop_norm, 4),
            "available": round(available, 2),
            "available_rate": round(avail_rate, 4),
            "funnel_leads": round(funnel_leads, 2),
            "funnel_norm": round(funnel_norm, 4),
        }

        reason = f"Population={int(population)}, AvailRate={round(avail_rate,3)}, FunnelLeads={int(funnel_leads)}"

        out.append({
            "id": sid,
            "rsid_prefix": sprefix,
            "population": population,
            "available": available,
            "contacted": contacted,
            "funnel_leads": funnel_leads,
            "score": score,
            "components": components,
            "reason": reason,
        })
    return out


@router.get('/ai/opportunity/schools')
def ai_opportunity_schools(top_n: int = Query(50), rsid_prefix: Optional[str] = Query(None)):
    """Return a ranked list of school opportunity scores (deterministic, explainable).

    Scoring components (weights):
      - population (40%) : larger populations favored
      - availability rate (30%) : proportion of available students
      - recent funnel activity (30%) : aggregated counts from `fact_funnel`

    The router attempts to match `fact_funnel.org_unit_id` to either the
    `school_program_fact.id` or `school_program_fact.rsid_prefix` when aggregating
    funnel activity.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        scored = _score_schools(cur, rsid_prefix)
    except Exception:
        return {"error": "failed_to_read_school_program_fact", "data": []}

    out_sorted = sorted(scored, key=lambda r: r.get('score', 0), reverse=True)[:int(top_n)]
    return {"count": len(out_sorted), "results": out_sorted}



@router.get('/ai/recommendations/schools')
def ai_recommendations_schools(top_n: int = Query(50), rsid_prefix: Optional[str] = Query(None)):
    """Deterministic recommendation engine layered on opportunity scores.

    Recommendation classes:
      - prioritize_now
      - monitor
      - deprioritize

    Rules (deterministic):
      - If score >= 50 -> prioritize_now, action_priority=high
      - If 25 <= score < 50 -> monitor, action_priority=medium
      - If score < 25 -> deprioritize, action_priority=low

    Engagement focus is suggested from dominant factor mix.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        scored = _score_schools(cur, rsid_prefix)
    except Exception:
        return {"error": "failed_to_read_school_program_fact", "data": []}

    recs = []
    for s in scored:
        score = s.get('score', 0)
        pop = s.get('population', 0)
        avail = s.get('available', 0)
        avail_rate = s.get('components', {}).get('available_rate', 0)
        funnel = s.get('funnel_leads', 0)

        if score >= 50:
            recommendation = 'prioritize_now'
            action_priority = 'high'
        elif score >= 25:
            recommendation = 'monitor'
            action_priority = 'medium'
        else:
            recommendation = 'deprioritize'
            action_priority = 'low'

        # engagement focus: if funnel > 0 then 'convert leads', else if avail_rate>0.2 then 'school outreach'
        if funnel > 0:
            engagement_focus = 'convert leads'
        elif avail_rate > 0.2:
            engagement_focus = 'school outreach'
        else:
            engagement_focus = 'general monitoring'

        # Compose explicit reason using observable factors
        reason_parts = []
        reason_parts.append(f"score={score}")
        reason_parts.append(f"population={int(pop)}")
        reason_parts.append(f"avail_rate={round(avail_rate,3)}")
        reason_parts.append(f"funnel_leads={int(funnel)}")
        recommendation_reason = ", ".join(reason_parts)

        recs.append({
            "rsid_prefix": s.get('rsid_prefix'),
            "score": score,
            "recommendation": recommendation,
            "action_priority": action_priority,
            "engagement_focus": engagement_focus,
            "recommendation_reason": recommendation_reason,
            "components": s.get('components'),
        })

    recs_sorted = sorted(recs, key=lambda r: r.get('score', 0), reverse=True)[:int(top_n)]
    return {"count": len(recs_sorted), "results": recs_sorted}


@router.get('/ai/risk/mission')
def ai_mission_risk(top_n: int = Query(50), unit_rsid: Optional[str] = Query(None)):
    """Deterministic mission-risk engine for units.

    Uses `fact_funnel` to compute lead volume and a proxy conversion rate
    (appointments / leads using stage name matching). Higher risk is
    assigned when lead volume is low and conversion is weak.
    """
    conn = connect()
    cur = conn.cursor()

    # Aggregate by org_unit_id
    try:
        where = ""
        params = ()
        if unit_rsid:
            where = " WHERE org_unit_id = ?"
            params = (unit_rsid,)
        q = f"SELECT org_unit_id, stage, SUM(COALESCE(count_value,0)) FROM fact_funnel {where} GROUP BY org_unit_id, stage"
        cur.execute(q, params)
        rows = cur.fetchall()
    except Exception:
        return {"error": "failed_to_read_fact_funnel", "data": []}

    # Build per-unit metrics
    units = {}
    for r in rows:
        uid = r[0]
        stage = r[1] or ''
        cnt = float(r[2] or 0)
        if uid not in units:
            units[uid] = {"lead_volume": 0.0, "appointments": 0.0, "stages": {}}
        units[uid]["stages"][stage] = units[uid]["stages"].get(stage, 0.0) + cnt
        # simple stage heuristics
        sl = stage.lower() if stage else ''
        if 'lead' in sl:
            units[uid]["lead_volume"] += cnt
        if 'appoint' in sl or 'appointment' in sl or 'appt' in sl:
            units[uid]["appointments"] += cnt

    # Compute risk scores
    out = []
    for uid, m in units.items():
        leads = m.get('lead_volume', 0.0)
        appts = m.get('appointments', 0.0)
        conversion = (appts / leads) if leads else 0.0

        # lead risk: targets: >=50 leads -> low risk, 0 leads -> high risk
        lead_risk = 1.0 - min(leads / 50.0, 1.0)
        # conversion risk: target conversion 20% -> lower -> higher risk
        conv_risk = 1.0 - min(conversion / 0.2, 1.0)
        # funnel health weak if leads < 10 or conversion < 0.05
        funnel_health_weak = 1 if (leads < 10 or conversion < 0.05) else 0

        # weights
        w_lead = 0.5
        w_conv = 0.4
        w_health = 0.1

        risk_score = round((lead_risk * w_lead + conv_risk * w_conv + funnel_health_weak * w_health) * 100)

        if risk_score >= 70:
            risk_level = 'high_risk'
        elif risk_score >= 40:
            risk_level = 'moderate_risk'
        else:
            risk_level = 'low_risk'

        # suggested attention
        if lead_risk > 0.6:
            suggested = 'lead_generation'
        elif conv_risk > 0.5:
            suggested = 'conversion_improvement'
        else:
            suggested = 'monitoring'

        reason_parts = []
        reason_parts.append(f"lead_volume={int(leads)}")
        reason_parts.append(f"conversion={round(conversion,3)}")
        reason_parts.append(f"funnel_health={'weak' if funnel_health_weak else 'ok'}")
        risk_reason = ", ".join(reason_parts)

        # Standardized fields: score, recommendation, reason, components
        out.append({
            "unit_id": uid,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "score": risk_score,
            "recommendation": risk_level,
            "reason": risk_reason,
            "components": {
                "lead_volume": int(leads),
                "appointments": int(appts),
                "conversion_rate": round(conversion, 4),
                "funnel_health": 'weak' if funnel_health_weak else 'ok'
            },
            "risk_factors": {
                "lead_volume": int(leads),
                "appointments": int(appts),
                "conversion_rate": round(conversion, 4),
                "funnel_health": 'weak' if funnel_health_weak else 'ok'
            },
            "risk_reason": risk_reason,
            "suggested_attention_area": suggested,
        })

    out_sorted = sorted(out, key=lambda r: r.get('risk_score', 0), reverse=True)[:int(top_n)]
    return {"count": len(out_sorted), "results": out_sorted}


@router.get('/ai/recommendations/markets')
def ai_recommendations_markets(top_n: int = Query(50), rsid_prefix: Optional[str] = Query(None)):
    """Rank market ZIPs (or markets) using `mi_zip_fact` as source.

    Factors used (deterministic):
      - potential_remaining (primary)
      - army_share (secondary)
      - p2p (tertiary)

    Scores are relative within the current query result set and returned
    with an explicit reason and suggested_focus.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        # actual columns in mi_zip_fact: id, zip5, potential_remaining, army_share_of_potential, p2p, army_potential
        q = "SELECT id, zip5, potential_remaining, army_share_of_potential, p2p, army_potential FROM mi_zip_fact WHERE 1=1"
        params = ()
        if rsid_prefix:
            q += " AND rsid_prefix = ?"
            params = (rsid_prefix,)
        cur.execute(q, params)
        rows = cur.fetchall()
    except Exception:
        return {"error": "failed_to_read_mi_zip_fact", "data": []}

    if not rows:
        return {"count": 0, "results": []}

    # compute relative normals
    potentials = [float(r[2] or 0) for r in rows]
    max_pot = max(potentials) or 1.0

    out = []
    for r in rows:
        mid = r[0]
        zip5 = r[1]
        potential = float(r[2] or 0)
        army_share = float(r[3] or 0)
        p2p = float(r[4] or 0)
        army_potential = float(r[5] or 0)

        pot_norm = potential / max_pot
        army_norm = min(army_share, 1.0)
        p2p_norm = min(p2p, 1.0)

        # Weights
        w_pot = 0.5
        w_army = 0.3
        w_p2p = 0.2

        score = round((pot_norm * w_pot + army_norm * w_army + p2p_norm * w_p2p) * 100, 2)

        if score >= 50:
            recommendation = 'prioritize_now'
        elif score >= 25:
            recommendation = 'monitor'
        else:
            recommendation = 'deprioritize'

        suggested = 'zip_outreach' if pot_norm > 0.5 else 'market_analysis'
        reason = f"potential_remaining={int(potential)}, army_share_of_potential={round(army_share,3)}, p2p={round(p2p,3)}"

        out.append({
            "market_id": zip5 or mid,
            "score": score,
            "recommendation": recommendation,
            "suggested_focus": suggested,
            "reason": reason,
            "components": {"potential_remaining": potential, "army_share_of_potential": army_share, "p2p": p2p, "army_potential": army_potential}
        })

    out_sorted = sorted(out, key=lambda r: r.get('score', 0), reverse=True)[:int(top_n)]
    return {"count": len(out_sorted), "results": out_sorted}


@router.get('/ai/recommendations/events')
def ai_recommendations_events(top_n: int = Query(50), event_id: Optional[str] = Query(None)):
    """Rank events using `event_metrics` and simple conversion proxies.

    Factors used: engagement_count, conversion proxies (attendees->leads), recent ROI if available.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        # actual columns in event_metrics: id, event_id, impressions, engagements, leads, appts_made, appts_conducted, contracts, accessions
        # roi column is not present; select available metrics
        q = "SELECT id, event_id, impressions, engagements, leads, appts_made, appts_conducted FROM event_metrics WHERE 1=1"
        params = ()
        if event_id:
            q += " AND event_id = ?"
            params = (event_id,)
        cur.execute(q, params)
        rows = cur.fetchall()
    except Exception:
        return {"error": "failed_to_read_event_metrics", "data": []}

    if not rows:
        return {"count": 0, "results": []}

    # normalize by max engagement
    engs = [float(r[2] or 0) for r in rows]
    max_eng = max(engs) or 1.0

    out = []
    for r in rows:
        rid = r[0]
        eid = r[1]
        impressions = float(r[2] or 0)
        engagement = float(r[3] or 0)
        leads = float(r[4] or 0)
        appts_made = float(r[5] or 0)
        appts_conducted = float(r[6] or 0)
        roi = 0.0

        eng_norm = engagement / max_eng
        # use engagements as the attendee proxy; conversion = leads / engagements
        conv = (leads / engagement) if engagement else 0.0

        # weights
        w_eng = 0.5
        w_conv = 0.3
        w_roi = 0.2

        roi_norm = min(max(roi / 100.0, 0.0), 1.0)

        score = round((eng_norm * w_eng + min(conv,1.0) * w_conv + roi_norm * w_roi) * 100, 2)

        if score >= 50:
            recommendation = 'prioritize_now'
        elif score >= 25:
            recommendation = 'monitor'
        else:
            recommendation = 'deprioritize'

        suggested = 'increase_engagement_quality' if conv < 0.05 else 'scale_event'
        reason = f"engagement={int(engagement)}, conversion={round(conv,3)}, roi={round(roi,2)}"

        out.append({
            "event_id": eid or rid,
            "score": score,
            "recommendation": recommendation,
            "suggested_focus": suggested,
            "reason": reason,
            "components": {"engagement": engagement, "conversion": conv, "roi": roi}
        })

    out_sorted = sorted(out, key=lambda r: r.get('score', 0), reverse=True)[:int(top_n)]
    return {"count": len(out_sorted), "results": out_sorted}


@router.get('/ai/recommendations/marketing')
def ai_recommendations_marketing(top_n: int = Query(50), channel: Optional[str] = Query(None), org_unit_id: Optional[str] = Query(None)):
    """Rank marketing campaigns using `fact_marketing`.

    Factors used: engagement rate, conversion rate, cost proxies if available.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        q = "SELECT id, campaign, channel, impressions, engagements, clicks, conversions FROM fact_marketing WHERE 1=1"
        params = []
        if channel:
            q += " AND channel = ?"
            params.append(channel)
        if org_unit_id:
            q += " AND org_unit_id = ?"
            params.append(org_unit_id)
        cur.execute(q, tuple(params))
        rows = cur.fetchall()
    except Exception:
        return {"error": "failed_to_read_fact_marketing", "data": []}

    if not rows:
        return {"count": 0, "results": []}

    imps = [float(r[3] or 0) for r in rows]
    max_imps = max(imps) or 1.0

    out = []
    for r in rows:
        mid = r[0]
        campaign = r[1]
        ch = r[2]
        imps = float(r[3] or 0)
        engagements = float(r[4] or 0)
        clicks = float(r[5] or 0)
        convs = float(r[6] or 0)

        engagement_rate = (engagements / imps) if imps else 0.0
        click_rate = (clicks / imps) if imps else 0.0
        conv_rate = (convs / imps) if imps else 0.0

        # weights
        w_eng = 0.4
        w_click = 0.3
        w_conv = 0.3

        score = round((engagement_rate * w_eng + click_rate * w_click + conv_rate * w_conv) * 100, 2)

        if score >= 50:
            recommendation = 'prioritize_now'
        elif score >= 25:
            recommendation = 'monitor'
        else:
            recommendation = 'deprioritize'

        suggested = 'email_follow_up' if click_rate > 0.02 else 'creative_refresh'
        reason = f"impressions={int(imps)}, engagement_rate={round(engagement_rate,3)}, conv_rate={round(conv_rate,3)}"

        out.append({
            "campaign": campaign or mid,
            "channel": ch,
            "score": score,
            "recommendation": recommendation,
            "suggested_focus": suggested,
            "reason": reason,
            "components": {"impressions": int(imps), "engagement_rate": round(engagement_rate,4), "conversion_rate": round(conv_rate,4)}
        })

    out_sorted = sorted(out, key=lambda r: r.get('score', 0), reverse=True)[:int(top_n)]
    return {"count": len(out_sorted), "results": out_sorted}
