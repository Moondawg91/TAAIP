from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import io
import csv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import logging
import random
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any


# --- Configuration & Initialization ---
app = FastAPI(
    title="TAAIP Targeting & AI Service",
    description="Provides real-time lead scoring and targeting recommendations.",
    version="1.0.0",
)
logging.basicConfig(level=logging.INFO)

# Allow CORS for local development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data file locations
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")
PILOT_FILE = os.path.join(DATA_DIR, "pilot_state.json")
DB_FILE = os.path.join(DATA_DIR, "taaip.sqlite3")


# --- SQLite helpers ---
def get_db_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def model_to_dict(m):
    """Compatibility helper for Pydantic v1/v2: prefer model_dump(), fall back to dict()."""
    if hasattr(m, "model_dump"):
        return m.model_dump()
    if hasattr(m, "dict"):
        return m.dict()
    try:
        return dict(m)
    except Exception:
        return {}


def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    
    # --- Original tables ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT,
            age INTEGER,
            education_level TEXT,
            cbsa_code TEXT,
            campaign_source TEXT,
            received_at TEXT,
            predicted_probability REAL,
            score INTEGER,
            recommendation TEXT,
            converted INTEGER DEFAULT 0,
            raw_json TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pilot_state (
            id INTEGER PRIMARY KEY,
            started_at TEXT,
            config TEXT,
            status TEXT
        )
        """
    )
    
    # --- Extended: Events & ROI Tracking ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            start_date TEXT,
            end_date TEXT,
            budget REAL,
            team_size INTEGER,
            targeting_principles TEXT,
            status TEXT DEFAULT 'planned',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS event_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            date TEXT,
            leads_generated INTEGER DEFAULT 0,
            leads_qualified INTEGER DEFAULT 0,
            conversion_count INTEGER DEFAULT 0,
            cost_per_lead REAL,
            roi REAL,
            engagement_rate REAL,
            created_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS capture_survey (
            survey_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            lead_id TEXT,
            timestamp TEXT,
            technician_id TEXT,
            effectiveness_rating INTEGER,
            feedback TEXT,
            data_quality_flag INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )
    
    # --- Extended: Recruiting Funnel ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS funnel_stages (
            stage_id TEXT PRIMARY KEY,
            stage_name TEXT NOT NULL,
            sequence_order INTEGER,
            description TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS funnel_transitions (
            transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT NOT NULL,
            from_stage TEXT,
            to_stage TEXT,
            transition_date TEXT,
            transition_reason TEXT,
            technician_id TEXT,
            created_at TEXT,
            FOREIGN KEY(to_stage) REFERENCES funnel_stages(stage_id)
        )
        """
    )
    
    # --- Extended: Project Management ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            event_id TEXT,
            start_date TEXT,
            target_date TEXT,
            owner_id TEXT,
            status TEXT DEFAULT 'planning',
            objectives TEXT,
            success_criteria TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            assigned_to TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT,
            completion_date TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(project_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS milestones (
            milestone_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            target_date TEXT,
            actual_date TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(project_id)
        )
        """
    )
    
    # --- Extended: M-IPOE ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mipoe (
            mipoe_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            phase TEXT NOT NULL,
            content TEXT,
            owner_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )
    
    # --- Extended: Targeting Profiles (D3AE/F3A) ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS targeting_profiles (
            profile_id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            target_age_min INTEGER,
            target_age_max INTEGER,
            target_education_level TEXT,
            target_locations TEXT,
            message_themes TEXT,
            contact_frequency INTEGER,
            conversion_target REAL,
            cost_per_lead_target REAL,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )
    
    # --- Extended: Forecasting ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS forecasts (
            forecast_id TEXT PRIMARY KEY,
            quarter INTEGER,
            year INTEGER,
            projected_leads INTEGER,
            projected_conversions INTEGER,
            projected_roi REAL,
            confidence_level REAL,
            methodology TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            quarter INTEGER,
            year INTEGER,
            total_events INTEGER,
            total_leads INTEGER,
            conversion_rate REAL,
            avg_cost_per_lead REAL,
            total_roi REAL,
            by_event TEXT,
            created_at TEXT
        )
        """
    )
    
    # NEW: Marketing Activity Tracking (USAREC-specific)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS marketing_activities (
            activity_id TEXT PRIMARY KEY,
            event_id TEXT,
            activity_type TEXT,
            campaign_name TEXT,
            channel TEXT,
            data_source TEXT,
            impressions INTEGER DEFAULT 0,
            engagement_count INTEGER DEFAULT 0,
            awareness_metric REAL DEFAULT 0.0,
            activation_conversions INTEGER DEFAULT 0,
            reporting_date TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )
    # Ensure cost column exists for activity-level costing (backwards-safe)
    try:
        cur.execute("ALTER TABLE marketing_activities ADD COLUMN cost REAL DEFAULT 0.0")
    except Exception:
        # Column probably already exists or SQLite cannot alter; ignore
        pass
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data_source_mappings (
            mapping_id TEXT PRIMARY KEY,
            source_system TEXT,
            source_name TEXT,
            description TEXT,
            api_endpoint TEXT,
            last_sync TEXT,
            sync_status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    # Budgets and cost allocations
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            budget_id TEXT PRIMARY KEY,
            event_id TEXT,
            campaign_name TEXT,
            allocated_amount REAL DEFAULT 0.0,
            currency TEXT DEFAULT 'USD',
            start_date TEXT,
            end_date TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
        """
    )

    # --- Segmentation: Profiles and History ---
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS segment_profiles (
            profile_id TEXT PRIMARY KEY,
            lead_id TEXT,
            segments TEXT,
            attributes TEXT,
            last_updated TEXT,
            created_at TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(lead_id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS segment_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT,
            lead_id TEXT,
            segments TEXT,
            attributes TEXT,
            changed_at TEXT,
            source TEXT,
            notes TEXT,
            FOREIGN KEY(profile_id) REFERENCES segment_profiles(profile_id)
        )
        """
    )
    # Initialize USAREC data source mappings (one-time)
    try:
        cur.execute("SELECT COUNT(*) FROM data_source_mappings")
        if cur.fetchone()[0] == 0:
            data_sources = [
                ("emm", "EMM", "Enterprise Marketing Manager - USAREC lead management"),
                ("ikrome", "iKrome", "Advanced analytics and attribution platform"),
                ("vantage", "Vantage", "Marketing performance and channel analysis"),
                ("g2_report_zone", "G2 Report Zone", "Competitive intelligence and market analysis"),
                ("aiem", "AIEM", "Army Integrated Enlisted Marketing system"),
                ("usarec_systems", "USAREC Systems", "Army Recruiting Command databases"),
            ]
            for idx, (sys, name, desc) in enumerate(data_sources, 1):
                cur.execute(
                    "INSERT INTO data_source_mappings (mapping_id, source_system, source_name, description, last_sync, sync_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (f"map_{idx}", sys, name, desc, None, "pending", datetime.now().isoformat()),
                )
    except Exception as e:
        logging.warning(f"Data source mappings already initialized: {e}")
    
    # Initialize USAREC recruiting funnel stages (one-time)
    try:
        cur.execute("SELECT COUNT(*) FROM funnel_stages")
        if cur.fetchone()[0] == 0:
            stages = [
                ("lead", "Lead", 1, "Raw prospect, initial capture from marketing channels"),
                ("prospect", "Prospect", 2, "Qualified demographic match, engaged with content"),
                ("appointment_made", "Appointment Made", 3, "Scheduled appointment with recruiter"),
                ("appointment_conducted", "Appointment Conducted", 4, "Met with recruiter, initial discussion completed"),
                ("test", "Test", 5, "ASVAB or qualification test administered"),
                ("test_pass", "Test Pass", 6, "Passed ASVAB with qualifying score"),
                ("physical", "Physical", 7, "Medical examination and physical qualification completed"),
                ("enlist", "Enlist", 8, "Contract signed, enlisted into service"),
            ]
            for stage_id, name, order, desc in stages:
                cur.execute(
                    "INSERT INTO funnel_stages (stage_id, stage_name, sequence_order, description) VALUES (?, ?, ?, ?)",
                    (stage_id, name, order, desc),
                )
    except Exception as e:
        logging.warning(f"USAREC funnel stages already initialized: {e}")
    
    conn.commit()
    conn.close()


