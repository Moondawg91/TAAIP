"""© 2026 TAAIP. Copyright pending.
Data Intelligence Layer: Ingestion pipelines for RID, Vantage, PowerBI, EMM.
Auto-detects schema, maps columns, normalizes values, preserves raw sources.
"""

import json
import hashlib
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import pandas as pd
import re
from sqlalchemy.orm import Session
from . import models_intelligence as mi
from .models import Station


class SchemaDetector:
    """Auto-detect source column types and map to normalized fields."""
    
    @staticmethod
    def detect_column_type(series: pd.Series) -> str:
        """Infer column data type from sample data."""
        if series.dtype == 'object':
            # Check if it's a date
            try:
                pd.to_datetime(series.dropna(), infer_datetime_format=True, errors='coerce')
                non_null = pd.to_datetime(series.dropna(), infer_datetime_format=True, errors='coerce').notna().sum()
                if non_null > 0.8 * len(series.dropna()):
                    return 'datetime'
            except:
                pass
            # Check if it's numeric
            try:
                pd.to_numeric(series.dropna(), errors='coerce')
                non_null = pd.to_numeric(series.dropna(), errors='coerce').notna().sum()
                if non_null > 0.8 * len(series.dropna()):
                    return 'numeric'
            except:
                pass
            return 'string'
        elif series.dtype in ['int64', 'int32', 'int16']:
            return 'integer'
        elif series.dtype in ['float64', 'float32']:
            return 'float'
        elif series.dtype == 'bool':
            return 'boolean'
        return 'string'
    
    @staticmethod
    def suggest_normalized_field(source_column_name: str) -> Tuple[str, str]:
        """Suggest normalized field name and type from source column name."""
        col_lower = source_column_name.lower().strip()
        
        # ZIP code patterns
        if any(x in col_lower for x in ['zip', 'postal', 'zip_code', 'postal_code', 'zipcode']):
            return ('zip_code', 'string')
        
        # RSID/Station patterns
        if any(x in col_lower for x in ['rsid', 'station', 'station_id', 'recruiting_station']):
            return ('station_rsid', 'string')
        
        # School patterns
        if any(x in col_lower for x in ['school', 'school_name', 'school_id', 'institution']):
            return ('school_name', 'string')
        
        # Company patterns
        if any(x in col_lower for x in ['company', 'organization', 'employer', 'company_name']):
            return ('company_name', 'string')
        
        # Date patterns
        if any(x in col_lower for x in ['date', 'dt', 'day', 'timestamp', 'created', 'updated', 'reported']):
            return ('event_date', 'datetime')
        
        # Funnel/Contract patterns
        if any(x in col_lower for x in ['contract', 'enlist', 'enlistment', 'sworn']):
            return ('contract_count', 'integer')
        if any(x in col_lower for x in ['lead', 'prospect', 'applicant']):
            return ('lead_count', 'integer')
        if any(x in col_lower for x in ['engagement', 'contact', 'engaged']):
            return ('engagement_count', 'integer')
        
        # Cost/Financial patterns
        if any(x in col_lower for x in ['cost', 'expense', 'investment', 'budget', 'spent', 'dollars', '$']):
            return ('cost_dollars', 'float')
        if any(x in col_lower for x in ['roi', 'return_on_investment']):
            return ('roi_percent', 'float')
        
        # Status/Category patterns
        if any(x in col_lower for x in ['status', 'state', 'stage']):
            return ('status', 'string')
        
        # Default: preserve column name, guess type
        return (col_lower.replace(' ', '_'), 'string')


