#!/usr/bin/env python3
"""
Migration script for marketing engagement performance tracking.
Captures data from multiple platforms: Vantage, Sprinkler, EMM, MACs, social media, etc.
Tracks engagements, impressions, views (awareness), clicks, conversions.
"""

import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "recruiting.db")


def migrate():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Creating marketing engagement tables...")

    # Marketing campaigns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id TEXT UNIQUE NOT NULL,
        campaign_name TEXT NOT NULL,
        campaign_type TEXT NOT NULL,
        platform TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        status TEXT NOT NULL,
        target_audience TEXT,
        budget_allocated REAL,
        budget_spent REAL,
        objective TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Marketing engagement metrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_engagement_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        metric_date TEXT NOT NULL,
        impressions INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        reach INTEGER DEFAULT 0,
        engagements INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        video_views INTEGER DEFAULT 0,
        video_completion_rate REAL DEFAULT 0,
        click_through_rate REAL DEFAULT 0,
        engagement_rate REAL DEFAULT 0,
        cost_per_impression REAL DEFAULT 0,
        cost_per_click REAL DEFAULT 0,
        cost_per_engagement REAL DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        conversion_rate REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(campaign_id),
        UNIQUE(campaign_id, platform, metric_date)
    )
    """)

    # Social media posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_media_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id TEXT UNIQUE NOT NULL,
        campaign_id TEXT,
        platform TEXT NOT NULL,
        post_type TEXT NOT NULL,
        content TEXT,
        post_url TEXT,
        posted_date TEXT NOT NULL,
        impressions INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        engagements INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        reach INTEGER DEFAULT 0,
        engagement_rate REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(campaign_id)
    )
    """)

    # Platform integrations tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_platform_integrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_name TEXT UNIQUE NOT NULL,
        platform_type TEXT NOT NULL,
        api_endpoint TEXT,
        last_sync_date TEXT,
        sync_status TEXT DEFAULT 'pending',
        sync_frequency TEXT DEFAULT 'daily',
        is_active INTEGER DEFAULT 1,
        credentials_status TEXT DEFAULT 'not_configured',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Digital advertising table (Vantage, programmatic ads, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS digital_advertising (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_id TEXT UNIQUE NOT NULL,
        campaign_id TEXT,
        platform TEXT NOT NULL,
        ad_name TEXT NOT NULL,
        ad_type TEXT NOT NULL,
        ad_format TEXT,
        placement TEXT,
        start_date TEXT NOT NULL,
        end_date TEXT,
        impressions INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        cost REAL DEFAULT 0,
        cpm REAL DEFAULT 0,
        cpc REAL DEFAULT 0,
        ctr REAL DEFAULT 0,
        conversion_rate REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(campaign_id)
    )
    """)

    # Email marketing metrics (MACs, Sprinkler)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_marketing_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id TEXT UNIQUE NOT NULL,
        campaign_id TEXT,
        platform TEXT NOT NULL,
        email_subject TEXT NOT NULL,
        send_date TEXT NOT NULL,
        recipients INTEGER DEFAULT 0,
        delivered INTEGER DEFAULT 0,
        opened INTEGER DEFAULT 0,
        clicked INTEGER DEFAULT 0,
        bounced INTEGER DEFAULT 0,
        unsubscribed INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        open_rate REAL DEFAULT 0,
        click_rate REAL DEFAULT 0,
        click_to_open_rate REAL DEFAULT 0,
        bounce_rate REAL DEFAULT 0,
        conversion_rate REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(campaign_id)
    )
    """)

    # Marketing attribution table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marketing_attribution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT,
        campaign_id TEXT,
        platform TEXT NOT NULL,
        touchpoint_type TEXT NOT NULL,
        touchpoint_date TEXT NOT NULL,
        attribution_weight REAL DEFAULT 1.0,
        converted INTEGER DEFAULT 0,
        conversion_value REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(campaign_id)
    )
    """)

    # Insert default platform integrations
    now = datetime.now().isoformat()
    platforms = [
        ('Vantage', 'Digital Advertising', 'https://api.vantage.mil', 'pending', 'daily'),
        ('Sprinkler', 'Email Marketing', 'https://api.sprinkler.mil', 'pending', 'daily'),
        ('EMM', 'Marketing Analytics', 'https://api.emm.mil', 'pending', 'hourly'),
        ('MACs', 'Email Marketing', 'https://api.macs.mil', 'pending', 'daily'),
        ('Facebook', 'Social Media', 'https://graph.facebook.com', 'pending', 'hourly'),
        ('Instagram', 'Social Media', 'https://graph.instagram.com', 'pending', 'hourly'),
        ('Twitter/X', 'Social Media', 'https://api.twitter.com', 'pending', 'hourly'),
        ('LinkedIn', 'Social Media', 'https://api.linkedin.com', 'pending', 'daily'),
        ('YouTube', 'Video Platform', 'https://www.googleapis.com/youtube', 'pending', 'daily'),
        ('TikTok', 'Social Media', 'https://open-api.tiktok.com', 'pending', 'hourly'),
        ('Google Ads', 'Digital Advertising', 'https://googleads.googleapis.com', 'pending', 'daily'),
        ('Display Network', 'Digital Advertising', 'https://api.display.mil', 'pending', 'daily'),
    ]

    for platform_name, platform_type, api_endpoint, sync_status, sync_frequency in platforms:
        cursor.execute("""
        INSERT OR IGNORE INTO marketing_platform_integrations 
        (platform_name, platform_type, api_endpoint, sync_status, sync_frequency, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (platform_name, platform_type, api_endpoint, sync_status, sync_frequency, 1, now, now))

    conn.commit()
    print("✅ Marketing engagement tables created successfully")
    print(f"✅ Created {len(platforms)} platform integrations")
    
    # Show created tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'marketing%' OR name LIKE 'email%' OR name LIKE 'social%' OR name LIKE 'digital%'
        ORDER BY name
    """)
    tables = cursor.fetchall()
    print("\nMarketing-related tables:")
    for table in tables:
        print(f"  - {table[0]}")

    conn.close()


if __name__ == "__main__":
    migrate()
