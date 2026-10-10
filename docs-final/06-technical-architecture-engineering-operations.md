# 06 — Technical Architecture, Engineering & Operations

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — TECHNICAL AND OPERATIONS SOURCE OF TRUTH

## Authority and implementation boundary

Use 01 for business rules, 02 for access, 03 for modules, 04 for data truth, 05 for workflow, 07 for UI, 08 for media, and supporting/ for authentication, production standards and Tenant consolidation. Together, these 11 canonical documents are the FINAL — PRODUCTION-READY MASTER SOURCE OF TRUTH for implementation governance. If a genuine business or authorization decision is absent, identify it rather than inventing it. Implementation details such as code structure, indexes, serializer shape, job mechanism and caching may follow repository evidence within the technology stack and portability boundaries locked below and in 08.

Inspect the actual repository, existing models, migrations, APIs, tests and deployment settings before implementation, then implement within the canonical stack below. VIRMS is a provider-neutral modular monolith; prefer its existing sound components over unnecessary additional frameworks, services or infrastructure.

## Canonical technology stack and deployment architecture

### Application stack

- Frontend: React 19, Vite, TypeScript, Tailwind CSS v4, React Router and TanStack Query. TypeScript is mandatory for frontend application code. Use React for the UI, Vite for build/development tooling, React Router for client-side routing, and TanStack Query for server-state fetching, caching, loading, invalidation and request state.
- Do not use Next.js for the core VIRMS application. VIRMS is an authenticated ERP/management application rather than an SEO-first content site. A separate SEO-heavy public website may be evaluated separately if a verified need arises; it does not replace the core frontend.
- Backend: Python, Django and Django REST Framework. Django/DRF is authoritative for business and financial rules, permissions, tenancy, authentication, validation, audit, transaction boundaries, APIs and persistence. Frontend code is not an authority for these rules.
- Database: PostgreSQL is the canonical relational database. Keep deployment compatible with standard PostgreSQL and do not require provider-specific database extensions without a documented need and reviewed portability impact.

### Authentication, files and runtime

- Authentication remains Django/backend controlled. Prefer secure server-controlled browser authentication using secure HttpOnly cookies or compatible sessions where practical. Never put sensitive long-lived credentials in insecure browser storage; frontend role checks are UX only and backend authorization remains authoritative.
- Cloudflare R2 is the current canonical object/file storage provider for appropriate uploaded and generated media. Access it through the replaceable S3-compatible object-storage adapter; R2 is the current provider, while S3 compatibility is the interface and portability contract. Do not put Cloudflare-specific API behavior in core Django/Python business code. Follow 08.
- Docker is a preferred and supported deployment packaging option, not a business/domain dependency. Core Django code must remain deployable without Docker-specific behavior.
- Production runtime supports a platform router/reverse proxy followed by Gunicorn and/or an appropriate ASGI/WSGI application server and Django. Nginx is optional where the platform supplies equivalent routing/TLS behavior. Keep deployment configuration replaceable.
- Do not require Redis or Celery initially. Add a background-job system only for an actual workload such as heavy reports, image processing, asynchronous notifications, scheduled jobs, long-running work or retryable external operations; place it behind an application/infrastructure boundary.

### Configuration, environments and hosting

- Externalize environment-specific settings, including database URL, Django secret, allowed hosts, R2-compatible storage endpoint, bucket, access key, secret key, optional public/custom media URL and required region/signature settings, email settings, frontend/API URLs, environment name and security settings. Store credentials securely; never hard-code R2 account IDs, bucket names, endpoints, public URLs, secrets or other provider values in application/domain code, repository files, frontend bundles or Docker images.
- Canonical progression is Local → Staging → Production. Environments run the same application code and business behavior; differences are configuration and infrastructure only.
- Staging deployment target is Render free tier. This is an infrastructure choice for staging, not a business or core architecture dependency. Keep Render settings in the deployment layer. A free-tier limitation is handled as an infrastructure constraint and must not weaken security, finance, Tenant isolation or backend validation.
- Production hosting provider is not selected. Do not treat DigitalOcean or any other provider as mandatory. Select production hosting later based on operational and technical requirements.
- Render free tier is the staging application hosting target only. Cloudflare R2 is an independent object-storage provider and may be used regardless of the application hosting provider. Production application hosting remains unselected; application hosting provider and storage provider are independent decisions.
- Provider migration must not require rewriting core Python/Django business/domain code. Application-host migration changes stay in deployment configuration, environment values, database connection/migration configuration, DNS, networking, CI/CD and infrastructure resources. Replacing R2 with another compatible object-storage provider must likewise stay behind the adapter and configuration boundary without changing domain logic. The PostgreSQL provider is also changeable while retaining the PostgreSQL contract.
- React/Vite must produce standard production assets that can be served through static/CDN hosting, a containerized web server, managed frontend hosting or another standards-compatible platform without changing frontend architecture.

