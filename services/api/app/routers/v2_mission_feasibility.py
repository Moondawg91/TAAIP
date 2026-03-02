from fastapi import APIRouter, HTTPException, Depends, Request
from .. import db as _db
from .rbac import require_perm
from datetime import datetime
from typing import Optional
import json

router = APIRouter(prefix='/v2/mission-feasibility', tags=['mission-feasibility'])


def _now_iso():
    return datetime.utcnow().isoformat()


def _scenario_for_target(inputs, computed, target_wr_assumption=1.0, weights=None):
    # compute recruiters_required, recruiter_strength_gap, WR_gap, MSI, FS
    try:
        M = inputs.get('annual_mission_contracts') or 0
        R = inputs.get('recruiters_available_avg') or inputs.get('recruiters_assigned_avg') or 0
        market_baseline = inputs.get('market_capacity_baseline') or 0
        mbf = inputs.get('market_burden_factor') or 1.0

        recruiters_required = None
        if target_wr_assumption and target_wr_assumption > 0:
            recruiters_required = M / (target_wr_assumption * 12.0) if M else None

        wr_required = None
        if R and R > 0:
            wr_required = (M / 12.0) / float(R) if M else 0.0

        # WR_actual estimation from computed if available
        wr_actual = None
        try:
            if computed.get('expected_wr_per_recruiter') is not None:
                wr_actual = float(computed.get('expected_wr_per_recruiter'))
        except Exception:
            wr_actual = None

        # MSI
        market_capacity_estimate = market_baseline * (mbf or 1.0) if market_baseline is not None else None
        msi = None
        if market_capacity_estimate and M:
            try:
                msi = float(market_capacity_estimate) / float(M) if M else None
            except Exception:
                msi = None

        # gaps
        wr_gap = None
        if wr_actual is not None and wr_required is not None and wr_required > 0:
            wr_gap = max(0.0, min(1.0, wr_actual / float(wr_required)))

        recruiter_strength_gap = None
        if recruiters_required and R:
            recruiter_strength_gap = max(0.0, min(1.0, float(R) / float(recruiters_required)))

        # weights
        if weights is None:
            weights = {'wr': 0.45, 'msi': 0.35, 'rs': 0.20}

        # normalized components
        wr_comp = wr_gap if wr_gap is not None else 0.0
        msi_comp = max(0.0, min(1.0, msi)) if msi is not None else 0.0
        rs_comp = recruiter_strength_gap if recruiter_strength_gap is not None else 0.0

        fs = int(round(100.0 * (weights['wr'] * wr_comp + weights['msi'] * msi_comp + weights['rs'] * rs_comp)))

        return {
            'target_wr_assumption': target_wr_assumption,
            'recruiters_required': None if recruiters_required is None else round(recruiters_required,2),
            'wr_required': None if wr_required is None else round(wr_required,3),
            'wr_actual': None if wr_actual is None else round(wr_actual,3),
            'msi': None if msi is None else round(msi,3),
            'feasibility_score': fs,
            'wr_gap': None if wr_gap is None else round(wr_gap,3),
            'recruiter_strength_gap': None if recruiter_strength_gap is None else round(recruiter_strength_gap,3)
        }
    except Exception:
        return {}


