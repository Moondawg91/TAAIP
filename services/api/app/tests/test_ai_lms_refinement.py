import json

from services.api.app.services import ai_lms


def _make_evidence(school_enrollment=None, avg_share=None, mission_total=None, confidence_score=None):
    ev = {}
    if school_enrollment is not None:
        ev['school'] = {'enrollment': school_enrollment, 'priority_score': 0.28, 'confidence_score': confidence_score or 0.66, 'components': {'historical_production': 0}}
    if avg_share is not None:
        ev['market'] = {'avg_share': avg_share, 'examples': [{'zip5': '94105', 'rsid': 'STN1'}]}
    if mission_total is not None:
        ev['mission'] = {'mission_total': mission_total}
    return json.dumps(ev)


def test_structured_explanation_shape():
    rec = {
        'recommendation_text': 'Shift targeting to RS2',
        'recommendation_type': 'shift_targeting',
        'fusion_score': 0.17,
        'evidence_json': _make_evidence(school_enrollment=150, avg_share=0.35, mission_total=7)
    }
    ann = ai_lms.generate_explanation_from_recommendation(rec)
    assert 'explanation' in ann
    assert 'explanation_struct' in ann
    s = ann['explanation_struct']
    assert isinstance(s, dict)
    for key in ('what', 'why', 'evidence', 'risk', 'expected_effect', 'confidence', 'assumptions', 'data_quality'):
        assert key in s, f'missing {key} in explanation_struct'


def test_doctrine_rule_mapping():
    # school/targeting -> UR 27-4, UR 601-210
    rec_school = {'recommendation_type': 'shift_targeting'}
    a1 = ai_lms.generate_explanation_from_recommendation(rec_school)
    refs = json.loads(a1['doctrine_refs_json'])
    assert any(r['ref'] == 'UR 27-4' for r in refs)
    assert any(r['ref'] == 'UR 601-210' for r in refs)

    # mission/allocation -> UR 350-1, UR 601-106
    rec_mission = {'recommendation_type': 'mission_allocation'}
    a2 = ai_lms.generate_explanation_from_recommendation(rec_mission)
    refs2 = json.loads(a2['doctrine_refs_json'])
    assert any(r['ref'] == 'UR 350-1' for r in refs2)
    assert any(r['ref'] == 'UR 601-106' for r in refs2)

    # market/analysis -> UM 3-0, UTP 3-10.2
    rec_market = {'recommendation_type': 'market_analysis'}
    a3 = ai_lms.generate_explanation_from_recommendation(rec_market)
    refs3 = json.loads(a3['doctrine_refs_json'])
    assert any(r['ref'] == 'UM 3-0' for r in refs3)
    assert any(r['ref'] == 'UTP 3-10.2' for r in refs3)

    # fallback -> UM 3-0
    rec_fallback = {'recommendation_type': 'something_unknown'}
    a4 = ai_lms.generate_explanation_from_recommendation(rec_fallback)
    refs4 = json.loads(a4['doctrine_refs_json'])
    assert any(r['ref'] == 'UM 3-0' for r in refs4)


def test_confidence_bounds_and_drop():
    # high-ish fusion score
    rec_high = {'fusion_score': 0.5, 'recommendation_type': 'shift_targeting'}
    a_high = ai_lms.generate_explanation_from_recommendation(rec_high)
    ch = a_high['explanation_struct']['confidence']
    assert 0.15 <= ch <= 0.95

    # low fusion score should yield lower confidence
    rec_low = {'fusion_score': 0.05, 'recommendation_type': 'shift_targeting'}
    a_low = ai_lms.generate_explanation_from_recommendation(rec_low)
    cl = a_low['explanation_struct']['confidence']
    assert 0.15 <= cl <= 0.95
    assert cl < ch
