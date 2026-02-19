# TAAIP Enterprise Requirements - Gap Analysis & Implementation Roadmap

**Date:** November 17, 2025  
**Version:** 2.0  
**Status:** Planning Phase

---

## Executive Summary

This document provides a comprehensive assessment of the current TAAIP implementation against enterprise requirements for USAREC operational integration, including database capabilities, live data integration, compliance, archival, and collaboration features.

---

## Current State Assessment

### ✅ **Currently Implemented**

#### 1. Database Integration (SQLite)
- **Status:** ✅ **PARTIAL** - Basic implementation exists
- **Current Capabilities:**
  - SQLite database (`taaip.sqlite3`) for local data persistence
  - Relational schema with foreign keys
  - Tables for:
    - Leads tracking
    - Events & event metrics
    - Marketing activities
    - Projects, tasks, milestones
    - Funnel stages & transitions
    - Budgets & cost allocations
    - Segment profiles & history
    - Data source mappings (metadata only)
    - Forecasts & analytics snapshots

#### 2. Python Backend
- **Status:** ✅ **IMPLEMENTED**
- FastAPI backend (`taaip_service.py`) with REST API
- Pydantic models for data validation
- SQLite query/insert capabilities
- JSON export functionality

#### 3. Basic Data Sources (Metadata)
- **Status:** ⚠️ **PLACEHOLDER ONLY**
- Data source mapping table exists with references to:
  - EMM (Enterprise Marketing Manager)
  - iKrome
  - Vantage
  - G2 Report Zone
  - AIEM
  - USAREC Systems
- **Gap:** No actual API integration or live data pull

---

## ❌ **Major Gaps Requiring Implementation**

### 1. Production-Grade Relational Database

#### Current Limitation:
- SQLite is file-based, single-writer, not suitable for multi-user enterprise deployment

#### Required Implementation:
**Migrate to PostgreSQL or Microsoft SQL Server**

**Why:**
- Multi-user concurrent access
- Row-level locking
- Better security & audit trails
- Native integration with Army enterprise infrastructure
- Support for stored procedures & advanced queries
- Backup & replication capabilities

**Implementation Plan:**
```python
# NEW: database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Support for PostgreSQL or SQL Server
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/taaip_prod"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Action Items:**
- [ ] Install PostgreSQL or configure connection to Army SQL Server
- [ ] Convert SQLite schema to PostgreSQL/SQL Server DDL
- [ ] Implement SQLAlchemy ORM models
- [ ] Add connection pooling & retry logic
- [ ] Create migration scripts from SQLite to production DB
- [ ] Add database health monitoring endpoint

---

### 2. Live Data Integration from USAREC Systems

#### Current Limitation:
- NO live data integration implemented
- All data is mock/simulated

#### Required Implementation:
**A. API Integration Layer**

Create dedicated connectors for each system:

```python
# NEW: integrations/emm_connector.py
class EMMConnector:
    """Enterprise Marketing Manager integration"""
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        
    async def fetch_leads(self, start_date: str, end_date: str):
        """Pull leads from EMM system"""
        # Implement OAuth2 or API key authentication
        # Poll EMM API endpoints
        # Return normalized lead data
        pass
        
    async def sync_campaigns(self):
        """Sync campaign data from EMM"""
        pass

# NEW: integrations/ikrome_connector.py
class IKromeConnector:
    """iKrome analytics platform integration"""
    async def fetch_attribution_data(self, campaign_id: str):
        pass
        
# NEW: integrations/sprinklr_connector.py
class SprinklrConnector:
    """Social media analytics from Sprinklr"""
    async def fetch_social_metrics(self, date_range: dict):
        """Pull engagement, impressions, reach data"""
        return {
            "impressions": 0,
            "engagements": 0,
            "reach": 0,
            "clicks": 0,
            "shares": 0,
            "comments": 0,
            "platform_breakdown": {}
        }

# NEW: integrations/recruiter_zone_connector.py
class RecruiterZoneConnector:
    """Integration with Recruiter Zone CRM"""
    async def fetch_recruiter_activities(self):
        pass
        
# NEW: integrations/vantage_connector.py
class VantageConnector:
    """Marketing performance data from Vantage"""
    async def fetch_channel_performance(self):
        pass
        
