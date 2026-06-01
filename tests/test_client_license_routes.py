from __future__ import annotations

from apps.api.v1.clients import license_routes


def test_client_license_routes_expose_gateway_bridge_only() -> None:
    paths = {(route.path, ",".join(sorted(route.methods))) for route in license_routes.client_license_router.routes}

    assert ("/licenses/activate-offline/license-file", "POST") in paths
    assert ("/licenses/deactivate-licensespring", "POST") in paths
    assert ("/licenses/deactivate-offline/request-file", "POST") in paths

    assert ("/licenses/activate-online", "POST") not in paths
    assert ("/licenses/activate-offline/request", "POST") not in paths
    assert ("/licenses/activate-offline/confirm", "POST") not in paths
    assert ("/licenses/validate", "POST") not in paths
    assert ("/licenses/deactivate", "POST") not in paths
