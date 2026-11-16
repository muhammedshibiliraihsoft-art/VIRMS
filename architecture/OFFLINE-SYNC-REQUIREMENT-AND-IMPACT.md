# Offline Accountant Work and Cloud Synchronization — Requirement and Impact

Status: DISCUSSION DRAFT; NOT ARCHITECTURE LOCKED; NO IMPLEMENTATION AUTHORIZED BY THIS DOCUMENT. Recorded 2026-11-09 from the user's discussion. Existing business permissions, accounting rules and approval settings remain applicable; this document does not resolve unspecified policies.

## Stated requirement

- With Internet, users retain their existing authorized actions and Company/Branch scope.
- During Internet loss, the main Accountant's designated computer should allow offline entry, including Income and Expense. Other users should have read-only access to whatever data is actually available to them; offline availability and prior authorization require further design.
- On reconnection, fetch current cloud state and submit locally recorded entries. Successful cloud acceptance and conflict/review states must be visible; no silent duplicate or false claim of cloud persistence.
- A shared office server is not requested. The user wishes to discuss this architecture now and continue the remaining Phase 5 work afterward; implementation timing and scope remain to be decided.

## Repository evidence and material change

- `demo/react/src/api/client.ts` uses same-origin API requests and `cache: no-store`; `queryClient.ts` holds query state in memory. `accountingApi.ts` stores a retry key in sessionStorage for the current intent, which does not establish durable offline sync or deduplication across device/session loss.
- `apps/accounting/services.py` applies authorization, module checks, transaction/Company and target locking, and idempotency on the server. Another authorized user can continue changing cloud state while the Accountant is offline; local inputs therefore cannot be presumed valid at replay time.
- The Phase 1 implementation plan explicitly excluded SQLite/desktop packaging, offline writes, queue and sync/conflict engine from that phase. It is a historical phase boundary, not proof that the user cannot approve a future feature. Persistent private-data retention was also gated there; the current request establishes direction but does not settle its security design.
- `docs-final-v2/06-technical-architecture-engineering-operations.md` assigns authoritative business and financial rules to Django/PostgreSQL, and requires scoped permissions, transactional writes and no stale financial authority in cache. Offline accepted local entries introduce an unsynchronized operational record and must be explicitly reconciled with that contract; neither local acceptance nor an offline balance proves a cloud-posted financial event.
- `docs/phase5-execution-progress.md` records Phase 5 backend as partial and React Investment/Vehicle/Fund as mock-based at its checkpoint. This requirement does not establish Phase 5 completion or remove the existing purchase/payable technical gate.

## Candidate architecture, not a locked design

1. An approved main-accountant device would retain a protected, Company/user-scoped local store and durable pending operation queue, distinct from the cloud financial ledger. Web IndexedDB versus a Windows shell/database is UNDECIDED; browser storage can be cleared/evicted and desktop packaging adds operational work.
2. Each permitted operation needs durable stable intent identity, original actor/Company/Branch, payload, creation time, and status. Example states for design: local pending, transmitting, cloud confirmed, conflict/rejected and unknown outcome. These are proposed UI semantics, not existing functionality or final business rules.
3. On reconnect the client re-establishes authenticated scope, module state and permissions, retrieves current server state, then submits the same intent with a stable key. Server processes each operation via existing authorized transactional services, with fresh validation. Replay ordering, dependent records and conflict handling need an explicit contract.
4. A request committed before connection loss needs same-intent retry/status reconciliation. A device loss before cloud confirmation can lose pending entries unless an independently recoverable local backup exists. Cloud backups do not contain unsynced entries.
5. Cloud-confirmed totals, offline pending entries and provisional local display must be distinguishable. Other users can only see authorized cached data if a separate offline access/retention design permits it; internet-connected users continue normal permitted workflows.

## Open decisions and technical blockers

- BUSINESS DECISION REQUIRED: exactly which Income/Expense actions and fields are allowed offline, whether additional workflows including payments, receipts, corrections, Fund and Vehicle actions are allowed, and whether offline entries are drafts, binding commitments, or another expressly defined business state.
- BUSINESS DECISION REQUIRED: what may be shown/edited offline to which users; designated-device authorization, offline sign-in/session expiry and revocation behavior, device replacement, pending-operation retention and approval mode on reconnection.
- BUSINESS DECISION REQUIRED: how to handle conflict with online users, stale balance, insufficient outstanding amount, corrected/archived category/account, Branch reassignment, module OFF, changed permissions, and partial sync; who reviews, retries, amends or cancels each case.
- TECHNICAL BLOCKER: per-device idempotency and reconciliation across lost sessions, device replacement and database restore; duplicate *business* intent versus safe transport retry; sequence/dependency semantics, replay limits and API response contracts.
- TECHNICAL BLOCKER: trusted local storage/encryption and key custody, cached-data segregation, revocation/expiry, backup and recovery of pending operations, device compromise, quota/eviction, audit and privacy; no secret values in the queue or documentation.
- TECHNICAL BLOCKER: prove transaction/authorization invariants against concurrently changed cloud state, preserve historical effective time and audit chronology, reject stale invalid financial submissions without partial writes, preserve pending operations on failure, and prevent duplicate cloud effects.
- TECHNICAL BLOCKER: explicit API cost and freshness measurements, desktop/browser platform choice, compatibility with existing no-store policy, offline app availability, update/migration of local state and observability of unresolved operations.

## Phase 5 compatibility and next step

Offline sync is a cross-cutting future architecture addition, not an already available Phase 5 capability. Preserve existing online API/permissions and business history; do not silently insert an offline queue into current mutations. First resolve the business decisions and produce a separately reviewed end-to-end impact/design including phase sequencing, then implement only within explicit authorization. Meanwhile continue the pre-existing Phase 5 seller-payable architecture work: typed purchase/payment/refund linkage, outstanding validation, correction ordering, transactions and idempotency. Do not infer those technical contracts are locked merely because the business decisions have been recorded.

## Approved Phase 5 boundary — 2026-11-09

The user confirmed that Phase 5 business writes use the current online cloud/backend API. Offline financial entry and synchronization are a separate future system-wide phase. This supersedes only the earlier statement that Phase 5 timing/scope for offline writes was undecided. It does not change the separate requirement that the future offline design consider the designated Main Accountant's offline entry and other users' authorized read-only/offline-data behavior. The future design remains unimplemented and not architecture-locked.
