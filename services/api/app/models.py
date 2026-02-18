from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class MarketCategory(enum.Enum):
    MK = "MK"
    MW = "MW"
    MO = "MO"
    SU = "SU"
    UNK = "UNK"


class Command(Base):
    __tablename__ = "commands"
    id = Column(Integer, primary_key=True)
    command = Column(String, unique=True, nullable=False)
    display = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Brigade(Base):
    __tablename__ = "brigades"
    id = Column(Integer, primary_key=True)
    brigade_prefix = Column(String(1), nullable=False)
    display = Column(String)
    command_id = Column(Integer, ForeignKey("commands.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('brigade_prefix', 'command_id', name='uq_brigade_cmd'),)


class Battalion(Base):
    __tablename__ = "battalions"
    id = Column(Integer, primary_key=True)
    battalion_prefix = Column(String(2), nullable=False)
    display = Column(String)
    brigade_id = Column(Integer, ForeignKey("brigades.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('battalion_prefix', 'brigade_id', name='uq_battalion_bde'),)


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    company_prefix = Column(String(3), nullable=False)
    display = Column(String)
    battalion_id = Column(Integer, ForeignKey("battalions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('company_prefix', 'battalion_id', name='uq_company_bn'),)


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True)
    rsid = Column(String(4), nullable=False, unique=True)
    display = Column(String)
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StationZipCoverage(Base):
    __tablename__ = "station_zip_coverage"
    id = Column(Integer, primary_key=True)
    station_rsid = Column(String(4), ForeignKey("stations.rsid"), nullable=False)
    zip_code = Column(String(5), nullable=False)
    market_category = Column(Enum(MarketCategory), nullable=False, server_default=MarketCategory.UNK.name)
    source_file = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('station_rsid', 'zip_code', name='uq_station_zip'),)


class MarketCategoryWeights(Base):
    __tablename__ = "market_category_weights"
    id = Column(Integer, primary_key=True)
    category = Column(Enum(MarketCategory), nullable=False, unique=True)
    weight = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserRole(enum.Enum):
    USAREC = "USAREC"
    BRIGADE_420T = "BRIGADE_420T"
    BATTALION_420T = "BATTALION_420T"
    FUSION = "FUSION"
    BRIGADE_VIEW = "BRIGADE_VIEW"
    BATTALION_VIEW = "BATTALION_VIEW"
    COMPANY_CMD = "COMPANY_CMD"
    STATION_VIEW = "STATION_VIEW"
    SYSADMIN = "SYSADMIN"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    scope = Column(String, nullable=True)  # e.g., brigade_prefix, battalion_prefix, company_prefix, station_rsid, or 'USAREC'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
