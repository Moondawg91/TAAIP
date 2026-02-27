from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from .. import db
from .rbac import require_scope
from datetime import datetime

router = APIRouter(prefix='/v1/roi', tags=['roi'])


def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _ensure_roi_tables(conn):
    cur = conn.cursor()
    # simple ROI results table
    cur.execute('''CREATE TABLE IF NOT EXISTS roi_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_start TEXT,
        period_end TEXT,
        org_scope TEXT,
        commit_fund REAL,
        adj_contracts INTEGER,
        value_per_contract REAL,
        value_out REAL,
        roi REAL,
        kpi_score REAL,
        conv_score REAL,
        roi_score REAL,
        payload_json TEXT,
        created_at TEXT
    )''')
    # conversion benchmarks (optional)
    cur.execute('''CREATE TABLE IF NOT EXISTS conversion_benchmark (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        objective TEXT,
        tactic TEXT,
        b_L2A REAL,
        b_A2C REAL,
        b_C2K REAL,
        b_L2K REAL,
        fiscal_year INTEGER
    )''')
    conn.commit()


@router.post('/financial')
def compute_financial_roi(payload: Dict[str, Any], allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    """Compute financial ROI.

    Expected payload keys:
      - commit_fund (Cost)
      - adj_contracts (Adjusted contracts)
      - value_per_contract (optional override)
      - vpc_lookup (optional): if present, ignored here (future)
    """
    commit_fund = float(payload.get('commit_fund') or payload.get('cost') or 0)
    adj_contracts = int(payload.get('adj_contracts') or payload.get('adj_contracts') or 0)
    value_per_contract = payload.get('value_per_contract')
    if value_per_contract is None:
        # fallback to env or payload default
        try:
            value_per_contract = float(payload.get('vpc') or 0)
        except Exception:
            value_per_contract = 0.0
    else:
        value_per_contract = float(value_per_contract)

    value_out = adj_contracts * value_per_contract
    roi = None
    if commit_fund:
        roi = (value_out - commit_fund) / commit_fund

    conn = db.connect()
    try:
        _ensure_roi_tables(conn)
        cur = conn.cursor()
        cur.execute('INSERT INTO roi_result(period_start, period_end, org_scope, commit_fund, adj_contracts, value_per_contract, value_out, roi, payload_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)', (
            payload.get('period_start'), payload.get('period_end'), payload.get('org_scope'), commit_fund, adj_contracts, value_per_contract, value_out, roi, str(payload), now_iso()
        ))
        conn.commit()
        return {'commit_fund': commit_fund, 'adj_contracts': adj_contracts, 'value_per_contract': value_per_contract, 'value_out': value_out, 'roi': roi}
    finally:
        conn.close()


@router.post('/score')
def compute_roi_score(payload: Dict[str, Any], allowed_orgs: Optional[list] = Depends(require_scope('STATION'))):
    """Compute ROI_Score (Benchmark Index Option A).

    Inputs (preferred): cost, impressions, engagements, adj_leads, appt_made, appt_conduct, adj_contracts, objective, tactic
    Benchmarks are read from `cost_benchmark` (for cost KPIs) and `conversion_benchmark` for conversion baselines.
    If benchmark rows are not present, KPI_band scoring or conversion indexes will gracefully return null/na values.
    """
    # ingest inputs
    cost = float(payload.get('cost') or payload.get('spend') or 0)
    impressions = int(payload.get('impressions') or 0)
    engagements = int(payload.get('engagements') or 0)
    adj_leads = int(payload.get('adj_leads') or payload.get('adjLeads') or 0)
    appt_made = int(payload.get('appt_made') or payload.get('appts') or 0)
    appt_conduct = int(payload.get('appt_conduct') or payload.get('appt_conduct') or 0)
    adj_contracts = int(payload.get('adj_contracts') or payload.get('adjContracts') or 0)
    objective = payload.get('objective')
    tactic = payload.get('tactic')

    # Step A: compute KPIs
    CPM = (cost / (impressions/1000)) if impressions else None
    CPE = (cost / engagements) if engagements else None
    CPL = (cost / adj_leads) if adj_leads else None

    # choose primary KPI based on objective
    KPI_name = None
    if objective and objective.lower().startswith('aware'):
        KPI_name = 'CPM'
    elif objective and (objective.lower().startswith('eng') or objective.lower().startswith('interest')):
        KPI_name = 'CPE'
    elif objective and (objective.lower().startswith('activ') or objective.lower().startswith('lead') or objective.lower().startswith('generate')):
        KPI_name = 'CPL'
    else:
        # fallback: prefer CPL if leads present, else CPE if engagements present, else CPM
        if adj_leads: KPI_name = 'CPL'
        elif engagements: KPI_name = 'CPE'
        else: KPI_name = 'CPM'

    actual_kpi = {'CPM': CPM, 'CPE': CPE, 'CPL': CPL}.get(KPI_name)

    conn = db.connect()
    try:
        _ensure_roi_tables(conn)
        cur = conn.cursor()
        # attempt to find cost benchmark row (benchmarks table may be `cost_benchmark`)
        kpi_score = None
        try:
            cur.execute("SELECT threshold_low, threshold_mid FROM cost_benchmark WHERE lower(kpi_type)=? AND lower(tactic)=? AND lower(stage)=? ORDER BY fiscal_year DESC LIMIT 1", (KPI_name.lower(), (tactic or '').lower(), (objective or '').lower()))
            b = cur.fetchone()
            if b:
                lt1 = b['threshold_low'] if 'threshold_low' in b.keys() else b[0]
                sd12 = b['threshold_mid'] if 'threshold_mid' in b.keys() else b[1]
                if actual_kpi is None:
                    kpi_score = None
                else:
                    # lower-is-better scoring
                    if actual_kpi <= lt1:
                        kpi_score = 100
                    elif actual_kpi <= sd12:
                        kpi_score = 70
                    else:
                        kpi_score = 30
        except Exception:
            kpi_score = None

        # Step C: conversion score
        # compute conversion rates
        L2A = (appt_made / adj_leads) if adj_leads else None
        A2C = (appt_conduct / appt_made) if appt_made else None
        C2K = (adj_contracts / appt_conduct) if appt_conduct else None
        L2K = (adj_contracts / adj_leads) if adj_leads else None

        # fetch conversion benchmarks
        conv_score = None
        try:
            cur.execute('SELECT b_L2A, b_A2C, b_C2K, b_L2K FROM conversion_benchmark WHERE lower(objective)=? AND lower(tactic)=? ORDER BY fiscal_year DESC LIMIT 1', ((objective or '').lower(), (tactic or '').lower()))
            cb = cur.fetchone()
            if cb:
                bL2A = cb['b_L2A'] if 'b_L2A' in cb.keys() else cb[0]
                bA2C = cb['b_A2C'] if 'b_A2C' in cb.keys() else cb[1]
                bC2K = cb['b_C2K'] if 'b_C2K' in cb.keys() else cb[2]
                bL2K = cb['b_L2K'] if 'b_L2K' in cb.keys() else cb[3]
                # compute indexes with cap
                inds = []
                for actual, bench in ((L2A, bL2A), (A2C, bA2C), (C2K, bC2K), (L2K, bL2K)):
                    try:
                        if actual is None or bench is None or bench == 0:
                            idx = 1.0
                        else:
                            idx = min(1.25, float(actual) / float(bench))
                    except Exception:
                        idx = 1.0
                    inds.append(idx)
                conv_score = 100.0 * (sum(inds) / len(inds)) if inds else None
        except Exception:
            conv_score = None

        # Step D: final ROI_Score
        roi_score = None
        if kpi_score is None and conv_score is None:
            roi_score = None
        else:
            kpart = kpi_score if kpi_score is not None else 0
            cpart = conv_score if conv_score is not None else 0
            roi_score = 0.6 * kpart + 0.4 * cpart

        # persist result row
        cur.execute('INSERT INTO roi_result(period_start, period_end, org_scope, commit_fund, adj_contracts, value_per_contract, value_out, roi, kpi_score, conv_score, roi_score, payload_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            payload.get('period_start'), payload.get('period_end'), payload.get('org_scope'), cost, adj_contracts, payload.get('value_per_contract'), adj_contracts * float(payload.get('value_per_contract') or 0), None, kpi_score, conv_score, roi_score, str(payload), now_iso()
        ))
        conn.commit()

        return {
            'KPI': KPI_name,
            'actual_kpi': actual_kpi,
            'kpi_score': kpi_score,
            'L2A': L2A,
            'A2C': A2C,
            'C2K': C2K,
            'L2K': L2K,
            'conv_score': conv_score,
            'roi_score': roi_score
        }
    finally:
        conn.close()


