# Ocuwell Gateway

FastAPI gateway for:
- Clickwrap decision tracking
- Product and installer metadata management
- Licensing issuance, activation, validation, deactivation, and revocation

## Prerequisites

- Python 3.10+
- MySQL (local or Azure Database for MySQL)

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
# Edit .env and set DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD

# 4) Run migrations
alembic upgrade head

# 5) Start the API
uvicorn apps.main:app --reload --host 0.0.0.0 --port 8000
```

## Verify

- Health check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`

## Production Readiness

- Production gate checklist: `docs/production-gate.md`

## Main Endpoints

- `POST /v1/client/clickwrap/acceptances`
- `GET /v1/client/clickwrap/acceptances/{acceptance_id}`
- `POST /v1/client/licenses/activate-online`
- `POST /v1/client/licenses/activate-offline/request`
- `POST /v1/client/licenses/activate-offline/confirm`
- `POST /v1/client/licenses/validate`
- `POST /v1/client/licenses/deactivate`
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

## Clickwrap Payload

`POST /v1/client/clickwrap/acceptances` accepts a simple decision payload with:
- `agreement_id`
- `agreement_version`
- `decision`: `accept` or `decline`
- `accepted_by`
- `accepted_at`

The gateway records `ip_address` and `user_agent` from the incoming request instead of accepting those fields from the client payload.
