from datetime import datetime
from typing import Dict


def build_audit_record(action: str, payload: Dict) -> Dict:
    return {
        "action": action,
        "payload": payload,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