@router.get('/summary')
def summary(request: Request = None, unit_rsid: str = 'USAREC', fy: Optional[int] = None, qtr_num: Optional[int] = None, rsm_month: Optional[str] = None, rollup: Optional[int] = None, compare_mode: str = 'C', user: dict = Depends(require_perm('dashboards.view'))):
    # apply scope defaults
    try:
        from .. import scope as scope_mod
        qp = {}
        if request is not None:
            qp = dict(request.query_params)
        # merge explicit args
        if unit_rsid is not None:
            qp['unit_rsid'] = unit_rsid
        if fy is not None:
            qp['fy'] = str(fy)
        if qtr_num is not None:
            qp['qtr_num'] = str(qtr_num)
        if rsm_month is not None:
            qp['rsm_month'] = rsm_month
        if rollup is not None:
            qp['rollup'] = str(rollup)
        scope = scope_mod.parse_scope_params(qp)
        unit_rsid = scope['unit_rsid']
        fy = scope['fy']
        qtr_num = scope['qtr_num']
        rsm_month = scope['rsm_month']
        rollup = scope['rollup']
    except Exception:
        # fall back to basic defaults
        try:
            if fy is None:
                fy = datetime.utcnow().year or 2026
        except Exception:
            fy = 2026

    conn = _db.connect()
    try:
        cur = conn.cursor()

        # unit display name
        unit_display = None
        try:
            cur.execute('SELECT display_name, name FROM org_unit WHERE rsid = ? OR id = ?', (unit_rsid, unit_rsid))
            r = cur.fetchone()
            if r:
                unit_display = r.get('display_name') or r.get('name')
        except Exception:
            unit_display = None

        # inputs
        mission_annual = None
        try:
            cur.execute('SELECT * FROM mission_target WHERE unit_rsid = ? AND fy = ? LIMIT 1', (unit_rsid, fy))
            row = cur.fetchone()
            if row:
                if row.get('annual_contract_mission') is not None:
                    mission_annual = int(row['annual_contract_mission'])
                elif row.get('mission_contracts') is not None:
                    mission_annual = int(row['mission_contracts'])
        except Exception:
            mission_annual = None

        recruiters_assigned_avg = None
        recruiters_available_avg = None
        try:
            # when rollup requested, resolve descendant rsids
            rsids = [unit_rsid]
            if rollup:
                try:
                    from .. import org_utils
                    rsids = org_utils.get_descendant_units(conn, unit_rsid)
                except Exception:
                    rsids = [unit_rsid]
            placeholders = ','.join('?' for _ in rsids)
            params = list(rsids)
            if rsm_month:
                cur.execute(f"SELECT AVG(recruiters_assigned) as avg_assigned FROM recruiter_strength WHERE month = ? AND org_unit_id IN ({placeholders})", [rsm_month] + params)
            else:
                cur.execute(f"SELECT AVG(recruiters_assigned) as avg_assigned FROM recruiter_strength WHERE month LIKE ? AND org_unit_id IN ({placeholders})", [f"{fy}-%"] + params)
            r = cur.fetchone()
            if r and r.get('avg_assigned') is not None:
                recruiters_assigned_avg = float(r['avg_assigned'])
        except Exception:
            recruiters_assigned_avg = None

        try:
            cur.execute('SELECT AVG(recruiters_available) as avg_available FROM recruiter_strength WHERE unit_rsid = ? AND month LIKE ?', (unit_rsid, f"{fy}-%"))
            r = cur.fetchone()
            if r and r.get('avg_available') is not None:
                recruiters_available_avg = float(r['avg_available'])
        except Exception:
            try:
                cur.execute('SELECT AVG(producers_available) as avg_producers_available FROM recruiter_strength WHERE unit_rsid = ? AND month LIKE ?', (unit_rsid, f"{fy}-%"))
                r2 = cur.fetchone()
                if r2 and r2.get('avg_producers_available') is not None:
                    recruiters_available_avg = float(r2['avg_producers_available'])
            except Exception:
                recruiters_available_avg = None

        market_capacity_baseline = None
        market_burden_factor = None
        try:
            cur.execute('SELECT * FROM market_capacity WHERE unit_rsid = ? AND fy = ? LIMIT 1', (unit_rsid, fy))
            m = cur.fetchone()
            if m:
                if m.get('baseline_contract_capacity') is not None:
                    market_capacity_baseline = int(m['baseline_contract_capacity'])
                elif m.get('market_index') is not None:
                    try:
                        market_capacity_baseline = int(m['market_index'])
                    except Exception:
                        market_capacity_baseline = None
                if m.get('market_burden_factor') is not None:
                    market_burden_factor = float(m['market_burden_factor'] or 1.0)
                else:
                    market_burden_factor = 1.0
        except Exception:
            market_capacity_baseline = None
            market_burden_factor = None

        inputs = {
            'annual_mission_contracts': mission_annual,
            'recruiters_assigned_avg': recruiters_assigned_avg,
            'recruiters_available_avg': recruiters_available_avg,
            'market_capacity_baseline': market_capacity_baseline,
            'market_burden_factor': market_burden_factor
        }

        # computations
        computed = {
            'mission_monthly': None,
            'required_wr_per_recruiter': None,
            'expected_wr_per_recruiter': None,
            'market_adjusted_expected_wr': None,
            'contract_gap_vs_market': None,
            'contract_gap_vs_capacity': None
        }

        if mission_annual is not None:
            computed['mission_monthly'] = round(float(mission_annual) / 12.0, 2)

        if computed['mission_monthly'] is not None and recruiters_available_avg and recruiters_available_avg > 0:
            computed['required_wr_per_recruiter'] = round(computed['mission_monthly'] / float(recruiters_available_avg), 2)

        if market_capacity_baseline is not None and recruiters_available_avg and recruiters_available_avg > 0:
            expected_wr = float(market_capacity_baseline) / 12.0 / float(recruiters_available_avg)
            computed['expected_wr_per_recruiter'] = round(expected_wr, 2)
            mbf = market_burden_factor or 1.0
            computed['market_adjusted_expected_wr'] = round(expected_wr / float(mbf), 2)

        if mission_annual is not None and market_capacity_baseline is not None:
            gap = int(mission_annual - market_capacity_baseline)
            computed['contract_gap_vs_market'] = gap
            computed['contract_gap_vs_capacity'] = gap

        # drivers & recommendations
        drivers = []
        recommendations = []
        reasons = []

        missing_inputs = any(v is None for v in [mission_annual, recruiters_available_avg, market_capacity_baseline, market_burden_factor])
        if missing_inputs:
            reasons.append({'code': 'DATA_MISSING', 'detail': 'One or more input elements are missing'})
            drivers.append({'type': 'DATA', 'label': 'Missing data', 'value': None})

        if market_capacity_baseline is not None and mission_annual is not None and market_capacity_baseline < mission_annual:
            reasons.append({'code': 'MARKET_CAPACITY_LOW', 'detail': f'Baseline capacity {market_capacity_baseline} < mission {mission_annual}'})
            drivers.append({'type': 'MARKET', 'label': 'Market capacity below mission', 'value': market_capacity_baseline})
            recommendations.append({'type': 'MISSION_REALLOCATE', 'text': 'Consider redistributing mission or reallocating recruiter strength.'})

        if computed.get('required_wr_per_recruiter') is not None and computed.get('market_adjusted_expected_wr') is not None:
            req = computed['required_wr_per_recruiter']
            exp = computed['market_adjusted_expected_wr']
            if exp < req:
                reasons.append({'code': 'RECRUITER_CAPACITY_LOW', 'detail': f'Required WR {req} exceeds expected {exp}'})
                drivers.append({'type': 'CAPACITY', 'label': 'Recruiter capacity insufficient', 'value': round(req - exp, 2)})
                recommendations.append({'type': 'TARGETING_SHIFT', 'text': 'Shift effort to higher-yield CBSA segments; reduce low-yield activities.'})

        # overall status
        overall = 'AMBER'
        try:
            ok_market = (market_capacity_baseline is not None and mission_annual is not None and market_capacity_baseline >= mission_annual)
            ok_wr = (computed.get('market_adjusted_expected_wr') is not None and computed.get('required_wr_per_recruiter') is not None and computed['market_adjusted_expected_wr'] >= computed['required_wr_per_recruiter'] * 0.95)
            if not missing_inputs and ok_market and ok_wr:
                overall = 'GREEN'
            else:
                # within 10% gap => AMBER
                if not missing_inputs and mission_annual and market_capacity_baseline:
                    ratio = float(market_capacity_baseline) / float(mission_annual) if mission_annual else 0
                    if ratio >= 0.9:
                        overall = 'AMBER'
                    else:
                        overall = 'RED'
                else:
                    overall = 'AMBER'
        except Exception:
            overall = 'AMBER'

        out = {
            'unit_rsid': unit_rsid,
            'unit_display_name': unit_display,
            'fy': fy,
            'applied_scope': {
                'unit_rsid': unit_rsid,
                'fy': fy,
                'qtr_num': qtr_num,
                'rsm_month': rsm_month,
                'rollup': rollup
            },
            'inputs': inputs,
            'computed': computed,
            # missionProduction: totals + bySegment (compatibility shape)
            'missionProduction': {
                'totals': {},
                'bySegment': []
            },
            # depLoss: byBucket
            'depLoss': {
                'byBucket': []
            },
            'status': {
                'overall': overall,
                'reasons': reasons
            },
            'drivers': drivers,
            'recommendations': recommendations,
            'explain': {
                'formula_notes': [
                    'required_wr = (annual_mission_contracts/12) / recruiters_available_avg',
                    'expected_wr = (market_capacity_baseline/12) / recruiters_available_avg',
                    'market_adjusted_expected_wr = expected_wr / market_burden_factor'
                ]
            },
            'computed_at': _now_iso()
        }

        # Populate missionProduction and depLoss from fact tables when present
        try:
            # resolve rsids for rollup if requested
            rsids = [unit_rsid]
            if rollup:
                try:
                    from .. import org_utils
                    rsids = org_utils.get_descendant_units(conn, unit_rsid)
                except Exception:
                    rsids = [unit_rsid]
            placeholders = ','.join('?' for _ in rsids)

            # mission totals for components and metrics
            comps = ['RA', 'AR']
            metrics = ['MISSION', 'PROD', 'NET_CONTRACTS']
            totals = {c: {m: 0 for m in metrics} for c in comps}
            cur.execute(f"SELECT component, metric, SUM(value) as v FROM fact_mission_production WHERE rsid IN ({placeholders}) GROUP BY component, metric", tuple(rsids))
            for r in cur.fetchall():
                try:
                    comp = r.get('component') if isinstance(r, dict) else r[0]
                    metric = r.get('metric') if isinstance(r, dict) else r[1]
                    val = r.get('v') if isinstance(r, dict) else r[2]
                    if comp in totals and metric in totals[comp]:
                        totals[comp][metric] = float(val or 0)
                except Exception:
                    continue

            # bySegment
            byseg = []
            cur.execute(f"SELECT component, segment, metric, SUM(value) as v FROM fact_mission_production WHERE rsid IN ({placeholders}) GROUP BY component, segment, metric", tuple(rsids))
            seg_rows = cur.fetchall()
            seg_map = {}
            for r in seg_rows:
                try:
                    comp = r.get('component') if isinstance(r, dict) else r[0]
                    seg = r.get('segment') if isinstance(r, dict) else r[1]
                    metric = r.get('metric') if isinstance(r, dict) else r[2]
                    val = r.get('v') if isinstance(r, dict) else r[3]
                    key = (comp, seg)
                    if key not in seg_map:
                        seg_map[key] = {m: 0 for m in metrics}
                    if metric in seg_map[key]:
                        seg_map[key][metric] = float(val or 0)
                except Exception:
                    continue
            for (comp, seg), vals in seg_map.items():
                rec = {'component': comp, 'segment': seg}
                rec.update(vals)
                byseg.append(rec)

            # depLoss by bucket
            dep_buckets = []
            try:
                cur.execute(f"SELECT bucket, SUM(dep_losses) as losses FROM fact_dep_loss WHERE rsid IN ({placeholders}) GROUP BY bucket ORDER BY bucket", tuple(rsids))
                for r in cur.fetchall():
                    try:
                        bucket = r.get('bucket') if isinstance(r, dict) else r[0]
                        losses = r.get('losses') if isinstance(r, dict) else r[1]
                        dep_buckets.append({'bucket': bucket, 'losses': int(losses or 0)})
                    except Exception:
                        continue
            except Exception:
                dep_buckets = []

            # attach to out
            out['missionProduction']['totals'] = totals
            out['missionProduction']['bySegment'] = byseg
            out['depLoss']['byBucket'] = dep_buckets or [{'bucket': '0-9_Days', 'losses': 0}, {'bucket': '10-19_Days', 'losses': 0}]
        except Exception:
            # leave defaults (zeros)
            try:
                out['missionProduction']['totals'] = { 'RA': {'MISSION': 0, 'PROD': 0, 'NET_CONTRACTS': 0}, 'AR': {'MISSION': 0, 'PROD': 0, 'NET_CONTRACTS': 0} }
                out['missionProduction']['bySegment'] = [
                    {'component':'RA','segment':'GA','MISSION':0,'PROD':0,'NET_CONTRACTS':0},
                    {'component':'RA','segment':'SA','MISSION':0,'PROD':0,'NET_CONTRACTS':0},
                    {'component':'RA','segment':'OTH','MISSION':0,'PROD':0,'NET_CONTRACTS':0},
                    {'component':'RA','segment':'PS','MISSION':0,'PROD':0,'NET_CONTRACTS':0}
                ]
                out['depLoss']['byBucket'] = [{'bucket':'0-9_Days','losses':0},{'bucket':'10-19_Days','losses':0}]
            except Exception:
                pass

            return out
    finally:
        try:
            conn.close()
        except Exception:
            pass
