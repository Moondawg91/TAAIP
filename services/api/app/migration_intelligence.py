"""© 2026 TAAIP. Copyright pending.
Migration: Add Data Intelligence Layer tables.
Additive only - no modifications to existing tables.
"""

import os
from sqlalchemy import inspect, text
from .database import engine
from . import models_intelligence as mi


def get_db_engine():
    """Return active SQLAlchemy engine used by the API runtime."""
    return engine


def migration_create_intelligence_tables():
    """Create all intelligence layer tables."""
    engine = get_db_engine()
    
    # Create all models
    mi.Base.metadata.create_all(engine)
    
    print("✓ Intelligence layer tables created")


def verify_intelligence_schema():
    """Verify intelligence schema is properly created."""
    engine = get_db_engine()
    inspector = inspect(engine)
    
    expected_tables = [
        'data_sources',
        'data_ingestion_logs',
        'column_mappings',
        'normalized_values',
        'historical_snapshots',
        'snapshot_metrics',
        'contract_classifications',
        'market_leakage',
        'contract_influence',
        'recruiter_activity',
        'recruiter_effectiveness',
        'predictive_production_pace',
        'vacancy_alignment',
        'target_populations',
        'messaging_themes',
        'recommendation_rationale',
        'advisory_recommendations'
    ]
    
    existing_tables = inspector.get_table_names()
    
    created = [t for t in expected_tables if t in existing_tables]
    missing = [t for t in expected_tables if t not in existing_tables]
    
    print(f"✓ Intelligence tables created: {len(created)}/{len(expected_tables)}")
    if missing:
        print(f"⚠ Missing tables: {', '.join(missing)}")
    
    return len(missing) == 0
