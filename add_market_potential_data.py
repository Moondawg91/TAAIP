#!/usr/bin/env python3
"""
Add sample market potential and DOD comparison data for testing.
"""

import sqlite3
import random
from datetime import datetime
import uuid

DB_FILE = "/Users/ambermooney/Desktop/TAAIP/data/taaip.sqlite3"

# Sample CBSAs and their characteristics
SAMPLE_CBSAS = [
    {"code": "41860", "name": "San Francisco-Oakland-Berkeley, CA", "pop": 4729484, "qualified": 350000},
    {"code": "31080", "name": "Los Angeles-Long Beach-Anaheim, CA", "pop": 13200998, "qualified": 980000},
    {"code": "35620", "name": "New York-Newark-Jersey City, NY-NJ-PA", "pop": 19216182, "qualified": 1420000},
    {"code": "16980", "name": "Chicago-Naperville-Elgin, IL-IN-WI", "pop": 9478801338, "qualified": 700000},
    {"code": "19100", "name": "Dallas-Fort Worth-Arlington, TX", "pop": 7637387, "qualified": 565000},
    {"code": "26420", "name": "Houston-The Woodlands-Sugar Land, TX", "pop": 7122240, "qualified": 527000},
    {"code": "47900", "name": "Washington-Arlington-Alexandria, DC-VA-MD-WV", "pop": 6280487, "qualified": 465000},
    {"code": "33100", "name": "Miami-Fort Lauderdale-Pompano Beach, FL", "pop": 6138333, "qualified": 454000},
    {"code": "37980", "name": "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", "pop": 6245051, "qualified": 462000},
    {"code": "12060", "name": "Atlanta-Sandy Springs-Alpharetta, GA", "pop": 6089815, "qualified": 450000},
]

# DOD Branches
BRANCHES = ["Army", "Navy", "Air Force", "Marines", "Space Force", "Coast Guard"]

# RSID mappings
RSID_OPTIONS = [
    {"rsid": "1BDE-1BN-1-1", "brigade": "1BDE", "battalion": "1BDE-1BN", "company": "1BDE-1BN-1", "station": "1BDE-1BN-1-1"},
    {"rsid": "1BDE-2BN-2-1", "brigade": "1BDE", "battalion": "1BDE-2BN", "company": "1BDE-2BN-2", "station": "1BDE-2BN-2-1"},
    {"rsid": "2BDE-3BN-3-1", "brigade": "2BDE", "battalion": "2BDE-3BN", "company": "2BDE-3BN-3", "station": "2BDE-3BN-3-1"},
    {"rsid": "2BDE-4BN-4-1", "brigade": "2BDE", "battalion": "2BDE-4BN", "company": "2BDE-4BN-4", "station": "2BDE-4BN-4-1"},
    {"rsid": "3BDE-5BN-5-1", "brigade": "3BDE", "battalion": "3BDE-5BN", "company": "3BDE-5BN-5", "station": "3BDE-5BN-5-1"},
    {"rsid": "3BDE-6BN-6-1", "brigade": "3BDE", "battalion": "3BDE-6BN", "company": "3BDE-6BN-6", "station": "3BDE-6BN-6-1"},
]

