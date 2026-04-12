from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class ExtractedAlignment(BaseModel):
    commander_intent: Optional[str] = ""
    mission_statement: Optional[str] = ""
    priorities: List[str] = Field(default_factory=list)
    loes: List[str] = Field(default_factory=list)
    targeting_guidance: List[str] = Field(default_factory=list)
    school_recruiting_guidance: List[str] = Field(default_factory=list)


class Extraction(BaseModel):
    document_type: Optional[str] = ""
    extracted_alignment: ExtractedAlignment = Field(default_factory=ExtractedAlignment)


class BuildRequest(BaseModel):
    filename: Optional[str] = ""
    stored_path: Optional[str] = ""
    extraction: Extraction = Field(default_factory=Extraction)


@router.post("/mission_bundle_pipeline/build")
def build_mission_bundle(payload: BuildRequest):
    align = payload.extraction.extracted_alignment

    mission_bundle = {
        "unit_mission": align.mission_statement or "",
        "commander_intent": align.commander_intent or "",
        "priority_markets": align.priorities or [],
        "loes": align.loes or [],
        "targeting_focus": align.targeting_guidance or [],
        "school_focus": align.school_recruiting_guidance or [],
    }

    return {
        "filename": payload.filename or "",
        "mission_bundle": mission_bundle,
        "status": "mission_bundle_ready",
    }
