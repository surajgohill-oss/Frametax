"""Codex final wiring remediation (P0-NL-001): projects.production_company_identifier

The Netherlands company/award-period incentive cap (EUR 3,000,000 per
production company per year) previously had no canonical company identity
to bind to at all — a caller-supplied prior-awards scalar plus two boolean
"evidenced" flags described identity/period binding only in comments,
while ProjectEconomicInputs carried neither field. Two independent
price_segment() calls using the same scalar both priced identically,
because nothing tied the aggregate to a real, stable company identity.

production_company_identifier is a producer-supplied, stable STRING
identity for the real-world legal production company entity behind a
project — explicitly NEVER the project's own title or id, and never
inferred. Two projects sharing the same production_company_identifier
(and the same, already-existing target_shoot_year, reused as the award
period/year) are treated as the SAME company for cross-project cap
conservation. Additive, nullable — existing projects get NULL (an honest
"no canonical company identity on file yet" state), which correctly
makes any company/period-scoped cap (e.g. nl_film_production_incentive)
conditional/non-priceable until a producer sets it, per this task's own
explicit "unknown company remains conditional/non-priceable" requirement.

Revision ID: 0072
Revises: 0071
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0072"
down_revision: Union[str, None] = "0071"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("production_company_identifier", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_projects_production_company_identifier",
        "projects",
        ["production_company_identifier"],
    )


def downgrade() -> None:
    op.drop_index("ix_projects_production_company_identifier", table_name="projects")
    op.drop_column("projects", "production_company_identifier")
