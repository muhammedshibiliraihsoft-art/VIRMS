# 06 — Technical Architecture, Engineering & Operations

Status: DRAFT V2 — technical and operations source after approval

## Authority and implementation boundary

Use 01 for business rules, 02 for access, 03 for modules, 04 for conceptual data, 05 for Investor/Stock Vehicle finance, 07 for UI, 08 for media, 09 for Company accounting/Owner distribution, 10 for Garage Jobs, and supporting/ for account security, production standards and Tenant consolidation. Missing genuine business meaning is `BUSINESS DECISION REQUIRED`; an implementation detail may follow repository evidence only within these boundaries. No production V1 transaction history requires a V1→V2 financial cutover or dual runtime engine. Preserve future transaction history and auditability under V2.

## Canonical application stack

- Frontend: React 19, Vite, TypeScript, Tailwind CSS v4, React Router and TanStack Query. TypeScript is mandatory for frontend application code. React is the UI, Vite the build/development tool, React Router navigation, and TanStack Query server-state management. Do not use Next.js for the core management application.
- Backend: Python, Django and Django REST Framework. Django/DRF owns business/financial rules, Company/Branch scope, authentication, authorization, validation, audit, transaction boundaries and APIs. Frontend calculations are explanatory only.
- Database: PostgreSQL. Use standard PostgreSQL without unreviewed provider-specific extensions. Source transactions/ledgers are authoritative; derived balances, reports, caches and projections reconcile and rebuild.
- Files: Cloudflare R2 is the current object-storage provider through a replaceable S3-compatible adapter. Core domain code has no Cloudflare-specific dependency. See 08.
- Architecture: provider-neutral modular monolith. Separate Platform Core, Accounting, Investment, Garage and Investor Portal responsibilities through stable internal contracts. Garage functions without Investment; Accounting links their source events without double posting. Do not require microservices, Kafka, multiple databases, Redis or Celery for hypothetical scale.

## Environments, runtime and provider boundaries

Local → Staging → Production uses the same business behavior; differences are configuration and infrastructure. Render free tier is the current staging application-host target. Production application host is unselected. Docker is supported optional packaging, not a domain dependency. Production runtime supports platform routing/reverse proxy, Gunicorn and/or suitable ASGI/WSGI server, and Django; Nginx is optional when the platform supplies equivalent routing/TLS. GitHub Actions is the preferred CI/CD platform under branch governance.

Externalize database connection, Django secret, allowed hosts, environment name, security options, frontend/API URLs, email configuration and R2 endpoint/bucket/keys/region/signature/public URL through controlled environment configuration. Do not embed secrets, account IDs or provider values in domain code, frontend bundles, repository files, images, logs or prompts. Replacing hosting, PostgreSQL provider or compatible object storage must not rewrite core business logic. Pin implementation versions with reproducible backend constraints/locks, frontend lockfile and runtime/container versions; upgrade majors intentionally.

## Company, Branch, module and authorization boundaries

Company/Tenant is the hard isolation boundary. Branch is a within-Company operational attribution and access boundary, not a separate Tenant or Investor Fund owner. Resolve every request from authenticated User, Company membership, relevant Branch assignment, enabled module, action permission and resource/object scope. Supplying an ID is not authorization. Owner Company-wide views require explicit authorization; cross-Company aggregation of private records is not an ordinary Company view. Enforce these checks in APIs, queries, reports, exports, search, media, cache, jobs, audit and notifications.

Module OFF is a versioned Company configuration state. Backend denies ordinary new module actions; it retains authorized historical reads and narrowly authorized actions necessary to close existing obligations. Re-enable restores ordinary supported module access without deleting data. Platform Back Office controls Company/Branch/module administration but does not inherit routine Tenant finance write authority. New module operations follow 02's explicit default-deny rule.

## Backend, financial data and API

