"""
Accumulates, WHILE an evaluation runs, what its persisted rows add up to.

evaluate_project() feeds every candidate row it persists to ``observe()`` (from the bulk
writer, at the single persistence site) and writes ``payload()`` as one narrow
EvaluationGenerationSummary row in the same transaction. Nothing here re-reads the
database, so serving an FVD-scale evaluation never has to count, group or load its
525K-row unpriced universe again.

"Unpriced" means no net cost (true_net_cost_usd IS NULL) -- exactly the population the
evaluator has always served as ``unpriceable``. ``non_rejected_ordinals`` lists the
generation_ordinal of every row that is NOT a plain RULE_REJECTED (plus any baseline,
whatever its status): the few hundred to few thousand rows ranking and the workspace
load, fetched by ordinal through the (fingerprint, engine, ordinal) index.
"""
from __future__ import annotations

from collections import Counter

REJECTED_STATUS = "RULE_REJECTED"


class GenerationSummaryBuilder:
    def __init__(self) -> None:
        self.total_rows = 0
        self.priced_count = 0
        self.unpriced_count = 0
        self._by_reason: Counter = Counter()
        self._non_rejected: list[int] = []

    def observe(self, ordinal: int, *, status: str, reason: str, priced: bool, is_baseline: bool) -> None:
        self.total_rows += 1
        if priced:
            self.priced_count += 1
        else:
            self.unpriced_count += 1
            self._by_reason[(status, reason)] += 1
        if status != REJECTED_STATUS or is_baseline:
            self._non_rejected.append(ordinal)

    def payload(self) -> dict:
        by_reason = [
            {"candidate_status": status or None, "rejection_reason_class": reason or None, "count": count}
            for (status, reason), count in sorted(self._by_reason.items())
        ]
        by_disposition: dict[str, int] = {}
        for (status, _), count in sorted(self._by_reason.items()):
            by_disposition[status or "UNSPECIFIED"] = by_disposition.get(status or "UNSPECIFIED", 0) + count
        return {
            "total_rows": self.total_rows,
            "priced_count": self.priced_count,
            "unpriced_count": self.unpriced_count,
            "by_disposition": by_disposition,
            "by_reason": by_reason,
            "non_rejected_ordinals": sorted(self._non_rejected),
        }
