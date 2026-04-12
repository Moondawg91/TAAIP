from typing import Any, Dict, List
from fastapi import APIRouter, Body

router = APIRouter()


def _collect_search_text(rec: Dict[str, Any]) -> str:
    parts: List[str] = []
    if rec.get("asset"):
        parts.append(str(rec.get("asset")))
    if rec.get("reason"):
        parts.append(str(rec.get("reason")))
    if isinstance(rec.get("supports"), list):
        parts.extend([str(s) for s in rec.get("supports") if s])
    return " ".join(parts).lower()


def score_recommendation(mission_alignment: Dict[str, Any], rec: Dict[str, Any]) -> Dict[str, Any]:
    """Score a single recommendation against mission_alignment using
    simple substring matching. Returns a dict with asset, alignment_score,
    matches and gaps.
    """
    text = _collect_search_text(rec)
    score = 0
    matches: List[str] = []
    gaps: List[str] = []

    # helpers
    def _match_any(keys: List[str]) -> List[str]:
        found: List[str] = []
        for k in keys or []:
            if not k:
                continue
            if str(k).lower() in text:
                found.append(k)
        return found

    # LOEs +30
    loes = mission_alignment.get("loes") or []
    found_loes = _match_any(loes)
    if found_loes:
        score += 30
        matches.extend([f"loe:{x}" for x in found_loes])
    else:
        gaps.extend([f"loe:{x}" for x in loes])

    # Priorities +30
    priorities = mission_alignment.get("priorities") or []
    found_prio = _match_any(priorities)
    if found_prio:
        score += 30
        matches.extend([f"priority:{x}" for x in found_prio])
    else:
        gaps.extend([f"priority:{x}" for x in priorities])

    # Targeting guidance +20
    targeting = mission_alignment.get("targeting_guidance") or []
    found_target = _match_any(targeting)
    if found_target:
        score += 20
        matches.extend([f"targeting:{x}" for x in found_target])
    else:
        gaps.extend([f"targeting:{x}" for x in targeting])

    # School recruiting guidance +20
    school = mission_alignment.get("school_recruiting_guidance") or []
    found_school = _match_any(school)
    if found_school:
        score += 20
        matches.extend([f"school:{x}" for x in found_school])
    else:
        gaps.extend([f"school:{x}" for x in school])

    # cap
    if score > 100:
        score = 100

    return {
        "asset": rec.get("asset") or rec.get("name") or "",
        "alignment_score": int(score),
        "matches": matches,
        "gaps": gaps,
    }


@router.post("/mission_alignment/scoring")
def mission_alignment_scoring(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Accepts `mission_alignment` and `recommendations` and returns
    scores and a basic summary.
    """
    mission_alignment = payload.get("mission_alignment") or {}
    recommendations = payload.get("recommendations") or []

    results: List[Dict[str, Any]] = []
    for rec in recommendations:
        scored = score_recommendation(mission_alignment, rec)
        results.append(scored)

    # summary buckets: high >=70, medium >=40, low <40
    summary = {"high_alignment": 0, "medium_alignment": 0, "low_alignment": 0}
    for r in results:
        s = r.get("alignment_score", 0)
        if s >= 70:
            summary["high_alignment"] += 1
        elif s >= 40:
            summary["medium_alignment"] += 1
        else:
            summary["low_alignment"] += 1

    return {"scores": results, "summary": summary}
