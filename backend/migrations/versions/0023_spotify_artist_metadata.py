"""Spotify artist metadata columns on events.

Revision ID: 0023
Revises: 0022
Create Date: 2026-06-18

Changes:
  1. events.spotify_artist_id  — VARCHAR(100) nullable
  2. events.spotify_artist_url — VARCHAR(500) nullable
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("spotify_artist_id", sa.String(100), nullable=True))
    op.add_column("events", sa.Column("spotify_artist_url", sa.String(500), nullable=True))


def downgrade():
    op.drop_column("events", "spotify_artist_url")
    op.drop_column("events", "spotify_artist_id")
