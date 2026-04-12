from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from services.api.app.db import connect
from services.api.app.services import lead_line as lead_line_mod

router = APIRouter()


def _fetch_recruiters(conn, unit_scope: Optional[str] = None):
    cur = conn.cursor()
    if unit_scope == 'recruiter':
        cur.execute('SELECT recruiter_id, unit_rsid FROM recruiters')
        rows = cur.fetchall()
        return [{'recruiter_id': r['recruiter_id'], 'unit_rsid': r['unit_rsid']} for r in rows]
    # default: return stations/companies/battalions as unit-level keys
    # We'll support rollups via unit_rsid grouping in fact_lead_journey
    return []


@router.get('/v2/mission/lead-line')
def get_lead_line(scope: Optional[str] = Query(None, description='Scope: recruiter|station|company|battalion'), unit_rsid: Optional[str] = Query(None, description='Optional unit rsid to filter')):
    """Return lead-line pacing status.

    - scope: recruiter|station|company|battalion
    - unit_rsid: optional filter for a specific unit
    """
    conn = connect()
    try:
        cur = conn.cursor()
        # Determine rollup key and annual mission by scope
        results = []
        # If recruiter scope, list individual recruiters and compute per-recruiter stats
        if scope == 'recruiter':
            # assume fact_lead_journey.recruiter_id exists
            if unit_rsid:
                cur.execute('SELECT recruiter_id, COUNT(*) as actual FROM fact_lead_journey WHERE recruiter_id=? AND contract_flag=1 AND created_dt>=?', (unit_rsid, f"{__import__('datetime').date.today().year}-01-01"))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail='No data')
                # fetch annual mission for recruiter from mission_allocation_runs if present (fallback 0)
                cur.execute('SELECT mission_total FROM mission_allocation_runs WHERE unit_rsid=? ORDER BY created_at DESC LIMIT 1', (None,))
                mrow = cur.fetchone()
                annual = int(mrow['mission_total']) if mrow and mrow.get('mission_total') is not None else 0
                ll = lead_line_mod.calculate_lead_line(int(row['actual'] or 0), annual)
                return {'recruiter_id': row['recruiter_id'], 'annual_mission': annual, 'actual_ytd': ll['actual_ytd'], 'expected_ytd': ll['expected_ytd'], 'variance': ll['variance'], 'status': ll['status']}
            # otherwise aggregate by recruiter
            cur.execute('SELECT recruiter_id, COUNT(*) as actual FROM fact_lead_journey WHERE contract_flag=1 AND created_dt>=? GROUP BY recruiter_id', (f"{__import__('datetime').date.today().year}-01-01",))
            rows = cur.fetchall()
            for r in rows:
                recruiter_id = r['recruiter_id']
                actual = int(r['actual'] or 0)
                # fetch annual mission for recruiter's unit if available
                cur.execute('SELECT mission_total FROM mission_allocation_runs WHERE unit_rsid IN (SELECT unit_rsid FROM recruiters WHERE recruiter_id=? ) ORDER BY created_at DESC LIMIT 1', (recruiter_id,))
                mrow = cur.fetchone()
                annual = int(mrow['mission_total']) if mrow and mrow.get('mission_total') is not None else 0
                ll = lead_line_mod.calculate_lead_line(actual, annual)
                results.append({'recruiter_id': recruiter_id, 'annual_mission': annual, 'actual_ytd': ll['actual_ytd'], 'expected_ytd': ll['expected_ytd'], 'variance': ll['variance'], 'status': ll['status']})
            return results

        # For station/company/battalion rollups, group by unit_rsid on fact_lead_journey
        # map scope -> prefix length or grouping field; here we assume unit_rsid contains the unit level
        group_field = 'unit_rsid'
        cur.execute(f"SELECT {group_field} as unit, COUNT(*) as actual FROM fact_lead_journey WHERE contract_flag=1 AND created_dt>=? GROUP BY {group_field}", (f"{__import__('datetime').date.today().year}-01-01",))
        rows = cur.fetchall()
        for r in rows:
            unit = r['unit']
            if unit is None:
                continue
            actual = int(r['actual'] or 0)
            # fetch annual mission for unit
            cur.execute('SELECT mission_total FROM mission_allocation_runs WHERE unit_rsid=? ORDER BY created_at DESC LIMIT 1', (unit,))
            mrow = cur.fetchone()
            annual = int(mrow['mission_total']) if mrow and mrow.get('mission_total') is not None else 0
            ll = lead_line_mod.calculate_lead_line(actual, annual)
            results.append({'unit_rsid': unit, 'annual_mission': annual, 'actual_ytd': ll['actual_ytd'], 'expected_ytd': ll['expected_ytd'], 'variance': ll['variance'], 'status': ll['status']})
        return results
    finally:
        try:
            conn.close()
        except Exception:
            pass