@router.get('/v2/roi/kpis')
def roi_kpis(unit_rsid: Optional[str] = None, echelon: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, compare_mode: str = 'THRESHOLDS', allowed_orgs: Optional[list] = Depends(require_scope('BN'))):
    """Return KPI summary for a unit scope."""
    conn = db.connect()
    try:
        cur = conn.cursor()

        # resolve scope rsids (simple: if unit_rsid not provided => global)
        rsids = None
        if unit_rsid and unit_rsid.upper() != 'USAREC':
            # collect rsid values for unit and descendants
            try:
                cur.execute("SELECT id FROM org_unit WHERE rsid = ?", (unit_rsid,))
                row = cur.fetchone()
                if row:
                    uid = row['id']
                    cur.execute("WITH RECURSIVE subtree(id) AS (SELECT id FROM org_unit WHERE id=? UNION ALL SELECT o.id FROM org_unit o JOIN subtree s ON o.parent_id = s.id) SELECT rsid FROM org_unit WHERE id IN (SELECT id FROM subtree)", (uid,))
                    rsids = [r['rsid'] for r in cur.fetchall()]
            except Exception:
                rsids = [unit_rsid]

        # build where clauses
        params = []
        time_clause = ""
        if start_date:
            time_clause += " AND lead_created_dt >= ?"
            params.append(start_date)
        if end_date:
            time_clause += " AND lead_created_dt <= ?"
            params.append(end_date)

        # leads_total
        where_rs = ""
        if rsids:
            where_rs = " AND unit_rsid IN (%s)" % (','.join('?' for _ in rsids))
            params = rsids + params

        # leads
        q_leads = f"SELECT COUNT(DISTINCT lead_id) as leads_total FROM lead_journey_fact WHERE 1=1 {where_rs} {time_clause}"
        cur.execute(q_leads, params)
        leads_total = cur.fetchone()['leads_total'] if cur.rowcount != 0 else 0

        # contracts
        q_contracts = f"SELECT COUNT(*) as contracts_total FROM lead_journey_fact WHERE contract_flag=1 {where_rs} {time_clause}"
        cur.execute(q_contracts, params)
        contracts_total = cur.fetchone()['contracts_total'] if cur.rowcount != 0 else 0

        # spend
        q_spend = "SELECT IFNULL(SUM(amount),0) as spend_total FROM spend_fact WHERE 1=1"
        spend_params = []
        if rsids:
            q_spend += " AND unit_rsid IN (%s)" % (','.join('?' for _ in rsids))
            spend_params.extend(rsids)
        if start_date:
            q_spend += " AND spend_dt >= ?"
            spend_params.append(start_date)
        if end_date:
            q_spend += " AND spend_dt <= ?"
            spend_params.append(end_date)
        cur.execute(q_spend, spend_params)
        spend_total = cur.fetchone()['spend_total'] or 0

        cpl = (spend_total / leads_total) if leads_total else None
        cpc = (spend_total / contracts_total) if contracts_total else None

        # average flash_to_bang (days) approximate
        q_ftb = f"SELECT AVG(julianday(contract_dt) - julianday(lead_created_dt)) as avg_days FROM lead_journey_fact WHERE contract_flag=1 {where_rs} {time_clause}"
        cur.execute(q_ftb, params)
        avg_days = cur.fetchone()['avg_days']

        # thresholds
        cur.execute("SELECT metric_key, value FROM roi_thresholds")
        th = {r['metric_key']: r['value'] for r in cur.fetchall()}
        cpl_target = th.get('cpl_target')
        cpc_target = th.get('cpc_target')

        def band_for(value, target):
            if value is None or target is None:
                return {'value': value, 'meets_threshold': False, 'band': 'RED'}
            # lower-is-better for CPL/CPC
            if value <= target:
                return {'value': value, 'meets_threshold': True, 'band': 'GREEN'}
            if value <= target * 1.1:
                return {'value': value, 'meets_threshold': False, 'band': 'AMBER'}
            return {'value': value, 'meets_threshold': False, 'band': 'RED'}

        status = {'cpl': band_for(cpl, cpl_target), 'cpc': band_for(cpc, cpc_target), 'contracts': {'value': contracts_total, 'band': 'GREEN' if contracts_total>0 else 'RED'}}

        comparisons = {}
        # compute unit_avg if requested
        if compare_mode in ('THRESHOLDS_UNIT_AVG','THRESHOLDS_UNIT_BDE_AVG') and unit_rsid:
            # last 12 months window
            import datetime as _dt
            ed = _dt.datetime.utcnow()
            sd = ed - _dt.timedelta(days=365)
            sd_s = sd.strftime('%Y-%m-%d')
            ed_s = ed.strftime('%Y-%m-%d')
            # reuse params
            p = []
            q = "SELECT COUNT(DISTINCT lead_id) as leads_total FROM lead_journey_fact WHERE lead_created_dt >= ? AND lead_created_dt <= ? AND unit_rsid = ?"
            cur.execute(q, (sd_s, ed_s, unit_rsid))
            ua_leads = cur.fetchone()['leads_total']
            cur.execute("SELECT IFNULL(SUM(amount),0) as spend_total FROM spend_fact WHERE spend_dt >= ? AND spend_dt <= ? AND unit_rsid = ?", (sd_s, ed_s, unit_rsid))
            ua_spend = cur.fetchone()['spend_total'] or 0
            ua_cpl = (ua_spend / ua_leads) if ua_leads else None
            comparisons['unit_avg'] = {'leads_total': ua_leads, 'spend_total': ua_spend, 'cpl': ua_cpl}

        # bde_avg placeholder: attempt to find parent BDE by walking org_unit
        if compare_mode == 'THRESHOLDS_UNIT_BDE_AVG' and unit_rsid:
            try:
                cur.execute("SELECT id, parent_id FROM org_unit WHERE rsid = ?", (unit_rsid,))
                r = cur.fetchone()
                bde_rs = None
                if r:
                    pid = r['parent_id']
                    # walk up until type == 'BDE' or parent is null
                    while pid:
                        cur.execute("SELECT id, parent_id, type, rsid FROM org_unit WHERE id = ?", (pid,))
                        prow = cur.fetchone()
                        if not prow:
                            break
                        if (prow.get('type') or '').upper() == 'BDE':
                            bde_rs = prow.get('rsid')
                            break
                        pid = prow.get('parent_id')
                if bde_rs:
                    # compute bde numbers for last 12 months
                    import datetime as _dt
                    ed = _dt.datetime.utcnow()
                    sd = ed - _dt.timedelta(days=365)
                    sd_s = sd.strftime('%Y-%m-%d')
                    ed_s = ed.strftime('%Y-%m-%d')
                    cur.execute("SELECT COUNT(DISTINCT l.lead_id) as leads_total FROM lead_journey_fact l JOIN org_unit o ON l.unit_rsid = o.rsid WHERE o.id IN (SELECT id FROM org_unit WHERE rsid = ? OR parent_id = (SELECT id FROM org_unit WHERE rsid=?)) AND l.lead_created_dt >= ? AND l.lead_created_dt <= ?", (bde_rs, bde_rs, sd_s, ed_s))
                    bde_leads = cur.fetchone()['leads_total']
                    cur.execute("SELECT IFNULL(SUM(s.amount),0) as spend_total FROM spend_fact s JOIN org_unit o ON s.unit_rsid = o.rsid WHERE o.id IN (SELECT id FROM org_unit WHERE rsid = ? OR parent_id = (SELECT id FROM org_unit WHERE rsid=?)) AND s.spend_dt >= ? AND s.spend_dt <= ?", (bde_rs, bde_rs, sd_s, ed_s))
                    bde_spend = cur.fetchone()['spend_total'] or 0
                    comparisons['bde_avg'] = {'leads_total': bde_leads, 'spend_total': bde_spend, 'cpl': (bde_spend / bde_leads) if bde_leads else None}
            except Exception:
                pass

        meta = {'unit_rsid': unit_rsid or 'USAREC', 'echelon': echelon or 'USAREC', 'start_date': start_date, 'end_date': end_date, 'compare_mode': compare_mode}

        return {
            'meta': meta,
            'thresholds': {'cpl_target': cpl_target, 'cpc_target': cpc_target},
            'kpis': {
                'events': 0,
                'spend_total': spend_total,
                'leads_total': leads_total,
                'contacts_total': None,
                'appointments_total': None,
                'applicants_total': None,
                'contracts_total': contracts_total,
                'cpl': cpl,
                'cpc': cpc,
                'flash_to_bang_median_days': avg_days,
                'conversion_rates': {}
            },
            'status': status,
            'comparisons': comparisons
        }
    finally:
        conn.close()