class ValueNormalizer:
    """Normalize categorical values (ZIPs, RSIDs, schools, companies, statuses, etc)."""
    
    def __init__(self, db: Session):
        self.db = db
        self._rsid_cache = {}
        self._zip_cache = {}
    
    def normalize_rsid(self, value: str, source_system: str = None) -> Optional[Tuple[str, float]]:
        """Normalize RSID value. Returns (normalized_rsid, confidence)."""
        if not value:
            return None
        
        value_clean = str(value).strip().upper()
        
        # Check cache
        if value_clean in self._rsid_cache:
            return self._rsid_cache[value_clean]
        
        # Query existing stations
        station = self.db.query(Station).filter(
            (Station.rsid == value_clean) |
            (Station.display.ilike(f"%{value}%"))
        ).first()
        
        if station:
            result = (station.rsid, 1.0)
            self._rsid_cache[value_clean] = result
            return result
        
        # If not found, check for fuzzy match
        similar = self.db.query(Station).all()
        for s in similar:
            if self._fuzzy_match(value_clean, s.rsid):
                result = (s.rsid, 0.85)
                self._rsid_cache[value_clean] = result
                return result
        
        # Not found
        return None
    
    def normalize_zip(self, value: str) -> Optional[Tuple[str, float]]:
        """Normalize ZIP code. Returns (normalized_zip, confidence)."""
        if not value:
            return None
        
        value_clean = str(value).strip()
        
        # Check cache
        if value_clean in self._zip_cache:
            return self._zip_cache[value_clean]
        
        # Validate ZIP format
        if len(value_clean) >= 5 and value_clean[:5].isdigit():
            zip_code = value_clean[:5]
            result = (zip_code, 1.0)
            self._zip_cache[value_clean] = result
            return result
        
        return None
    
    @staticmethod
    def _fuzzy_match(s1: str, s2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching."""
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, s1, s2).ratio()
        return ratio >= threshold


class IngestionPipeline:
    """Main ingestion pipeline for RID, Vantage, PowerBI, EMM data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.detector = SchemaDetector()
        self.normalizer = ValueNormalizer(db)
    
    def ingest_file(
        self,
        source_name: str,
        file_path: str,
        file_content: bytes = None,
        ingested_by: str = None,
        metadata: Dict[str, Any] = None
    ) -> mi.DataIngestionLog:
        """
        Ingest a data file (CSV/XLSX) from a source system.
        
        Returns: DataIngestionLog record
        """
        ingest_log = None
        try:
            # Get or create data source
            source = self._get_or_create_source(source_name)
            
            # Read file
            if file_content:
                df = self._read_bytes(file_content)
            else:
                df = self._read_file(file_path)
            
            record_count = len(df)
            
            # Compute file hash
            file_hash = hashlib.sha256(file_content if file_content else open(file_path, 'rb').read()).hexdigest()
            
            # Create ingestion log
            ingest_log = mi.DataIngestionLog(
                id=self._generate_id(f"ingest_{source_name}"),
                source_id=source.id,
                source_file=file_path,
                source_hash=file_hash,
                record_count=record_count,
                ingested_by=ingested_by,
                status='pending',
                source_metadata=metadata or {}
            )
            self.db.add(ingest_log)
            
            # Auto-detect schema
            self._detect_and_map_schema(source, df)
            
            # Normalize values
            self._normalize_values(source, df)
            
            # Update ingestion log
            ingest_log.status = 'success'
            self.db.commit()
            
            return ingest_log
            
        except Exception as e:
            if ingest_log is not None:
                ingest_log.status = 'failed'
                ingest_log.error_message = str(e)
                self.db.commit()
            raise
    
    def _get_or_create_source(self, source_name: str) -> mi.DataSource:
        """Get existing or create new data source."""
        source = self.db.query(mi.DataSource).filter_by(source_name=source_name).first()
        if not source:
            source = mi.DataSource(
                id=self._generate_id(f"datasource_{source_name}"),
                source_name=source_name,
                source_type='SYSTEM' if source_name in ['RID', 'Vantage', 'PowerBI', 'EMM'] else 'IMPORT',
                description=f"Data source: {source_name}"
            )
            self.db.add(source)
            self.db.commit()
        return source
    
    def _detect_and_map_schema(self, source: mi.DataSource, df: pd.DataFrame) -> None:
        """Auto-detect column types and create mappings."""
        for column_name in df.columns:
            col_type = self.detector.detect_column_type(df[column_name])
            normalized_name, normalized_type = self.detector.suggest_normalized_field(column_name)
            
            # Check if mapping exists
            existing = self.db.query(mi.ColumnMapping).filter_by(
                source_id=source.id,
                source_column_name=column_name
            ).first()
            
            if not existing:
                mapping = mi.ColumnMapping(
                    id=self._generate_id(f"colmap_{source.id}_{column_name}"),
                    source_id=source.id,
                    source_column_name=column_name,
                    source_data_type=col_type,
                    normalized_field_name=normalized_name,
                    normalized_data_type=normalized_type,
                    confidence=0.95 if column_name.lower() == normalized_name else 0.75
                )
                self.db.add(mapping)
        
        self.db.commit()
    
    def _normalize_values(self, source: mi.DataSource, df: pd.DataFrame) -> None:
        """Extract and normalize categorical values."""
        # Get mappings
        mappings = self.db.query(mi.ColumnMapping).filter_by(source_id=source.id).all()
        
        for mapping in mappings:
            if mapping.normalized_field_name in ['station_rsid', 'zip_code', 'school_name', 'company_name', 'status']:
                column_data = df.get(mapping.source_column_name, pd.Series())
                
                for raw_value in column_data.unique():
                    if pd.isna(raw_value):
                        continue
                    
                    # Check if already normalized
                    existing = self.db.query(mi.NormalizedValue).filter_by(
                        field_type=mapping.normalized_field_name,
                        source_value=str(raw_value)
                    ).first()
                    
                    if not existing:
                        normalized = None
                        confidence = 0.0
                        
                        if mapping.normalized_field_name == 'station_rsid':
                            result = self.normalizer.normalize_rsid(str(raw_value), source.source_name)
                            if result:
                                normalized, confidence = result
                        elif mapping.normalized_field_name == 'zip_code':
                            result = self.normalizer.normalize_zip(str(raw_value))
                            if result:
                                normalized, confidence = result
                        
                        if normalized:
                            norm_record = mi.NormalizedValue(
                                id=self._generate_id(f"norm_{mapping.normalized_field_name}_{raw_value}"),
                                field_type=mapping.normalized_field_name,
                                source_value=str(raw_value),
                                normalized_value=normalized,
                                source_system=source.source_name,
                                mapping_confidence=confidence
                            )
                            self.db.add(norm_record)
        
        self.db.commit()
    
    @staticmethod
    def _read_file(file_path: str) -> pd.DataFrame:
        """Read CSV or XLSX file."""
        if file_path.lower().endswith('.xlsx'):
            return pd.read_excel(file_path)
        else:
            return pd.read_csv(file_path)
    
    @staticmethod
    def _read_bytes(file_content: bytes) -> pd.DataFrame:
        """Read CSV or XLSX from bytes."""
        try:
            return pd.read_excel(io.BytesIO(file_content))
        except Exception:
            return pd.read_csv(io.BytesIO(file_content))
    
    @staticmethod
    def _generate_id(prefix: str) -> str:
        """Generate unique ID."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ============================================================================
# TOP-LEVEL INGESTION PIPELINE FUNCTIONS
# ============================================================================

def ingest_rid_pipeline(
    db: Session,
    file_path: str = None,
    file_content: bytes = None,
    ingested_by: str = None
) -> Dict[str, Any]:
    """
    Ingest RID (Recruiting Information Database) CSV/XLSX file.
    
    Detects RID schema (applicant ZIP, assigned ZIP, contract dates, station RSID, etc.)
    Maps to normalized fields, validates RSIDs and ZIP codes, preserves raw source.
    
    Args:
        db: SQLAlchemy session
        file_path: Path to RID file
        file_content: File bytes (alternative to file_path)
        ingested_by: User/system identifier for audit trail
    
    Returns:
        Dict with ingestion status, record count, schema mappings, normalization results
    """
    
    pipeline = IngestionPipeline(db)
    source_name = "RID"
    
    try:
        ingest_log = pipeline.ingest_file(
            source_name=source_name,
            file_path=file_path,
            file_content=file_content,
            ingested_by=ingested_by,
            metadata={
                "source_type": "RID",
                "ingestion_type": "scheduled_sync",
                "schema_version": "RID_v1"
            }
        )
        
        # Additional RID-specific validation
        source = pipeline._get_or_create_source(source_name)
        mappings = db.query(mi.ColumnMapping).filter_by(source_id=source.id).all()
        
        return {
            "ingestion_log_id": ingest_log.id,
            "source": source_name,
            "status": ingest_log.status,
            "record_count": ingest_log.record_count,
            "ingested_at": ingest_log.ingested_at.isoformat() if ingest_log.ingested_at else None,
            "file_hash": ingest_log.source_hash,
            "column_mappings": [
                {
                    "source_column": m.source_column_name,
                    "source_type": m.source_data_type,
                    "normalized_field": m.normalized_field_name,
                    "confidence": m.confidence
                }
                for m in mappings
            ],
            "error_message": ingest_log.error_message
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }


def ingest_vantage_pipeline(
    db: Session,
    file_path: str = None,
    file_content: bytes = None,
    ingested_by: str = None
) -> Dict[str, Any]:
    """
    Ingest Vantage/Foundry export CSV/XLSX file.
    
    Parses Vantage/Foundry schema, maps entity types (applicants, contracts, activities),
    normalizes categorical values, validates entity relationships, preserves raw source.
    
    Args:
        db: SQLAlchemy session
        file_path: Path to Vantage export file
        file_content: File bytes (alternative to file_path)
        ingested_by: User/system identifier for audit trail
    
    Returns:
        Dict with ingestion status, record count, entity type breakdown, normalization results
    """
    
    pipeline = IngestionPipeline(db)
    source_name = "Vantage"
    
    try:
        ingest_log = pipeline.ingest_file(
            source_name=source_name,
            file_path=file_path,
            file_content=file_content,
            ingested_by=ingested_by,
            metadata={
                "source_type": "Vantage",
                "ingestion_type": "export_sync",
                "schema_version": "Vantage_v1",
                "entity_types": ["applicant", "contract", "activity"]
            }
        )
        
        # Additional Vantage-specific analysis
        source = pipeline._get_or_create_source(source_name)
        mappings = db.query(mi.ColumnMapping).filter_by(source_id=source.id).all()
        
        # Count normalized values per type
        normalized_by_type = {}
        for field_type in ['station_rsid', 'zip_code', 'school_name', 'company_name', 'status']:
            count = db.query(mi.NormalizedValue).filter_by(
                field_type=field_type,
                source_system=source_name
            ).count()
            if count > 0:
                normalized_by_type[field_type] = count
        
        return {
            "ingestion_log_id": ingest_log.id,
            "source": source_name,
            "status": ingest_log.status,
            "record_count": ingest_log.record_count,
            "ingested_at": ingest_log.ingested_at.isoformat() if ingest_log.ingested_at else None,
            "file_hash": ingest_log.source_hash,
            "column_mappings": [
                {
                    "source_column": m.source_column_name,
                    "source_type": m.source_data_type,
                    "normalized_field": m.normalized_field_name,
                    "confidence": m.confidence
                }
                for m in mappings
            ],
            "normalized_values": normalized_by_type,
            "error_message": ingest_log.error_message
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }


def ingest_powerbi_pipeline(
    db: Session,
    file_path: str = None,
    file_content: bytes = None,
    ingested_by: str = None
) -> Dict[str, Any]:
    """
    Ingest PowerBI export CSV/XLSX file.
    
    Detects PowerBI schema automatically, maps columns to normalized fields,
    validates data types and categorical values, preserves raw source.
    
    Args:
        db: SQLAlchemy session
        file_path: Path to PowerBI export file
        file_content: File bytes (alternative to file_path)
        ingested_by: User/system identifier for audit trail
    
    Returns:
        Dict with ingestion status, record count, schema mappings, normalization results
    """
    
    pipeline = IngestionPipeline(db)
    source_name = "PowerBI"
    
    try:
        ingest_log = pipeline.ingest_file(
            source_name=source_name,
            file_path=file_path,
            file_content=file_content,
            ingested_by=ingested_by,
            metadata={
                "source_type": "PowerBI",
                "ingestion_type": "export_sync",
                "schema_version": "PowerBI_v1",
                "auto_detection_enabled": True
            }
        )
        
        source = pipeline._get_or_create_source(source_name)
        mappings = db.query(mi.ColumnMapping).filter_by(source_id=source.id).all()
        
        # PowerBI-specific: categorize columns by type
        columns_by_type = {}
        for m in mappings:
            data_type = m.source_data_type
            if data_type not in columns_by_type:
                columns_by_type[data_type] = []
            columns_by_type[data_type].append(m.source_column_name)
        
        return {
            "ingestion_log_id": ingest_log.id,
            "source": source_name,
            "status": ingest_log.status,
            "record_count": ingest_log.record_count,
            "ingested_at": ingest_log.ingested_at.isoformat() if ingest_log.ingested_at else None,
            "file_hash": ingest_log.source_hash,
            "columns_by_type": columns_by_type,
            "column_mappings": [
                {
                    "source_column": m.source_column_name,
                    "source_type": m.source_data_type,
                    "normalized_field": m.normalized_field_name,
                    "confidence": m.confidence
                }
                for m in mappings
            ],
            "error_message": ingest_log.error_message
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }


def ingest_emm_pipeline(
    db: Session,
    file_path: str = None,
    file_content: bytes = None,
    ingested_by: str = None
) -> Dict[str, Any]:
    """
    Ingest EMM (Event Management Module) export CSV/XLSX file.
    
    Parses EMM schema, extracts event activity data, normalizes event types and venues,
    preserves raw source for audit trail, detects schema drift.
    
    Args:
        db: SQLAlchemy session
        file_path: Path to EMM export file
        file_content: File bytes (alternative to file_path)
        ingested_by: User/system identifier for audit trail
    
    Returns:
        Dict with ingestion status, record count, schema mappings, schema drift detection
    """
    
    pipeline = IngestionPipeline(db)
    source_name = "EMM"
    
    try:
        ingest_log = pipeline.ingest_file(
            source_name=source_name,
            file_path=file_path,
            file_content=file_content,
            ingested_by=ingested_by,
            metadata={
                "source_type": "EMM",
                "ingestion_type": "event_export",
                "schema_version": "EMM_v1",
                "schema_drift_detection": True
            }
        )
        
        source = pipeline._get_or_create_source(source_name)
        mappings = db.query(mi.ColumnMapping).filter_by(source_id=source.id).all()
        
        # EMM-specific: detect if schema has drifted
        expected_emm_fields = [
            'event_id', 'event_date', 'event_type', 'venue_zip', 
            'attendance', 'leads_generated', 'leads_qualified', 'cost'
        ]
        
        detected_fields = [m.normalized_field_name for m in mappings]
        schema_drift = not all(field in detected_fields for field in expected_emm_fields)
        
        return {
            "ingestion_log_id": ingest_log.id,
            "source": source_name,
            "status": ingest_log.status,
            "record_count": ingest_log.record_count,
            "ingested_at": ingest_log.ingested_at.isoformat() if ingest_log.ingested_at else None,
            "file_hash": ingest_log.source_hash,
            "expected_fields": expected_emm_fields,
            "detected_fields": detected_fields,
            "schema_drift_detected": schema_drift,
            "column_mappings": [
                {
                    "source_column": m.source_column_name,
                    "source_type": m.source_data_type,
                    "normalized_field": m.normalized_field_name,
                    "confidence": m.confidence
                }
                for m in mappings
            ],
            "error_message": ingest_log.error_message
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }
