from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = 1
REQUEST_TYPE_ACTIVATION = "activation"
REQUEST_TYPE_DEACTIVATION = "deactivation"
DEFAULT_LICENSE_FILE_NAME = "licensespring-offline.lic"
FORBIDDEN_CLIENT_FIELDS = {
    "api_key",
    "shared_key",
    "client_id",
    "client_secret",
    "signature",
    "authorization",
}


class LicenseSpringGatewayError(Exception):
    status_code = 500
    public_message = "LicenseSpring gateway error."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)
        self.message = message or self.public_message


class OfflineActivationRequestError(LicenseSpringGatewayError):
    status_code = 400
    public_message = "Offline activation request is invalid."


class LicenseSpringConfigError(LicenseSpringGatewayError):
    status_code = 503
    public_message = "License service is not configured."


class LicenseSpringUpstreamError(LicenseSpringGatewayError):
    status_code = 502
    public_message = "License service rejected the offline activation request."


@dataclass(frozen=True)
class LicenseSpringSettings:
    api_key: str
    shared_key: str
    allowed_product_code: str | None = None
    api_protocol: str = "https"
    api_domain: str = "api.licensespring.com"
    api_version: str = "v4"


class RequestIdHardwareProvider:
    def __init__(self, request_id: str) -> None:
        self._request_id = request_id

    def get_id(self) -> str:
        return ""

    def get_os_ver(self) -> str:
        return ""

    def get_hostname(self) -> str:
        return ""

    def get_ip(self) -> str:
        return ""

    def get_is_vm(self) -> bool:
        return False

    def get_vm_info(self) -> str:
        return ""

    def get_mac_address(self) -> str:
        return ""

    def get_request_id(self) -> str:
        return self._request_id


def load_licensespring_settings() -> LicenseSpringSettings:
    api_key = os.getenv("LICENSESPRING_API_KEY", "").strip()
    shared_key = os.getenv("LICENSESPRING_SHARED_KEY", "").strip()
    if not api_key or not shared_key:
        raise LicenseSpringConfigError("LICENSESPRING_API_KEY and LICENSESPRING_SHARED_KEY are required.")

    allowed_product_code = os.getenv("LICENSESPRING_PRODUCT_CODE", "").strip() or None
    return LicenseSpringSettings(
        api_key=api_key,
        shared_key=shared_key,
        allowed_product_code=allowed_product_code,
        api_protocol=os.getenv("LICENSESPRING_API_PROTOCOL", "https").strip() or "https",
        api_domain=os.getenv("LICENSESPRING_API_DOMAIN", "api.licensespring.com").strip()
        or "api.licensespring.com",
        api_version=os.getenv("LICENSESPRING_API_VERSION", "v4").strip() or "v4",
    )


