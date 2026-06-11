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


def build_event_lineage(event, tracked_events: list, marketplace_ids: list) -> dict:
    """Structured provenance: DB → enrichment → marketplace resolution."""
    return {
        "source_table": "events",
        "event_id": event.id,
        "canonical_id": event.canonical_id,
        "tracked_event_count": len(tracked_events),
        "marketplaces": [te.marketplace.slug for te in tracked_events if te.marketplace],
        "query_path": [
            "SELECT events WHERE id=?",
            f"SELECT tracked_events WHERE event_id={event.id}",
            f"SELECT MIN(price) FROM listings GROUP BY marketplace_id WHERE event_id={event.id}",
        ],
    }