def generate_market_potential_data():
    """Generate sample market potential data for CBSAs"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("📊 Generating market potential data...")
    
    for cbsa in SAMPLE_CBSAS:
        for fy in [2024, 2025]:
            for quarter in ["Q1", "Q2", "Q3", "Q4"]:
                rsid = random.choice(RSID_OPTIONS)
                
                qualified = cbsa["qualified"]
                
                # Army metrics
                army_potential = int(qualified * random.uniform(0.15, 0.25))
                army_contacted = int(army_potential * random.uniform(0.30, 0.60))
                army_remaining = army_potential - army_contacted
                
                # Other DOD branches
                navy_potential = int(qualified * random.uniform(0.12, 0.20))
                navy_contacted = int(navy_potential * random.uniform(0.25, 0.55))
                
                af_potential = int(qualified * random.uniform(0.10, 0.18))
                af_contacted = int(af_potential * random.uniform(0.28, 0.58))
                
                marines_potential = int(qualified * random.uniform(0.08, 0.15))
                marines_contacted = int(marines_potential * random.uniform(0.30, 0.60))
                
                sf_potential = int(qualified * random.uniform(0.02, 0.05))
                sf_contacted = int(sf_potential * random.uniform(0.20, 0.45))
                
                cg_potential = int(qualified * random.uniform(0.03, 0.07))
                cg_contacted = int(cg_potential * random.uniform(0.22, 0.50))
                
                total_dod_contacted = (army_contacted + navy_contacted + af_contacted + 
                                      marines_contacted + sf_contacted + cg_contacted)
                total_dod_remaining = qualified - total_dod_contacted
                
                # Market shares
                army_share = (army_contacted / total_dod_contacted * 100) if total_dod_contacted > 0 else 0
                navy_share = (navy_contacted / total_dod_contacted * 100) if total_dod_contacted > 0 else 0
                af_share = (af_contacted / total_dod_contacted * 100) if total_dod_contacted > 0 else 0
                marines_share = (marines_contacted / total_dod_contacted * 100) if total_dod_contacted > 0 else 0
                sf_share = (sf_contacted / total_dod_contacted * 100) if total_dod_contacted > 0 else 0
                cg_share = (cg_contacted / total_dod_contacted * 100) if total_dod_contacted > 0 else 0
                
                cursor.execute("""
                    INSERT OR REPLACE INTO market_potential (
                        id, geographic_level, geographic_id, geographic_name,
                        brigade, battalion,
                        qualified_population,
                        army_contacted, army_remaining_potential, army_market_share,
                        navy_contacted, navy_remaining_potential, navy_market_share,
                        air_force_contacted, air_force_remaining_potential, air_force_market_share,
                        marines_contacted, marines_remaining_potential, marines_market_share,
                        space_force_contacted, space_force_remaining_potential, space_force_market_share,
                        coast_guard_contacted, coast_guard_remaining_potential, coast_guard_market_share,
                        total_dod_contacted, total_dod_remaining,
                        fiscal_year, quarter, data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"mp_{cbsa['code']}_{fy}_{quarter}",
                    "cbsa",
                    cbsa["code"],
                    cbsa["name"],
                    rsid["brigade"],
                    rsid["battalion"],
                    qualified,
                    army_contacted, army_remaining, army_share,
                    navy_contacted, navy_potential - navy_contacted, navy_share,
                    af_contacted, af_potential - af_contacted, af_share,
                    marines_contacted, marines_potential - marines_contacted, marines_share,
                    sf_contacted, sf_potential - sf_contacted, sf_share,
                    cg_contacted, cg_potential - cg_contacted, cg_share,
                    total_dod_contacted, total_dod_remaining,
                    fy, quarter, "SAMPLE_DATA"
                ))
    
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM market_potential").fetchone()[0]
    print(f"  ✅ Added {count} market potential records")
    conn.close()