### Delivery, versions and initial scope

- GitHub Actions is the preferred CI/CD platform for suitable automated checks such as backend/frontend tests, lint, type checks, builds, migration safety and container build verification, with staging automation added as appropriate. CI/CD must obey repository branch governance.
- Use supported stable/LTS versions appropriate at implementation time. Pin exact implementation versions using reproducible Python constraints/lock strategy, frontend package lockfile and explicit runtime/container versions. Major upgrades are intentional and tested; do not automatically upgrade production dependencies to a new major version.
- Keep the initial runtime close to React/Vite, Django REST API, PostgreSQL and Cloudflare R2 through the S3-compatible adapter when object storage is needed. Do not prematurely require Kubernetes, microservices, service mesh, Kafka, Elasticsearch, Redis, Celery, multiple databases or multi-cloud active-active systems. Introduce additional infrastructure only for a verified requirement and an explicit architecture decision.

## Tenant and authorization architecture

- Garage = Tenant. Implement multi-Tenant boundaries from day one even if one Tenant is initially active. Tenant UUID is stable; name is editable.
- Resolve Tenant context on every Tenant-scoped request from authenticated User, explicit membership, permission and resource. A request-supplied Tenant ID never grants access.
- Enforce backend and object-level authorization across database access, APIs, reports, search, exports, media, jobs, audit, cache and notifications. Owner combined view is an explicitly authorized union, not an isolation bypass.
- User, Investor, Investor Fund and Business Owner identities are global. Vehicle, Buyer, Labour, Expense Category and operational Vehicle records are Tenant-scoped as defined in 04.
- Owner has full relevant authorized read visibility and no normal write authority. Accountant is the daily operational writer. Media has public-facing scope only and cannot mutate core Vehicle lifecycle or inspect finance. Investor private finance is self-scoped. Labour has no login.
- Centralize permission evaluation; frontend navigation state only reflects backend permission.
- Follow 02's explicit default-deny policy for every new module, feature, resource, and operation. Existing role philosophy never creates implicit access to an undefined future capability; define its authorization contract before implementation.

## Backend, data, and API