def decode_desktop_activation_request(encoded_request: str) -> dict[str, Any]:
    try:
        decoded = base64.urlsafe_b64decode(encoded_request.encode("ascii"))
        request = json.loads(decoded.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise OfflineActivationRequestError("activation request is not valid base64 JSON") from exc
    return validate_desktop_activation_request(request)


def validate_desktop_activation_request(request: Mapping[str, Any]) -> dict[str, Any]:
    validated = _validate_desktop_license_request(
        request,
        expected_request_type=REQUEST_TYPE_ACTIVATION,
        label="activation",
    )
    variables = validated.get("variables")
    if variables is not None and not isinstance(variables, Mapping):
        raise OfflineActivationRequestError("variables must be an object when provided")

    return validated


def decode_desktop_deactivation_request(encoded_request: str) -> dict[str, Any]:
    try:
        decoded = base64.urlsafe_b64decode(encoded_request.encode("ascii"))
        request = json.loads(decoded.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise OfflineActivationRequestError("deactivation request is not valid base64 JSON") from exc
    return validate_desktop_deactivation_request(request)


def validate_desktop_deactivation_request(request: Mapping[str, Any]) -> dict[str, Any]:
    return _validate_desktop_license_request(
        request,
        expected_request_type=REQUEST_TYPE_DEACTIVATION,
        label="deactivation",
    )


def _validate_desktop_license_request(
    request: Mapping[str, Any],
    *,
    expected_request_type: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise OfflineActivationRequestError(f"{label} request must be an object")

    lower_keys = {str(key).lower() for key in request.keys()}
    forbidden = sorted(lower_keys.intersection(FORBIDDEN_CLIENT_FIELDS))
    if forbidden:
        raise OfflineActivationRequestError(
            f"{label} request contains forbidden client fields: {', '.join(forbidden)}"
        )

    if request.get("schema_version") != SCHEMA_VERSION:
        raise OfflineActivationRequestError(f"{label} request schema version is not supported")
    if request.get("request_type") != expected_request_type:
        raise OfflineActivationRequestError(f"{label} request type is not supported")

    validated = dict(request)
    for field_name in ("request_id", "created_at", "license_key", "hardware_id", "product_code"):
        value = validated.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise OfflineActivationRequestError(f"{field_name} is required")
        validated[field_name] = value.strip()

    return validated


def resolve_desktop_activation_request(
    *,
    activation_request: Mapping[str, Any] | None,
    encoded_request: str | None,
) -> dict[str, Any]:
    if bool(activation_request) == bool(encoded_request):
        raise OfflineActivationRequestError("Provide exactly one of activation_request or encoded_request.")
    if encoded_request is not None:
        return decode_desktop_activation_request(encoded_request)
    return validate_desktop_activation_request(activation_request or {})


def resolve_desktop_deactivation_request(
    *,
    deactivation_request: Mapping[str, Any] | None,
    encoded_request: str | None,
) -> dict[str, Any]:
    if bool(deactivation_request) == bool(encoded_request):
        raise OfflineActivationRequestError("Provide exactly one of deactivation_request or encoded_request.")
    if encoded_request is not None:
        return decode_desktop_deactivation_request(encoded_request)
    return validate_desktop_deactivation_request(deactivation_request or {})


def create_licensespring_offline_license_file(
    request: Mapping[str, Any],
    *,
    settings: LicenseSpringSettings | None = None,
    api_client_factory: Callable[..., Any] | None = None,
) -> dict[str, str]:
    validated = validate_desktop_activation_request(request)
    settings = settings or load_licensespring_settings()
    if settings.allowed_product_code and validated["product_code"] != settings.allowed_product_code:
        raise OfflineActivationRequestError("activation request product_code is not allowed")

    if api_client_factory is None:
        from licensespring.api import APIClient

        api_client_factory = APIClient

    try:
        api_client = api_client_factory(
            api_key=settings.api_key,
            shared_key=settings.shared_key,
            hardware_id_provider=lambda: RequestIdHardwareProvider(validated["request_id"]),
            api_protocol=settings.api_protocol,
            api_domain=settings.api_domain,
            api_version=settings.api_version,
        )
        signed_request = api_client.activate_offline_dump(
            product=validated["product_code"],
            hardware_id=validated["hardware_id"],
            license_key=validated["license_key"],
            app_ver=validated.get("app_version"),
            os_ver=validated.get("os_ver", ""),
            hostname=validated.get("hostname", ""),
            ip=validated.get("ip", ""),
            is_vm=validated.get("is_vm", False),
            vm_info=validated.get("vm_info", ""),
            mac_address=validated.get("mac_address", ""),
            variables=validated.get("variables"),
        )
        activation_response = api_client.activate_offline(signed_request)
    except LicenseSpringGatewayError:
        raise
    except Exception as exc:
        raise LicenseSpringUpstreamError() from exc

    license_file_content = _encode_license_file_response(activation_response)
    return {
        "request_id": validated["request_id"],
        "file_name": DEFAULT_LICENSE_FILE_NAME,
        "license_file_content": license_file_content,
        "license_file_long_code": _encode_license_file_long_code(license_file_content),
    }


def deactivate_licensespring_license(
    request: Mapping[str, Any],
    *,
    settings: LicenseSpringSettings | None = None,
    api_client_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    validated = validate_desktop_license_reference(request)
    settings = settings or load_licensespring_settings()
    if settings.allowed_product_code and validated["product_code"] != settings.allowed_product_code:
        raise OfflineActivationRequestError("deactivation request product_code is not allowed")

    if api_client_factory is None:
        from licensespring.api import APIClient

        api_client_factory = APIClient

    try:
        api_client = api_client_factory(
            api_key=settings.api_key,
            shared_key=settings.shared_key,
            api_protocol=settings.api_protocol,
            api_domain=settings.api_domain,
            api_version=settings.api_version,
        )
        api_client.deactivate_license(
            product=validated["product_code"],
            hardware_id=validated["hardware_id"],
            license_key=validated["license_key"],
        )
    except Exception as exc:
        raise LicenseSpringUpstreamError() from exc

    return {"ok": True, "request_id": validated.get("request_id")}


def validate_desktop_license_reference(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise OfflineActivationRequestError("deactivation request must be an object")
    lower_keys = {str(key).lower() for key in request.keys()}
    forbidden = sorted(lower_keys.intersection(FORBIDDEN_CLIENT_FIELDS))
    if forbidden:
        raise OfflineActivationRequestError(
            f"deactivation request contains forbidden client fields: {', '.join(forbidden)}"
        )

    validated = dict(request)
    for field_name in ("license_key", "hardware_id", "product_code"):
        value = validated.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise OfflineActivationRequestError(f"{field_name} is required")
        validated[field_name] = value.strip()
    request_id = validated.get("request_id")
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id.strip():
            raise OfflineActivationRequestError("request_id must be text when provided")
        validated["request_id"] = request_id.strip()
    return validated


def _encode_license_file_response(response: Mapping[str, Any]) -> str:
    payload = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


def _encode_license_file_long_code(license_file_content: str) -> str:
    encoded = base64.b32encode(license_file_content.encode("ascii")).decode("ascii").rstrip("=")
    return "-".join(encoded[index:index + 4] for index in range(0, len(encoded), 4))


def redact_desktop_activation_request(request: Mapping[str, Any]) -> dict[str, Any]:
    safe = dict(request)
    for field_name in ("license_key", "hardware_id"):
        value = safe.get(field_name)
        if isinstance(value, str) and value:
            safe[field_name] = f"***{value[-4:]}"
    return safe
