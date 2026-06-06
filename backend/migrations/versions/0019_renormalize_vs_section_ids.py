"""Renormalize VividSeats section_id values to strip venue-tier qualifiers.

VS listings stored section_id values like "UPPER BOWL 211" while all other
markets use "211". This migration applies the same normalization logic as the
updated vividseats.py normalize_section to all existing VS listings.

After this migration, identity-key dedup (section_id, row, qty) will correctly
match VS listings against StubHub/GameTime/TickPick/SeatGeek.

Revision ID: 0019
Revises: 0018
"""
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


_TIER_PREFIXES = [
    "lower bowl",
    "upper bowl",
    "lower level",
    "upper level",
    "lower deck",
    "upper deck",
    "lower tier",
    "upper tier",
    "club level",
    "loge level",
    "mezzanine level",
    "mezzanine",
    "terrace level",
    "terrace",
    "field level",
    "field",
    "suite level",
    "suite",
    "box",
]


def upgrade() -> None:
    # Build a CASE expression that strips tier qualifiers from section_id.
    # Applied only to rows from the VividSeats marketplace.
    #
    # The expression is:
    #   UPPER(TRIM(REGEXP_REPLACE(section_id, '(?i)^(prefix1|prefix2|...)\s+', '')))
    #
    # Postgres regexp_replace supports (?i) for case-insensitive matching.

    pattern = "(?i)^(" + "|".join(_TIER_PREFIXES) + r")\s+"

    op.execute(f"""
        UPDATE listings l
        SET    section_id = UPPER(TRIM(REGEXP_REPLACE(l.section_id, '{pattern}', '')))
        FROM   marketplaces m
        WHERE  l.marketplace_id = m.id
          AND  m.slug = 'vividseats'
          AND  l.section_id IS NOT NULL
          AND  l.section_id ~ '{pattern}'
    """)


def downgrade() -> None:
    # Not reversible — original values not stored.
    pass
