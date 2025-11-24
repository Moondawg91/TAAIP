#!/usr/bin/env python3
"""
Database migration for calendar/scheduler and automated reporting system.
"""

import sqlite3
from datetime import datetime

DB_FILE = 'recruiting.db'

def run_migration():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🔄 Starting calendar/scheduler migration...\n")
    
    try:
        # ====================
        # CALENDAR EVENTS TABLE
        # ====================
        print("  ➤ Creating calendar_events table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                event_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT CHECK(event_type IN (
                    'event', 'marketing', 'meeting', 'deadline', 
                    'training', 'report_due', 'review', 'other'
                )),
                category TEXT,
                start_datetime TEXT NOT NULL,
                end_datetime TEXT NOT NULL,
                all_day INTEGER DEFAULT 0,
                location TEXT,
                attendees TEXT,
                status TEXT DEFAULT 'scheduled' CHECK(status IN (
                    'scheduled', 'in_progress', 'completed', 'cancelled', 'postponed'
                )),
                priority TEXT DEFAULT 'medium' CHECK(priority IN (
                    'low', 'medium', 'high', 'critical'
                )),
                recurrence_rule TEXT,
                recurrence_end_date TEXT,
                reminder_minutes INTEGER DEFAULT 60,
                linked_entity_type TEXT,
                linked_entity_id TEXT,
                created_by TEXT,
                assigned_to TEXT,
                notes TEXT,
                rsid TEXT,
                brigade TEXT,
                battalion TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("    ✅ calendar_events table created")
        
        # ====================
        # STATUS REPORTS TABLE
        # ====================
        print("  ➤ Creating status_reports table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_reports (
                report_id TEXT PRIMARY KEY,
                report_type TEXT CHECK(report_type IN (
                    'daily', 'weekly', 'monthly', 'quarterly', 'annual', 'custom'
                )),
                report_category TEXT CHECK(report_category IN (
                    'events', 'marketing', 'recruiting', 'projects', 
                    'leads', 'performance', 'overall'
                )),
                report_period_start TEXT NOT NULL,
                report_period_end TEXT NOT NULL,
                generated_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN (
                    'pending', 'generating', 'completed', 'failed', 'archived'
                )),
                report_data TEXT,
                summary TEXT,
                key_metrics TEXT,
                highlights TEXT,
                concerns TEXT,
                recommendations TEXT,
                auto_generated INTEGER DEFAULT 1,
                generated_by TEXT,
                reviewed_by TEXT,
                review_date TEXT,
                distribution_list TEXT,
                rsid TEXT,
                brigade TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("    ✅ status_reports table created")
        
        # ====================
        # REPORT SCHEDULES TABLE
        # ====================
        print("  ➤ Creating report_schedules table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_schedules (
                schedule_id TEXT PRIMARY KEY,
                schedule_name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                report_category TEXT NOT NULL,
                frequency TEXT CHECK(frequency IN (
                    'daily', 'weekly', 'monthly', 'quarterly', 'annual'
                )),
                day_of_week INTEGER,
                day_of_month INTEGER,
                time_of_day TEXT,
                enabled INTEGER DEFAULT 1,
                last_run_date TEXT,
                next_run_date TEXT,
                recipients TEXT,
                auto_distribute INTEGER DEFAULT 0,
                template_id TEXT,
                filters TEXT,
                rsid TEXT,
                brigade TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("    ✅ report_schedules table created")
        
        # ====================
        # ACTIVITY TIMELINE TABLE
        # ====================
        print("  ➤ Creating activity_timeline table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_timeline (
                activity_id TEXT PRIMARY KEY,
                activity_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                user_name TEXT,
                action TEXT NOT NULL,
                description TEXT,
                metadata TEXT,
                rsid TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("    ✅ activity_timeline table created")
        
        # ====================
        # NOTIFICATIONS TABLE
        # ====================
        print("  ➤ Creating notifications table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                notification_type TEXT CHECK(notification_type IN (
                    'reminder', 'alert', 'deadline', 'report_ready', 
                    'status_change', 'milestone', 'other'
                )),
                priority TEXT DEFAULT 'medium' CHECK(priority IN (
                    'low', 'medium', 'high', 'urgent'
                )),
                title TEXT NOT NULL,
                message TEXT,
                action_url TEXT,
                linked_entity_type TEXT,
                linked_entity_id TEXT,
                recipient_user_id TEXT,
                recipient_email TEXT,
                status TEXT DEFAULT 'unread' CHECK(status IN (
                    'unread', 'read', 'dismissed', 'actioned'
                )),
                delivery_method TEXT DEFAULT 'in_app' CHECK(delivery_method IN (
                    'in_app', 'email', 'sms', 'all'
                )),
                scheduled_send_time TEXT,
                sent_time TEXT,
                read_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("    ✅ notifications table created")
        
        # ====================
        # CREATE INDEXES
        # ====================
        print("  ➤ Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_start_date ON calendar_events(start_datetime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_type ON calendar_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_status ON calendar_events(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calendar_rsid ON calendar_events(rsid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_type ON status_reports(report_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_category ON status_reports(report_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_date ON status_reports(generated_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_timeline(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_entity ON activity_timeline(entity_type, entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status)")
        conn.commit()
        print("    ✅ Indexes created")
        
    except sqlite3.OperationalError as e:
        if "table already exists" in str(e) or "duplicate column name" in str(e):
            print("    ⚠️  Tables already exist, skipping...")
        else:
            raise
    
    conn.close()
    print("\n✅ Calendar/scheduler migration completed!\n")

if __name__ == '__main__':
    run_migration()
