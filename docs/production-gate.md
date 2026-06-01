# Ocuwell Gateway Production Gate

This document defines mandatory release gates for deploying the gateway to production.

Scope:
- Module 1: Clickwrap
- Module 2: Licensing (online/offline activation, validation, deactivation)

Release decision:
- `GO`: all `P0` gates pass, and no open critical incidents.
- `NO-GO`: any `P0` gate fails.
- `CONDITIONAL GO`: only allowed for `P1` gaps with explicit owner and due date.

## 1) Security Gate (P0)

### Required outcomes
- Public client endpoints are separated from admin/internal endpoints.
- Authentication is enforced on all non-health endpoints.
- Authorization (RBAC/scopes) is enforced for admin/internal operations.
- Upstream management/licensing keys are server-side only.
- Secrets are stored in Azure Key Vault and loaded via Managed Identity or Key Vault references.
- No secrets are present in repository files, logs, or API responses.
- TLS is enabled for all ingress traffic.

### Evidence required
- API route inventory showing endpoint classification: `client`, `admin`, `internal`.
- Auth middleware/dependency tests for unauthorized and forbidden access.
- Config proof: no plaintext production secrets in `.env`, code, or repo history.
- Key Vault integration verification in deployment settings.
- Pen test or security review checklist sign-off.

## 2) Correctness Gate (P0)

### Required outcomes
- Licensing flows pass integration tests:
  - Online activation
  - Offline activation request/confirm
  - License validation
  - Deactivation
- Idempotency is enforced for activation/deactivation endpoints.
- Offline license artifact is signed and verifiable.
- Validation behavior is correct for:
  - Valid license
  - Expired license
  - Tampered license file
  - Revoked license/device
- Clickwrap acceptance remains append-only and retrievable.

### Evidence required
- Integration test report from CI.
- Negative-path test results (invalid token, expired, tampered, revoked).
- Cryptographic signature verification test outputs.

## 3) Data Integrity Gate (P0)

### Required outcomes
- DB schema supports multi-product licensing at scale.
- Constraints and indexes exist for:
  - Product/license/device references
  - Activation uniqueness rules
  - Query-critical paths
- Alembic migrations apply cleanly and rollback is tested in staging.
- Backups and restore test are successful.
- Audit log records are immutable (append-only semantics).

### Evidence required
- Schema review sign-off (ERD + migration diff).
- Migration up/down execution logs on staging clone.
- Backup/restore drill report with timestamps.

## 4) Reliability Gate (P0)

### Required outcomes
- Upstream provider calls use timeout, retry, and circuit-breaker/fallback policy.
- Gateway returns deterministic errors when upstream provider is unavailable.
- Rate limiting is enabled on public licensing endpoints.
- Service has health/readiness probes.
- Deployment has at least one safe rollout strategy (blue/green or canary).

### Evidence required
- Fault-injection test result (simulate provider timeout/5xx).
- Load test baseline (target p95 latency and error rate).
- APIM/App Service policy/config screenshots or IaC diff.

## 5) Observability Gate (P0)

### Required outcomes
- Structured logs include correlation/request IDs.
- Metrics exported for:
  - Activation success/failure
  - Validation latency
  - Upstream error rate
  - Deactivation/revocation events
- Alerts configured for SLO breach and error spikes.
- Dashboards available to engineering + on-call.

### Evidence required
- Example log entries with correlation IDs.
- Alert rules and dashboard links.
- On-call runbook for top failure modes.

## 6) Operational Readiness Gate (P0)

### Required outcomes
- SLOs are defined and approved.
- Incident response runbook exists.
- Key rotation runbook exists and is tested.
- Rollback procedure is tested in staging.
- Feature flags exist for high-risk licensing behavior changes.

### Evidence required
- SLO document and ownership.
- Drill report: rollback and key rotation.
- Release checklist signed by service owner.

## 7) Current Repo Delta (Immediate Actions Before Go-Live)

These are known blockers based on current repository state:
- Add authentication/authorization layer (currently missing).
- Add structured audit logging module.
- Add rate limiting and observability for public licensing endpoints.
- Disable or protect API documentation in production.

## 8) CI/CD Gate Policy

Minimum required CI checks before deploy:
- `ruff`/lint pass
- type checks pass (recommended: `mypy`/`pyright`)
- unit tests pass
- integration tests pass
- migration smoke test pass (`alembic upgrade head` on ephemeral DB)
- dependency/security scan pass
- SOUP register reviewed and updated for vendored third-party frontend assets
  (`docs/soup-register.md`)

Deployment promotion policy:
- `dev -> staging` automatic after CI pass
- `staging -> prod` requires manual approval plus all `P0` gates complete

## 9) Azure Target Baseline

Recommended baseline:
- Hosting: Azure App Service (Linux, Python) with `Always On` enabled.
- Edge/API governance: Azure API Management in front of gateway.
- Database: Azure SQL Database or Azure Database for MySQL.
- Secrets: Azure Key Vault + Managed Identity.
- Monitoring: Azure Monitor + Application Insights.

## 10) Go/No-Go Template

Use this template for each release:

```text
Release:
Date:
Owner:

Security Gate (P0): PASS/FAIL
Correctness Gate (P0): PASS/FAIL
Data Integrity Gate (P0): PASS/FAIL
Reliability Gate (P0): PASS/FAIL
Observability Gate (P0): PASS/FAIL
Operational Readiness Gate (P0): PASS/FAIL

Open P1 items:
1)
2)

Decision: GO / NO-GO / CONDITIONAL GO
Approvers:
```
