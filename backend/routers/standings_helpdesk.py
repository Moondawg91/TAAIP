"""
Company Standings and Help Desk API Router
Provides real-time company rankings and helpdesk ticket management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
import sqlite3
import random

router = APIRouter()

# Pydantic Models
class CompanyStanding(BaseModel):
    rank: int
    previous_rank: int
    company_id: str
    company_name: str
    battalion: str
    brigade: str
    rsid: str
    station: str
    ytd_mission: int
    ytd_actual: int
    ytd_attainment: float
    monthly_mission: int
    monthly_actual: int
    monthly_attainment: float
    total_enlistments: int
    future_soldier_losses: int
    net_gain: int
    last_enlistment: Optional[str]
    trend: Literal['up', 'down', 'stable']

class HelpdeskRequest(BaseModel):
    type: Literal['access_request', 'feature_request', 'bug_report', 'upgrade_request', 'training', 'other']
    priority: Literal['low', 'medium', 'high', 'critical']
    title: str
    description: str
    requestedAccessLevel: Optional[str] = None
    currentAccessLevel: Optional[str] = None
    submittedBy: str
    submittedAt: str

class UserAccess(BaseModel):
    userId: str
    name: str
    email: str
    dodId: str
    accessLevel: Literal['tier_1', 'tier_2', 'tier_3', 'tier_4']


@router.get("/standings/companies")
async def get_company_standings():
    """Get real-time company standings with YTD and monthly metrics"""
    try:
        conn = sqlite3.connect("data/taaip.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create standings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_standings (
                company_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                battalion TEXT,
                brigade TEXT,
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
                previous_rank INTEGER DEFAULT 999,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check if we need to seed data
        cursor.execute("SELECT COUNT(*) as count FROM company_standings")
        count = cursor.fetchone()['count']

        if count == 0:
            # Seed with sample company data
            brigades = ['1st BDE', '2nd BDE', '3rd BDE', '4th BDE', '5th BDE', '6th BDE']
            companies = []
            
            for bde_idx, brigade in enumerate(brigades, 1):
                for bn in range(1, 4):  # 3 battalions per brigade
                    battalion = f'{bde_idx * 3 - 3 + bn}BN'
                    for co in ['A', 'B', 'C']:  # 3 companies per battalion
                        company_id = f'{battalion}-{co}CO'
                        company_name = f'{co} Company, {battalion}'
                        
                        ytd_mission = random.randint(80, 150)
                        ytd_actual = random.randint(50, ytd_mission + 20)
                        ytd_attainment = (ytd_actual / ytd_mission * 100) if ytd_mission > 0 else 0
                        
                        monthly_mission = random.randint(15, 30)
                        monthly_actual = random.randint(8, monthly_mission + 5)
                        monthly_attainment = (monthly_actual / monthly_mission * 100) if monthly_mission > 0 else 0
                        
                        total_enlistments = ytd_actual
                        future_soldier_losses = random.randint(0, 15)
                        net_gain = total_enlistments - future_soldier_losses
                        
                        companies.append((
                            company_id, company_name, battalion, brigade,
                            ytd_mission, ytd_actual, ytd_attainment,
                            monthly_mission, monthly_actual, monthly_attainment,
                            total_enlistments, future_soldier_losses, net_gain,
                            datetime.now().isoformat() if random.random() > 0.3 else None
                        ))
            
            cursor.executemany("""
                INSERT INTO company_standings (
                    company_id, company_name, battalion, brigade,
                    ytd_mission, ytd_actual, ytd_attainment,
                    monthly_mission, monthly_actual, monthly_attainment,
                    total_enlistments, future_soldier_losses, net_gain,
                    last_enlistment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, companies)
            conn.commit()

        # Fetch current standings ordered by YTD attainment
        cursor.execute("""
            SELECT 
                company_id, company_name, battalion, brigade, rsid, station,
                ytd_mission, ytd_actual, ytd_attainment,
                monthly_mission, monthly_actual, monthly_attainment,
                total_enlistments, future_soldier_losses, net_gain,
                last_enlistment, previous_rank
            FROM company_standings
            ORDER BY ytd_attainment DESC, ytd_actual DESC, company_name ASC
        """)
        
        standings = []
        for idx, row in enumerate(cursor.fetchall(), 1):
            company = dict(row)
            current_rank = idx
            prev_rank = company['previous_rank']
            
            # Determine trend
            if prev_rank == 999:  # First time
                trend = 'stable'
            elif current_rank < prev_rank:
                trend = 'up'
            elif current_rank > prev_rank:
                trend = 'down'
            else:
                trend = 'stable'
            
            standings.append({
                'rank': current_rank,
                'previous_rank': prev_rank if prev_rank != 999 else current_rank,
                'company_id': company['company_id'],
                'company_name': company['company_name'],
                'battalion': company['battalion'],
                'brigade': company['brigade'],
                'ytd_mission': company['ytd_mission'],
                'ytd_actual': company['ytd_actual'],
                'ytd_attainment': round(company['ytd_attainment'], 2),
                'monthly_mission': company['monthly_mission'],
                'monthly_actual': company['monthly_actual'],
                'monthly_attainment': round(company['monthly_attainment'], 2),
                'total_enlistments': company['total_enlistments'],
                'future_soldier_losses': company['future_soldier_losses'],
                'net_gain': company['net_gain'],
                'last_enlistment': company['last_enlistment'],
                'trend': trend
            })
        
        # Update previous ranks for next comparison
        for standing in standings:
            cursor.execute("""
                UPDATE company_standings 
                SET previous_rank = ?
                WHERE company_id = ?
            """, (standing['rank'], standing['company_id']))
        
        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "standings": standings,
            "total_companies": len(standings),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching standings: {str(e)}")


