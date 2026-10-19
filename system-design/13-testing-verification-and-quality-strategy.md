# 13 — Testing, verification and quality strategy

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/01–08, especially 05 and 06 Verification cadence, plus supporting production standards and authentication/Tenant Merge.

## Test layers

| Layer | Required evidence |
|---|---|
| Domain unit | Decimal INR, snapshot selection, balanced paise, principal-first allocation, correction targets, payout/settlement gates |
| Property and exhaustive small-domain | Conservation, nonnegative Owner allocations/positions, deterministic ties, 0%/100% Investor boundaries, arbitrary configured Owner count, tiny paise pools |
| Application command | One source event and linked Fund/audit effect; valid partial payments; reject nonpositive/excess/stale amount; no cross-category netting |
| Persistence/transaction | Foreign keys, unique source/idempotency constraints, lock order, projection rebuild and rollback of partial failure |
| Authorization/Tenant | Every role's allow/deny contract, Investor self-scope, Owner authorized union, Back Office finance read-only, Media/public privacy, cross-Tenant IDOR |
| API contract | Versioning, error semantics, pagination/filtering, public-safe serialization, command idempotency and request fingerprint |
| Concurrency | Parallel Buyer payments/refunds, payouts/recoveries, Owner contributions/returns, principal settlements, Fund uses and image uploads |
| Correction chains | Repeated same-side and crossovers, actual partial recoveries/refunds/returns, reserve release, post-closure correction, immutable source reconstruction |
| Frontend component/navigation | Role shell, Tenant context, financial labels, review/confirmation, safe loading/error/timeout/offline, no false success |
| End-to-end critical flow | Capital → purchase/Expense → Sale → partial/full collection → recovery → Profit/Loss settlement → Investor Exit; media/public and account recovery |
| Migration/storage/operations | Upgrade with existing data, rollback/restore rehearsal, R2 adapter failure, private/public object access, health/readiness and production smoke |

Use real PostgreSQL transaction tests for row-lock and uniqueness behavior; in-memory mocks cannot prove concurrency. Mathematical tests include brute-force small paise pools and property-based random valid percentages, including half-paise over-rounding, negative residual reconciliation, Loss allocations and exact conservation. Test principal/Fund examples from canonical 05, not only an implementation-derived expected value. Check immutable history plus current projection after each correction.

## Critical scenario inventory

- A profitable deal with full and partial collection; loss deal with partial then complete actual Owner coverage; 0%/100% Investor share.
- Buyer payment exactly at/above receivable, downward Sale correction, partial/full refund, upward correction before and after an actual refund, principal-backed reserve and uncovered liquidity.
- Profit paid pre-Exit, correction to less Profit, actual partial recovery, correction to more Profit, Investor-before-Owner gate and historical payout not duplicated.
- Same-side Loss increase/decrease, Investor recognition reversal, Owner contribution obligation versus return payable, Loss-to-Profit and Profit-to-Loss-to-Profit chains.
- Redeploy recovered principal, partial principal settlement, final principal-first settlement, blocked closure with receivable/refund/Locked Principal or unpaid obligation, post-closure correction history.
- Two sessions and retry-after-timeout for each capped write; an idempotency key with changed payload must conflict.
- Unauthorized Investor ID, cross-Tenant Buyer/Vehicle, Owner write, Back Office ordinary finance write, Media finance request and public internal-field leak attempt.
- Four concurrent media upload slots, Primary repair, bad MIME/content, R2 failure and public unpublish/cached variant.
- Tenant Merge preflight conflict, dual membership mapping, unresolved Source receivable, retryable cutover and preserved historical context.

## Cadence and exit evidence

Task change: focused relevant checks. Related batch: integration/regression of affected boundaries. Finance/auth/Tenant foundation or phase completion: broader invariant, security, history, concurrency, performance and recovery audit. Before a production release, rehearse migration, backup/restore and smoke tests against the target environment. Independent audit findings become changes only after reproduction against actual code/evidence.

A phase exit report records changed paths, canonical trace links, tests run, result, observed metrics where relevant and material limitations. No invented test result is claimed by this design document; no application exists yet.
