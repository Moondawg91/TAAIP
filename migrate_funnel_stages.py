#!/usr/bin/env python3
"""
Update recruiting funnel stages to match Army recruiting process:
Lead → Prospect → Appointment Made → Appointment Conducted → Test → Test Pass → Enlistment

This migration:
1. Backs up existing leads table
2. Updates leads table schema with new stage columns
3. Migrates existing data to new stage structure
4. Updates funnel_transitions and funnel_metrics tables
"""

import sqlite3
from datetime import datetime

DB_FILE = "/Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3"

def migrate_funnel_stages():
    print("🔄 Updating recruiting funnel stages to match Army process...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Step 1: Backup existing data
        print("  📦 Backing up existing leads data...")
        backup_table = f"leads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM leads")
        print(f"    ✅ Backup created: {backup_table}")
        
        # Step 2: Create new leads table with updated stages
        print("  🏗️  Creating new leads table with Army recruiting stages...")
        
        cursor.execute("DROP TABLE IF EXISTS leads_new")
        cursor.execute("""
            CREATE TABLE leads_new (
                prid TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                education_level TEXT,
                rsid TEXT,
                brigade TEXT,
                battalion TEXT,
                station TEXT,
                recruiter_id TEXT,
                lead_source TEXT,
                mos_interest TEXT,
                
                -- Current funnel stage
                current_stage TEXT NOT NULL CHECK (current_stage IN (
                    'lead', 'prospect', 'appointment_made', 'appointment_conducted', 
                    'test', 'test_pass', 'enlistment', 'ship', 'loss'
                )),
                
                -- Stage timestamps (flash-to-bang tracking)
                lead_date TEXT,
                prospect_date TEXT,
                appointment_made_date TEXT,
                appointment_conducted_date TEXT,
                test_date TEXT,
                test_pass_date TEXT,
                enlistment_date TEXT,
                ship_date TEXT,
                loss_date TEXT,
                
                -- Test information
                asvab_score INTEGER,
                test_type TEXT,
                test_location TEXT,
                
                -- Appointment tracking
                appointment_type TEXT,
                appointment_location TEXT,
                appointment_no_show BOOLEAN DEFAULT 0,
                
                -- Loss/attrition tracking
                loss_reason TEXT,
                loss_stage TEXT,
                
                -- DEP tracking
                dep_date TEXT,
                dep_length_days INTEGER,
                
                -- Fiscal year and recruiting metrics
                fiscal_year INTEGER,
                recruiting_year TEXT,
                quarter TEXT,
                ship_month TEXT,
                
                -- USAREC system integration
                emm_id TEXT,
                ikrome_id TEXT,
                rzone_id TEXT,
                last_sync_at TEXT,
                
                -- Metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("    ✅ New leads table created")
        
        # Step 3: Migrate existing data to new structure
        print("  🔄 Migrating existing data to new structure...")
        
        # Mapping old stages to new stages
        stage_mapping = {
            'lead': 'lead',
            'prospect': 'prospect',
            'applicant': 'appointment_made',  # applicant becomes appointment_made
            'dep': 'test_pass',  # DEP typically comes after test pass
            'contract': 'enlistment',  # contract is enlistment
            'ship': 'ship',
            'loss': 'loss'
        }
        
        cursor.execute("SELECT * FROM leads")
        old_leads = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        migrated = 0
        for row in old_leads:
            old_data = dict(zip(columns, row))
            
            # Map old stage to new stage
            old_stage = old_data.get('current_stage', 'lead')
            new_stage = stage_mapping.get(old_stage, 'lead')
            
            # Map date columns
            appointment_made_date = old_data.get('applicant_date')
            test_pass_date = old_data.get('dep_date')
            enlistment_date = old_data.get('contract_date')
            
            # For test_pass stage, estimate test_date as 1 day before
            test_date = None
            if test_pass_date and new_stage in ['test_pass', 'enlistment', 'ship']:
                # test_date would be same as or slightly before test_pass_date
                test_date = test_pass_date
            
            # Insert into new table
            cursor.execute("""
                INSERT INTO leads_new (
                    prid, first_name, last_name, age, education_level,
                    rsid, brigade, battalion, station,
                    recruiter_id, lead_source, mos_interest,
                    current_stage,
                    lead_date, prospect_date, appointment_made_date, appointment_conducted_date,
                    test_date, test_pass_date, enlistment_date, ship_date, loss_date,
                    loss_reason, loss_stage, dep_date, dep_length_days,
                    fiscal_year, recruiting_year, quarter, ship_month,
                    emm_id, ikrome_id, rzone_id, last_sync_at,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?
                )
            """, (
                old_data.get('prid'),
                old_data.get('first_name'),
                old_data.get('last_name'),
                old_data.get('age'),
                old_data.get('education_level'),
                old_data.get('rsid'),
                old_data.get('brigade'),
                old_data.get('battalion'),
                old_data.get('station'),
                old_data.get('recruiter_id'),
                old_data.get('lead_source'),
                old_data.get('mos_interest'),
                new_stage,
                old_data.get('lead_date'),
                old_data.get('prospect_date'),
                appointment_made_date,
                appointment_made_date,  # Assume conducted same as made for existing data
                test_date,
                test_pass_date,
                enlistment_date,
                old_data.get('ship_date'),
                old_data.get('loss_date'),
                old_data.get('loss_reason'),
                old_data.get('loss_stage'),
                old_data.get('dep_date'),
                old_data.get('dep_length_days'),
                old_data.get('fiscal_year'),
                old_data.get('recruiting_year'),
                old_data.get('quarter'),
                old_data.get('ship_month'),
                old_data.get('emm_id'),
                old_data.get('ikrome_id'),
                old_data.get('rzone_id'),
                old_data.get('last_sync_at'),
                old_data.get('created_at'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            migrated += 1
        
        print(f"    ✅ Migrated {migrated} leads to new structure")
        
        # Step 4: Replace old table with new table
        print("  🔄 Replacing old leads table...")
        cursor.execute("DROP TABLE leads")
        cursor.execute("ALTER TABLE leads_new RENAME TO leads")
        print("    ✅ Leads table updated")
        
        # Step 5: Create indexes for performance
        print("  📊 Creating indexes...")
        indexes = [
            "CREATE INDEX idx_leads_current_stage ON leads(current_stage)",
            "CREATE INDEX idx_leads_fiscal_year ON leads(fiscal_year)",
            "CREATE INDEX idx_leads_rsid ON leads(rsid)",
            "CREATE INDEX idx_leads_brigade ON leads(brigade)",
            "CREATE INDEX idx_leads_battalion ON leads(battalion)",
            "CREATE INDEX idx_leads_station ON leads(station)",
            "CREATE INDEX idx_leads_recruiter ON leads(recruiter_id)",
            "CREATE INDEX idx_leads_lead_date ON leads(lead_date)",
            "CREATE INDEX idx_leads_enlistment_date ON leads(enlistment_date)",
            "CREATE INDEX idx_leads_loss_stage ON leads(loss_stage)"
        ]
        for idx_sql in indexes:
            cursor.execute(idx_sql)
        print("    ✅ Indexes created")
        
        # Step 6: Update funnel_transitions table
        print("  🔄 Updating funnel_transitions table...")
        cursor.execute("DROP TABLE IF EXISTS funnel_transitions")
        cursor.execute("""
            CREATE TABLE funnel_transitions (
                transition_id TEXT PRIMARY KEY,
                prid TEXT NOT NULL,
                from_stage TEXT,
                to_stage TEXT NOT NULL,
                transition_date TEXT NOT NULL,
                notes TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(prid) REFERENCES leads(prid)
            )
        """)
        cursor.execute("CREATE INDEX idx_transitions_prid ON funnel_transitions(prid)")
        cursor.execute("CREATE INDEX idx_transitions_date ON funnel_transitions(transition_date)")
        print("    ✅ Funnel transitions table updated")
        
        # Step 7: Update funnel_metrics table
        print("  🔄 Updating funnel_metrics table...")
        cursor.execute("DROP TABLE IF EXISTS funnel_metrics")
        cursor.execute("""
            CREATE TABLE funnel_metrics (
                metric_id TEXT PRIMARY KEY,
                fiscal_year INTEGER,
                rsid TEXT,
                
                -- Stage counts
                leads_count INTEGER DEFAULT 0,
                prospects_count INTEGER DEFAULT 0,
                appointments_made_count INTEGER DEFAULT 0,
                appointments_conducted_count INTEGER DEFAULT 0,
                tests_count INTEGER DEFAULT 0,
                test_passes_count INTEGER DEFAULT 0,
                enlistments_count INTEGER DEFAULT 0,
                ships_count INTEGER DEFAULT 0,
                losses_count INTEGER DEFAULT 0,
                
                -- Conversion rates (%)
                lead_to_prospect_rate REAL DEFAULT 0,
                prospect_to_appointment_rate REAL DEFAULT 0,
                appointment_made_to_conducted_rate REAL DEFAULT 0,
                appointment_to_test_rate REAL DEFAULT 0,
                test_to_pass_rate REAL DEFAULT 0,
                test_pass_to_enlistment_rate REAL DEFAULT 0,
                enlistment_to_ship_rate REAL DEFAULT 0,
                overall_conversion_rate REAL DEFAULT 0,
                
                -- Average days between stages
                avg_lead_to_prospect_days REAL DEFAULT 0,
                avg_prospect_to_appointment_days REAL DEFAULT 0,
                avg_appointment_to_test_days REAL DEFAULT 0,
                avg_test_to_enlistment_days REAL DEFAULT 0,
                avg_lead_to_enlistment_days REAL DEFAULT 0,
                avg_enlistment_to_ship_days REAL DEFAULT 0,
                
                -- No-show and attrition
                appointment_no_show_rate REAL DEFAULT 0,
                test_failure_rate REAL DEFAULT 0,
                loss_rate REAL DEFAULT 0,
                
                -- Metadata
                calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fiscal_year, rsid)
            )
        """)
        cursor.execute("CREATE INDEX idx_metrics_fy ON funnel_metrics(fiscal_year)")
        cursor.execute("CREATE INDEX idx_metrics_rsid ON funnel_metrics(rsid)")
        print("    ✅ Funnel metrics table updated")
        
        conn.commit()
        print()
        print("✅ Recruiting funnel stages migration completed!")
        print()
        print("New Recruiting Funnel Stages (Army Process):")
        print("  1. Lead - Initial contact/interest")
        print("  2. Prospect - Qualified and interested")
        print("  3. Appointment Made - Appointment scheduled")
        print("  4. Appointment Conducted - Appointment completed")
        print("  5. Test - ASVAB/physical test scheduled")
        print("  6. Test Pass - Passed all required tests")
        print("  7. Enlistment - Enlisted (signed contract)")
        print("  8. Ship - Shipped to basic training")
        print("  9. Loss - Lost from funnel at any stage")
        print()
        print("Additional Features:")
        print("  ✅ ASVAB score tracking")
        print("  ✅ Appointment no-show tracking")
        print("  ✅ Test type and location tracking")
        print("  ✅ Flash-to-bang metrics for each stage")
        print("  ✅ Conversion rate tracking")
        print("  ✅ Loss/attrition analysis")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_funnel_stages()
