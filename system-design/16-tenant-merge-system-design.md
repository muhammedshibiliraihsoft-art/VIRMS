# 16 — Tenant Merge system design

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical source: docs-final/supporting/tenant-merge-consolidation.md, with identity/access rules in 02/04. This is a rare controlled Back Office or migration procedure, not a normal operational UI.

## Controlled stages

| Stage | Required evidence and action |
|---|---|
| Preflight | Identify environment and Source/Target UUIDs; inventory active Vehicles, sold/open finance, memberships, configuration, media, jobs, reports, caches and conflicting writes; classify safe mappings, manual review and blockers |
| Reviewed manifest | Operation UUID, actor, cutover, approved transfer list, access mapping, target configuration decisions, unresolved Source positions, expected counts, validation and recovery plan |
| Dry run/rehearsal | Simulate mappings and constraints against a safe environment, report conflicts and counts without mutating production history |
| Cutover | Control new Source writes, revalidate manifest/permissions, transfer only approved continuing operational scope via Vehicle Tenant History and explicit memberships |
| Legacy completion | Keep authorized Source access for outstanding receivables, corrections and settlements; Target membership alone does not grant it |
| Finalization | Validate identities, counts, financial reconciliation, membership scope, media/public safety, reports/jobs; retain Source UUID and mark inactive/archived/consolidated only when appropriate |

Global User, Owner, Investor, Investor Fund and agreement identities are never duplicated. Vehicle UUID and one-Investor link remain. Historical Fund, Expense, Sale, payment/refund, snapshot, Profit, Settlement, Labour, publication and audit rows retain their original Tenant context. Buyer/Labour/Category are not auto-merged by names, phone or labels. Target's approved configuration governs future Target operations; historical snapshot/configuration remains intact.

Active continuing Vehicles may change current Tenant only through an approved transfer event. Sold Vehicles with unresolved receivables ordinarily remain under Source financial context and complete with controlled Source access. A proposed exception moving unresolved financial positions requires separate proof of history/idempotency/reconciliation and cannot be inferred from this design. Consolidation itself posts no Fund money, Profit/Loss, recovery or settlement.

Execution uses reviewed checkpoints, deterministic operation IDs, short transaction units and idempotent re-entry, with appropriate cutover write controls and no unbounded locks. Preserve manifest, actor/time, mappings, counts, warnings, failure and recovery reference. Restore/recovery is planned before mutation. Once Target activity exists, do not blindly reverse by deleting history; use controlled recovery preserving audit. No dedicated self-service Merge UI is assumed.
