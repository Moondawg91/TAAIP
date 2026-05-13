from typing import Dict


def route_task(task: str, payload: Dict) -> Dict:
    return {
        "task": task,
        "provider": "unconfigured",
        "result": "provider execution is scaffolded and disabled by default",
    }