Separate request/API, authorization/scope, validation, domain operation, persistence and audit concerns. Each financial fact has one authoritative source; bridge records between Investment, Garage and Accounting identify source rather than create a second economic amount. Company Share from a Stock Vehicle enters Company accounting once, not direct Owner payout. Company Running Capital has its own actual contribution/recovery history. Monthly Interim Payout is distinct from earned Investor Profit. Human-confirmed payments, receipts, settlements, manual Loss impacts and sensitive corrections remain separate from calculations, suggestions and reminders.

Use fixed-precision decimal arithmetic, current INR, two-decimal final posted amounts with `ROUND_HALF_UP`, and high-precision intermediates. Binary floating point is not money authority. Investor agreement percentage remains configurable and snapshotted. 09 defines deterministic balanced-paise Owner allocation from an approved **Company-level** positive distributable amount; it is not a new Vehicle-deal Owner payout or automatic Loss allocation.

Protect critical purchase, Expense, Sale, Buyer Payment/refund, Investor Fund, Running Capital, Interim Payout, Profit payout/recovery, Company receipt/payment, Owner Distribution, correction and settlement writes with appropriate transaction boundaries, constraints, concurrency checks and duplicate/retry protection. Existing bounded new Buyer Payments and actual refunds cannot exceed their current authoritative open positions. New ordinary eligible Profit Payments cannot exceed outstanding eligible entitlement. Interim advances use their own approved cycle/payment controls and are not mislabelled eligible deal Profit. Reject corrupt/excess postings without silently clamping or creating balancing money. An authorized exception requires explicit scope, reason and auditable action; a general flexibility principle does not override data-integrity invariants.

Protected APIs validate Company/Branch/object/field scope and monetary inputs server-side. Public Vehicle access uses a dedicated approved-safe schema, not internal entity serialization. Growing lists use server-side pagination/filter/search/sort. Reports are bounded, reconcilable and Company/Branch-scoped. Consistent safe errors distinguish validation, unauthorized, forbidden, missing, conflict, timeout and server failure. Background jobs, if justified by image processing, reports, notifications or retryable external work, carry Company/Branch context and are bounded, observable, retry-safe and idempotent where they affect money or media.

## Security, privacy and AI

Authentication follows supporting/authentication-account-security.md. Prefer secure backend-controlled browser sessions/HttpOnly cookies where practical. Frontend role state is UX only. Apply server-side validation, object authorization, CSRF/XSS/SQL-injection/SSRF protection where relevant, secure upload checks, appropriate rate limits and dependency hygiene. Public media delivery follows publication rules; permanent R2 credentials never reach browsers.

Owner AI is read-only over verified authorized data. Backend query/filtering selects the minimum Company/Branch/object data needed for a request, excludes secrets and unrelated sensitive records, and cannot expand authorization scope. AI output cannot post money or become authoritative financial truth; AI failure leaves core business access usable. No automated Loss allocation or settlement is permitted.

## Performance, release and verification

Design for lower-end phones and unstable networks: stable loading/empty/error states, bounded payloads, responsive optimized images, no false success, no endless spinner, no unbounded table download, no N+1 and no stale financial authority in cache. Optional media, AI and notification failures degrade locally. Production has safe health/liveness and readiness signals; readiness must not claim the system can serve required work when a critical dependency or migration condition prevents it.

Identify target environment before migrations or production operations. Staging uses isolated data and exercises Company isolation, Branch scope, module OFF/ON, finance, Garage, media and release behavior. Production needs backups, tested restore, practical rollback/forward-fix, structured safe logs, correlation IDs and monitored failures. Verification cadence is focused task checks, related batch regression and broad phase/release audits. Critical tests include one Investor per funded Stock Vehicle, external Garage Vehicle without Investor, Company isolation, Branch movement/history, module OFF with open obligations, Fund/Running Capital separation, actual Buyer collection/refunds, positive split, manual Loss, interim cycle/reconciliation, recoverable partial settlement, Owner distribution, role denials, concurrent writes and public/media privacy.

## Current non-scope

No generic ERP, mandatory full inventory/payroll/attendance, automatic Loss engine, AI financial mutation, normal user-facing Company merge button or infrastructure added solely for hypothetical scale. Production hosting provider remains unselected and is not a blocker for defining core business behavior.
