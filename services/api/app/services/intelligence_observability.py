from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional


_logger = logging.getLogger("taaip.intelligence")


def emit_event(event: str, *, rsid: Optional[str] = None, period: Optional[str] = None, duration_ms: Optional[int] = None, **extra: Any) -> None:
    payload: Dict[str, Any] = {
        "event": event,
        "rsid": rsid,
        "period": period,
        "duration_ms": duration_ms,
    }
    for key, value in extra.items():
        if value is not None and key not in payload:
            payload[key] = value
    _logger.info(json.dumps(payload, default=str))


@contextmanager
def timed_event(event: str, *, rsid: Optional[str] = None, period: Optional[str] = None, **extra: Any) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        safe_extra = dict(extra)
        safe_extra.pop("duration_ms", None)
        emit_event(event, rsid=rsid, period=period, duration_ms=duration_ms, **safe_extra)


def error_payload(message: str, *, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "error": True,
        "message": message,
        "context": context or {},
    }
