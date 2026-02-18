"""
SQLAlchemy ORM Models for TAAIP 2.0
Replaces direct SQLite queries with proper ORM
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database.config import Base


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(100), unique=True, index=True)
    age = Column(Integer)
    education_level = Column(String(50))
    cbsa_code = Column(String(20))
    campaign_source = Column(String(100))
    received_at = Column(DateTime, default=datetime.utcnow)
    predicted_probability = Column(Float)
    score = Column(Integer)
    recommendation = Column(Text)
    converted = Column(Boolean, default=False)
    raw_json = Column(Text)
    
    # Archival fields
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    archived_reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    segment_profile = relationship("SegmentProfile", back_populates="lead", uselist=False)


class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50))
    location = Column(String(255))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    budget = Column(Float)
    team_size = Column(Integer)
    targeting_principles = Column(Text)
    status = Column(String(50), default="planned")
    
    # Archival fields
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    metrics = relationship("EventMetric", back_populates="event", cascade="all, delete-orphan")
    surveys = relationship("CaptureSurvey", back_populates="event")
    projects = relationship("Project", back_populates="event")


class EventMetric(Base):
    __tablename__ = "event_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), ForeignKey("events.event_id"), nullable=False)
    date = Column(DateTime)
    leads_generated = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)
    cost_per_lead = Column(Float)
    roi = Column(Float)
    engagement_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="metrics")


class CaptureSurvey(Base):
    __tablename__ = "capture_survey"
    
    survey_id = Column(String(100), primary_key=True)
    event_id = Column(String(100), ForeignKey("events.event_id"), nullable=False)
    lead_id = Column(String(100))
    timestamp = Column(DateTime)
    technician_id = Column(String(100))
    effectiveness_rating = Column(Integer)
    feedback = Column(Text)
    data_quality_flag = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="surveys")


class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    event_id = Column(String(100), ForeignKey("events.event_id"), nullable=True)
    start_date = Column(DateTime)
    target_date = Column(DateTime)
    owner_id = Column(String(100))
    status = Column(String(50), default="planning")
    objectives = Column(Text)
    success_criteria = Column(Text)
    
    # Enhanced fields
    funding_status = Column(String(50), default="requested")
    funding_amount = Column(Float, default=0.0)
    spent_amount = Column(Float, default=0.0)
    percent_complete = Column(Integer, default=0)
    risk_level = Column(String(20))
    next_milestone = Column(String(255))
    blockers = Column(Text)
    
    # Archival fields
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    
    task_id = Column(String(100), primary_key=True)
    project_id = Column(String(100), ForeignKey("projects.project_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assigned_to = Column(String(100))
    due_date = Column(DateTime)
    status = Column(String(50), default="open")
    priority = Column(String(20))
    completion_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")


class Milestone(Base):
    __tablename__ = "milestones"
    
    milestone_id = Column(String(100), primary_key=True)
    project_id = Column(String(100), ForeignKey("projects.project_id"), nullable=False)
    name = Column(String(255), nullable=False)
    target_date = Column(DateTime)
    actual_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="milestones")


class SegmentProfile(Base):
    __tablename__ = "segment_profiles"
    
    profile_id = Column(String(100), primary_key=True)
    lead_id = Column(String(100), ForeignKey("leads.lead_id"), nullable=True)
    segments = Column(JSON)  # Store as JSON for flexibility
    attributes = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="segment_profile")
    history = relationship("SegmentHistory", back_populates="profile", cascade="all, delete-orphan")


class SegmentHistory(Base):
    __tablename__ = "segment_history"
    
    history_id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String(100), ForeignKey("segment_profiles.profile_id"))
    lead_id = Column(String(100))
    segments = Column(JSON)
    attributes = Column(JSON)
    changed_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    profile = relationship("SegmentProfile", back_populates="history")


class ArchivedRecord(Base):
    """Universal archive table for all soft-deleted records"""
    __tablename__ = "archived_records"
    
    archive_id = Column(String(100), primary_key=True)
    original_table = Column(String(100), nullable=False, index=True)
    original_id = Column(String(100), nullable=False)
    record_data = Column(JSON, nullable=False)  # Full JSON snapshot
    archived_at = Column(DateTime, default=datetime.utcnow)
    archived_by = Column(String(100))
    archive_reason = Column(String(255))
    is_deleted = Column(Boolean, default=False)  # True if "deleted", False if just archived
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class DataValidationLog(Base):
    """Track all data validation checks"""
    __tablename__ = "data_validation_log"
    
    log_id = Column(String(100), primary_key=True)
    record_type = Column(String(100), nullable=False)
    record_id = Column(String(100))
    validation_result = Column(String(20))  # passed, failed, warning
    errors = Column(JSON)  # List of error messages
    warnings = Column(JSON)  # List of warnings
    validated_at = Column(DateTime, default=datetime.utcnow)
    validated_by = Column(String(100))
    
    # For tracking data quality over time
    quality_score = Column(Float)  # 0-100


class SocialMediaMetric(Base):
    """Social media metrics from Sprinklr"""
    __tablename__ = "social_media_metrics"
    
    metric_id = Column(String(100), primary_key=True)
    platform = Column(String(50))  # Facebook, Instagram, Twitter, etc.
    post_id = Column(String(255))
    post_date = Column(DateTime)
    impressions = Column(Integer, default=0)
    engagements = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    video_views = Column(Integer, default=0)
    engagement_rate = Column(Float)
    sentiment_score = Column(Float, nullable=True)
    campaign_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DataSourceSync(Base):
    """Track sync status for external data sources"""
    __tablename__ = "data_source_sync"
    
    sync_id = Column(String(100), primary_key=True)
    source_system = Column(String(100), nullable=False)  # EMM, iKrome, Sprinklr, etc.
    sync_type = Column(String(50))  # full, incremental
    status = Column(String(50))  # running, completed, failed
    records_synced = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
