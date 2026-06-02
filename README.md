# Ocuwell Gateway

FastAPI gateway for:
- Clickwrap decision tracking
- Product and installer metadata management
- LicenseSpring activation and deactivation bridge
- Offline licensing UI for OcuMaps release workflows

## Prerequisites

- Python 3.10+
- MySQL or Azure SQL Database

## Local Setup (PowerShell)

Run from:
`c:\Users\chaya\GitHub\ocuwell-gateway`

```powershell
# 1) Create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# If activation is blocked:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# 2) Install dependencies
python -m pip install -r requirements.txt

# 3) Create local env file (first time only)
Copy-Item .env.example .env
# Edit .env and set either MySQL values or Azure SQL values

# 4) Run migrations
alembic upgrade head

# 5) Start the API
uvicorn apps.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify

- Health check: `http://localhost:8000/health`
- Offline licensing UI: `http://localhost:8000/ui/`
- Swagger UI for development: `http://localhost:8000/docs`
- OpenAPI JSON for development: `http://localhost:8000/openapi.json`

## Release UI

The release offline licensing UI is a Vite React app in `apps/ui`. It is served
by FastAPI at `/ui/`.

```powershell
cd apps\ui
npm install
npm run dev
```

For FastAPI static serving, build the React app first:

```powershell
cd apps\ui
npm run build
cd ..\..
uvicorn apps.main:app --reload --host 0.0.0.0 --port 8000
```

The UI supports activation and deactivation request transfer by file or QR.
Activation responses can be returned to the workstation by downloaded file or
ordered QR handoff.

## Export Swagger Docs

Export the generated OpenAPI document to `docs/openapi.json`:

```powershell
.\.venv\Scripts\python scripts\export_openapi.py
```

Or choose a custom output path:

```powershell
.\.venv\Scripts\python scripts\export_openapi.py --output .tmp\openapi.json
```

## Production Readiness

- Production gate checklist: `docs/production-gate.md`
- SOUP register for vendored frontend libraries: `docs/soup-register.md`

## Main Endpoints

- `POST /v1/client/clickwrap/acceptances`
- `GET /v1/client/clickwrap/acceptances/{acceptance_id}`
- `POST /v1/client/licenses/activate-offline/license-file`
- `POST /v1/client/licenses/deactivate-licensespring`
- `POST /v1/client/licenses/deactivate-offline/request-file`
- `POST /v1/admin/products`
- `GET /v1/admin/products`
- `PATCH /v1/admin/products/{product_id}`
- `POST /v1/admin/products/{product_id}/installers`
- `GET /v1/admin/products/{product_id}/installers`
- `POST /v1/admin/licenses`
- `GET /v1/admin/licenses/{license_id}`
- `POST /v1/admin/licenses/{license_id}/revoke`
- `GET /v1/admin/licenses/{license_id}/activations`
- `GET /v1/admin/licenses/audit-logs`
- `POST /v1/internal/licenses/sync-upstream`
- `POST /v1/internal/licenses/reconcile`
- `POST /v1/internal/licenses/revoke-device`

## Offline Licensing Contract

The desktop app creates `.req` files for offline activation and deactivation.
Those files contain encoded request text and can be uploaded, scanned from a QR
code.

### Activation Response

`POST /v1/client/licenses/activate-offline/license-file` accepts either:

```json
{
  "encoded_request": "base64url-desktop-activation-request"
}
```

or:

```json
{
  "activation_request": {
    "schema_version": 1,
    "request_type": "activation",
    "request_id": "request-id",
    "created_at": "2026-05-29T10:00:00+00:00",
    "license_key": "XXXX-XXXX-XXXX",
    "hardware_id": "device-hardware-id",
    "product_code": "OCUMAP-TST-01"
  }
}
```

Response:

```json
{
  "request_id": "request-id",
  "file_name": "licensespring-offline.lic",
  "license_file_content": "standard-base64-licensespring-response",
  "content_encoding": "licensespring-offline-base64-json",
  "license_file_long_code": "BASE-32MA-NUAL-CODE",
  "long_code_encoding": "base32-ascii-no-padding"
}
```

For downloaded files and QR response content, use only `license_file_content`.
The `.lic` file content must be exactly that base64 text, not the full JSON
wrapper and not decoded JSON. The v1 release UI does not expose manual entry.

For QR response transfer, split `license_file_content` into raw chunks of 1065
characters, with a maximum of 4 chunks. Do not add headers, JSON wrappers, or
chunk metadata to the QR payloads. The OcuMaps workstation combines scanned
chunks in scan order.

### Deactivation Request

`POST /v1/client/licenses/deactivate-offline/request-file` accepts either:

```json
{
  "encoded_request": "base64url-desktop-deactivation-request"
}
```

or:

```json
{
  "deactivation_request": {
    "schema_version": 1,
    "request_type": "deactivation",
    "request_id": "request-id",
    "created_at": "2026-05-29T10:00:00+00:00",
    "license_key": "XXXX-XXXX-XXXX",
    "hardware_id": "device-hardware-id",
    "product_code": "OCUMAP-TST-01"
  }
}
```

Response:

```json
{
  "ok": true,
  "request_id": "request-id"
}
```

There is no deactivation response file to import into the desktop app.

## Clickwrap Payload

`POST /v1/client/clickwrap/acceptances` accepts a simple decision payload with:
- `agreement_id`
- `agreement_version`
- `decision`: `accept` or `decline`
- `accepted_by`
- `accepted_at`

The gateway records `ip_address` and `user_agent` from the incoming request instead of accepting those fields from the client payload.

## Database Backends

The app supports two backend modes through `.env.example`:

- `DB_BACKEND=mysql`
  Uses `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DB_BACKEND=azure_sql`
  Uses `AZURE_SQL_SERVER`, `AZURE_SQL_PORT`, `AZURE_SQL_DATABASE`

You can also bypass both modes with a full `DATABASE_URL`.

For Azure SQL, the default auth mode is Microsoft Entra token auth:
- `AZURE_SQL_AUTH_MODE=entra`
- local development can use Azure CLI / Visual Studio / cached Entra credentials through `DefaultAzureCredential`
- Azure deployment can use Managed Identity with the same code path

There is also a fallback SQL login mode:
- `AZURE_SQL_AUTH_MODE=sql_password`
- requires `AZURE_SQL_USERNAME` and `AZURE_SQL_PASSWORD`

