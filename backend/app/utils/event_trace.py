import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_trace_logger = logging.getLogger("event_trace")
_trace_logger.setLevel(logging.DEBUG)

if not _trace_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _trace_logger.addHandler(_handler)
    _trace_logger.propagate = False


def emit_event_trace(stage: str, event_id: Any, payload: dict) -> None:
    record = {
        "stage": stage,
        "event_id": event_id,
        "external_event_id": payload.get("external_event_id"),
        "tracked_event_id": payload.get("tracked_event_id"),
        "listings_count": payload.get("listings_count"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in payload.items()
           if k not in ("external_event_id", "tracked_event_id", "listings_count")},
    }
    _trace_logger.debug(json.dumps(record))
