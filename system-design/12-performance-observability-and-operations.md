# 12 — Performance, observability and operations

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/06, 07, 08 and supporting production engineering standards.

## Performance without premature infrastructure

Start with bounded PostgreSQL queries, proper indexes and server pagination. Common access paths are Tenant/status/time Vehicle lists, Investor/global Fund history, Sale receipt/refund chain, correction history, authorized reports and publication queries. Use select/prefetch strategies to avoid N+1 reads. Dashboards fetch purpose-built bounded summaries; do not download an entire ledger into React to filter it. Reports are read projections over source records and remain rebuildable. Cache only non-authoritative or versioned scoped queries after measurement; invalidation follows committed source events and preserves Tenant/field scope. A stale cache cannot authorize or post money.

React routes split where useful, keep the shell responsive on lower-end phones, avoid heavyweight galleries and unbounded tables, and prevent fonts/images from blocking core text. Use optimized image variants, aspect-ratio reservation and localized media errors. Important UI verification includes narrow screens near 360px, slow network/CPU, cold cache, open keyboard and interrupted requests. Define measurable LCP/INP/CLS, route bundle, API p95, DB latency/query count and image payload budgets once real implementation and target devices are known; no arbitrary canonical threshold is introduced here.

Background processing is introduced only when measured work needs it: expensive image variants, reports, notifications or retryable external I/O. A queue/worker is not a prerequisite for the initial monolith. Any job is Tenant-aware, bounded, idempotent, observable and resumable as appropriate. Core financial posting remains synchronous and transactionally authoritative.

## Operational signals

| Signal | Content and response |
|---|---|
| Structured request log | Correlation ID, safe actor/role reference, Tenant context, route, outcome, duration and error class; never credentials, tokens or full private payload |
| Business audit | Immutable actor/object/source/reason/time evidence from command transaction; separate from operational logs |
| API/DB metrics | p95 latency, query count, slow query and error rate by route/class, bounded cardinality |
| Financial integrity | Reconciliation failure count, duplicate/conflict rejection, open unresolved positions; no sensitive amounts in broad telemetry |
| Media/jobs | Pending/failed processing, orphan cleanup, bounded retry attempts, storage errors |
| Health/liveness | Lightweight process signal without business data |
| Readiness | Database/migration/startup and other critical workload dependencies; never false-ready |
| Optional dependency status | AI, notification or media degradation signaled separately where core business remains usable |

Alerts target repeated failures, unhealthy readiness, failed jobs, storage processing failures, abnormal API/query latency and financial reconciliation exceptions. A correlation ID links safe operational diagnostics to protected audit/source records without copying secrets into logs.

## Recovery and maintenance

Identify environment before migrations, data correction, restore or infrastructure changes. Maintain backups and a tested restore procedure that checks source-event counts, Fund/claim reconciliation, permission/Tenant isolation and media references. Stage schema changes with compatible deploy order, lock awareness and batched resumable backfill when needed. Releases have a rollback or forward-fix path; a targeted kill switch is permissible for risky optional behavior, never to bypass finance/security invariants. Production is not a debugging sandbox.

Local, staging and production use the same business code and behavior. Provider-specific monitoring/probes/configuration stay in deployment/infrastructure. Choose additional cache/queue/search infrastructure only from measured need and a recorded decision.
