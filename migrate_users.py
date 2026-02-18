#!/usr/bin/env python3
"""
Migration script for user management system.
Creates users, roles, and permissions tables with audit logging.
"""

import sqlite3
import os
from datetime import datetime
import hashlib
import secrets

DB_FILE = os.path.join(os.path.dirname(__file__), "recruiting.db")


def hash_password(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256"""
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def migrate():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Creating user management tables...")

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        rank TEXT,
        role TEXT NOT NULL DEFAULT 'analyst',
        tier INTEGER NOT NULL DEFAULT 3,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_login TEXT
    );
    """)

    # User permissions table (many-to-many)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        permission TEXT NOT NULL,
        granted_by INTEGER,
        granted_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (granted_by) REFERENCES users(id),
        UNIQUE(user_id, permission)
    )
    """)

    # Audit log for user management actions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        user_id INTEGER,
        performed_by INTEGER,
        details TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (performed_by) REFERENCES users(id)
    )
    """)

    # Create default admin user
    admin_salt = secrets.token_hex(16)
    admin_password = hash_password("admin123", admin_salt)
    now = datetime.now().isoformat()

    cursor.execute("""
    INSERT OR IGNORE INTO users 
    (username, email, password_hash, password_salt, first_name, last_name, rank, role, tier, start_date, end_date, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "admin",
        "admin@taaip.mil",
        admin_password,
        admin_salt,
        "Admin",
        "User",
        "O-6",
        "administrator",
        1,
        now,
        now,
        1,
        now,
        now
    ))

    admin_id = cursor.lastrowid or 1

    # Grant all permissions to admin
    admin_permissions = [
        'view_all_dashboards', 'view_analytics', 'upload_data', 'edit_data', 
        'delete_data', 'export_data', 'create_events', 'approve_events', 
        'edit_events', 'delete_events', 'manage_twg', 'manage_tdb', 
        'assign_roles', 'manage_users', 'delegate_permissions', 
        'edit_budget', 'approve_budget', 'system_admin'
    ]

    for perm in admin_permissions:
        cursor.execute("""
        INSERT OR IGNORE INTO user_permissions (user_id, permission, granted_by, granted_at)
        VALUES (?, ?, ?, ?)
        """, (admin_id, perm, admin_id, now))

    # Create sample users for testing
    sample_users = [
        ("jsmith", "jsmith@taaip.mil", "John", "Smith", "Capt", "manager", 2),
        ("mjohnson", "mjohnson@taaip.mil", "Mary", "Johnson", "Lt", "analyst", 3),
        ("rwilliams", "rwilliams@taaip.mil", "Robert", "Williams", "MSgt", "recruiter", 3),
    ]

    for username, email, first_name, last_name, rank, role, tier in sample_users:
        salt = secrets.token_hex(16)
        password = hash_password("password123", salt)
        cursor.execute("""
        INSERT OR IGNORE INTO users 
        (username, email, password_hash, password_salt, first_name, last_name, rank, role, tier, start_date, end_date, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, password, salt, first_name, last_name, rank, role, tier, now, now, 1, now, now))

    conn.commit()
    print("✅ User management tables created successfully")
    print(f"✅ Created default admin user (username: admin, password: admin123)")
    print(f"✅ Created {len(sample_users)} sample users (password: password123)")
    
    # Show created users
    cursor.execute("SELECT id, username, email, rank, role, tier FROM users")
    users = cursor.fetchall()
    print("\nUsers in database:")
    for user in users:
        print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Rank: {user[3]}, Role: {user[4]}, Tier: {user[5]}")

    conn.close()


if __name__ == "__main__":
    migrate()
