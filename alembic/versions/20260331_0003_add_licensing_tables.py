"""add licensing tables

Revision ID: 20260331_0003
Revises: 20260311_0002
Create Date: 2026-03-31 10:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_0003"
down_revision = "20260311_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "license",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("license_key", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("product_version", sa.String(length=64), nullable=True),
        sa.Column("issued_to", sa.String(length=255), nullable=True),
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'active'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("license_key"),
    )
    op.create_index("ix_license_product_status", "license", ["product_id", "status"], unique=False)
    op.create_index("ix_license_expires_at", "license", ["expires_at"], unique=False)

    op.create_table(
        "device",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("product_version", sa.String(length=64), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "device_id", name="uq_device_product_device_id"),
    )
    op.create_index("ix_device_product_registered_at", "device", ["product_id", "registered_at"], unique=False)

    op.create_table(
        "license_activation",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("license_id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=False),
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=32), server_default=sa.text("'client'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["license_id"], ["license.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_license_activation_license_time",
        "license_activation",
        ["license_id", "activated_at"],
        unique=False,
    )
    op.create_index(
        "ix_license_activation_device_time",
        "license_activation",
        ["device_id", "activated_at"],
        unique=False,
    )

    op.create_table(
        "license_deactivation",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("license_id", sa.String(length=36), nullable=False),
        sa.Column("device_id", sa.String(length=36), nullable=True),
        sa.Column(
            "deactivated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=32), server_default=sa.text("'client'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["license_id"], ["license.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_license_deactivation_license_time",
        "license_deactivation",
        ["license_id", "deactivated_at"],
        unique=False,
    )
    op.create_index(
        "ix_license_deactivation_device_time",
        "license_deactivation",
        ["device_id", "deactivated_at"],
        unique=False,
    )

    op.create_table(
        "license_revocation",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("license_id", sa.String(length=36), nullable=False),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("revoked_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["license_id"], ["license.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_license_revocation_license_time",
        "license_revocation",
        ["license_id", "revoked_at"],
        unique=False,
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("actor_type", sa.String(length=64), nullable=True),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_correlation_id", "audit_log", ["correlation_id"], unique=False)
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_correlation_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_license_revocation_license_time", table_name="license_revocation")
    op.drop_table("license_revocation")

    op.drop_index("ix_license_deactivation_device_time", table_name="license_deactivation")
    op.drop_index("ix_license_deactivation_license_time", table_name="license_deactivation")
    op.drop_table("license_deactivation")

    op.drop_index("ix_license_activation_device_time", table_name="license_activation")
    op.drop_index("ix_license_activation_license_time", table_name="license_activation")
    op.drop_table("license_activation")

    op.drop_index("ix_device_product_registered_at", table_name="device")
    op.drop_table("device")

    op.drop_index("ix_license_expires_at", table_name="license")
    op.drop_index("ix_license_product_status", table_name="license")
    op.drop_table("license")
