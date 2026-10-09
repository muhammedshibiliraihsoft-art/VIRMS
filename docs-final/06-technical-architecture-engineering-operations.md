# 06 — Technical Architecture, Engineering & Operations

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — TECHNICAL AND OPERATIONS SOURCE OF TRUTH

## Authority and implementation boundary

Use 01 for business rules, 02 for access, 03 for modules, 04 for data truth, 05 for workflow, 07 for UI, 08 for media, and supporting/ for authentication, production standards and Tenant consolidation. Together, these 11 canonical documents are the FINAL — PRODUCTION-READY MASTER SOURCE OF TRUTH for implementation governance. If a genuine business or authorization decision is absent, identify it rather than inventing it. Technical choices such as code structure, indexes, serializer shape, job mechanism, caching, and provider configuration may follow actual repository evidence without changing these rules.

Inspect the actual repository, framework, existing models, migrations, APIs, tests and deployment settings before implementation. Prefer extending a sound existing architecture and a modular monolith over unnecessary new frameworks, services or infrastructure.

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
- Use fixed-precision decimal money/percentages and the INR two-decimal `ROUND_HALF_UP` and residual-allocation rules in 05; binary floating point is not authoritative. Protect atomic critical writes against lost updates, Buyer Payment overrun, Buyer Refund overrun, duplicate Buyer Payments/refunds, duplicate Principal Recovery, Profit overpayment, double payouts, duplicate settlements, and partially committed corrections through appropriate constraints, locking/version checks, transaction boundaries and idempotency.
- Validate Investor percentage within inclusive 0%–100% and nonnegative Owner percentages totaling exactly 100% before configuration becomes effective. Enforce nonnegative Outstanding Vehicle Principal and Available Fund, the documented Investor Principal Claim reconciliation even when an Owner Contribution Return Payable or Buyer Principal Refund Reserve exceeds current Fund liquidity, and settlement closure only after every payable and obligation is reconciled and actually settled. Profit/Loss crossover corrections retain separate payout recovery, principal recognition, Owner contribution, contribution-return and Buyer refund positions; never silently net them. A linked reclassification of an existing Buyer receipt between collected Profit and Principal Recovery adjusts or reserves the Fund once without creating another receipt. A correction-created Buyer Refund Payable cannot be treated as an accepted excess new Buyer Payment or as settled before actual refund.
- Protected APIs check authentication, role, Tenant membership and object scope. Validate all critical fields server-side; do not trust supplied roles, Tenant IDs, monetary calculations, or hidden UI state.
- Public Vehicle API uses a dedicated safe schema for published eligible Vehicles. Internal Vehicle, Investor, purchase, Expense, profit, audit and configuration data never enter public responses.
- Growing lists use server-side pagination/filter/search/sort. Dashboard and reports use bounded queries or purpose-built summaries instead of full-table downloads.
- Errors are consistent and safe: distinguish validation, unauthorized, forbidden, missing, conflict, timeout and server failure without exposing stack traces, SQL, internal paths or secrets.
- Background jobs, if needed, carry Tenant context, are bounded, observable, retry-safe and idempotent where financial/media effects require it.

## Security and privacy

Authentication details follow supporting/authentication-account-security.md. Normal authentication, backend authorization, role controls and audit apply; a separate protected password is not required.

Apply server-side validation, object authorization, CSRF/XSS/SQL-injection/SSRF protections where relevant, secure upload checks, rate limiting for exposed or abuse-prone endpoints, and dependency/security hygiene. Validate file content, size, type and dimensions as 08 requires. Never expose storage credentials or secrets in source, committed environment files, frontend bundles, logs, API responses or AI prompts.

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
- Keep secrets and provider values in controlled environment configuration. This document selects no deployment provider.
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
