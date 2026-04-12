from fastapi import APIRouter
from services.api.app.routers.asset_recommendations import asset_recommendations as get_asset_recommendations
from services.api.app.data.commander_intent_store import get_current_intent
from services.api.app.data.mission_alignment_registry import MISSION_ALIGNMENT_TEMPLATE

router = APIRouter()


def score_alignment(asset, intent):
    score = 0
    reasons = []

    loes = intent.get("merged", {}).get("loes", [])
    priorities = intent.get("merged", {}).get("priorities", [])
    markets = intent.get("merged", {}).get("focus_markets", [])
    populations = intent.get("merged", {}).get("target_population", [])

    supports = asset.get("supports", [])

    # LOE alignment
    for loe in loes:
        if any(loe.lower() in s.lower() for s in supports):
            score += 20
            reasons.append(f"Supports LOE: {loe}")

    # Priority alignment
    for p in priorities:
        if any(p.lower() in s.lower() for s in supports):
            score += 15
            reasons.append(f"Supports Priority: {p}")

    # Market alignment
    if markets:
        score += 10
        reasons.append("Aligned to focus market")

    # Population alignment
    if populations:
        score += 10
        reasons.append("Aligned to target population")

    return score, reasons


@router.get("/mission_alignment")
def get_mission_alignment():
    # get_asset_recommendations is expected to return a dict with a
    # `recommendations` list of assets
    recs = get_asset_recommendations()
    intent = get_current_intent()

    aligned = []

    for r in recs.get("recommendations", []):
        score, reasons = score_alignment(r, intent)

        aligned.append({
            **r,
            "alignment_score": score,
            "alignment_reasons": reasons
        })

    # sort highest first
    aligned = sorted(aligned, key=lambda x: x["alignment_score"], reverse=True)

    return {
        "aligned_recommendations": aligned
    }


@router.get("/mission_alignment/template")
def get_mission_alignment_template():
    """Return the canonical mission-alignment input template."""
    return MISSION_ALIGNMENT_TEMPLATE


@router.post("/mission_alignment/analyze_stub")
def analyze_stub(payload: dict):
    """Lightweight analyzer stub that accepts a subset of the template
    and returns a simple assessment. This is intentionally non-AI and
    only checks for presence of key fields to bootstrap ingestion tests.
    """
    assessment = {
        "has_intent": bool(payload.get("commander_intent")),
        "has_loes": bool(payload.get("loes")),
        "has_priorities": bool(payload.get("priorities")),
        "has_targeting_guidance": bool(payload.get("targeting_guidance")),
        "has_school_guidance": bool(payload.get("school_recruiting_guidance")),
    }

    return {
        "received": payload,
        "assessment": assessment,
        "status": "stub_ready",
    }
