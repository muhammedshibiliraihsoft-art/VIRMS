# 18 — Technical decision register and ADRs

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


These are technical decisions subordinate to /docs-final/. They cannot settle a missing business, permission or privacy rule. A later phase may revise an ADR with evidence while preserving traceability and canonical constraints. Production hosting is intentionally undecided.

## ADR-01 — Modular monolith with explicit application commands

**Context:** Multiple financial modules share one PostgreSQL transaction and immutable history. **Decision:** Django/DRF modular monolith with scoped packages and application command services; no network microservices. **Reason:** Atomic source/Fund/audit writes and simpler authorization. **Alternatives:** Microservices or a generic CRUD monolith. **Trade-off:** Package boundaries require discipline and integration tests. **Canonical constraints:** docs-final/06 stack and no premature distributed infrastructure.

## ADR-02 — Backend-controlled browser session

**Context:** An authenticated ERP has sensitive finance and no external identity provider requirement. **Decision:** Django-managed opaque session in Secure HttpOnly cookie with CSRF, rotation and revocation. **Reason:** Server controls credential lifetime and permission revalidation. **Alternatives:** Long-lived browser tokens or external SSO. **Trade-off:** Cross-origin/CORS and CSRF deployment configuration need care. **Canonical constraints:** docs-final/06 Authentication and supporting authentication; no invented MFA/recovery flow.

## ADR-03 — One database transaction per financial command

**Context:** A real action may affect source record, Fund, adjustment and audit. **Decision:** Application service posts all database effects atomically with stable row-lock order, constraints and idempotency. **Reason:** Prevent partial or duplicate economic effects. **Alternatives:** Eventual distributed saga or view-only checks. **Trade-off:** Commands must keep transactions short and avoid external I/O while locked. **Canonical constraints:** docs-final/04/05/06 financial and concurrency invariants.

## ADR-04 — Immutable events with rebuildable current projections

**Context:** Corrections preserve old truth but operators need fast current views. **Decision:** Keep source/correction/payment events append-only; materialize versioned current positions only when justified, reconcilable and rebuildable. **Reason:** Audit and current operability without editable balances. **Alternatives:** Overwrite amount/status fields or compute every report from a full scan. **Trade-off:** Projection versioning/rebuild validation adds work. **Canonical constraints:** docs-final/04/05 immutable history and single financial authority.

## ADR-05 — Explicit business command API

**Context:** Generic PATCH can obscure payment, refund and correction authority. **Decision:** Versioned DRF resource reads and explicit POST commands for consequential actions, with idempotency key and current-state response. **Reason:** Clear authorization, validation and audit boundary. **Alternatives:** Generic CRUD mutation of finance rows. **Trade-off:** More endpoint contracts. **Canonical constraints:** docs-final/02 backend authorization and 05 actual-confirmation semantics.

## ADR-06 — Scoped read models and public projection

**Context:** Same underlying Vehicle has different private/public views. **Decision:** Central scope evaluation and separate role/field read models, including a dedicated published public schema. **Reason:** Prevent frontend hiding or serializer reuse from leaking data. **Alternatives:** Send broad entity then filter in React. **Trade-off:** More query/serializer definitions. **Canonical constraints:** docs-final/02/06/07/08.

## ADR-07 — Media intent/finalization behind S3-compatible port

**Context:** R2 object writes do not share PostgreSQL ACID commit; active image count and publication must remain correct. **Decision:** Private pending upload intent, backend validation, deterministic object key/version, finalization under Vehicle lock and cleanup of orphans; adapter isolates R2. **Reason:** Retry-safe storage and provider portability. **Alternatives:** Permanent server filesystem or browser-owned R2 credentials. **Trade-off:** Pending/failure state needs monitoring. **Canonical constraints:** docs-final/08 and 06 R2/provider boundary.

## ADR-08 — TanStack Query for server state, local state for forms

**Context:** Financial screens need fresh authorized positions and resilient forms. **Decision:** React Router route shell, TanStack Query scoped keys/invalidation and separate local review-form state. **Reason:** Avoid stale cross-Tenant data and false success. **Alternatives:** Global mutable financial store or full client ledger download. **Trade-off:** Query keys and invalidation need tests. **Canonical constraints:** docs-final/06/07 UI stack and server authority.

## ADR-09 — No queue/cache dependency by default

**Context:** Initial workload has no verified need for Redis/Celery. **Decision:** Keep core commands synchronous; introduce background jobs or cache only after measurement and a narrow interface. **Reason:** Fewer failure modes while preserving correctness. **Alternatives:** Start with a distributed worker/cache stack. **Trade-off:** Heavy media/report work may need a later job design. **Canonical constraints:** docs-final/06 and production standards.

## ADR-10 — Controlled Tenant Merge as administration

**Context:** Consolidation is rare and history-sensitive. **Decision:** Reviewed manifest, preflight/dry run, checkpointed transfer and explicit Source legacy access; no routine Merge button. **Reason:** Preserve UUIDs, permissions and money history. **Alternatives:** Blind Tenant ID rewrite or generic self-service merge. **Trade-off:** More operator review. **Canonical constraints:** supporting/tenant-merge-consolidation.md.

## ADR-11 — Risk-scaled engineering review

**Context:** Financial, tenancy and security changes carry more risk than routine UI/doc work. **Decision:** Classify work ROUTINE, STANDARD or HIGH-RISK. For HIGH-RISK work use the strongest available reasoning configuration supported by the active Codex environment; if automatic routing is unavailable, state the recommendation so the operator can choose. **Reason:** Match verification effort to impact without coupling correctness to a commercial model name. **Alternatives:** One fixed model/effort for all work. **Trade-off:** High-risk review costs more time. **Canonical constraints:** docs-final/06 and production standards test/audit cadence. No automatic routing capability is assumed.

## Open technical choices

Exact table/route names, lock granularity proved by implementation, performance budgets, job mechanism if needed, provider-specific CI wiring and production hosting remain phase/release decisions. None authorizes a new business behavior.