@router.get('/scenarios')
def scenarios(request: Request = None, unit_rsid: str = 'USAREC', fy: Optional[int] = None, qtr_num: Optional[int] = None, rsm_month: Optional[str] = None, rollup: Optional[int] = None, user: dict = Depends(require_perm('dashboards.view'))):
    # produce scenario A (1.0) and B (0.7)
    # pass through request/query params to summary so applied_scope is consistent
    summary_out = summary(request=request, unit_rsid=unit_rsid, fy=fy, qtr_num=qtr_num, rsm_month=rsm_month, rollup=rollup, user=user)
    inputs = summary_out.get('inputs', {})
    computed = summary_out.get('computed', {})
    sc1 = _scenario_for_target(inputs, computed, target_wr_assumption=1.0)
    sc2 = _scenario_for_target(inputs, computed, target_wr_assumption=0.7)
    recommended = None
    try:
        # recommend higher feasibility score
        if sc1.get('feasibility_score',0) >= sc2.get('feasibility_score',0):
            recommended = {'recommended_wr': sc1['target_wr_assumption'], 'reason': 'Higher feasibility score'}
        else:
            recommended = {'recommended_wr': sc2['target_wr_assumption'], 'reason': 'Higher feasibility score'}
    except Exception:
        recommended = None
    return {'unit_rsid': unit_rsid, 'fy': summary_out.get('fy'), 'applied_scope': summary_out.get('applied_scope'), 'scenario_A': sc1, 'scenario_B': sc2, 'recommended': recommended}


