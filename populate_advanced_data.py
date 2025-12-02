#!/usr/bin/env python3
"""
Populate sample data for event performance predictions, G2 zones, and EMM historical data.
"""

import sqlite3
import uuid
import random
from datetime import datetime, timedelta

DB_FILE = '/opt/TAAIP/recruiting.db'

def populate_sample_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🔄 Populating sample data...\n")
    
    # ====================
    # 1. POPULATE EMM HISTORICAL DATA
    # ====================
    print("  ➤ Adding EMM historical event data...")
    
    event_types = ['lead_generating', 'shaping', 'brand_awareness', 'community_engagement']
    locations = ['Dallas, TX', 'Houston, TX', 'San Antonio, TX', 'Austin, TX', 'Fort Worth, TX']
    venues = ['High School', 'Community Center', 'Mall', 'College Campus', 'Sports Arena']
    weather_conds = ['Clear', 'Rainy', 'Partly Cloudy', 'Hot', 'Mild']
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    emm_records = []
    for i in range(50):  # 50 historical events for ML training
        event_type = random.choice(event_types)
        budget = random.randint(2000, 15000)
        team_size = random.randint(3, 12)
        
        # Generate realistic outcomes based on event type
        if event_type == 'lead_generating':
            leads = int(budget / 100) + random.randint(-20, 40)
            conversions = int(leads * random.uniform(0.05, 0.15))
        elif event_type == 'shaping':
            leads = int(budget / 150) + random.randint(-10, 25)
            conversions = int(leads * random.uniform(0.03, 0.08))
        elif event_type == 'brand_awareness':
            leads = int(budget / 200) + random.randint(-5, 15)
            conversions = int(leads * random.uniform(0.02, 0.05))
        else:  # community_engagement
            leads = int(budget / 180) + random.randint(-8, 20)
            conversions = int(leads * random.uniform(0.03, 0.07))
        
        roi = (conversions * 50000 - budget) / budget if budget > 0 else 0  # Assume $50k value per conversion
        cost_per_lead = budget / leads if leads > 0 else 0
        
        emm_records.append((
            f"emm_{uuid.uuid4().hex[:12]}",
            f"evt_{uuid.uuid4().hex[:8]}",
            event_type,
            (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat(),
            random.choice(locations),
            budget,
            team_size,
            'Military age youth',
            random.choice(weather_conds),
            random.choice(days),
            random.choice(months),
            random.randint(0, 3),
            random.randint(1000, 50000),
            random.randint(500, 5000),
            random.choice(['Low', 'Medium', 'High']),
            random.choice(venues),
            max(0, leads),
            max(0, conversions),
            round(roi, 2),
            round(cost_per_lead, 2),
            round(random.uniform(0.4, 0.9), 2),
            round(random.uniform(0.5, 0.95), 2),
            f"zone_{random.randint(1, 10)}",
            f"RSID_00{random.randint(1, 5)}",
            f"{random.randint(1, 3)}BDE",
            datetime.now().isoformat()
        ))
    
    cursor.executemany("""
        INSERT OR REPLACE INTO emm_historical_data (
            data_id, event_id, event_type_category, event_date, location,
            budget, team_size, target_audience, weather_conditions, day_of_week,
            month, competing_events, social_media_reach, email_invites_sent,
            partnership_level, venue_type, leads_generated, conversions, roi,
            cost_per_lead, engagement_score, follow_up_rate, zone_id, rsid,
            brigade, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, emm_records)
    
    print(f"    ✅ Added {len(emm_records)} EMM historical records")
    
    # ====================
    # 2. UPDATE EVENTS WITH PREDICTIONS
    # ====================
    print("  ➤ Generating ML predictions for existing events...")
    
    cursor.execute("SELECT event_id FROM events LIMIT 10")
    event_ids = [row[0] for row in cursor.fetchall()]
    
    from ml_prediction_engine import generate_event_prediction
    
    predictions_count = 0
    for event_id in event_ids:
        try:
            prediction = generate_event_prediction(event_id)
            if 'error' not in prediction:
                predictions_count += 1
        except Exception as e:
            print(f"    ⚠️  Failed to predict {event_id}: {str(e)}")
    
    print(f"    ✅ Generated {predictions_count} event predictions")
    
    # ====================
    # 3. POPULATE G2 ZONE PERFORMANCE
    # ====================
    print("  ➤ Adding G2 Zone performance data...")
    
    zones = [
        ("zone_1", "Dallas-Fort Worth Metro", "North Texas", 7000000, 1200000),
        ("zone_2", "Houston Metro", "Southeast Texas", 6500000, 1100000),
        ("zone_3", "San Antonio Metro", "South Central Texas", 2500000, 450000),
        ("zone_4", "Austin Metro", "Central Texas", 2200000, 380000),
        ("zone_5", "El Paso Region", "West Texas", 850000, 150000),
        ("zone_6", "Corpus Christi Region", "Coastal Texas", 450000, 80000),
        ("zone_7", "Lubbock Region", "West Texas", 320000, 55000),
        ("zone_8", "Tyler-Longview", "East Texas", 280000, 48000),
        ("zone_9", "Waco Region", "Central Texas", 270000, 46000),
        ("zone_10", "Amarillo Region", "Panhandle", 265000, 45000),
    ]
    
    g2_records = []
    for zone_id, zone_name, geo_area, pop, mil_age_pop in zones:
        # Generate realistic performance metrics
        lead_count = random.randint(150, 800)
        qualified_leads = int(lead_count * random.uniform(0.45, 0.75))
        conversion_count = int(qualified_leads * random.uniform(0.15, 0.35))
        enlistment_count = int(conversion_count * random.uniform(0.60, 0.85))
        
        qualification_rate = qualified_leads / lead_count if lead_count > 0 else 0
        conversion_rate = conversion_count / qualified_leads if qualified_leads > 0 else 0
        enlistment_rate = enlistment_count / conversion_count if conversion_count > 0 else 0
        
        # Market penetration = leads / military age population
        market_penetration = (lead_count / mil_age_pop) if mil_age_pop > 0 else 0
        
        # Competitive index (0-1, lower is better - less competition)
        competitive_index = random.uniform(0.3, 0.8)
        
        trend = random.choice(['up', 'up', 'stable', 'down'])  # More "up" trends
        
        lead_sources = ['Website', 'Social Media', 'Referral', 'Event', 'Partnership']
        mos_options = ['11B Infantry', '25B IT Specialist', '68W Medic', '15T Helicopter Repair', '92Y Supply']
        
        g2_records.append((
            zone_id,
            zone_name,
            geo_area,
            pop,
            mil_age_pop,
            'FY2025 Q1',
            2025,
            lead_count,
            qualified_leads,
            conversion_count,
            enlistment_count,
            round(qualification_rate, 3),
            round(conversion_rate, 3),
            round(enlistment_rate, 3),
            round(random.uniform(60, 85), 1),
            round(random.uniform(30, 90), 1),
            random.choice(lead_sources),
            random.choice(mos_options),
            round(market_penetration, 4),
            round(competitive_index, 3),
            trend,
            f"RSID_00{random.randint(1, 5)}",
            f"{random.randint(1, 3)}BDE",
            f"BN_{random.randint(1, 8)}",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    
    cursor.executemany("""
        INSERT OR REPLACE INTO g2_zone_performance (
            zone_id, zone_name, geographic_area, population, military_age_population,
            current_quarter, fiscal_year, lead_count, qualified_leads, conversion_count,
            enlistment_count, qualification_rate, conversion_rate, enlistment_rate,
            avg_lead_quality_score, avg_days_to_conversion, top_lead_source, top_mos,
            market_penetration_rate, competitive_index, trend_direction, rsid, brigade,
            battalion, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, g2_records)
    
    print(f"    ✅ Added {len(g2_records)} G2 zone records")
    
    # ====================
    # 4. POPULATE MARKETING NOMINATIONS
    # ====================
    print("  ➤ Adding marketing nominations...")
    
    nominations = []
    nomination_types = ['event', 'campaign', 'sponsorship', 'partnership', 'digital']
    nomination_descriptions = [
        'High school career fair sponsorship',
        'College football game recruiting booth',
        'Community festival participation',
        'Social media advertising campaign',
        'Local radio station partnership',
        'Youth sports league sponsorship',
        'Music festival vendor booth',
        'STEM fair partnership',
        'Job fair participation',
        'Digital billboard campaign'
    ]
    
    for i in range(15):
        nom_type = random.choice(nomination_types)
        estimated_cost = random.randint(1000, 10000)
        
        # Generate prediction
        from ml_prediction_engine import TAIPPredictionEngine
        engine = TAIPPredictionEngine()
        
        prediction = engine.predict_event_performance(
            event_type_category=nom_type,
            budget=estimated_cost,
            team_size=random.randint(3, 8),
            location=random.choice(locations),
            target_audience='Military age youth',
            month=random.choice(months),
            day_of_week=random.choice(days),
            rsid=f"RSID_00{random.randint(1, 5)}"
        )
        
        status = random.choice(['submitted', 'under_review', 'approved', 'rejected'])
        
        nominations.append((
            f"nom_{uuid.uuid4().hex[:12]}",
            datetime.now().isoformat(),
            f"REC{random.randint(1000, 9999)}",
            f"SSG {random.choice(['Johnson', 'Smith', 'Williams', 'Brown', 'Davis'])}",
            nom_type,
            random.choice(nomination_descriptions),
            'Military age youth 18-24',
            random.randint(5000, 50000),
            estimated_cost,
            prediction['predicted_leads'],
            prediction['predicted_roi'],
            prediction['confidence_score'],
            status,
            datetime.now().isoformat() if status in ['approved', 'rejected'] else None,
            f"COL {random.choice(['Anderson', 'Martinez', 'Garcia'])}",
            0,  # actual_leads
            0,  # actual_conversions
            0.0,  # actual_roi
            0.0,  # leads_variance
            0.0,  # roi_variance
            f"RSID_00{random.randint(1, 5)}",
            f"{random.randint(1, 3)}BDE",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    
    cursor.executemany("""
        INSERT OR REPLACE INTO marketing_nominations (
            nomination_id, nomination_date, nominator_id, nominator_name, nomination_type,
            description, target_audience, estimated_reach, estimated_cost,
            predicted_leads, predicted_roi, prediction_confidence, status, approval_date,
            approver_id, actual_leads, actual_conversions, actual_roi, leads_variance,
            roi_variance, rsid, brigade, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, nominations)
    
    print(f"    ✅ Added {len(nominations)} marketing nominations")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print("\n✅ Sample data population complete!\n")
    print("Summary:")
    print(f"  • {len(emm_records)} EMM historical records")
    print(f"  • {predictions_count} event predictions")
    print(f"  • {len(g2_records)} G2 zone performance records")
    print(f"  • {len(nominations)} marketing nominations")
    print("\n🎉 Ready for testing!")

if __name__ == '__main__':
    populate_sample_data()
