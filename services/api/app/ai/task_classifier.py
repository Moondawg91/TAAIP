from typing import Dict


def classify_task(payload: Dict) -> str:
    text = str(payload.get("prompt") or payload.get("task") or "").lower()
    if "lms" in text or "training" in text:
        return "lms"
    if "mipoe" in text:
        return "mipoe"
    if "mdmp" in text:
        return "mdmp"
    return "general"
