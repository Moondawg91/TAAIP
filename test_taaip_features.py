"""
TAAIP v2.0 - Comprehensive Feature Test Script
Tests all API endpoints and verifies functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_api_health():
    """Test if API is running"""
    print_section("1. API Health Check")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API is running on port 8000")
            return True
        else:
            print("❌ API returned unexpected status:", response.status_code)
            return False
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        return False

def test_company_standings():
    """Test company standings endpoint"""
    print_section("2. Company Standings Leaderboard")
    try:
        response = requests.get(f"{BASE_URL}/api/v2/standings/companies")
        if response.status_code == 200:
            data = response.json()
            companies = data.get('companies', [])
            print(f"✅ Retrieved {len(companies)} companies")
            
            if companies:
                print("\nTop 5 Companies:")
                print("-" * 80)
                for i, company in enumerate(companies[:5], 1):
                    print(f"{i}. {company['company_name']:<30} "
                          f"Brigade: {company['brigade']:<15} "
                          f"Attainment: {company['ytd_attainment']:>6.1f}%")
                
                print("\nMetrics Available:")
                sample = companies[0]
                metrics = ['rank', 'ytd_mission', 'ytd_actual', 'ytd_attainment', 
                          'monthly_mission', 'monthly_actual', 'net_gain', 'last_enlistment']
                for metric in metrics:
                    if metric in sample:
                        print(f"  ✓ {metric}")
                
                return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_access():
    """Test user access endpoint"""
    print_section("3. User Access System")
    
    # Test users from different tiers
    test_users = [
        ("admin001", "Tier 4 - Administrator"),
        ("editor001", "Tier 3 - Editor"),
        ("user001", "Tier 2 - Standard User"),
        ("viewer001", "Tier 1 - View Only")
    ]
    
    all_passed = True
    for user_id, tier_name in test_users:
        try:
            response = requests.get(f"{BASE_URL}/api/v2/users/{user_id}/access")
            if response.status_code == 200:
                data = response.json()
                user = data.get('user', {})
                print(f"✅ {tier_name:<30} User: {user.get('name', 'N/A')}")
                
                # Verify permissions exist
                permissions = user.get('permissions', {})
                if permissions:
                    print(f"   Permissions: canView={permissions.get('canView')}, "
                          f"canEdit={permissions.get('canEdit')}, "
                          f"canExport={permissions.get('canExport')}")
            else:
                print(f"❌ Failed for {user_id}: Status {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error testing {user_id}: {e}")
            all_passed = False
    
    return all_passed

def test_helpdesk_submission():
    """Test helpdesk request submission"""
    print_section("4. Help Desk System")
    
    test_request = {
        "type": "access_request",
        "priority": "medium",
        "title": "Test Access Upgrade Request",
        "description": "Automated test of help desk functionality",
        "requestedAccessLevel": "tier_3",
        "currentAccessLevel": "tier_2",
        "submittedBy": "test_user",
        "submittedAt": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/helpdesk/requests",
            json=test_request
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Help desk request submitted successfully")
            print(f"   Request ID: {data.get('request_id', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_helpdesk_retrieval():
    """Test retrieving helpdesk requests"""
    print_section("5. Help Desk Retrieval")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v2/helpdesk/requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get('requests', [])
            print(f"✅ Retrieved {len(requests_list)} help desk requests")
            
            if requests_list:
                print("\nRecent Requests:")
                print("-" * 80)
                for req in requests_list[:3]:
                    print(f"  • {req.get('type', 'N/A')}: {req.get('title', 'N/A')}")
                    print(f"    Priority: {req.get('priority', 'N/A')} | "
                          f"Status: {req.get('status', 'N/A')}")
            
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_standings_update():
    """Test updating company standings"""
    print_section("6. Standings Update (Enlistment Recording)")
    
    update_data = {
        "company_id": "CO-001",
        "enlistment": True,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/standings/update",
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Standing update recorded successfully")
            print(f"   Company: {data.get('company_name', 'N/A')}")
            print(f"   New Rank: {data.get('new_rank', 'N/A')}")
            print(f"   YTD Actual: {data.get('ytd_actual', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_brigade_filtering():
    """Test brigade filtering"""
    print_section("7. Brigade Filtering")
    
    brigades = ["1st Brigade", "2nd Brigade", "3rd Brigade"]
    all_passed = True
    
    for brigade in brigades:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v2/standings/companies",
                params={"brigade": brigade}
            )
            
            if response.status_code == 200:
                data = response.json()
                companies = data.get('companies', [])
                # Verify all companies are from the requested brigade
                correct_brigade = all(c.get('brigade') == brigade for c in companies)
                if correct_brigade:
                    print(f"✅ {brigade:<15} {len(companies)} companies")
                else:
                    print(f"❌ {brigade:<15} Filtering error")
                    all_passed = False
            else:
                print(f"❌ {brigade}: Status {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ {brigade}: {e}")
            all_passed = False
    
    return all_passed

def verify_database():
    """Verify database has data"""
    print_section("8. Database Verification")
    
    import sqlite3
    
    try:
        conn = sqlite3.connect('data/taaip.sqlite3')
        cursor = conn.cursor()
        
        # Check company_standings
        cursor.execute("SELECT COUNT(*) FROM company_standings")
        companies_count = cursor.fetchone()[0]
        print(f"✅ Company Standings: {companies_count} records")
        
        # Check user_access
        cursor.execute("SELECT COUNT(*) FROM user_access")
        users_count = cursor.fetchone()[0]
        print(f"✅ User Access: {users_count} records")
        
        # Check helpdesk_requests (if exists)
        try:
            cursor.execute("SELECT COUNT(*) FROM helpdesk_requests")
            helpdesk_count = cursor.fetchone()[0]
            print(f"✅ Help Desk Requests: {helpdesk_count} records")
        except:
            print("ℹ️  Help Desk Requests: Table not yet created (will be on first request)")
        
        # Check access level distribution
        print("\nAccess Level Distribution:")
        cursor.execute("""
            SELECT access_level, COUNT(*) 
            FROM user_access 
            GROUP BY access_level 
            ORDER BY access_level
        """)
        for level, count in cursor.fetchall():
            tier_name = level.replace('_', ' ').title()
            print(f"  {tier_name:<20} {count:>3} users")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def run_all_tests():
    """Run all tests and generate summary"""
    print("\n" + "█" * 80)
    print("  TAAIP v2.0 - COMPREHENSIVE FEATURE TEST")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("█" * 80)
    
    results = []
    
    # Run tests
    results.append(("API Health Check", test_api_health()))
    results.append(("Company Standings", test_company_standings()))
    results.append(("User Access System", test_user_access()))
    results.append(("Help Desk Submission", test_helpdesk_submission()))
    results.append(("Help Desk Retrieval", test_helpdesk_retrieval()))
    results.append(("Standings Update", test_standings_update()))
    results.append(("Brigade Filtering", test_brigade_filtering()))
    results.append(("Database Verification", verify_database()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("-" * 80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    # Overall result
    print("\n" + "=" * 80)
    if passed == total:
        print("  🎉 ALL TESTS PASSED! System is fully operational.")
    else:
        print(f"  ⚠️  {total - passed} test(s) failed. Review errors above.")
    print("=" * 80 + "\n")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()
