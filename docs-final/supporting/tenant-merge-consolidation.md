# Tenant Merge & Consolidation

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — SUPPORTING CONSOLIDATION SOURCE OF TRUTH

## Purpose and authority

Tenant consolidation is a rare Back Office/controlled system administration operation. It is not Owner, Accountant, Investor, Media, public API or routine UI self-service. If a dedicated Back Office workflow is unjustified, a controlled administrative/migration procedure is acceptable. It must not make the core application merge-centric.

Source Tenant is the Garage whose future operations move; Target Tenant continues operations. Source and Target retain their original UUIDs. Source remains a historical Tenant, not a deleted or silently rewritten identity.

## Identity and historical truth

- Global User, Owner, Investor, Investor Fund, agreement, ledger and lifecycle identities are not duplicated by consolidation. Vehicle UUID and its one-Investor relationship remain unchanged.
- Historical records retain their original Tenant/Vehicle context: Fund entries, Expenses, Sales, Buyer Payments, correction-created Buyer Refund Payables and actual refunds, Profit/Loss snapshots, percentage history, Profit Payments, Settlements, Labour Payments, media/publication and audit.
- An active Vehicle that must continue under Target may change current Tenant only through a controlled transfer with Vehicle Tenant History. Completed/historical Vehicles normally retain Source context. Never rewrite financial history merely for a cleaner Target view.
- No record is auto-merged by name, phone, registration, category label, title or filename. Buyer, Labour and Expense Category identities remain Tenant-scoped and historical references remain intact.
- Target's approved configuration governs future Target activity. Source historical configuration and completed-deal snapshots remain unchanged; any necessary Target configuration change requires an explicit authorized decision.

## Staged consolidation

1. **Preflight:** identify Source/Target UUIDs and environment; inventory active Vehicles, open receivables, payments, settlements, corrections, configuration, memberships, media, jobs and constraints. Classify safe mappings, manual reviews and blockers. Blocking conflicts stop execution.
2. **Reviewed manifest:** record operation identity, actor, cutover, transfer list, membership mapping, configuration decisions, unresolved Source positions, expected counts and validation checks. Execute the reviewed decisions rather than discovering them during mutation.
3. **Operational cutover:** control new Source operations, move only approved continuing operational scope to Target, preserve Vehicle Tenant History and source financial context.
4. **Legacy completion:** Source may remain available under explicit authorization for open receivables, corrections, settlements and historical review. Target membership alone never grants Source access.
5. **Finalization:** after required legacy positions resolve, mark Source inactive/archived/consolidated or equivalent while retaining UUID, history and merge audit. Target continues with its own UUID.

## User and permission safety

- A User is global; do not duplicate them because they belonged to both Tenants. Treat identity and Tenant Membership separately.
- Source-only Users continuing in Target need explicit Target assignment. Existing dual memberships are reconciled without duplicate active assignments or automatic privilege union. Preserve Source membership history.
- Owner retains authorized Source history and Target/combined read visibility but no operational or merge write permission. Accountant may receive explicit temporary Source/Target operational scopes for legitimate legacy work but cannot perform Tenant Merge.
- Tenant isolation remains backend-enforced before, during and after merge. A known Source/Target UUID is never authorization.

## Financial, media, and infrastructure safety

- Consolidation itself must not add Fund, recover principal, allocate profit/loss, change Investor exit state, close a Settlement or recalculate historical deals. Normal independently authorized workflows handle open positions.
- Sold Vehicles with unresolved receivables normally keep Source financial context and complete under controlled Source access. Any proposed movement of unresolved financial positions must prove history, audit, idempotency and reconciliation without inventing a new rule.
- Media assets stay attached to the same Vehicle UUID; avoid duplication for Tenant movement. Public responses remain limited to approved safe fields and reveal no merge internals.
- Account for Tenant-aware caches, search indexes, reports, exports, jobs and notifications. Stale Source operational access must not survive cutover; Target views must include approved transferred records without losing origin traceability.

## Execution and recovery controls

- Before production mutation: identify environment, verify backup/checkpoint and restore path, rehearse where feasible, and accept the merge manifest.
- Prevent conflicting writes around cutover through operational controls and revalidation. Execute with appropriate transaction boundaries, checkpoints and repeat-safe behavior; avoid unbounded locks or uncontrolled row-by-row mutation.
- Persist durable audit of operation, actor, Source/Target, times, mappings, affected counts, transfers, warnings, completion/failure and recovery reference. Never log secrets.
- Define rollback/recovery before execution. After new Target activity exists, do not blindly reverse by deleting or rewriting financial history; use a controlled recovery path that retains merge audit.
- Post-merge validation checks identities, counts, Vehicle Tenant History, finance reconciliation, membership permissions, Owner read-only access, media/public safety, reports, caches, jobs and Source/Target isolation.

## Non-scope

No generic acquisition workflow, routine Merge button, automatic cross-Tenant Buyer/Labour/category unification, automatic configuration blending, duplicated global Investor/Fund, or financial ledger reposting solely for consolidation.
