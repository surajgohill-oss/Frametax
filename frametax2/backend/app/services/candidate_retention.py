"""
Bounded candidate retention: the decision set CineGlobe serves is persisted as detailed rows; everything
else is aggregated (services/candidate_aggregation.py).

    Enumeration cardinality must never define persistence cardinality. Every high-volume status,
    including PRICED, requires an explicit bounded retention policy before implementation.

The engine still evaluates EVERY candidate. What is persisted in detail:

  * the baseline (any status);
  * every PRICED candidate in the global top ``GLOBAL_TOP`` (100) -- ranked on BOTH keys the served
    surfaces use: the verified NPC (true_net_cost_usd; evaluation ranking) and the risk-adjusted NPC
    (production-view review order), ties broken by the canonical economic identity;
  * every PRICED candidate in the top ``TYPE_TOP`` (100) of its canonical ``structure_type``
    (the Optimizer Globe's per-family candidates), on both keys;
  * the best PRICED single/local-stack candidate per primary jurisdiction (the frozen Jurisdictions
    Globe), on both keys;
  * every DOMINATED_WITH_PROOF row (capped at ``DOMINATED_CAP``) and every other genuinely
    reviewable/opportunity status -- CO_PRO_OPPORTUNITY, FEASIBILITY_REVIEW_REQUIRED,
    UNPRICEABLE_AUTHORITY_INSUFFICIENT, RULE_DATA_INCOMPLETE, QUALIFICATION_HARD_FAIL, ... (each capped at
    ``OPPORTUNITY_CAP``); the writer applies those caps;
  * any PRICED candidate a retained proof directly references (its incumbent).

Everything else -- all plain RULE_REJECTED permutations, every PRICED candidate outside the retained
sets, and anything over a cap -- is counted exactly in evaluation_candidate_aggregates.

Retention is decided in ONE streaming pass with exact bounded top-K lanes, so it needs O(bound) memory
however many candidates are generated, and it is independent of generation order: a lane always holds
exactly the K best candidates seen so far, so the final retained set equals what a full enumeration
sorted after the fact would retain.

Proofs reference their incumbent either by the generator's deterministic structure id
(``structural_generator_structure_id``) or by the row's own structure uuid. The two incumbent-tracking
sites call ``hold``/``release`` as the running incumbent changes; a DOMINATED_WITH_PROOF row then
``resolve_final``s its reference, which pins the referenced candidate permanently. A candidate leaving
the lanes waits in a short ring before it is aggregated, so a reference registered a moment after the
candidate was added (the multi-component search) still resolves.
"""
from __future__ import annotations

import bisect
from collections import Counter, OrderedDict

GLOBAL_TOP = 100
TYPE_TOP = 100
JURISDICTION_TOP = 1
#: A retained per-status cap for the reviewable/opportunity statuses (writer applies it).
OPPORTUNITY_CAP = 5000
#: DOMINATED_WITH_PROOF rows carry the numeric proofs; capped only to keep persistence bounded.
DOMINATED_CAP = 20000
#: Candidates that just left the lanes wait here before being aggregated (see module docstring).
DROPPED_RING = 256

#: Structure types that are a single jurisdiction's own (or same-jurisdiction stacked) candidate: what the
#: frozen Jurisdictions Globe shows one best candidate per jurisdiction of.
LOCAL_STACK_TYPES = frozenset({
    "single_country", "full_relocation", "multi_program",
    "same_jurisdiction_group_stack", "same_jurisdiction_distinct_cost_pool_stack",
})
METRICS = ("verified", "adjusted")
_INF = float("inf")


class _Lane:
    """The K best (lowest) keys seen so far, exactly, in ascending order. key = (value, identity, seq)."""
    __slots__ = ("k", "items")

    def __init__(self, k: int) -> None:
        self.k = k
        self.items: list[tuple] = []

    def offer(self, key: tuple) -> tuple[bool, int | None]:
        """(accepted, evicted_seq). O(log K) compare on the common reject path."""
        items = self.items
        if len(items) >= self.k and key > items[-1]:
            return False, None
        bisect.insort(items, key)
        if len(items) > self.k:
            worst = items.pop()
            if worst == key:
                return False, None
            return True, worst[2]
        return True, None


class Held:
    """A PRICED candidate (structure + result objects) currently retained in memory."""
    __slots__ = ("seq", "structure", "result", "npc", "adjusted", "incentive", "identity", "stype",
                 "jurisdiction", "refs", "lane_refs", "baseline", "holds", "final")

    def __init__(self, seq, structure, result, *, npc, adjusted, incentive, identity, stype, jurisdiction,
                 refs, baseline) -> None:
        self.seq = seq
        self.structure = structure
        self.result = result
        self.npc = npc
        self.adjusted = adjusted
        self.incentive = incentive
        self.identity = identity
        self.stype = stype
        self.jurisdiction = jurisdiction
        self.refs = refs
        self.lane_refs = 0
        self.baseline = baseline
        self.holds = 0
        self.final = False

    def retained(self) -> bool:
        return self.lane_refs > 0 or self.baseline or self.holds > 0 or self.final


