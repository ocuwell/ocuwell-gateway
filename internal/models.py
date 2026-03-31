from datetime import datetime

from sqlalchemy import (
    BIGINT,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from internal.db import Base


class Product(Base):
    __tablename__ = "product"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    installers: Mapped[list["ProductInstaller"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    # Licensing entities are scoped per product for multi-product support.
    licenses: Mapped[list["License"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    devices: Mapped[list["Device"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductInstaller(Base):
    __tablename__ = "product_installer"
    __table_args__ = (
        Index("ix_product_installer_lookup", "product_id", "platform", "version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    blob_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    product: Mapped["Product"] = relationship(back_populates="installers")


class ClickwrapAcceptance(Base):
    __tablename__ = "clickwrap_acceptance"
    __table_args__ = (
        Index("ix_clickwrap_agreement_version", "agreement_id", "agreement_version"),
        Index("ix_clickwrap_decision_at", "decision", "accepted_at"),
        Index("ix_clickwrap_accepted_by_at", "accepted_by", "accepted_at"),
        Index("ix_clickwrap_product_version", "product_id", "product_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agreement_id: Mapped[str] = mapped_column(String(255), nullable=False)
    agreement_version: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'accept'"))
    product_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("product.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    accepted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class License(Base):
    __tablename__ = "license"
    __table_args__ = (
        Index("ix_license_product_status", "product_id", "status"),
        Index("ix_license_expires_at", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    license_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issued_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Keep status explicit for lifecycle policies (active/revoked/suspended/expired).
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'active'"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    product: Mapped["Product"] = relationship(back_populates="licenses")
    activations: Mapped[list["LicenseActivation"]] = relationship(
        back_populates="license",
        cascade="all, delete-orphan",
    )
    deactivations: Mapped[list["LicenseDeactivation"]] = relationship(
        back_populates="license",
        cascade="all, delete-orphan",
    )
    revocations: Mapped[list["LicenseRevocation"]] = relationship(
        back_populates="license",
        cascade="all, delete-orphan",
    )


class Device(Base):
    __tablename__ = "device"
    __table_args__ = (
        UniqueConstraint("product_id", "device_id", name="uq_device_product_device_id"),
        Index("ix_device_product_registered_at", "product_id", "registered_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # Unique per product, not global, to support the same physical device across products.
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    product: Mapped["Product"] = relationship(back_populates="devices")
    activations: Mapped[list["LicenseActivation"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )
    deactivations: Mapped[list["LicenseDeactivation"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )


class LicenseActivation(Base):
    __tablename__ = "license_activation"
    __table_args__ = (
        Index("ix_license_activation_license_time", "license_id", "activated_at"),
        Index("ix_license_activation_device_time", "device_id", "activated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    license_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("license.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("device.id", ondelete="CASCADE"),
        nullable=False,
    )
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'client'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    license: Mapped["License"] = relationship(back_populates="activations")
    device: Mapped["Device"] = relationship(back_populates="activations")


class LicenseDeactivation(Base):
    __tablename__ = "license_deactivation"
    __table_args__ = (
        Index("ix_license_deactivation_license_time", "license_id", "deactivated_at"),
        Index("ix_license_deactivation_device_time", "device_id", "deactivated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    license_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("license.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("device.id", ondelete="SET NULL"),
        nullable=True,
    )
    deactivated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'client'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    license: Mapped["License"] = relationship(back_populates="deactivations")
    device: Mapped["Device"] = relationship(back_populates="deactivations")


class LicenseRevocation(Base):
    __tablename__ = "license_revocation"
    __table_args__ = (
        Index("ix_license_revocation_license_time", "license_id", "revoked_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    license_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("license.id", ondelete="CASCADE"),
        nullable=False,
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    revoked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    license: Mapped["License"] = relationship(back_populates="revocations")


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_correlation_id", "correlation_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
