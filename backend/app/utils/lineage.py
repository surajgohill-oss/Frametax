import time
import uuid


def trace_event(event_id: str) -> dict:
    return {
        "trace_id": str(uuid.uuid4()),
        "event_id": event_id,
        "stages": [],
    }


def add_stage(trace: dict, stage: str, metadata: dict | None = None) -> dict:
    trace["stages"].append({
        "stage": stage,
        "ts": round(time.time(), 4),
        "meta": metadata or {},
    })
    return trace
