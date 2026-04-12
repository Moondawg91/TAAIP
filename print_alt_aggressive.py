from services.api.app.services.coa_engine import run_coa_generation, fetch_latest_for_unit
import json

if __name__ == '__main__':
    run_coa_generation('STN_DEMO_01')
    rows = fetch_latest_for_unit('STN_DEMO_01', limit=10)
    alt = None
    agg = None
    for r in rows:
        t = r.get('coa_type','').upper()
        if t == 'ALTERNATE' and not alt:
            alt = r
        if t == 'AGGRESSIVE' and not agg:
            agg = r
    def pick_fields(r):
        if not r:
            return None
        return {
            'coa_title': r.get('coa_title'),
            'coa_summary': r.get('coa_summary'),
            'recommended_actions_json': r.get('recommended_actions_json'),
            'objective_json': r.get('objective_json')
        }
    print(json.dumps({'alternate': pick_fields(alt), 'aggressive': pick_fields(agg)}, default=str))
