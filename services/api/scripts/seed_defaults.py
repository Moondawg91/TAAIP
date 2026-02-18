"""Seed required system defaults only (idempotent).

This script intentionally does NOT seed any demo or synthetic domain data.
It will only create reference/configuration rows necessary for the system to operate:
- market_category_weights (MK/MW/MO/SU/UNK)
- funnel_stages baseline (if the table exists)

Optional: create two admin users if `SEED_SAMPLE_USERS=true` is set in the environment.
This is disabled by default to avoid contaminating real environments.
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, engine
from app.models import MarketCategoryWeights, MarketCategory, User, UserRole, Base
from app.models_domain import FunnelStage


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed market category weights (idempotent)
    defaults = {"MK": 4, "MW": 3, "MO": 2, "SU": 1, "UNK": 0}
    for cat, w in defaults.items():
        try:
            enum_val = MarketCategory[cat]
        except Exception:
            enum_val = None
        if enum_val is None:
            continue
        obj = db.query(MarketCategoryWeights).filter_by(category=enum_val).one_or_none()
        if not obj:
            db.add(MarketCategoryWeights(category=enum_val, weight=w))
    db.commit()

    # Optionally seed funnel stages (idempotent)
    stages = [
        ("lead", "lead", 1),
        ("prospect", "prospect", 2),
        ("appointment_made", "appointment_made", 3),
        ("appointment_conducted", "appointment_conducted", 4),
        ("test", "test", 5),
        ("test_pass", "test_pass", 6),
        ("physical", "physical", 7),
        ("enlist", "enlist", 8),
    ]
    for sid, name, order in stages:
        existing = db.query(FunnelStage).filter_by(id=sid).one_or_none()
        if not existing:
            db.add(FunnelStage(id=sid, stage_name=name, sequence_order=order))
    db.commit()

    # Optional: create minimal admin users only when explicitly requested
    if os.environ.get('SEED_SAMPLE_USERS', '').lower() in ('1', 'true', 'yes'):
        sample = [
            ("sysadmin", UserRole.SYSADMIN, "USAREC"),
            ("usarec_admin", UserRole.USAREC, "USAREC"),
        ]
        for username, role, scope in sample:
            u = db.query(User).filter_by(username=username).one_or_none()
            if not u:
                db.add(User(username=username, role=role, scope=scope))
        db.commit()

    print("Seed complete (only system defaults were applied)")


if __name__ == '__main__':
    seed()
