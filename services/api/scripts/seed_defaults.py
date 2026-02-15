"""Seed default market weights and sample users for Phase 1"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2] / 'app'))

from database import SessionLocal, engine
from models import MarketCategoryWeights, MarketCategory, User, UserRole, Base


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # seed weights
    defaults = {"MK": 4, "MW": 3, "MO": 2, "SU": 1, "UNK": 0}
    for cat, w in defaults.items():
        obj = db.query(MarketCategoryWeights).filter_by(category=MarketCategory[cat]).one_or_none()
        if not obj:
            obj = MarketCategoryWeights(category=MarketCategory[cat], weight=w)
            db.add(obj)
    db.commit()

    # seed sample users
    sample = [
        ("usarec_admin", UserRole.USAREC, "USAREC"),
        ("bde_420t", UserRole.BRIGADE_420T, "1"),
        ("bn_420t", UserRole.BATTALION_420T, "1A"),
        ("fusion_analyst", UserRole.FUSION, "USAREC"),
        ("bde_view", UserRole.BRIGADE_VIEW, "1"),
        ("bn_view", UserRole.BATTALION_VIEW, "1A"),
        ("company_cmd", UserRole.COMPANY_CMD, "1A1"),
        ("station_view", UserRole.STATION_VIEW, "1A1D"),
        ("sysadmin", UserRole.SYSADMIN, "USAREC"),
    ]

    for username, role, scope in sample:
        u = db.query(User).filter_by(username=username).one_or_none()
        if not u:
            u = User(username=username, role=role, scope=scope)
            db.add(u)
    db.commit()
    print("Seed complete")


if __name__ == '__main__':
    seed()
