#!/bin/bash
# Layer 3 — Client-Side Code Validation
# Static analysis of the frontend API adapter and render paths.
# Any pattern that could inflate event cardinality causes an immediate exit.
set -euo pipefail

FRONTEND="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/frontend/src"

echo "Checking API base URL..."
BASE_LINE=$(grep -r "NEXT_PUBLIC_API_URL\|const BASE" "$FRONTEND/lib/api.ts")
echo "  $BASE_LINE"
if echo "$BASE_LINE" | grep -q "localhost:3000"; then
  echo "❌ API base points to Next.js port 3000 — must point to FastAPI at 8000"
  exit 1
fi
echo "  API base  ✓  (targets :8000)"

echo ""
echo "Checking for forbidden render patterns..."
FAIL=0

# concat() on events arrays inflates cardinality
if grep -rn "\.concat(" "$FRONTEND" --include="*.tsx" --include="*.ts" | grep -i "event"; then
  echo "❌ CARDINALITY VIOLATION: .concat() on event array detected"
  FAIL=1
fi

# spread merge e.g. [...events, ...otherEvents]
if grep -rn "\[\.\.\.events" "$FRONTEND" --include="*.tsx" --include="*.ts"; then
  echo "❌ CARDINALITY VIOLATION: spread-merge of events array detected"
  FAIL=1
fi

# flatMap over events
if grep -rn "events\.flatMap\|events\.flat(" "$FRONTEND" --include="*.tsx" --include="*.ts"; then
  echo "❌ CARDINALITY VIOLATION: flatMap/flat over events array"
  FAIL=1
fi

# tracked_events iterated as render source
if grep -rn "tracked_events\.map\|tracked_events\.forEach" "$FRONTEND" --include="*.tsx" --include="*.ts"; then
  echo "❌ DOMAIN VIOLATION: tracked_events used as render iteration source"
  FAIL=1
fi

# Direct localStorage access outside the allowed hook
LOCALSTORAGE_VIOLATIONS=$(grep -rn "localStorage" "$FRONTEND" --include="*.tsx" --include="*.ts" \
  | grep -v "useFollowed.ts" || true)
if [ -n "$LOCALSTORAGE_VIOLATIONS" ]; then
  echo "❌ TRACKING VIOLATION: localStorage accessed outside useFollowed hook:"
  echo "$LOCALSTORAGE_VIOLATIONS"
  FAIL=1
fi

if [ $FAIL -eq 0 ]; then
  echo "  No forbidden patterns  ✓"
fi

echo ""
echo "Checking assertEventCardinality guard is present..."
if ! grep -rq "assertEventCardinality" "$FRONTEND/app/page.tsx"; then
  echo "❌ assertEventCardinality not called in FeedPage — runtime cardinality guard is missing"
  FAIL=1
else
  echo "  assertEventCardinality  ✓"
fi

echo ""
echo "Checking mounted guard in useFollowed..."
if ! grep -q "mounted" "$FRONTEND/hooks/useFollowed.ts"; then
  echo "❌ mounted guard missing in useFollowed — hydration mismatch possible"
  FAIL=1
else
  echo "  mounted guard  ✓"
fi

[ $FAIL -eq 0 ] || exit 1
