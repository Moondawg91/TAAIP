from services.api.app.db import connect
from services.api.app.services.coa_engine import run_coa_generation, fetch_latest_for_unit
import json

conn = connect()
cur = conn.cursor()
# Seed mission allocation run
cur.execute("INSERT OR REPLACE INTO mission_allocation_runs (run_id, unit_rsid, mission_total, created_at) VALUES (?,?,?,datetime('now'))", ('mal_seed_demo','STN_DEMO_01', 24))
# Seed one contracted lead
cur.execute("INSERT OR REPLACE INTO fact_lead_journey (lead_id, unit_rsid, created_dt, contract_flag, source_system) VALUES (?,?,?,?,?)", ('lead_demo_1','STN_DEMO_01','2026-03-01',1,'SEED'))
# Seed fusion recommendation for S123
cur.execute("INSERT OR REPLACE INTO fusion_recommendations (fusion_run_id, unit_rsid, school_id, market_key, zip5, fusion_score, evidence_json, recommendation_type, recommendation_text, created_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))", ('fus_seed_1','STN_DEMO_01','S123','MK1','12345',0.95,json.dumps({'note':'demo'}),'SCHOOL_PUSH','Target S123 (demo target) - high priority'))
conn.commit()
# Run COA
run = run_coa_generation('STN_DEMO_01')
rows = fetch_latest_for_unit('STN_DEMO_01', limit=5)
primary = None
for r in rows:
    if r.get('coa_type','').upper() == 'PRIMARY' or (r.get('coa_title') and r.get('coa_title').upper().startswith('URGENT')):
        primary = r
        break
if not primary and rows:
    primary = rows[0]
if primary:
    ra = primary.get('recommended_actions_json') or {}
    obj = primary.get('objective_json') or (ra.get('objective') if isinstance(ra, dict) else None)
    out = {
        'coa_title': primary.get('coa_title'),
        'coa_summary': primary.get('coa_summary'),
        'recommended_actions_json': ra,
        'objective_json': obj
    }
    print(json.dumps(out, default=str))
else:
    print('NO_COA')
conn.close()
