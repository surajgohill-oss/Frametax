"""
holdout_guard.py

Script Analyzer SA-1.5, Part G — the data-leakage guard.

The corpus exists so the Script Analyzer can eventually be scored against
real productions. That is only meaningful if the predictor never sees the
answers. This module makes that a mechanical guarantee rather than a
convention someone has to remember.

The rule:

    While a fixture is being used to evaluate prediction quality, held-out
    actual data MUST NOT be reachable from the prediction path.

Held-out means: actual gross budget, department totals, fringes,
contingency, bond, actual shoot days, actual schedule/DOOD, actual crew
counts, actual geography, actual incentive/QPE.

The one legitimate exception is an input the producer genuinely supplies up
front. A production really does know its own intended shoot days before
anyone predicts anything. So a field can be explicitly declared a
USER-PROVIDED INPUT for a specific evaluation — but that declaration is
explicit, per-field and recorded, never a silent default.

Usage:

    session = PredictionSession(fixture, user_provided={"shoot_days"})
    inputs = session.prediction_inputs()      # script side only
    ... predictor runs ...
    session.close_prediction(prediction)
    actuals = session.reveal_actuals()        # now, and only now

Calling `reveal_actuals()` before `close_prediction()` raises. Reading a
held-out field that was not declared user-provided raises. Both are hard
errors, not warnings — a silently-leaked evaluation is worse than a failed one.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.validation.real_production_corpus import (
    HeldOutActuals,
    ProductionFixture,
    ScriptSideInputs,
)


class HoldoutViolation(RuntimeError):
    """Raised when a prediction path tries to reach held-out actual data."""


#: Every field on HeldOutActuals is held out by definition.
HELD_OUT_FIELDS: frozenset[str] = frozenset(HeldOutActuals.__dataclass_fields__.keys())


def is_held_out(field_name: str) -> bool:
    return field_name in HELD_OUT_FIELDS


@dataclass
class PredictionSession:
    """A guarded evaluation of one fixture.

    Holds the fixture but exposes only its script side until a prediction has
    been recorded.
    """

    fixture: ProductionFixture
    #: Held-out field names the evaluation explicitly treats as producer-supplied.
    user_provided: frozenset[str] = frozenset()
    _prediction: Any = field(default=None, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.user_provided, frozenset):
            object.__setattr__(self, "user_provided", frozenset(self.user_provided))
        unknown = self.user_provided - HELD_OUT_FIELDS
        if unknown:
            raise ValueError(
                f"user_provided names fields that are not held-out actuals: {sorted(unknown)}"
            )
        if not self.fixture.holdout_eligible:
            raise HoldoutViolation(
                f"Fixture {self.fixture.fixture_key!r} is not holdout-eligible and "
                "must not be used to evaluate prediction quality. "
                f"{self.fixture.notes}"
            )

    # ── prediction phase ───────────────────────────────────────────────────

    def prediction_inputs(self) -> ScriptSideInputs:
        """The ONLY data a predictor may see. Script-derived facts."""
        return self.fixture.script_side

    def user_input(self, field_name: str) -> Any:
        """Read a held-out field that this evaluation explicitly declared a
        producer-supplied input. Anything else raises."""
        if field_name not in HELD_OUT_FIELDS:
            raise ValueError(f"{field_name!r} is not a held-out field.")
        if field_name not in self.user_provided:
            raise HoldoutViolation(
                f"{field_name!r} is held-out actual data for fixture "
                f"{self.fixture.fixture_key!r} and was NOT declared a user-provided "
                "input for this evaluation. A predictor may not read it. Declare it "
                "explicitly in PredictionSession(user_provided={...}) only if the "
                "producer genuinely supplies it up front."
            )
        return getattr(self.fixture.held_out, field_name)

    def close_prediction(self, prediction: Any) -> None:
        """Record the prediction. After this, actuals may be revealed."""
        if self._closed:
            raise HoldoutViolation("Prediction already closed for this session.")
        self._prediction = prediction
        self._closed = True

    # ── evaluation phase ───────────────────────────────────────────────────

    @property
    def prediction(self) -> Any:
        if not self._closed:
            raise HoldoutViolation("No prediction has been recorded yet.")
        return self._prediction

    def reveal_actuals(self) -> HeldOutActuals:
        """The answers — available only after a prediction is recorded."""
        if not self._closed:
            raise HoldoutViolation(
                "Held-out actuals cannot be revealed before a prediction is "
                "recorded. Call close_prediction(...) first. This ordering is the "
                "whole point of the corpus: a predictor that can see the answer "
                "proves nothing."
            )
        return self.fixture.held_out


def assert_no_leakage(payload: Any, fixture: ProductionFixture,
                      *, allowed: frozenset[str] = frozenset()) -> None:
    """Assert that a prediction-path payload carries no held-out actual value.

    Compares against the fixture's real held-out values rather than looking
    for field names, so a leak survives being renamed or nested. Numeric
    values are compared with a small tolerance so an incidental collision on
    a tiny number does not produce a false alarm.
    """
    actuals = fixture.held_out
    watched: dict[str, Any] = {}
    for name, value in asdict(actuals).items():
        if value is None or name in allowed:
            continue
        # Ignore small integers (e.g. shoot_days=18) unless explicitly watched —
        # they collide too easily with unrelated counts to be evidence on their own.
        if isinstance(value, (int, float)) and abs(value) < 1000:
            continue
        watched[name] = value

    found: list[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for v in node.values():
                _walk(v)
        elif isinstance(node, (list, tuple, set)):
            for v in node:
                _walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            for name, value in watched.items():
                if isinstance(value, (int, float)) and abs(float(node) - float(value)) < 0.01:
                    found.append(f"{name}={value}")
        elif isinstance(node, str):
            for name, value in watched.items():
                if isinstance(value, str) and value and value.lower() in node.lower():
                    found.append(f"{name}={value!r}")

    _walk(payload if not hasattr(payload, "__dataclass_fields__") else asdict(payload))

    if found:
        raise HoldoutViolation(
            f"Held-out actual data leaked into the prediction path for fixture "
            f"{fixture.fixture_key!r}: {sorted(set(found))}. If one of these is "
            "genuinely a producer-supplied input, pass it in `allowed`."
        )
