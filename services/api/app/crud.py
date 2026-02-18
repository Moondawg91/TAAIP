from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models
from typing import Tuple, List, Dict
import pandas as pd
import re


def upsert_command(db: Session, command_code: str, display: str):
    obj = db.query(models.Command).filter_by(command=command_code).one_or_none()
    if obj:
        obj.display = display
    else:
        obj = models.Command(command=command_code, display=display)
        db.add(obj)
    db.commit()
    return obj


def upsert_brigade(db: Session, brigade_prefix: str, display: str, command_obj):
    obj = db.query(models.Brigade).filter_by(brigade_prefix=brigade_prefix, command_id=command_obj.id).one_or_none()
    if obj:
        obj.display = display
    else:
        obj = models.Brigade(brigade_prefix=brigade_prefix, display=display, command_id=command_obj.id)
        db.add(obj)
    db.commit()
    return obj


def import_rsids_from_excel(db: Session, path: str) -> Dict:
    df = pd.read_excel(path, engine="openpyxl")
    report = {"rows": 0, "created": 0, "updated": 0, "errors": []}
    for _, row in df.iterrows():
        report["rows"] += 1
        try:
            cmd = str(row.get("COMMAND", "")).strip()
            bde = str(row.get("BRIGADE", "")).strip()
            bn = str(row.get("BATTALION", "")).strip()
            co = str(row.get("COMPANY", "")).strip()
            stn = str(row.get("STATION", "")).strip() or row.get("STN") or row.get("STN_NAME")
            stn = str(stn).strip()
            if not stn:
                report["errors"].append((report["rows"], "missing station"))
                continue
            # parse RSID and station name
            parts = stn.split(" - ")
            rsid = parts[0].strip()
            station_display = parts[1].strip() if len(parts) > 1 else ""
            # derive prefixes
            brigade_prefix = rsid[0:1]
            battalion_prefix = rsid[0:2]
            company_prefix = rsid[0:3]

            # upsert command
            cmd_obj = db.query(models.Command).filter_by(command=cmd).one_or_none()
            if not cmd_obj:
                cmd_obj = models.Command(command=cmd, display=cmd)
                db.add(cmd_obj)
                db.commit()
                report["created"] += 1

            # upsert brigade
            bde_obj = db.query(models.Brigade).filter_by(brigade_prefix=brigade_prefix, command_id=cmd_obj.id).one_or_none()
            if not bde_obj:
                bde_obj = models.Brigade(brigade_prefix=brigade_prefix, display=bde, command_id=cmd_obj.id)
                db.add(bde_obj)
                db.commit()

            # upsert battalion
            bn_obj = db.query(models.Battalion).filter_by(battalion_prefix=battalion_prefix, brigade_id=bde_obj.id).one_or_none()
            if not bn_obj:
                bn_obj = models.Battalion(battalion_prefix=battalion_prefix, display=bn, brigade_id=bde_obj.id)
                db.add(bn_obj)
                db.commit()

            # upsert company
            co_obj = db.query(models.Company).filter_by(company_prefix=company_prefix, battalion_id=bn_obj.id).one_or_none()
            if not co_obj:
                co_obj = models.Company(company_prefix=company_prefix, display=co, battalion_id=bn_obj.id)
                db.add(co_obj)
                db.commit()

            # upsert station
            st_obj = db.query(models.Station).filter_by(rsid=rsid).one_or_none()
            if st_obj:
                st_obj.display = station_display
                report["updated"] += 1
            else:
                st_obj = models.Station(rsid=rsid, display=station_display, company_id=co_obj.id)
                db.add(st_obj)
                db.commit()
                report["created"] += 1

            # validation checks (prefix align)
            # verify that company_prefix matches provided CO label if possible (best-effort)
            # skipping complex name checks
        except Exception as e:
            report["errors"].append((report["rows"], str(e)))
    return report


def import_zip_coverage_from_excel(db: Session, path: str, source_file: str = None) -> Dict:
    df = pd.read_excel(path, engine="openpyxl")
    report = {"rows": 0, "created": 0, "updated": 0, "invalid_station": 0, "invalid_zip": 0, "invalid_category": 0, "errors": []}
    allowed = {"MK", "MW", "MO", "SU"}
    for _, row in df.iterrows():
        report["rows"] += 1
        try:
            stn = str(row.get("Recruiting STN", "")).strip()
            category = str(row.get("Category", "")).strip()
            zip_code = str(row.get("ZIP", "")).strip()
            # parse station RSID
            parts = stn.split(" - ")
            if len(parts) < 1 or not parts[0]:
                report["invalid_station"] += 1
                report["errors"].append((report["rows"], "invalid station format"))
                continue
            rsid = parts[0].strip()
            # validate station exists
            st_obj = db.query(models.Station).filter_by(rsid=rsid).one_or_none()
            if not st_obj:
                report["invalid_station"] += 1
                report["errors"].append((report["rows"], f"station {rsid} not found"))
                continue
            # validate zip
            if not re.fullmatch(r"\d{5}", zip_code):
                report["invalid_zip"] += 1
                report["errors"].append((report["rows"], f"invalid ZIP {zip_code}"))
                continue
            # validate category
            cat = category if category in allowed else "UNK"
            if cat == "UNK":
                report["invalid_category"] += 1

            # upsert
            obj = db.query(models.StationZipCoverage).filter_by(station_rsid=rsid, zip_code=zip_code).one_or_none()
            if obj:
                obj.market_category = getattr(models.MarketCategory, cat)
                obj.source_file = source_file
                report["updated"] += 1
            else:
                obj = models.StationZipCoverage(station_rsid=rsid, zip_code=zip_code, market_category=getattr(models.MarketCategory, cat), source_file=source_file)
                db.add(obj)
                report["created"] += 1
            db.commit()
        except Exception as e:
            report["errors"].append((report["rows"], str(e)))
    return report


def get_station_zip_coverage(db: Session, rsid: str):
    # return a query so callers can apply additional filters (e.g., RBAC)
    return db.query(models.StationZipCoverage).filter(models.StationZipCoverage.station_rsid == rsid)


def get_zip_to_station(db: Session, zip_code: str):
    # return a query for the coverage row so caller can enforce RBAC before materializing
    return db.query(models.StationZipCoverage).filter(models.StationZipCoverage.zip_code == zip_code)


def coverage_summary_query(db: Session):
    # return a query grouped by market_category so callers can apply RBAC filters
    return db.query(models.StationZipCoverage.market_category, func.count(models.StationZipCoverage.id)).group_by(models.StationZipCoverage.market_category)
