

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from apps.api.v1.admin.license_routes import admin_license_router
from apps.api.v1.admin.product_routes import admin_product_router
from apps.api.v1.clients.clickwrap_routes import client_clickwrap_router
from apps.api.v1.clients.license_routes import client_license_router
from apps.api.v1.internal.license_routes import internal_license_router

app = FastAPI(title="Ocuwell Gateway API", version="0.1.0")
app.include_router(client_clickwrap_router, prefix="/v1/client")
app.include_router(client_license_router, prefix="/v1/client")
app.include_router(admin_product_router, prefix="/v1/admin")
app.include_router(admin_license_router, prefix="/v1/admin")
app.include_router(internal_license_router, prefix="/v1/internal")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def frontend_redirect() -> RedirectResponse:
    return RedirectResponse(url="/ui/")


UI_SRC_DIR = Path(__file__).resolve().parent / "ui"
UI_DIST_DIR = UI_SRC_DIR / "dist"
UI_DIR = UI_DIST_DIR if UI_DIST_DIR.joinpath("index.html").is_file() else UI_SRC_DIR
app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")
