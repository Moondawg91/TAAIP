from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, database, auth, rbac, models

router = APIRouter(prefix="/api/org", tags=["org"])


@router.get("/stations/{rsid}/zip-coverage", response_model=schemas.StationZipCoverageResponse)
def station_zip_coverage(rsid: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # ensure station exists
    station = db.query(models.Station).filter(models.Station.rsid == rsid).one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # enforce RBAC: station must be within user scope
    if not rbac.is_rsid_in_scope(current_user.scope, rsid):
        raise HTTPException(status_code=403, detail="Forbidden: out of scope")

    rows = db.query(models.StationZipCoverage).filter(models.StationZipCoverage.station_rsid == rsid).all()
    zip_items = [schemas.ZipCoverageItem(zip_code=r.zip_code, market_category=r.market_category.name, source_file=r.source_file) for r in rows]
    return schemas.StationZipCoverageResponse(station_rsid=rsid, station_display=station.display, zip_coverage=zip_items)


@router.get("/zip/{zip_code}/station", response_model=schemas.ZipToStationResponse)
def zip_to_station(zip_code: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    coverage = db.query(models.StationZipCoverage).filter(models.StationZipCoverage.zip_code == zip_code).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="ZIP not found")
    station = db.query(models.Station).filter(models.Station.rsid == coverage.station_rsid).one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station for ZIP not found")

    # enforce RBAC
    if not rbac.is_rsid_in_scope(current_user.scope, station.rsid):
        raise HTTPException(status_code=403, detail="Forbidden: out of scope")

    company = db.query(models.Company).filter(models.Company.id == station.company_id).one_or_none() if station and station.company_id else None
    battalion = db.query(models.Battalion).filter(models.Battalion.id == company.battalion_id).one_or_none() if company and company.battalion_id else None
    brigade = db.query(models.Brigade).filter(models.Brigade.id == battalion.brigade_id).one_or_none() if battalion and battalion.brigade_id else None

    return schemas.ZipToStationResponse(
        zip_code=coverage.zip_code,
        station_rsid=station.rsid if station else None,
        station_display=station.display if station else None,
        company_prefix=company.company_prefix if company else None,
        battalion_prefix=battalion.battalion_prefix if battalion else None,
        brigade_prefix=brigade.brigade_prefix if brigade else None,
        market_category=coverage.market_category.name if coverage else None,
    )


@router.get("/coverage/summary", response_model=schemas.CoverageSummaryResponse)
def coverage_summary(scope: str = "USAREC", value: str = None, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Build base query
    q = db.query(models.StationZipCoverage.market_category, db.query(models.StationZipCoverage).filter(models.StationZipCoverage.market_category != None).count())
    # We will instead aggregate properly using SQLAlchemy
    from sqlalchemy import func
    q2 = db.query(models.StationZipCoverage.market_category, func.count(models.StationZipCoverage.id)).group_by(models.StationZipCoverage.market_category)

    # apply optional scope/value filter from request
    if scope and scope != 'USAREC' and value:
        # restrict q2 by provided scope/value
        q_filtered = q2
        # map provided scope/value to station prefix logic
        if scope == 'STN':
            q_filtered = q_filtered.filter(models.StationZipCoverage.station_rsid == value)
        elif scope == 'CO':
            stations = db.query(models.Station.rsid).join(models.Company, models.Station.company_id == models.Company.id).filter(models.Company.company_prefix == value).subquery()
            q_filtered = q_filtered.filter(models.StationZipCoverage.station_rsid.in_(stations))
        elif scope == 'BN':
            stations = db.query(models.Station.rsid).join(models.Company, models.Station.company_id == models.Company.id).join(models.Battalion, models.Company.battalion_id == models.Battalion.id).filter(models.Battalion.battalion_prefix == value).subquery()
            q_filtered = q_filtered.filter(models.StationZipCoverage.station_rsid.in_(stations))
        elif scope == 'BDE':
            stations = db.query(models.Station.rsid).join(models.Company, models.Station.company_id == models.Company.id).join(models.Battalion, models.Company.battalion_id == models.Battalion.id).join(models.Brigade, models.Battalion.brigade_id == models.Brigade.id).filter(models.Brigade.brigade_prefix == value).subquery()
            q_filtered = q_filtered.filter(models.StationZipCoverage.station_rsid.in_(stations))
        else:
            q_filtered = q2
    else:
        q_filtered = q2

    # enforce user's own scope
    q_filtered = rbac.apply_scope_filter(q_filtered, models.StationZipCoverage, current_user.scope)

    rows = q_filtered.all()
    totals = [schemas.CoverageSummaryItem(category=r[0].name if hasattr(r[0], 'name') else str(r[0]), count=r[1]) for r in rows]
    return schemas.CoverageSummaryResponse(scope=scope, value=value or "ALL", totals=totals)
