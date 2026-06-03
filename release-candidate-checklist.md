# OcuWell Gateway Release Candidate Checklist

This checklist covers the gateway service used by OCUMAPS desktop for online and offline licensing.
Use it with `docs/production-gate.md` and `docs/azure-deploy.md`.

## 1. Release Identity And Scope

- [ ] Confirm gateway release version.
- [ ] Confirm source commit SHA.
- [ ] Confirm deployment target: `https://ocuwell-gateway.azurewebsites.net` or the intended staging URL.
- [ ] Confirm release owner and approver.
- [ ] Confirm release scope includes the correct modules:
  - [ ] Clickwrap
  - [ ] Online activation/deactivation
  - [ ] Offline activation/deactivation
  - [ ] Admin/internal license management
  - [ ] Offline licensing UI under `/ui/`
- [ ] Confirm known issues and release-blocking defects are documented.

## 2. Python API Tests And Coverage

- [ ] Install backend dependencies in a clean virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

- [ ] Run the Python test suite.

```powershell
python -m pytest
```

- [ ] Confirm coverage output from `pytest.ini` is reviewed.
- [ ] If licensing or gateway internals changed, run expanded coverage for release-critical modules.

```powershell
python -m pytest tests `
  --cov=apps.api.v1.clients.license_routes `
  --cov=apps.api.v1.admin.license_routes `
  --cov=apps.api.v1.internal.license_routes `
  --cov=internal.licensespring_gateway `
  --cov=internal.license_store `
  --cov=internal.product_store `
  --cov=internal.db `
  --cov-report=term-missing `
  --cov-report=html
