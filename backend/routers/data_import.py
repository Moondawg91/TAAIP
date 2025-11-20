"""
Data Import API Router
Handles bulk CSV/Excel file uploads for events, projects, leads, and other data
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import pandas as pd
import io
import sqlite3
from datetime import datetime

router = APIRouter()

# Database connection
def get_db():
    conn = sqlite3.connect("data/recruiting.db")
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/import/events")
async def import_events(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import events from CSV/Excel file
    
    Expected columns:
    - name (required)
    - type (optional, defaults to 'recruitment_event')
    - location (required)
    - start_date (required, format: YYYY-MM-DD)
    - end_date (required, format: YYYY-MM-DD)
    - budget (optional, defaults to 0)
    - team_size (optional, defaults to 0)
    - targeting_principles (optional)
    - status (optional, defaults to 'planned')
    """
    try:
        # Read file based on extension
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        # Validate required columns
        required_cols = ['name', 'location', 'start_date', 'end_date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Connect to database
        db = get_db()
        cursor = db.cursor()
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                event_id = f"EVT-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                cursor.execute("""
                    INSERT INTO events (
                        event_id, name, type, location, start_date, end_date,
                        budget, team_size, targeting_principles, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    row['name'],
                    row.get('type', 'recruitment_event'),
                    row['location'],
                    row['start_date'],
                    row['end_date'],
                    row.get('budget', 0),
                    row.get('team_size', 0),
                    row.get('targeting_principles', ''),
                    row.get('status', 'planned'),
                    datetime.now().isoformat()
                ))
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "imported": imported_count,
            "total_rows": len(df),
            "errors": errors if errors else None,
            "message": f"Successfully imported {imported_count} of {len(df)} events"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/projects")
async def import_projects(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import projects from CSV/Excel file
    
    Expected columns:
    - name (required)
    - owner_id (required)
    - start_date (required, format: YYYY-MM-DD)
    - target_date (required, format: YYYY-MM-DD)
    - objectives (required)
    - event_id (optional)
    - funding_amount (optional, defaults to 0)
    - status (optional, defaults to 'planning')
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['name', 'owner_id', 'start_date', 'target_date', 'objectives']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        db = get_db()
        cursor = db.cursor()
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                project_id = f"PRJ-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                cursor.execute("""
                    INSERT INTO projects (
                        project_id, name, event_id, start_date, target_date,
                        owner_id, status, objectives, funding_amount, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    row['name'],
                    row.get('event_id', ''),
                    row['start_date'],
                    row['target_date'],
                    row['owner_id'],
                    row.get('status', 'planning'),
                    row['objectives'],
                    row.get('funding_amount', 0),
                    datetime.now().isoformat()
                ))
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "imported": imported_count,
            "total_rows": len(df),
            "errors": errors if errors else None,
            "message": f"Successfully imported {imported_count} of {len(df)} projects"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/leads")
async def import_leads(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import leads from CSV/Excel file
    
    Expected columns:
    - age (required, 17-42)
    - education_level (required)
    - cbsa_code (required)
    - campaign_source (required)
    - propensity_score (optional, 1-10)
    - lead_id (optional, auto-generated if not provided)
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['age', 'education_level', 'cbsa_code', 'campaign_source']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        db = get_db()
        cursor = db.cursor()
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Validate age
                age = int(row['age'])
                if age < 17 or age > 42:
                    raise ValueError(f"Age must be between 17 and 42, got {age}")
                
                lead_id = row.get('lead_id', f"LEAD-{int(datetime.now().timestamp() * 1000)}-{index}")
                
                # Calculate simple score (can be enhanced with ML model)
                propensity = row.get('propensity_score', 5)
                score = min(100, max(0, (propensity * 10) + (age * 0.5)))
                
                cursor.execute("""
                    INSERT INTO leads (
                        lead_id, age, education_level, cbsa_code, campaign_source,
                        propensity_score, score, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    age,
                    row['education_level'],
                    row['cbsa_code'],
                    row['campaign_source'],
                    propensity,
                    score,
                    datetime.now().isoformat()
                ))
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "imported": imported_count,
            "total_rows": len(df),
            "errors": errors if errors else None,
            "message": f"Successfully imported {imported_count} of {len(df)} leads"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/import/templates")
async def get_templates() -> Dict[str, Any]:
    """Get CSV template information for each data type"""
    return {
        "events": {
            "columns": [
                {"name": "name", "required": True, "example": "Spring Job Fair 2025"},
                {"name": "type", "required": False, "example": "recruitment_event"},
                {"name": "location", "required": True, "example": "San Antonio, TX"},
                {"name": "start_date", "required": True, "example": "2025-03-15"},
                {"name": "end_date", "required": True, "example": "2025-03-15"},
                {"name": "budget", "required": False, "example": "5000"},
                {"name": "team_size", "required": False, "example": "10"},
                {"name": "targeting_principles", "required": False, "example": "D3AE, F3A"},
                {"name": "status", "required": False, "example": "planned"}
            ]
        },
        "projects": {
            "columns": [
                {"name": "name", "required": True, "example": "Q1 Digital Campaign"},
                {"name": "owner_id", "required": True, "example": "SSG Smith"},
                {"name": "start_date", "required": True, "example": "2025-01-01"},
                {"name": "target_date", "required": True, "example": "2025-03-31"},
                {"name": "objectives", "required": True, "example": "Increase leads by 20%"},
                {"name": "event_id", "required": False, "example": "EVT-12345"},
                {"name": "funding_amount", "required": False, "example": "25000"},
                {"name": "status", "required": False, "example": "in_progress"}
            ]
        },
        "leads": {
            "columns": [
                {"name": "age", "required": True, "example": "20"},
                {"name": "education_level", "required": True, "example": "High School"},
                {"name": "cbsa_code", "required": True, "example": "41700"},
                {"name": "campaign_source", "required": True, "example": "social_media"},
                {"name": "propensity_score", "required": False, "example": "7"},
                {"name": "lead_id", "required": False, "example": "LEAD-001"}
            ]
        }
    }
