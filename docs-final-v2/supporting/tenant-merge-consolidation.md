# Tenant Merge & Consolidation

Status: DRAFT V2 — supporting controlled consolidation source after approval

## Purpose and authority

A Tenant is a Company. Company/Tenant consolidation is a rare controlled Platform Back Office/system administration operation, not an Owner, Accountant, Investor, Media or public self-service action. A dedicated UI is not required if a reviewed administrative procedure is safer. Moving a Vehicle between Branches *inside one Company* is ordinary controlled Vehicle movement under 04/10, not a Tenant Merge.

Source Company is the Tenant whose future operations would move; Target Company is the continuing Tenant. Both original UUIDs and historical Company context remain. A consolidation cannot silently turn two Companies into one pre-existing financial identity or bypass their original isolation during review.

## Identity and historical truth

- Preserve original Company, Branch, User membership, Owner recipient, Investor/Fund, Vehicle, Job, Sale, Buyer Payment/refund, Company Ledger, Running Capital, Interim Payout, reconciliation, Owner Distribution, media and audit identity/history. No record is auto-merged by name, phone, registration, category label or filename.
- An approved active Vehicle continuing under Target needs a controlled transfer or equivalent reviewed transition with origin, Company/Branch movement and audit history. Completed historical records normally retain Source context. Never rewrite financial history to simplify a Target report.
- Source and Target module enablement, percentage agreements, Owner distribution configuration, cycle rules and historical snapshots remain distinct. Target configuration governs future approved Target activity only after explicit authorized decisions; it does not recalculate completed Source activity.

## Staged controlled operation

1. Preflight identifies Source/Target Company UUIDs and environment; inventories Branches, memberships, active Vehicles/Jobs, open Buyer/customer receivables, Funds, Running Capital, interim/recoverable/Owner distribution positions, corrections, media, configuration, jobs and constraints. Blocking conflicts stop execution.
2. A reviewed manifest records operation identity, actor, cutover, transfer list, Branch mapping, membership mapping, module/configuration decisions, unresolved Source positions, expected counts and validation checks. Do not discover business decisions during mutation.
3. Operational cutover controls new Source activity and moves only approved continuing scope, retaining origin and financial history.
4. Source remains available under explicit authorization for open receivables, corrections, reconciliations, settlements and history. Target membership alone never grants Source access.
5. Finalization may mark Source inactive/archived/consolidated after necessary positions resolve, while retaining identity and audit. Target continues with its own UUID.

## Permission, finance and media safety

Global authentication identity does not automatically union Source and Target Company business permissions. Continuing Users need explicit Target membership and Branch assignments; preserve Source access history. Owner retains only authorized read access; Accountant may receive explicit temporary operational scope but cannot perform Company Merge. Backend Company isolation remains enforced throughout.

Consolidation itself does not add Investor Fund, recover principal, create Company Share, settle interim/recoverable positions, allocate Owner Profit, change Investor Exit, close a Sale or calculate Loss. Normal independently authorized workflows handle open money. Sold Stock Vehicles with unresolved Buyer balances normally retain Source financial context until an explicitly reviewed approach proves exact history, reconciliation and authorization. Media remains attached to stable Vehicle identity, without unsafe duplication or public disclosure of merge internals. Account for Company/Branch-scoped caches, search, reports, exports, jobs and notifications.

## Execution and recovery controls

Before production mutation identify environment, confirm backup/checkpoint and restore path, rehearse where feasible and accept the manifest. Prevent conflicting writes at cutover; use bounded transaction/checkpoint and repeat-safe behavior. Record durable actor, Source/Target, time, mappings, affected counts, transfers, warnings, failure/completion and recovery reference, without secrets. Define rollback/recovery before execution. Once Target activity exists, do not blindly reverse by deleting or rewriting transactions. Validate identities, Branch movement, counts, financial reconciliation, module state, permissions, media/public safety, reports, caches and Source/Target isolation after the operation.

## Non-scope

No generic acquisition workflow, routine Merge button, automatic cross-Company customer/Labour/category unification, configuration blending, duplicated Investor Fund, or financial reposting merely for consolidation. Branch transfer within one Company does not require this procedure.
