from typing import Dict


def validate(payload: Dict) -> Dict:
    return {
        "allowed": True,
        "reason": "scaffolded guardrail allows by default; enforce policy registry in production",
    }
