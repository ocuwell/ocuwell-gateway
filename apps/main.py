

from fastapi import FastAPI

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