def migrate_json_to_db():
    # Migrate leads
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
        except Exception:
            leads = []
        if leads:
            conn = get_db_conn()
            cur = conn.cursor()
            for l in leads:
                cur.execute(
                    "SELECT COUNT(1) as c FROM leads WHERE lead_id = ? AND received_at = ?",
                    (l.get("lead_id"), l.get("received_at")),
                )
                if cur.fetchone()[0] > 0:
                    continue
                cur.execute(
                    """
                    INSERT INTO leads (lead_id, age, education_level, cbsa_code, campaign_source, received_at, predicted_probability, score, recommendation, converted, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        l.get("lead_id"),
                        l.get("age"),
                        l.get("education_level"),
                        l.get("cbsa_code"),
                        l.get("campaign_source"),
                        l.get("received_at"),
                        l.get("predicted_probability"),
                        l.get("score"),
                        l.get("recommendation"),
                        1 if l.get("converted") else 0,
                        json.dumps(l),
                    ),
                )
            conn.commit()
            conn.close()
    # Migrate pilot state
    if os.path.exists(PILOT_FILE):
        try:
            with open(PILOT_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = None
        if state:
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute(
                "REPLACE INTO pilot_state (id, started_at, config, status) VALUES (1, ?, ?, ?)",
                (state.get("started_at"), json.dumps(state.get("config")), state.get("status")),
            )
            conn.commit()
            conn.close()


# Ensure DB exists and migrate any JSON demo data
init_db()
migrate_json_to_db()


# --- ML Model Loader & Scoring ---
def load_ml_model():
    logging.info("Loading Lead Scoring Model from storage...")
    model_path = os.path.join(DATA_DIR, "model.joblib")
    if os.path.exists(model_path):
        try:
            from joblib import load

            mdl = load(model_path)
            logging.info(f"Loaded model from {model_path}")
            return {"status": "ready", "model": mdl, "model_version": getattr(mdl, 'version', 'unknown')}
        except Exception as e:
            logging.warning(f"Failed to load model.joblib: {e}; falling back to simulated model")
    return {"status": "simulated", "model": None, "model_version": "simulated-v1"}


ML_MODEL = load_ml_model()
logging.info(f"ML Model initialized. Status: {ML_MODEL['status']}")


# --- Simple token auth (optional) ---
API_TOKEN = os.environ.get("TAAIP_API_TOKEN")
if API_TOKEN:
    logging.info("API token auth enabled for /api/v1 endpoints")


@app.middleware("http")
def auth_middleware(request: Request, call_next):
    # If an API token is configured, require Bearer token for internal API paths
    if API_TOKEN and request.url.path.startswith("/api/v1"):
        auth = request.headers.get("authorization")
        if not auth or auth != f"Bearer {API_TOKEN}":
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return call_next(request)


def compute_score_from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Use real model if available, otherwise fall back to the simple simulator."""
    if ML_MODEL.get("model") is not None:
        try:
            model = ML_MODEL["model"]
            features = [
                float(d.get("age", 30)),
                1.0 if d.get("education_level") in ("Bachelors", "Masters") else 0.0,
                1.0 if d.get("campaign_source") == "High-Impact-Targeting-Campaign" else 0.0,
            ]
            prob = float(model.predict_proba([features])[0][1])
            score_int = int(min(100, max(1, round(prob * 100))))
            rec = "High Priority: Immediate Recruiter Engagement Required" if score_int >= 85 else (
                "Medium Priority: Add to Nurture Campaign Queue" if score_int >= 60 else "Low Priority: Monitor and Re-evaluate"
            )
            return {"lead_id": d.get("lead_id"), "predicted_probability": round(prob, 4), "score": score_int, "recommendation": rec}
        except Exception as e:
            logging.warning(f"Model scoring failed, falling back to simulated logic: {e}")

    base_score = random.randint(30, 85)
    education = d.get("education_level", "")
    campaign = d.get("campaign_source", "")
    if education in ["Bachelors", "Masters"]:
        base_score += 5
    if campaign == "High-Impact-Targeting-Campaign":
        base_score += 10
    final_score = min(100, base_score)
    probability = final_score / 100.0
    if final_score >= 85:
        recommendation = "High Priority: Immediate Recruiter Engagement Required"
    elif final_score >= 60:
        recommendation = "Medium Priority: Add to Nurture Campaign Queue"
    else:
        recommendation = "Low Priority: Monitor and Re-evaluate"
    return {
        "lead_id": d.get("lead_id"),
        "predicted_probability": round(probability, 4),
        "score": final_score,
        "recommendation": recommendation,
    }


class LeadData(BaseModel):
    """Schema for the input data required for lead scoring."""
    lead_id: str = Field(..., description="Unique identifier for the recruitment lead.")
    age: int = Field(..., ge=18, description="Age of the prospective recruit.")
    education_level: str = Field(..., description="Highest level of education completed (e.g., 'High School', 'Some College', 'Bachelors').")
    cbsa_code: str = Field(..., description="Core Based Statistical Area (CBSA) code for geographic targeting.")
    campaign_source: str = Field(..., description="Marketing channel/campaign that generated the lead.")


class ScoringResult(BaseModel):
    """Schema for the output data returned by the scoring engine."""
    lead_id: str
    predicted_probability: float = Field(..., ge=0.0, le=1.0, description="The probability (0.0 to 1.0) the lead will convert.")
    score: int = Field(..., ge=1, le=100, description="Lead score scaled from 1 to 100.")
    recommendation: str = Field(..., description="Actionable recommendation for the recruiter (e.g., High Priority Engagement).")


def get_metrics() -> Dict[str, Any]:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) as total, AVG(score) as avg_score, SUM(converted) as converted_sum FROM leads")
    row = cur.fetchone()
    total = row[0] or 0
    avg_score = float(row[1]) if row[1] is not None else 0.0
    converted = row[2] or 0
    conversion_rate = (converted / total) if total > 0 else 0.0

    by_cbsa = {}
    cur.execute("SELECT cbsa_code, COUNT(1) as cnt, AVG(score) as avg_score FROM leads GROUP BY cbsa_code")
    for r in cur.fetchall():
        cbsa = r[0] or "unknown"
        by_cbsa[cbsa] = {"count": r[1], "average_score": float(r[2]) if r[2] is not None else 0.0}

    conn.close()
    return {"total_leads": total, "average_score": round(avg_score, 2), "conversion_rate": round(conversion_rate, 4), "by_cbsa": by_cbsa}


