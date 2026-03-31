from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from internal.models import (
    AuditLog,
    Device,
    License,
    LicenseActivation,
    LicenseDeactivation,
    LicenseRevocation,
)


class LicensingError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _generate_license_key() -> str:
    return f"OCW-{uuid4().hex[:8].upper()}-{uuid4().hex[:8].upper()}"


def _record_audit_log(
    db: Session,
    *,
    event_type: str,
    target_type: str,
    target_id: str | None,
    status: str | None,
    actor_id: str | None = None,
    actor_type: str | None = None,
    correlation_id: str | None = None,
    event_data: dict | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        id=str(uuid4()),
        event_type=event_type,
        actor_id=actor_id,
        actor_type=actor_type,
        target_type=target_type,
        target_id=target_id,
        status=status,
        correlation_id=correlation_id,
        event_data=event_data or {},
        created_at=_now_utc(),
    )
    db.add(audit_log)
    return audit_log


def _license_is_expired(license_record: License, now_utc: datetime | None = None) -> bool:
    if license_record.expires_at is None:
        return False
    comparison_time = now_utc or _now_utc()
    return license_record.expires_at <= comparison_time


def _assert_license_usable(license_record: License) -> None:
    if license_record.status == "revoked" or not license_record.is_active:
        raise LicensingError(
            "License is not active.",
            code="license_inactive",
            status_code=409,
        )
    if _license_is_expired(license_record):
        if license_record.status != "expired":
            license_record.status = "expired"
            license_record.is_active = False
        raise LicensingError(
            "License has expired.",
            code="license_expired",
            status_code=409,
        )


def create_license(db: Session, payload: dict) -> License:
    license_record = License(
        id=str(uuid4()),
        license_key=_generate_license_key(),
        product_id=str(payload["product_id"]),
        product_version=payload.get("product_version"),
        issued_to=payload.get("issued_to"),
        issued_at=_now_utc(),
        expires_at=payload.get("expires_at"),
        status="active",
        is_active=True,
        created_at=_now_utc(),
    )
    db.add(license_record)
    _record_audit_log(
        db,
        event_type="license.created",
        target_type="license",
        target_id=license_record.id,
        status="success",
        event_data={
            "product_id": license_record.product_id,
            "product_version": license_record.product_version,
            "issued_to": license_record.issued_to,
        },
    )
    db.commit()
    db.refresh(license_record)
    return license_record


def get_license(db: Session, license_id: str) -> License | None:
    return db.get(License, license_id)


def get_license_by_key(db: Session, license_key: str, product_id: str) -> License | None:
    stmt = select(License).where(
        License.license_key == license_key,
        License.product_id == product_id,
    )
    return db.scalar(stmt)


def _get_device(db: Session, product_id: str, device_id: str) -> Device | None:
    stmt = select(Device).where(
        Device.product_id == product_id,
        Device.device_id == device_id,
    )
    return db.scalar(stmt)


def _get_or_create_device(
    db: Session,
    *,
    product_id: str,
    device_id: str,
    product_version: str | None,
) -> Device:
    device = _get_device(db, product_id, device_id)
    if device is not None:
        if product_version is not None and not device.product_version:
            device.product_version = product_version
        return device

    device = Device(
        id=str(uuid4()),
        device_id=device_id,
        product_id=product_id,
        product_version=product_version,
        registered_at=_now_utc(),
        created_at=_now_utc(),
    )
    db.add(device)
    db.flush()
    return device


def _active_activation_stmt(license_id: str, device_row_id: str) -> Select[tuple[LicenseActivation]]:
    deactivation_exists = (
        select(LicenseDeactivation.id)
        .where(
            LicenseDeactivation.license_id == license_id,
            LicenseDeactivation.device_id == device_row_id,
            LicenseDeactivation.deactivated_at >= LicenseActivation.activated_at,
        )
        .exists()
    )
    return (
        select(LicenseActivation)
        .where(
            LicenseActivation.license_id == license_id,
            LicenseActivation.device_id == device_row_id,
            ~deactivation_exists,
        )
        .order_by(LicenseActivation.activated_at.desc())
    )


