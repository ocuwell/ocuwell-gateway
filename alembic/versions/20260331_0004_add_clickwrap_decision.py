"""add clickwrap decision

Revision ID: 20260331_0004
Revises: 20260331_0003
Create Date: 2026-03-31 12:05:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_0004"
down_revision = "20260331_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("clickwrap_acceptance", recreate="auto") as batch_op:
        batch_op.add_column(
            sa.Column(
                "decision",
                sa.String(length=16),
                nullable=False,
                server_default="accept",
            )
        )
        batch_op.create_index(
            "ix_clickwrap_decision_at",
            ["decision", "accepted_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("clickwrap_acceptance", recreate="auto") as batch_op:
        batch_op.drop_index("ix_clickwrap_decision_at")
        batch_op.drop_column("decision")