@app.post("/api/v1/scoreLead", response_model=ScoringResult)
def score_lead(data: LeadData):
    try:
        logging.info(f"Scoring lead {data.lead_id} from CBSA {data.cbsa_code}...")
        result = compute_score_from_dict(model_to_dict(data))
        logging.info(f"Lead {data.lead_id} scored {result['score']}/100.")
        return ScoringResult(**result)
    except Exception as e:
        logging.error(f"Error during lead scoring for {data.lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error in ML service.")


@app.post("/api/v1/ingestLead")
def ingest_lead(data: LeadData):
    """Score the lead and persist it to the SQLite store."""
    result = compute_score_from_dict(model_to_dict(data))
    received_at = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO leads (lead_id, age, education_level, cbsa_code, campaign_source, received_at, predicted_probability, score, recommendation, converted, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.lead_id,
            data.age,
            data.education_level,
            data.cbsa_code,
            data.campaign_source,
            received_at,
            result["predicted_probability"],
            result["score"],
            result["recommendation"],
            0,
            json.dumps(model_to_dict(data)),
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "lead": {**result, "received_at": received_at}}


@app.get("/api/v1/metrics")
def metrics_endpoint():
    return get_metrics()


@app.post("/api/v1/startPilot")
def start_pilot(payload: Optional[Dict[str, Any]] = None):
    payload = payload or {}
    started_at = datetime.utcnow().isoformat()
    config = payload.get("config", {})
    status = payload.get("status", "running")
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO pilot_state (id, started_at, config, status) VALUES (1, ?, ?, ?)",
        (started_at, json.dumps(config), status),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "started_at": started_at, "config": config, "pilot_status": status}


@app.get("/api/v1/pilotStatus")
def pilot_status():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT started_at, config, status FROM pilot_state WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"status": "not_started"}
    return {"started_at": row[0], "config": json.loads(row[1]) if row[1] else {}, "status": row[2]}


@app.get("/health")
def health_check():
    """Returns the status of the service and the loaded ML model."""
    return {"status": "ok", "service": "TAAIP Targeting & AI Service", "model_status": ML_MODEL.get("status", "unknown")}


# ========== EXTENDED API (v2): ROI, Funnel, Project Management, M-IPOE, Targeting, Forecasting ==========

# --- Pydantic Models ---

class EventCreate(BaseModel):
    name: str
    type: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    team_size: Optional[int] = None
    targeting_principles: Optional[str] = None


class EventMetricsCreate(BaseModel):
    event_id: str
    date: str
    leads_generated: int = 0
    leads_qualified: int = 0
    conversion_count: int = 0
    cost_per_lead: Optional[float] = None
    roi: Optional[float] = None
    engagement_rate: Optional[float] = None


class CaptureSurveyCreate(BaseModel):
    event_id: str
    lead_id: Optional[str] = None
    technician_id: str
    effectiveness_rating: int
    feedback: str


class FunnelTransitionCreate(BaseModel):
    lead_id: str
    from_stage: Optional[str] = None
    to_stage: str
    transition_reason: Optional[str] = None
    technician_id: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    event_id: Optional[str] = None
    start_date: str
    target_date: str
    owner_id: str
    objectives: Optional[str] = None
    success_criteria: Optional[str] = None


class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: str
    priority: Optional[str] = None


class MIPOECreate(BaseModel):
    event_id: str
    phase: str  # intent, plan, order, execute, evaluate
    content: Dict[str, Any]
    owner_id: Optional[str] = None


class TargetingProfileCreate(BaseModel):
    event_id: str
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None
    target_education_level: Optional[str] = None
    target_locations: Optional[str] = None  # comma-separated CBSA codes
    message_themes: Optional[str] = None  # comma-separated themes
    contact_frequency: Optional[int] = None
    conversion_target: Optional[float] = None
    cost_per_lead_target: Optional[float] = None


# NEW: Marketing Activity Models (USAREC-specific)
class MarketingActivityCreate(BaseModel):
    event_id: Optional[str] = None
    activity_type: str  # 'social_media', 'email', 'display_ad', 'event', 'referral', 'organic'
    campaign_name: str
    channel: str  # 'Facebook', 'Instagram', 'Email', 'Google Ads', 'TikTok', 'In-Person', 'YouTube'
    data_source: str  # 'emm', 'ikrome', 'vantage', 'g2_report_zone', 'aiem', 'usarec_systems'
    impressions: int = 0
    engagement_count: int = 0
    awareness_metric: float = 0.0  # 0.0-1.0 scale
    activation_conversions: int = 0
    reporting_date: str
    metadata: Optional[str] = None


class DataSourceSync(BaseModel):
    source_system: str  # 'emm', 'ikrome', 'vantage', 'g2_report_zone', 'aiem', 'usarec_systems'
    sync_data: Dict[str, Any]  # Flexible JSON for source-specific data


# --- Segmentation & Ingest Models ---
class SegmentProfileCreate(BaseModel):
    lead_id: str
    segments: Optional[Dict[str, Any]] = None  # e.g., {"age_group":"18-24","interests":[...]}
    attributes: Optional[Dict[str, Any]] = None  # free-form attributes


class SurveyIngest(BaseModel):
    lead_id: Optional[str] = None
    survey_id: str
    responses: Dict[str, Any]
    source: Optional[str] = "survey"
    received_at: Optional[str] = None


class CensusIngest(BaseModel):
    geography_code: str
    attributes: Dict[str, Any]
    source: Optional[str] = "census"
    received_at: Optional[str] = None


class SocialSignalIngest(BaseModel):
    external_id: str
    handle: Optional[str] = None
    signals: Dict[str, Any]
    source: Optional[str] = "social"
    received_at: Optional[str] = None


class EngagementIngest(BaseModel):
    event_id: Optional[str] = None
    activity_id: Optional[str] = None
    impressions: Optional[int] = 0
    engagement_count: Optional[int] = 0
    data_source: Optional[str] = None
    reporting_date: Optional[str] = None


# --- Events & ROI Tracking Endpoints ---

@app.post("/api/v2/events")
def create_event(event: EventCreate):
    """Create a new recruiting event."""
    import uuid
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (event_id, name, type, location, start_date, end_date, budget, team_size, targeting_principles, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)
        """,
        (event_id, event.name, event.type, event.location, event.start_date, event.end_date, event.budget, event.team_size, event.targeting_principles, now, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "event_id": event_id}


@app.get("/api/v2/events/{event_id}/metrics")
def get_event_metrics(event_id: str):
    """Get real-time ROI metrics for an event."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT date, leads_generated, leads_qualified, conversion_count, cost_per_lead, roi, engagement_rate FROM event_metrics WHERE event_id = ? ORDER BY date DESC LIMIT 100", (event_id,))
    metrics = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"event_id": event_id, "metrics": metrics}



def _now_iso():
    return datetime.utcnow().isoformat()


