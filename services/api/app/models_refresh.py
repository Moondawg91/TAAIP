from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from .models import Base


class RefreshSource(Base):
    __tablename__ = "refresh_sources"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    canonical_target = Column(String)  # logical target name
    file_types = Column(String, default='csv,xlsx')
    required_merge_keys = Column(JSON, nullable=True)  # list of key column names
    mapping_profile = Column(JSON, nullable=True)
    owner = Column(String, nullable=True)
    default_mode = Column(String, default='replace')
    trusted = Column(String, default='false')
    auto_commit = Column(String, default='false')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefreshJob(Base):
    __tablename__ = "refresh_jobs"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("refresh_sources.id"))
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    checksum = Column(String, nullable=True)
    uploaded_by = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default='uploaded')
    row_count = Column(Integer, default=0)
    profile = Column(JSON, nullable=True)


class RefreshStagingRow(Base):
    __tablename__ = "refresh_staging_rows"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("refresh_jobs.id"))
    row_number = Column(Integer)
    row_json = Column(JSON)


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("refresh_sources.id"))
    version = Column(String, nullable=False)
    checksum = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    row_count = Column(Integer, default=0)
    notes = Column(Text)


class RefreshDatasetRow(Base):
    __tablename__ = "refresh_dataset_rows"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("refresh_sources.id"))
    version_id = Column(Integer, ForeignKey("dataset_versions.id"))
    row_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefreshHistory(Base):
    __tablename__ = "refresh_history"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("refresh_jobs.id"))
    version_id = Column(Integer, ForeignKey("dataset_versions.id"))
    mode = Column(String)
    status = Column(String)
    applied_by = Column(String)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    row_count_before = Column(Integer)
    row_count_after = Column(Integer)
    notes = Column(Text)


class DatasetActive(Base):
    __tablename__ = "dataset_active"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("refresh_sources.id"), unique=True)
    version_id = Column(Integer, ForeignKey("dataset_versions.id"))
    bound_at = Column(DateTime(timezone=True), server_default=func.now())
    bound_by = Column(String)