@router.get('/v2/roi/breakdown')
def roi_breakdown(unit_rsid: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('BN'))):
    """Return breakdown by event_type, source_type, and child unit."""
    conn = db.connect()
    try:
        cur = conn.cursor()
        params = []
        where = " WHERE 1=1"
        if unit_rsid and unit_rsid.upper() != 'USAREC':
            where += " AND unit_rsid = ?"
            params.append(unit_rsid)
        if start_date:
            where += " AND lead_created_dt >= ?"
            params.append(start_date)
        if end_date:
            where += " AND lead_created_dt <= ?"
            params.append(end_date)

        # breakdown by source_type
        cur.execute(f"SELECT source_type, COUNT(*) as leads FROM lead_journey_fact {where} GROUP BY source_type", params)
        by_source = [dict(r) for r in cur.fetchall()]

        # breakdown by event_type via join
        cur.execute(f"SELECT e.event_type, COUNT(l.lead_id) as leads FROM lead_journey_fact l JOIN event_fact e ON l.event_id = e.event_id {where.replace('lead_created_dt','l.lead_created_dt').replace('unit_rsid = ?','l.unit_rsid = ?')} GROUP BY e.event_type", params)
        by_event = [dict(r) for r in cur.fetchall()]

        return {'by_source': by_source, 'by_event': by_event}
    finally:
        conn.close()