def activate_license(
    db: Session,
    *,
    license_key: str,
    product_id: str,
    device_id: str,
    product_version: str | None,
    source: str,
) -> LicenseActivation:
    license_record = get_license_by_key(db, license_key, product_id)
    if license_record is None:
        raise LicensingError(
            "License not found for product.",
            code="license_not_found",
            status_code=404,
        )

    try:
        _assert_license_usable(license_record)
    except LicensingError:
        db.commit()
        raise
    device = _get_or_create_device(
        db,
        product_id=product_id,
        device_id=device_id,
        product_version=product_version,
    )

    existing_activation = db.scalar(_active_activation_stmt(license_record.id, device.id))
    if existing_activation is not None:
        return existing_activation

    activation = LicenseActivation(
        id=str(uuid4()),
        license_id=license_record.id,
        device_id=device.id,
        activated_at=_now_utc(),
        source=source,
        created_at=_now_utc(),
    )
    db.add(activation)
    _record_audit_log(
        db,
        event_type="license.activated",
        target_type="license",
        target_id=license_record.id,
        status="success",
        actor_id=device.device_id,
        actor_type="device",
        event_data={"device_id": device.device_id, "source": source},
    )
    db.commit()
    db.refresh(activation)
    return activation


def validate_license(
    db: Session,
    *,
    license_key: str,
    product_id: str,
    device_id: str | None,
) -> dict[str, object]:
    license_record = get_license_by_key(db, license_key, product_id)
    if license_record is None:
        raise LicensingError(
            "License not found for product.",
            code="license_not_found",
            status_code=404,
        )

    device_registered = False
    effective_status = license_record.status
    effective_is_active = license_record.is_active
    is_valid = effective_status == "active" and effective_is_active

    if _license_is_expired(license_record):
        license_record.status = "expired"
        license_record.is_active = False
        effective_status = "expired"
        effective_is_active = False
        is_valid = False

    if device_id is not None:
        device = _get_device(db, product_id, device_id)
        if device is not None:
            device_registered = db.scalar(
                select(LicenseActivation.id)
                .where(
                    LicenseActivation.license_id == license_record.id,
                    LicenseActivation.device_id == device.id,
                )
                .limit(1)
            ) is not None
            if not device_registered:
                is_valid = False
        else:
            is_valid = False

    db.commit()
    return {
        "license_id": license_record.id,
        "product_id": license_record.product_id,
        "is_valid": is_valid,
        "status": effective_status,
        "is_active": effective_is_active,
        "expires_at": license_record.expires_at,
        "device_registered": device_registered,
    }


def deactivate_license(
    db: Session,
    *,
    license_key: str,
    product_id: str,
    device_id: str | None,
    reason: str | None,
    source: str,
) -> LicenseDeactivation:
    license_record = get_license_by_key(db, license_key, product_id)
    if license_record is None:
        raise LicensingError(
            "License not found for product.",
            code="license_not_found",
            status_code=404,
        )

    device_row = _get_device(db, product_id, device_id) if device_id is not None else None
    if device_id is not None and device_row is None:
        raise LicensingError(
            "Device not found for product.",
            code="device_not_found",
            status_code=404,
        )

    deactivation = LicenseDeactivation(
        id=str(uuid4()),
        license_id=license_record.id,
        device_id=device_row.id if device_row is not None else None,
        deactivated_at=_now_utc(),
        reason=reason,
        source=source,
        created_at=_now_utc(),
    )
    db.add(deactivation)
    _record_audit_log(
        db,
        event_type="license.deactivated",
        target_type="license",
        target_id=license_record.id,
        status="success",
        actor_id=device_id,
        actor_type="device" if device_id is not None else None,
        event_data={"device_id": device_id, "reason": reason, "source": source},
    )
    db.commit()
    db.refresh(deactivation)
    return deactivation


