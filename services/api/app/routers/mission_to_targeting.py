"""Lightweight bridge: convert mission alignment guidance into targeting recommendations.
This file is intentionally self-contained: no DB, no AI, no persistence.
"""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class MissionAlignment(BaseModel):
    commander_intent: Optional[str] = ""
    mission_statement: Optional[str] = ""
    priorities: Optional[List[str]] = []
    loes: Optional[List[str]] = []
    targeting_guidance: Optional[List[str]] = []
    school_recruiting_guidance: Optional[List[str]] = []


class RecommendRequest(BaseModel):
    mission_alignment: MissionAlignment


@router.post("/mission_to_targeting/recommend_stub")
def recommend_stub(payload: RecommendRequest):
    ma = payload.mission_alignment

    markets = set()
    school_segments = set()
    engagement_types = set()
    targeting_notes = set()

    # Normalize text snippets for matching
    commander = (ma.commander_intent or "").lower()
    priorities = [p.lower() for p in (ma.priorities or [])]
    loes = [l.lower() for l in (ma.loes or [])]
    targeting = [t.lower() for t in (ma.targeting_guidance or [])]
    school_guidance = [s.lower() for s in (ma.school_recruiting_guidance or [])]

    # Rule: senior mentions -> add senior segments/markets
    if "senior" in commander or any("senior" in p for p in priorities):
        school_segments.add("high_school_seniors")
        markets.add("senior_market")

    # Rule: LOE mentions School Recruiting -> add school engagement
    if any("school recruiting" in l for l in loes):
        engagement_types.add("school_engagement")

    # Rule: targeting guidance mentions high school -> add list targeting note
    if any("high school" in t for t in targeting):
        targeting_notes.add("school_list_targeting")

    # Rule: school recruiting guidance mentions engagement -> add increase visits note
    if any("engagement" in s for s in school_guidance):
        targeting_notes.add("increase_school_visits")

    recommended_focus = {
        "markets": sorted(list(markets)),
        "school_segments": sorted(list(school_segments)),
        "engagement_types": sorted(list(engagement_types)),
        "targeting_notes": sorted(list(targeting_notes)),
    }

    return {
        "recommended_focus": recommended_focus,
        "status": "targeting_stub_ready",
    }
