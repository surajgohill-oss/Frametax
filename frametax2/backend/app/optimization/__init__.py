"""
app/optimization — Phase E deterministic optimization layer.

Pure Python. No DB access. Operates on GlobalProgramEntry inventory.

Modules:
  types.py             — shared dataclasses
  stacking_rules.py    — static stacking rule lookup
  enumerate_structures.py — structure candidate generator
  score_structures.py  — economic scoring + explanation
  optimizer.py         — top-level orchestration API
"""
from app.optimization.optimizer import run_optimizer, OptimizationResult  # noqa: F401

OPTIMIZER_VERSION = "1.0.0"
