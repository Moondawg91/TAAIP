from fastapi import APIRouter, Query
from ..db import connect
from ..utils.rollup_utils import build_empty_rollup_contract
import datetime

router = APIRouter()


def _now_iso():
    return datetime.datetime.utcnow().isoformat() + 'Z'


@router.get('/school-program/readiness')
def school_program_readiness():
    conn = connect()
    cur = conn.cursor()
    datasets = []
    if 'school_program_fact' in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        try:
            cur.execute('SELECT COUNT(1) FROM school_program_fact')
            rc = cur.fetchone()[0] or 0
        except Exception:
            rc = 0
        datasets.append({'dataset_key':'school_program_fact','table':'school_program_fact','display_name':'School Program Fact','loaded': bool(rc>0),'row_count': rc})
    else:
        datasets.append({'dataset_key':'school_program_fact','table':'school_program_fact','display_name':'School Program Fact','loaded': False,'row_count':0})
    blocking = []
    for d in datasets:
        if not d['loaded']:
            blocking.append(d['dataset_key'])
    status = 'ok' if len(blocking)==0 else 'partial'
    return {'status': status, 'datasets': datasets, 'blocking': blocking}


@router.get('/school-program/summary')
def school_program_summary(fy: str = Query(None), qtr: str = Query(None), rsid_prefix: str = Query(None)):
    conn = connect()
    cur = conn.cursor()
    contract = build_empty_rollup_contract({}, kpi_keys=['population_total','available_total','attempted_total','attempted_rate','contacted_total','contacted_rate'], breakdown_keys=['by_bde','by_bn','by_co'], trend_keys=[])
    contract['data_as_of'] = _now_iso()

    if not any([r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='school_program_fact'").fetchall()]):
        contract['missing_data'] = ['school_program_fact']
        contract['status'] = 'partial'
        return contract

    try:
        q = "SELECT SUM(COALESCE(population,0)), SUM(COALESCE(available,0)), SUM(COALESCE(attempted_students,0)), SUM(COALESCE(contacted_students,0)) FROM school_program_fact WHERE 1=1"
        if fy:
            q += f" AND fy='{fy}'"
        if rsid_prefix:
            q += f" AND rsid_prefix='{rsid_prefix}'"
        cur.execute(q)
        row = cur.fetchone()
        pop = row[0] or 0
        avail = row[1] or 0
        attempted = row[2] or 0
        contacted = row[3] or 0
        attempted_rate = (attempted / pop) if pop else 0
        contacted_rate = (contacted / pop) if pop else 0
        contract['kpis'] = {
            'population_total': pop,
            'available_total': avail,
            'attempted_total': attempted,
            'attempted_rate': round(attempted_rate,4),
            'contacted_total': contacted,
            'contacted_rate': round(contacted_rate,4)
        }
        # breakdowns
        cur.execute("SELECT bde, SUM(COALESCE(population,0)), SUM(COALESCE(contacted_students,0)) FROM school_program_fact GROUP BY bde")
        contract['breakdowns'] = {
            'by_bde': [{'bde': r[0], 'population': r[1], 'contacted': r[2]} for r in cur.fetchall()]
        }
    except Exception:
        contract['kpis'] = {}
        contract['breakdowns'] = {'by_bde':[]}
        contract['missing_data'] = ['school_program_fact']
        contract['status'] = 'partial'
        return contract

    contract['missing_data'] = []
    contract['status'] = 'ok'
    return contract
