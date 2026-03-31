from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)


class ProductRecord(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class ProductAmend(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)


class ProductInstallerCreate(BaseModel):
    version: str = Field(min_length=1, max_length=64)
    platform: str = Field(min_length=1, max_length=32)
    blob_url: str = Field(min_length=1, max_length=2048)
    file_name: str = Field(min_length=1, max_length=255)
    checksum_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    file_size_bytes: int | None = Field(default=None, ge=0)
    is_latest: bool = False


class ProductInstallerRecord(ProductInstallerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    created_at: datetime


class ClickwrapAcceptanceCreate(BaseModel):
    agreement_id: str = Field(min_length=1, max_length=255)
    agreement_version: str = Field(min_length=1, max_length=64)
    decision: Literal["accept", "decline"]
    product_id: UUID | None = None
    product_version: str | None = Field(default=None, max_length=64)
    accepted_by: str = Field(min_length=1, max_length=255)
    accepted_at: datetime
    context: dict[str, Any] = Field(default_factory=dict)


class ClickwrapAcceptanceRecord(ClickwrapAcceptanceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ip_address: str | None = None
    user_agent: str | None = None
    recorded_at: datetime


class LicenseCreate(BaseModel):
    product_id: UUID
    product_version: str | None = Field(default=None, max_length=64)
    issued_to: str | None = Field(default=None, max_length=255)
    expires_at: datetime | None = None


class LicenseRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    license_key: str = Field(min_length=1, max_length=255)
    product_id: UUID
    product_version: str | None = None
    issued_to: str | None = None
    issued_at: datetime
    expires_at: datetime | None = None
    status: str = Field(min_length=1, max_length=32)
    is_active: bool
    created_at: datetime


class LicenseActivationRequest(BaseModel):
    license_key: str = Field(min_length=1, max_length=255)
    product_id: UUID
    device_id: str = Field(min_length=1, max_length=255)
    product_version: str | None = Field(default=None, max_length=64)


class LicenseValidationRequest(BaseModel):
    license_key: str = Field(min_length=1, max_length=255)
    product_id: UUID
    device_id: str | None = Field(default=None, min_length=1, max_length=255)


class LicenseDeactivationRequest(BaseModel):
    license_key: str = Field(min_length=1, max_length=255)
    product_id: UUID
    device_id: str | None = Field(default=None, min_length=1, max_length=255)
    reason: str | None = Field(default=None, max_length=255)


class LicenseActivationRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    license_id: UUID
    device_id: UUID
    activated_at: datetime
    source: str = Field(min_length=1, max_length=32)
    created_at: datetime


class LicenseDeactivationRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    license_id: UUID
    device_id: UUID | None = None
    deactivated_at: datetime
    reason: str | None = None
    source: str = Field(min_length=1, max_length=32)
    created_at: datetime


class LicenseRevocationRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)
    revoked_by: str | None = Field(default=None, max_length=255)


class LicenseRevocationRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    license_id: UUID
    revoked_at: datetime
    reason: str | None = None
    revoked_by: str | None = None
    created_at: datetime


class LicenseValidationResult(BaseModel):
    license_id: UUID
    product_id: UUID
    is_valid: bool
    status: str = Field(min_length=1, max_length=32)
    is_active: bool
    expires_at: datetime | None = None
    device_registered: bool


class AuditLogRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str = Field(min_length=1, max_length=255)
    actor_id: str | None = None
    actor_type: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    status: str | None = None
    correlation_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    event_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class InternalSyncRequest(BaseModel):
    actor_id: str | None = Field(default=None, max_length=255)
    correlation_id: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class InternalReconcileRequest(BaseModel):
    actor_id: str | None = Field(default=None, max_length=255)
    correlation_id: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class InternalDeviceRevokeRequest(BaseModel):
    product_id: UUID
    device_id: str = Field(min_length=1, max_length=255)
    reason: str | None = Field(default=None, max_length=255)
    actor_id: str | None = Field(default=None, max_length=255)
    correlation_id: str | None = Field(default=None, max_length=64)
