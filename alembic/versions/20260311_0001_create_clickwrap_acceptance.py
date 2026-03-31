"""create clickwrap acceptance table

Revision ID: 20260311_0001
Revises:
Create Date: 2026-03-11 10:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260311_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clickwrap_acceptance",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agreement_id", sa.String(length=255), nullable=False),
        sa.Column("agreement_version", sa.String(length=64), nullable=False),
        sa.Column("accepted_by", sa.String(length=255), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_clickwrap_agreement_version",
        "clickwrap_acceptance",
        ["agreement_id", "agreement_version"],
        unique=False,
    )
    op.create_index(
        "ix_clickwrap_accepted_by_at",
        "clickwrap_acceptance",
        ["accepted_by", "accepted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_clickwrap_accepted_by_at", table_name="clickwrap_acceptance")
    op.drop_index("ix_clickwrap_agreement_version", table_name="clickwrap_acceptance")
    op.drop_table("clickwrap_acceptance")
