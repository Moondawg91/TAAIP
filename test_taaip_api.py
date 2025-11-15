#!/usr/bin/env python3
"""
TAAIP Integration Test Suite

This script tests all major API endpoints of the TAAIP v2 system.
Run this after starting the service: python taaip_service.py

Usage:
    python test_taaip_api.py
    python test_taaip_api.py --token YOUR_API_TOKEN
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

class TAAIPTester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v2", token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        
        self.test_results = []
        self.event_id = None
        self.project_id = None
        self.profile_id = None
        self.mipoe_id = None
    
    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"         {details}")
        self.test_results.append({"name": name, "passed": passed, "details": details})
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=self.headers)
            else:
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_events(self):
        """Test event management endpoints."""
        print("\n" + "="*60)
        print("TESTING: Event Management")
        print("="*60)
        
        # Create event
        event_data = {
            "name": "Test Event 2025",
            "type": "In-Person-Meeting",
            "location": "Test Location, SC",
            "start_date": "2025-02-15",
            "end_date": "2025-02-15",
            "budget": 50000,
            "team_size": 12,
            "targeting_principles": "D3AE_Primary"
        }
        result = self.make_request("POST", "/events", event_data)
        passed = result and "event_id" in result
        self.log_test("Create Event", passed, result.get("event_id") if passed else str(result))
        
        if passed:
            self.event_id = result["event_id"]
            
            # Record metrics
            metrics_data = {
                "event_id": self.event_id,
                "date": datetime.now().date().isoformat(),
                "leads_generated": 150,
                "leads_qualified": 95,
                "conversion_count": 12,
                "cost_per_lead": 333.33,
                "roi": 1.45,
                "engagement_rate": 0.63
            }
            result = self.make_request("POST", f"/events/{self.event_id}/metrics", metrics_data)
            passed = result and result.get("status") == "ok"
            self.log_test("Record Event Metrics", passed)
            
            # Get metrics
            result = self.make_request("GET", f"/events/{self.event_id}/metrics")
            passed = result and "metrics" in result
            self.log_test("Get Event Metrics", passed, f"{len(result.get('metrics', []))} metrics retrieved")
            
            # Capture survey
            survey_data = {
                "event_id": self.event_id,
                "lead_id": "lead_test_001",
                "technician_id": "tech_001",
                "effectiveness_rating": 4,
                "feedback": "Strong engagement with D3AE targeting"
            }
            result = self.make_request("POST", f"/events/{self.event_id}/survey", survey_data)
            passed = result and result.get("status") == "ok"
            self.log_test("Capture Survey Feedback", passed)
            
            # Get feedback
            result = self.make_request("GET", f"/events/{self.event_id}/feedback")
            passed = result and "feedback" in result
            self.log_test("Get Event Feedback", passed)
    
    def test_funnel(self):
        """Test recruiting funnel endpoints."""
        print("\n" + "="*60)
        print("TESTING: Recruiting Funnel")
        print("="*60)
        
        # Get funnel stages
        result = self.make_request("GET", "/funnel/stages")
        passed = result and "stages" in result and len(result["stages"]) == 8
        self.log_test("Get Funnel Stages", passed, f"{len(result.get('stages', []))} stages retrieved")
        
        # Record transition
        transition_data = {
            "lead_id": "lead_test_001",
            "from_stage": "lead",
            "to_stage": "qualified",
            "transition_reason": "ASVAB 70+ score",
            "technician_id": "tech_001"
        }
        result = self.make_request("POST", "/funnel/transition", transition_data)
        passed = result and result.get("status") == "ok"
        self.log_test("Record Funnel Transition", passed)
        
        # Get funnel metrics
        result = self.make_request("GET", "/funnel/metrics")
        passed = result and "stage_distribution" in result
        self.log_test("Get Funnel Metrics", passed, f"{len(result.get('stage_distribution', {}))} stages")
    
    def test_projects(self):
        """Test project management endpoints."""
        print("\n" + "="*60)
        print("TESTING: Project Management")
        print("="*60)
        
        if not self.event_id:
            self.log_test("Create Project", False, "No event ID available")
            return
        
        # Create project
        project_data = {
            "name": "Test Project",
            "event_id": self.event_id,
            "start_date": "2025-01-15",
            "target_date": "2025-02-15",
            "owner_id": "commander_001",
            "objectives": "Test objectives",
            "success_criteria": "Test criteria"
        }
        result = self.make_request("POST", "/projects", project_data)
        passed = result and "project_id" in result
        self.log_test("Create Project", passed, result.get("project_id") if passed else str(result))
        
        if passed:
            self.project_id = result["project_id"]
            
            # Create task
            task_data = {
                "project_id": self.project_id,
                "title": "Test Task",
                "description": "Test task description",
                "assigned_to": "team_member",
                "due_date": "2025-02-01",
                "priority": "high"
            }
            result = self.make_request("POST", f"/projects/{self.project_id}/tasks", task_data)
            passed = result and result.get("status") == "ok"
            self.log_test("Create Task", passed)
            
            # Get timeline
            result = self.make_request("GET", f"/projects/{self.project_id}/timeline")
            passed = result and "milestones" in result
            self.log_test("Get Project Timeline", passed, f"{len(result.get('milestones', []))} milestones")
    
    def test_mipoe(self):
        """Test M-IPOE endpoints."""
        print("\n" + "="*60)
        print("TESTING: M-IPOE Framework")
        print("="*60)
        
        if not self.event_id:
            self.log_test("Create M-IPOE", False, "No event ID available")
            return
        
        # Create intent
        mipoe_data = {
            "event_id": self.event_id,
            "phase": "intent",
            "content": {
                "strategic_objective": "Test objective",
                "target_demographic": "HS grads 18-28",
                "commander_intent": "Focus on high-propensity demographics"
            },
            "owner_id": "commander_001"
        }
        result = self.make_request("POST", "/mipoe", mipoe_data)
        passed = result and "mipoe_id" in result
        self.log_test("Create M-IPOE Intent", passed)
        
        if passed:
            self.mipoe_id = result["mipoe_id"]
            
            # Create plan
            mipoe_data["phase"] = "plan"
            mipoe_data["content"] = {
                "event_type": "In-Person Meeting",
                "venue": "Test Venue",
                "budget": 50000
            }
            result = self.make_request("POST", "/mipoe", mipoe_data)
            passed = result and result.get("status") == "ok"
            self.log_test("Create M-IPOE Plan", passed)
            
            # Create execute
            mipoe_data["phase"] = "execute"
            mipoe_data["content"] = {
                "actual_leads": 150,
                "actual_conversions": 12,
                "actual_roi": 1.45
            }
            result = self.make_request("POST", "/mipoe", mipoe_data)
            passed = result and result.get("status") == "ok"
            self.log_test("Create M-IPOE Execute", passed)
            
            # Create evaluate
            mipoe_data["phase"] = "evaluate"
            mipoe_data["content"] = {
                "achievements": ["Hit targets"],
                "lessons_learned": ["D3AE effective"],
                "recommendations": ["Replicate format"]
            }
            result = self.make_request("POST", "/mipoe", mipoe_data)
            passed = result and result.get("status") == "ok"
            self.log_test("Create M-IPOE Evaluate", passed)
            
            # Get M-IPOE
            result = self.make_request("GET", f"/mipoe/{self.mipoe_id}")
            passed = result and "phase" in result
            self.log_test("Get M-IPOE Record", passed)
    
    def test_targeting(self):
        """Test D3AE/F3A targeting endpoints."""
        print("\n" + "="*60)
        print("TESTING: D3AE/F3A Targeting Profiles")
        print("="*60)
        
        if not self.event_id:
            self.log_test("Create Targeting Profile", False, "No event ID available")
            return
        
        # Create profile
        profile_data = {
            "event_id": self.event_id,
            "target_age_min": 18,
            "target_age_max": 28,
            "target_education_level": "High School, Some College",
            "target_locations": "37980,41884",
            "message_themes": "career_growth,education_benefits",
            "contact_frequency": 3,
            "conversion_target": 0.12,
            "cost_per_lead_target": 333.33
        }
        result = self.make_request("POST", "/targeting-profiles", profile_data)
        passed = result and "profile_id" in result
        self.log_test("Create Targeting Profile", passed, result.get("profile_id") if passed else str(result))
        
        if passed:
            self.profile_id = result["profile_id"]
            
            # Get profile
            result = self.make_request("GET", f"/targeting-profiles/{self.profile_id}")
            passed = result and "target_age_min" in result
            self.log_test("Get Targeting Profile", passed)
    
    def test_forecasting(self):
        """Test forecasting endpoints."""
        print("\n" + "="*60)
        print("TESTING: Forecasting & Analytics")
        print("="*60)
        
        # Generate forecast
        forecast_data = {"quarter": 1, "year": 2025}
        result = self.make_request("POST", "/forecasts/generate", forecast_data)
        passed = result and "forecast_id" in result
        self.log_test("Generate Forecast", passed)
        
        # Get forecast
        result = self.make_request("GET", "/forecasts/1/2025")
        passed = result and "projected_leads" in result
        self.log_test("Get Forecast", passed, f"Projected leads: {result.get('projected_leads')}")
        
        # Get dashboard
        result = self.make_request("GET", "/analytics/dashboard")
        passed = result and "dashboard" in result
        self.log_test("Get Dashboard Snapshot", passed)
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*60)
        print("TAAIP API TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Authentication: {'Enabled' if self.token else 'Disabled'}")
        
        self.test_events()
        self.test_funnel()
        self.test_projects()
        self.test_mipoe()
        self.test_targeting()
        self.test_forecasting()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for t in self.test_results if t["passed"])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if passed < total:
            print("\nFailed Tests:")
            for test in self.test_results:
                if not test["passed"]:
                    print(f"  - {test['name']}")
        
        return passed == total

def main():
    parser = argparse.ArgumentParser(description="TAAIP API Test Suite")
    parser.add_argument("--base-url", default="http://localhost:8000/api/v2",
                       help="Base API URL")
    parser.add_argument("--token", help="Bearer token for authentication")
    
    args = parser.parse_args()
    
    tester = TAAIPTester(args.base_url, args.token)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
