"""
Accumulates, WHILE an evaluation runs, what its persisted rows add up to.

evaluate_project() feeds every candidate row it persists to ``observe()`` (from the bulk
writer, at the single persistence site) and writes ``payload()`` as one narrow
EvaluationGenerationSummary row in the same transaction. Nothing here re-reads the
database, so serving an FVD-scale evaluation never has to count, group or load its
525K-row unpriced universe again.

Bounded candidate retention (canonical-1.90.0): a candidate outside the retained decision set (plain
RULE_REJECTED, PRICED outside the retained top sets, anything over a status cap) is COUNTED here
(``observe(None, ...)``, no ordinal) but never becomes a physical row -- it is folded into
evaluation_candidate_aggregates (services/candidate_aggregation.py). ``total_rows`` therefore counts
every candidate GENERATED and always equals ``persisted_rows + aggregated``.

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
        self.persisted_rows = 0
        self.aggregated = 0
        self.aggregated_priced = 0
        self._non_rejected: list[int] = []

    def observe(self, ordinal: int | None, *, status: str, reason: str, priced: bool, is_baseline: bool) -> None:
        """``ordinal`` is the physical row's generation_ordinal, or None for a candidate that was
        aggregated instead of persisted."""
        self.total_rows += 1
        if ordinal is None:
            self.aggregated += 1
            if priced:
                self.aggregated_priced += 1
        else:
            self.persisted_rows += 1
        if priced:
            self.priced_count += 1
        else:
            self.unpriced_count += 1
            self._by_reason[(status, reason)] += 1
        if ordinal is not None and (status != REJECTED_STATUS or is_baseline):
            self._non_rejected.append(ordinal)

    def payload(self, aggregate_groups: int = 0) -> dict:
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
            "persisted_rows": self.persisted_rows,
            "aggregated_candidates": self.aggregated,
            "aggregated_priced": self.aggregated_priced,
            "aggregate_groups": aggregate_groups,
        }