# NEW: integrations/g2_zone_connector.py
class G2ZoneConnector:
    """USAREC G2 intelligence reports"""
    async def fetch_market_intelligence(self):
        pass
```

**B. Data Sync Scheduler**

```python
# NEW: scheduler/data_sync.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from integrations import (
    EMMConnector, IKromeConnector, SprinklrConnector,
    RecruiterZoneConnector, VantageConnector, G2ZoneConnector
)

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=15)
async def sync_emm_leads():
    """Pull new leads from EMM every 15 minutes"""
    connector = EMMConnector(api_key=os.getenv("EMM_API_KEY"))
    leads = await connector.fetch_leads()
    # Store in database with timestamp
    
@scheduler.scheduled_job('interval', hours=1)
async def sync_sprinklr_metrics():
    """Update social media metrics hourly"""
    connector = SprinklrConnector(api_key=os.getenv("SPRINKLR_API_KEY"))
    metrics = await connector.fetch_social_metrics()
    # Update marketing_activities table
    
@scheduler.scheduled_job('cron', hour=3, minute=0)
async def nightly_full_sync():
    """Complete data refresh overnight"""
    # Sync all systems
    pass
```

**Action Items:**
- [ ] Obtain API credentials & documentation for each system
- [ ] Implement OAuth2/API key authentication for each connector
- [ ] Create data normalization layer (different systems = different schemas)
- [ ] Add rate limiting & retry logic
- [ ] Implement incremental sync (only pull new/changed records)
- [ ] Add sync status monitoring dashboard
- [ ] Log all API calls for audit trail
- [ ] Handle system downtime gracefully (fallback to cached data)

---

### 3. Real-Time Dashboard Updates (WebSockets)

#### Current Limitation:
- Frontend uses static data, requires manual refresh

#### Required Implementation:

```python
# NEW: Add WebSocket support to FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: dict):
        """Push updates to all connected dashboards"""
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Trigger updates when data changes
async def on_new_lead(lead_data: dict):
    await manager.broadcast({
        "type": "lead_update",
        "data": lead_data,
        "timestamp": datetime.utcnow().isoformat()
    })
```

**Frontend (React):**
```typescript
// NEW: taaip-dashboard/src/hooks/useRealtimeData.ts
import { useEffect, useState } from 'react';

export function useRealtimeData() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setData(update);
    };
    
    return () => ws.close();
  }, []);
  
  return data;
}
```

**Action Items:**
- [ ] Add WebSocket endpoint to FastAPI
- [ ] Implement connection manager for multiple clients
- [ ] Update React dashboard to use WebSocket hook
- [ ] Add reconnection logic for network failures
- [ ] Implement authentication for WebSocket connections
- [ ] Add real-time KPI updates
- [ ] Create live event feed component

---

### 4. Data Validation Layer

#### Current Limitation:
- Basic Pydantic validation only

#### Required Implementation:

```python
# NEW: validation/data_quality.py
from typing import Dict, List, Any
from datetime import datetime

class DataValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: bool = True
        
class DataValidator:
    """Multi-layer data validation before publishing"""
    
    @staticmethod
    def validate_lead(lead_data: Dict[str, Any]) -> DataValidationResult:
        result = DataValidationResult()
        
        # Layer 1: Schema validation (Pydantic already does this)
        
        # Layer 2: Business logic validation
        if lead_data.get('age') and lead_data['age'] < 17:
            result.errors.append("Age below minimum Army eligibility")
            result.passed = False
            
        if lead_data.get('age') and lead_data['age'] > 42:
            result.warnings.append("Age above typical recruiting range")
            
        # Layer 3: Data quality checks
        if not lead_data.get('email') and not lead_data.get('phone'):
            result.errors.append("Missing contact information")
            result.passed = False
            
        # Layer 4: Duplicate detection
        # Check if lead_id already exists in database
        
        # Layer 5: PII compliance check
        if not DataValidator._is_pii_compliant(lead_data):
            result.errors.append("PII handling violation")
            result.passed = False
            
        return result
        
    @staticmethod
    def validate_metric(metric_data: Dict[str, Any]) -> DataValidationResult:
        result = DataValidationResult()
        
        # Check for negative values where inappropriate
        if metric_data.get('cost_per_lead', 0) < 0:
            result.errors.append("Negative CPL value")
            result.passed = False
            
        # Check for outliers
        if metric_data.get('cost_per_lead', 0) > 5000:
            result.warnings.append("Unusually high CPL - verify accuracy")
            
        return result
        
    @staticmethod
    def validate_export(data: List[Dict], export_type: str) -> DataValidationResult:
        """Validate data before export/publication"""
        result = DataValidationResult()
        
        # Ensure no sensitive data in public exports
        # Check for completeness
        # Verify date ranges
        
        return result

