from fastapi import APIRouter, HTTPException, Depends
from .. import db as _db
from .rbac import require_perm
from datetime import datetime
from typing import Optional

router = APIRouter(prefix='/v2/mission-feasibility', tags=['mission-feasibility'])


def _now_iso():
    return datetime.utcnow().isoformat()


@router.get('/summary')
def summary(unit_rsid: str = 'USAREC', fy: Optional[int] = None, compare_mode: str = 'C', user: dict = Depends(require_perm('dashboards.view'))):
    # default FY: current year, fallback 2026
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
            cur.execute('SELECT AVG(recruiters_assigned) as avg_assigned FROM recruiter_strength WHERE unit_rsid = ? AND month LIKE ?', (unit_rsid, f"{fy}-%"))
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
            'inputs': inputs,
            'computed': computed,
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

        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass


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
