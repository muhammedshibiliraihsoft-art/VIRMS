# VIRMS — Integrated Module Delivery Architecture

> **Status: HISTORICAL / SUPERSEDED V1-DERIVED DELIVERY PROPOSAL. CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the living maps. Missing behavior is an **IMPLEMENTATION GAP**; unresolved meaning is **BUSINESS DECISION REQUIRED**. This proposal is not an approved V2 module order or authorization to implement.

## Purpose

This document records a previously proposed integrated-module delivery pattern. Its foundation prerequisites and module sequence are not approved V2 requirements; no V2 delivery contract or implementation order is set here.

## Source Basis

### V2 target sources (business boundary only)

- `docs-final-v2/01-business-rules.md` through `10-garage-jobs-workflow.md`
- `docs-final-v2/supporting/production-engineering-standards.md`
- `docs-final-v2/supporting/tenant-merge-consolidation.md`

### Historical System Design references

- `system-design/00-authority-and-design-contract.md`
- `system-design/02-domain-and-module-architecture.md`
- `system-design/04-data-and-persistence-design.md`
- `system-design/05-financial-engine-design.md`
- `system-design/06-workflows-state-machines-and-corrections.md`
- `system-design/07-backend-application-and-api-design.md`
- `system-design/08-frontend-and-ui-shell-design.md`
- `system-design/09-media-storage-and-publication-design.md`
- `system-design/11-concurrency-idempotency-and-failure-design.md`
- `system-design/13-testing-verification-and-quality-strategy.md`
- `system-design/19-requirement-traceability-matrix.md`

### Historical derived architecture

- The former proposal grouped backend, API, frontend and integration into a reviewed module slice.
- It described shared foundations for identity, authorization, Company/Branch scope, transactions, audit, API, session, tests and UI.
- These remain a historical delivery pattern, not a current V2 implementation contract.

### Business decisions

No decisions are resolved by this historical proposal. Applicable V2 open decisions are listed below and in `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.

## Historical V1-derived module workflow proposal

For each module, in order:

1. Read its exact canonical business, permission, data, finance, UI and operational rules.
2. Read the relevant System Design sections and traceability rows.
3. Inspect current branch/repository state and completed modules.
4. Create and review a detailed architecture plan for this module only.
5. Define module-owned data and state, backend operations, API contract, scopes and UI behavior without duplicating another authority.
6. Implement backend domain and persistence within the existing modular monolith.
7. Implement application commands/queries and transaction, concurrency, idempotency and audit behavior as required.
8. Expose the approved API contract and verify server-side authorization and Tenant/object scope.
9. Implement the frontend feature against the real API, including loading, validation, denial, conflict, timeout and success states.
10. Verify audit/history and financial/data invariants that apply to the module.
11. Run focused tests, related integration and regression checks; audit changes against the actual repository.
12. Mark complete only when the module Definition of Done below is met; then plan the next module from current evidence.

## Historical proposal: module Definition of Done

A module is complete only when all applicable items are integrated and verified:

- backend domain behavior and persistence constraints
- application commands/queries with correct transaction ownership
- real API contract and error behavior
- backend authentication, permission, Tenant/resource/object and field scope
- frontend UI connected to the actual API
- loading, empty, validation, forbidden, conflict, timeout and failure behavior
- immutable audit/history and correction links where applicable
- idempotency/concurrency protection for non-repeatable or capped actions
- focused unit/API/permission/Tenant/invariant tests as applicable
- related integration/regression checks and documented evidence

Backend-only and UI-only work can be tracked as incomplete but cannot be called a completed business module. A visual mock, frontend route, endpoint, or model alone is not a delivered module.

## Historical V1 module progression — not approved for V2

The module progression below is a V1-derived historical proposal, not an approved V2 module order. It does not grant access or create a new business workflow.

| Historical slice group | V1-derived module focus |
|---|---|
| Foundation (separate prerequisite) | Backend Foundation, then Frontend Foundation + real integration; see documents 02 and 03 |
| Core investment/vehicle | Investor Management; Investor Fund & Ledger; Vehicle Management; Vehicle Expense Management |
| Sale/collection | Buyer / Customer; Sales; Receivables & Payment Tracking; Principal Recovery |
| Profit/Loss | Profit, Loss & Distribution; Owner loss coverage and payout ordering |
| Corrections/refunds/returns | Audit & Correction History; Buyer Refund adjustments; Profit recovery; Owner Contribution Return reconciliation |
| Exit/settlement | Investor Exit & Settlement and global closure checks |
| Ancillary/media | Labour; Media / Vehicle Publication; Public Vehicle Access; optional GST / Tax / Invoice Capability |
| Read/admin/AI | Dashboard; Reports; Tenant / Garage Management; User & Permission Management; Back Office; System & Business Configuration; Owner AI Assistant |
| Consolidation/release | Controlled Tenant Merge and release/readiness/recovery audit |

The V1-derived rows above are historical references only. They must not reintroduce automatic Loss, Owner Loss coverage, global Investor settlement or other superseded behavior. V2 module boundaries are in `/docs-final-v2/03` and related V2 documents; no V2 module order is locked here. Cross-cutting requirements in V2 apply within each future slice.

### Explicit open-decision gates

| Decision | V2 dependency | Blocks |
|---|---|---|
| BDR-1 — Monthly eligible-principal basis and active-cycle withdrawal limits | Monthly Interim Payout | Interim amount and affected reconciliation/settlement calculations |
| BDR-2 — Reconciliation deal inclusion and ordinary Profit/interim payment interaction | Investor reconciliation | Reconciliation payable/recoverable and affected final settlement |
| BDR-3 — Manual Loss impact, confirmation authority and closure effect | Loss and settlement | Loss posting and settlement of affected Loss positions |
| BDR-4 — Company distributable-Profit basis, recognition and period close/carryforward | Company Accounting / Owner Distribution | Distributable amount and Owner payout |
| BDR-5 — Cross-Branch correction authority and scope | Branch-scoped corrections | Corrections to another Branch's records |
| BDR-6 — Platform Back Office private-finance read beyond assignment | Back Office support | That private-finance access path |
| BDR-7 — Minimum settlement actions while a module is OFF | Module OFF / open obligations | Those module-OFF resolution actions |

These labels map to the deduplicated open decisions in `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`; this table does not resolve them or assign a V2 phase order.

## Integration rule

The former proposal's reusable delivery flow is:

```text
V2 business target → Reconciled technical design → Module scope
  → Backend Domain/Persistence → Application Operation → API
  → Frontend UI → Real API Integration → Authorization/Tenant Scope
  → Audit/History → Tests → Regression → Module Complete
```

The backend remains authoritative. The UI never invents a contract, calculates authoritative money, grants permissions, or bypasses a V2 module dependency. This historical pattern creates no detailed module architecture and does not make unreconciled System Design authoritative.
