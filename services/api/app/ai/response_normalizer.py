from datetime import datetime
from typing import Dict


def normalize_response(task: str, raw: Dict) -> Dict:
    return {
        "status": "ok",
        "data": {
            "task": task,
            "provider": raw.get("provider"),
            "result": raw.get("result"),
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
    }
