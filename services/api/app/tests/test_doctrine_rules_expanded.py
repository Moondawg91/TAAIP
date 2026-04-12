from services.api.app.services.doctrine import ENGINE
from services.api.app.services import ai_lms
import json


def test_single_rule_trigger_age_density():
    ctx = {'market': {'age_eligible_pct': 0.25}}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('UR_601_210_AGE_DENSITY_01') for r in res['triggered_rules'])
    assert 'UR 601-210' in res['doctrine_refs']


def test_multiple_rule_triggers_market_and_school():
    ctx = {
        'market': {'median_age': 19, 'avg_share': 0.3, 'infrastructure_score': 0.8},
        'school': {'enrollment': 350, 'components': {'historical_production': 10}}
    }
    res = ENGINE.evaluate(ctx)
    ids = [r['id'] for r in res['triggered_rules']]
    # expect age-density or median-age targeting, market share, infra, and outreach
    assert any('UR_601_210' in i for i in ids) or any('UM_3_0_MARKET_01' in i for i in ids)
    assert any('UM_3_30_INFRA_01' in i for i in ids)
    assert any('UR_27_4_OUTREACH_01' in i for i in ids)


def test_conflicting_conditions_flagged():
    ctx = {'school': {'enrollment': 300, 'components': {'historical_production': 0}}}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('CONFLICT_HIGH_ENROLL_LOW_PROD_01') for r in res['triggered_rules'])


def test_no_match_fallback_integration_with_ai_lms():
    # Engine returns no refs for empty context; ai_lms should fallback to UM 3-0
    res = ENGINE.evaluate({})
    assert res['doctrine_refs'] == []
    # ai_lms layer provides fallback to UM 3-0
    ann = ai_lms.generate_explanation_from_recommendation({'recommendation_type': 'unknown'})
    refs = json.loads(ann['doctrine_refs_json'])
    assert any(r['ref'] == 'UM 3-0' for r in refs)
