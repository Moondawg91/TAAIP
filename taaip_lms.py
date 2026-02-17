"""
Minimal LMS for TAAIP
- Course management
- Enrollment tracking
- Progress tracking
- Reporting
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

LMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    duration_minutes INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    enrolled_at TEXT,
    completed_at TEXT,
    progress_percent INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    FOREIGN KEY(course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id TEXT NOT NULL,
    lesson_number INTEGER,
    completed_at TEXT,
    score INTEGER,
    FOREIGN KEY(enrollment_id) REFERENCES enrollments(enrollment_id)
);
"""

def init_lms_db(db_path: str):
    """Initialize LMS tables."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    for statement in LMS_SCHEMA.split(';'):
        if statement.strip():
            cur.execute(statement)
    
    conn.commit()
    conn.close()


class LMSManager:
    """Manage courses, enrollments, and progress tracking."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_lms_db(db_path)
        
        # Pre-load default courses
        self._create_default_courses()
    
    def _create_default_courses(self):
        """Create default courses if not exist."""
        courses = [
            {
                "course_id": "usarec-101",
                "title": "USAREC Fundamentals",
                "description": "Overview of USAREC recruiting mission, structure, and operations",
                "category": "Fundamentals",
                "duration_minutes": 120,
            },
            {
                "course_id": "segment-201",
                "title": "Market Segmentation & PRIZM",
                "description": "Deep dive into Claritas PRIZM segmentation and market analysis",
                "category": "Advanced",
                "duration_minutes": 90,
            },
            {
                "course_id": "scoring-301",
                "title": "Lead Scoring Mastery",
                "description": "Master AI-powered lead scoring and propensity prediction",
                "category": "Advanced",
                "duration_minutes": 75,
            },
        ]
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        for course in courses:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO courses 
                    (course_id, title, description, category, duration_minutes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (course["course_id"], course["title"], course["description"], 
                      course["category"], course["duration_minutes"], now, now))
            except Exception as e:
                print(f"Error creating course {course['course_id']}: {e}")
        
        conn.commit()
        conn.close()
    
    def enroll_user(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """Enroll a user in a course."""
        enrollment_id = f"enr_{user_id}_{course_id}_{int(datetime.utcnow().timestamp())}"
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO enrollments 
                (enrollment_id, user_id, course_id, enrolled_at, status)
                VALUES (?, ?, ?, ?, 'in_progress')
            """, (enrollment_id, user_id, course_id, now))
            conn.commit()
            return {"status": "ok", "enrollment_id": enrollment_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    def update_progress(self, enrollment_id: str, progress_percent: int) -> Dict[str, Any]:
        """Update course progress."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE enrollments SET progress_percent = ? WHERE enrollment_id = ?
            """, (min(100, max(0, progress_percent)), enrollment_id))
            
            # Mark as completed if 100%
            if progress_percent >= 100:
                now = datetime.utcnow().isoformat()
                cur.execute("""
                    UPDATE enrollments SET completed_at = ?, status = 'completed' 
                    WHERE enrollment_id = ? AND progress_percent >= 100
                """, (now, enrollment_id))
            
            conn.commit()
            return {"status": "ok", "progress": progress_percent}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
    
    def get_user_enrollments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all enrollments for a user."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT e.enrollment_id, e.course_id, c.title, e.progress_percent, 
                       e.status, e.enrolled_at, e.completed_at
                FROM enrollments e
                JOIN courses c ON e.course_id = c.course_id
                WHERE e.user_id = ?
                ORDER BY e.enrolled_at DESC
            """, (user_id,))
            
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def get_course_stats(self) -> Dict[str, Any]:
        """Get overall LMS statistics."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT COUNT(DISTINCT course_id) as total_courses FROM courses")
            total_courses = cur.fetchone()['total_courses']
            
            cur.execute("SELECT COUNT(*) as total_enrollments FROM enrollments")
            total_enrollments = cur.fetchone()['total_enrollments']
            
            cur.execute("SELECT COUNT(*) as completed FROM enrollments WHERE status = 'completed'")
            completed = cur.fetchone()['completed']
            
            cur.execute("SELECT AVG(progress_percent) as avg_progress FROM enrollments WHERE status = 'in_progress'")
            avg_progress = cur.fetchone()['avg_progress'] or 0
            
            return {
                "total_courses": total_courses,
                "total_enrollments": total_enrollments,
                "completed_enrollments": completed,
                "average_progress": round(avg_progress, 1),
                "completion_rate": round((completed / max(total_enrollments, 1)) * 100, 1),
            }
        finally:
            conn.close()


# Global LMS instance
lms_manager = None

def get_lms_manager(db_path: str) -> LMSManager:
    """Get or create LMS manager."""
    global lms_manager
    if lms_manager is None:
        lms_manager = LMSManager(db_path)
    return lms_manager
