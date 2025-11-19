#!/usr/bin/env python3
"""
Add market potential tracking and DOD branch comparison tables.
Tracks market potential, DOD remaining potential, and comparative analysis
by ZIP code, CBSA, and RSID levels.
"""

import sqlite3
from datetime import datetime

DB_FILE = "/Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3"

def migrate_market_potential():
    print("🔄 Adding market potential and DOD comparison tracking...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 1. Market Potential by Geography
        print("  📊 Creating market_potential table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_potential (
                id TEXT PRIMARY KEY,
                geographic_level TEXT NOT NULL CHECK (geographic_level IN ('zipcode', 'cbsa', 'rsid')),
                geographic_id TEXT NOT NULL,
                geographic_name TEXT,
                
                -- USAREC hierarchy (for RSID level)
                usarec_region TEXT,
                brigade TEXT,
                battalion TEXT,
                company TEXT,
                station TEXT,
                
                -- Total addressable market
                total_population INTEGER DEFAULT 0,
                target_age_population INTEGER DEFAULT 0,
                qualified_population INTEGER DEFAULT 0,
                
                -- Army market data
                army_total_potential INTEGER DEFAULT 0,
                army_contacted INTEGER DEFAULT 0,
                army_remaining_potential INTEGER DEFAULT 0,
                army_market_share REAL DEFAULT 0,
                
                -- DOD branch comparisons
                navy_total_potential INTEGER DEFAULT 0,
                navy_contacted INTEGER DEFAULT 0,
                navy_remaining_potential INTEGER DEFAULT 0,
                navy_market_share REAL DEFAULT 0,
                
                air_force_total_potential INTEGER DEFAULT 0,
                air_force_contacted INTEGER DEFAULT 0,
                air_force_remaining_potential INTEGER DEFAULT 0,
                air_force_market_share REAL DEFAULT 0,
                
                marines_total_potential INTEGER DEFAULT 0,
                marines_contacted INTEGER DEFAULT 0,
                marines_remaining_potential INTEGER DEFAULT 0,
                marines_market_share REAL DEFAULT 0,
                
                space_force_total_potential INTEGER DEFAULT 0,
                space_force_contacted INTEGER DEFAULT 0,
                space_force_remaining_potential INTEGER DEFAULT 0,
                space_force_market_share REAL DEFAULT 0,
                
                coast_guard_total_potential INTEGER DEFAULT 0,
                coast_guard_contacted INTEGER DEFAULT 0,
                coast_guard_remaining_potential INTEGER DEFAULT 0,
                coast_guard_market_share REAL DEFAULT 0,
                
                -- Competitive analysis
                total_dod_contacted INTEGER DEFAULT 0,
                total_dod_remaining INTEGER DEFAULT 0,
                army_competitive_position INTEGER DEFAULT 0,
                
                -- Fiscal year and time tracking
                fiscal_year INTEGER,
                quarter TEXT,
                reporting_period TEXT,
                
                -- Metadata
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                data_source TEXT,
                UNIQUE(geographic_level, geographic_id, fiscal_year, quarter)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_geo_level ON market_potential(geographic_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_geo_id ON market_potential(geographic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_fy ON market_potential(fiscal_year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_rsid ON market_potential(usarec_region, brigade, battalion, company, station)")
        print("    ✅ market_potential table created")
        
        # 2. Mission Analysis Tracking
        print("  🎯 Creating mission_analysis table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mission_analysis (
                analysis_id TEXT PRIMARY KEY,
                
                -- USAREC hierarchy level
                analysis_level TEXT NOT NULL CHECK (analysis_level IN ('usarec', 'brigade', 'battalion', 'company', 'station')),
                usarec_region TEXT DEFAULT 'USAREC',
                brigade TEXT,
                battalion TEXT,
                company TEXT,
                station TEXT,
                
                -- Mission goals and actuals
                mission_goal INTEGER DEFAULT 0,
                contracts_actual INTEGER DEFAULT 0,
                contracts_variance INTEGER DEFAULT 0,
                goal_attainment_pct REAL DEFAULT 0,
                
                -- Production metrics
                leads_generated INTEGER DEFAULT 0,
                appointments_made INTEGER DEFAULT 0,
                appointments_conducted INTEGER DEFAULT 0,
                tests_administered INTEGER DEFAULT 0,
                tests_passed INTEGER DEFAULT 0,
                enlistments INTEGER DEFAULT 0,
                ships INTEGER DEFAULT 0,
                
                -- Efficiency metrics
                lead_to_enlistment_rate REAL DEFAULT 0,
                appointment_show_rate REAL DEFAULT 0,
                test_pass_rate REAL DEFAULT 0,
                enlistment_to_ship_rate REAL DEFAULT 0,
                
                -- Market penetration
                market_penetration_rate REAL DEFAULT 0,
                dod_share_of_market REAL DEFAULT 0,
                army_share_of_dod REAL DEFAULT 0,
                
                -- Resource allocation
                recruiters_assigned INTEGER DEFAULT 0,
                contracts_per_recruiter REAL DEFAULT 0,
                cost_per_contract REAL DEFAULT 0,
                
                -- Time period
                fiscal_year INTEGER,
                quarter TEXT,
                month TEXT,
                reporting_period TEXT,
                
                -- Metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(analysis_level, usarec_region, brigade, battalion, company, station, fiscal_year, quarter)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mission_level ON mission_analysis(analysis_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mission_fy ON mission_analysis(fiscal_year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mission_hierarchy ON mission_analysis(brigade, battalion, company, station)")
        print("    ✅ mission_analysis table created")
        
        # 3. DOD Branch Performance Comparison
        print("  🏆 Creating dod_branch_comparison table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dod_branch_comparison (
                comparison_id TEXT PRIMARY KEY,
                
                branch TEXT NOT NULL CHECK (branch IN ('Army', 'Navy', 'Air Force', 'Marines', 'Space Force', 'Coast Guard')),
                
                -- Geographic scope
                geographic_level TEXT NOT NULL CHECK (geographic_level IN ('national', 'state', 'cbsa', 'zipcode')),
                geographic_id TEXT,
                geographic_name TEXT,
                
                -- Recruiting metrics
                total_recruiters INTEGER DEFAULT 0,
                total_leads INTEGER DEFAULT 0,
                total_contracts INTEGER DEFAULT 0,
                total_ships INTEGER DEFAULT 0,
                
                -- Conversion metrics
                lead_to_contract_rate REAL DEFAULT 0,
                contract_to_ship_rate REAL DEFAULT 0,
                overall_efficiency_score REAL DEFAULT 0,
                
                -- Market metrics
                market_potential INTEGER DEFAULT 0,
                market_penetration_rate REAL DEFAULT 0,
                contracts_per_recruiter REAL DEFAULT 0,
                
                -- Quality metrics
                avg_asvab_score REAL DEFAULT 0,
                tier_1_percentage REAL DEFAULT 0,
                high_school_grad_rate REAL DEFAULT 0,
                
                -- Time period
                fiscal_year INTEGER,
                quarter TEXT,
                
                -- Metadata
                data_source TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(branch, geographic_level, geographic_id, fiscal_year, quarter)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dod_branch ON dod_branch_comparison(branch)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dod_geo ON dod_branch_comparison(geographic_level, geographic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dod_fy ON dod_branch_comparison(fiscal_year)")
        print("    ✅ dod_branch_comparison table created")
        
        # 4. Geographic Reference Data
        print("  🗺️  Creating geographic_reference table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geographic_reference (
                geo_id TEXT PRIMARY KEY,
                geo_type TEXT NOT NULL CHECK (geo_type IN ('zipcode', 'cbsa', 'state', 'county')),
                geo_code TEXT NOT NULL,
                geo_name TEXT,
                
                -- Parent relationships
                state_code TEXT,
                state_name TEXT,
                cbsa_code TEXT,
                cbsa_name TEXT,
                county_code TEXT,
                county_name TEXT,
                
                -- RSID mapping (for recruitment territories)
                rsid TEXT,
                brigade TEXT,
                battalion TEXT,
                station TEXT,
                
                -- Demographics
                total_population INTEGER DEFAULT 0,
                age_17_24_population INTEGER DEFAULT 0,
                median_household_income INTEGER DEFAULT 0,
                high_school_grad_rate REAL DEFAULT 0,
                unemployment_rate REAL DEFAULT 0,
                
                -- Geographic data
                latitude REAL,
                longitude REAL,
                
                -- Metadata
                last_census_update TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(geo_type, geo_code)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_type ON geographic_reference(geo_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_code ON geographic_reference(geo_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_rsid ON geographic_reference(rsid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_cbsa ON geographic_reference(cbsa_code)")
        print("    ✅ geographic_reference table created")
        
        conn.commit()
        print()
        print("✅ Market potential and DOD comparison tracking completed!")
        print()
        print("New Tables Created:")
        print("  1. market_potential - Track Army vs DOD branch potential by geography")
        print("  2. mission_analysis - USAREC hierarchy mission tracking and analysis")
        print("  3. dod_branch_comparison - Comparative performance across all DOD branches")
        print("  4. geographic_reference - ZIP/CBSA/RSID mapping and demographics")
        print()
        print("Features:")
        print("  ✅ Market potential tracking (total, contacted, remaining)")
        print("  ✅ DOD branch comparison (Army, Navy, Air Force, Marines, Space Force, Coast Guard)")
        print("  ✅ Geographic filtering (ZIP code, CBSA, RSID)")
        print("  ✅ USAREC hierarchy analysis (USAREC → Brigade → Battalion → Company → Station)")
        print("  ✅ Mission goal tracking with variance analysis")
        print("  ✅ Market penetration and competitive positioning")
        print("  ✅ Fiscal year and quarterly reporting")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_market_potential()
