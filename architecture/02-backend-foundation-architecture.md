# VIRMS — Backend Foundation Architecture

> **Status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL PROPOSAL. CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the living maps. Missing V2 behavior is an **IMPLEMENTATION GAP**; unresolved meaning is **BUSINESS DECISION REQUIRED**. This is not an approved V2 implementation contract; reuse technical details only after V2 and source verification.

## Purpose and boundary

This file records a V1-derived proposal for backend foundation capabilities. It does not prescribe V2 implementation order or contract. No Django apps, model definitions, migrations, serializers, views, URL routes, database tables or code are created by this document. Use V2 sources and current implementation evidence for any later, separately authorized design.

## Source Basis

### V2 target sources (business boundary only)

- `docs-final-v2/01-business-rules.md` through `10-garage-jobs-workflow.md`
- `docs-final-v2/supporting/authentication-account-security.md`
- `docs-final-v2/supporting/production-engineering-standards.md`
- `docs-final-v2/supporting/tenant-merge-consolidation.md`

### Historical System Design references

- `system-design/00-authority-and-design-contract.md`
- `system-design/02-domain-and-module-architecture.md`
- `system-design/03-identity-tenancy-and-authorization.md`
- `system-design/04-data-and-persistence-design.md`
- `system-design/05-financial-engine-design.md`
- `system-design/07-backend-application-and-api-design.md`
- `system-design/10-security-audit-and-compliance-design.md`
- `system-design/11-concurrency-idempotency-and-failure-design.md`
- `system-design/13-testing-verification-and-quality-strategy.md`
- `system-design/14-deployment-environments-and-release-design.md`

### Derived Architecture

- Use one Django/DRF modular monolith with PostgreSQL as canonical persistence.
- Establish backend identity, authorization and Tenant isolation before normal frontend feature work.
- Route state-changing use cases through application operations that own authorization revalidation, domain behavior, transaction, persistence and audit coordination.
- Treat immutable authoritative events as distinct from rebuildable current-position projections.

### Business decisions

No decisions are resolved by this historical proposal. Applicable V2 open decisions are listed in `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.

## Runtime and request layers

```text
HTTPS / request boundary
  → DRF parsing and safe response formatting
  → Django session authentication
  → operation permission and Company/Branch/resource scope resolution
  → application command or authorized query
  → domain policy and validation
  → PostgreSQL repositories / transaction
  → append-only audit and source-linked event
```

The request layer translates transport data and errors; it does not own business truth. Application operations coordinate cross-module work. Domain policy is independent of HTTP, React and storage providers. Persistence enforces identity and integrity constraints. External work such as email, AI or object storage does not run while holding a financial database transaction unless a reviewed design establishes a safe boundary.

## Django modular-monolith organization

Organize future code by bounded project capabilities from `system-design/02`, with shared infrastructure kept narrow:

- **Project/configuration boundary:** environment-specific settings, URL mounting, middleware and logging configuration.
- **Foundation capabilities:** Accounts/Auth, Users/Roles/Permissions, Tenant/Membership, shared authorization and Audit.
- **Business capabilities:** separate module boundaries for Investor, Fund, Vehicle, Sales, Finance, Settlement, Media and other canonical modules as they are implemented.
- **Application layer:** explicit commands and queries coordinate repositories and module operations.
- **Domain layer:** canonical business/financial rules and invariants, independent of transport and UI.
- **Infrastructure layer:** PostgreSQL, R2 adapter, email/notification and optional providers behind interfaces.

Do not build a generic all-purpose domain/utils package, let modules mutate another module's private records directly, or split this application into network microservices. A future Phase 1 detailed plan may choose exact Python package names after inspecting repository state.

## PostgreSQL and persistence boundary

PostgreSQL is the V2 target relational database. Persist identities and Company/Branch-scoped links only as specified by `/docs-final-v2/04`; do not carry forward V1 global/Branch-owned business identity assumptions. Enforce relationships, uniqueness and check constraints at the database boundary where appropriate. Financial source facts and history are authoritative; current positions, reports and caches are derived and reconcilable.

Each application command owns one bounded database transaction for its authoritative state change. Commit all related database source events, linked ledger effects, current-position update/watermark and audit atomically. Failure rolls back all database effects and must not return false success. External object-store operations require an intent/finalization or equivalent compensating pattern because they do not share PostgreSQL ACID transactions.

Migration discipline: inspect real schema and data before each change; review constraints, lock duration, deploy order, compatibility, backfill and recovery; batch and resume large changes; verify reconciliation after migration. No schema, migration or table design is implemented by this document.

## Identity and VIRMS authentication

Company is the Tenant/isolation boundary. Branch/Garage is within Company and does not own an Investor Fund or duplicate Vehicle identity. Investor and Fund are Company-scoped; one funded Stock Vehicle has one Investor, while an external-customer Garage Vehicle need not have one. Do not assume Investor, Owner-recipient or Fund identities are global across Companies. A known UUID or caller-supplied Company/Branch ID never grants access. Consult V2/02 and V2/04 for exact permissions and relationships.

Authentication target follows `docs-final-v2/supporting/authentication-account-security.md`:

- Django/backend-controlled Username/Login ID and password.
- Administrator-issued temporary credential with private first-login password replacement.
- Own password change validates current password; recovery is administrator-assisted.
- No public self-service password reset, security questions, mandatory MFA, SSO, social login, email or OTP flow is introduced.
- Store password hashes only; never return or log credentials, reset codes, tokens or secrets.
- Deactivation blocks login; reset/compromise revokes prior sessions; activation, deactivation and reactivation preserve history.

Use the approved Django-controlled session approach with secure HttpOnly cookies and CSRF protection as applicable to the deployed origin. The browser does not store long-lived credentials. Exact cookie/origin settings are environment configuration selected in a reviewed phase plan.

## Tenant resolution and authorization

For every protected request, evaluate backend-side:

```text
Authenticated active User
  → explicit operation permission
  → Company membership
  → relevant Branch assignment and enabled-module state
  → role/action permission
  → resource and sensitive-field scope
  → target object and linked-object checks
  → ALLOW scoped query/command or DENY
