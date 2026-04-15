from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.api.app.services import live_context_engine


def _session():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_live_context_engine_ingest_and_classify_signals():
    db = _session()
    try:
        now = datetime.utcnow().isoformat() + "Z"
        live_context_engine.ingest_context_signals(
            db,
            [
                {
                    "signal_id": "sig-001",
                    "signal_summary": "State policy update increases student outreach opportunity.",
                    "source": "state_policy_feed",
                    "source_type": "official",
                    "published_at": now,
                    "confidence": 0.82,
                    "operational_implication": "Opportunity to expand school access in high-yield areas.",
                    "scope_type": "USAREC",
                    "scope_value": "USAREC",
                },
                {
                    "signal_id": "sig-002",
                    "signal_summary": "Weather disruption risk across multiple districts.",
                    "source": "weather_partner",
                    "source_type": "external",
                    "published_at": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z",
                    "confidence": 0.6,
                    "operational_implication": "Risk to event throughput and schedule reliability.",
                    "scope_type": "USAREC",
                    "scope_value": "USAREC",
                },
            ],
        )

        payload = live_context_engine.summarize_context_signals(db, "USAREC", "USAREC")
        assert payload["status"] == "ok"
        engine_payload = payload["live_context_engine"]
        assert engine_payload["summary"]["signals_ingested"] == 2
        assert engine_payload["summary"]["approval_required_signals"] == 2

        signals = engine_payload["context_signals"]
        assert signals[0]["confidence"] >= signals[1]["confidence"]
        assert all(item["trust_label"] in {"high", "medium", "low"} for item in signals)
        assert all(item["approval_required"] is True for item in signals)
    finally:
        db.close()
