from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.services import adaptive_update_engine, live_context_engine, outcome_learning_engine


def _session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_adaptive_update_engine_generates_approval_gated_proposals_with_versioning():
    db = _session()
    try:
        outcome_learning_engine.record_outcome(
            db,
            {
                "recommendation_id": "rec-101",
                "source_engine": "market_engine",
                "scope_type": "USAREC",
                "scope_value": "USAREC",
                "recommendation_kind": "market_shift",
                "expected_kpi": {"leads": 100},
                "actual_kpi": {"leads": 70},
                "observed_state": "on_track",
            },
        )
        live_context_engine.ingest_context_signals(
            db,
            [
                {
                    "signal_id": "signal-ctx-01",
                    "signal_summary": "Local labor market opportunity increases outreach yield.",
                    "source": "regional_market_feed",
                    "source_type": "official",
                    "confidence": 0.9,
                    "operational_implication": "Opportunity to increase conversion focus.",
                    "scope_type": "USAREC",
                    "scope_value": "USAREC",
                }
            ],
        )

        payload = adaptive_update_engine.generate_update_proposals(db, "USAREC", "USAREC", persist=True)
        assert payload["status"] == "ok"

        engine_payload = payload["adaptive_update_engine"]
        assert engine_payload["summary"]["proposals_generated"] >= 2
        assert engine_payload["summary"]["approval_required"] == engine_payload["summary"]["proposals_generated"]
        assert engine_payload["summary"]["auto_applicable"] == 0
        assert engine_payload["versioning"]["current_config_version"].startswith("controlled-learning-v")

        proposals = engine_payload["update_proposals"]
        assert all(item["approval_state"] == "draft" for item in proposals)
        assert all(item["rollback_plan"] for item in proposals)

        first = proposals[0]["proposal_id"]
        state_change = adaptive_update_engine.update_proposal_state(db, first, "pending_review")
        assert state_change["status"] == "ok"
        listed = adaptive_update_engine.list_proposals(db, "USAREC", "USAREC", approval_state="pending_review")
        assert any(item["proposal_id"] == first for item in listed["items"])
    finally:
        db.close()
