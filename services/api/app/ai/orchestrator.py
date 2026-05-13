from typing import Dict

from services.api.app.ai.task_classifier import classify_task
from services.api.app.ai.response_normalizer import normalize_response
from services.api.app.ai.router import route_task


def orchestrate(payload: Dict) -> Dict:
    task = classify_task(payload)
    raw = route_task(task, payload)
    return normalize_response(task, raw)
