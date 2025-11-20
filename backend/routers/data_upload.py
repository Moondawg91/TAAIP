"""
Enhanced Data Upload API Router
Handles bulk CSV/Excel file uploads for all recruiting pipeline data types
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


@router.post("/upload/leads")
async def upload_leads(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import leads from CSV/Excel file
    
    Required columns:
    - first_name
    - last_name
    - date_of_birth (format: YYYY-MM-DD)
    - education_code
    - phone_number
    - lead_source
    - prid
    
    Optional columns:
    - cbsa_code
    - middle_name
    - address
    - asvab_score
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid']
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
                lead_id = row.get('lead_id', f"LEAD-{int(datetime.now().timestamp() * 1000)}-{index}")
                
                # Calculate age from date of birth
                dob = pd.to_datetime(row['date_of_birth'])
                age = (datetime.now() - dob).days // 365
                
                cursor.execute("""
                    INSERT INTO leads (
                        lead_id, first_name, last_name, middle_name, date_of_birth,
                        age, education_code, phone_number, address, cbsa_code,
                        lead_source, prid, asvab_score, received_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id,
                    row['first_name'],
                    row['last_name'],
                    row.get('middle_name', ''),
                    row['date_of_birth'],
                    age,
                    row['education_code'],
                    row['phone_number'],
                    row.get('address', ''),
                    row.get('cbsa_code', ''),
                    row['lead_source'],
                    row['prid'],
                    row.get('asvab_score', None),
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


@router.post("/upload/prospects")
async def upload_prospects(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import prospects from CSV/Excel file
    
    Required columns:
    - first_name
    - last_name
    - date_of_birth
    - education_code
    - phone_number
    - lead_source
    - prid
    - prospect_status (contacted, interested, qualified, etc.)
    
    Optional columns:
    - cbsa_code, middle_name, address, asvab_score
    - last_contact_date
    - recruiter_assigned
    - notes
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid', 'prospect_status']
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
                prospect_id = f"PROS-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                dob = pd.to_datetime(row['date_of_birth'])
                age = (datetime.now() - dob).days // 365
                
                cursor.execute("""
                    INSERT INTO prospects (
                        prospect_id, first_name, last_name, middle_name, date_of_birth,
                        age, education_code, phone_number, address, cbsa_code,
                        lead_source, prid, asvab_score, prospect_status,
                        last_contact_date, recruiter_assigned, notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prospect_id,
                    row['first_name'],
                    row['last_name'],
                    row.get('middle_name', ''),
                    row['date_of_birth'],
                    age,
                    row['education_code'],
                    row['phone_number'],
                    row.get('address', ''),
                    row.get('cbsa_code', ''),
                    row['lead_source'],
                    row['prid'],
                    row.get('asvab_score', None),
                    row['prospect_status'],
                    row.get('last_contact_date', None),
                    row.get('recruiter_assigned', ''),
                    row.get('notes', ''),
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
            "message": f"Successfully imported {imported_count} of {len(df)} prospects"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/upload/applicants")
async def upload_applicants(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import applicants from CSV/Excel file
    
    Required columns:
    - first_name, last_name, date_of_birth, education_code
    - phone_number, lead_source, prid
    - application_date
    - applicant_status (pending, processing, approved, etc.)
    
    Optional columns:
    - cbsa_code, middle_name, address, asvab_score
    - meps_scheduled_date
    - recruiter_assigned
    - mos_preference
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid', 'application_date', 'applicant_status']
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
                applicant_id = f"APP-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                dob = pd.to_datetime(row['date_of_birth'])
                age = (datetime.now() - dob).days // 365
                
                cursor.execute("""
                    INSERT INTO applicants (
                        applicant_id, first_name, last_name, middle_name, date_of_birth,
                        age, education_code, phone_number, address, cbsa_code,
                        lead_source, prid, asvab_score, application_date, applicant_status,
                        meps_scheduled_date, recruiter_assigned, mos_preference, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    applicant_id,
                    row['first_name'],
                    row['last_name'],
                    row.get('middle_name', ''),
                    row['date_of_birth'],
                    age,
                    row['education_code'],
                    row['phone_number'],
                    row.get('address', ''),
                    row.get('cbsa_code', ''),
                    row['lead_source'],
                    row['prid'],
                    row.get('asvab_score', None),
                    row['application_date'],
                    row['applicant_status'],
                    row.get('meps_scheduled_date', None),
                    row.get('recruiter_assigned', ''),
                    row.get('mos_preference', ''),
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
            "message": f"Successfully imported {imported_count} of {len(df)} applicants"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/upload/future_soldiers")
async def upload_future_soldiers(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import future soldiers from CSV/Excel file
    
    Required columns:
    - first_name, last_name, date_of_birth, education_code
    - phone_number, lead_source, prid
    - contract_date
    - ship_date
    - mos_assigned
    - future_soldier_status
    
    Optional columns:
    - cbsa_code, middle_name, address, asvab_score
    - recruiter_assigned
    - unit_assignment
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['first_name', 'last_name', 'date_of_birth', 'education_code', 'phone_number', 'lead_source', 'prid', 'contract_date', 'ship_date', 'mos_assigned', 'future_soldier_status']
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
                fs_id = f"FS-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                dob = pd.to_datetime(row['date_of_birth'])
                age = (datetime.now() - dob).days // 365
                
                cursor.execute("""
                    INSERT INTO future_soldiers (
                        fs_id, first_name, last_name, middle_name, date_of_birth,
                        age, education_code, phone_number, address, cbsa_code,
                        lead_source, prid, asvab_score, contract_date, ship_date,
                        mos_assigned, future_soldier_status, recruiter_assigned,
                        unit_assignment, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fs_id,
                    row['first_name'],
                    row['last_name'],
                    row.get('middle_name', ''),
                    row['date_of_birth'],
                    age,
                    row['education_code'],
                    row['phone_number'],
                    row.get('address', ''),
                    row.get('cbsa_code', ''),
                    row['lead_source'],
                    row['prid'],
                    row.get('asvab_score', None),
                    row['contract_date'],
                    row['ship_date'],
                    row['mos_assigned'],
                    row['future_soldier_status'],
                    row.get('recruiter_assigned', ''),
                    row.get('unit_assignment', ''),
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
            "message": f"Successfully imported {imported_count} of {len(df)} future soldiers"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/upload/events")
async def upload_events(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import events from CSV/Excel file
    
    Required columns:
    - name, location, start_date, end_date
    
    Optional columns:
    - type, budget, team_size, targeting_principles, status
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['name', 'location', 'start_date', 'end_date']
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


@router.post("/upload/projects")
async def upload_projects(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import projects from CSV/Excel file
    
    Required columns:
    - name, owner_id, start_date, target_date, objectives
    
    Optional columns:
    - event_id, funding_amount, status
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


@router.post("/upload/marketing_activities")
async def upload_marketing_activities(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import marketing activities from CSV/Excel file
    
    Required columns:
    - activity_name, campaign_type, start_date, end_date, budget_allocated
    
    Optional columns:
    - target_audience, channels, leads_generated, cost_per_lead, status
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['activity_name', 'campaign_type', 'start_date', 'end_date', 'budget_allocated']
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
                activity_id = f"MKT-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                cursor.execute("""
                    INSERT INTO marketing_activities (
                        activity_id, activity_name, campaign_type, start_date, end_date,
                        budget_allocated, target_audience, channels, leads_generated,
                        cost_per_lead, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_id,
                    row['activity_name'],
                    row['campaign_type'],
                    row['start_date'],
                    row['end_date'],
                    row['budget_allocated'],
                    row.get('target_audience', ''),
                    row.get('channels', ''),
                    row.get('leads_generated', 0),
                    row.get('cost_per_lead', 0),
                    row.get('status', 'active'),
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
            "message": f"Successfully imported {imported_count} of {len(df)} marketing activities"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/upload/budgets")
async def upload_budgets(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import budget records from CSV/Excel file
    
    Required columns:
    - campaign_name, allocated_amount, start_date, end_date
    
    Optional columns:
    - event_id, spent_amount, remaining_amount, fiscal_year
    """
    try:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        required_cols = ['campaign_name', 'allocated_amount', 'start_date', 'end_date']
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
                budget_id = f"BDG-{int(datetime.now().timestamp() * 1000)}-{index}"
                
                cursor.execute("""
                    INSERT INTO budgets (
                        budget_id, event_id, campaign_name, allocated_amount,
                        spent_amount, remaining_amount, start_date, end_date,
                        fiscal_year, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    budget_id,
                    row.get('event_id', ''),
                    row['campaign_name'],
                    row['allocated_amount'],
                    row.get('spent_amount', 0),
                    row.get('remaining_amount', row['allocated_amount']),
                    row['start_date'],
                    row['end_date'],
                    row.get('fiscal_year', '2025'),
                    datetime.now().isoformat(),
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
            "message": f"Successfully imported {imported_count} of {len(df)} budget records"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/upload/templates")
async def get_upload_templates() -> Dict[str, Any]:
    """Get template information for all upload types"""
    return {
        "leads": {
            "required": ["first_name", "last_name", "date_of_birth", "education_code", "phone_number", "lead_source", "prid"],
            "optional": ["cbsa_code", "middle_name", "address", "asvab_score"],
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "middle_name": "A",
                "date_of_birth": "2003-05-15",
                "education_code": "HS",
                "phone_number": "555-1234",
                "address": "123 Main St, City, ST 12345",
                "cbsa_code": "41700",
                "lead_source": "social_media",
                "prid": "PR123456",
                "asvab_score": "75"
            }
        },
        "prospects": {
            "required": ["first_name", "last_name", "date_of_birth", "education_code", "phone_number", "lead_source", "prid", "prospect_status"],
            "optional": ["cbsa_code", "middle_name", "address", "asvab_score", "last_contact_date", "recruiter_assigned", "notes"],
            "example": {
                "first_name": "Jane",
                "last_name": "Doe",
                "date_of_birth": "2002-08-20",
                "education_code": "SC",
                "phone_number": "555-5678",
                "lead_source": "referral",
                "prid": "PR789012",
                "prospect_status": "qualified",
                "last_contact_date": "2025-11-15",
                "recruiter_assigned": "SSG Smith",
                "cbsa_code": "41700"
            }
        },
        "applicants": {
            "required": ["first_name", "last_name", "date_of_birth", "education_code", "phone_number", "lead_source", "prid", "application_date", "applicant_status"],
            "optional": ["cbsa_code", "middle_name", "address", "asvab_score", "meps_scheduled_date", "recruiter_assigned", "mos_preference"],
            "example": {
                "first_name": "Mike",
                "last_name": "Johnson",
                "date_of_birth": "2001-12-10",
                "education_code": "HS",
                "phone_number": "555-9012",
                "lead_source": "walk_in",
                "prid": "PR345678",
                "application_date": "2025-10-01",
                "applicant_status": "processing",
                "meps_scheduled_date": "2025-11-25",
                "mos_preference": "11B",
                "asvab_score": "82"
            }
        },
        "future_soldiers": {
            "required": ["first_name", "last_name", "date_of_birth", "education_code", "phone_number", "lead_source", "prid", "contract_date", "ship_date", "mos_assigned", "future_soldier_status"],
            "optional": ["cbsa_code", "middle_name", "address", "asvab_score", "recruiter_assigned", "unit_assignment"],
            "example": {
                "first_name": "Sarah",
                "last_name": "Williams",
                "date_of_birth": "2003-03-22",
                "education_code": "HS",
                "phone_number": "555-3456",
                "lead_source": "event",
                "prid": "PR901234",
                "contract_date": "2025-09-15",
                "ship_date": "2026-01-10",
                "mos_assigned": "68W",
                "future_soldier_status": "active",
                "unit_assignment": "A Co, 1-50 IN",
                "asvab_score": "88"
            }
        },
        "events": {
            "required": ["name", "location", "start_date", "end_date"],
            "optional": ["type", "budget", "team_size", "targeting_principles", "status"],
            "example": {
                "name": "Career Fair - Tech High",
                "type": "school_visit",
                "location": "Austin, TX",
                "start_date": "2025-12-01",
                "end_date": "2025-12-01",
                "budget": "500",
                "team_size": "3",
                "targeting_principles": "D3AE",
                "status": "planned"
            }
        },
        "projects": {
            "required": ["name", "owner_id", "start_date", "target_date", "objectives"],
            "optional": ["event_id", "funding_amount", "status"],
            "example": {
                "name": "Q1 Digital Campaign",
                "owner_id": "SSG Smith",
                "start_date": "2026-01-01",
                "target_date": "2026-03-31",
                "objectives": "Increase social media leads by 25%",
                "funding_amount": "15000",
                "status": "planning"
            }
        },
        "marketing_activities": {
            "required": ["activity_name", "campaign_type", "start_date", "end_date", "budget_allocated"],
            "optional": ["target_audience", "channels", "leads_generated", "cost_per_lead", "status"],
            "example": {
                "activity_name": "Instagram Ad Campaign",
                "campaign_type": "social_media",
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
                "budget_allocated": "5000",
                "target_audience": "18-24, college students",
                "channels": "Instagram, Facebook",
                "leads_generated": "150",
                "cost_per_lead": "33.33",
                "status": "active"
            }
        },
        "budgets": {
            "required": ["campaign_name", "allocated_amount", "start_date", "end_date"],
            "optional": ["event_id", "spent_amount", "remaining_amount", "fiscal_year"],
            "example": {
                "campaign_name": "FY25 Q2 Recruiting",
                "allocated_amount": "25000",
                "spent_amount": "12500",
                "remaining_amount": "12500",
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "fiscal_year": "2025",
                "event_id": "EVT-12345"
            }
        }
    }


# Data retrieval endpoints for dynamic dashboard
@router.get("/data/leads")
async def get_leads_data() -> Dict[str, Any]:
    """Get all leads data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")


@router.get("/data/prospects")
async def get_prospects_data() -> Dict[str, Any]:
    """Get all prospects data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prospects")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prospects: {str(e)}")


@router.get("/data/applicants")
async def get_applicants_data() -> Dict[str, Any]:
    """Get all applicants data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applicants")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch applicants: {str(e)}")


@router.get("/data/future_soldiers")
async def get_future_soldiers_data() -> Dict[str, Any]:
    """Get all future soldiers data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM future_soldiers")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch future soldiers: {str(e)}")


@router.get("/data/events")
async def get_events_data() -> Dict[str, Any]:
    """Get all events data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.get("/data/projects")
async def get_projects_data() -> Dict[str, Any]:
    """Get all projects data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.get("/data/marketing_activities")
async def get_marketing_data() -> Dict[str, Any]:
    """Get all marketing activities data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM marketing_activities")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch marketing activities: {str(e)}")


@router.get("/data/budgets")
async def get_budgets_data() -> Dict[str, Any]:
    """Get all budgets data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch budgets: {str(e)}")
