from fastapi import APIRouter, Query
from services.api.app.db import connect
from services.api.app.services.coa_engine import fetch_latest_for_unit
from services.api.app.services import lead_line as lead_line_mod
from services.api.app.services.ai_lms import compute_decision_summary
from datetime import date

router = APIRouter()


@router.get("/v2/coa/compare")
def coa_compare(unit_rsid: str = Query(..., description="Unit RSID to compare COAs for")):
    # compute lead-line
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT mission_total FROM mission_allocation_runs WHERE unit_rsid=? ORDER BY created_at DESC LIMIT 1', (unit_rsid,))
        row = cur.fetchone()
        annual = int(row['mission_total']) if row and row['mission_total'] is not None else 0
        start_of_year = date(date.today().year, 1, 1).isoformat()
        cur.execute('SELECT COUNT(*) as cnt FROM fact_lead_journey WHERE unit_rsid=? AND contract_flag=1 AND created_dt>=?', (unit_rsid, start_of_year))
        cnt = cur.fetchone()
        actual = int(cnt['cnt']) if cnt and cnt['cnt'] is not None else 0
        ll = lead_line_mod.calculate_lead_line(actual, annual)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # fetch latest COAs and normalize
    coas_raw = fetch_latest_for_unit(unit_rsid, limit=10)
    coas = []
    # pick one COA per type (PRIMARY, ALTERNATE, AGGRESSIVE) - prefer most recent
    picked = {}
    preferred = ['PRIMARY', 'ALTERNATE', 'AGGRESSIVE']
    for c in coas_raw:
        ra = c.get('recommended_actions_json') or {}
        # normalize recommended_actions_json to dict
        if isinstance(ra, list) and ra:
            # try to pick the first dict entry
            ra = next((x for x in ra if isinstance(x, dict)), {})
        if not isinstance(ra, dict):
            ra = {}
        obj = c.get('objective_json') or {}
        if not isinstance(obj, dict):
            obj = {}
        mapped = {
            'type': (c.get('coa_type') or '').upper(),
            'title': c.get('coa_title'),
            'summary': c.get('coa_summary'),
            'recommendation_id': c.get('id'),
            'recommendation_table': 'coa_recommendations',
            # carry through original evidence fields so lead linkage can be resolved
            'supporting_evidence_json': c.get('supporting_evidence_json'),
            'market_key': c.get('market_key'),
            'school_id': c.get('school_id'),
            'zip5': c.get('zip5'),
            # lead-list linkage placeholders (populated below when possible)
            'lead_query': None,
            'lead_count': None,
            'recruiters_assigned': (ra.get('task_organization') or {}).get('recruiters_assigned'),
            'timeline_days': ra.get('timeline_days') or (obj.get('target_completion_window_days')),
            'contracts_to_recover': obj.get('contracts_to_recover'),
            'risk': c.get('risk') or c.get('risk_level'),
            'expected_effect': c.get('expected_effect') or c.get('expected_benefit')
        }
        t = mapped['type']
        if t in preferred and t not in picked:
            picked[t] = mapped

    # order coas by preferred list
    for t in preferred:
        if t in picked:
            coas.append(picked[t])

    # fetch LMS summary and apply small, explainable adaptive adjustments per COA type
    try:
        summary_conn = connect()
        summary = compute_decision_summary(summary_conn, unit_rsid=unit_rsid)
    except Exception:
        summary = None
    finally:
        try:
            summary_conn.close()
        except Exception:
            pass

    # Apply adjustment rules (small, capped, explainable)
    # Rules: base_adj = (success_rate - 0.5) * 0.2  -> range approx [-0.1, +0.1]
    #        contracts_adj = min(0.05, avg_contracts * 0.01)
    #        total_adj = clamp(base_adj + contracts_adj, -0.15, +0.15)
    def clamp(v, lo=-0.15, hi=0.15):
        return max(lo, min(hi, v))

    for c in coas:
        t = (c.get('type') or '').upper()
        adj = 0.0
        reasons = []
        if summary:
            sr = (summary.get('success_rate_by_type') or {}).get(t, None)
            ac = (summary.get('avg_contracts_by_type') or {}).get(t, None)
            if sr is not None:
                base_adj = (float(sr) - 0.5) * 0.2
                adj += base_adj
                reasons.append(f"success_rate={sr} -> {round(base_adj,3):+}")
            if ac is not None:
                contracts_adj = min(0.05, float(ac) * 0.01)
                adj += contracts_adj
                reasons.append(f"avg_contracts={ac} -> {round(contracts_adj,3):+}")
        adj = clamp(adj)
        c['adaptive_adjustment'] = round(adj, 3)
        if reasons:
            c['adaptive_reason'] = f"Adjustment applied: {', '.join(reasons)}; capped to {c['adaptive_adjustment']}"
        else:
            c['adaptive_reason'] = 'No historical signal; no adjustment applied.'

        # compute a simple, explainable adjusted priority score
        base_score = 0.5
        c['adjusted_priority_score'] = round(base_score + c['adaptive_adjustment'], 3)

        # Estimate recruiter availability / feasibility for this COA
        try:
            db_conn = connect()
            dbc = db_conn.cursor()
            available = None
            # 1) try mission_analysis by station/company matching unit_rsid
            try:
                dbc.execute('SELECT recruiters_assigned FROM mission_analysis WHERE station=? OR company=? ORDER BY created_at DESC LIMIT 1', (unit_rsid, unit_rsid))
                r = dbc.fetchone()
                if r and r['recruiters_assigned'] is not None:
                    available = int(r['recruiters_assigned'])
            except Exception:
                available = None

            # 2) fallback: try dod_branch_comparison by geographic id (use market_key/zip5 if present)
            if available is None:
                try:
                    mk = c.get('supporting_evidence_json') and c.get('supporting_evidence_json').get('market')
                except Exception:
                    mk = None
                market_key = mk.get('market_id') if isinstance(mk, dict) else c.get('market_key') or c.get('zip5')
                if market_key:
                    try:
                        dbc.execute("SELECT total_recruiters FROM dod_branch_comparison WHERE geographic_id=? ORDER BY last_updated DESC LIMIT 1", (market_key,))
                        rr = dbc.fetchone()
                        if rr and rr['total_recruiters'] is not None:
                            available = int(rr['total_recruiters'])
                    except Exception:
                        available = None

            # final fallback default
            if available is None:
                available = 3

            suggested = c.get('recruiters_assigned') or 1
            max_feasible = min(available, int(suggested))
            unavailable = max(0, int(suggested) - max_feasible)
            feasible = (max_feasible >= int(suggested))
            note = 'Sufficient recruiters available' if feasible else f'Only {available} available; {unavailable} short for suggested {suggested}'
            c['availability'] = {
                'available_recruiters': available,
                'unavailable_conflicts': unavailable,
                'max_feasible_recruiters': max_feasible,
                'feasible': feasible,
                'note': note
            }
            # Lead-linkage: resolve school_id/zip5 from supporting evidence if present
            try:
                se = c.get('supporting_evidence_json') or {}
                school_id = None
                zip5 = None
                if isinstance(se, list):
                    # look for fusion evidence
                    for ev in se:
                        if ev.get('type') == 'fusion' and isinstance(ev.get('payload'), dict):
                            school_id = ev['payload'].get('school_id') or school_id
                            zip5 = ev['payload'].get('zip5') or zip5
                elif isinstance(se, dict):
                    payload = se.get('payload') if se.get('payload') else se
                    if isinstance(payload, dict):
                        school_id = payload.get('school_id') or None
                        zip5 = payload.get('zip5') or None
                # fallback to objective or direct fields
                if not school_id:
                    school_id = c.get('supporting_evidence_json') and c.get('supporting_evidence_json').get('school_id') if isinstance(c.get('supporting_evidence_json'), dict) else None
                if not zip5:
                    zip5 = c.get('zip5') or None

                # count leads matching school or zip5
                lead_count = None
                try:
                    if school_id or zip5:
                        lc_conn = connect()
                        lcur = lc_conn.cursor()
                        # Prefer canonical lead columns when they actually contain matching data;
                        # otherwise fall back to legacy columns to avoid breaking linkage when
                        # canonical columns exist but are empty for legacy rows.
                        from services.api.app.db import column_exists
                        has_school_col = column_exists(lc_conn, 'leads', 'school_id')
                        has_zip_col = column_exists(lc_conn, 'leads', 'zip5')

                        use_school_col = False
                        use_zip_col = False
                        # If canonical column exists and a matching value is present, prefer it
                        if school_id and has_school_col:
                            try:
                                lcur.execute('SELECT 1 as ok FROM leads WHERE school_id=? LIMIT 1', (school_id,))
                                use_school_col = bool(lcur.fetchone())
                            except Exception:
                                use_school_col = False

                        if zip5 and has_zip_col:
                            try:
                                lcur.execute('SELECT 1 as ok FROM leads WHERE zip5=? LIMIT 1', (zip5,))
                                use_zip_col = bool(lcur.fetchone())
                            except Exception:
                                use_zip_col = False

                        school_col = 'school_id' if use_school_col else 'campaign_source'
                        zip_col = 'zip5' if use_zip_col else 'cbsa_code'
                        if school_id and zip5:
                            lcur.execute(f"SELECT COUNT(*) as cnt FROM leads WHERE {school_col}=? OR {zip_col}=?", (school_id, zip5))
                        elif school_id:
                            lcur.execute(f"SELECT COUNT(*) as cnt FROM leads WHERE {school_col}=?", (school_id,))
                        else:
                            lcur.execute(f"SELECT COUNT(*) as cnt FROM leads WHERE {zip_col}=?", (zip5,))
                        rlc = lcur.fetchone()
                        lead_count = int(rlc['cnt']) if rlc and rlc['cnt'] is not None else 0
                except Exception:
                    lead_count = None
                finally:
                    try:
                        lc_conn.close()
                    except Exception:
                        pass

                c['school_id'] = school_id
                c['zip5'] = zip5
                c['lead_query'] = {'school_id': school_id, 'zip5': zip5}
                c['lead_count'] = lead_count
            except Exception:
                c['school_id'] = None
                c['zip5'] = None
                c['lead_query'] = None
                c['lead_count'] = None
        except Exception:
            c['availability'] = {'available_recruiters': None, 'unavailable_conflicts': None, 'max_feasible_recruiters': None, 'feasible': None, 'note': 'availability unknown'}
        finally:
            try:
                db_conn.close()
            except Exception:
                pass

        # Add a short execution checklist to each COA
        checklist = [
            {'step': 'Assign recruiters', 'detail': 'Allocate recruiters and confirm availability'},
            {'step': 'Schedule engagements', 'detail': f'Schedule engagements at target within {c.get("timeline_days") or "N/A"} days'},
            {'step': 'Pull target lead list', 'detail': 'Export leads for target school/zip for outreach'},
            {'step': 'Execute follow-ups', 'detail': 'Perform follow-ups and log engagement outcomes'},
            {'step': 'Review pipeline', 'detail': f'Review pipeline in {14 if not c.get("timeline_days") else max(7, int(c.get("timeline_days")))} days'}
        ]
        c['checklist'] = checklist

    # sort by adjusted priority (highest first) and mark top recommendation
    coas = sorted(coas, key=lambda x: x.get('adjusted_priority_score', 0), reverse=True)
    if coas:
        coas[0]['is_top_recommendation'] = True

    return {
        'unit_rsid': unit_rsid,
        'lead_line': {'status': ll.get('status'), 'variance': ll.get('variance')},
        'coas': coas
    }
