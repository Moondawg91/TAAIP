from services.api.app.services.doctrine import ENGINE


def test_political_low_risk_triggers():
    ctx = {'market': {'political_risk': 0.2}}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('PMESII_POLITICAL_LOW_RISK_01') for r in res['triggered_rules'])


def test_social_unrest_penalty():
    ctx = {'market': {'social_unrest': True}}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('PMESII_SOCIAL_UNREST_01') for r in res['triggered_rules'])


def test_ascope_information_and_structures():
    ctx = {'market': {'media_influence': 0.8, 'community_centers': 2}, 'school': {'facilities': True}}
    res = ENGINE.evaluate(ctx)
    ids = [r['id'] for r in res['triggered_rules']]
    assert any('ASCOPE_INFORMATION_ENV_01' in i for i in ids)
    assert any('ASCOPE_STRUCTURES_COMMUNITY_01' in i for i in ids)


def test_population_transient_flagged():
    ctx = {'market': {'population_transient_pct': 0.4}}
    res = ENGINE.evaluate(ctx)
    assert any(r['id'].startswith('PMESII_POP_MOVEMENT_01') for r in res['triggered_rules'])
