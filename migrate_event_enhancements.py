#!/usr/bin/env python3
"""
Database migration to add event type classification, predictive analytics,
and G2 Zone lead performance tracking capabilities.
"""

import sqlite3
from datetime import datetime

DB_FILE = 'recruiting.db'

def run_migration():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🔄 Starting event enhancements migration...")
    
    # Ensure base events table exists (aligns with taaip_service.py schema)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            start_date TEXT,
            end_date TEXT,
            budget REAL,
            team_size INTEGER,
            targeting_principles TEXT,
            status TEXT DEFAULT 'planned',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()
    
    try:
        # Add event_type_category column to events table
        print("  ➤ Adding event type classification...")
        cursor.execute("""
            ALTER TABLE events ADD COLUMN event_type_category TEXT 
            DEFAULT 'lead_generating' 
            CHECK(event_type_category IN (
                'lead_generating', 'shaping', 'brand_awareness', 
                'community_engagement', 'retention', 'research'
            ))
        """)
        
        # Add predicted metrics columns
        print("  ➤ Adding predicted metrics tracking...")
        cursor.execute("ALTER TABLE events ADD COLUMN predicted_leads INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE events ADD COLUMN predicted_conversions INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE events ADD COLUMN predicted_roi REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE events ADD COLUMN predicted_cost_per_lead REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE events ADD COLUMN prediction_confidence REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE events ADD COLUMN prediction_date TEXT")
        cursor.execute("ALTER TABLE events ADD COLUMN prediction_model TEXT")
        
        # Add actual metrics columns
        cursor.execute("ALTER TABLE events ADD COLUMN actual_leads INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE events ADD COLUMN actual_conversions INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE events ADD COLUMN actual_roi REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE events ADD COLUMN actual_cost_per_lead REAL DEFAULT 0.0")
        
        # Add variance tracking
        cursor.execute("ALTER TABLE events ADD COLUMN leads_variance REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE events ADD COLUMN roi_variance REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE events ADD COLUMN prediction_accuracy REAL DEFAULT 0.0")
        
        conn.commit()
        print("  ✅ Events table enhanced")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("  ⚠️  Columns already exist, skipping...")
        else:
            raise
    
    # Create marketing_nominations table
    print("  ➤ Creating marketing_nominations table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marketing_nominations (
            nomination_id TEXT PRIMARY KEY,
            event_id TEXT,
            nomination_date TEXT NOT NULL,
            nominator_id TEXT,
            nominator_name TEXT,
            nomination_type TEXT CHECK(nomination_type IN (
                'event', 'campaign', 'sponsorship', 'partnership', 'digital'
            )),
            description TEXT,
            target_audience TEXT,
            estimated_reach INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0.0,
            predicted_leads INTEGER DEFAULT 0,
            predicted_roi REAL DEFAULT 0.0,
            prediction_confidence REAL DEFAULT 0.0,
            status TEXT DEFAULT 'submitted' CHECK(status IN (
                'submitted', 'under_review', 'approved', 'rejected', 'executed', 'completed'
            )),
            approval_date TEXT,
            approver_id TEXT,
            actual_leads INTEGER DEFAULT 0,
            actual_conversions INTEGER DEFAULT 0,
            actual_roi REAL DEFAULT 0.0,
            leads_variance REAL DEFAULT 0.0,
            roi_variance REAL DEFAULT 0.0,
            rsid TEXT,
            brigade TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    """)
    conn.commit()
    print("  ✅ marketing_nominations table created")
    
    # Create g2_zone_performance table
    print("  ➤ Creating G2 Zone lead performance tracking table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS g2_zone_performance (
            zone_id TEXT PRIMARY KEY,
            zone_name TEXT NOT NULL,
            geographic_area TEXT,
            population INTEGER DEFAULT 0,
            military_age_population INTEGER DEFAULT 0,
            current_quarter TEXT,
            fiscal_year INTEGER,
            lead_count INTEGER DEFAULT 0,
            qualified_leads INTEGER DEFAULT 0,
            conversion_count INTEGER DEFAULT 0,
            enlistment_count INTEGER DEFAULT 0,
            ship_count INTEGER DEFAULT 0,
            qualification_rate REAL DEFAULT 0.0,
            conversion_rate REAL DEFAULT 0.0,
            enlistment_rate REAL DEFAULT 0.0,
            avg_lead_quality_score REAL DEFAULT 0.0,
            avg_days_to_conversion REAL DEFAULT 0.0,
            top_lead_source TEXT,
            top_mos TEXT,
            market_penetration_rate REAL DEFAULT 0.0,
            competitive_index REAL DEFAULT 0.0,
            trend_direction TEXT CHECK(trend_direction IN ('up', 'down', 'stable')),
            rsid TEXT,
            brigade TEXT,
            battalion TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("  ✅ g2_zone_performance table created")
    
    # Create emm_historical_data table for ML training
    print("  ➤ Creating EMM historical data table for ML...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emm_historical_data (
            data_id TEXT PRIMARY KEY,
            event_id TEXT,
            event_type_category TEXT,
            event_date TEXT,
            location TEXT,
            budget REAL,
            team_size INTEGER,
            target_audience TEXT,
            weather_conditions TEXT,
            day_of_week TEXT,
            month TEXT,
            competing_events INTEGER DEFAULT 0,
            social_media_reach INTEGER DEFAULT 0,
            email_invites_sent INTEGER DEFAULT 0,
            partnership_level TEXT,
            venue_type TEXT,
            leads_generated INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            roi REAL DEFAULT 0.0,
            cost_per_lead REAL DEFAULT 0.0,
            engagement_score REAL DEFAULT 0.0,
            follow_up_rate REAL DEFAULT 0.0,
            zone_id TEXT,
            rsid TEXT,
            brigade TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(event_id),
            FOREIGN KEY (zone_id) REFERENCES g2_zone_performance(zone_id)
        )
    """)
    conn.commit()
    print("  ✅ emm_historical_data table created")
    
    # Create ml_predictions table
    print("  ➤ Creating ML predictions tracking table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            prediction_id TEXT PRIMARY KEY,
            entity_type TEXT CHECK(entity_type IN ('event', 'nomination', 'campaign')),
            entity_id TEXT NOT NULL,
            prediction_date TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT,
            predicted_leads INTEGER DEFAULT 0,
            predicted_conversions INTEGER DEFAULT 0,
            predicted_roi REAL DEFAULT 0.0,
            predicted_cost_per_lead REAL DEFAULT 0.0,
            confidence_score REAL DEFAULT 0.0,
            feature_importance TEXT,
            actual_leads INTEGER,
            actual_conversions INTEGER,
            actual_roi REAL,
            prediction_accuracy REAL,
            mean_absolute_error REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("  ✅ ml_predictions table created")
    
    # Create indexes for performance
    print("  ➤ Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nominations_status ON marketing_nominations(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nominations_rsid ON marketing_nominations(rsid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_g2_zone_rsid ON g2_zone_performance(rsid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emm_event_type ON emm_historical_data(event_type_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emm_date ON emm_historical_data(event_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ml_entity ON ml_predictions(entity_type, entity_id)")
    conn.commit()
    print("  ✅ Indexes created")
    
    # Update existing events with default event_type_category based on name/type
    print("  ➤ Classifying existing events...")
    cursor.execute("""
        UPDATE events 
        SET event_type_category = CASE
            WHEN lower(name) LIKE '%career%' OR lower(name) LIKE '%recruiting%' THEN 'lead_generating'
            WHEN lower(name) LIKE '%community%' OR lower(name) LIKE '%partnership%' THEN 'shaping'
            WHEN lower(name) LIKE '%brand%' OR lower(name) LIKE '%awareness%' THEN 'brand_awareness'
            WHEN lower(name) LIKE '%research%' OR lower(name) LIKE '%intel%' THEN 'research'
            ELSE 'lead_generating'
        END
        WHERE event_type_category IS NULL
    """)
    conn.commit()
    print("  ✅ Existing events classified")
    
    conn.close()
    print("\n✅ Migration completed successfully!\n")

if __name__ == '__main__':
    run_migration()
