"""
Archival Manager for TAAIP 2.0
Implements no-delete policy - all records are archived, never truly deleted
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class ArchivalManager:
    """Manage data archival and historical record keeping"""
    
    @staticmethod
    async def archive_record(
        db: Session,
        table_name: str,
        record_id: str,
        record_data: Dict[str, Any],
        reason: str,
        archived_by: str,
        soft_delete: bool = False
    ) -> str:
        """
        Archive a record instead of deleting it
        
        Args:
            table_name: Source table name
            record_id: Original record ID
            record_data: Full record as dictionary
            reason: Reason for archiving
            archived_by: User/system that archived it
            soft_delete: If True, mark as deleted (else just archived)
            
        Returns:
            Archive ID
        """
        from database.models import ArchivedRecord
        
        archive_id = str(uuid.uuid4())
        
        try:
            # Create archive record
            archived = ArchivedRecord(
                archive_id=archive_id,
                original_table=table_name,
                original_id=record_id,
                record_data=record_data,
                archived_at=datetime.utcnow(),
                archived_by=archived_by,
                archive_reason=reason,
                is_deleted=soft_delete
            )
            
            db.add(archived)
            
            # Mark original record as archived (if table has is_archived column)
            try:
                table_class = ArchivalManager._get_table_class(table_name)
                if table_class:
                    original = db.query(table_class).filter_by(**{
                        ArchivalManager._get_id_field(table_name): record_id
                    }).first()
                    
                    if original and hasattr(original, 'is_archived'):
                        original.is_archived = True
                        original.archived_at = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Could not update original record: {e}")
            
            db.commit()
            logger.info(f"Archived {table_name}/{record_id} -> {archive_id}")
            return archive_id
            
        except Exception as e:
            logger.error(f"Failed to archive record: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def restore_record(
        db: Session,
        archive_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Restore an archived record
        
        Args:
            archive_id: Archive record ID
            
        Returns:
            Restored record data or None
        """
        from database.models import ArchivedRecord
        
        try:
            archived = db.query(ArchivedRecord).filter_by(archive_id=archive_id).first()
            
            if not archived:
                logger.warning(f"Archive record not found: {archive_id}")
                return None
            
            # Get original table class
            table_class = ArchivalManager._get_table_class(archived.original_table)
            if not table_class:
                logger.error(f"Unknown table: {archived.original_table}")
                return None
            
            # Check if original still exists
            id_field = ArchivalManager._get_id_field(archived.original_table)
            original = db.query(table_class).filter_by(**{
                id_field: archived.original_id
            }).first()
            
            if original:
                # Unmark as archived
                if hasattr(original, 'is_archived'):
                    original.is_archived = False
                    original.archived_at = None
            else:
                # Recreate from archived data
                new_record = table_class(**archived.record_data)
                db.add(new_record)
            
            db.commit()
            logger.info(f"Restored {archived.original_table}/{archived.original_id}")
            return archived.record_data
            
        except Exception as e:
            logger.error(f"Failed to restore record: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def get_archived_records(
        db: Session,
        table_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False
    ) -> list:
        """
        Query archived records with filters
        
        Args:
            table_name: Filter by source table
            start_date: Filter by archive date (start)
            end_date: Filter by archive date (end)
            include_deleted: Include soft-deleted records
            
        Returns:
            List of archived records
        """
        from database.models import ArchivedRecord
        
        query = db.query(ArchivedRecord)
        
        if table_name:
            query = query.filter(ArchivedRecord.original_table == table_name)
        
        if start_date:
            query = query.filter(ArchivedRecord.archived_at >= start_date)
        
        if end_date:
            query = query.filter(ArchivedRecord.archived_at <= end_date)
        
        if not include_deleted:
            query = query.filter(ArchivedRecord.is_deleted == False)
        
        return query.all()
    
    @staticmethod
    async def get_record_history(
        db: Session,
        table_name: str,
        record_id: str
    ) -> list:
        """
        Get full history of a record (including archived versions)
        
        Args:
            table_name: Source table
            record_id: Record ID
            
        Returns:
            List of all versions (current + archived)
        """
        from database.models import ArchivedRecord
        
        history = []
        
        # Get current version
        table_class = ArchivalManager._get_table_class(table_name)
        if table_class:
            id_field = ArchivalManager._get_id_field(table_name)
            current = db.query(table_class).filter_by(**{id_field: record_id}).first()
            if current:
                history.append({
                    "version": "current",
                    "date": current.updated_at if hasattr(current, 'updated_at') else None,
                    "data": ArchivalManager._model_to_dict(current)
                })
        
        # Get archived versions
        archived = db.query(ArchivedRecord).filter_by(
            original_table=table_name,
            original_id=record_id
        ).order_by(ArchivedRecord.archived_at.desc()).all()
        
        for arch in archived:
            history.append({
                "version": arch.archive_id,
                "date": arch.archived_at,
                "reason": arch.archive_reason,
                "archived_by": arch.archived_by,
                "data": arch.record_data
            })
        
        return history
    
    @staticmethod
    def _get_table_class(table_name: str):
        """Get SQLAlchemy model class from table name"""
        from database.models import (
            Lead, Event, EventMetric, CaptureSurvey, Project,
            Task, Milestone, SegmentProfile, SegmentHistory
        )
        
        table_map = {
            "leads": Lead,
            "events": Event,
            "event_metrics": EventMetric,
            "capture_survey": CaptureSurvey,
            "projects": Project,
            "tasks": Task,
            "milestones": Milestone,
            "segment_profiles": SegmentProfile,
            "segment_history": SegmentHistory
        }
        
        return table_map.get(table_name)
    
    @staticmethod
    def _get_id_field(table_name: str) -> str:
        """Get primary key field name for table"""
        id_map = {
            "leads": "lead_id",
            "events": "event_id",
            "event_metrics": "metric_id",
            "capture_survey": "survey_id",
            "projects": "project_id",
            "tasks": "task_id",
            "milestones": "milestone_id",
            "segment_profiles": "profile_id",
            "segment_history": "history_id"
        }
        return id_map.get(table_name, "id")
    
    @staticmethod
    def _model_to_dict(model) -> dict:
        """Convert SQLAlchemy model to dictionary"""
        return {c.name: getattr(model, c.name) for c in model.__table__.columns}


class DashboardArchiver:
    """Archive dashboard configurations and reports"""
    
    @staticmethod
    async def archive_dashboard(
        db: Session,
        dashboard_id: str,
        dashboard_config: Dict[str, Any],
        archived_by: str
    ) -> str:
        """Save dashboard configuration for historical reference"""
        return await ArchivalManager.archive_record(
            db=db,
            table_name="dashboards",
            record_id=dashboard_id,
            record_data=dashboard_config,
            reason="Dashboard configuration snapshot",
            archived_by=archived_by,
            soft_delete=False
        )
    
    @staticmethod
    async def archive_report(
        db: Session,
        report_id: str,
        report_data: Dict[str, Any],
        generated_by: str
    ) -> str:
        """Preserve generated report indefinitely"""
        return await ArchivalManager.archive_record(
            db=db,
            table_name="reports",
            record_id=report_id,
            record_data=report_data,
            reason="Generated report archive",
            archived_by=generated_by,
            soft_delete=False
        )
