"""
Populate Company Standings with Realistic Data
"""

import sqlite3
import random
from datetime import datetime, timedelta

def populate_company_standings():
    """Populate company standings with realistic recruiting data"""
    
    conn = sqlite3.connect('data/taaip.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create table if doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_standings (
            company_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            battalion TEXT NOT NULL,
            brigade TEXT NOT NULL,
            rank INTEGER,
            previous_rank INTEGER,
            ytd_mission INTEGER DEFAULT 0,
            ytd_actual INTEGER DEFAULT 0,
            ytd_attainment REAL DEFAULT 0.0,
            monthly_mission INTEGER DEFAULT 0,
            monthly_actual INTEGER DEFAULT 0,
            monthly_attainment REAL DEFAULT 0.0,
            total_enlistments INTEGER DEFAULT 0,
            future_soldier_losses INTEGER DEFAULT 0,
            net_gain INTEGER DEFAULT 0,
            last_enlistment TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM company_standings")
    
    # Brigade and Battalion structure
    brigades = {
        "1st Brigade": ["1-1 BN", "1-2 BN", "1-3 BN"],
        "2nd Brigade": ["2-1 BN", "2-2 BN", "2-3 BN"],
        "3rd Brigade": ["3-1 BN", "3-2 BN", "3-3 BN"],
        "4th Brigade": ["4-1 BN", "4-2 BN", "4-3 BN"],
        "5th Brigade": ["5-1 BN", "5-2 BN", "5-3 BN"],
        "6th Brigade": ["6-1 BN", "6-2 BN", "6-3 BN"]
    }
    
    company_names = ["Alpha", "Bravo", "Charlie"]
    
    companies = []
    company_id = 1
    
    # Generate companies
    for brigade, battalions in brigades.items():
        for battalion in battalions:
            for company_name in company_names:
                # Realistic mission numbers based on company size
                ytd_mission = random.randint(45, 75)
                ytd_actual = int(ytd_mission * random.uniform(0.65, 1.35))  # 65-135% attainment
                
                monthly_mission = random.randint(8, 15)
                monthly_actual = int(monthly_mission * random.uniform(0.50, 1.50))
                
                # Calculate losses (typically 5-15% of enlistments)
                total_enlistments = ytd_actual + random.randint(3, 10)
                losses = random.randint(int(total_enlistments * 0.05), int(total_enlistments * 0.15))
                net_gain = total_enlistments - losses
                
                # Recent enlistment timestamp
                days_ago = random.randint(0, 14)
                last_enlistment = (datetime.now() - timedelta(days=days_ago)).isoformat()
                
                companies.append({
                    'company_id': f'CO-{company_id:03d}',
                    'company_name': f"{company_name} Co, {battalion}",
                    'battalion': battalion,
                    'brigade': brigade,
                    'ytd_mission': ytd_mission,
                    'ytd_actual': ytd_actual,
                    'ytd_attainment': round((ytd_actual / ytd_mission * 100), 2),
                    'monthly_mission': monthly_mission,
                    'monthly_actual': monthly_actual,
                    'monthly_attainment': round((monthly_actual / monthly_mission * 100), 2),
                    'total_enlistments': total_enlistments,
                    'future_soldier_losses': losses,
                    'net_gain': net_gain,
                    'last_enlistment': last_enlistment
                })
                company_id += 1
    
    # Sort by YTD attainment for ranking
    companies.sort(key=lambda x: x['ytd_attainment'], reverse=True)
    
    # Assign ranks
    for idx, company in enumerate(companies, 1):
        company['rank'] = idx
        company['previous_rank'] = idx + random.randint(-3, 3)  # Simulate rank changes
        if company['previous_rank'] < 1:
            company['previous_rank'] = 1
        if company['previous_rank'] > len(companies):
            company['previous_rank'] = len(companies)
    
    # Insert into database
    for company in companies:
        cursor.execute("""
            INSERT INTO company_standings (
                company_id, company_name, battalion, brigade, rank, previous_rank,
                ytd_mission, ytd_actual, ytd_attainment,
                monthly_mission, monthly_actual, monthly_attainment,
                total_enlistments, future_soldier_losses, net_gain, last_enlistment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company['company_id'], company['company_name'], company['battalion'],
            company['brigade'], company['rank'], company['previous_rank'],
            company['ytd_mission'], company['ytd_actual'], company['ytd_attainment'],
            company['monthly_mission'], company['monthly_actual'], company['monthly_attainment'],
            company['total_enlistments'], company['future_soldier_losses'],
            company['net_gain'], company['last_enlistment']
        ))
    
    conn.commit()
    
    # Display summary
    print(f"\n✅ Successfully populated {len(companies)} companies across 6 brigades")
    print("\nTop 5 Companies by YTD Attainment:")
    print("-" * 80)
    for i, company in enumerate(companies[:5], 1):
        print(f"{i}. {company['company_name']:<25} {company['brigade']:<15} "
              f"{company['ytd_attainment']:>6.1f}% ({company['ytd_actual']}/{company['ytd_mission']})")
    
    print("\nBottom 5 Companies:")
    print("-" * 80)
    for i, company in enumerate(companies[-5:], len(companies)-4):
        print(f"{i}. {company['company_name']:<25} {company['brigade']:<15} "
              f"{company['ytd_attainment']:>6.1f}% ({company['ytd_actual']}/{company['ytd_mission']})")
    
    conn.close()

if __name__ == "__main__":
    populate_company_standings()
