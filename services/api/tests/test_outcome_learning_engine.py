from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.services import outcome_learning_engine


def _session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_outcome_learning_engine_evaluates_and_suggests_confidence_bounds():
    db = _session()
    try:
        outcome_learning_engine.record_outcome(
            db,
            {
                "recommendation_id": "rec-001",
                "source_engine": "targeting_engine",
                "scope_type": "USAREC",
                "scope_value": "USAREC",
                "recommendation_kind": "zip_shift",
                "target_object": "zip:12345",
                "expected_kpi": {"contracts": 10},
                "actual_kpi": {"contracts": 13},
                "observed_state": "on_track",
                "pattern_type": "zip_focus",
                "pattern_value": "12345",
            },
        )
        outcome_learning_engine.record_outcome(
            db,
            {
                "recommendation_id": "rec-002",
                "source_engine": "targeting_engine",
                "scope_type": "USAREC",
                "scope_value": "USAREC",
                "recommendation_kind": "zip_shift",
                "target_object": "zip:54321",
                "expected_kpi": {"contracts": 10},
                "actual_kpi": {"contracts": 6},
                "observed_state": "on_track",
                "pattern_type": "zip_focus",
                "pattern_value": "54321",
            },
        )

        payload = outcome_learning_engine.evaluate_outcomes(db, "USAREC", "USAREC")
        assert payload["status"] == "ok"
        engine = payload["outcome_learning_engine"]
        assert engine["summary"]["recommendations_evaluated"] == 2
        assert len(engine["outcome_evaluations"]) == 2

        first = engine["outcome_evaluations"][0]
        assert first["confidence_adjustment_suggestion"]["direction"] in {"increase", "decrease", "hold"}
        assert first["confidence_adjustment_suggestion"]["magnitude"] in {"minor", "moderate", "significant"}

        assert all(item.get("trace_id") for item in engine["pattern_performance"])
    finally:
        db.close()


def test_outcome_learning_engine_handles_insufficient_data():
    db = _session()
    try:
        outcome_learning_engine.record_outcome(
            db,
            {
                "recommendation_id": "rec-insufficient",
                "source_engine": "roi_engine",
                "scope_type": "USAREC",
                "scope_value": "USAREC",
                "expected_kpi": {},
                "actual_kpi": {},
            },
        )
        payload = outcome_learning_engine.evaluate_outcomes(db, "USAREC", "USAREC")
        evaluations = payload["outcome_learning_engine"]["outcome_evaluations"]
        assert evaluations[0]["outcome_classification"] == "insufficient_data"
        assert evaluations[0]["confidence_adjustment_suggestion"]["direction"] == "hold"
    finally:
        db.close()
