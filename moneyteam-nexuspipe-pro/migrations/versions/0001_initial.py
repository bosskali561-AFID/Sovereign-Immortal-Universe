"""initial schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(50), index=True),
        sa.Column("event_id", sa.String(255), unique=True, index=True),
        sa.Column("event_type", sa.String(150)),
        sa.Column("processed", sa.Boolean),
        sa.Column("payload", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("webhook_events")