@router.get('/drivers')
def drivers(unit_rsid: str = 'USAREC', fy: Optional[int] = None, user: dict = Depends(require_perm('dashboards.view'))):
    s = summary(unit_rsid=unit_rsid, fy=fy, user=user)
    return {'unit_rsid': unit_rsid, 'fy': s.get('fy'), 'drivers': s.get('drivers', []), 'reasons': s.get('status', {}).get('reasons', [])}


@router.post('/narrative')
def narrative(payload: dict, user: dict = Depends(require_perm('dashboards.view'))):
    """Generate a short structured narrative for the provided summary/scenario payload and persist it."""
    try:
        from ..ai import feasibility_narrative as _fn
    except Exception:
        _fn = None
    summary_json = payload.get('summary') or {}
    drivers_list = payload.get('drivers') or []
    gaps = payload.get('gaps') or []
    unit = summary_json.get('unit_rsid') or payload.get('unit_rsid') or 'USAREC'
    fy = summary_json.get('fy') or payload.get('fy') or None
    narrative_text = None
    structured = None
    if _fn:
        structured = _fn.generate(summary_json, drivers_list, gaps)
        narrative_text = structured.get('narrative')
    # persist
    conn = _db.connect()
    try:
        cur = conn.cursor()
        now = _now_iso()
        cur.execute('INSERT INTO mission_feasibility_narrative(unit_rsid, fy, payload, created_at) VALUES (?,?,?,?)', (unit, fy, json.dumps(structured or {'text': narrative_text}), now))
        conn.commit()
    finally:
        try: conn.close()
        except Exception: pass
    return {'status': 'ok', 'narrative': structured}


