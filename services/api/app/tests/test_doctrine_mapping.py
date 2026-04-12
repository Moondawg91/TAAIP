from services.api.app.services.doctrine import ENGINE
from services.api.app.services import ai_lms


def test_doctrine_engine_triggers_targeting_rule():
    ctx = {'market': {'median_age': 20, 'avg_share': 0.1}, 'school': {}, 'mission': {}, 'data_quality': 'medium'}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('UR_601_210') for r in res['triggered_rules'])
    assert 'UR 601-210' in res['doctrine_refs']


def test_doctrine_engine_mission_capacity():
    ctx = {'market': {}, 'school': {}, 'mission': {'mission_total': 5}, 'data_quality': 'medium'}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('UR_601_106') for r in res['triggered_rules'])
    assert 'UR 601-106' in res['doctrine_refs']


def test_ai_lms_includes_doctrine_struct():
    rec = {
        'recommendation_text': 'Increase HS engagement',
        'fusion_score': 0.5,
        'recommendation_type': 'school-target',
        'evidence_json': '{"school": {"enrollment": 300, "components": {"historical_production": 5}}, "market": {"median_age": 19}}'
    }
    ann = ai_lms.generate_explanation_from_recommendation(rec)
    assert 'explanation_struct' in ann
    s = ann['explanation_struct']
    assert 'doctrine' in s
    assert isinstance(s['doctrine'].get('triggered_rules'), list)
    assert s['doctrine'].get('rule_alignment_score') >= 0.0
