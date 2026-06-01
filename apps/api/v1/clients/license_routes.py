from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from apps.api.schema import (
    LicenseSpringDeactivationRequest,
    LicenseSpringDeactivationResponse,
    OfflineActivationFileRequest,
    OfflineActivationFileResponse,
    OfflineDeactivationFileRequest,
)
from internal.licensespring_gateway import (
    LicenseSpringGatewayError,
    create_licensespring_offline_license_file,
    deactivate_licensespring_license,
    resolve_desktop_activation_request,
    resolve_desktop_deactivation_request,
)

client_license_router = APIRouter(prefix="/licenses", tags=["v1-client-licenses"])


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
