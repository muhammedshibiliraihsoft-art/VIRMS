# 11 — Concurrency, idempotency and failure design

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/01, 04, 05, 06, 08 and supporting production standards. Section 05 defines economic targets and caps. This document defines how one PostgreSQL-backed monolith preserves them under races and retries.

## Command execution protocol

1. Authenticate, parse a safe decimal amount and require an idempotency key for every critical financial write, settlement, image finalization and other non-repeatable command.
2. Begin a database transaction. Claim/retrieve a unique scoped key (actor + operation + resource + key) with a payload fingerprint. Exact retry returns the committed outcome; changed payload conflicts.
3. Lock the relevant Investor Fund or parent resource, then Vehicle/Sale, then recipient obligation/Settlement in a fixed order. Lock the parent even when a child current-position row does not yet exist.
4. Recheck role, Tenant/self/object authorization and the current authoritative position after locks. Reject nonpositive, excess, stale or invalid state without clamping or partial posting.
5. Append immutable source event, linked Fund movement if any, correction/projection update and audit in the same transaction. Use database uniqueness and check constraints as a second line of defense.
6. Commit, then return event identity and resulting version. Optional notification/AI/media work runs after commit and cannot roll back or redefine the financial outcome.

PostgreSQL READ COMMITTED with explicit row locks and constraints is the starting technical strategy. A phase plan must prove whether a command requires a stronger isolation level or a narrower lock to prevent a specific anomaly. Do not add distributed locks or Redis merely for ordinary single-database commands. Deadlock/serialization retries are bounded and reuse the same idempotency key; an ambiguous timeout is checked by key before another attempt.

## Critical lock and invariant matrix

| Position / command family | Lock/version anchor | Revalidation and duplicate defense |
|---|---|---|
| Available Fund; capital, purchase, Expense, return, refund, principal settlement | Investor Fund/Investor position row | Recompute ledger/reserves; check same-Fund amount and source-event uniqueness |
| Buyer Receivable and Buyer Payment | Fund then Sale and Vehicle | Current price/applied receipts; 0 < payment <= receivable; unique receipt/idempotency key |
| Buyer Refund Payable and actual refund | Fund then Sale/correction chain | Current payable, held reserve and latest corrected price; 0 < refund <= payable; unique refund source |
| Principal allocation/reclassification | Fund then Vehicle/Sale/receipt chain | Net applied receipt and OVP; one allocation effect per linked version; no second receipt |
| Profit entitlement and payout | Fund where relevant, then Sale/recipient chain | Full eligibility, Investor-before-Owner gate, 0 < payout <= current outstanding |
| Profit Recovery Obligation | Recipient correction chain | 0 < actual recovery <= current obligation; actual recovered only once |
| Owner Contribution Obligation | Fund then Vehicle/Owner chain | 0 < contribution <= current obligation; Fund credit and coverage in one transaction |
| Owner Return Payable | Fund then Owner return chain | 0 < return <= payable and available same-Fund money; debit and payable reduction together |
| Principal Settlement Payable | Fund then global Settlement | 0 < payment <= payable and Available Fund; claim/debit/payable reduction together |
| Corrected financial position | Fund then affected Sale/Vehicle/recipient chain | Original snapshot, cumulative actual effects and existing open adjustment; one target version |
| Four-active-image limit and Primary | Vehicle then image slots | Count active/reserved slots under lock; one Primary when active count > 0; idempotent finalization |
| Tenant Merge cutover | Source/Target controlled operation and affected roots | Approved manifest/checkpoints, access freeze/revalidation and repeat-safe transfer IDs |

The lock order is a technical deadlock-avoidance convention, not a new money priority rule. Commands involving only a recipient adjustment need not lock an unrelated Fund row unless their operation affects it; the same ordered hierarchy applies when it does. Materialized position rows carry versions/watermarks and must reconcile to source events inside the transaction.

## Retry and failure outcomes

- Double-click/parallel sessions: one command commits; the other replays the exact idempotent outcome or receives a current-position conflict. No aggregate overrun.
- Timeout after success: client queries the idempotency key/command status before retrying. It never claims failure or reissues a different key blindly.
- Validation failure or stale UI: retain entered form values, show latest authoritative cap/state and require a fresh review.
- Database transaction failure: rollback source event, Fund effect, projection and audit together; emit safe correlation ID and no false success.
- Optional notification/AI/media delivery failure: preserve committed core result, record a bounded retryable operational task if needed, and localize the failure.
- External R2 upload cannot join a database transaction; a Pending intent, deterministic object key, post-write verification, finalized metadata and orphan cleanup converge safely.
- Repeated job execution is idempotent by operation/source identity and Tenant context; bounded retry/backoff, visible failed state and manual recovery are preferable to infinite loops.
- Current-position projections can be rebuilt from immutable source chains after a fault. Reconciliation failure blocks affected financial write/closure and raises an operational alert rather than inventing a balancing entry.

No command silently nets Buyer refund, Owner return, Investor recovery, Profit payment or principal settlement against another category. A reserve release is a designation change and never a Fund credit. These economic constraints remain governed by docs-final/05.
