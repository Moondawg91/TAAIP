import json

from services.api.app.services import ai_lms


def test_confidence_high_alignment_high_quality():
    rec = {
        'recommendation_text': 'Full evidence target',
        'recommendation_type': 'school-target',
        'fusion_score': 0.6,
        'evidence_json': json.dumps({
            'market': {'median_age': 19, 'avg_share': 0.3, 'infrastructure_score': 0.8},
            'school': {'enrollment': 400, 'components': {'historical_production': 12}, 'confidence_score': 0.9},
            'mission': {'mission_total': 4}
        })
    }
    ann = ai_lms.generate_explanation_from_recommendation(rec)
    cd = ann['explanation_struct'].get('confidence_detail')
    assert cd is not None
    assert cd['band'] in ('high', 'medium-high', 'moderate')
    # allow slight variance in numeric mapping; require reasonably high mapped confidence
    assert ann['explanation_struct']['confidence'] >= 0.55


def test_confidence_high_alignment_low_quality():
    rec = {
        'recommendation_type': 'school-target',
        'fusion_score': 0.6,
        'evidence_json': json.dumps({
            'market': {'median_age': 19},
            # missing many school/mission fields -> low data quality
            'school': {}
        })
    }
    ann = ai_lms.generate_explanation_from_recommendation(rec)
    cd = ann['explanation_struct'].get('confidence_detail')
    assert cd is not None
    # high doctrine align but low data quality should not be 'high'
    assert cd['band'] != 'high'


def test_confidence_conflict_penalty():
    rec = {
        'recommendation_type': 'school-target',
        'evidence_json': json.dumps({
            'school': {'enrollment': 300, 'components': {'historical_production': 0}, 'confidence_score': 0.8},
            'market': {'median_age': 22}
        })
    }
    ann = ai_lms.generate_explanation_from_recommendation(rec)
    cd = ann['explanation_struct'].get('confidence_detail')
    assert 'flag' in json.dumps(cd['factors_negative']).lower() or len(cd['factors_negative']) > 0


def test_confidence_no_match_weak_evidence_low():
    rec = {'recommendation_type': 'unknown', 'evidence_json': '{}'}
    ann = ai_lms.generate_explanation_from_recommendation(rec)
    cd = ann['explanation_struct'].get('confidence_detail')
    assert cd is not None
    assert cd['band'] == 'low'
