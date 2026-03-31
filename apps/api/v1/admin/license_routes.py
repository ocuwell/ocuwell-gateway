from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.schema import (
    AuditLogRecord,
    LicenseActivationRecord,
    LicenseCreate,
    LicenseRecord,
    LicenseRevocationRecord,
    LicenseRevocationRequest,
)
from internal.db import get_db
from internal.license_store import (
    LicensingError,
    create_license,
    get_license,
    list_audit_logs,
    list_license_activations,
    revoke_license,
)
from internal.product_store import get_product

admin_license_router = APIRouter(prefix="/licenses", tags=["v1-admin-licenses"])


def _raise_http_from_error(exc: LicensingError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@admin_license_router.post("", response_model=LicenseRecord, status_code=status.HTTP_201_CREATED)
def create_license_endpoint(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
) -> LicenseRecord:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    created = create_license(db, payload.model_dump())
    return LicenseRecord.model_validate(created)


@admin_license_router.get("/audit-logs", response_model=list[AuditLogRecord])
def list_audit_logs_endpoint(
    license_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AuditLogRecord]:
    records = list_audit_logs(db, str(license_id) if license_id is not None else None)
    return [AuditLogRecord.model_validate(record) for record in records]


@admin_license_router.get("/{license_id}", response_model=LicenseRecord)
def get_license_endpoint(
    license_id: UUID,
    db: Session = Depends(get_db),
) -> LicenseRecord:
    license_record = get_license(db, str(license_id))
    if license_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found.")
    return LicenseRecord.model_validate(license_record)


@admin_license_router.post(
    "/{license_id}/revoke",
    response_model=LicenseRevocationRecord,
    status_code=status.HTTP_201_CREATED,
)
def revoke_license_endpoint(
    license_id: UUID,
    payload: LicenseRevocationRequest,
    db: Session = Depends(get_db),
) -> LicenseRevocationRecord:
    try:
        _, revocation = revoke_license(
            db,
            license_id=str(license_id),
            reason=payload.reason,
            revoked_by=payload.revoked_by,
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return LicenseRevocationRecord.model_validate(revocation)


@admin_license_router.get("/{license_id}/activations", response_model=list[LicenseActivationRecord])
def list_license_activations_endpoint(
    license_id: UUID,
    db: Session = Depends(get_db),
) -> list[LicenseActivationRecord]:
    if get_license(db, str(license_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found.")
    activations = list_license_activations(db, str(license_id))
    return [LicenseActivationRecord.model_validate(record) for record in activations]
