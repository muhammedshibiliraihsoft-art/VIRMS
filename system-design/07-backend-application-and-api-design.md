# 07 — Backend application and API design

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/02–06, 08 and supporting authentication/production standards. This is a contract design, not endpoint implementation. Financial command meanings are defined in 05.

## Django modular-monolith layers

| Layer | Responsibility | Forbidden shortcut |
|---|---|---|
| DRF request/response | Parse, serialize, paginate, version and format safe errors | No authoritative finance calculation in serializer/view |
| Authentication and scope | Verify session, role, operation, Tenant, resource and object/field access | No trust in supplied UUID, role or frontend visibility |
| Application commands | Coordinate authorization, idempotency, locks, domain operation, repositories and audit in one transaction | No cross-module partial financial posting |
| Application queries | Build permission-scoped read models, pagination and reporting | No mutation or independent balances |
| Domain rules | Decimal allocation, eligibility, correction reconciliation and invariant checks | No HTTP, React, AI or provider dependency |
| Persistence | PostgreSQL source events, constraints, projections and transaction boundaries | No manual balance overwrite |
| Infrastructure | R2 adapter, email/notification, optional AI and deployment integration | No provider logic in domain rules |

Package boundaries follow 02. Domain services use narrow repository/port interfaces, not a giant shared utils module. The application service orchestrates multi-module commands; a Fund source effect links to the operation that caused it. Audit is committed with the same database transaction. Optional notifications are emitted only after commit and cannot decide the financial outcome.

## REST and command conventions

Use a versioned internal API (representatively /api/v1/) and a separate public read API. Ordinary identity/descriptive edits may use resource-oriented operations. Financial postings, lifecycle confirmations and corrections use explicit POST command resources with a reason and idempotency key where required, avoiding ambiguous generic PATCH of money/status. IDs are opaque UUIDs. Server-generated computed positions are read-only response fields.

List responses use bounded page size, stable ordering, filters and server-side search/sort; no full-table download for a UI filter. Investor global reports and Owner combined views carry an explicit authorized scope description. Internal serializers are role/field specific; public Vehicle serializers are built from approved safe fields only. Audit/history endpoints expose records only under the same object and field authorization as the parent.

Representative routes below express shape, not a final URL lock:

| Route shape | Purpose and boundary |
|---|---|
| POST /api/v1/auth/login, /logout, /password/change | Django-controlled session lifecycle and CSRF-protected unsafe operations |
| GET /api/v1/me, /me/permissions | Current authorized identity, memberships and UI capability hints; backend still checks every request |
| GET/POST /api/v1/investors | Scoped Investor list/create; no Tenant-owned duplicate |
| GET /api/v1/investors/{id}/fund | Global Investor Fund position, source history and Tenant provenance under self/authorized scope |
| POST /api/v1/investors/{id}/capital | Explicit Accountant capital credit command |
| POST /api/v1/vehicles/purchases | One-Investor purchase and Fund use command |
| POST /api/v1/vehicles/{id}/expenses | Approved expense plus same-Fund debit |
| POST /api/v1/vehicles/{id}/lifecycle-transitions | Authorized core state change; Media denied |
| GET/POST /api/v1/buyers | Tenant-scoped Buyer data; phone is not identity |
| POST /api/v1/vehicles/{id}/sales | Confirm one authoritative Sale and snapshot |
| POST /api/v1/sales/{id}/buyer-payments | Actual bounded receipt and principal-first allocation |
| POST /api/v1/sales/{id}/corrections | Linked Sale price correction, payable/reserve and entitlement reconciliation |
| POST /api/v1/sales/{id}/buyer-refunds | Actual bounded correction-created refund |
| POST /api/v1/sales/{id}/profit-payments | Actual eligible recipient payout with Investor-before-Owner gate |
| POST /api/v1/sales/{id}/profit-recoveries | Actual bounded recovery receipt against current correction obligation |
| POST /api/v1/sales/{id}/owner-contributions | Actual bounded Owner loss coverage into the same Fund |
| POST /api/v1/sales/{id}/owner-returns | Actual bounded return from the same Fund |
| POST /api/v1/financial-corrections | Audited correction of a finalized financial source with explicit source/type/reason |
| POST /api/v1/investor/me/exit-requests | Own normal request with Terms acceptance, never financial closure |
| POST /api/v1/investors/{id}/settlement/principal-payments | Actual capped Accountant principal settlement |
| GET /api/v1/investors/{id}/settlement | Separate principal, Profit, unresolved blockers and historical payouts |
| GET /api/v1/vehicles/{id}/history, /api/v1/investors/{id}/history | Scope-safe immutable event and audit views |
| POST /api/v1/vehicles/{id}/images/uploads, /finalizations | Authorized image flow with four-active-image gate and retry safety |
| GET /api/v1/reports/... | Authorized bounded, rebuildable read views |
| GET /public/v1/vehicles | Only published eligible Vehicle projection and safe image metadata |

Back Office Financial Review uses read routes/read serializers for the documented finance scope and receives no ordinary write route grant. Tenant Merge, if implemented through a controlled admin procedure, is not exposed as a general operations endpoint.

## Request and response contract

For a critical POST, require a client-generated idempotency key scoped to actor, operation and resource; store a request fingerprint and committed response identity. Return the same outcome on an exact retry and a conflict on changed payload. Optionally require a resource version/If-Match on correction/review screens; rechecking the authoritative position under lock is mandatory regardless of the UI version. A successful response includes event UUID, resulting current-position/version and trace/correlation ID. Never report success before commit.

Use consistent field-level validation errors (invalid amount/percentage/state), 401 for missing/expired authentication, 403 or privacy-preserving 404 for denied scope, 404 for a genuinely unavailable permitted resource, 409 for stale version/idempotency conflict, and safe 5xx/timeout handling. Do not expose SQL, stack traces, R2 keys, secrets or another Tenant's existence. Payment excess is a clear backend validation failure, never silently clamped. Input types are explicit decimal strings or equivalent safe money representation, never JavaScript floating-point authority.

Public and private API schemas are separate. Upload/finalization verifies content/signature, size, dimensions, Vehicle/Tenant access and active count on the backend; the client never receives permanent R2 administrative credentials. Audit and reporting endpoints use pagination/filtering and the same field-level privacy rules as operational queries.
