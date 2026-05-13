import sys
from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "services/api")

from app.models import Station
from app.models_domain import FunnelStage, FunnelTransition, Event, EventMetric
from app.models_intelligence import (
    ContractClassification,
    RecruiterEffectiveness,
    MarketLeakage,
    RecommendationRationale,
    AdvisoryRecommendation,
    RopPlan,
    RopPlanVersion,
    SrpPlan,
    SrpPlanVersion,
    FragoOrder,
    FragoOrderVersion,
    AnalyticsSnapshot,
    AnalyticsSnapshotVersion,
    RecommendationRecord,
    RecommendationRecordVersion,
    ExplanationArchive,
    VacancyAlignment,
)
from app.intelligence_analytics import analyze_contract_roi
from app.intelligence_recommendations import (
    recommend_vacancy_alignment,
    recommend_rop_srp,
    recommend_school_prioritization,
)

POSTGRES_URL = "postgresql://taaip@localhost/taaip"


def create_all_tables(engine):
    # Order matters for Postgres FK enforcement:
    # analytics/recommendation version tables must exist before frago_order_versions
    for tbl in [
        Station.__table__,
        FunnelStage.__table__,
        FunnelTransition.__table__,
        Event.__table__,
        EventMetric.__table__,
        ContractClassification.__table__,
        RecruiterEffectiveness.__table__,
        MarketLeakage.__table__,
        RecommendationRationale.__table__,
        AdvisoryRecommendation.__table__,
        RopPlan.__table__,
        RopPlanVersion.__table__,
        SrpPlan.__table__,
        SrpPlanVersion.__table__,
        AnalyticsSnapshot.__table__,
        AnalyticsSnapshotVersion.__table__,
        RecommendationRecord.__table__,
        RecommendationRecordVersion.__table__,
        FragoOrder.__table__,
        FragoOrderVersion.__table__,
        ExplanationArchive.__table__,
        VacancyAlignment.__table__,
    ]:
        tbl.create(bind=engine, checkfirst=True)


def seed_minimal_picture(session):
    from sqlalchemy import text

    # Ensure station row exists (Postgres enforces events.station_rsid FK)
    session.execute(
        text(
            "INSERT INTO stations (id, rsid, display) VALUES (:id, :rsid, :display)"
            " ON CONFLICT (rsid) DO NOTHING"
        ),
        {"id": 9999, "rsid": "6L4B", "display": "Test Station 6L4B"},
    )
    session.flush()

    # Ensure funnel_stages rows exist (Postgres enforces funnel_transitions FK)
    session.execute(
        text(
            "INSERT INTO funnel_stages (id, stage_name, sequence_order)"
            " VALUES ('prospect', 'Prospect', 1), ('lead', 'Lead', 2)"
            " ON CONFLICT (id) DO NOTHING"
        )
    )
    session.flush()

    session.add_all(
        [
            Event(
                id="e1",
                name="HS Fair",
                event_type="school",
                station_rsid="6L4B",
                start_date=datetime(2026, 2, 1),
            ),
            EventMetric(
                id="em1",
                event_id="e1",
                metric_date=date(2026, 2, 1),
                cost=350.0,
                leads_generated=18,
                conversions=3,
                engagement_rate=0.42,
            ),
            ContractClassification(
                id="cc1",
                contract_id="c1",
                school_zip="98038",
                writing_rsid="6L4B",
                classification="in_area",
                classified_at=datetime(2026, 2, 3),
            ),
            ContractClassification(
                id="cc2",
                contract_id="c2",
                school_zip="98042",
                writing_rsid="6L4B",
                classification="out_of_area",
                classified_at=datetime(2026, 2, 10),
            ),
            RecruiterEffectiveness(
                id="re1",
                recruiter_id="R1",
                station_rsid="6L4B",
                reporting_period="weekly",
                period_date=date(2026, 2, 7),
                efficiency_index=0.28,
                contracts_per_hour=0.6,
            ),
            RecruiterEffectiveness(
                id="re2",
                recruiter_id="R2",
                station_rsid="6L4B",
                reporting_period="weekly",
                period_date=date(2026, 2, 7),
                efficiency_index=0.72,
                contracts_per_hour=1.5,
            ),
            MarketLeakage(
                id="ml1",
                from_zip="98038",
                to_zip="98052",
                from_rsid="6L4B",
                to_rsid="6L1D",
                leak_type="cross_rsid",
                contract_count=5,
                period_start=date(2026, 1, 1),
                period_end=date(2026, 3, 31),
            ),
            FunnelTransition(
                id="ft1",
                lead_key="lead1",
                station_rsid="6L4B",
                from_stage="prospect",
                to_stage="lead",
                transitioned_at=datetime(2026, 2, 12),
            ),
        ]
    )
    session.commit()


def run_reality_check(label, engine):
    print(f"\n===== {label} =====")
    create_all_tables(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    seed_minimal_picture(db)

    print("\n=== ANALYTICS (FY2026 Q2, RSM=6L) ===")
    roi = analyze_contract_roi(db, station_rsid="6L4B", fy="2026", quarter="Q2")
    print("ROI period:", roi.get("period_analyzed_string"))

    print("\n=== RECOMMENDATIONS: VACANCY ALIGNMENT ===")
    vac = recommend_vacancy_alignment(
        db,
        vacancy_mos="11X",
        vacancy_count=4,
        market_zip_primary="98038",
        station_rsid="6L4B",
        fy="2026",
        quarter="Q2",
        rsm="6L",
    )
    print("Vacancy keys:", sorted(vac.keys()))

    print("\n=== RECOMMENDATIONS: ROP/SRP ===")
    rop = recommend_rop_srp(
        db,
        station_rsid="6L4B",
        fy="2026",
        quarter="Q2",
        rsm="6L",
    )
    print("ROP/SRP status:", rop.get("status"))
    print("ROP/SRP rec count:", len(rop.get("recommendations", [])))
    print("FRAGOs created:", len(rop.get("frago_version_ids", [])))

    print("\n=== RECOMMENDATIONS: SCHOOL PRIORITIZATION ===")
    sch = recommend_school_prioritization(
        db,
        station_rsid="6L4B",
        fy="2026",
        quarter="Q2",
        rsm="6L",
    )
    print("School keys:", sorted(sch.keys()))
    print("School ranking count:", len(sch.get("school_rankings", [])))

    print("\n=== VERSIONING COUNTS ===")
    print("AnalyticsSnapshot:", db.query(AnalyticsSnapshot).count())
    print("AnalyticsSnapshotVersion:", db.query(AnalyticsSnapshotVersion).count())
    print("RecommendationRecord:", db.query(RecommendationRecord).count())
    print("RecommendationRecordVersion:", db.query(RecommendationRecordVersion).count())
    print("ExplanationArchive:", db.query(ExplanationArchive).count())
    print("FragoOrder:", db.query(FragoOrder).count())
    print("FragoOrderVersion:", db.query(FragoOrderVersion).count())

    db.close()


def main():
    # SQLite in-memory (fast logic check)
    sqlite_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    run_reality_check("SQLite (in-memory)", sqlite_engine)

    # Postgres (embedded URL)
    pg_engine = create_engine(POSTGRES_URL)
    run_reality_check("Postgres (taaip)", pg_engine)


if __name__ == "__main__":
    main()