def update_segment_profile(lead_id: Optional[str], segments: Optional[Dict[str, Any]], attributes: Optional[Dict[str, Any]], source: str = "ingest", notes: Optional[str] = None):
    """Merge incoming segment/attribute data into segment_profiles and record history."""
    conn = get_db_conn()
    cur = conn.cursor()
    now = _now_iso()

    profile_id = None
    if lead_id:
        profile_id = f"profile_{lead_id}"
    else:
        import uuid
        profile_id = f"profile_{uuid.uuid4().hex[:12]}"

    # Fetch existing
    cur.execute("SELECT segments, attributes FROM segment_profiles WHERE profile_id = ?", (profile_id,))
    row = cur.fetchone()
    existing_segments = {}
    existing_attrs = {}
    if row:
        try:
            existing_segments = json.loads(row[0]) if row[0] else {}
        except Exception:
            existing_segments = {}
        try:
            existing_attrs = json.loads(row[1]) if row[1] else {}
        except Exception:
            existing_attrs = {}

    # Merge (simple overwrite semantics for keys)
    merged_segments = existing_segments.copy()
    if segments:
        for k, v in segments.items():
            merged_segments[k] = v

    merged_attrs = existing_attrs.copy()
    if attributes:
        for k, v in attributes.items():
            merged_attrs[k] = v

    # Upsert profile
    cur.execute(
        "REPLACE INTO segment_profiles (profile_id, lead_id, segments, attributes, last_updated, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (profile_id, lead_id, json.dumps(merged_segments), json.dumps(merged_attrs), now, now),
    )

    # Insert history
    cur.execute(
        "INSERT INTO segment_history (profile_id, lead_id, segments, attributes, changed_at, source, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (profile_id, lead_id, json.dumps(merged_segments), json.dumps(merged_attrs), now, source, notes),
    )
    conn.commit()
    conn.close()
    return {"profile_id": profile_id, "segments": merged_segments, "attributes": merged_attrs}


@app.post("/api/v2/ingest/survey")
def ingest_survey(payload: SurveyIngest):
    """Ingest survey responses and update segmentation for the lead (if provided)."""
    received_at = payload.received_at or _now_iso()
    # Basic rule: convert some survey answers into segments
    segments = {}
    attributes = {"survey_id": payload.survey_id, "responses": payload.responses}
    # Example mapping: if age question present
    if payload.responses.get("age"):
        age = payload.responses.get("age")
        try:
            age = int(age)
            if age < 25:
                segments["age_group"] = "18-24"
            elif age < 35:
                segments["age_group"] = "25-34"
            else:
                segments["age_group"] = "35_plus"
        except Exception:
            pass

    result = update_segment_profile(payload.lead_id, segments, attributes, source=payload.source, notes=f"survey:{payload.survey_id}")
    return {"status": "ok", "result": result}


