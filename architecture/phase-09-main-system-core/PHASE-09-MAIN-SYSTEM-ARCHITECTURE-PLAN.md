# Phase 9 — Main VIRMS System Core: Architecture Plan

**Status:** `ACCEPTANCE PLAN — PHASE 8 INCOMPLETE; PHASE 9 ACCEPTANCE BLOCKED`

**Roadmap status:** `BLOCKED — PHASE 8 END CONDITION NOT MET`. This plan is an acceptance architecture, not a new owner of financial records. Current local Phase 8 work is partial and uncommitted; a connected read-only projection or focused test does not satisfy Phase 8 completion.

## Outcome and authority

The Main VIRMS operational system is usable for its required core workflows and has a verified backend position for the first separate portal. The [Malayalam scope](PHASE-09-SCOPE-DRAFT-ML.md) defines the product boundary. The V2 roadmap and canonical V2 rules take precedence over this plan. Later approved additions resolve several earlier decisions, as reconciled in the Phase 8 architecture; remaining missing records/APIs and unresolved source-recognition details still block acceptance and cannot be guessed by Phase 9.

## Current implementation boundary

The inspected worktree is `codex/phase5-investment-foundation` at `d57a9208` on 2026-11-19. Phases 4–7 have local completion records. Phase 8 source now includes partial result confirmation, gross-period projection, Company Accounting Result read, Investor binding/self portal and Exit request work; payment/reconciliation/final settlement/Owner distribution remain missing. Local completion does not establish deployed CI, staging, production, or database role permissions. The worktree contains substantial existing dirty Phase 5–10 work; preserve it.

| Capability | Owning source | Phase 9 work |
| --- | --- | --- |
| Authentication, sessions, Company/Branch roles and module state | Platform Core / Accounts / Tenants | Verify current authorization in every core flow and ensure Back Office has only its approved configuration authority |
| Actual Cash/Bank events and applications | Accounting | Verify one canonical movement per actual transaction and correct Company/Branch classifications |
| Investor Fund, principal and reconciliation | Investment; Phase 8 for integrated positions | Verify source-to-position-to-payment trace and Company-wide versus Branch permissions |
| Vehicle, purchase, cost and Sale | Vehicle Management | Verify one Vehicle UUID, one valid cost, Sale/Buyer cash history and corrections |
| Garage Jobs and Stock cost links | Garage | Verify Job source and Vehicle cost link without duplicate Vehicle cost or Accounting receipt |
| Main React Operations | Existing React app | Verify canonical API state after mutation/reload at desktop, tablet and phone widths |

## Acceptance architecture

**Inventory.** Build a machine-readable or tabular coverage map from each approved core action to its current UI route, API, domain owner, model/migration, permission gate, module gate, tests, and browser path. Mark each item `VERIFIED`, `MISSING`, `BLOCKED BY DECISION`, or `UNVERIFIED` with evidence. This map is an acceptance artifact, not another data source.

**Critical connected journeys.** Verify the Company/Branch login context; authorized Investor/Fund credit; Vehicle purchase and source allocation; Stock and customer Garage Jobs; direct/Job Vehicle cost; confirmed Sale and partial Buyer collection/refund; Accounting cash movement; Phase 8 principal/Running Capital/Profit position; actual settlement/Owner payout only where their policy is approved. Include corrections, historical display, and reload. Run on disposable PostgreSQL for financial mutations.

**Data and API flow.** The browser sends a scoped request to its owning endpoint. The server resolves the actor's Company and Branch rights, validates current module state and source identity, applies the domain transaction, and returns persisted canonical data. React updates only after a successful response; reload must show the same state. Classify each existing request as REQUIRED, CONDITIONAL, REDUNDANT, DUPLICATE, or UNKNOWN before considering API reduction. Do not merge separate cash and domain requests without proving one atomic source contract.

**Financial invariants.** Source prices, costs, Fund movements, Running Capital, Garage charges, Sale receipts/refunds, Investor/Company Profit and Owner allocation have distinct owners. An actual money movement is recorded once in Accounting and linked to its domain source. Pending receivables, proposed recoveries, calculated entitlements and reminders are not Paid. A correction retains original/effective history and cannot silently rewrite paid cash.

**Authorization and privacy.** Test Company isolation, object ownership, Branch assignment, Accountant action scope, Investor self-view, Owner read-only scope, Media/public field restrictions, and Platform Back Office configuration versus ordinary posting. A frontend route guard alone is insufficient. Company-wide Fund and cross-Branch Exit views remain Company-level Accountant operations. Existing action-specific module-OFF exceptions are not generalized.

**Schema and migrations.** Phase 9 should introduce no parallel financial ledger or duplicate identity. Any acceptance fix that needs a schema/API change gets its own impact report, migration compatibility check, focused tests and regression. Run fresh and replay PostgreSQL migration checks against disposable data; inspect historical rows before a destructive migration.

**UI and runtime.** Preserve the accepted React design, routes, navigation and mobile composition. Check loading, empty, error, disabled and stale states; no false success after failed mutation. Verify core flows at desktop, tablet, phone and narrow-phone widths. Distinguish source/build checks from authenticated browser and runtime/database observations.

## Ordered execution plan

1. **Gate Phase 8:** record its exact accepted end state and any exceptional behavior intentionally blocked by an unresolved V2 decision. Do not mark Phase 9 started before the roadmap dependency is met.
2. **Build coverage map:** enumerate each required core workflow and its source, API, permission and verification evidence. Inspect the current worktree and running service identity before testing.
3. **Close confirmed gaps:** fix only reproducible failures, in owning modules, with focused regression and migration checks. Preserve existing routes, contracts and unrelated dirty files.
4. **Run one integrated acceptance pass:** disposable PostgreSQL backend/API/migration/concurrency checks, React test/lint/build, and role-based browser journeys after related fixes. Verify exact persisted records and single cash effect.
5. **Audit risks and status:** classify A/B/C/D findings; resolve acceptance blockers, record deferred items with reason, and update only documents whose verified truth changed. Mark local versus CI/staging/production separately.

## Phase 8–10 combined delivery

Phase 8 financial implementation, Phase 9 coverage mapping, and Phase 10 portal design/read-contract preparation may share a work programme. Their acceptance gates stay ordered: Phase 8 end condition → Phase 9 core acceptance → Phase 10 Investor Portal release. Phase 10 work must consume Phase 8 authoritative positions; it cannot create a substitute finance calculation to bypass an open Phase 8 decision.

## Completion gate

Phase 9 is complete only when the required Main System core workflows are usable against real backend data in the verified environment; critical cross-module, financial, permission, migration and UI regressions pass; no unresolved A-level or acceptance-blocking B-level finding remains; and evidence states the deployment boundary honestly. A locally verified candidate is not production readiness.

## References

- `planning/V2-DEVELOPMENT-ROADMAP.md`, Phases 8–10.
- `docs-final-v2/01-business-rules.md`, `02-user-roles-permissions.md`, `03-system-modules.md`, `04-data-model-relationships.md`, `05-vehicle-investor-finance-workflow.md`, `07-ui-navigation-structure.md`, `09-company-accounting-owner-distribution.md`.
- `architecture/01-DATA-FLOW.md` through `04-CHANGE-IMPACT-COMPATIBILITY.md`; Phase 4–8 architecture and local verification records.
