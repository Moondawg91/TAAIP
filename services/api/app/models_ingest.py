from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import enum

from .models import Base


class TransformRecipe(Base):
    __tablename__ = "transform_recipes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    # steps stored as JSON list of step dicts
    steps = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IngestedFile(Base):
    __tablename__ = "ingested_files"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    source = Column(String)
    uploaded_by = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("ingested_files.id"))
    recipe_id = Column(Integer, ForeignKey("transform_recipes.id"), nullable=True)
    status = Column(String, default="pending")
    report = Column(JSON)
    run_at = Column(DateTime(timezone=True), server_default=func.now())
