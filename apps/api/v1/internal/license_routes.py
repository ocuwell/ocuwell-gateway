from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.schema import (
    AuditLogRecord,
    InternalDeviceRevokeRequest,
    InternalReconcileRequest,
    InternalSyncRequest,
    LicenseDeactivationRecord,
)
from internal.db import get_db
from internal.license_store import (
    LicensingError,
    reconcile_licenses,
    revoke_device,
    sync_upstream,
)
from internal.product_store import get_product

internal_license_router = APIRouter(prefix="/licenses", tags=["v1-internal-licenses"])


def _raise_http_from_error(exc: LicensingError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@internal_license_router.post(
    "/sync-upstream",
    response_model=AuditLogRecord,
    status_code=status.HTTP_202_ACCEPTED,
)
def sync_upstream_endpoint(
    payload: InternalSyncRequest,
    db: Session = Depends(get_db),
) -> AuditLogRecord:
    record = sync_upstream(
        db,
        actor_id=payload.actor_id,
        correlation_id=payload.correlation_id,
        payload=payload.payload,
    )
    return AuditLogRecord.model_validate(record)


@internal_license_router.post(
    "/reconcile",
    response_model=AuditLogRecord,
    status_code=status.HTTP_202_ACCEPTED,
)
def reconcile_endpoint(
    payload: InternalReconcileRequest,
    db: Session = Depends(get_db),
) -> AuditLogRecord:
    record = reconcile_licenses(
        db,
        actor_id=payload.actor_id,
        correlation_id=payload.correlation_id,
        payload=payload.payload,
    )
    return AuditLogRecord.model_validate(record)


@internal_license_router.post(
    "/revoke-device",
    response_model=list[LicenseDeactivationRecord],
    status_code=status.HTTP_201_CREATED,
)
def revoke_device_endpoint(
    payload: InternalDeviceRevokeRequest,
    db: Session = Depends(get_db),
) -> list[LicenseDeactivationRecord]:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    try:
        deactivations = revoke_device(
            db,
            product_id=str(payload.product_id),
            device_id=payload.device_id,
            reason=payload.reason,
            actor_id=payload.actor_id,
            correlation_id=payload.correlation_id,
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return [LicenseDeactivationRecord.model_validate(record) for record in deactivations]