- Separate request/API, authorization/scope, validation, domain operation, persistence and audit concerns. Do not duplicate financial logic in frontend, reports or AI.
- Keep ledgers and source transactions authoritative. Derived balances, reports, caches and projections must reconcile and rebuild from them. Available Fund is ledger-derived; cumulative Recovered Principal is never added twice.
- Use fixed-precision decimal money/percentages, INR two-decimal `ROUND_HALF_UP`, and the balanced paise reconciliation rule in 05 for nonnegative, exact Owner Profit and Loss allocations; binary floating point is not authoritative. Protect atomic critical writes against lost updates, Buyer Payment overrun, Buyer Refund overrun, duplicate Buyer Payments/refunds, duplicate Principal Recovery, Profit overpayment, double payouts, duplicate settlements, and partially committed corrections through appropriate constraints, locking/version checks, transaction boundaries and idempotency.
- Validate Investor percentage within inclusive 0%–100% and nonnegative Owner percentages totaling exactly 100% before configuration becomes effective. Enforce nonnegative Outstanding Vehicle Principal and Available Fund, the documented Investor Principal Claim reconciliation even when an Owner Contribution Return Payable or Buyer Principal Refund Reserve exceeds current Fund liquidity, and settlement closure only after every payable and obligation is reconciled and actually settled. Repeated corrections derive one current position from immutable gross events, confirmed reversals, actual payments, actual recoveries, actual refunds/returns and existing open adjustments. Profit adjustments use Net Retained Profit Payment after actual confirmed recoveries; Loss-to-Profit reverses only Net Investor Loss Recognition and returns only current net retained Owner contribution. Reconcile existing open positions to the corrected target without duplicate economic effects. Keep payout recovery, principal recognition, Owner contribution, contribution-return and Buyer refund positions separate; never silently net them. A linked reclassification of an existing Buyer receipt between collected Profit and Principal Recovery adjusts or reserves the Fund once without creating another receipt. A correction-created Buyer Refund Payable cannot be treated as an accepted excess new Buyer Payment or as cash returned before an actual refund; a later valid Sale correction may adjust the open payable through linked history.
- Preserve normal deal-level eligibility for Investor Profit Payments before Exit. For new Profit Payments and final Investor Settlement, use Net Retained Profit Payment after actual confirmed correction-chain recoveries to determine the remaining eligible Profit without duplication; enforce actual payment of the remaining Principal Settlement Payable to zero before any remaining eligible Investor Profit is paid as part of final Settlement. Keep principal and Profit transactions separate and apply all existing settlement closure blockers.
- Same-side Loss corrections use the original shared Profit/Loss percentage snapshot and balanced paise allocation. Reconcile corrected Investor Loss Share against net confirmed recognitions with linked additional recognition or reversal, and each corrected Owner requirement against actual retained contribution with one current obligation or return payable. Do not duplicate open positions, count unpaid return payables as resolved Vehicle principal, credit unreceived Owner contributions, or rewrite original financial history; preserve the existing Fund reserve and Settlement conditions.
- Backend financial commands enforce `0 < amount <= current authoritative outstanding position` for Accountant-confirmed Profit Recovery Receipts, Owner Loss Contribution Receipts, Owner Contribution Return Payments and Principal Settlement Payments. A Principal Settlement Payment must also not exceed the authoritative Available Fund available for that Settlement. Check authorization, Tenant/account/resource scope and the current obligation/payable inside the same atomic transaction that records the immutable event and any Fund effect. Use locking/version checks and idempotency or equivalent duplicate protection so concurrent or retried requests cannot exceed the current position. Reject excess amounts without clamping, netting, reclassification, Fund conversion or balancing entries; frontend validation is UX only. Owner, Media, Investor and Public cannot confirm these transactions, Labour has no login, and Back Office is not their normal daily confirmer.
- For a correction-created Buyer Refund Payable, derive one current nonnegative position from valid confirmed Buyer Payments, separately confirmed cumulative refunds and the current corrected Sale Price. Later corrections adjust that position and any principal-backed Fund reserve through linked immutable records; never rewrite an original receipt, duplicate an already paid refund, count pending refundable money as applied Sale/Profit/recovered principal, or relax the existing new Buyer Payment cap. Keep affected Sale resolution and final Settlement blocked while the payable remains open.
- Protected APIs check authentication, role, Tenant membership and object scope. Validate all critical fields server-side; do not trust supplied roles, Tenant IDs, monetary calculations, or hidden UI state.
- Public Vehicle API uses a dedicated safe schema for published eligible Vehicles. Internal Vehicle, Investor, purchase, Expense, profit, audit and configuration data never enter public responses.
- Growing lists use server-side pagination/filter/search/sort. Dashboard and reports use bounded queries or purpose-built summaries instead of full-table downloads.
- Errors are consistent and safe: distinguish validation, unauthorized, forbidden, missing, conflict, timeout and server failure without exposing stack traces, SQL, internal paths or secrets.
- Background jobs, if needed, carry Tenant context, are bounded, observable, retry-safe and idempotent where financial/media effects require it.

## Security and privacy

Authentication details follow supporting/authentication-account-security.md. Normal authentication, backend authorization, role controls and audit apply; a separate protected password is not required.

Apply server-side validation, object authorization, CSRF/XSS/SQL-injection/SSRF protections where relevant, secure upload checks, rate limiting for exposed or abuse-prone endpoints, and dependency/security hygiene. Validate file content, size, type and dimensions as 08 requires. Backend/storage-layer controls determine upload and access authorization. Do not expose permanent or administrative R2 credentials to browser clients; public delivery is allowed only under 02/08 publication rules, and private/internal files remain private. Never expose storage credentials or secrets in source, committed environment files, frontend bundles, Docker images, logs, API responses or AI prompts.

