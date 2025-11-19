"""
Database Migration: Add Targeting Working Group (TWG) Tables
Enables review boards, analysis tracking, and approval workflows
"""
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = SCRIPT_DIR / "data" / "taaip.sqlite3"


def create_twg_tables():
    """Create Targeting Working Group tables for review boards and analysis"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔄 Creating Targeting Working Group (TWG) tables...")
    
    # TWG Review Boards table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twg_review_boards (
            board_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            project_id TEXT,
            event_id TEXT,
            review_type TEXT,  -- 'project', 'event', 'strategy', 'campaign'
            status TEXT DEFAULT 'scheduled',  -- 'scheduled', 'in_progress', 'completed', 'cancelled'
            scheduled_date DATETIME,
            completed_date DATETIME,
            facilitator TEXT,
            attendees TEXT,  -- JSON array of attendee names
            rsid TEXT,
            brigade TEXT,
            battalion TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    """)
    print("  ✅ Created 'twg_review_boards' table")
    
    # TWG Analysis Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twg_analysis_items (
            analysis_id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            category TEXT,  -- 'market_analysis', 'competitor_analysis', 'strategy', 'metrics', 'risks'
            title TEXT NOT NULL,
            description TEXT,
            findings TEXT,
            recommendations TEXT,
            priority TEXT DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
            status TEXT DEFAULT 'open',  -- 'open', 'in_review', 'approved', 'rejected', 'deferred'
            assigned_to TEXT,
            due_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES twg_review_boards(board_id)
        )
    """)
    print("  ✅ Created 'twg_analysis_items' table")
    
    # TWG Decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twg_decisions (
            decision_id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            analysis_id TEXT,
            decision_text TEXT NOT NULL,
            decision_type TEXT,  -- 'approve', 'reject', 'defer', 'modify', 'escalate'
            rationale TEXT,
            impact TEXT,  -- Expected impact of the decision
            action_items TEXT,  -- JSON array of follow-up actions
            decided_by TEXT,
            decision_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES twg_review_boards(board_id),
            FOREIGN KEY (analysis_id) REFERENCES twg_analysis_items(analysis_id)
        )
    """)
    print("  ✅ Created 'twg_decisions' table")
    
    # TWG Meeting Notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twg_meeting_notes (
            note_id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            section TEXT,  -- 'discussion', 'analysis', 'decisions', 'action_items', 'next_steps'
            content TEXT NOT NULL,
            author TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES twg_review_boards(board_id)
        )
    """)
    print("  ✅ Created 'twg_meeting_notes' table")
    
    # TWG Action Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twg_action_items (
            action_id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            decision_id TEXT,
            action_text TEXT NOT NULL,
            assigned_to TEXT,
            due_date DATETIME,
            status TEXT DEFAULT 'open',  -- 'open', 'in_progress', 'completed', 'blocked'
            priority TEXT DEFAULT 'medium',
            completion_notes TEXT,
            completed_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES twg_review_boards(board_id),
            FOREIGN KEY (decision_id) REFERENCES twg_decisions(decision_id)
        )
    """)
    print("  ✅ Created 'twg_action_items' table")
    
    # TWG Strategy Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS twg_strategy_documents (
            doc_id TEXT PRIMARY KEY,
            board_id TEXT,
            project_id TEXT,
            event_id TEXT,
            title TEXT NOT NULL,
            document_type TEXT,  -- 'strategy', 'analysis', 'market_research', 'competitive_intel', 'plan'
            content TEXT,
            version TEXT DEFAULT '1.0',
            status TEXT DEFAULT 'draft',  -- 'draft', 'review', 'approved', 'archived'
            author TEXT,
            approved_by TEXT,
            approved_date DATETIME,
            rsid TEXT,
            brigade TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES twg_review_boards(board_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    """)
    print("  ✅ Created 'twg_strategy_documents' table")
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_boards_project ON twg_review_boards(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_boards_event ON twg_review_boards(event_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_boards_rsid ON twg_review_boards(rsid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_analysis_board ON twg_analysis_items(board_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_decisions_board ON twg_decisions(board_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_actions_board ON twg_action_items(board_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_twg_docs_project ON twg_strategy_documents(project_id)")
    print("  ✅ Created TWG indexes")
    
    conn.commit()
    conn.close()
    
    print("✅ TWG tables created successfully!")
    print("\nTargeting Working Group Features:")
    print("  ✅ Review boards for projects/events")
    print("  ✅ Analysis items with recommendations")
    print("  ✅ Decision tracking with rationale")
    print("  ✅ Meeting notes and documentation")
    print("  ✅ Action items with assignments")
    print("  ✅ Strategy document management")


if __name__ == "__main__":
    try:
        create_twg_tables()
    except Exception as e:
        print(f"❌ TWG table creation failed: {e}")
        import traceback
        traceback.print_exc()