def revoke_license(
    db: Session,
    *,
    license_id: str,
    reason: str | None,
    revoked_by: str | None,
) -> tuple[License, LicenseRevocation]:
    license_record = get_license(db, license_id)
    if license_record is None:
        raise LicensingError(
            "License not found.",
            code="license_not_found",
            status_code=404,
        )
    if license_record.status == "revoked":
        raise LicensingError(
            "License is already revoked.",
            code="license_already_revoked",
            status_code=409,
        )

    license_record.status = "revoked"
    license_record.is_active = False
    revocation = LicenseRevocation(
        id=str(uuid4()),
        license_id=license_record.id,
        revoked_at=_now_utc(),
        reason=reason,
        revoked_by=revoked_by,
        created_at=_now_utc(),
    )
    db.add(revocation)
    _record_audit_log(
        db,
        event_type="license.revoked",
        target_type="license",
        target_id=license_record.id,
        status="success",
        actor_id=revoked_by,
        actor_type="admin" if revoked_by is not None else None,
        event_data={"reason": reason},
    )
    db.commit()
    db.refresh(license_record)
    db.refresh(revocation)
    return license_record, revocation


def list_license_activations(db: Session, license_id: str) -> list[LicenseActivation]:
    stmt = (
        select(LicenseActivation)
        .where(LicenseActivation.license_id == license_id)
        .order_by(LicenseActivation.activated_at.desc())
    )
    return list(db.scalars(stmt).all())


def list_audit_logs(db: Session, license_id: str | None = None) -> list[AuditLog]:
    stmt = select(AuditLog)
    if license_id is not None:
        stmt = stmt.where(
            AuditLog.target_type == "license",
            AuditLog.target_id == license_id,
        )
    stmt = stmt.order_by(AuditLog.created_at.desc())
    return list(db.scalars(stmt).all())


def sync_upstream(
    db: Session,
    *,
    actor_id: str | None,
    correlation_id: str | None,
    payload: dict,
) -> AuditLog:
    audit_log = _record_audit_log(
        db,
        event_type="licensing.sync_upstream",
        target_type="licensing",
        target_id=None,
        status="accepted",
        actor_id=actor_id,
        actor_type="internal",
        correlation_id=correlation_id,
        event_data=payload,
    )
    db.commit()
    db.refresh(audit_log)
    return audit_log


def reconcile_licenses(
    db: Session,
    *,
    actor_id: str | None,
    correlation_id: str | None,
    payload: dict,
) -> AuditLog:
    audit_log = _record_audit_log(
        db,
        event_type="licensing.reconcile",
        target_type="licensing",
        target_id=None,
        status="accepted",
        actor_id=actor_id,
        actor_type="internal",
        correlation_id=correlation_id,
        event_data=payload,
    )
    db.commit()
    db.refresh(audit_log)
    return audit_log


def revoke_device(
    db: Session,
    *,
    product_id: str,
    device_id: str,
    reason: str | None,
    actor_id: str | None,
    correlation_id: str | None,
) -> list[LicenseDeactivation]:
    device = _get_device(db, product_id, device_id)
    if device is None:
        raise LicensingError(
            "Device not found for product.",
            code="device_not_found",
            status_code=404,
        )

    active_activations = list(
        db.scalars(
            select(LicenseActivation).where(
                LicenseActivation.device_id == device.id,
                ~select(LicenseDeactivation.id)
                .where(
                    LicenseDeactivation.license_id == LicenseActivation.license_id,
                    or_(
                        LicenseDeactivation.device_id == device.id,
                        LicenseDeactivation.device_id.is_(None),
                    ),
                    LicenseDeactivation.deactivated_at >= LicenseActivation.activated_at,
                )
                .exists(),
            )
        ).all()
    )

    deactivations: list[LicenseDeactivation] = []
    for activation in active_activations:
        deactivation = LicenseDeactivation(
            id=str(uuid4()),
            license_id=activation.license_id,
            device_id=device.id,
            deactivated_at=_now_utc(),
            reason=reason,
            source="internal",
            created_at=_now_utc(),
        )
        db.add(deactivation)
        deactivations.append(deactivation)

    _record_audit_log(
        db,
        event_type="device.revoked",
        target_type="device",
        target_id=device.id,
        status="success",
        actor_id=actor_id,
        actor_type="internal" if actor_id is not None else None,
        correlation_id=correlation_id,
        event_data={"product_id": product_id, "device_id": device_id, "reason": reason},
    )
    db.commit()
    for deactivation in deactivations:
        db.refresh(deactivation)
    return deactivations