Sensitive audit records preserve actor, action, time, entity UUID, Tenant context, old/new values and reason where relevant. Never log credentials or tokens.

Owner AI is read-only over verified authorized data. It may explain or analyse; it cannot mutate, invent financial truth, or cross Tenant/privacy boundaries. Authorization alone is not sufficient justification to send data to an AI provider or model. For each request, use deterministic backend query/filtering to select the minimum authorized data reasonably necessary for that specific query, remove secrets and unrelated private or sensitive records, and avoid broad database or whole-Tenant dataset transmission when a smaller result can answer it. AI processing must not silently expand Tenant, object, or resource scope. AI output remains explanatory/analytical rather than an authoritative financial record. If AI fails, core business access remains usable.

## Performance and failure behavior

- Design for lower-end phones and slow or unstable networks. Avoid blank initial screens, unbounded payloads, blocking image loads, heavy unnecessary dependencies, N+1 queries and stale financial caches.
- Keep the application shell stable through loading, empty, validation, timeout and server-error states. Preserve entered form data when possible; never show false success or endless spinners.
- Optional media, AI or notification failure must degrade locally without blocking core business data or financial operations.
- Measure relevant latency, query count, payload size, render cost and image transfer. Optimize only with evidence and without weakening accuracy, image clarity, authorization or Tenant isolation.
- Follow 08 for responsive optimized images, original preservation, and localized media failure.

## Production health and readiness

- Production deployments must provide lightweight health/liveness and readiness signals that monitoring and deployment infrastructure can use to distinguish a running process from a service that is ready to accept traffic.
- Readiness must detect critical dependency, startup, migration, or other required-workload conditions and must not report ready when the application cannot safely serve that workload. A degraded non-critical dependency may be reported separately and must degrade locally where practical.
- Health/readiness responses must expose no secrets or sensitive business data. Deployment and release validation must verify the signals; exact paths and provider-specific mechanics remain implementation choices.

## Environment and release safety

- Use Local/Development → Staging → Production progression. Staging should exercise realistic authentication, Tenant isolation, migrations, storage, jobs, public API, responsive UI and release behavior with isolated data.
- Identify the target environment before any migration, destructive operation, data correction or infrastructure change. Never assume a connected service is development.
- Keep secrets and provider values in controlled environment configuration. Render free tier is the locked staging target; production hosting remains unselected and provider-neutral.
- Migrations account for existing data, deployment order, locks, rollback and recovery. Risky changes use safe staged transitions; large backfills are batched, resumable and observable.
- Production requires backups and a known, tested restore path. Releases need a practical rollback or forward-fix path; risky features may use a targeted kill switch.
- Record structured logs with request/correlation ID, safe User reference, Tenant context and failure type. Monitor slow APIs/queries, failed jobs, repeated failures and image processing.

## Verification and audit cadence

| Level | When | Required scope |
|---|---|---|
| Task-level | After each implementation task | Focused checks and relevant tests for changed behavior, permissions, Tenant scope, finance or UI |
| Batch/loop | At a logical batch boundary | Integration and regression across that batch; no routine full-system audit |
| Phase/milestone | After major module/foundation completion and before production release | Broad relevant review of business rules, finance, permissions, Tenant isolation, security, performance, concurrency, failures, history, observability and recovery |

Critical tests cover one Investor per Vehicle, Fund reconciliation, actual-payment recovery, positive and negative allocation, universal payout ordering, exit/settlement, permission denials, cross-Tenant isolation, Media/Investor privacy, audit, duplicate/concurrent writes, public API safety and recovery paths. Independent audit findings are verified against actual code/evidence before becoming fixes. Do not run a deep project-wide audit after every small task.

## Current non-scope

No dedicated Cash/Bank operational modules, General Garage Expense, Labour payroll/attendance/assignment, manual loss selector, early profit payout mode, normal Tenant Merge UI, AI financial mutation, or infrastructure added solely for hypothetical scale.
