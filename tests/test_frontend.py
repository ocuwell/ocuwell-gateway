from __future__ import annotations

from apps.main import UI_DIR, UI_SRC_DIR, app, frontend_redirect


def test_release_ui_static_files_are_registered() -> None:
    assert UI_DIR.joinpath("index.html").is_file()
    package_json = UI_SRC_DIR.joinpath("package.json").read_text(encoding="utf-8")
    assert "react" in package_json
    assert "vite" in package_json
    assert "lucide-react" in package_json
    assert "qrcode" in package_json
    assert "@zxing/browser" in package_json
    assert "jsqr" in package_json
    app_source = UI_SRC_DIR.joinpath("src", "App.tsx").read_text(encoding="utf-8")
    assert "/v1/client/licenses/activate-offline/license-file" in app_source
    assert "/v1/client/licenses/deactivate-offline/request-file" in app_source
    assert "const QR_CHUNK_SIZE = 1065" in app_source
    assert "const QR_MAX_CHUNKS = 4" in app_source
    assert "chunks.length === QR_MAX_CHUNKS" in app_source
    assert "Array.from({ length: QR_MAX_CHUNKS }" in app_source
    assert "license_file_long_code" not in app_source
    assert str(app.url_path_for("ui", path="/")) == "/ui/"


def test_frontend_redirect_points_to_release_ui() -> None:
    response = frontend_redirect()

    assert response.headers["location"] == "/ui/"
