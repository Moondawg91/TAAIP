#!/usr/bin/env python3
"""
Populate sample calendar events, schedules, and reports.
"""

import sqlite3
import secrets
from datetime import datetime, timedelta
import random
import json

DB_FILE = 'recruiting.db'

# Sample data
EVENT_TYPES = ['event', 'marketing', 'meeting', 'deadline', 'training', 'report_due', 'review']
PRIORITIES = ['low', 'medium', 'high', 'critical']
STATUSES = ['scheduled', 'in_progress', 'completed', 'cancelled', 'postponed']
LOCATIONS = [
    'Fort Sam Houston', 'Fort Cavazos', 'Fort Bliss', 'JBSA Lackland',
    'Dallas Recruiting Station', 'Houston Recruiting Station', 'Austin Recruiting Station',
    'San Antonio Convention Center', 'Virtual Meeting', 'Zoom Conference'
]
BRIGADES = ['1BDE', '2BDE', '3BDE', '4BDE', '5BDE']
RSIDS = ['RSID_001', 'RSID_002', 'RSID_003', 'RSID_004', 'RSID_005']

EVENT_TITLES = [
    'Career Fair - High School', 'College Football Game Booth', 'Community Festival',
    'STEM Fair Participation', 'Weekly Team Meeting', 'Monthly Planning Session',
    'Quarterly Review Meeting', 'Marketing Campaign Kickoff', 'Social Media Strategy Session',
    'Training: Lead Qualification', 'Training: TAAIP Platform', 'Budget Planning Meeting',
    'Performance Review Deadline', 'Monthly Report Due', 'Quarterly Report Due',
    'Annual Planning Session', 'Partnership Meeting - University', 'Recruiter Conference',
    'Youth Sports Sponsorship Event', 'Music Festival Booth', 'Job Fair - Veterans',
    'Radio Partnership Planning', 'Digital Billboard Campaign Review', 'Email Campaign Launch',
    'Lead Follow-up Deadline', 'Contract Review Meeting', 'Funnel Optimization Workshop'
]

