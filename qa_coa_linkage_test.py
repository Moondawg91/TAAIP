from services.api.app.routers.v2_coa_compare import coa_compare
from services.api.app.services.coa_engine import fetch_latest_for_unit
from services.api.app.services.ai_lms import persist_user_decision, persist_outcome, fetch_decision_history, compute_decision_summary
from services.api.app.db import connect
import json
import pytest

unit = 'STN_DEMO_01'

# 1. fetch compare payload
payload = coa_compare(unit_rsid=unit)
coas = payload.get('coas', [])
if not coas:
    print('NO_COAS')
    pytest.skip('No COAs returned by coa_compare; skipping QA linkage test (environment-dependent)', allow_module_level=True)

# pick first COA
coa = coas[0]
rec_table = coa.get('recommendation_table') or 'coa_recommendations'
rec_id = coa.get('recommendation_id') or coa.get('id')
print('CHOSE_COA', rec_table, rec_id)

# 2. persist decision
conn = connect()
did = persist_user_decision(conn, rec_table, int(rec_id), 'select', json.dumps({'unit_rsid': unit, 'coa_type': coa.get('type'), 'coa_title': coa.get('title')}), 'qa_tester')
print('DECISION_ID', did)

# 3. persist outcome linked to that decision
out_val = json.dumps({'contracts_achieved': 2, 'engagements': 3, 'notes': 'QA test'})
oid = persist_outcome(conn, rec_table, int(rec_id), int(did), 'decision_outcome', out_val, None, 'QA')
print('OUTCOME_ID', oid)

# 4. fetch decision history and summary
hist = fetch_decision_history(conn, unit_rsid=unit, limit=20)
summary = compute_decision_summary(conn, unit_rsid=unit)

# find our decision in history
found = None
for h in hist:
    if h.get('id') == did:
        found = h
        break

print('\nHISTORY_FOUND', bool(found))
if found:
    print('history.recommendation_table', found.get('recommendation_table'), 'recommendation_id', found.get('recommendation_id'))
    print('history.outcome_present', bool(found.get('outcome')))
    print('history.outcome_parsed', found.get('outcome') and found.get('outcome').get('outcome_parsed'))

print('\nSUMMARY_KEYS', list(summary.keys()))
print('decision_count_by_type', summary.get('decision_count_by_type'))
print('success_rate_by_type', summary.get('success_rate_by_type'))
print('avg_contracts_by_type', summary.get('avg_contracts_by_type'))

conn.close()