@router.post('/inputs')
def upsert_inputs(payload: dict, user: dict = Depends(require_perm('dashboards.edit'))):
    """Upsert mission inputs: mission_target, recruiter_strength rows, market_capacity."""
    conn = _db.connect()
    try:
        cur = conn.cursor()
        unit_rsid = payload.get('unit_rsid') or 'USAREC'
        fy = payload.get('fy') or (datetime.utcnow().year or 2026)
        now = datetime.utcnow().isoformat()

        # mission_target
        ann = payload.get('annual_mission_contracts')
        if ann is not None:
            try:
                cur.execute('INSERT OR REPLACE INTO mission_target(unit_rsid, fy, annual_contract_mission, created_at, updated_at) VALUES(?,?,?,?,?)', (unit_rsid, fy, int(ann), now, now))
            except Exception:
                # fallback for legacy schema (mission_contracts)
                try:
                    cur.execute('INSERT OR IGNORE INTO mission_target(unit_rsid, fy, mission_contracts, created_at) VALUES(?,?,?,?)', (unit_rsid, fy, int(ann), now))
                    cur.execute('UPDATE mission_target SET mission_contracts = ?, updated_at = ? WHERE unit_rsid = ? AND fy = ?', (int(ann), now, unit_rsid, fy))
                except Exception:
                    pass

        # recruiter_strength list
        rs_list = payload.get('recruiter_strength') or []
        try:
            for item in rs_list:
                m = item.get('month')
                assigned = int(item.get('assigned') or item.get('recruiters_assigned') or 0)
                available = int(item.get('available') or item.get('recruiters_available') or 0)
                if m:
                    cur.execute('INSERT OR REPLACE INTO recruiter_strength(unit_rsid, month, recruiters_assigned, recruiters_available, created_at, updated_at) VALUES(?,?,?,?,?,?)', (unit_rsid, m, assigned, available, now, now))
        except Exception:
            # fallback to legacy column name producers_available
            try:
                for item in rs_list:
                    m = item.get('month')
                    assigned = int(item.get('assigned') or item.get('recruiters_assigned') or 0)
                    available = int(item.get('available') or item.get('recruiters_available') or 0)
                    if m:
                        cur.execute('INSERT OR REPLACE INTO recruiter_strength(unit_rsid, month, recruiters_assigned, producers_available, created_at, updated_at) VALUES(?,?,?,?,?,?)', (unit_rsid, m, assigned, available, now, now))
            except Exception:
                pass

        # market_capacity
        mcap = payload.get('market_capacity_baseline') or payload.get('market_capacity')
        mbf = payload.get('market_burden_factor')
        if mcap is not None:
            try:
                cur.execute('INSERT OR REPLACE INTO market_capacity(unit_rsid, fy, baseline_contract_capacity, market_burden_factor, created_at, updated_at) VALUES(?,?,?,?,?,?)', (unit_rsid, fy, int(mcap), float(mbf or 1.0), now, now))
            except Exception:
                # fallback for legacy market_capacity schema: write into market_index and snapshot_month
                try:
                    snapshot = f"{fy}-01"
                    cur.execute('INSERT OR IGNORE INTO market_capacity(unit_rsid, snapshot_month, market_index, created_at) VALUES(?,?,?,?)', (unit_rsid, snapshot, float(mcap), now))
                    cur.execute('UPDATE market_capacity SET market_index = ?, created_at = ? WHERE unit_rsid = ? AND snapshot_month = ?', (float(mcap), now, unit_rsid, snapshot))
                except Exception:
                    pass

        conn.commit()
        return {'status': 'ok', 'unit_rsid': unit_rsid, 'fy': fy}
    finally:
        try:
            conn.close()
        except Exception:
            pass
