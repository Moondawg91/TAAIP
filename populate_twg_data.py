"""
Populate TWG (Targeting Working Group) tables with sample data
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid

SCRIPT_DIR = Path(__file__).parent.resolve()
# Align TWG sample data with primary recruiting database
DB_PATH = SCRIPT_DIR / "recruiting.db"


def generate_sample_twg_data():
    """Generate sample TWG review boards, analysis, decisions, and actions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Populating TWG tables with sample data...")
    
    # Sample review boards
    boards = [
        {
            "board_id": f"twg_{uuid.uuid4().hex[:8]}",
            "name": "Q1 FY2025 Market Strategy Review",
            "review_type": "strategy",
            "status": "completed",
            "scheduled_date": (datetime.now() - timedelta(days=15)).isoformat(),
            "completed_date": (datetime.now() - timedelta(days=14)).isoformat(),
            "facilitator": "MAJ Smith",
            "attendees": json.dumps(["MAJ Smith", "CPT Johnson", "1SG Williams", "SFC Davis"]),
            "rsid": "RSID_001",
            "brigade": "1BDE",
            "battalion": "1-1 BN"
        },
        {
            "board_id": f"twg_{uuid.uuid4().hex[:8]}",
            "name": "Dallas CBSA Campaign Review",
            "review_type": "campaign",
            "status": "in_progress",
            "scheduled_date": datetime.now().isoformat(),
            "facilitator": "CPT Martinez",
            "attendees": json.dumps(["CPT Martinez", "SSG Brown", "SGT Garcia"]),
            "rsid": "RSID_002",
            "brigade": "1BDE",
            "battalion": "1-2 BN"
        },
        {
            "board_id": f"twg_{uuid.uuid4().hex[:8]}",
            "name": "SF Bay Area Event Planning",
            "review_type": "event",
            "status": "scheduled",
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "facilitator": "1SG Thompson",
            "attendees": json.dumps(["1SG Thompson", "SFC Lee", "SSG Rodriguez"]),
            "rsid": "RSID_003",
            "brigade": "2BDE",
            "battalion": "2-1 BN"
        },
        {
            "board_id": f"twg_{uuid.uuid4().hex[:8]}",
            "name": "FY2025 Q2 Resource Allocation",
            "review_type": "project",
            "status": "scheduled",
            "scheduled_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "facilitator": "COL Anderson",
            "attendees": json.dumps(["COL Anderson", "MAJ Smith", "MAJ Jones", "CPT White"]),
            "rsid": "RSID_001",
            "brigade": "1BDE"
        }
    ]
    
    for board in boards:
        cursor.execute("""
            INSERT OR REPLACE INTO twg_review_boards 
            (board_id, name, review_type, status, scheduled_date, completed_date, 
             facilitator, attendees, rsid, brigade, battalion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            board["board_id"], board["name"], board["review_type"], board["status"],
            board["scheduled_date"], board.get("completed_date"), board["facilitator"],
            board["attendees"], board["rsid"], board["brigade"], board.get("battalion")
        ))
    
    print(f"  ✅ Inserted {len(boards)} review boards")
    
    # Sample analysis items for first board
    board1_id = boards[0]["board_id"]
    analyses = [
        {
            "analysis_id": f"ana_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "category": "market_analysis",
            "title": "Dallas Metro Market Saturation Analysis",
            "description": "Evaluation of current market penetration in Dallas-Fort Worth CBSA",
            "findings": "Current Army market share at 34.15% vs Navy 36.2%. Digital engagement shows 15% lower reach than competitor branches.",
            "recommendations": "Increase social media ad spend by 25%, focus on Hispanic demographic (42% of market), partner with local colleges for events",
            "priority": "high",
            "status": "approved",
            "assigned_to": "CPT Johnson",
            "due_date": (datetime.now() + timedelta(days=30)).isoformat()
        },
        {
            "analysis_id": f"ana_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "category": "competitor_analysis",
            "title": "Navy Recruiting Tactics - Q4 Review",
            "description": "Analysis of Navy's successful campus engagement strategy",
            "findings": "Navy leverages technical school partnerships, averaging 3-4 campus events per month vs our 1-2. Their digital content focuses on career training opportunities.",
            "recommendations": "Establish partnerships with community colleges offering IT/technical programs, create video content series highlighting Army technical MOSs",
            "priority": "medium",
            "status": "in_review",
            "assigned_to": "1SG Williams"
        },
        {
            "analysis_id": f"ana_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "category": "strategy",
            "title": "Lookalike Audience Optimization",
            "description": "Review of current lookalike modeling performance",
            "findings": "Current model yields 68% propensity accuracy. Top-performing segments: Young Achievers (Seg 12), College Towns (Seg 31)",
            "recommendations": "Expand lookalike seed audience from 1,000 to 5,000 converters, test multiple segment combinations, implement dynamic creative optimization",
            "priority": "critical",
            "status": "open",
            "assigned_to": "SFC Davis",
            "due_date": (datetime.now() + timedelta(days=14)).isoformat()
        }
    ]
    
    for analysis in analyses:
        cursor.execute("""
            INSERT OR REPLACE INTO twg_analysis_items
            (analysis_id, board_id, category, title, description, findings, 
             recommendations, priority, status, assigned_to, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis["analysis_id"], analysis["board_id"], analysis["category"],
            analysis["title"], analysis["description"], analysis["findings"],
            analysis["recommendations"], analysis["priority"], analysis["status"],
            analysis.get("assigned_to"), analysis.get("due_date")
        ))
    
    print(f"  ✅ Inserted {len(analyses)} analysis items")
    
    # Sample decisions
    decisions = [
        {
            "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "analysis_id": analyses[0]["analysis_id"],
            "decision_text": "Approve 25% increase in Dallas Metro digital ad budget for Q2",
            "decision_type": "approve",
            "rationale": "Market data shows clear opportunity to gain share from Navy. Budget reallocation justified by projected 15% increase in qualified leads.",
            "impact": "Expected to generate additional 120 qualified leads per month, estimated 12-15 additional contracts",
            "decided_by": "MAJ Smith",
            "decision_date": (datetime.now() - timedelta(days=14)).isoformat()
        },
        {
            "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "analysis_id": analyses[1]["analysis_id"],
            "decision_text": "Defer Navy tactics analysis pending additional competitor intel",
            "decision_type": "defer",
            "rationale": "Need more detailed breakdown of Navy's partnership agreements before implementing similar strategy",
            "impact": "Delayed implementation by one quarter, minimal risk",
            "decided_by": "MAJ Smith",
            "decision_date": (datetime.now() - timedelta(days=14)).isoformat()
        },
        {
            "decision_id": f"dec_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "analysis_id": analyses[2]["analysis_id"],
            "decision_text": "Modify lookalike model expansion to phased approach",
            "decision_type": "modify",
            "rationale": "Full implementation too aggressive. Start with 2,500 seed audience, evaluate after 30 days before full expansion",
            "impact": "Reduces risk while maintaining upside potential. Allows mid-course correction if needed",
            "decided_by": "MAJ Smith",
            "decision_date": (datetime.now() - timedelta(days=14)).isoformat()
        }
    ]
    
    for decision in decisions:
        cursor.execute("""
            INSERT OR REPLACE INTO twg_decisions
            (decision_id, board_id, analysis_id, decision_text, decision_type,
             rationale, impact, decided_by, decision_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision["decision_id"], decision["board_id"], decision.get("analysis_id"),
            decision["decision_text"], decision["decision_type"], decision["rationale"],
            decision["impact"], decision["decided_by"], decision["decision_date"]
        ))
    
    print(f"  ✅ Inserted {len(decisions)} decisions")
    
    # Sample action items
    actions = [
        {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "decision_id": decisions[0]["decision_id"],
            "action_text": "Submit budget reallocation request to finance",
            "assigned_to": "CPT Johnson",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "status": "completed",
            "priority": "high",
            "completion_notes": "Budget request approved, funds available from Q1 savings",
            "completed_date": (datetime.now() - timedelta(days=10)).isoformat()
        },
        {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "decision_id": decisions[0]["decision_id"],
            "action_text": "Develop Hispanic-focused creative assets for Dallas campaign",
            "assigned_to": "SFC Davis",
            "due_date": (datetime.now() + timedelta(days=21)).isoformat(),
            "status": "in_progress",
            "priority": "high"
        },
        {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "decision_id": decisions[1]["decision_id"],
            "action_text": "Coordinate with G2 for Navy partnership intel gathering",
            "assigned_to": "1SG Williams",
            "due_date": (datetime.now() + timedelta(days=45)).isoformat(),
            "status": "open",
            "priority": "medium"
        },
        {
            "action_id": f"act_{uuid.uuid4().hex[:8]}",
            "board_id": board1_id,
            "decision_id": decisions[2]["decision_id"],
            "action_text": "Configure lookalike model with 2,500 seed audience",
            "assigned_to": "SFC Davis",
            "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "status": "open",
            "priority": "critical"
        }
    ]
    
    for action in actions:
        cursor.execute("""
            INSERT OR REPLACE INTO twg_action_items
            (action_id, board_id, decision_id, action_text, assigned_to,
             due_date, status, priority, completion_notes, completed_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            action["action_id"], action["board_id"], action.get("decision_id"),
            action["action_text"], action["assigned_to"], action["due_date"],
            action["status"], action["priority"], action.get("completion_notes"),
            action.get("completed_date")
        ))
    
    print(f"  ✅ Inserted {len(actions)} action items")
    
    conn.commit()
    conn.close()
    
    print("\n✅ TWG sample data populated successfully!")
    print(f"   📊 {len(boards)} boards, {len(analyses)} analyses, {len(decisions)} decisions, {len(actions)} actions")


if __name__ == "__main__":
    try:
        generate_sample_twg_data()
    except Exception as e:
        print(f"❌ Error populating TWG data: {e}")
        import traceback
        traceback.print_exc()
