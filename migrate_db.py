"""
Database migration to add project management columns
Run this to upgrade your database schema
"""
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "data", "taaip.sqlite3")

def migrate_projects_table():
    """Add missing columns to projects table"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Get existing columns
    cur.execute("PRAGMA table_info(projects)")
    existing_columns = {row[1] for row in cur.fetchall()}
    
    print(f"Existing columns: {existing_columns}")
    
    # Columns to add
    new_columns = [
        ("funding_status", "TEXT DEFAULT 'requested'"),
        ("funding_amount", "REAL DEFAULT 0.0"),
        ("spent_amount", "REAL DEFAULT 0.0"),
        ("percent_complete", "INTEGER DEFAULT 0"),
        ("risk_level", "TEXT"),
        ("next_milestone", "TEXT"),
        ("blockers", "TEXT"),
        ("is_archived", "INTEGER DEFAULT 0"),
        ("archived_at", "TEXT"),
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            try:
                cur.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Column {col_name} might already exist: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Database migration completed!")

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_projects_table()