def generate_dod_branch_comparison():
    """Generate DOD branch comparison data"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🏆 Generating DOD branch comparison data...")
    
    for cbsa in SAMPLE_CBSAS:
        for branch in BRANCHES:
            for fy in [2024, 2025]:
                for quarter in ["Q1", "Q2", "Q3", "Q4"]:
                    # Branch-specific metrics
                    if branch == "Army":
                        recruiters = random.randint(45, 75)
                        leads = random.randint(8000, 15000)
                        contracts = random.randint(450, 850)
                        efficiency = random.uniform(0.05, 0.08)
                    elif branch == "Navy":
                        recruiters = random.randint(35, 60)
                        leads = random.randint(6000, 12000)
                        contracts = random.randint(380, 720)
                        efficiency = random.uniform(0.05, 0.07)
                    elif branch == "Air Force":
                        recruiters = random.randint(25, 45)
                        leads = random.randint(5000, 10000)
                        contracts = random.randint(320, 600)
                        efficiency = random.uniform(0.06, 0.08)
                    elif branch == "Marines":
                        recruiters = random.randint(30, 50)
                        leads = random.randint(4500, 9000)
                        contracts = random.randint(280, 550)
                        efficiency = random.uniform(0.05, 0.07)
                    elif branch == "Space Force":
                        recruiters = random.randint(5, 12)
                        leads = random.randint(800, 2000)
                        contracts = random.randint(45, 110)
                        efficiency = random.uniform(0.04, 0.06)
                    else:  # Coast Guard
                        recruiters = random.randint(8, 18)
                        leads = random.randint(1200, 3000)
                        contracts = random.randint(60, 150)
                        efficiency = random.uniform(0.04, 0.06)
                    
                    ships = int(contracts * random.uniform(0.85, 0.95))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO dod_branch_comparison (
                            comparison_id, branch, geographic_level, geographic_id, geographic_name,
                            total_recruiters, total_leads, total_contracts, total_ships,
                            lead_to_contract_rate, contract_to_ship_rate, overall_efficiency_score,
                            contracts_per_recruiter, fiscal_year, quarter, data_source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"cmp_{branch}_{cbsa['code']}_{fy}_{quarter}",
                        branch,
                        "cbsa",
                        cbsa["code"],
                        cbsa["name"],
                        recruiters,
                        leads,
                        contracts,
                        ships,
                        efficiency,
                        ships / contracts if contracts > 0 else 0,
                        random.uniform(0.65, 0.85),
                        contracts / recruiters if recruiters > 0 else 0,
                        fy, quarter, "SAMPLE_DATA"
                    ))
    
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM dod_branch_comparison").fetchone()[0]
    print(f"  ✅ Added {count} DOD branch comparison records")
    conn.close()

def generate_mission_analysis():
    """Generate mission analysis data for USAREC hierarchy"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("🎯 Generating mission analysis data...")
    
    for fy in [2024, 2025]:
        for quarter in ["Q1", "Q2", "Q3", "Q4"]:
            # USAREC level
            cursor.execute("""
                INSERT OR REPLACE INTO mission_analysis (
                    analysis_id, analysis_level, usarec_region,
                    mission_goal, contracts_actual, contracts_variance, goal_attainment_pct,
                    leads_generated, appointments_made, appointments_conducted,
                    tests_administered, tests_passed, enlistments, ships,
                    lead_to_enlistment_rate, appointment_show_rate, test_pass_rate,
                    fiscal_year, quarter
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"ma_usarec_{fy}_{quarter}",
                "usarec",
                "USAREC",
                15000, random.randint(13500, 16200), 0, 0,
                185000, 95000, 78000,
                65000, 58500, 15100, 14300,
                0.082, 0.82, 0.90,
                fy, quarter
            ))
            
            # Brigade level
            for rsid in RSID_OPTIONS[:3]:  # Top 3 brigades
                goal = random.randint(2200, 2800)
                actual = random.randint(2000, 3000)
                variance = actual - goal
                attainment = (actual / goal * 100) if goal > 0 else 0
                
                cursor.execute("""
                    INSERT OR REPLACE INTO mission_analysis (
                        analysis_id, analysis_level, usarec_region, brigade,
                        mission_goal, contracts_actual, contracts_variance, goal_attainment_pct,
                        leads_generated, appointments_made, appointments_conducted,
                        tests_administered, tests_passed, enlistments, ships,
                        fiscal_year, quarter
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"ma_{rsid['brigade']}_{fy}_{quarter}",
                    "brigade",
                    "USAREC",
                    rsid["brigade"],
                    goal, actual, variance, attainment,
                    random.randint(28000, 35000),
                    random.randint(14000, 18000),
                    random.randint(11000, 15000),
                    random.randint(9500, 13000),
                    random.randint(8500, 11700),
                    actual,
                    int(actual * 0.95),
                    fy, quarter
                ))
    
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM mission_analysis").fetchone()[0]
    print(f"  ✅ Added {count} mission analysis records")
    conn.close()

def main():
    print("🚀 Adding sample market potential and DOD comparison data...\n")
    
    generate_market_potential_data()
    generate_dod_branch_comparison()
    generate_mission_analysis()
    
    print()
    print("✅ Sample data generation completed!")
    print()
    print("Data Summary:")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    mp_count = cursor.execute("SELECT COUNT(*) FROM market_potential").fetchone()[0]
    dod_count = cursor.execute("SELECT COUNT(*) FROM dod_branch_comparison").fetchone()[0]
    ma_count = cursor.execute("SELECT COUNT(*) FROM mission_analysis").fetchone()[0]
    
    print(f"  • Market Potential Records: {mp_count}")
    print(f"  • DOD Branch Comparisons: {dod_count}")
    print(f"  • Mission Analysis Records: {ma_count}")
    
    # Sample query
    print()
    print("Sample Army vs DOD Comparison (FY2025 Q4):")
    cursor.execute("""
        SELECT 
            geographic_name,
            army_contacted,
            army_remaining_potential,
            total_dod_contacted,
            total_dod_remaining,
            ROUND(army_market_share, 2) as army_share
        FROM market_potential
        WHERE fiscal_year = 2025 AND quarter = 'Q4'
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0][:40]}: Army {row[1]:,} contacted, {row[2]:,} remaining | DOD {row[3]:,} contacted, {row[4]:,} remaining | Army Share: {row[5]}%")
    
    conn.close()

if __name__ == "__main__":
    main()
