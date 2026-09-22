"""knowledge base and remaining schema

Revision ID: 0002_knowledge
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_knowledge"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _columns():
    return [
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    ]


def upgrade():
    op.create_table(
        "signals_raw",
        *_columns(),
        sa.Column("source", sa.String(60), index=True),
        sa.Column("payload", sa.JSON),
    )
    op.create_table(
        "opportunities",
        *_columns(),
        sa.Column("symbol", sa.String(60), index=True),
        sa.Column("ept", sa.Float),
        sa.Column("action", sa.String(80)),
        sa.Column("phase", sa.String(80)),
        sa.Column("status", sa.String(40)),
        sa.Column("payload", sa.JSON),
    )
    op.create_table(
        "winners",
        *_columns(),
        sa.Column("symbol", sa.String(60), index=True),
        sa.Column("pnl_paper", sa.Float),
        sa.Column("strategy_dna", sa.JSON),
    )
    op.create_table(
        "failures",
        *_columns(),
        sa.Column("symbol", sa.String(60), index=True),
        sa.Column("reason", sa.String(200)),
        sa.Column("autopsy", sa.JSON),
    )
    op.create_table(
        "audit_events",
        *_columns(),
        sa.Column("event_type", sa.String(100), index=True),
        sa.Column("actor", sa.String(120)),
        sa.Column("detail", sa.Text),
    )


def downgrade():
    op.drop_table("audit_events")
    op.drop_table("failures")
    op.drop_table("winners")
    op.drop_table("opportunities")
    op.drop_table("signals_raw")
