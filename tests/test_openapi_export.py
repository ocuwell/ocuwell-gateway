from __future__ import annotations

import json

from scripts.export_openapi import export_openapi


def test_export_openapi_writes_schema(tmp_path) -> None:
    output_path = tmp_path / "openapi.json"

    written_path = export_openapi(output_path)

    assert written_path == output_path
    document = json.loads(output_path.read_text(encoding="utf-8"))
    assert document["info"]["title"] == "Ocuwell Gateway API"
    assert document["info"]["version"] == "0.1.0"
    assert "/health" in document["paths"]
    assert "/v1/client/licenses/activate-offline/license-file" in document["paths"]
    assert "/v1/client/licenses/deactivate-offline/request-file" in document["paths"]
