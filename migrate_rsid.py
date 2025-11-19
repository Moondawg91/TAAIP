"""
Database Migration: Add RSID organizational hierarchy columns
Enables filtering by Brigade, Battalion, and Station
"""
import sqlite3
import sys
from pathlib import Path
import os

# Get absolute path to database
SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = SCRIPT_DIR / "data" / "taaip.sqlite3"

print(f"Database path: {DB_PATH}")
if not DB_PATH.exists():
    print(f"❌ Database not found at {DB_PATH}")
    sys.exit(1)


def migrate_add_rsid_columns():
    """Add RSID hierarchy columns to projects, events, and tasks tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Starting RSID hierarchy migration...")
    
    # Get existing columns for projects table
    cursor.execute("PRAGMA table_info(projects)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    # Add RSID columns to projects table
    rsid_columns = {
        "rsid": "TEXT",  # Full RSID: "1BDE-1BN-1-1"
        "brigade": "TEXT",  # Brigade code: "1BDE"
        "battalion": "TEXT",  # Battalion code: "1BN"
        "station": "TEXT",  # Station code: "1-1"
    }
    
    for col_name, col_type in rsid_columns.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ Added column 'projects.{col_name}'")
        else:
            print(f"  ⏭️  Column 'projects.{col_name}' already exists")
    
    # Add RSID columns to events table
    cursor.execute("PRAGMA table_info(events)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in rsid_columns.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE events ADD COLUMN {col_name} {col_type}")
            print(f"  ✅ Added column 'events.{col_name}'")
        else:
            print(f"  ⏭️  Column 'events.{col_name}' already exists")
    
    # Create index for faster RSID queries
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_rsid ON projects(rsid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_brigade ON projects(brigade)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_rsid ON events(rsid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_brigade ON events(brigade)")
        print("  ✅ Created RSID indexes")
    except Exception as e:
        print(f"  ⚠️  Index creation: {e}")
    
    conn.commit()
    conn.close()
    
    print("✅ RSID hierarchy migration completed!")
    print("\nNow you can filter data by:")
    print("  - Brigade level: rsid='1BDE'")
    print("  - Battalion level: rsid='1BDE-1BN'")
    print("  - Station level: rsid='1BDE-1BN-1-1'")


if __name__ == "__main__":
    try:
        migrate_add_rsid_columns()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
