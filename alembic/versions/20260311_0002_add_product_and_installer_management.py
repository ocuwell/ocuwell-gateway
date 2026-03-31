"""add product and installer management

Revision ID: 20260311_0002
Revises: 20260311_0001
Create Date: 2026-03-11 11:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260311_0002"
down_revision = "20260311_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product_installer",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("blob_url", sa.String(length=2048), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("file_size_bytes", sa.BIGINT(), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_installer_lookup",
        "product_installer",
        ["product_id", "platform", "version"],
        unique=False,
    )

    with op.batch_alter_table("clickwrap_acceptance", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("product_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("product_version", sa.String(length=64), nullable=True))
        batch_op.create_foreign_key(
            "fk_clickwrap_product_id",
            "product",
            ["product_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_clickwrap_product_version",
            ["product_id", "product_version"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("clickwrap_acceptance", recreate="auto") as batch_op:
        batch_op.drop_index("ix_clickwrap_product_version")
        batch_op.drop_constraint("fk_clickwrap_product_id", type_="foreignkey")
        batch_op.drop_column("product_version")
        batch_op.drop_column("product_id")

    op.drop_index("ix_product_installer_lookup", table_name="product_installer")
    op.drop_table("product_installer")
    op.drop_table("product")