@router.get('/v2/roi/funnel')
def roi_funnel(unit_rsid: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('BN'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        params = []
        where = " WHERE 1=1"
        if unit_rsid and unit_rsid.upper() != 'USAREC':
            where += " AND unit_rsid = ?"
            params.append(unit_rsid)
        if start_date:
            where += " AND lead_created_dt >= ?"
            params.append(start_date)
        if end_date:
            where += " AND lead_created_dt <= ?"
            params.append(end_date)

        cur.execute(f"SELECT COUNT(*) as leads FROM lead_journey_fact {where}", params)
        leads = cur.fetchone()['leads']
        cur.execute(f"SELECT COUNT(*) as contacts FROM lead_journey_fact WHERE contact_made_dt IS NOT NULL {where.replace('lead_created_dt','contact_made_dt')}", params)
        contacts = cur.fetchone()['contacts'] if cur.rowcount!=0 else None
        cur.execute(f"SELECT COUNT(*) as appts FROM lead_journey_fact WHERE appointment_dt IS NOT NULL {where.replace('lead_created_dt','appointment_dt')}", params)
        appts = cur.fetchone()['appts'] if cur.rowcount!=0 else None
        cur.execute(f"SELECT COUNT(*) as applicants FROM lead_journey_fact WHERE applicant_dt IS NOT NULL {where.replace('lead_created_dt','applicant_dt')}", params)
        applicants = cur.fetchone()['applicants'] if cur.rowcount!=0 else None
        cur.execute(f"SELECT COUNT(*) as contracts FROM lead_journey_fact WHERE contract_flag=1 {where}", params)
        contracts = cur.fetchone()['contracts'] if cur.rowcount!=0 else None

        conv = {}
        try:
            conv['lead_to_contact'] = (contacts / leads) if leads and contacts is not None else None
            conv['contact_to_appt'] = (appts / contacts) if contacts and appts is not None else None
            conv['appt_to_applicant'] = (applicants / appts) if appts and applicants is not None else None
            conv['applicant_to_contract'] = (contracts / applicants) if applicants and contracts is not None else None
        except Exception:
            pass

        return {'funnel': {'leads': leads, 'contacts': contacts, 'appointments': appts, 'applicants': applicants, 'contracts': contracts}, 'conversion_rates': conv}
    finally:
        conn.close()


@router.get('/v2/roi/event/{event_id}')
def roi_event_detail(event_id: str, unit_rsid: Optional[str] = None, allowed_orgs: Optional[list] = Depends(require_scope('BN'))):
    conn = db.connect()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM event_fact WHERE event_id = ?', (event_id,))
        ev = cur.fetchone()
        if not ev:
            raise HTTPException(status_code=404, detail='event not found')
        # attributed leads
        cur.execute('SELECT * FROM lead_journey_fact WHERE event_id = ? ORDER BY lead_created_dt ASC', (event_id,))
        leads = [dict(r) for r in cur.fetchall()]
        # flash-to-bang distribution
        cur.execute('SELECT julianday(contract_dt)-julianday(lead_created_dt) as days FROM lead_journey_fact WHERE event_id = ? AND contract_flag=1', (event_id,))
        days = [r['days'] for r in cur.fetchall() if r['days'] is not None]
        return {'event': dict(ev), 'leads': leads, 'flash_to_bang_days': days}
    finally:
        conn.close()
