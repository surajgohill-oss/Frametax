"""User-selected leading structure contract (app/services/leading_selection.py). Pure; no database."""
import uuid

from app.services.leading_selection import choose_leading

CANONICAL = uuid.uuid4()
USER = uuid.uuid4()


def test_no_user_selection_uses_canonical_leader():
    assert choose_leading(None, None, CANONICAL) == (CANONICAL, False)
    assert choose_leading(None, None, None) == (None, False)


def test_user_selection_survives_regeneration_when_its_identity_still_exists():
    assert choose_leading("abc", USER, CANONICAL) == (USER, False)
    assert choose_leading("abc", USER, None) == (USER, False)


def test_vanished_user_selection_falls_back_to_canonical_and_is_disclosed():
    assert choose_leading("abc", None, CANONICAL) == (CANONICAL, True)
    assert choose_leading("abc", None, None) == (None, True)
