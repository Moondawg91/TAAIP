"""
Configure User Access Levels (Tier 1-4 System)
"""

import sqlite3
from datetime import datetime

def configure_user_access():
    """Set up user access levels in the database"""
    
    conn = sqlite3.connect('data/taaip.sqlite3')
    cursor = conn.cursor()
    
    # Create table if doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_access (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            dod_id TEXT UNIQUE NOT NULL,
            access_level TEXT DEFAULT 'tier_1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM user_access")
    
    # Sample users with different access levels
    users = [
        # Tier 4 - Full System Administrators
        ('admin001', 'COL Sarah Mitchell', 'sarah.mitchell@army.mil', 'DOD1234567', 'tier_4'),
        ('admin002', 'MAJ Robert Chen', 'robert.chen@army.mil', 'DOD2345678', 'tier_4'),
        
        # Tier 3 - Editors (Battalion/Company Leadership)
        ('editor001', 'CPT James Rodriguez', 'james.rodriguez@army.mil', 'DOD3456789', 'tier_3'),
        ('editor002', 'CPT Emily Thompson', 'emily.thompson@army.mil', 'DOD4567890', 'tier_3'),
        ('editor003', '1SG Michael Davis', 'michael.davis@army.mil', 'DOD5678901', 'tier_3'),
        ('editor004', 'SFC Jennifer Martinez', 'jennifer.martinez@army.mil', 'DOD6789012', 'tier_3'),
        
        # Tier 2 - Standard Users (Recruiters, Station Commanders)
        ('user001', 'SSG David Wilson', 'david.wilson@army.mil', 'DOD7890123', 'tier_2'),
        ('user002', 'SGT Ashley Johnson', 'ashley.johnson@army.mil', 'DOD8901234', 'tier_2'),
        ('user003', 'SGT Marcus Brown', 'marcus.brown@army.mil', 'DOD9012345', 'tier_2'),
        ('user004', 'SSG Lisa Anderson', 'lisa.anderson@army.mil', 'DOD0123456', 'tier_2'),
        ('user005', 'SGT Kevin Taylor', 'kevin.taylor@army.mil', 'DOD1234560', 'tier_2'),
        ('user006', 'SSG Maria Garcia', 'maria.garcia@army.mil', 'DOD2345601', 'tier_2'),
        ('user007', 'SGT Christopher Lee', 'christopher.lee@army.mil', 'DOD3456012', 'tier_2'),
        ('user008', 'SSG Amanda White', 'amanda.white@army.mil', 'DOD4560123', 'tier_2'),
        
        # Tier 1 - View Only (Support Staff, Analysts)
        ('viewer001', 'SPC John Harris', 'john.harris@army.mil', 'DOD5601234', 'tier_1'),
        ('viewer002', 'SPC Rachel Clark', 'rachel.clark@army.mil', 'DOD6012345', 'tier_1'),
        ('viewer003', 'SPC Daniel Lewis', 'daniel.lewis@army.mil', 'DOD7123456', 'tier_1'),
        ('viewer004', 'SPC Michelle Walker', 'michelle.walker@army.mil', 'DOD8234567', 'tier_1'),
    ]
    
    # Insert users
    for user in users:
        cursor.execute("""
            INSERT INTO user_access (user_id, name, email, dod_id, access_level)
            VALUES (?, ?, ?, ?, ?)
        """, user)
    
    conn.commit()
    
    # Display summary
    print(f"\n✅ Successfully configured {len(users)} users with access levels")
    print("\nAccess Level Distribution:")
    print("-" * 80)
    
    for tier in ['tier_4', 'tier_3', 'tier_2', 'tier_1']:
        cursor.execute("SELECT COUNT(*) FROM user_access WHERE access_level = ?", (tier,))
        count = cursor.fetchone()[0]
        tier_name = {
            'tier_4': 'Tier 4 - Administrator',
            'tier_3': 'Tier 3 - Editor',
            'tier_2': 'Tier 2 - Standard User',
            'tier_1': 'Tier 1 - View Only'
        }[tier]
        print(f"{tier_name:<30} {count:>3} users")
    
    print("\nSample Users by Access Level:")
    print("-" * 80)
    
    for tier in ['tier_4', 'tier_3', 'tier_2', 'tier_1']:
        cursor.execute("""
            SELECT name, dod_id, access_level 
            FROM user_access 
            WHERE access_level = ? 
            LIMIT 2
        """, (tier,))
        users_sample = cursor.fetchall()
        
        if users_sample:
            tier_label = tier.replace('_', ' ').title()
            print(f"\n{tier_label}:")
            for user in users_sample:
                print(f"  • {user[0]:<25} (DOD ID: {user[1]})")
    
    conn.close()

if __name__ == "__main__":
    configure_user_access()
