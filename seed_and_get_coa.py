from services.api.app.services.coa_engine import run_coa_generation, fetch_latest_for_unit
import json

if __name__ == '__main__':
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
        obj = ra.get('objective') if isinstance(ra, dict) else None
        out = {
            'coa_title': primary.get('coa_title'),
            'coa_summary': primary.get('coa_summary'),
            'recommended_actions_json': ra,
            'objective_json': obj
        }
        print(json.dumps(out, default=str))
    else:
        print('NO_COA')
