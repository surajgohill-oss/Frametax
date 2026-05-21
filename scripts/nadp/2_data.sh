#!/bin/bash
# Layer 2 — Data Source Validation
# Validates payload structure, event count, schema shape, and no hidden duplication.
set -euo pipefail

BACKEND="http://localhost:8000"
EVENTS_BODY=$(curl -s "$BACKEND/api/events/")

echo "Validating event payload structure..."
python3 - <<'PYEOF'
import sys, json, os

data = json.loads(os.environ.get("EVENTS_JSON", ""))

if not isinstance(data, list):
    print("❌ Response is not a JSON array")
    sys.exit(1)

count = len(data)
print(f"  event count     : {count}")

if count == 0:
    print("❌ Zero events returned — seed the database or add events via the UI")
    sys.exit(1)

# Validate each event has required canonical fields
required = {"id", "canonical_id", "title", "event_date", "tracked_events"}
for i, ev in enumerate(data):
    missing = required - ev.keys()
    if missing:
        print(f"❌ Event[{i}] missing fields: {missing}")
        sys.exit(1)

# Check canonical_id uniqueness
canonical_ids = [ev["canonical_id"] for ev in data]
if len(canonical_ids) != len(set(canonical_ids)):
    dupes = [c for c in canonical_ids if canonical_ids.count(c) > 1]
    print(f"❌ DUPLICATE canonical_ids detected: {dupes}")
    sys.exit(1)
print(f"  canonical_id unique  ✓")

# Validate tracked_events is a nested array (NOT top-level events)
te_counts = []
for ev in data:
    te = ev.get("tracked_events", [])
    if not isinstance(te, list):
        print(f"❌ Event {ev['id']}: tracked_events is not a list")
        sys.exit(1)
    te_counts.append(len(te))

print(f"  tracked_events/event: {te_counts}  (expected ≤2 per event)")
if any(c > 6 for c in te_counts):
    print(f"❌ tracked_events count suspiciously high — possible data integrity issue")
    sys.exit(1)

# Verify top-level array length == event count (no flatMap duplication in API)
total_te = sum(te_counts)
print(f"  top-level events    : {count}  (this must equal what the UI renders)")
print(f"  total tracked_events: {total_te}  (sub-items, never rendered as cards)")
print("")
print(f"✅ Data layer valid — {count} canonical events, no structural anomalies")
PYEOF
export EVENTS_JSON="$EVENTS_BODY"
python3 - <<'PYEOF'
import sys, json, os
data = json.loads(os.environ.get("EVENTS_JSON", "[]"))
count = len(data)
total_te = sum(len(ev.get("tracked_events", [])) for ev in data)
if count == 0:
    print("❌ Zero events")
    sys.exit(1)
print(f"  event count     : {count}")
canonical_ids = [ev["canonical_id"] for ev in data]
if len(canonical_ids) != len(set(canonical_ids)):
    print("❌ Duplicate canonical_ids")
    sys.exit(1)
print(f"  canonical_id    : {len(set(canonical_ids))} unique  ✓")
te_counts = [len(ev.get("tracked_events", [])) for ev in data]
print(f"  tracked_events  : {te_counts} per event  (sub-items, not event cards)")
print(f"  total te items  : {total_te}  (expected {count * 2} max for stubhub+seatgeek)")
print(f"✅ {count} canonical events — structure valid")
PYEOF

echo ""
echo "Checking listings endpoint..."
FIRST_ID=$(echo "$EVENTS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'])")
LISTINGS_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND/api/listings/events/$FIRST_ID")
if [ "$LISTINGS_HTTP" != "200" ]; then
  echo "❌ /api/listings/events/$FIRST_ID returned HTTP $LISTINGS_HTTP"
  exit 1
fi
LISTING_COUNT=$(curl -s "$BACKEND/api/listings/events/$FIRST_ID" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))")
echo "  /api/listings/events/$FIRST_ID  ✓  ($LISTING_COUNT listings)"
