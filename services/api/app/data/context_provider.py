def get_operational_context():
    """
    Temporary context provider.
    Later this will pull from:
    - EMM
    - EMM Portal
    - User role/session
    - Command configuration
    """

    # This returns a structured, authoritative operational context for
    # the recommendation engine. In production this should be populated
    # from live signals (EMM, EMM Portal, session, budget systems, etc.).
    # conservative defaults; attempt to enrich from EMM integration
    emm_status = None
    try:
        from services.api.app.routers.emm_integration import get_emm_status
        emm_status = get_emm_status()
    except Exception:
        emm_status = None

    emm_available = True
    emm_portal_available = True
    available_systems = ["EMM", "EMM_PORTAL"]
    if isinstance(emm_status, dict):
        emm_available = bool(emm_status.get("emm_available", True))
        emm_portal_available = bool(emm_status.get("emm_portal_available", True))
        # allow integration to declare fewer systems
        if emm_status.get("data_source") != "stub":
            available_systems = emm_status.get("available_systems", available_systems)

    # attempt to read sync-layer connectivity flags from emm_sync
    emm_calendar_connected = False
    emm_budget_connected = False
    emm_leads_connected = False
    emm_roi_connected = False
    try:
        from services.api.app.routers.emm_sync import get_emm_calendar_sync, get_emm_budget_sync, get_emm_leads_sync, get_emm_roi_sync
        try:
            cal = get_emm_calendar_sync()
            emm_calendar_connected = bool(cal and cal.get('source') != 'stub' and (cal.get('synced') or []))
        except Exception:
            emm_calendar_connected = False
        try:
            bud = get_emm_budget_sync()
            emm_budget_connected = bool(bud and bud.get('source') != 'stub' and (bud.get('synced') or []))
        except Exception:
            emm_budget_connected = False
        try:
            leads = get_emm_leads_sync()
            emm_leads_connected = bool(leads and leads.get('source') != 'stub' and (leads.get('synced') or []))
        except Exception:
            emm_leads_connected = False
        try:
            roi = get_emm_roi_sync()
            emm_roi_connected = bool(roi and roi.get('source') != 'stub' and (roi.get('synced') or []))
        except Exception:
            emm_roi_connected = False
    except Exception:
        # if importing fails, leave defaults as False
        pass

    # attempt to read commander intent from the in-memory store
    commander_intent_loaded = False
    priority_focus = []
    target_markets = []
    try:
        from services.api.app.data.commander_intent_store import get_current_intent
        try:
            ci = get_current_intent()
            if isinstance(ci, dict) and ci.get('commander_intent_loaded'):
                commander_intent_loaded = True
                priority_focus = ci.get('merged', {}).get('priorities', []) or []
                target_markets = ci.get('merged', {}).get('focus_markets', []) or []
        except Exception:
            commander_intent_loaded = False
    except Exception:
        # leave defaults
        pass

    return {
        "command_scope": "battalion",
        "funding_available": [
            "organic",
            "company_funded",
            "battalion_funded"
        ],
        "event_date": None,
        "event_type": None,
        "geography_scope": None,
        "market_partial_rate": 0.0,
        "funnel_lead_count": 0,
        "funnel_applicant_count": 0,
        "funnel_dep_count": 0,
        "funnel_ship_count": 0,
        "lead_to_applicant_rate": 0.0,
        "applicant_to_dep_rate": 0.0,
        "days_until_event": None,
        "emm_available": emm_available,
        "emm_portal_available": emm_portal_available,
        "available_systems": available_systems,
        "emm_calendar_connected": emm_calendar_connected,
        "emm_budget_connected": emm_budget_connected,
        "emm_leads_connected": emm_leads_connected,
        "emm_roi_connected": emm_roi_connected,
        "commander_intent_loaded": commander_intent_loaded,
        "priority_focus": priority_focus,
        "target_markets": target_markets,
        "user_role": "420T"
    }
