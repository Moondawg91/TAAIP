"""
Database migration to add prospects, applicants, and future soldiers tables
Run this script to update the database schema
"""

import sqlite3
from datetime import datetime

def migrate_database():
    conn = sqlite3.connect("data/recruiting.db")
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Update leads table with new fields
    print("1. Updating leads table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                middle_name TEXT,
                date_of_birth TEXT,
                age INTEGER,
                education_code TEXT,
                phone_number TEXT,
                address TEXT,
                cbsa_code TEXT,
                lead_source TEXT,
                prid TEXT,
                asvab_score INTEGER,
                campaign_source TEXT,
                received_at TEXT,
                predicted_probability REAL,
                score INTEGER,
                recommendation TEXT,
                converted INTEGER DEFAULT 0,
                raw_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy existing data
        cursor.execute("""
            INSERT INTO leads_new (
                id, lead_id, age, cbsa_code, campaign_source,
                received_at, predicted_probability, score,
                recommendation, converted, raw_json
            )
            SELECT 
                id, lead_id, age, cbsa_code, campaign_source,
                received_at, predicted_probability, score,
                recommendation, converted, raw_json
            FROM leads
        """)
        
        cursor.execute("DROP TABLE leads")
        cursor.execute("ALTER TABLE leads_new RENAME TO leads")
        print("   ✓ Leads table updated")
    except Exception as e:
        print(f"   ⚠ Leads table already updated or error: {e}")
    
    # Create prospects table
    print("2. Creating prospects table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            date_of_birth TEXT NOT NULL,
            age INTEGER,
            education_code TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            address TEXT,
            cbsa_code TEXT,
            lead_source TEXT NOT NULL,
            prid TEXT NOT NULL,
            asvab_score INTEGER,
            prospect_status TEXT NOT NULL,
            last_contact_date TEXT,
            recruiter_assigned TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Prospects table created")
    
    # Create applicants table
    print("3. Creating applicants table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            date_of_birth TEXT NOT NULL,
            age INTEGER,
            education_code TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            address TEXT,
            cbsa_code TEXT,
            lead_source TEXT NOT NULL,
            prid TEXT NOT NULL,
            asvab_score INTEGER,
            application_date TEXT NOT NULL,
            applicant_status TEXT NOT NULL,
            meps_scheduled_date TEXT,
            recruiter_assigned TEXT,
            mos_preference TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Applicants table created")
    
    # Create future_soldiers table
    print("4. Creating future_soldiers table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS future_soldiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fs_id TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            date_of_birth TEXT NOT NULL,
            age INTEGER,
            education_code TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            address TEXT,
            cbsa_code TEXT,
            lead_source TEXT NOT NULL,
            prid TEXT NOT NULL,
            asvab_score INTEGER,
            contract_date TEXT NOT NULL,
            ship_date TEXT NOT NULL,
            mos_assigned TEXT NOT NULL,
            future_soldier_status TEXT NOT NULL,
            recruiter_assigned TEXT,
            unit_assignment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Future soldiers table created")
    
    # Create indexes for better query performance
    print("5. Creating indexes...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_prid ON leads(prid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prospects_prid ON prospects(prid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(prospect_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applicants_prid ON applicants(prid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applicants_status ON applicants(applicant_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fs_prid ON future_soldiers(prid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fs_ship_date ON future_soldiers(ship_date)")
        print("   ✓ Indexes created")
    except Exception as e:
        print(f"   ⚠ Some indexes already exist: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database migration completed successfully!")
    print("\nNew tables added:")
    print("  - prospects")
    print("  - applicants")
    print("  - future_soldiers")
    print("\nLeads table updated with:")
    print("  - first_name, last_name, middle_name")
    print("  - date_of_birth, education_code")
    print("  - phone_number, address")
    print("  - lead_source, prid, asvab_score")

if __name__ == "__main__":
    migrate_database()
