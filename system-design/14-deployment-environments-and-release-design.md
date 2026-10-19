# 14 — Deployment environments and release design

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/06 and supporting production engineering standards. This is provider-neutral design; it creates no deployment files or resources.

## Environment progression

| Environment | Purpose and constraints |
|---|---|
| Local | Reproducible Django/DRF, React/Vite and PostgreSQL development with isolated non-production data and configurable R2-compatible storage access |
| Staging | Render free-tier application target with isolated PostgreSQL/data, secure backend-controlled auth, R2 adapter, migration and release verification; free-tier limits never relax business/security rules |
| Production | Hosting provider undecided; same code/business behavior, secure PostgreSQL and R2-compatible adapter, backups, monitoring, readiness and tested recovery |

Cloudflare R2 is the current object-storage provider independent of the application host. Docker is supported optional packaging; code remains deployable without Docker-specific domain behavior. A platform router/reverse proxy plus Gunicorn or suitable ASGI/WSGI server serves Django; Nginx is optional where equivalent platform routing/TLS exists. React/Vite outputs standard static assets suitable for standard static/CDN or container hosting.

## Configuration and delivery

Environment name, database URL, Django secret, allowed hosts, CSRF/cookie settings, frontend/API origins, R2 endpoint/bucket/credentials/region/signature/public URL, email settings and monitoring endpoints are external secure configuration. Never commit credentials, embed them in frontend/Docker images or print them in logs. Pin supported runtime/dependency versions and lockfiles during implementation. Production provider choice stays open.

GitHub Actions is the preferred CI/CD platform: lint/type/build, backend/frontend/integration checks, migration review and container verification as appropriate. Branch governance determines promotion; CI never bypasses protected main. The design does not prescribe a CI file before implementation. Stage release candidate with real auth/Tenant, media, public API and finance smoke paths on isolated data; check liveness and readiness before traffic.

## Safe schema and release path

Review environment and backup first. Prefer compatible expand/backfill/contract migrations, bounded locks and resumable large backfills; reconcile money/source events after migration. Record release identity, schema state and rollback/forward-fix procedure. Database restore must be tested, including audit/financial/permission integrity. Deploy optional media/AI changes so their failures degrade locally rather than preventing core finance operations. A new infrastructure dependency requires measured need and ADR review.

Only the future production-host choice and provider-specific deployment wiring remain intentionally undecided. They are not business-rule gaps and must not change domain/API semantics.