# Apply validation to all API endpoints
@app.post("/api/v2/leads")
async def submit_lead(lead: LeadInput):
    validation = DataValidator.validate_lead(lead.dict())
    if not validation.passed:
        raise HTTPException(status_code=422, detail={
            "errors": validation.errors,
            "warnings": validation.warnings
        })
    # Proceed with storage
```

**Action Items:**
- [ ] Implement comprehensive validation rules
- [ ] Add data quality scoring (0-100)
- [ ] Create validation dashboard showing data quality metrics
- [ ] Add manual review queue for flagged records
- [ ] Implement automated data cleaning for common issues
- [ ] Log all validation failures for analysis

---

### 5. Historical Data Archival (No Deletion Policy)

#### Current Limitation:
- No explicit archival strategy

#### Required Implementation:

```python
# NEW: archival/retention_policy.py
from sqlalchemy import Column, String, DateTime, Boolean, Text
from database.connection import Base

class ArchivedRecord(Base):
    __tablename__ = "archived_records"
    
    archive_id = Column(String, primary_key=True)
    original_table = Column(String, nullable=False)
    original_id = Column(String, nullable=False)
    record_data = Column(Text, nullable=False)  # JSON
    archived_at = Column(DateTime, default=datetime.utcnow)
    archived_by = Column(String)
    archive_reason = Column(String)
    is_deleted = Column(Boolean, default=False)  # Soft delete flag

class ArchivalManager:
    """Manage data retention and historical archiving"""
    
    @staticmethod
    async def archive_record(table: str, record_id: str, reason: str):
        """Archive a record instead of deleting it"""
        # Fetch original record
        # Store in archived_records with full JSON snapshot
        # Mark original as archived (add is_archived column to all tables)
        pass
        
    @staticmethod
    async def archive_dashboard(dashboard_id: str, user_id: str):
        """Save dashboard configuration for historical reference"""
        pass
        
    @staticmethod
    async def archive_report(report_id: str, generated_by: str):
        """Preserve generated reports indefinitely"""
        pass
        
    @staticmethod
    async def retrieve_historical_data(
        table: str,
        start_date: str,
        end_date: str
    ):
        """Query historical/archived data"""
        pass

# Add soft-delete columns to all tables
"""
ALTER TABLE leads ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN archived_at TIMESTAMP;
ALTER TABLE events ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
-- etc for all tables
"""

# Modify delete endpoints to archive instead
@app.delete("/api/v2/leads/{lead_id}")
async def archive_lead(lead_id: str, reason: str):
    """Archive lead instead of deleting"""
    await ArchivalManager.archive_record("leads", lead_id, reason)
    return {"status": "archived", "lead_id": lead_id}
```

**Archival Storage Schema:**
```sql
CREATE TABLE archived_dashboards (
    dashboard_id TEXT PRIMARY KEY,
    name TEXT,
    created_by TEXT,
    created_at TIMESTAMP,
    archived_at TIMESTAMP,
    configuration JSONB,  -- Full dashboard state
    version INTEGER
);

CREATE TABLE archived_reports (
    report_id TEXT PRIMARY KEY,
    report_type TEXT,
    generated_by TEXT,
    generated_at TIMESTAMP,
    parameters JSONB,
    data_snapshot JSONB,  -- Full report data
    pdf_path TEXT,
    archived_at TIMESTAMP
);
```

**Action Items:**
- [ ] Add `is_archived` and `archived_at` columns to all tables
- [ ] Create `archived_records` table
- [ ] Implement archival API endpoints
- [ ] Add "View Archived" UI option to all dashboards
- [ ] Create historical data query interface
- [ ] Implement retention policy enforcement (auto-archive old data)
- [ ] Add audit log for all archive operations

---

### 6. Army/USAREC Policy Compliance Engine

#### Current Limitation:
- No policy validation or auto-update capability

#### Required Implementation:

```python
# NEW: compliance/policy_engine.py
import requests
from datetime import datetime

