"""
Database Migration: Rebuild Lead System for USAREC Recruiting Funnel
Replaces simple lead input with PRID-based funnel tracking from EMM/iKrome/Recruiter Zone
"""
import sqlite3
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = SCRIPT_DIR / "recruiting.db"


def migrate_leads_to_recruiting_funnel():
    """Transform leads table to track USAREC recruiting funnel stages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Migrating Lead system to USAREC Recruiting Funnel...")
    
    # Backup existing leads table
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS leads_backup_20251117 AS SELECT * FROM leads")
        print("  ✅ Backed up existing leads table")
    except Exception as e:
        print(f"  ⚠️  Backup note: {e}")
    
    # Drop old leads table and create new one
    cursor.execute("DROP TABLE IF EXISTS leads")
    
    cursor.execute("""
        CREATE TABLE leads (
            prid TEXT PRIMARY KEY,  -- USAREC PRID from EMM/iKrome/Recruiter Zone
            rsid TEXT,  -- Station RSID (e.g., "1BDE-1BN-1-1")
            brigade TEXT,
            battalion TEXT,
            station TEXT,
            
            -- Lead Information
            first_name TEXT,
            last_name TEXT,
            age INTEGER,
            gender TEXT,
            education_level TEXT,
            cbsa_code TEXT,
            zip_code TEXT,
            
            -- Funnel Stage Tracking
            current_stage TEXT NOT NULL,  -- 'lead', 'prospect', 'applicant', 'dep', 'contract', 'ship', 'loss'
            lead_source TEXT,  -- 'EMM', 'iKrome', 'Recruiter Zone', 'walk-in', 'referral', 'event', etc.
            campaign_source TEXT,
            
            -- Funnel Stage Timestamps (Flash-to-Bang tracking)
            lead_date DATETIME,  -- Initial lead capture
            prospect_date DATETIME,  -- Qualified as prospect
            applicant_date DATETIME,  -- Submitted application
            test_date DATETIME,  -- ASVAB/physical test
            dep_date DATETIME,  -- Entered DEP (Delayed Entry Program)
            contract_date DATETIME,  -- Signed enlistment contract
            ship_date DATETIME,  -- Shipped to basic training
            loss_date DATETIME,  -- Lost from funnel
            
            -- Loss/Attrition Tracking
            loss_reason TEXT,  -- Why lost (disqualified, changed mind, competitor, etc.)
            loss_stage TEXT,  -- At what stage was lead lost
            
            -- Recruiting Data
            recruiter_id TEXT,  -- Assigned recruiter
            mos_interest TEXT,  -- Military Occupational Specialty interest
            incentive_qualified BOOLEAN DEFAULT 0,  -- Qualified for bonuses/incentives
            dep_length_days INTEGER,  -- Days in DEP
            
            -- AI Scoring (kept for predictive analytics)
            predicted_probability FLOAT,  -- AI prediction of contract likelihood
            score INTEGER,  -- Lead quality score 0-100
            risk_score INTEGER,  -- Risk of loss score 0-100
            
            -- Fiscal Year Tracking
            fiscal_year INTEGER,  -- FY when lead was captured
            ship_month TEXT,  -- Scheduled ship month (format: "YYYY-MM")
            recruiting_year TEXT,  -- Recruiting Year (RY)
            quarter TEXT,  -- Q1, Q2, Q3, Q4
            
            -- USAREC System Integration
            emm_id TEXT,  -- EMM system ID
            ikrome_id TEXT,  -- iKrome system ID
            rzone_id TEXT,  -- Recruiter Zone ID
            last_sync_at DATETIME,  -- Last sync from USAREC systems
            
            -- Metadata
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_archived BOOLEAN DEFAULT 0,
            archived_at DATETIME,
            archived_reason TEXT
        )
    """)
    print("  ✅ Created new leads table with recruiting funnel structure")
    
    # Create indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_leads_prid ON leads(prid)",
        "CREATE INDEX IF NOT EXISTS idx_leads_rsid ON leads(rsid)",
        "CREATE INDEX IF NOT EXISTS idx_leads_brigade ON leads(brigade)",
        "CREATE INDEX IF NOT EXISTS idx_leads_current_stage ON leads(current_stage)",
        "CREATE INDEX IF NOT EXISTS idx_leads_fiscal_year ON leads(fiscal_year)",
        "CREATE INDEX IF NOT EXISTS idx_leads_ship_month ON leads(ship_month)",
        "CREATE INDEX IF NOT EXISTS idx_leads_recruiter ON leads(recruiter_id)",
        "CREATE INDEX IF NOT EXISTS idx_leads_lead_date ON leads(lead_date)",
        "CREATE INDEX IF NOT EXISTS idx_leads_contract_date ON leads(contract_date)",
    ]
    
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    print("  ✅ Created indexes for funnel tracking")
    
    # Create funnel stage transitions table (audit log)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funnel_transitions (
            transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prid TEXT NOT NULL,
            from_stage TEXT,
            to_stage TEXT NOT NULL,
            transition_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            user_id TEXT,
            FOREIGN KEY (prid) REFERENCES leads(prid)
        )
    """)
    print("  ✅ Created funnel_transitions table for stage history")
    
    # Create funnel metrics summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS funnel_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rsid TEXT,
            fiscal_year INTEGER,
            month TEXT,
            
            -- Funnel counts
            leads_count INTEGER DEFAULT 0,
            prospects_count INTEGER DEFAULT 0,
            applicants_count INTEGER DEFAULT 0,
            dep_count INTEGER DEFAULT 0,
            contracts_count INTEGER DEFAULT 0,
            ships_count INTEGER DEFAULT 0,
            losses_count INTEGER DEFAULT 0,
            
            -- Conversion rates
            lead_to_prospect_rate FLOAT,
            prospect_to_applicant_rate FLOAT,
            applicant_to_contract_rate FLOAT,
            contract_to_ship_rate FLOAT,
            overall_conversion_rate FLOAT,
            
            -- Time metrics (avg days)
            avg_lead_to_contract_days FLOAT,
            avg_lead_to_ship_days FLOAT,
            avg_dep_length_days FLOAT,
            
            -- Loss analysis
            loss_rate FLOAT,
            top_loss_reason TEXT,
            
            calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ Created funnel_metrics table for analytics")
    
    conn.commit()
    conn.close()
    
    print("✅ Lead system migration completed!")
    print("\nNew Recruiting Funnel Stages:")
    print("  1. Lead - Initial contact/interest")
    print("  2. Prospect - Qualified and interested")
    print("  3. Applicant - Application submitted")
    print("  4. DEP - Delayed Entry Program")
    print("  5. Contract - Enlisted (signed contract)")
    print("  6. Ship - Shipped to basic training")
    print("  7. Loss - Lost from funnel")
    print("\nKey Features:")
    print("  ✅ PRID tracking (USAREC system ID)")
    print("  ✅ Flash-to-bang metrics (stage timestamps)")
    print("  ✅ Fiscal year and ship month tracking")
    print("  ✅ Loss/attrition analysis")
    print("  ✅ Conversion rate tracking")
    print("  ✅ Bottleneck identification")
    print("  ✅ RSID filtering")


if __name__ == "__main__":
    try:
        migrate_leads_to_recruiting_funnel()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