```

- [ ] Confirm coverage report is attached or linked for release sign-off.
- [ ] Confirm no meaningful coverage regression in changed modules.
- [ ] Confirm skipped or xfailed tests are understood and documented.

## 3. Gateway API Correctness

- [ ] `/health` returns `200`.
- [ ] Clickwrap acceptance create/read tests pass.
- [ ] Online activation works for a valid license.
- [ ] Online activation rejects invalid, expired, already-used, and activation-limit-reached licenses.
- [ ] Online deactivation works for an activated license.
- [ ] Online deactivation handles invalid or already-deactivated states correctly.
- [ ] Offline activation request file upload returns a valid `.lic` response.
- [ ] Offline activation QR response contract matches the desktop app: exactly 4 ordered raw chunks when QR handoff is used.
- [ ] Offline deactivation request file upload returns success.
- [ ] Invalid offline request payloads are rejected.
- [ ] Tampered request payloads are rejected.
- [ ] Gateway timeout/upstream LicenseSpring failure returns deterministic user-safe errors.
- [ ] Error responses do not expose upstream secrets or sensitive internals.

## 4. Frontend UI Build

The release offline licensing UI is `apps/ui` and is served by FastAPI at `/ui/`.

- [ ] Build the release UI.

```powershell
cd apps\ui
npm ci
npm run build
cd ..\..
```

- [ ] Confirm `apps/ui/dist/index.html` exists.
- [ ] Confirm `/ui/` loads when FastAPI runs.
- [ ] Confirm `/ui/assets/*.js` and `/ui/assets/*.css` return `200` after deployment.
- [ ] Confirm activation request upload works in the UI.
- [ ] Confirm deactivation request upload works in the UI.
- [ ] Confirm downloaded `.lic` response contains only the license file content expected by desktop.
- [ ] Confirm QR response display works for offline activation.
- [ ] If `apps/web` is included in the release, run its build too.

```powershell
cd apps\web
npm ci
npm run build
cd ..\..
```

## 5. OpenAPI And Contract

- [ ] Export OpenAPI docs.

```powershell
.\.venv\Scripts\python scripts\export_openapi.py
```

- [ ] Review diff in `docs/openapi.json`.
- [ ] Confirm desktop-facing routes remain backward compatible.
- [ ] Confirm request/response fields match the desktop offline licensing contract in `README.md`.
- [ ] Confirm no internal/admin-only routes are documented as public client routes by mistake.

## 6. Database And Migration Gate

- [ ] Confirm database backend for release: MySQL or Azure SQL.
- [ ] Confirm required environment variables are set for the target database.
- [ ] Run migrations on a staging clone.

```powershell
alembic upgrade head
```

- [ ] Confirm migrations are idempotent in staging.
- [ ] Confirm rollback plan is documented, even if Alembic downgrade is not used for production rollback.
- [ ] Confirm backup exists before production migration.
- [ ] Confirm restore has been tested for this release or recent release window.
- [ ] Confirm audit records remain append-only.

## 7. Security Gate

Use `docs/production-gate.md` as the source of truth.

- [ ] Public client endpoints are separated from admin/internal endpoints.
- [ ] Authentication is enforced on all non-health endpoints that require protection.
- [ ] Authorization is enforced for admin/internal operations.
- [ ] LicenseSpring API key, shared key, and product code are server-side only.
- [ ] Production secrets are stored in Azure Key Vault or approved secret storage.
- [ ] No secrets are present in repo files, logs, responses, screenshots, or release artifacts.
- [ ] TLS is enabled for all ingress traffic.
- [ ] API docs are disabled or protected in production if required.
- [ ] Rate limiting or abuse protection is enabled/planned for public licensing endpoints.
- [ ] Logs do not print license keys, API keys, QR payloads, or full offline request/response payloads.

## 8. Azure Deployment Gate

Use `docs/azure-deploy.md` for exact commands and target names.

- [ ] Confirm Azure resource group: `rg-ocuwell-gateway`.
- [ ] Confirm App Service: `ocuwell-gateway`.
- [ ] Confirm Key Vault: `kv-ocuwell-gateway`.
- [ ] Confirm Azure SQL server/database values are correct.
- [ ] Confirm managed identity has Key Vault read access.
- [ ] Confirm app settings use Key Vault references for LicenseSpring secrets.
- [ ] Confirm `Always On` and HTTPS-only are enabled.
- [ ] Confirm startup command uses Gunicorn/Uvicorn for `apps.main:app`.
- [ ] Deploy package from a committed release state.
- [ ] Restart the web app after deployment.

## 9. Post-Deployment Smoke Test

- [ ] Health check succeeds.

```powershell
Invoke-WebRequest https://ocuwell-gateway.azurewebsites.net/health -UseBasicParsing
```

- [ ] UI loads.

```powershell
Invoke-WebRequest https://ocuwell-gateway.azurewebsites.net/ui/ -UseBasicParsing
```

- [ ] `/ui/assets/*.js` and `/ui/assets/*.css` return `200`.
- [ ] Desktop online activation works against deployed gateway.
- [ ] Desktop online deactivation works against deployed gateway.
- [ ] Desktop offline activation request file can be completed through deployed UI.
- [ ] Desktop offline activation QR response can be completed through deployed UI.
- [ ] Desktop offline deactivation request file can be completed through deployed UI.
- [ ] Gateway logs show expected requests with correlation/debug context but no secrets.
- [ ] No new critical errors appear in Azure logs after smoke testing.

## 10. Frontend And Backend Handoff

- [ ] Provide frontend release owner with gateway deployment URL.
- [ ] Confirm `default-config.json` in frontend points to the intended gateway URL.
- [ ] Confirm desktop `PRODUCT_CODE` matches gateway/LicenseSpring configuration.
- [ ] Confirm backend `LICENSE_GATEWAY_BASE_URL` matches deployed gateway.
- [ ] Confirm offline activation/deactivation contract is unchanged or documented.
- [ ] Confirm any breaking contract change is coordinated with both desktop frontend and backend executable releases.

## 11. Final Sign-Off

- [ ] Python tests passed.
- [ ] Python coverage reviewed.
- [ ] UI build passed.
- [ ] OpenAPI export reviewed.
- [ ] Migration gate passed.
- [ ] Production gate P0 items passed or formally accepted.
- [ ] Azure deployment smoke test passed.
- [ ] Desktop end-to-end licensing smoke test passed.
- [ ] No secrets exposed.
- [ ] Release notes updated.
- [ ] Gateway release owner signs off.
