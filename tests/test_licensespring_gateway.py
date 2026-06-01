from __future__ import annotations

import base64
import json

import pytest

from internal.licensespring_gateway import (
    LicenseSpringConfigError,
    LicenseSpringSettings,
    OfflineActivationRequestError,
    create_licensespring_offline_license_file,
    deactivate_licensespring_license,
    decode_desktop_activation_request,
    decode_desktop_deactivation_request,
    load_licensespring_settings,
    resolve_desktop_activation_request,
    resolve_desktop_deactivation_request,
)


def make_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "schema_version": 1,
        "request_type": "activation",
        "request_id": "request-1",
        "created_at": "2026-05-28T13:30:00+00:00",
        "license_key": "TEST-LICENSE-1234",
        "hardware_id": "HWID-9999",
        "product_code": "ocumap",
        "app_version": "1.0.0",
    }
    request.update(overrides)
    return request


def make_deactivation_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "schema_version": 1,
        "request_type": "deactivation",
        "request_id": "deactivate-1",
        "created_at": "2026-05-28T13:30:00+00:00",
        "license_key": "TEST-LICENSE-1234",
        "hardware_id": "HWID-9999",
        "product_code": "ocumap",
        "app_version": "1.0.0",
    }
    request.update(overrides)
    return request


def encode_request(request: dict[str, object]) -> str:
    payload = json.dumps(request, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def test_decodes_neutral_desktop_request() -> None:
    request = make_request()

    assert decode_desktop_activation_request(encode_request(request)) == request


def test_decodes_neutral_desktop_deactivation_request() -> None:
    request = make_deactivation_request()

    assert decode_desktop_deactivation_request(encode_request(request)) == request


def test_resolve_requires_exactly_one_request_shape() -> None:
    with pytest.raises(OfflineActivationRequestError, match="exactly one"):
        resolve_desktop_activation_request(activation_request=None, encoded_request=None)
    with pytest.raises(OfflineActivationRequestError, match="exactly one"):
        resolve_desktop_activation_request(
            activation_request=make_request(),
            encoded_request=encode_request(make_request()),
        )


def test_resolve_deactivation_requires_exactly_one_request_shape() -> None:
    with pytest.raises(OfflineActivationRequestError, match="exactly one"):
        resolve_desktop_deactivation_request(deactivation_request=None, encoded_request=None)
    with pytest.raises(OfflineActivationRequestError, match="exactly one"):
        resolve_desktop_deactivation_request(
            deactivation_request=make_deactivation_request(),
            encoded_request=encode_request(make_deactivation_request()),
        )


@pytest.mark.parametrize("field_name", ["api_key", "shared_key", "signature", "authorization"])
def test_rejects_licensespring_secrets_from_client(field_name: str) -> None:
    request = make_request(**{field_name: "client-value"})

    with pytest.raises(OfflineActivationRequestError, match="forbidden client fields"):
        decode_desktop_activation_request(encode_request(request))


@pytest.mark.parametrize("field_name", ["api_key", "shared_key", "signature", "authorization"])
def test_rejects_licensespring_secrets_from_deactivation_request(field_name: str) -> None:
    request = make_deactivation_request(**{field_name: "client-value"})

    with pytest.raises(OfflineActivationRequestError, match="forbidden client fields"):
        decode_desktop_deactivation_request(encode_request(request))


def test_load_settings_requires_server_side_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LICENSESPRING_API_KEY", raising=False)
    monkeypatch.delenv("LICENSESPRING_SHARED_KEY", raising=False)

    with pytest.raises(LicenseSpringConfigError):
        load_licensespring_settings()


def test_create_offline_license_file_uses_server_side_credentials() -> None:
    captured: dict[str, object] = {}

    class FakeAPIClient:
        def __init__(self, **kwargs: object) -> None:
            captured["init"] = kwargs

        def activate_offline_dump(self, **kwargs: object) -> str:
            captured["offline_dump"] = kwargs
            return "SIGNED-OFFLINE-REQUEST"

        def activate_offline(self, data: str) -> dict[str, object]:
            captured["activate_offline"] = data
            return {
                "license_key": "TEST-LICENSE-1234",
                "license_signature": "legacy-signature",
                "license_signature_v2": "signature-v2",
            }

    result = create_licensespring_offline_license_file(
        make_request(),
        settings=LicenseSpringSettings(
            api_key="SERVER_API_KEY",
            shared_key="SERVER_SHARED_KEY",
            allowed_product_code="ocumap",
        ),
        api_client_factory=FakeAPIClient,
    )

    assert captured["init"] == {
        "api_key": "SERVER_API_KEY",
        "shared_key": "SERVER_SHARED_KEY",
        "hardware_id_provider": captured["init"]["hardware_id_provider"],
        "api_protocol": "https",
        "api_domain": "api.licensespring.com",
        "api_version": "v4",
    }
    provider = captured["init"]["hardware_id_provider"]()
    assert provider.get_request_id() == "request-1"
    assert captured["offline_dump"] == {
        "product": "ocumap",
        "hardware_id": "HWID-9999",
        "license_key": "TEST-LICENSE-1234",
        "app_ver": "1.0.0",
        "os_ver": "",
        "hostname": "",
        "ip": "",
        "is_vm": False,
        "vm_info": "",
        "mac_address": "",
        "variables": None,
    }
    assert captured["activate_offline"] == "SIGNED-OFFLINE-REQUEST"
    decoded_license = json.loads(base64.b64decode(result["license_file_content"]).decode("utf-8"))
    assert decoded_license["license_signature_v2"] == "signature-v2"
    assert result["license_file_content"].endswith("=")
    assert "license_file_content_b64" not in result
    long_code = result["license_file_long_code"].replace("-", "")
    long_code += "=" * (-len(long_code) % 8)
    assert base64.b32decode(long_code).decode("ascii") == result["license_file_content"]
    assert result["request_id"] == "request-1"
    assert result["file_name"] == "licensespring-offline.lic"


def test_product_code_can_be_locked_to_server_config() -> None:
    with pytest.raises(OfflineActivationRequestError, match="not allowed"):
        create_licensespring_offline_license_file(
            make_request(product_code="other-product"),
            settings=LicenseSpringSettings(
                api_key="SERVER_API_KEY",
                shared_key="SERVER_SHARED_KEY",
                allowed_product_code="ocumap",
            ),
            api_client_factory=object,
        )


def test_deactivate_license_uses_server_side_credentials() -> None:
    captured: dict[str, object] = {}

    class FakeAPIClient:
        def __init__(self, **kwargs: object) -> None:
            captured["init"] = kwargs

        def deactivate_license(self, **kwargs: object) -> str:
            captured["deactivate_license"] = kwargs
            return "ok"

    result = deactivate_licensespring_license(
        {
            "request_id": "deactivate-1",
            "license_key": "TEST-LICENSE-1234",
            "hardware_id": "HWID-9999",
            "product_code": "ocumap",
        },
        settings=LicenseSpringSettings(
            api_key="SERVER_API_KEY",
            shared_key="SERVER_SHARED_KEY",
            allowed_product_code="ocumap",
        ),
        api_client_factory=FakeAPIClient,
    )

    assert result == {"ok": True, "request_id": "deactivate-1"}
    assert captured["init"] == {
        "api_key": "SERVER_API_KEY",
        "shared_key": "SERVER_SHARED_KEY",
        "api_protocol": "https",
        "api_domain": "api.licensespring.com",
        "api_version": "v4",
    }
    assert captured["deactivate_license"] == {
        "product": "ocumap",
        "hardware_id": "HWID-9999",
        "license_key": "TEST-LICENSE-1234",
    }