@app.post("/api/v2/ingest/census")
def ingest_census(payload: CensusIngest):
    """Ingest census attributes for a geography and update segment profiles of matching leads (basic behavior: store as attributes keyed by geography)."""
    received_at = payload.received_at or _now_iso()
    # For this prototype, we will store the census attributes as a standalone segment profile under geography code
    profile_id = f"census_{payload.geography_code}"
    conn = get_db_conn()
    cur = conn.cursor()
    now = _now_iso()
    cur.execute(
        "REPLACE INTO segment_profiles (profile_id, lead_id, segments, attributes, last_updated, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (profile_id, None, json.dumps({}), json.dumps(payload.attributes), now, now),
    )
    cur.execute(
        "INSERT INTO segment_history (profile_id, lead_id, segments, attributes, changed_at, source, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (profile_id, None, json.dumps({}), json.dumps(payload.attributes), now, payload.source, "census_import"),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "profile_id": profile_id}


@app.post("/api/v2/ingest/social")
def ingest_social(payload: SocialSignalIngest):
    """Ingest social signals and create/update segment profile mapped to external handle."""
    received_at = payload.received_at or _now_iso()
    # Map external_id/handle to a profile
    profile_id = f"social_{payload.external_id}"
    conn = get_db_conn()
    cur = conn.cursor()
    now = _now_iso()
    cur.execute(
        "REPLACE INTO segment_profiles (profile_id, lead_id, segments, attributes, last_updated, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (profile_id, None, json.dumps({}), json.dumps(payload.signals), now, now),
    )
    cur.execute(
        "INSERT INTO segment_history (profile_id, lead_id, segments, attributes, changed_at, source, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (profile_id, None, json.dumps({}), json.dumps(payload.signals), now, payload.source, "social_import"),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "profile_id": profile_id}


@app.post("/api/v2/ingest/engagements")
def ingest_engagements(payload: EngagementIngest):
    """Ingest bulk engagement/impression updates and optionally create marketing activity entries or update existing ones."""
    conn = get_db_conn()
    cur = conn.cursor()
    created = 0
    now = _now_iso()
    # If activity_id provided, update that activity
    if payload.activity_id:
        cur.execute("SELECT activity_id FROM marketing_activities WHERE activity_id = ?", (payload.activity_id,))
        if cur.fetchone():
            cur.execute(
                "UPDATE marketing_activities SET impressions = impressions + ?, engagement_count = engagement_count + ?, updated_at = ? WHERE activity_id = ?",
                (payload.impressions or 0, payload.engagement_count or 0, now, payload.activity_id),
            )
            conn.commit()
            conn.close()
            return {"status": "ok", "updated": payload.activity_id}

    # Otherwise, create a lightweight activity record
    import uuid
    activity_id = f"mkt_{uuid.uuid4().hex[:12]}"
    cur.execute(
        "INSERT INTO marketing_activities (activity_id, event_id, activity_type, campaign_name, channel, data_source, impressions, engagement_count, awareness_metric, activation_conversions, reporting_date, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (activity_id, payload.event_id, 'engagement_batch', None, None, payload.data_source, payload.impressions or 0, payload.engagement_count or 0, 0.0, 0, payload.reporting_date or now, None, now, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "activity_id": activity_id}


@app.get("/api/v2/segments/{lead_id}")
def get_segment_profile(lead_id: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT profile_id, segments, attributes, last_updated FROM segment_profiles WHERE lead_id = ?", (lead_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"status": "not_found"}
    try:
        segments = json.loads(row[1]) if row[1] else {}
    except Exception:
        segments = {}
    try:
        attrs = json.loads(row[2]) if row[2] else {}
    except Exception:
        attrs = {}
    return {"status": "ok", "profile_id": row[0], "segments": segments, "attributes": attrs, "last_updated": row[3]}


@app.post("/api/v2/events/{event_id}/metrics")
def add_event_metrics(event_id: str, metrics: EventMetricsCreate):
    """Record event metrics (live update from TA technician)."""
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO event_metrics (event_id, date, leads_generated, leads_qualified, conversion_count, cost_per_lead, roi, engagement_rate, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, metrics.date, metrics.leads_generated, metrics.leads_qualified, metrics.conversion_count, metrics.cost_per_lead, metrics.roi, metrics.engagement_rate, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Metrics recorded"}


@app.post("/api/v2/events/{event_id}/survey")
def capture_survey(event_id: str, survey: CaptureSurveyCreate):
    """Capture real-time survey feedback from TA technician."""
    import uuid
    survey_id = f"sur_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO capture_survey (survey_id, event_id, lead_id, timestamp, technician_id, effectiveness_rating, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (survey_id, event_id, survey.lead_id, now, survey.technician_id, survey.effectiveness_rating, survey.feedback, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "survey_id": survey_id}


@app.get("/api/v2/events/{event_id}/feedback")
def get_event_feedback(event_id: str):
    """Get aggregated survey feedback for an event."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT technician_id, effectiveness_rating, feedback FROM capture_survey WHERE event_id = ? ORDER BY created_at DESC", (event_id,))
    feedback = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"event_id": event_id, "feedback": feedback}


# --- Funnel Endpoints ---

@app.get("/api/v2/funnel/stages")
def get_funnel_stages():
    """List all recruiting funnel stages."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT stage_id, stage_name, sequence_order, description FROM funnel_stages ORDER BY sequence_order")
    stages = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"stages": stages}


@app.post("/api/v2/funnel/transition")
def record_funnel_transition(transition: FunnelTransitionCreate):
    """Move a lead between funnel stages."""
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO funnel_transitions (lead_id, from_stage, to_stage, transition_date, transition_reason, technician_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (transition.lead_id, transition.from_stage, transition.to_stage, now, transition.transition_reason, transition.technician_id, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": f"Lead {transition.lead_id} transitioned to {transition.to_stage}"}


@app.get("/api/v2/funnel/metrics")
def get_funnel_metrics():
    """Get conversion metrics across all funnel stages."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Count leads in each stage (via most recent transition)
    cur.execute("""
        SELECT DISTINCT on_stage, COUNT(*) as count
        FROM (
            SELECT lead_id, to_stage as on_stage
            FROM funnel_transitions
            WHERE (lead_id, created_at) IN (
                SELECT lead_id, MAX(created_at)
                FROM funnel_transitions
                GROUP BY lead_id
            )
        ) latest_stage
        GROUP BY on_stage
        ORDER BY on_stage
    """)
    
    # Fallback if distinct on not supported
    try:
        stage_counts = {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        cur.execute("""
            SELECT to_stage, COUNT(DISTINCT lead_id) as count
            FROM funnel_transitions
            GROUP BY to_stage
        """)
        stage_counts = {row[0]: row[1] for row in cur.fetchall()}
    
    conn.close()
    return {"stage_distribution": stage_counts}


# --- Project Management Endpoints ---

@app.post("/api/v2/projects")
def create_project(project: ProjectCreate):
    """Create an event planning project."""
    import uuid
    project_id = f"prj_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (project_id, name, event_id, start_date, target_date, owner_id, objectives, success_criteria, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?)
        """,
        (project_id, project.name, project.event_id, project.start_date, project.target_date, project.owner_id, project.objectives, project.success_criteria, now, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "project_id": project_id}


@app.post("/api/v2/projects/{project_id}/tasks")
def create_task(project_id: str, task: TaskCreate):
    """Create a task within a project."""
    import uuid
    task_id = f"tsk_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tasks (task_id, project_id, title, description, assigned_to, due_date, status, priority, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
        """,
        (task_id, project_id, task.title, task.description, task.assigned_to, task.due_date, task.priority, now, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "task_id": task_id}


@app.put("/api/v2/projects/{project_id}/tasks/{task_id}")
def update_task(project_id: str, task_id: str, updates: Dict[str, Any]):
    """Update task status, due date, etc."""
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    set_clause += ", updated_at = ?"
    values = list(updates.values()) + [now, task_id]
    
    cur.execute(f"UPDATE tasks SET {set_clause} WHERE task_id = ?", values)
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Task updated"}


@app.get("/api/v2/projects/{project_id}/timeline")
def get_project_timeline(project_id: str):
    """Get project milestones and timeline."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT milestone_id, name, target_date, actual_date FROM milestones WHERE project_id = ? ORDER BY target_date", (project_id,))
    milestones = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"project_id": project_id, "milestones": milestones}


# --- M-IPOE Endpoints ---

@app.post("/api/v2/mipoe")
def create_mipoe(mipoe: MIPOECreate):
    """Create/document M-IPOE phase (Intent, Plan, Order, Execute, Evaluate)."""
    import uuid
    mipoe_id = f"mip_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mipoe (mipoe_id, event_id, phase, content, owner_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (mipoe_id, mipoe.event_id, mipoe.phase, json.dumps(mipoe.content), mipoe.owner_id, now, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "mipoe_id": mipoe_id}


@app.get("/api/v2/mipoe/{mipoe_id}")
def get_mipoe(mipoe_id: str):
    """Retrieve M-IPOE record."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT event_id, phase, content, owner_id, created_at, updated_at FROM mipoe WHERE mipoe_id = ?", (mipoe_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="M-IPOE not found")
    return {
        "mipoe_id": mipoe_id,
        "event_id": row[0],
        "phase": row[1],
        "content": json.loads(row[2]),
        "owner_id": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


# --- Targeting Profile (D3AE/F3A) Endpoints ---

@app.post("/api/v2/targeting-profiles")
def create_targeting_profile(profile: TargetingProfileCreate):
    """Create targeting profile with D3AE/F3A principles."""
    import uuid
    profile_id = f"tgt_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO targeting_profiles (profile_id, event_id, target_age_min, target_age_max, target_education_level, target_locations, message_themes, contact_frequency, conversion_target, cost_per_lead_target, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (profile_id, profile.event_id, profile.target_age_min, profile.target_age_max, profile.target_education_level, profile.target_locations, profile.message_themes, profile.contact_frequency, profile.conversion_target, profile.cost_per_lead_target, now, now),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "profile_id": profile_id}


@app.get("/api/v2/targeting-profiles/{profile_id}")
def get_targeting_profile(profile_id: str):
    """Retrieve targeting profile."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id, target_age_min, target_age_max, target_education_level, target_locations, message_themes, contact_frequency, conversion_target, cost_per_lead_target, created_at, updated_at
        FROM targeting_profiles WHERE profile_id = ?
    """, (profile_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Targeting profile not found")
    return {
        "profile_id": profile_id,
        "event_id": row[0],
        "target_age_min": row[1],
        "target_age_max": row[2],
        "target_education_level": row[3],
        "target_locations": row[4],
        "message_themes": row[5],
        "contact_frequency": row[6],
        "conversion_target": row[7],
        "cost_per_lead_target": row[8],
        "created_at": row[9],
        "updated_at": row[10],
    }


# --- Forecasting & Analytics Endpoints ---

@app.get("/api/v2/forecasts/{quarter}/{year}")
def get_forecast(quarter: int, year: int):
    """Get quarterly forecast."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT forecast_id, projected_leads, projected_conversions, projected_roi, confidence_level, methodology, created_at FROM forecasts WHERE quarter = ? AND year = ?", (quarter, year))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"quarter": quarter, "year": year, "message": "No forecast available"}
    return {
        "forecast_id": row[0],
        "quarter": quarter,
        "year": year,
        "projected_leads": row[1],
        "projected_conversions": row[2],
        "projected_roi": row[3],
        "confidence_level": row[4],
        "methodology": row[5],
        "created_at": row[6],
    }


@app.post("/api/v2/forecasts/generate")
def generate_forecast(quarter: int, year: int):
    """Trigger forecast generation (can use historical data or ML model)."""
    import uuid
    forecast_id = f"fct_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    # Simple heuristic: use average metrics from historical data
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), AVG(conversion_count), AVG(roi) FROM event_metrics")
    row = cur.fetchone()
    
    total_events = row[0] or 1
    avg_conversions = row[1] or 5
    avg_roi = row[2] or 1.5
    
    # Project forward
    projected_leads = int(total_events * 10 * (quarter / 4))
    projected_conversions = int(projected_leads * (avg_conversions / 100))
    projected_roi = avg_roi
    confidence = 0.75
    
    cur.execute(
        """
        INSERT OR REPLACE INTO forecasts (forecast_id, quarter, year, projected_leads, projected_conversions, projected_roi, confidence_level, methodology, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (forecast_id, quarter, year, projected_leads, projected_conversions, projected_roi, confidence, "historical_average", now, now),
    )
    conn.commit()
    conn.close()
    return {
        "status": "ok",
        "forecast_id": forecast_id,
        "quarter": quarter,
        "year": year,
        "projected_leads": projected_leads,
        "projected_conversions": projected_conversions,
        "projected_roi": projected_roi,
        "confidence_level": confidence,
    }


@app.get("/api/v2/analytics/dashboard")
def get_dashboard_snapshot():
    """Get comprehensive dashboard snapshot (all metrics, by quarter)."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Aggregate current quarter metrics
    cur.execute("SELECT COUNT(*), SUM(leads_generated), SUM(conversion_count), AVG(cost_per_lead), AVG(roi) FROM event_metrics")
    row = cur.fetchone()
    
    total_events = row[0] or 0
    total_leads = row[1] or 0
    total_conversions = row[2] or 0
    avg_cost = row[3] or 0
    avg_roi = row[4] or 0
    conversion_rate = (total_conversions / total_leads) if total_leads > 0 else 0
    
    conn.close()
    return {
        "dashboard": {
            "total_events": total_events,
            "total_leads": total_leads,
            "total_conversions": total_conversions,
            "conversion_rate": round(conversion_rate, 4),
            "avg_cost_per_lead": round(avg_cost, 2),
            "avg_roi": round(avg_roi, 2),
        }
    }


# --- NEW: Marketing Activity Tracking (USAREC Integration) ---

@app.post("/api/v2/marketing/activities")
def record_marketing_activity(data: MarketingActivityCreate):
    """Record marketing activity metrics (impressions, engagement, awareness, activation)."""
    import uuid
    conn = get_db_conn()
    cur = conn.cursor()
    
    activity_id = f"mkt_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()
    
    cur.execute(
        """
        INSERT INTO marketing_activities 
        (activity_id, event_id, activity_type, campaign_name, channel, data_source, 
         impressions, engagement_count, awareness_metric, activation_conversions, 
         reporting_date, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            activity_id, data.event_id, data.activity_type, data.campaign_name, 
            data.channel, data.data_source, data.impressions, data.engagement_count, 
            data.awareness_metric, data.activation_conversions, data.reporting_date, 
            data.metadata, now, now
        )
    )
    conn.commit()
    conn.close()
    
    return {"status": "ok", "activity_id": activity_id}


@app.get("/api/v2/marketing/activities")
def get_marketing_activities(event_id: Optional[str] = None, data_source: Optional[str] = None):
    """Get marketing activities (filtered by event or data source)."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    query = "SELECT * FROM marketing_activities WHERE 1=1"
    params = []
    
    if event_id:
        query += " AND event_id = ?"
        params.append(event_id)
    if data_source:
        query += " AND data_source = ?"
        params.append(data_source)
    
    query += " ORDER BY reporting_date DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    activities = [dict(row) for row in rows]
    return {"status": "ok", "count": len(activities), "activities": activities}


@app.get("/api/v2/marketing/analytics")
def get_marketing_analytics(event_id: Optional[str] = None):
    """Get aggregated marketing performance metrics."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    if event_id:
        cur.execute(
            """
            SELECT 
                SUM(impressions) as total_impressions,
                SUM(engagement_count) as total_engagement,
                AVG(awareness_metric) as avg_awareness,
                SUM(activation_conversions) as total_activations,
                COUNT(DISTINCT data_source) as sources_count,
                COUNT(DISTINCT channel) as channels_count
            FROM marketing_activities
            WHERE event_id = ?
            """,
            (event_id,)
        )
    else:
        cur.execute(
            """
            SELECT 
                SUM(impressions) as total_impressions,
                SUM(engagement_count) as total_engagement,
                AVG(awareness_metric) as avg_awareness,
                SUM(activation_conversions) as total_activations,
                COUNT(DISTINCT data_source) as sources_count,
                COUNT(DISTINCT channel) as channels_count
            FROM marketing_activities
            """
        )
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return {
            "status": "ok",
            "total_impressions": 0,
            "total_engagement": 0,
            "avg_awareness": 0.0,
            "total_activations": 0,
            "sources_count": 0,
            "channels_count": 0
        }
    
    return {
        "status": "ok",
        "total_impressions": row[0] or 0,
        "total_engagement": row[1] or 0,
        "avg_awareness": round(row[2] or 0.0, 2),
        "total_activations": row[3] or 0,
        "sources_count": row[4] or 0,
        "channels_count": row[5] or 0
    }


@app.get("/api/v2/kpis")
def get_kpis(event_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, data_source: Optional[str] = None, segment_key: Optional[str] = None, segment_value: Optional[str] = None):
    """Compute derived KPIs: CPL, CPE, CPC, total event/campaign cost.

    - If `event_id` provided, scope to that event.
    - Optionally filter by `start_date`/`end_date` (reporting_date on activities).
    - `segment_key` and `segment_value` perform a simple substring match against serialized segment JSON in `segment_profiles`.
    """
    conn = get_db_conn()
    cur = conn.cursor()

    params = []
    where_clauses = []

    if event_id:
        where_clauses.append("ma.event_id = ?")
        params.append(event_id)

    if data_source:
        where_clauses.append("ma.data_source = ?")
        params.append(data_source)

    if start_date:
        where_clauses.append("ma.reporting_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("ma.reporting_date <= ?")
        params.append(end_date)

    base_where = ""
    if where_clauses:
        base_where = "WHERE " + " AND ".join(where_clauses)

    # Aggregate activity-level sums
    query = f"SELECT SUM(ma.cost) as total_cost, SUM(ma.impressions) as impressions, SUM(ma.engagement_count) as engagements, SUM(ma.activation_conversions) as activations FROM marketing_activities ma {base_where}"
    cur.execute(query, params)
    row = cur.fetchone()
    total_cost = row[0] or 0.0
    total_impressions = row[1] or 0
    total_engagements = row[2] or 0
    total_activations = row[3] or 0

    # Include budgets for event-level if event_id provided
    budget_total = 0.0
    if event_id:
        cur.execute("SELECT SUM(allocated_amount) FROM budgets WHERE event_id = ?", (event_id,))
        brow = cur.fetchone()
        if brow and brow[0]:
            budget_total = brow[0]

    # Combine costs (activity-level cost + budgets)
    combined_cost = float(total_cost or 0.0) + float(budget_total or 0.0)

    # Compute derived KPIs with safe guards
    cpl = (combined_cost / total_activations) if total_activations > 0 else None
    cpe = (combined_cost / total_engagements) if total_engagements > 0 else None
    cpc = (combined_cost / total_impressions) if total_impressions > 0 else None

    result = {
        "status": "ok",
        "total_cost": combined_cost,
        "budget_total": budget_total,
        "activity_cost": total_cost,
        "total_impressions": total_impressions,
        "total_engagements": total_engagements,
        "total_activations": total_activations,
        "cpl": round(cpl, 2) if cpl is not None else None,
        "cpe": round(cpe, 2) if cpe is not None else None,
        "cpc": round(cpc, 4) if cpc is not None else None,
    }

    # If segment filter provided, compute segment-level KPIs by joining segment_profiles
    if segment_key and segment_value:
        seg_clause = f"AND sp.segments LIKE ?"
        seg_param = f'%"{segment_key}": "{segment_value}"%'
        # Need to run a join query
        seg_query = f"SELECT SUM(ma.cost) as total_cost, SUM(ma.impressions) as impressions, SUM(ma.engagement_count) as engagements, SUM(ma.activation_conversions) as activations FROM marketing_activities ma JOIN segment_profiles sp ON sp.lead_id = ma.event_id {('WHERE ' + ' AND '.join(where_clauses) + ' ') if where_clauses else 'WHERE '} AND sp.segments LIKE ?"
        # Build params for seg_query
        seg_params = params.copy()
        seg_params.append(seg_param)
        try:
            cur.execute(seg_query, seg_params)
            srow = cur.fetchone()
            s_total_cost = srow[0] or 0.0
            s_impressions = srow[1] or 0
            s_engagements = srow[2] or 0
            s_activations = srow[3] or 0
            scpl = (s_total_cost / s_activations) if s_activations > 0 else None
            scpe = (s_total_cost / s_engagements) if s_engagements > 0 else None
            scpc = (s_total_cost / s_impressions) if s_impressions > 0 else None
            result["segment"] = {
                "key": segment_key,
                "value": segment_value,
                "total_cost": s_total_cost,
                "impressions": s_impressions,
                "engagements": s_engagements,
                "activations": s_activations,
                "cpl": round(scpl, 2) if scpl is not None else None,
                "cpe": round(scpe, 2) if scpe is not None else None,
                "cpc": round(scpc, 4) if scpc is not None else None,
            }
        except Exception:
            # If join fails (data shapes), skip segment breakdown
            result["segment"] = {"error": "segment breakdown unavailable"}

    conn.close()
    return result


def _stream_csv(rows, headers):
    """Helper to stream CSV from rows (iterable of dict) and headers list."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in headers})
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv")


# --- Simple token-based auth for export endpoints ---
EXPORT_API_TOKEN = os.environ.get("EXPORT_API_TOKEN", "devtoken123")


def _verify_export_token(request: Request):
    # Look for X-API-KEY or Bearer token
    key = request.headers.get("X-API-KEY") or None
    if not key:
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            key = auth.split(None, 1)[1].strip()
    if not key or key != EXPORT_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


# --- Export scheduler (background thread) ---
_export_scheduler = {"thread": None, "stop_event": None, "interval": None}


def _export_worker(interval: int, stop_event: "threading.Event"):
    import time
    while not stop_event.is_set():
        try:
            # call internal export runner
            run_exports()
        except Exception:
            logging.exception("Scheduled export failed")
        # wait for interval or stop
        stop_event.wait(interval)




@app.get("/api/v2/exports/activities.csv")
def export_activities_csv(event_id: Optional[str] = None, data_source: Optional[str] = None, request: Request = None):
    """Return a CSV of marketing activities optionally filtered by event_id or data_source."""
    if request is not None:
        _verify_export_token(request)
    conn = get_db_conn()
    cur = conn.cursor()
    params = []
    where = []
    if event_id:
        where.append("event_id = ?")
        params.append(event_id)
    if data_source:
        where.append("data_source = ?")
        params.append(data_source)
    # include segment JSON columns where lead_id matches event_id (best-effort)
    q = "SELECT ma.activity_id, ma.event_id, ma.activity_type, ma.campaign_name, ma.channel, ma.data_source, ma.impressions, ma.engagement_count, ma.awareness_metric, ma.activation_conversions, ma.cost, ma.reporting_date, ma.metadata, ma.created_at, (SELECT sp.segments FROM segment_profiles sp WHERE sp.lead_id = ma.event_id LIMIT 1) as segments, (SELECT sp.attributes FROM segment_profiles sp WHERE sp.lead_id = ma.event_id LIMIT 1) as attributes FROM marketing_activities ma"
    if where:
        q += " WHERE " + " AND ".join(where)
    cur.execute(q, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    headers = ["activity_id", "event_id", "activity_type", "campaign_name", "channel", "data_source", "impressions", "engagement_count", "awareness_metric", "activation_conversions", "cost", "reporting_date", "metadata", "created_at", "segments", "attributes"]
    return _stream_csv(rows, headers)


@app.get("/api/v2/exports/kpis.csv")
def export_kpis_csv(event_id: Optional[str] = None, request: Request = None):
    """Return a CSV with KPI rows (per event or overall)."""
    if request is not None:
        _verify_export_token(request)
    conn = get_db_conn()
    cur = conn.cursor()
    if event_id:
        cur.execute("SELECT event_id FROM events WHERE event_id = ?", (event_id,))
        if not cur.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="event not found")
        # return a single-row CSV for the event
        kpi = get_kpis(event_id=event_id)
        row = {
            "event_id": event_id,
            "total_cost": kpi.get("total_cost"),
            "activity_cost": kpi.get("activity_cost"),
            "budget_total": kpi.get("budget_total"),
            "total_impressions": kpi.get("total_impressions"),
            "total_engagements": kpi.get("total_engagements"),
            "total_activations": kpi.get("total_activations"),
            "cpl": kpi.get("cpl"),
            "cpe": kpi.get("cpe"),
            "cpc": kpi.get("cpc"),
        }
        conn.close()
        return _stream_csv([row], list(row.keys()))
    # otherwise, return KPIs for all events
    cur.execute("SELECT event_id FROM events")
    events = [r[0] for r in cur.fetchall()]
    rows = []
    for ev in events:
        kpi = get_kpis(event_id=ev)
        rows.append({
            "event_id": ev,
            "total_cost": kpi.get("total_cost"),
            "activity_cost": kpi.get("activity_cost"),
            "budget_total": kpi.get("budget_total"),
            "total_impressions": kpi.get("total_impressions"),
            "total_engagements": kpi.get("total_engagements"),
            "total_activations": kpi.get("total_activations"),
            "cpl": kpi.get("cpl"),
            "cpe": kpi.get("cpe"),
            "cpc": kpi.get("cpc"),
        })
    conn.close()
    headers = ["event_id", "total_cost", "activity_cost", "budget_total", "total_impressions", "total_engagements", "total_activations", "cpl", "cpe", "cpc"]
    return _stream_csv(rows, headers)


@app.post("/api/v2/exports/run")
def run_exports(request: Request = None):
    """Run exports and write CSV files to the `exports/` folder inside project root."""
    if request is not None:
        _verify_export_token(request)
    exports_dir = Path(os.path.join(os.path.dirname(__file__), "exports"))
    exports_dir.mkdir(parents=True, exist_ok=True)
    # Write activities.csv
    act_resp = export_activities_csv()
    # act_resp is a StreamingResponse backed by StringIO; read its body
    act_body = act_resp.body_iterator
    # To write, call export endpoint logic directly to obtain rows
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT activity_id, event_id, activity_type, campaign_name, channel, data_source, impressions, engagement_count, awareness_metric, activation_conversions, cost, reporting_date, metadata, created_at FROM marketing_activities")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    activities_path = exports_dir / "activities.csv"
    with activities_path.open("w", newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=["activity_id", "event_id", "activity_type", "campaign_name", "channel", "data_source", "impressions", "engagement_count", "awareness_metric", "activation_conversions", "cost", "reporting_date", "metadata", "created_at"]) 
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Write kpis.csv
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT event_id FROM events")
    events = [r[0] for r in cur.fetchall()]
    kpis_path = exports_dir / "kpis.csv"
    with kpis_path.open("w", newline='') as fh:
        headers = ["event_id", "total_cost", "activity_cost", "budget_total", "total_impressions", "total_engagements", "total_activations", "cpl", "cpe", "cpc"]
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for ev in events:
            kpi = get_kpis(event_id=ev)
            writer.writerow({
                "event_id": ev,
                "total_cost": kpi.get("total_cost"),
                "activity_cost": kpi.get("activity_cost"),
                "budget_total": kpi.get("budget_total"),
                "total_impressions": kpi.get("total_impressions"),
                "total_engagements": kpi.get("total_engagements"),
                "total_activations": kpi.get("total_activations"),
                "cpl": kpi.get("cpl"),
                "cpe": kpi.get("cpe"),
                "cpc": kpi.get("cpc"),
            })

    return {"status": "ok", "exports": [str(activities_path), str(kpis_path)]}


@app.post("/api/v2/exports/schedule")
def schedule_exports(interval_seconds: int = 300, request: Request = None):
    """Start a background export scheduler that runs every `interval_seconds` seconds."""
    if request is not None:
        _verify_export_token(request)
    import threading
    if _export_scheduler.get("thread") and _export_scheduler.get("thread").is_alive():
        return {"status": "ok", "message": "scheduler already running", "interval": _export_scheduler.get("interval")}
    stop_event = threading.Event()
    t = threading.Thread(target=_export_worker, args=(interval_seconds, stop_event), daemon=True)
    _export_scheduler["thread"] = t
    _export_scheduler["stop_event"] = stop_event
    _export_scheduler["interval"] = interval_seconds
    t.start()
    return {"status": "ok", "message": "scheduler started", "interval": interval_seconds}


@app.post("/api/v2/exports/schedule/stop")
def stop_export_scheduler(request: Request = None):
    if request is not None:
        _verify_export_token(request)
    import threading
    ev = _export_scheduler.get("stop_event")
    th = _export_scheduler.get("thread")
    if ev:
        ev.set()
    if th and th.is_alive():
        th.join(timeout=2)
    _export_scheduler["thread"] = None
    _export_scheduler["stop_event"] = None
    _export_scheduler["interval"] = None
    return {"status": "ok", "message": "scheduler stopped"}


@app.get("/api/v2/odata/activities")
def odata_activities(select: Optional[str] = None, filter: Optional[str] = None, top: Optional[int] = None, skip: Optional[int] = None, request: Request = None):
    """Simple OData-like endpoint for marketing activities supporting select, filter (single equality), top, skip.

    Example: /api/v2/odata/activities?select=activity_id,activity_type&filter=activity_type eq 'social_media'&top=10
    """
    if request is not None:
        _verify_export_token(request)
    conn = get_db_conn()
    cur = conn.cursor()

    allowed_cols = {"activity_id", "event_id", "activity_type", "campaign_name", "channel", "data_source", "impressions", "engagement_count", "reporting_date", "cost"}

    if select:
        cols = [c.strip() for c in select.split(',') if c.strip() and c.strip() in allowed_cols]
        if not cols:
            cols = ["activity_id", "event_id", "activity_type"]
    else:
        cols = ["activity_id", "event_id", "activity_type", "campaign_name", "channel", "data_source", "impressions", "engagement_count", "reporting_date"]

    params = []
    where_clauses = []
    if filter:
        parts = filter.split(" eq ")
        if len(parts) == 2:
            field = parts[0].strip()
            val = parts[1].strip().strip("'\"")
            if field in allowed_cols:
                where_clauses.append(f"{field} = ?")
                params.append(val)

    q = f"SELECT {', '.join(cols)} FROM marketing_activities"
    if where_clauses:
        q += " WHERE " + " AND ".join(where_clauses)

    if top is not None:
        q += f" LIMIT {top}"
    if skip is not None:
        if "LIMIT" in q:
            q += f" OFFSET {skip}"
        else:
            q += f" LIMIT -1 OFFSET {skip}"

    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "items": rows}


@app.get("/api/v2/marketing/sources")
def get_data_sources():
    """Get list of available USAREC data sources (EMM, iKrome, Vantage, G2, AIEM, USAREC Systems)."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT mapping_id, source_system, source_name, description, last_sync, sync_status FROM data_source_mappings ORDER BY source_system")
    rows = cur.fetchall()
    conn.close()
    
    sources = [dict(row) for row in rows]
    return {"status": "ok", "sources": sources}


@app.post("/api/v2/marketing/sync")
def sync_data_source(data: DataSourceSync):
    """Sync data from a USAREC data source (EMM, iKrome, Vantage, G2, AIEM, USAREC Systems)."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Validate data source
    cur.execute("SELECT mapping_id FROM data_source_mappings WHERE source_system = ?", (data.source_system,))
    if not cur.fetchone():
        conn.close()
        return {"status": "error", "message": f"Unknown data source: {data.source_system}"}
    
    # Update sync status
    cur.execute(
        "UPDATE data_source_mappings SET last_sync = ?, sync_status = ?, updated_at = ? WHERE source_system = ?",
        (now, "synced", now, data.source_system)
    )
    
    # Parse incoming data and create marketing activities
    activities_created = 0
    if isinstance(data.sync_data, dict):
        for key, value in data.sync_data.items():
            if isinstance(value, dict) and all(k in value for k in ['campaign', 'impressions', 'engagement']):
                import uuid
                activity_id = f"mkt_{uuid.uuid4().hex[:12]}"
                
                cur.execute(
                    """
                    INSERT INTO marketing_activities 
                    (activity_id, activity_type, campaign_name, channel, data_source, 
                     impressions, engagement_count, awareness_metric, activation_conversions, 
                     reporting_date, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        activity_id, value.get('type', 'sync'), value.get('campaign', key), 
                        value.get('channel', key), data.source_system,
                        int(value.get('impressions', 0)), int(value.get('engagement', 0)),
                        float(value.get('awareness', 0.0)), int(value.get('activation', 0)),
                        datetime.now().date().isoformat(), json.dumps(value),
                        now, now
                    )
                )
                activities_created += 1
    
    conn.commit()
    conn.close()
    
    return {
        "status": "ok",
        "source": data.source_system,
        "activities_created": activities_created,
        "sync_timestamp": now
    }


@app.get("/api/v2/marketing/funnel-attribution")
def get_funnel_attribution(data_source: Optional[str] = None):
    """Get marketing attribution by recruiting funnel stage."""
    conn = get_db_conn()
    cur = conn.cursor()
    
    if data_source:
        cur.execute(
            """
            SELECT 
                fs.stage_name,
                COUNT(DISTINCT ft.lead_id) as leads_in_stage,
                SUM(ma.impressions) as total_impressions,
                SUM(ma.engagement_count) as total_engagement,
                AVG(ma.awareness_metric) as avg_awareness,
                SUM(ma.activation_conversions) as activations
            FROM funnel_stages fs
            LEFT JOIN funnel_transitions ft ON fs.stage_id = ft.to_stage
            LEFT JOIN marketing_activities ma ON ma.data_source = ?
            GROUP BY fs.stage_id, fs.stage_name
            ORDER BY fs.sequence_order
            """,
            (data_source,)
        )
    else:
        cur.execute(
            """
            SELECT 
                fs.stage_name,
                COUNT(DISTINCT ft.lead_id) as leads_in_stage,
                SUM(ma.impressions) as total_impressions,
                SUM(ma.engagement_count) as total_engagement,
                AVG(ma.awareness_metric) as avg_awareness,
                SUM(ma.activation_conversions) as activations
            FROM funnel_stages fs
            LEFT JOIN funnel_transitions ft ON fs.stage_id = ft.to_stage
            LEFT JOIN marketing_activities ma ON 1=1
            GROUP BY fs.stage_id, fs.stage_name
            ORDER BY fs.sequence_order
            """
        )
    
    rows = cur.fetchall()
    conn.close()
    
    attribution = [
        {
            "stage": row[0],
            "leads_in_stage": row[1] or 0,
            "impressions": row[2] or 0,
            "engagement": row[3] or 0,
            "awareness": round(row[4] or 0.0, 2),
            "activations": row[5] or 0
        }
        for row in rows
    ]
    
    return {"status": "ok", "attribution": attribution}


if __name__ == "__main__":
    uvicorn.run("taaip_service:app", host="0.0.0.0", port=8000, reload=False)