class PolicyEngine:
    """Track and enforce Army/USAREC regulations"""
    
    def __init__(self):
        self.policies = []
        self.last_update = None
        
    async def fetch_policy_updates(self):
        """
        Pull latest policies from Army/USAREC sources
        - Army Regulations (ARs)
        - USAREC Regulations
        - ALARACT messages
        - Local SOPs
        """
        sources = [
            "https://armypubs.army.mil/",  # Army Publishing Directorate
            # USAREC internal policy portal (requires CAC authentication)
        ]
        # Parse and store policy documents
        # Flag changes from previous version
        
    def validate_against_policy(self, action: str, data: dict) -> dict:
        """Check if action complies with current policies"""
        violations = []
        warnings = []
        
        # Example: Check PII handling per AR 25-22
        if action == "export_data":
            if self._contains_pii(data) and not data.get('pii_approved'):
                violations.append("AR 25-22: PII export requires approval")
                
        # Example: Check recruiting age requirements
        if action == "create_lead":
            if data.get('age', 99) < 17:
                violations.append("AR 601-210: Below minimum age for Army enlistment")
                
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "policy_version": self.last_update
        }
        
    async def generate_compliance_report(self):
        """Generate report showing policy adherence"""
        pass

# NEW: compliance/policy_database.py
# Store policy versions and change history
CREATE TABLE policies (
    policy_id TEXT PRIMARY KEY,
    policy_number TEXT,  -- e.g., "AR 601-210"
    title TEXT,
    effective_date DATE,
    version TEXT,
    full_text TEXT,
    summary TEXT,
    relevant_sections JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE policy_checks (
    check_id TEXT PRIMARY KEY,
    action_type TEXT,
    policy_id TEXT REFERENCES policies(policy_id),
    check_result BOOLEAN,
    details TEXT,
    checked_at TIMESTAMP
);
```

**Action Items:**
- [ ] Compile list of applicable Army/USAREC regulations
- [ ] Create policy database schema
- [ ] Implement policy update scheduler (check weekly)
- [ ] Add compliance validation to all data operations
- [ ] Create compliance dashboard
- [ ] Implement alerts for policy violations
- [ ] Add manual policy override workflow (with justification logging)
- [ ] Generate quarterly compliance reports

---

### 7. SharePoint Integration & Collaboration

#### Current Limitation:
- No SharePoint or collaboration features

#### Required Implementation:

```python
# NEW: integrations/sharepoint_connector.py
from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext

class SharePointConnector:
    """Microsoft SharePoint integration for document sharing"""
    
    def __init__(self, site_url: str, username: str, password: str):
        ctx_auth = UserCredential(username, password)
        self.ctx = ClientContext(site_url).with_credentials(ctx_auth)
        
    async def upload_report(self, file_path: str, sharepoint_folder: str):
        """Upload generated report to SharePoint"""
        with open(file_path, 'rb') as content_file:
            file_content = content_file.read()
            
        target_folder = self.ctx.web.get_folder_by_server_relative_url(sharepoint_folder)
        target_folder.upload_file(file_path, file_content).execute_query()
        
    async def create_dashboard_link(self, dashboard_id: str, sharepoint_path: str):
        """Create shareable link to dashboard"""
        # Generate secure link with permissions
        pass
        
    async def sync_dashboard_to_sharepoint(self, dashboard_config: dict):
        """Export dashboard as PDF/Excel to SharePoint"""
        pass

# NEW: collaboration/sharing.py
class DashboardSharing:
    """Manage dashboard sharing and permissions"""
    
    @staticmethod
    async def create_share_link(
        dashboard_id: str,
        created_by: str,
        permissions: str = "view"
    ) -> str:
        """Generate shareable link with access control"""
        share_token = generate_secure_token()
        
        # Store in database
        await db.execute("""
            INSERT INTO shared_dashboards 
            (share_id, dashboard_id, created_by, permissions, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (share_token, dashboard_id, created_by, permissions, expiry_date))
        
        return f"https://taaip.usarec.army.mil/shared/{share_token}"
        
    @staticmethod
    async def get_shared_dashboard(share_token: str):
        """Retrieve dashboard from share link"""
        # Check if token is valid and not expired
        # Return dashboard configuration
        pass

# Add database tables
CREATE TABLE shared_dashboards (
    share_id TEXT PRIMARY KEY,
    dashboard_id TEXT NOT NULL,
    created_by TEXT,
    shared_with TEXT,  -- Email or user ID
    permissions TEXT DEFAULT 'view',  -- view, edit, admin
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP
);

CREATE TABLE dashboard_collaborators (
    collaboration_id TEXT PRIMARY KEY,
    dashboard_id TEXT,
    user_id TEXT,
    role TEXT,  -- owner, editor, viewer
    added_at TIMESTAMP,
    added_by TEXT
);
```

**Action Items:**
- [ ] Set up SharePoint site for TAAIP
- [ ] Implement SharePoint authentication (CAC-compatible)
- [ ] Add "Share Dashboard" UI button
- [ ] Create permission management interface
- [ ] Implement auto-sync of reports to SharePoint
- [ ] Add email notifications for shared dashboards
- [ ] Create collaboration audit log
- [ ] Implement role-based access control (RBAC)

---

### 8. Sprinklr Social Media Metrics Integration

#### Current Limitation:
- No Sprinklr integration

#### Required Implementation:

```python
# NEW: integrations/sprinklr_connector.py (expanded)
import aiohttp
from typing import Dict, List

class SprinklrAPIClient:
    """Full Sprinklr API integration for USAREC social media"""
    
    def __init__(self, api_key: str, client_id: str):
        self.api_key = api_key
        self.client_id = client_id
        self.base_url = "https://api2.sprinklr.com/api/v2"
        
    async def get_post_metrics(
        self,
        start_date: str,
        end_date: str,
        platforms: List[str] = None
    ) -> Dict:
        """
        Fetch engagement metrics for USAREC social media posts
        Platforms: Facebook, Instagram, Twitter/X, LinkedIn, TikTok, YouTube
        """
        metrics = {
            "total_posts": 0,
            "total_impressions": 0,
            "total_engagements": 0,
            "total_reach": 0,
            "by_platform": {},
            "top_performing_posts": [],
            "engagement_rate": 0.0
        }
        
        # Call Sprinklr API endpoints
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Example: Get post performance
            url = f"{self.base_url}/analytics/posts"
            params = {
                "startTime": start_date,
                "endTime": end_date,
                "metrics": "impressions,engagements,reach,clicks,shares,comments"
            }
            
            async with session.get(url, headers=headers, params=params) as resp:
                data = await resp.json()
                # Process and normalize data
                
        return metrics
        
    async def get_audience_insights(self) -> Dict:
        """Fetch demographic and behavioral insights"""
        pass
        
    async def get_sentiment_analysis(self, date_range: dict) -> Dict:
        """Analyze sentiment of comments/mentions"""
        pass
        
    async def get_campaign_performance(self, campaign_id: str) -> Dict:
        """Track specific recruiting campaign performance"""
        pass

# Add Sprinklr metrics to dashboard
@app.get("/api/v2/social-media/metrics")
async def get_social_metrics(start_date: str, end_date: str):
    """Endpoint for social media metrics"""
    sprinklr = SprinklrAPIClient(
        api_key=os.getenv("SPRINKLR_API_KEY"),
        client_id=os.getenv("SPRINKLR_CLIENT_ID")
    )
    
    metrics = await sprinklr.get_post_metrics(start_date, end_date)
    
    # Store in database
    await store_social_metrics(metrics)
    
    return metrics

# Database table for social metrics
CREATE TABLE social_media_metrics (
    metric_id TEXT PRIMARY KEY,
    platform TEXT,
    post_id TEXT,
    post_date TIMESTAMP,
    impressions INTEGER,
    engagements INTEGER,
    reach INTEGER,
    clicks INTEGER,
    shares INTEGER,
    comments INTEGER,
    likes INTEGER,
    video_views INTEGER,
    engagement_rate REAL,
    sentiment_score REAL,
    campaign_id TEXT,
    created_at TIMESTAMP
);
```

**Action Items:**
- [ ] Obtain Sprinklr API credentials from USAREC PAO
- [ ] Map Sprinklr account structure to TAAIP
- [ ] Create social media dashboard panel
- [ ] Implement hourly metric sync
- [ ] Add social media performance KPIs
- [ ] Create alerts for high-performing posts
- [ ] Build sentiment tracking dashboard
- [ ] Add competitive benchmarking (if available)

---

### 9. Project & Event Status Tracking

#### Current Limitation:
- Basic project table exists but no status dashboard

#### Required Implementation:

```python
# NEW: project_management/tracker.py
from enum import Enum

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class FundingStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    ALLOCATED = "allocated"
    SPENT = "spent"
    RECONCILED = "reconciled"

# Expand projects table
"""
ALTER TABLE projects ADD COLUMN funding_status TEXT DEFAULT 'requested';
ALTER TABLE projects ADD COLUMN funding_amount REAL DEFAULT 0.0;
ALTER TABLE projects ADD COLUMN spent_amount REAL DEFAULT 0.0;
ALTER TABLE projects ADD COLUMN percent_complete INTEGER DEFAULT 0;
ALTER TABLE projects ADD COLUMN risk_level TEXT;
ALTER TABLE projects ADD COLUMN next_milestone TEXT;
ALTER TABLE projects ADD COLUMN blockers TEXT;
"""

@app.get("/api/v2/projects/dashboard")
async def get_project_dashboard():
    """Get overview of all projects and their status"""
    conn = get_db_conn()
    
    projects = conn.execute("""
        SELECT 
            p.*,
            COUNT(DISTINCT t.task_id) as total_tasks,
            SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
            COUNT(DISTINCT m.milestone_id) as total_milestones,
            SUM(CASE WHEN m.actual_date IS NOT NULL THEN 1 ELSE 0 END) as completed_milestones
        FROM projects p
        LEFT JOIN tasks t ON p.project_id = t.project_id
        LEFT JOIN milestones m ON p.project_id = m.project_id
        GROUP BY p.project_id
    """).fetchall()
    
    return {
        "projects": [dict(p) for p in projects],
        "summary": {
            "total_projects": len(projects),
            "at_risk": sum(1 for p in projects if p['risk_level'] == 'high'),
            "on_track": sum(1 for p in projects if p['status'] == 'in_progress'),
            "completed": sum(1 for p in projects if p['status'] == 'completed')
        }
    }

@app.get("/api/v2/events/status")
async def get_event_status():
    """Get real-time status of recruiting events"""
    conn = get_db_conn()
    
    events = conn.execute("""
        SELECT 
            e.*,
            em.leads_generated,
            em.conversion_count,
            em.roi,
            b.allocated_amount,
            b.spent_amount
        FROM events e
        LEFT JOIN event_metrics em ON e.event_id = em.event_id
        LEFT JOIN budgets b ON e.event_id = b.event_id
        WHERE e.status IN ('planned', 'in_progress')
        ORDER BY e.start_date
    """).fetchall()
    
    return {"events": [dict(e) for e in events]}

@app.get("/api/v2/funding/status")
async def get_funding_status():
    """Track funding allocation and spending"""
    conn = get_db_conn()
    
    funding = conn.execute("""
        SELECT 
            SUM(allocated_amount) as total_allocated,
            SUM(spent_amount) as total_spent,
            (SUM(allocated_amount) - SUM(spent_amount)) as remaining
        FROM budgets
        WHERE EXTRACT(YEAR FROM start_date) = EXTRACT(YEAR FROM CURRENT_DATE)
    """).fetchone()
    
    return dict(funding)
```

**Action Items:**
- [ ] Build project status dashboard UI
- [ ] Add event timeline view (Gantt chart)
- [ ] Create funding tracker widget
- [ ] Implement automatic risk detection (missed milestones, budget overruns)
- [ ] Add project progress reports
- [ ] Create project collaboration workspace
- [ ] Implement milestone notifications

---

## Implementation Priority Matrix

| Priority | Feature | Complexity | Timeline | Blocker |
|----------|---------|------------|----------|---------|
| **P0** | Production Database (PostgreSQL) | High | 2-3 weeks | Required for multi-user |
| **P0** | Data Validation Layer | Medium | 1-2 weeks | Compliance requirement |
| **P0** | Archival System (No Delete) | Medium | 1-2 weeks | Policy requirement |
| **P1** | EMM Integration | High | 3-4 weeks | API access needed |
| **P1** | Sprinklr Integration | Medium | 2 weeks | API credentials needed |
| **P1** | Real-time Dashboard Updates | Medium | 2 weeks | WebSocket implementation |
| **P2** | SharePoint Integration | Medium | 2-3 weeks | CAC authentication |
| **P2** | Policy Compliance Engine | High | 3-4 weeks | Policy documentation |
| **P2** | iKrome/Vantage Integration | High | 3-4 weeks | API access needed |
| **P3** | G2 Zone Integration | Medium | 2 weeks | Security clearance |
| **P3** | Recruiter Zone Integration | Medium | 2 weeks | API access needed |
| **P3** | Advanced Project Management | Low | 1-2 weeks | Nice-to-have |

---

## Technical Architecture Recommendations

### 1. Microservices Architecture
Instead of monolithic service, split into:
- **API Gateway** (already exists: `api-gateway.js`)
- **Core Data Service** (FastAPI)
- **Integration Service** (handles all external APIs)
- **Validation Service** (data quality checks)
- **Archival Service** (historical data management)
- **Notification Service** (alerts, emails, WebSocket)

### 2. Message Queue for Async Processing
Add RabbitMQ or Redis for:
- Async data sync jobs
- Report generation
- Email notifications
- Webhook processing

```python
# NEW: messaging/queue.py
from celery import Celery

celery_app = Celery('taaip', broker='redis://localhost:6379/0')

@celery_app.task
def sync_emm_data():
    """Background task to sync EMM data"""
    pass
    
@celery_app.task
def generate_report(report_id: str):
    """Generate report asynchronously"""
    pass
```

### 3. Caching Layer
Add Redis for:
- API response caching
- Session management
- Real-time dashboard data

### 4. Security Enhancements
- [ ] Implement CAC (Common Access Card) authentication
- [ ] Add role-based access control (RBAC)
- [ ] Encrypt sensitive data at rest
- [ ] Add audit logging for all operations
- [ ] Implement rate limiting on APIs
- [ ] Add IP whitelisting for admin functions

---

## Deployment Recommendations

### Production Environment:
- **Server:** Army-approved cloud (cATO compliant) or on-prem
- **Database:** PostgreSQL 14+ or SQL Server 2019+
- **Container Orchestration:** Kubernetes (already have k8s configs)
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Backup:** Daily automated backups with 7-year retention

---

## Estimated Timeline

**Phase 1 (Months 1-2): Core Infrastructure**
- PostgreSQL migration
- Data validation layer
- Archival system
- Basic authentication

**Phase 2 (Months 3-4): Primary Integrations**
- EMM integration
- Sprinklr integration
- Real-time dashboard updates
- SharePoint basic integration

**Phase 3 (Months 5-6): Advanced Features**
- iKrome/Vantage/G2 Zone integrations
- Policy compliance engine
- Advanced project management
- Full SharePoint collaboration

**Phase 4 (Months 7-8): Testing & Hardening**
- Security audit
- Load testing
- User acceptance testing
- Documentation & training

---

## Next Steps

1. **Immediate Actions:**
   - [ ] Schedule meeting with USAREC G6/IT for system access
   - [ ] Request API credentials for all external systems
   - [ ] Set up PostgreSQL development instance
   - [ ] Document current data flows

2. **Within 1 Week:**
   - [ ] Create detailed technical specifications
   - [ ] Set up development environment with production-like DB
   - [ ] Begin database migration scripts
   - [ ] Start validation layer implementation

3. **Within 1 Month:**
   - [ ] Complete core infrastructure (DB, validation, archival)
   - [ ] Begin EMM integration development
   - [ ] Set up Sprinklr test account
   - [ ] Implement first iteration of real-time updates

---

## Questions Requiring Clarification

1. **Database:** Is there an existing Army PostgreSQL/SQL Server instance to use, or do we provision new?
2. **Authentication:** Will CAC authentication be required, or can we use username/password initially?
3. **API Access:** Who can provide API credentials and documentation for EMM, iKrome, Vantage, etc.?
4. **SharePoint:** What is the SharePoint site URL and access permissions?
5. **Sprinklr:** Does USAREC have a Sprinklr enterprise account? What's the account structure?
6. **Compliance:** Is there a designated compliance officer to review policy implementation?
7. **Deployment:** On-premise servers or Army cloud (e.g., cARMY)?

---

**Document Owner:** TAAIP Development Team  
**Last Updated:** November 17, 2025  
**Status:** Pending Review & Approval
