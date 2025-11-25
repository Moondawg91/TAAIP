#!/usr/bin/env python3
"""
Add sample recruiting funnel data to test the dashboard.
"""

import sqlite3
from datetime import datetime, timedelta
import random
import os

# Use unified recruiting.db so backend endpoints reflect sample data
DB_FILE = os.path.join(os.path.dirname(__file__), "recruiting.db")

# Sample data pools
FIRST_NAMES = ["James", "John", "Michael", "David", "William", "Robert", "Joseph", "Thomas", "Charles", "Christopher"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
MOS_INTERESTS = ["11B Infantry", "13F Fire Support", "25B IT Specialist", "68W Combat Medic", "92Y Supply", "31B Military Police", "15T Helicopter Mechanic", "35F Intelligence Analyst"]
LEAD_SOURCES = ["EMM", "iKrome", "Recruiter Zone", "Walk-in", "Referral", "Event", "Website"]
LOSS_REASONS = ["Age ineligible", "Medical disqualification", "ASVAB score", "Criminal record", "Changed mind", "Family concerns", "Found other job", "Moved away"]
RSID_OPTIONS = ["1BDE-1BN-1-1", "1BDE-1BN-1-2", "1BDE-2BN-2-1", "2BDE-4BN-4-1", "3BDE-6BN-6-1", "4BDE-8BN-8-1", "5BDE-10BN-10-1", "6BDE-12BN-12-1"]

# Stage distribution (realistic recruiting funnel)
# 100 leads → 60 prospects → 35 applicants → 20 DEP → 15 contracts → 12 ships → 25 losses
STAGES_DISTRIBUTION = {
    'lead': 15,
    'prospect': 25,
    'applicant': 15,
    'dep': 10,
    'contract': 8,
    'ship': 7,
    'loss': 20
}

def generate_prid():
    """Generate a fake PRID (format: 3 letters + 6 digits)"""
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    numbers = ''.join(random.choices('0123456789', k=6))
    return f"{letters}{numbers}"

def generate_lead_data(stage, index):
    """Generate a lead record for the specified stage"""
    base_date = datetime.now() - timedelta(days=random.randint(30, 180))
    
    # Stage progression dates
    lead_date = base_date
    prospect_date = None
    applicant_date = None
    dep_date = None
    contract_date = None
    ship_date = None
    loss_date = None
    loss_reason = None
    loss_stage = None
    
    if stage == 'loss':
        # Lost at various stages
        loss_stage_options = ['lead', 'prospect', 'applicant', 'dep']
        loss_stage = random.choice(loss_stage_options)
        loss_reason = random.choice(LOSS_REASONS)
        loss_date = base_date + timedelta(days=random.randint(7, 120))
        
        if loss_stage in ['prospect', 'applicant', 'dep']:
            prospect_date = lead_date + timedelta(days=random.randint(3, 14))
        if loss_stage in ['applicant', 'dep']:
            applicant_date = prospect_date + timedelta(days=random.randint(7, 21))
        if loss_stage == 'dep':
            dep_date = applicant_date + timedelta(days=random.randint(14, 45))
            
    elif stage in ['prospect', 'applicant', 'dep', 'contract', 'ship']:
        prospect_date = lead_date + timedelta(days=random.randint(3, 14))
        
        if stage in ['applicant', 'dep', 'contract', 'ship']:
            applicant_date = prospect_date + timedelta(days=random.randint(7, 21))
            
        if stage in ['dep', 'contract', 'ship']:
            dep_date = applicant_date + timedelta(days=random.randint(14, 45))
            
        if stage in ['contract', 'ship']:
            contract_date = dep_date + timedelta(days=random.randint(30, 120))
            
        if stage == 'ship':
            ship_date = contract_date + timedelta(days=random.randint(30, 180))
    
    # Calculate DEP length
    dep_length_days = None
    if dep_date and ship_date:
        dep_length_days = (ship_date - dep_date).days
    
    # Fiscal year (Oct 1 - Sep 30)
    fiscal_year = lead_date.year if lead_date.month >= 10 else lead_date.year - 1
    fiscal_year += 1  # FY2025 means Oct 2024 - Sep 2025
    
    recruiting_year = f"RY{fiscal_year}"
    
    # Quarter (Oct-Dec=Q1, Jan-Mar=Q2, Apr-Jun=Q3, Jul-Sep=Q4)
    month = lead_date.month
    if month in [10, 11, 12]:
        quarter = 'Q1'
    elif month in [1, 2, 3]:
        quarter = 'Q2'
    elif month in [4, 5, 6]:
        quarter = 'Q3'
    else:
        quarter = 'Q4'
    
    # Ship month (if shipped)
    ship_month = ship_date.strftime('%Y-%m') if ship_date else None
    
    return {
        'prid': generate_prid(),
        'first_name': random.choice(FIRST_NAMES),
        'last_name': random.choice(LAST_NAMES),
        'age': random.randint(17, 35),
        'education_level': random.choice(['High School', 'Some College', 'Associates', 'Bachelors']),
        'rsid': random.choice(RSID_OPTIONS),
        'brigade': random.choice(RSID_OPTIONS).split('-')[0],
        'battalion': '-'.join(random.choice(RSID_OPTIONS).split('-')[:2]),
        'station': random.choice(RSID_OPTIONS),
        'recruiter_id': f"REC{random.randint(1000, 9999)}",
        'lead_source': random.choice(LEAD_SOURCES),
        'mos_interest': random.choice(MOS_INTERESTS),
        'current_stage': stage,
        'lead_date': lead_date.strftime('%Y-%m-%d'),
        'prospect_date': prospect_date.strftime('%Y-%m-%d') if prospect_date else None,
        'applicant_date': applicant_date.strftime('%Y-%m-%d') if applicant_date else None,
        'dep_date': dep_date.strftime('%Y-%m-%d') if dep_date else None,
        'contract_date': contract_date.strftime('%Y-%m-%d') if contract_date else None,
        'ship_date': ship_date.strftime('%Y-%m-%d') if ship_date else None,
        'loss_date': loss_date.strftime('%Y-%m-%d') if loss_date else None,
        'loss_reason': loss_reason,
        'loss_stage': loss_stage,
        'dep_length_days': dep_length_days,
        'fiscal_year': fiscal_year,
        'recruiting_year': recruiting_year,
        'quarter': quarter,
        'ship_month': ship_month,
        'emm_id': f"EMM{random.randint(10000, 99999)}",
        'ikrome_id': f"IK{random.randint(10000, 99999)}",
        'rzone_id': f"RZ{random.randint(10000, 99999)}",
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_sync_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def insert_lead(conn, lead_data):
    """Insert a lead record into the database"""
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO leads (
            prid, first_name, last_name, age, education_level,
            rsid, brigade, battalion, station,
            recruiter_id, lead_source, mos_interest,
            current_stage,
            lead_date, prospect_date, applicant_date, dep_date, contract_date, ship_date, loss_date,
            loss_reason, loss_stage, dep_length_days,
            fiscal_year, recruiting_year, quarter, ship_month,
            emm_id, ikrome_id, rzone_id,
            created_at, last_sync_at
        ) VALUES (
            :prid, :first_name, :last_name, :age, :education_level,
            :rsid, :brigade, :battalion, :station,
            :recruiter_id, :lead_source, :mos_interest,
            :current_stage,
            :lead_date, :prospect_date, :applicant_date, :dep_date, :contract_date, :ship_date, :loss_date,
            :loss_reason, :loss_stage, :dep_length_days,
            :fiscal_year, :recruiting_year, :quarter, :ship_month,
            :emm_id, :ikrome_id, :rzone_id,
            :created_at, :last_sync_at
        )
    """
    
    try:
        cursor.execute(sql, lead_data)
        return True
    except sqlite3.IntegrityError as e:
        print(f"⚠️  Duplicate PRID {lead_data['prid']}: {e}")
        return False

def main():
    print("🚀 Adding sample recruiting funnel data...")
    print(f"📊 Target distribution: {STAGES_DISTRIBUTION}")
    print()
    
    conn = sqlite3.connect(DB_FILE)
    
    total_inserted = 0
    for stage, count in STAGES_DISTRIBUTION.items():
        print(f"Adding {count} leads in stage '{stage}'...")
        inserted = 0
        attempts = 0
        max_attempts = count * 3  # Allow retries for duplicate PRIDs
        
        while inserted < count and attempts < max_attempts:
            lead_data = generate_lead_data(stage, inserted)
            if insert_lead(conn, lead_data):
                inserted += 1
                total_inserted += 1
            attempts += 1
        
        print(f"  ✅ Added {inserted} {stage} leads")
    
    conn.commit()
    conn.close()
    
    print()
    print(f"✅ Successfully added {total_inserted} sample leads!")
    print()
    print("📈 You can now view the Recruiting Funnel Dashboard at http://localhost:5173")
    print("   Click the 'Recruiting Funnel' tab to see the visualization.")

if __name__ == "__main__":
    main()
