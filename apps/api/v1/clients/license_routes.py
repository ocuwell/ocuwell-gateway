from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.schema import (
    LicenseActivationRecord,
    LicenseActivationRequest,
    LicenseDeactivationRecord,
    LicenseDeactivationRequest,
    LicenseSpringDeactivationRequest,
    LicenseSpringDeactivationResponse,
    LicenseValidationRequest,
    LicenseValidationResult,
    OfflineActivationFileRequest,
    OfflineActivationFileResponse,
    OfflineDeactivationFileRequest,
)
from internal.db import get_db
from internal.license_store import (
    LicensingError,
    activate_license,
    deactivate_license,
    validate_license,
)
from internal.licensespring_gateway import (
    LicenseSpringGatewayError,
    create_licensespring_offline_license_file,
    deactivate_licensespring_license,
    resolve_desktop_activation_request,
    resolve_desktop_deactivation_request,
)
from internal.product_store import get_product

client_license_router = APIRouter(prefix="/licenses", tags=["v1-client-licenses"])


def _raise_http_from_error(exc: LicensingError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@client_license_router.post(
    "/activate-online",
    response_model=LicenseActivationRecord,
    status_code=status.HTTP_201_CREATED,
)
def activate_online(
    payload: LicenseActivationRequest,
    db: Session = Depends(get_db),
) -> LicenseActivationRecord:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    try:
        activation = activate_license(
            db,
            license_key=payload.license_key,
            product_id=str(payload.product_id),
            device_id=payload.device_id,
            product_version=payload.product_version,
            source="client",
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return LicenseActivationRecord.model_validate(activation)


@client_license_router.post(
    "/activate-offline/request",
    response_model=LicenseValidationResult,
)
def activate_offline_request(
    payload: LicenseValidationRequest,
    db: Session = Depends(get_db),
) -> LicenseValidationResult:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    try:
        validation = validate_license(
            db,
            license_key=payload.license_key,
            product_id=str(payload.product_id),
            device_id=payload.device_id,
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return LicenseValidationResult.model_validate(validation)


@client_license_router.post(
    "/activate-offline/license-file",
    response_model=OfflineActivationFileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_offline_license_file(
    payload: OfflineActivationFileRequest,
) -> OfflineActivationFileResponse:
    try:
        activation_request = resolve_desktop_activation_request(
            activation_request=payload.activation_request,
            encoded_request=payload.encoded_request,
        )
        license_file = create_licensespring_offline_license_file(activation_request)
    except LicenseSpringGatewayError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return OfflineActivationFileResponse(**license_file)


@client_license_router.post(
    "/deactivate-licensespring",
    response_model=LicenseSpringDeactivationResponse,
)
def deactivate_licensespring_endpoint(
    payload: LicenseSpringDeactivationRequest,
) -> LicenseSpringDeactivationResponse:
    try:
        result = deactivate_licensespring_license(payload.model_dump())
    except LicenseSpringGatewayError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return LicenseSpringDeactivationResponse(**result)


@client_license_router.post(
    "/deactivate-offline/request-file",
    response_model=LicenseSpringDeactivationResponse,
)
def deactivate_offline_request_file(
    payload: OfflineDeactivationFileRequest,
) -> LicenseSpringDeactivationResponse:
    try:
        deactivation_request = resolve_desktop_deactivation_request(
            deactivation_request=payload.deactivation_request,
            encoded_request=payload.encoded_request,
        )
        result = deactivate_licensespring_license(deactivation_request)
    except LicenseSpringGatewayError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return LicenseSpringDeactivationResponse(**result)


@client_license_router.post(
    "/activate-offline/confirm",
    response_model=LicenseActivationRecord,
    status_code=status.HTTP_201_CREATED,
)
def activate_offline_confirm(
    payload: LicenseActivationRequest,
    db: Session = Depends(get_db),
) -> LicenseActivationRecord:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    try:
        activation = activate_license(
            db,
            license_key=payload.license_key,
            product_id=str(payload.product_id),
            device_id=payload.device_id,
            product_version=payload.product_version,
            source="offline",
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return LicenseActivationRecord.model_validate(activation)


@client_license_router.post("/validate", response_model=LicenseValidationResult)
def validate_license_endpoint(
    payload: LicenseValidationRequest,
    db: Session = Depends(get_db),
) -> LicenseValidationResult:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    try:
        validation = validate_license(
            db,
            license_key=payload.license_key,
            product_id=str(payload.product_id),
            device_id=payload.device_id,
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return LicenseValidationResult.model_validate(validation)


@client_license_router.post(
    "/deactivate",
    response_model=LicenseDeactivationRecord,
    status_code=status.HTTP_201_CREATED,
)
def deactivate_license_endpoint(
    payload: LicenseDeactivationRequest,
    db: Session = Depends(get_db),
) -> LicenseDeactivationRecord:
    if get_product(db, str(payload.product_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    try:
        deactivation = deactivate_license(
            db,
            license_key=payload.license_key,
            product_id=str(payload.product_id),
            device_id=payload.device_id,
            reason=payload.reason,
            source="client",
        )
    except LicensingError as exc:
        _raise_http_from_error(exc)
    return LicenseDeactivationRecord.model_validate(deactivation)