def populate_sample_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🔄 Populating calendar sample data...\n")
    
    # ==================
    # CALENDAR EVENTS
    # ==================
    print("  ➤ Adding calendar events...")
    
    base_date = datetime.now()
    events_created = 0
    
    for i in range(50):
        # Create events spread across past 30 days to future 60 days
        days_offset = random.randint(-30, 60)
        start_datetime = base_date + timedelta(days=days_offset, hours=random.randint(8, 17))
        end_datetime = start_datetime + timedelta(hours=random.randint(1, 4))
        
        event_type = random.choice(EVENT_TYPES)
        priority = random.choice(PRIORITIES)
        
        # Set status based on date
        if start_datetime < base_date:
            status = random.choice(['completed', 'completed', 'completed', 'cancelled'])
        elif start_datetime < base_date + timedelta(days=1):
            status = 'in_progress'
        else:
            status = 'scheduled'
        
        event_id = f"cal_{secrets.token_hex(6)}"
        title = random.choice(EVENT_TITLES)
        
        description = f"{'High priority' if priority in ['high', 'critical'] else 'Standard'} {event_type} event."
        
        cursor.execute("""
            INSERT INTO calendar_events (
                event_id, title, description, event_type, category,
                start_datetime, end_datetime, all_day, location,
                status, priority, reminder_minutes,
                created_by, assigned_to, rsid, brigade
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            title,
            description,
            event_type,
            'recruiting' if event_type in ['event', 'marketing'] else 'operations',
            start_datetime.isoformat(),
            end_datetime.isoformat(),
            0,
            random.choice(LOCATIONS),
            status,
            priority,
            random.choice([30, 60, 120, 1440]),  # 30min, 1hr, 2hr, 1day
            'SSG Johnson',
            random.choice(['SSG Smith', 'SSG Williams', 'SSG Brown', 'SSG Davis']),
            random.choice(RSIDS),
            random.choice(BRIGADES)
        ))
        events_created += 1
    
    conn.commit()
    print(f"    ✅ Added {events_created} calendar events")
    
    # ==================
    # STATUS REPORTS
    # ==================
    print("  ➤ Generating status reports...")
    
    report_types = ['daily', 'weekly', 'monthly', 'quarterly']
    report_categories = ['events', 'marketing', 'recruiting', 'overall']
    reports_created = 0
    
    for report_type in report_types:
        for report_category in report_categories:
            # Create 3 historical reports for each type/category
            for j in range(3):
                if report_type == 'daily':
                    days_back = (j + 1) * 1
                    period_days = 1
                elif report_type == 'weekly':
                    days_back = (j + 1) * 7
                    period_days = 7
                elif report_type == 'monthly':
                    days_back = (j + 1) * 30
                    period_days = 30
                else:  # quarterly
                    days_back = (j + 1) * 90
                    period_days = 90
                
                generated_date = base_date - timedelta(days=days_back)
                period_start = generated_date - timedelta(days=period_days)
                period_end = generated_date
                
                report_id = f"rpt_{secrets.token_hex(6)}"
                
                # Generate some metrics
                key_metrics = {
                    'events': {
                        'total_events': random.randint(5, 50),
                        'completed_events': random.randint(3, 40),
                        'cancelled_events': random.randint(0, 5)
                    },
                    'marketing': {
                        'total_nominations': random.randint(2, 20),
                        'approved': random.randint(1, 15),
                        'avg_predicted_roi': round(random.uniform(1.0, 2.5), 2)
                    },
                    'recruiting': {
                        'total_leads': random.randint(50, 500),
                        'enlistments': random.randint(5, 50),
                        'ships': random.randint(3, 40)
                    }
                }
                
                summary = f"{report_type.upper()} {report_category.upper()} Report - Generated {generated_date.strftime('%Y-%m-%d')}"
                
                cursor.execute("""
                    INSERT INTO status_reports (
                        report_id, report_type, report_category,
                        report_period_start, report_period_end, generated_date,
                        status, summary, key_metrics, rsid, brigade
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_id,
                    report_type,
                    report_category,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    generated_date.isoformat(),
                    'completed',
                    summary,
                    json.dumps(key_metrics),
                    random.choice(RSIDS),
                    random.choice(BRIGADES)
                ))
                reports_created += 1
    
    conn.commit()
    print(f"    ✅ Added {reports_created} status reports")
    
    # ==================
    # REPORT SCHEDULES
    # ==================
    print("  ➤ Creating report schedules...")
    
    schedules = [
        {'name': 'Daily Events Report', 'type': 'daily', 'category': 'events', 'frequency': 'daily', 'time': '08:00'},
        {'name': 'Weekly Marketing Report', 'type': 'weekly', 'category': 'marketing', 'frequency': 'weekly', 'time': '09:00'},
        {'name': 'Monthly Recruiting Report', 'type': 'monthly', 'category': 'recruiting', 'frequency': 'monthly', 'time': '10:00'},
        {'name': 'Monthly Overall Report', 'type': 'monthly', 'category': 'overall', 'frequency': 'monthly', 'time': '11:00'},
        {'name': 'Quarterly Performance Report', 'type': 'quarterly', 'category': 'overall', 'frequency': 'quarterly', 'time': '14:00'},
    ]
    
    schedules_created = 0
    
    for schedule in schedules:
        schedule_id = f"sch_{secrets.token_hex(6)}"
        
        cursor.execute("""
            INSERT INTO report_schedules (
                schedule_id, schedule_name, report_type, report_category,
                frequency, time_of_day, enabled, auto_distribute,
                recipients, rsid, brigade
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule_id,
            schedule['name'],
            schedule['type'],
            schedule['category'],
            schedule['frequency'],
            schedule['time'],
            1,
            1,
            'battalion_staff@army.mil,brigade_staff@army.mil',
            random.choice(RSIDS),
            random.choice(BRIGADES)
        ))
        schedules_created += 1
    
    conn.commit()
    print(f"    ✅ Added {schedules_created} report schedules")
    
    # ==================
    # NOTIFICATIONS
    # ==================
    print("  ➤ Creating notifications...")
    
    notifications_created = 0
    
    # Create notifications for upcoming events
    cursor.execute("""
        SELECT event_id, title, start_datetime, priority
        FROM calendar_events
        WHERE start_datetime > datetime('now')
        AND status = 'scheduled'
        ORDER BY start_datetime
        LIMIT 10
    """)
    
    upcoming_events = cursor.fetchall()
    
    for event in upcoming_events:
        notification_id = f"not_{secrets.token_hex(6)}"
        
        # Map event priority to notification priority
        event_priority = event[3]
        notification_priority = 'urgent' if event_priority == 'critical' else event_priority
        
        cursor.execute("""
            INSERT INTO notifications (
                notification_id, notification_type, priority, title, message,
                linked_entity_type, linked_entity_id, status, delivery_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            notification_id,
            'reminder',
            notification_priority,  # Use mapped priority
            f"Reminder: {event[1]}",
            f"Your event '{event[1]}' is scheduled for {event[2]}",
            'calendar_event',
            event[0],  # event_id
            'unread',
            'in_app'
        ))
        notifications_created += 1
    
    conn.commit()
    print(f"    ✅ Added {notifications_created} notifications")
    
    conn.close()
    
    print(f"\n✅ Calendar sample data population complete!")
    print(f"\nSummary:")
    print(f"  • {events_created} calendar events")
    print(f"  • {reports_created} status reports")
    print(f"  • {schedules_created} report schedules")
    print(f"  • {notifications_created} notifications")

if __name__ == '__main__':
    populate_sample_data()