@router.post("/standings/update")
async def update_company_standing(company_id: str, enlistment: Optional[bool] = None, loss: Optional[bool] = None):
    """Update company standing when an enlistment or loss occurs"""
    try:
        conn = sqlite3.connect("data/taaip.sqlite3")
        cursor = conn.cursor()

        if enlistment:
            cursor.execute("""
                UPDATE company_standings 
                SET 
                    ytd_actual = ytd_actual + 1,
                    ytd_attainment = (ytd_actual + 1) * 100.0 / ytd_mission,
                    monthly_actual = monthly_actual + 1,
                    monthly_attainment = (monthly_actual + 1) * 100.0 / monthly_mission,
                    total_enlistments = total_enlistments + 1,
                    net_gain = total_enlistments + 1 - future_soldier_losses,
                    last_enlistment = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = ?
            """, (datetime.now().isoformat(), company_id))
        
        if loss:
            cursor.execute("""
                UPDATE company_standings 
                SET 
                    future_soldier_losses = future_soldier_losses + 1,
                    net_gain = total_enlistments - (future_soldier_losses + 1),
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = ?
            """, (company_id,))

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "message": f"Company {company_id} standing updated",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating standing: {str(e)}")


@router.get("/helpdesk/requests")
async def get_helpdesk_requests(status: Optional[str] = None, user_id: Optional[str] = None):
    """Get helpdesk requests with optional filtering"""
    try:
        conn = sqlite3.connect("data/taaip.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create helpdesk_requests table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS helpdesk_requests (
                request_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requested_access_level TEXT,
                current_access_level TEXT,
                status TEXT DEFAULT 'pending',
                submitted_by TEXT NOT NULL,
                submitted_at TIMESTAMP NOT NULL,
                assigned_to TEXT,
                resolved_at TIMESTAMP,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        query = "SELECT * FROM helpdesk_requests WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if user_id:
            query += " AND submitted_by = ?"
            params.append(user_id)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        requests = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "status": "ok",
            "requests": requests,
            "total": len(requests)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching requests: {str(e)}")


@router.post("/helpdesk/requests")
async def create_helpdesk_request(request: HelpdeskRequest):
    """Submit a new helpdesk request"""
    try:
        conn = sqlite3.connect("data/taaip.sqlite3")
        cursor = conn.cursor()

        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS helpdesk_requests (
                request_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requested_access_level TEXT,
                current_access_level TEXT,
                status TEXT DEFAULT 'pending',
                submitted_by TEXT NOT NULL,
                submitted_at TIMESTAMP NOT NULL,
                assigned_to TEXT,
                resolved_at TIMESTAMP,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Generate request ID
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

        cursor.execute("""
            INSERT INTO helpdesk_requests (
                request_id, type, priority, title, description,
                requested_access_level, current_access_level,
                submitted_by, submitted_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id, request.type, request.priority, request.title, request.description,
            request.requestedAccessLevel, request.currentAccessLevel,
            request.submittedBy, request.submittedAt, 'pending'
        ))

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "message": "Helpdesk request submitted successfully",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating request: {str(e)}")


@router.get("/users/{user_id}/access")
async def get_user_access(user_id: str):
    """Get user access level and permissions"""
    try:
        conn = sqlite3.connect("data/taaip.sqlite3")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_access (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                dod_id TEXT UNIQUE NOT NULL,
                access_level TEXT DEFAULT 'tier_1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        cursor.execute("SELECT * FROM user_access WHERE user_id = ? OR dod_id = ?", (user_id, user_id))
        user = cursor.fetchone()
        conn.close()

        if not user:
            # Return default tier 1 access
            return {
                "status": "ok",
                "user": {
                    "userId": user_id,
                    "name": "Guest User",
                    "email": "",
                    "dodId": user_id,
                    "accessLevel": "tier_1",
                    "permissions": {
                        "canView": True,
                        "canEdit": False,
                        "canCreate": False,
                        "canDelete": False,
                        "canExport": False,
                        "canManageUsers": False,
                        "canAccessAdmin": False
                    }
                }
            }

        # Define permissions based on access level (Tier-based)
        access_level = user['access_level']
        permissions = {
            "tier_1": {
                "canView": True,
                "canEdit": False,
                "canCreate": False,
                "canDelete": False,
                "canExport": False,
                "canManageUsers": False,
                "canAccessAdmin": False
            },
            "tier_2": {
                "canView": True,
                "canEdit": False,
                "canCreate": False,
                "canDelete": False,
                "canExport": True,
                "canManageUsers": False,
                "canAccessAdmin": False
            },
            "tier_3": {
                "canView": True,
                "canEdit": True,
                "canCreate": True,
                "canDelete": False,
                "canExport": True,
                "canManageUsers": False,
                "canAccessAdmin": False
            },
            "tier_4": {
                "canView": True,
                "canEdit": True,
                "canCreate": True,
                "canDelete": True,
                "canExport": True,
                "canManageUsers": True,
                "canAccessAdmin": True
            }
        }

        return {
            "status": "ok",
            "user": {
                "userId": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "dodId": user['dod_id'],
                "accessLevel": access_level,
                "permissions": permissions.get(access_level, permissions['tier_1'])
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user access: {str(e)}")
