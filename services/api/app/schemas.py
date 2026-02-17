from pydantic import BaseModel
from typing import List, Optional


class ZipCoverageItem(BaseModel):
    zip_code: str
    market_category: str
    source_file: Optional[str]

    class Config:
        orm_mode = True


class StationZipCoverageResponse(BaseModel):
    station_rsid: str
    station_display: Optional[str]
    zip_coverage: List[ZipCoverageItem]


class ZipToStationResponse(BaseModel):
    zip_code: str
    station_rsid: Optional[str]
    station_display: Optional[str]
    company_prefix: Optional[str]
    battalion_prefix: Optional[str]
    brigade_prefix: Optional[str]
    market_category: Optional[str]


class CoverageSummaryItem(BaseModel):
    category: str
    count: int


class CoverageSummaryResponse(BaseModel):
    scope: str
    value: str
    totals: List[CoverageSummaryItem]