class BoundedRetention:
    def __init__(self, global_top: int | None = None, type_top: int | None = None,
                 jurisdiction_top: int | None = None) -> None:
        self.global_top = GLOBAL_TOP if global_top is None else global_top
        self.type_top = TYPE_TOP if type_top is None else type_top
        self.jurisdiction_top = JURISDICTION_TOP if jurisdiction_top is None else jurisdiction_top
        self._lanes: dict[tuple, _Lane] = {}
        self.held: dict[int, Held] = {}
        self._by_ref: dict[str, int] = {}
        self._hold_keys: Counter = Counter()
        self._ring: OrderedDict[int, Held] = OrderedDict()
        self.considered = 0

    # ---------------------------------------------------------------- lanes
    def _lane(self, name: tuple, k: int) -> _Lane:
        lane = self._lanes.get(name)
        if lane is None:
            lane = self._lanes[name] = _Lane(k)
        return lane

    def _lane_plan(self, h: Held):
        for metric in METRICS:
            value = h.npc if metric == "verified" else (h.adjusted if h.adjusted is not None else _INF)
            key = (value, h.identity, h.seq)
            yield self._lane((metric, "global"), self.global_top), key
            yield self._lane((metric, "type", h.stype), self.type_top), key
            if h.jurisdiction and h.stype in LOCAL_STACK_TYPES:
                yield self._lane((metric, "jurisdiction", h.jurisdiction), self.jurisdiction_top), key

    # ------------------------------------------------------------- lifecycle
    def _index(self, h: Held) -> None:
        self.held[h.seq] = h
        for ref in h.refs:
            self._by_ref[ref] = h.seq

    def _unindex(self, h: Held) -> None:
        self.held.pop(h.seq, None)
        for ref in h.refs:
            if self._by_ref.get(ref) == h.seq:
                del self._by_ref[ref]

    def _drop(self, h: Held, out: list) -> None:
        """h left every lane/pin: it waits in the ring, then is aggregated (returned in ``out``)."""
        self._unindex(h)
        self._ring[h.seq] = h
        while len(self._ring) > DROPPED_RING:
            out.append(self._ring.popitem(last=False)[1])

    def consider(self, h: Held) -> list[Held]:
        """Offer one PRICED candidate. Returns the candidates that must now be aggregated."""
        out: list[Held] = []
        self.considered += 1
        h.holds = sum(1 for r in h.refs if self._hold_keys.get(r))
        evicted: list[int] = []
        for lane, key in self._lane_plan(h):
            accepted, ev = lane.offer(key)
            if accepted:
                h.lane_refs += 1
            if ev is not None:
                evicted.append(ev)
        for seq in evicted:
            other = self.held.get(seq)
            if other is not None:
                other.lane_refs -= 1
                if not other.retained():
                    self._drop(other, out)
        if h.retained():
            self._index(h)
        else:
            self._drop(h, out)
        return out

    # ----------------------------------------------------- proof references
    def _readmit(self, ref: str) -> Held | None:
        """A reference arrived after its candidate left the lanes: bring it back from the ring."""
        for seq, h in self._ring.items():
            if ref in h.refs:
                del self._ring[seq]
                self._index(h)
                return h
        return None

    def hold(self, ref: str) -> None:
        self._hold_keys[ref] += 1
        seq = self._by_ref.get(ref)
        h = self.held.get(seq) if seq is not None else self._readmit(ref)
        if h is not None:
            h.holds += 1

    def release(self, ref: str) -> list[Held]:
        out: list[Held] = []
        if self._hold_keys.get(ref, 0) <= 0:
            return out
        self._hold_keys[ref] -= 1
        seq = self._by_ref.get(ref)
        h = self.held.get(seq) if seq is not None else None
        if h is not None:
            h.holds -= 1
            if not h.retained():
                self._drop(h, out)
        return out

    def resolve_final(self, ref: str) -> bool:
        """A retained proof references ``ref``: pin that candidate permanently. False if it is not
        (or no longer) available -- the caller fails closed."""
        seq = self._by_ref.get(ref)
        h = self.held.get(seq) if seq is not None else self._readmit(ref)
        if h is None:
            return False
        h.final = True
        return True

    # -------------------------------------------------------------- finish
    def best_structure_id_by_type(self) -> dict:
        """structure_type -> id of the RETAINED best (verified NPC) candidate of that type: it dominates
        every aggregated PRICED candidate of the type (they all fell outside the type's top set)."""
        out = {}
        for name, lane in self._lanes.items():
            if name[0] == "verified" and name[1] == "type" and lane.items:
                h = self.held.get(lane.items[0][2])
                if h is not None:
                    out[name[2]] = h.structure.id
        return out

    def finalize(self) -> tuple[list[Held], list[Held]]:
        """(retained, to_aggregate). retained is sorted by (verified NPC, identity, seq)."""
        # A hold is TEMPORARY protection for a running incumbent: at the end only lane members, the
        # baseline and proof-referenced (``final``) candidates are rows; a hold nobody referenced is not.
        keeps = lambda h: h.lane_refs > 0 or h.baseline or h.final
        retained = sorted((h for h in self.held.values() if keeps(h)), key=lambda h: (h.npc, h.identity, h.seq))
        to_aggregate = list(self._ring.values()) + [h for h in self.held.values() if not keeps(h)]
        self._dominating = self.best_structure_id_by_type()
        self.held = {}
        self._by_ref = {}
        self._ring = OrderedDict()
        return retained, to_aggregate

    @property
    def dominating_by_type(self) -> dict:
        return getattr(self, "_dominating", {})

    def bound(self, structure_types: int, jurisdictions: int) -> int:
        """Upper bound on lane-retained PRICED candidates for that many types/jurisdictions (both metrics)."""
        per_metric = self.global_top + structure_types * self.type_top + jurisdictions * self.jurisdiction_top
        return len(METRICS) * per_metric
