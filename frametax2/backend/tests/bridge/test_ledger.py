from __future__ import annotations

from app.bridge.ledger import PERMANENT_DOCTRINES, current_ledger, seed_ledger
from app.bridge.schema import LedgerStatus


class TestSeeding:
    def test_seed_writes_expected_entries(self):
        n = seed_ledger()
        assert n == len(current_ledger())
        assert n > 15  # 11 doctrines + milestones + backlog + phases

    def test_seed_is_idempotent(self):
        seed_ledger()
        second = seed_ledger()
        assert second == 0

    def test_all_permanent_doctrines_present(self):
        seed_ledger()
        entries = current_ledger()
        entry_ids = {e.entry_id for e in entries}
        for doctrine_id, _ in PERMANENT_DOCTRINES:
            assert doctrine_id in entry_ids

    def test_no_automatic_rule_mutation_doctrine_present(self):
        """The Bridge's own governing rule must be in its own ledger."""
        seed_ledger()
        entries = {e.entry_id: e for e in current_ledger()}
        assert "doctrine-no-automatic-rule-mutation" in entries
        assert "human" in entries["doctrine-no-automatic-rule-mutation"].description.lower()


class TestLedgerContent:
    def test_requirements_backlog_entry_present(self):
        seed_ledger()
        entries = {e.entry_id: e for e in current_ledger()}
        assert "backlog-requirements-profiles" in entries
        assert entries["backlog-requirements-profiles"].status == LedgerStatus.NOT_IMPLEMENTED

    def test_current_and_next_phase_present(self):
        seed_ledger()
        entries = {e.entry_id: e for e in current_ledger()}
        assert "phase-current" in entries
        assert "phase-next-authorized" in entries

    def test_every_entry_has_nonempty_provenance(self):
        seed_ledger()
        for e in current_ledger():
            assert e.provenance and e.provenance.strip()

    def test_every_entry_has_a_valid_status(self):
        seed_ledger()
        for e in current_ledger():
            assert isinstance(e.status, LedgerStatus)