```

Default deny applies to new resources and operations. Resolve Company and relevant Branch from authenticated assignments and the requested object's authoritative scope; caller-supplied context is a selector, not a grant. Scope database queries before applying caller-supplied object IDs. Recheck membership, object links, module state and current position inside critical transactions. Investor views are limited to that Investor's own authorized Company-scoped records. Owner reads remain read-only in authorized scope. Back Office private-finance reads beyond explicit Company assignment remain `BUSINESS DECISION REQUIRED`. Frontend navigation and permission hints are UX only. These are V2 target requirements; the current code implements narrower Tenant/account paths only.

## DRF/API foundation

- Use a versioned internal API convention, initially represented by `/api/v1/`, and a separate public-safe read boundary where required.
- Keep authentication, authorization/scope, input validation and error translation in explicit request/application boundaries.
- Separate commands from queries. Consequential state transitions use explicit application operations; do not expose generic writable financial records or accept authoritative totals from the browser.
- Use server pagination with bounded page sizes, stable ordering, allowlisted filtering/search/sort and permission-scoped querysets.
- Keep public and internal response schemas separate. Do not serialize internal entities and hide fields in React.
- Provide consistent safe validation, unauthenticated, forbidden/privacy-preserving missing, conflict, timeout and server-error responses. Never return stack traces, SQL, secrets or another Tenant's existence.
- Every route and field checks backend authority regardless of client route visibility. This foundation defines conventions, not the full endpoint catalog.

## Application operation, audit and transactions

Application operation responsibilities are ordered:

1. Authenticate and resolve the actor.
2. Check explicit operation permission, Tenant/resource scope and linked objects.
3. Parse/validate input and current state.
4. Open the transaction and acquire the required parent/resource locks in a deterministic order.
5. Revalidate access and authoritative current positions under lock.
6. Apply domain operation; append source events, linked database effects and a current projection update if used.
7. Append audit evidence in the same database transaction.
8. Commit, then return the committed event/version and correlation reference.

Audit covers sensitive account/access/configuration changes, financial commands and corrections, settlement, publication and administrative operations. Record actor, scope, object/source, action, time, outcome and relevant before/after values/reason as approved. Audit is append-only evidence, not another financial ledger. Secrets and raw credentials never enter audit or operational logs.

## Idempotency, concurrency and failure handling

Require duplicate protection for critical writes and non-repeatable operations. An idempotency record binds actor, operation, resource and key to a request fingerprint and committed outcome. Exact retries replay the outcome; changed payload under the same key conflicts. A timeout after commit is resolved by key lookup before retrying.

Use PostgreSQL transactions, uniqueness/check constraints, parent-row locks and current-position revalidation. Lock related resources in stable order. Retry deadlock/serialization failures only in a bounded manner with the same idempotency identity. Start with the System Design's single-database locking strategy; do not add distributed locks, Redis or a queue without a verified requirement. Database failure rolls back related source, Fund, projection and audit effects together.

## Financial event foundation (not the finance engine)

Every financial write follows this technical shape:

```text
Authorized financial command
  → current-position validation under transaction/lock
  → immutable authoritative source event and required linked records
  → atomic persistence and audit
  → rebuildable/reconcilable current-position projection
```

An authoritative event/history record is not a derived balance or report. Projections cannot be manually edited, cannot authorize an action, and must reconcile to source events. Corrections append linked history rather than overwriting finalized facts. This foundation does not restate or implement financial formulas; canonical 01/04/05 and `system-design/05` govern those rules.

## Testing and environment foundation

Backend Foundation testing includes domain/unit checks, API contract/error checks, account and permission allow/deny tests, Tenant isolation/object-scope tests, real PostgreSQL transaction and constraint checks, idempotency/retry/concurrency tests, financial event/projection invariants, audit safety and migration-safety checks. Test cases must prove actual backend enforcement; frontend-only or in-memory mocks cannot prove Tenant isolation or row-lock behavior.

Use isolated Local/Development data, Render Staging and production configuration only after a provider is selected. Externalize secrets and environment settings. Staging limitations cannot weaken business or security behavior. Readiness must not claim service readiness when critical database/startup/migration conditions prevent safe service. Production hosting remains unselected.

## Backend Foundation exit gate

Phase 2 frontend feature work may start only when all applicable items pass:

- PostgreSQL connection, schema/migration workflow and isolated environment configuration are verified.
- Project/module layering and API error/version/pagination conventions are stable.
- VIRMS account lifecycle and backend-controlled authentication work according to canonical rules.
- Active User, role, operation, Tenant membership, resource and object authorization are enforced with default deny.
- Owner authorized combined reads, Investor self-scope and Back Office read-only boundary have backend tests.
- DRF query/command boundary and real API test client path are ready.
- Sensitive command audit commits atomically without secrets.
- PostgreSQL transaction rollback and current-position revalidation patterns are proven.
- Duplicate/retry and concurrency controls are demonstrated for the foundation's critical operations.
- Immutable event versus projection ownership is established without an editable-balance path.
- Unit, API, permission, Tenant isolation, database transaction and invariant test infrastructure runs.
- Environment/readiness and safe logging configuration are established.
- Backend correctness and verification can run without a frontend being present.

A running Django process alone is not an exit gate. No business module is declared complete by this foundation.
