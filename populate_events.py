#!/usr/bin/env python3
"""
Seed sample events to drive ML predictions and frontend visuals.
Safe to run multiple times (uses INSERT OR IGNORE by event_id).
"""

import sqlite3
import uuid
from datetime import datetime, timedelta

DB_FILE = 'recruiting.db'


def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def seed_events():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row

    # Ensure base events table exists (align with taaip_service schema)
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

    now = datetime.now()
    events = [
        {
            'name': 'Dallas HS Career Fair',
            'type': 'career_fair',
            'location': 'Dallas, TX',
            'start': now + timedelta(days=7),
            'end': now + timedelta(days=7, hours=4),
            'budget': 7500,
            'team': 6,
            'principles': 'Lead generation, school partnership',
            'status': 'planned',
            'category': 'lead_generating',
        },
        {
            'name': 'Houston Community Festival',
            'type': 'community_event',
            'location': 'Houston, TX',
            'start': now + timedelta(days=14),
            'end': now + timedelta(days=14, hours=6),
            'budget': 5000,
            'team': 5,
            'principles': 'Community engagement, brand awareness',
            'status': 'planned',
            'category': 'community_engagement',
        },
        {
            'name': 'Austin Tech Job Fair',
            'type': 'job_fair',
            'location': 'Austin, TX',
            'start': now + timedelta(days=21),
            'end': now + timedelta(days=21, hours=8),
            'budget': 12000,
            'team': 8,
            'principles': 'Lead generation, STEM focus',
            'status': 'planned',
            'category': 'lead_generating',
        },
        {
            'name': 'San Antonio College Outreach',
            'type': 'campus_outreach',
            'location': 'San Antonio, TX',
            'start': now + timedelta(days=10),
            'end': now + timedelta(days=10, hours=3),
            'budget': 4000,
            'team': 4,
            'principles': 'Shaping, partnerships',
            'status': 'planned',
            'category': 'shaping',
        },
        {
            'name': 'DFW Social Media Campaign Launch',
            'type': 'digital_campaign',
            'location': 'Fort Worth, TX',
            'start': now + timedelta(days=3),
            'end': now + timedelta(days=33),
            'budget': 9000,
            'team': 3,
            'principles': 'Brand awareness, digital targeting',
            'status': 'planned',
            'category': 'brand_awareness',
        },
    ]

    rows = []
    for e in events:
        eid = f"evt_{uuid.uuid4().hex[:10]}"
        rows.append(
            (
                eid,
                e['name'],
                e['type'],
                e['location'],
                e['start'].isoformat(),
                e['end'].isoformat(),
                float(e['budget']),
                int(e['team']),
                e['principles'],
                e['status'],
                now.isoformat(),
                now.isoformat(),
                e['category'],  # optional column
            )
        )

    # Determine if event_type_category column exists
    has_category = column_exists(cursor, 'events', 'event_type_category')

    if has_category:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO events (
                event_id, name, type, location, start_date, end_date, budget,
                team_size, targeting_principles, status, created_at, updated_at,
                event_type_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    else:
        cursor.executemany(
            """
            INSERT OR IGNORE INTO events (
                event_id, name, type, location, start_date, end_date, budget,
                team_size, targeting_principles, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [r[:-1] for r in rows],  # drop category value
        )

    conn.commit()

    # Fetch inserted IDs to generate predictions
    cursor.execute("SELECT event_id FROM events ORDER BY created_at DESC LIMIT ?", (len(events),))
    event_ids = [row[0] for row in cursor.fetchall()]

    # Generate predictions for each event (stores in ml_predictions and updates events)
    from ml_prediction_engine import generate_event_prediction

    success = 0
    for eid in event_ids:
        try:
            pred = generate_event_prediction(eid)
            if 'error' not in pred:
                success += 1
        except Exception as ex:
            print(f"⚠️  Prediction failed for {eid}: {ex}")

    print(f"✅ Seeded {len(events)} events; generated {success} predictions")
    conn.close()


if __name__ == '__main__':
    seed_events()
