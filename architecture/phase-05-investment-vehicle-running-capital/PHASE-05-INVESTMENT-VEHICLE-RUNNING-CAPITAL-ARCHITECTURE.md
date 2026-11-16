# Phase 5 — Investment, Vehicle and Running Capital Code Architecture

**Current architecture state:** `READY_FOR_IMPLEMENTATION` (target architecture locked).<br>
**Implementation state (verified 2026-11-16):** `PHASE_5_IMPLEMENTED_AND_VERIFIED_LOCALLY`; see the latest checkpoint below. The partial/blocked entries below are dated historical snapshots.<br>
**Deferred dependencies:** Vehicle deactivation/registration reuse awaits authoritative Garage and open-finance/settlement state. Demo-data import and additional automation are not Phase 5 blockers. Preserve the existing core module-gate decisions; no offline financial writes are included.

> The original 2026-11-07 architecture baseline is retained below as history. Later approved decisions and the latest implementation checkpoint supersede its older scope, route, schema, blocker, and implementation statements. Use the current scope summary and latest checkpoint below for the audit candidate; use the API-flow map and source code for implemented endpoint details.

## 1. Evidence and authority

- **VERIFIED_FROM_REPOSITORY:** Phase 4 checkpoint is commit `50fb67c1c2256f6a164344344c8c2a12e04407f8` in the isolated Phase 5 worktree. Current branch is `codex/phase5-investment-foundation`.
- **VERIFIED_FROM_BACKEND:** `apps/accounting` owns `AccountingEvent`, `AccountMovement`, `AccountingApplication`, immutable event history, and request idempotency. Event kinds currently cover Income, Expense, Receipt, Payment, Opening Balance and Transfer only. `source_reference` is free text and is not an entity relationship.
- **VERIFIED_FROM_BACKEND:** `apps/tenants` owns Company/Tenant, Branch and immutable company module-state revisions. Accounting mutation serializes on the Tenant row, checks the enabled revision inside the transaction, and applies server-side Company/Branch grants.
- **VERIFIED_FROM_DATA_FLOW:** React uses TanStack Query for the Phase 1 context and Phase 4 Accounting; Vehicle, Investor and Fund records still come from mutable `mockData.ts` / App state.
- **DOCUMENTATION_CLAIM:** `docs-final-v2/03-system-modules.md` assigns Investor/Fund to Investment, the single Company-wide Vehicle identity/current Branch/movement to Vehicle Management, and Cash/Bank/Company Running Capital to Accounting. Garage, Sales and Investor profit/settlement are later modules/phases.
- **HISTORICAL BASELINE (2026-11-07):** Q39 permits purchase before full payment; zero advance is valid. The original baseline did not yet define seller payable/installments. Later approved decisions and implementation add those Vehicle-owned records; Accounting continues to own actual Cash/Bank movements.

Repository evidence outranks older Phase 5 drafts in other worktrees. This architecture does not copy their stale “no Accounting app” or unresolved-permission claims.

## Implementation and local verification checkpoint — 2026-11-15

The approved Phase 5 core scope described in this architecture is implemented in the current worktree and locally verified. The full execution report at [`docs/phase5-execution-progress.md`](../../docs/phase5-execution-progress.md) contains exact commands and evidence boundaries.

- Django `apps` suite: 330/330 passed on disposable PostgreSQL, followed by 2 targeted Purchase concurrency/module-OFF race tests; current schema migrations applied fresh and `investment.0007_fund_credit_attribution_correction` reversed/reapplied on an empty disposable database.
- React suite: 132/132 across 22 files; configured lint and production build passed. The production build emits a 614.10 kB main-chunk advisory.
- Browser reload confirmed an API-created Fund Credit and wrong-Investor attribution correction persisted with the corrected owner and correction-history entry.
- Q133–Q134 behavior is manual-review-only when linked Fund use or principal-return history exists. Preserve old use/return rows and cash events; do not auto-restatement/posting of historical Profit or settlement.
- Vehicle deactivation/registration reuse stays blocked until authoritative Garage Job and Investor settlement providers exist. This is deferred scope, not a Phase 5 core blocker.
- Worktree: `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`, HEAD `50fb67c1c2256f6a164344344c8c2a12e04407f8`. Changes remain uncommitted/unpushed. Staging, production, deployment, hosted database roles, and hosted backups are `UNVERIFIED`.

## 2. Scope and protected contracts

The implemented Phase 5 scope owns Investor profiles and approved settings; Fund credits, available principal, uses, and returns; Company-wide Vehicle identity and Branch movement; Vehicle purchases with seller payable, installments, refunds, and corrections; direct Stock Vehicle expenses with payable, installments, refunds, and corrections; confirmed Vehicle Sales with Buyer receipts, refunds, and sale-price corrections; exact Company Running Capital allocations; and the typed links to Phase 4 Accounting for actual Cash/Bank events. The React operational workspace uses these backend records for the integrated Phase 5 flows.

Phase 5 does not calculate or pay Investor Profit, execute loss offsets, close Investor periods, settle full Exit, implement Garage Jobs, Owner distribution, payroll, inventory, CRM, or ERP. Vehicle deactivation/registration reuse remains unavailable until authoritative Garage and Investor-settlement status can be checked. Offline financial writes/sync and automatic migration of demo/mock records are also excluded. Existing UI composition, visual hierarchy, and route identities remain preserved; backend/database records are runtime truth for implemented Phase 5 flows. No Phase 5 migration is applied to the persistent 8002 database or a hosted environment.

## 3. Django app ownership and schema boundaries

### `apps/vehicles` — sole Vehicle aggregate owner

- `Vehicle`: UUID identity; Company FK; current Branch FK; normalized registration; model/description; active flag; created/updated actor and timestamps. Registration is unique among active Vehicles within one Company. Branch is a current-location projection; it never changes Vehicle UUID or historical records.
- `VehicleBranchMovement`: immutable Company/Vehicle/from-Branch/to-Branch/actor/time/reason/module-revision history. A move and current-Branch update commit together.
- `VehiclePurchase`: immutable purchase fact and one initial purchase per applicable stock Vehicle; Company, Vehicle, Branch, cost, effective instant, actor, Vehicle Management revision, and creation time. It stores cost once. Seller payment/source linkage is blocked by Q39.
- No Investor, Fund balance, customer/Job contact, Sale status, or Accounting cash balance is stored on `Vehicle`.

### `apps/investment` — sole Investor and Fund owner

- `Investor`: Company-scoped UUID and editable profile fields. No Branch FK: identity is Company-wide. Financial events are separate immutable records.
- `InvestorInterimConfiguration`: append-only per-Investor fixed INR amount and effective date, actor, version and Investment module revision. A same-Company Company-level Accountant alone may add a version; mid-month changes take effect next month. This is configuration, not a payment.
- `InvestorFundCredit`: immutable credit lot with Company, Investor, required source Branch, positive INR amount, actual receipt instant, actor and Investment revision. Balance is derived, never stored as a mutable total.
- `InvestorFundUseAllocation`: immutable lot-to-`VehiclePurchase` allocation. One purchase may draw only from one Investor’s Fund, plus Company Running Capital; allocations consume that Investor’s eligible credits FIFO by effective instant then UUID. Purchase source sums must reconcile exactly; no credit-tranche Profit split is created.
- `InvestorPrincipalReturn`: immutable actual principal return linked to the specific credit lot(s), only from unallocated Available Fund. It is not an Income or Expense.
- `InvestorPrincipalReturnAllocation`: immutable amount allocation from one return to one same-Investor/source-Branch credit lot. A return command is limited to one source Branch so its single Accounting event keeps an unambiguous Branch; Company Accountant can issue separate returns for different Branches.
- Fund credit/return Accounting links are owned by the typed Accounting source-link table described below; Investment does not duplicate AccountMovement.
- Each app owns its immutable `(tenant, actor, Idempotency-Key)` request record. Do not reuse Accounting's idempotency table for non-Accounting commands.
- Mutable Investor/Vehicle profile changes append the existing immutable `AccountSecurityEvent` with bounded old/new metadata. Fund credits/returns, Interim versions, and Branch movements have their own immutable domain rows; no audit event is a substitute for a financial source record.

### `apps/accounting` — sole actual Cash/Bank and Company Running Capital owner

- Extend `AccountingEvent.EventType` with `CAPITAL_INFLOW` and `CAPITAL_OUTFLOW`; these have no Income/Expense category and are excluded from Company Profit.
- `AccountMovement` remains the only Cash/Bank balance source. A Fund Credit creates exactly one positive movement. A real principal return creates exactly one negative movement. A full Vehicle purchase creates exactly one negative movement only if Q39 confirms the conditional full-payment contract.
- Add `AccountingSourceLink` with required `AccountingEvent` FK and typed nullable FKs to the supported source rows (Investor Fund Credit, Investor Principal Return, Vehicle Purchase). A database check requires exactly one source FK; uniqueness makes each source and event link one-to-one. There is no free-form entity ID or generic polymorphic reference.
- Add `CompanyRunningCapitalMovement` for exact Vehicle-linked allocation/recovery history. Phase 5 creates purchase allocation rows only; later actual recovery requires the relevant Sale/cash integration. Allocation rows do not create extra AccountMovements.

### Relationship and tenant rules

Every record uses immutable UUID primary keys and `PROTECT` for financial/history dependencies. Each Company-owned record has one Tenant FK. Every Branch FK must resolve to that same Tenant; cross-table same-Company invariants are enforced in services and PostgreSQL constraint triggers where ordinary FK/check constraints cannot express them. Fund is pooled at Company level; Branch is source provenance and authorization context, not a separate Branch Fund. Vehicle moves do not rewrite the Branch on old credits, purchases, jobs or Accounting events.

## 4. API/resource contracts

All routes are under `/api/v1/tenants/{company_id}/`; Company is resolved from the path, never trusted from a request body. Reads are paginated, private/no-store, same-Company, and filtered by server-side role/Branch scope. UUIDs are the only record identity. Mutations require `Idempotency-Key`; create/update responses return canonical serialized records and generated UUIDs.

| Method | Resource | Contract and permission |
|---|---|---|
| GET/POST | `investment/investors/` | List/create Company-wide profiles; Branch or Company Accountant may create. Branch Accountant profile edits are permitted by the approved decision. Owner/read-only roles cannot mutate. Investor module ON. |
| GET/PATCH | `investment/investors/{investor_id}/` | Same-Company UUID. Profile fields only; immutable Fund/vehicle history is never patched. |
| GET/POST | `investment/investors/{investor_id}/interim-configurations/` | Read current/history; only same-Company Company-level Accountant writes a version. Investment ON. |
| GET | `investment/fund/credits/` | Company Accountant sees all source Branch credits; Branch Accountant sees only assigned Branch credits. No consolidated Fund total or cross-Branch balance is returned to Branch Accountant. |
| POST | `investment/fund/credits/` | `{branch_id, amount, received_at, account_id, reference}`. Branch is mandatory. Branch Accountant may use an assigned Branch; Company Accountant may use any same-Company Branch. Requires Investment + Accounting ON. Atomically creates the credit, one typed source link, one CAPITAL_INFLOW event and one positive AccountMovement. |
| GET/POST | `investment/fund/principal-returns/` | Return only currently available/unallocated credit-lot value. Branch Accountant limited to their source Branch; Company Accountant may select any same-Company source Branch. Requires Investment + Accounting ON and actual cash-outflow account. No over-return or negative Fund. |
| GET/POST | `vehicle-management/vehicles/` | List by current Branch scope/create with registration, model and Branch. Branch Accountant own assigned Branch; Company Accountant any same-Company Branch. Vehicle Management ON. No Investor responsibility, customer contact, purchase cost or mutable status hidden in profile fields. |
| GET/PATCH | `vehicle-management/vehicles/{vehicle_id}/` | Same-Company UUID and current Branch authorization. Only approved descriptive attributes are mutable; identity is immutable. |
| POST | `vehicle-management/vehicles/{vehicle_id}/branch-movements/` | Company-level Accountant only. `{to_branch_id, reason}`; same Company; appends movement and updates current Branch atomically. Vehicle Management ON. |
| POST | `vehicle-management/purchases/` | **BLOCKED BY Q39.** If full payment is approved: `{vehicle_id, branch_id, purchase_cost, investor_id?, investor_fund_amount, company_running_capital_amount, account_id, paid_at, reference}`; Company-level Accountant only; all modules Investment + Vehicle Management + Accounting ON; exact source total equals purchase cost and actual payment is full/atomic. If partial payment is selected, do not use this contract; first approve a payable/payment-application model. |

Errors use DRF validation/permission/not-found responses and a structured conflict for stale module state, duplicate-key mismatch, or exhausted current position. Do not echo secrets or expose other Branch IDs/amounts in error messages.

## 5. Permission and module-state matrix

| Action | Branch Accountant | Company-level Accountant | Required modules |
|---|---|---|---|
| Investor profile create/edit | Same Company | Same Company | Investment |
| Interim amount configuration | Deny | Any Investor in same Company | Investment |
| Fund credit / principal return | Assigned/source Branch only | Any same-Company Branch | Investment + Accounting |
| View Fund credits | Own Branch only; no pooled total | Whole Company | Investment |
| Use pooled Fund for Vehicle purchase | Deny | Same Company only | Investment + Vehicle Management + Accounting |
| Vehicle create/edit in current Branch | Assigned Branch only | Any same-Company Branch | Vehicle Management |
| Vehicle move between Branches | Deny | Same-Company Branches only | Vehicle Management |
| Vehicle deactivation/registration reuse | Deny until dependent authoritative proof exists | Same Company, only after required proof | Vehicle Management plus future Garage/Sales/finance evidence |

Selected Branch is never authorization. Re-resolve active Company membership, role grant, and BranchAssignment from the server for every action. Company Accountant cross-Branch permission here is Investment/Vehicle-specific and does not alter any other module. Owners remain read-only.

Module-state transitions serialize through the Company/Tenant row. A consequential request observes and rechecks immutable revisions while holding the same lock used by module-state writes. If OFF wins, reject the new action; if an in-flight action wins the lock and commits fully, it is recorded before OFF. After OFF, no new root credit, return, move, or purchase is accepted. Existing pre-OFF obligations remain history; any later exception must be explicitly approved per module and is outside this Phase 5 slice.

## 6. Transactions, concurrency, idempotency and data integrity

- One outer `transaction.atomic()` owns every domain + Accounting write. The server validates all Company/Branch/module/role/object relations before writing; any failure rolls back domain row, source link, event, movement, use allocations, and idempotency response together.
- Deterministic lock order: authenticated actor row (using existing account lock helper), Company/Tenant row, module-state revisions ordered by module code, Investor, Vehicle/Purchase, FundCredit lots ordered by `(effective_at, id)`, then AccountingAccount. Recheck current module revisions after the Tenant lock. Use PostgreSQL `SELECT … FOR UPDATE` for pooled fund availability and current account validation.
- A unique `(tenant, actor, key)` idempotency record stores HTTP method/path, canonical request hash, status and response. Same-key/same-request returns the original response; key reuse for different intent is `409`; no duplicate credit, return, purchase, movement or cash event.
- Check constraints: positive two-decimal INR source amounts; valid event/source type pairing; exactly one typed source link; source/event unique; active Company registration uniqueness; no same-Branch no-op movement; one initial purchase per stock Vehicle; immutable event/allocation/movement records.
- Cross-table constraints/triggers: source links, credit Investor, purchase, vehicle, branch, event, movement and module revision all belong to the same Tenant; Fund allocations do not exceed that Investor’s available lots; same purchase total funding equals purchase cost; each purchase has at most one Company Running Capital allocation summary; Accounting capital events cannot carry Income/Expense category.
- Corrections append reversals/replacements only under a separately designed typed command. No delete/update of confirmed financial history; Phase 5 does not invent a correction or refund policy beyond existing Accounting rules.

## 7. Migration sequence and compatibility

1. `vehicles.0001`: Vehicle identity, normalized registration, active-only unique constraint, movement history and Vehicle request idempotency. No Accounting or Investment FK, preventing dependency cycles.
2. `investment.0001`: Investor profile, versioned Interim configuration, Fund credits, principal returns/credit-lot applications and Investment request idempotency; depends on tenants/accounts only.
3. `accounting.0004`: add CAPITAL_INFLOW/OUTFLOW and typed links for Fund credits/returns, with PostgreSQL integrity triggers. It depends on `investment.0001` and `accounting.0003`; no VehiclePurchase link or Running Capital purchase allocation is added yet.
4. **After Q39 only:** `vehicles.0002` adds VehiclePurchase using the approved full-payment or payable contract. No application-visible purchase write before decision.
5. **After Q39 only:** `investment.0002` adds Fund-use allocations to VehiclePurchase; `accounting.0005` adds the typed VehiclePurchase link and Vehicle-linked Running Capital movement. Keep migration dependencies acyclic and run `showmigrations`, fresh apply, upgrade, and history-protected reverse checks on disposable PostgreSQL.
6. Data import: do not map `v-*`/`inv-*` mock strings to UUIDs or auto-import existing mock records. The sample mock includes duplicate registration numbers and conflicting amounts. A separately reviewed, explicitly selected demo seed/import manifest must map Company/Branch and resolve duplicates. No implicit seed on startup.
7. React: add typed API services and query keys; migrate one view/form at a time. Keep mock fixtures for tests and read-only demo fallback only if clearly separated from runtime business truth. Do not maintain a parallel mutable mock store after parity. Mutate the query cache only from server responses; reload reads backend.

Rollback is application-code rollback while retaining schema/history. Do not reverse non-empty financial migrations; existing Phase 4 pattern refuses unsafe history reversal. Stop traffic/writers before any approved rollback affecting in-flight requests. Never drop tables or erase source links to restore a mock UI.

## 8. Implementation slices and acceptance gates

1. **Schema/API contract:** implement Vehicle and Investor profile, scoped permissions, audit history, migration/system tests. No purchase/capital event.
2. **Fund credit and return:** typed capital event source links, immutable lot ledger, Branch scoping, idempotency, cash-account movement; prove exact one cash movement and no Company Income/Expense.
3. **Vehicle lifecycle:** CRUD and Company Accountant-only Branch transfer; uniqueness and historical movement; defer deactivation until authoritative Sold/Job/open-finance providers exist.
4. **Vehicle Purchase / allocations:** start only after Q39; exact source reconciliation, FIFO Fund usage, Running Capital, source cash event, locked positions. Atomic rollback/concurrency tests required.
5. **React integration:** current views/forms/lists use shared API services and TanStack Query; preserve routes and visual UI. No false success; persistence across reload.
6. **Regression closeout:** current Company context, Phase 1–4 APIs, migrations, non-financial routes and UI preserved; full test/build/E2E audit.

Every slice is independently testable, lists exact file scope in its implementation log, and may roll back its application layer without deleting recorded history. No phase is considered complete from schema presence alone.

## 9. Required test architecture

- Model/DB: UUIDs, same-Company Branch relations, active-only unique registration, immutable history, typed source-link exactness, protected deletion, migration trigger behavior.
- Service: amount precision, FIFO credit consumption, Available Fund only, purchase source totals, module OFF serialization, idempotent retry and key mismatch, atomic rollback injection, one cash effect.
- API: same-Company reads/writes; cross-Company IDOR denied; unassigned/wrong Branch denied; Branch Accountant sees only own Fund records and no total; Company Accountant cross-Branch only in approved actions; Owners denied mutations; module-off/new mutation fail-closed.
- Concurrency (PostgreSQL `TransactionTestCase`): two concurrent Fund uses/returns cannot exceed available position; concurrent duplicate idempotency key yields one source event; module OFF and credit race serializes; unique registration race yields one active Vehicle.
- React: request contract/validation, error remains visible and never shows success, server-generated UUID mapping, query invalidation from returned data, cache not mutating independently, reload persistence, exact route/UI snapshot or DOM contract unchanged.
- Verification: targeted Django tests, full Phase 1–4 regression, migration check/fresh apply/upgrade/reverse-with-history protection, React tests/lint/build, disposable local PostgreSQL browser workflow. Staging/production remain `UNVERIFIED` absent authorized access.

## 10. Blockers, decisions and readiness

- **BUSINESS DECISION REQUIRED — Q39:** full seller payment before saving Purchase, with one Accounting outflow, versus record acquisition first and support later/partial payments. Supplier payable/payment applications are not currently supported. The latter requires a different schema, API and workflow, so no Purchase slice can begin until answered.
- **DEPENDENCY BLOCKER:** Vehicle deactivation/registration reuse cannot safely confirm `Sold` and absence of open Garage jobs, finance, settlement or refunds until those authoritative modules exist. Keep deactivation disabled in Phase 5; preserve the rule for the later integrated slice.
- **DATA IMPORT BLOCKER:** legacy mock IDs and duplicate registration rows cannot be auto-migrated. Require a reviewed Company/Branch/record manifest if historical mock data is to be imported.
- **UI_CHANGE_REQUIRED:** the existing Vehicle form collects classification, a mock Garage identity, an Investor or customer-person, and purchase price. Approved V2 rules make Vehicle identity/current Branch a Vehicle Management action, Investor responsibility a separate Investment action, customer-person a Garage Job contact, and purchase a Q39-gated action. It also lacks a backend Branch UUID, actual cash account and required reference for a Fund credit. Do not submit or silently discard these fields. Preserve current composition/routes; hold semantic form integration until sequential actions and required backend identities/inputs can be represented without changing the approved UI contract.
- Protected agreement rate mutation, Profit/Loss calculation and full Exit settlement stay outside Phase 5. Do not add speculative APIs.

Therefore this document locks the independent contracts but does not classify the entire Phase 5 architecture as ready: `PHASE_5_CODE_ARCHITECTURE_BLOCKED` until Q39 is explicitly answered and data-import/deactivation dependencies are bounded. No implementation starts for those blocked actions.

## Local implementation checkpoint — 2026-11-07

**Implementation state:** `PHASE_5_IMPLEMENTATION_PARTIAL_BLOCKED`. The code-architecture readiness classification above remains `PHASE_5_CODE_ARCHITECTURE_BLOCKED`; this checkpoint does not change that gate or any business rule.

Implemented on local branch `codex/phase5-investment-foundation` from Phase 4 checkpoint `50fb67c1c2256f6a164344344c8c2a12e04407f8`:

- `apps/investment`: Company-scoped Investor profiles, append-only Interim configuration, Branch-attributed immutable Fund credits/principal returns and FIFO actual-principal-return allocation, scoped read/summary resources, audit/idempotency, and module gates.
- `apps/vehicles`: Company-wide UUID Vehicle identity, active-only normalized registration uniqueness, Company Accountant Branch movement with immutable movement history, and module gates. No deactivation endpoint is exposed.
- `apps/accounting`: typed `AccountingSourceLink` from actual capital inflow/outflow to Fund credit/principal return; existing Accounting owns the corresponding Cash/Bank event and one AccountMovement. These events are not Income/Expense/Profit.
- `apps/common`: shared Company/Branch authorization and atomic mutation boundary that locks/rechecks Company module-state revisions.

Historical implementation snapshot as of 2026-11-07: Purchase/funding, Garage-dependent deactivation, and React integration were still blocked or outside that snapshot; no Phase 5 React files had been changed at that time. The latest 2026-11-15 checkpoint above supersedes those implementation claims. Current deferred scope is Vehicle deactivation until authoritative Garage/settlement state, automatic mock import, Investor Profit/Loss/Exit settlement, offline financial writes, and hosted deployment verification. Current code remains uncommitted/unpushed.

## Current V2 business decision checkpoint — 2026-11-08

The approved additions in `docs-final-v2/05-vehicle-investor-finance-workflow.md` supersede this document's earlier Q39 decision gate and conditional full-payment purchase contract. A Vehicle purchase may be recorded with ₹0 paid; the complete cost remains purchase cost, and its unpaid balance is seller payable. Require seller name and allow optional seller phone. The purchase view must warn when no seller advance has been paid. One or more actual installments reduce that payable, never beyond the outstanding amount; each actual installment has one Accounting cash effect. Purchase/funding allocation does not itself create a cash movement.

An already-created seller payable may receive authorized installments when Investment or Vehicle Management is OFF, provided Accounting is ON and the purchase/payable predates OFF. No new purchase or Fund-use allocation is permitted by this exception. Accounting OFF receives no new seller-payment exception. All writes retain Company/Branch permission, module revision, idempotency and audit checks.

Each actual seller installment follows the purchase's original Branch: Branch Accountant may pay only within their authorized Branch; Company-level Accountant may pay for any Branch in the same Company. Purchase creation and pooled Fund-use remain Company-level Accountant actions.

**Architecture work remaining before purchase implementation:** replace the earlier full-payment-only `POST purchases/` input; define a separate purchase-linked installment resource and typed payment/application identity; keep one event-to-source link per actual installment while allowing many installments per purchase; define payable derivation, correction/reversal, row-lock and overpayment behavior; revise the migration DAG after existing `accounting.0005`; and define response/cache/warning fields including required seller name, optional phone, and original-Branch actor scope. The earlier direct one-to-one `VehiclePurchase` source-link proposal cannot represent multiple installments. This checkpoint records approved meaning; the purchase code contract remains `PHASE_5_CODE_ARCHITECTURE_BLOCKED` until those technical details are reconciled and verified.

## Current V2 Business Decision Additions Referenced — lender finance and EMI excluded

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions).
- Technical impact: Phase 5 purchase supports only the approved seller payable and actual seller installments. Do not add lender debt, EMI schedule/payment, interest/fee, or finance-tag resources; keep the seller payable separate from any future lender-liability domain.

## Current V2 Business Decision Additions Referenced — purchase funding allocation timing

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions).
- Technical impact: commit full Investor Fund and Company Running Capital allocations atomically when the purchase is created, even for zero seller advance. Compute the seller payable separately; create no AccountMovement until an actual installment.

## Current V2 Business Decision Additions Referenced — purchase cost correction

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions).
- Technical impact: a correction below cumulative seller installments requires an actual seller refund recorded in Accounting. Original payment/movement rows remain immutable; the typed refund link, correction/reallocation rows, and transactional validation still need to be designed before implementation.

## Current V2 Business Decision Additions Referenced — proportional source correction

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions).
- Technical impact: reduce Investor Fund and Company Running Capital according to the recorded split, preserving FIFO Fund-lot attribution and immutable history. Paise rounding remains unresolved.

## Current V2 Business Decision Additions Referenced — purchase-source paise rounding

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions).
- Technical impact: use `ROUND_HALF_UP`, balanced-paise residual distribution, and stable Fund-first tie-breaking for source reallocation.

## Current V2 Business Decision Additions Referenced — Company-wide automation approval

- Canonical decision: [01 — Business Rules](../../../docs-final-v2/01-business-rules.md#approved-business-decision-additions).
- Technical impact: use one versioned Company setting for all modules. Consequential automation is pending while ON; OFF permits only already-approved automation. Place Approve and business-readable calculation Details in the relevant workflow. Phase 5 still needs toggle authorization, pending-item transition, paise-rounding, and typed purchase/refund contracts.

## Current V2 Business Decision Additions Referenced — automation setting authority

- Canonical decision: [02 — User Roles and Permissions](../../../docs-final-v2/02-user-roles-permissions.md#approved-business-decision-additions).
- Technical impact: only a same-Company Company-level Accountant changes the versioned policy; enforce the grant at the API/service boundary.

## Current V2 Business Decision Additions Referenced — pending action behavior

- Canonical decision: [01 — Business Rules](../../../docs-final-v2/01-business-rules.md#approved-business-decision-additions).
- Technical impact: an OFF transition affects only future automation. Existing pending Phase 5 actions retain their state and require separate authorized approval/cancellation.

## Current V2 Business Decision Additions Referenced — auto-posting in approval OFF mode

- Canonical decision: [01 — Business Rules](../../../docs-final-v2/01-business-rules.md#approved-business-decision-additions).
- Technical impact: only separately approved Phase 5 automations may skip per-action confirmation while OFF; preserve real-source, role, Company/Branch, module-state, and transaction checks.

## Current V2 Business Decision Additions Referenced — manual Purchase refund and correction

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions), also recorded in the canonical data-relationship and Accounting documents.
- Technical impact: an authorized Accountant separately initiates an actual seller refund record and its related Purchase cost correction; both explicitly reference the same Purchase. The refund must reflect cash actually returned and be recorded through Accounting. Do not auto-create either record, infer a refund from a cost correction, or mutate original payment/movement history. Derive outstanding payable from corrected cost, valid installments, and linked actual refunds; do not store a mutable payable total. Typed source models, validation order, transaction boundary, idempotency, and exact payable/refund validation remain technical blockers.

## Current V2 Business Decision Additions Referenced — seller-payment account selection

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../docs-final-v2/05-vehicle-investor-finance-workflow.md).
- Technical impact: the initial seller payment requires an account choice; the next payment offers the last selected account and allows a change. Preference scope, storage and the point at which a selection is remembered remain open. Validate the account and authorization on the server; do not mutate confirmed payment history.

## Current V2 Business Decision Additions Referenced — per-Accountant payment preference

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../docs-final-v2/05-vehicle-investor-finance-workflow.md#addition--seller-payment-account-preference-is-per-accountant).
- Technical impact: the last selected seller-payment account is scoped to the Accountant and Company. Storage and the exact selection lifecycle remain to be designed; validate current account access and status before posting. This supersedes only the earlier reference's statement that per-Accountant versus Company-wide scope was open.

## Current V2 Business Decision Additions Referenced — successful-payment preference

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../docs-final-v2/05-vehicle-investor-finance-workflow.md#addition--remember-account-after-a-successful-seller-payment).
- Technical impact: only a successfully saved seller payment updates the per-Accountant, per-Company remembered account; unsaved or failed forms do not. Preference storage and retry/recovery mechanics remain to be designed. This supersedes only the earlier reference's unresolved selection lifecycle.

## Current V2 Business Decision Additions Referenced — demo import

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../docs-final-v2/05-vehicle-investor-finance-workflow.md#addition--no-automatic-import-of-demo-investor-and-vehicle-data).
- Technical impact: integrate actual backend Investor/Vehicle records without automatic mock import or deletion of existing records. Any historical import is a separately reviewed activity.

## Phase 5 scope decision — Vehicle deactivation dependency checks

The user has requested that all related backend checks required for safe Sold Vehicle deactivation be included in Phase 5, rather than deferring the feature. This supersedes the earlier Phase 5 deferral as a scope decision only; it does not make deactivation safe or implemented.

- Preserve the approved rule: a Vehicle must be Sold and must have no open Garage Job, unresolved Sale/finance, refund or settlement before authorized manual deactivation; retain its identity and history. Never infer that a missing module, table, endpoint, record or unimplemented source means there is no open obligation. Unknown or unverifiable dependency state blocks deactivation.
- Repository review found Vehicle, Investor and Accounting models, but no authoritative Garage Job, Sale or settlement applications in this checkout. Phase 5 scope expansion therefore requires a repository-grounded dependency and ownership map, the smallest authoritative supporting records/contracts necessary to prove each condition, and an explicit integration boundary for later Garage/Sales/settlement phases. It must not invent business meanings, duplicate source-of-truth records, or treat mock data as evidence.
- Lock a concurrency-safe check-and-deactivate protocol, stable lock order with all relevant obligation writers, Company/Branch and role/module authorization, idempotency, audit/history, registration uniqueness and migration/compatibility. Until those contracts and authoritative dependencies exist and are verified, deactivation remains unavailable; do not bypass existing model/DB guards.
- This is a scope expansion and an unresolved architecture dependency, not implementation approval, evidence of complete Garage/Sales workflows, or permission to change unrelated Phase 1–4 behavior. Review business decisions required by the additional dependencies before implementation.

## Phase 5 scope clarification — authoritative Sale required for Sold

The user confirmed that a Vehicle is considered Sold only after an actual Sale backend record is completed/confirmed. The canonical V2 workflow already states that Sale confirmation marks Sold while buyer collection remains separately Pending, Partially Received or Fully Received; this clarification does not require full payment to mark Sold. Existing deactivation requirements still block deactivation while a financial or settlement position remains open.

- Canonical source: [05 — Vehicle/Investor Finance Workflow](../../docs-final-v2/05-vehicle-investor-finance-workflow.md) (Stock Vehicle Sale and approved deactivation additions).
- Phase 5 must design an authoritative Sale source and explicit check contract without duplicating the later Sales module's ownership or inventing a parallel manual Sold flag. Current checkout has no Sales application; the exact minimal Sale scope, collection/refund dependencies, migration order, access/module rules and concurrency contract remain to be designed and reconciled before the Phase 5 architecture can be locked.

## Phase 5 scope decision — minimal authoritative Sale dependency

The user selected the smallest real Sale capability and authoritative obligation checks necessary to make Vehicle deactivation safe in Phase 5. Document clearly which Sales capabilities this slice implements and which Sales, Collection, Refund and related workflows remain for later phases. Keep the API surface simple and extensible for subsequent Sales delivery; an exact route, number of endpoints and schemas are not yet approved or locked.

- A confirmed real Sale remains the authoritative Sold source; do not introduce a parallel manual flag, demo record or incomplete placeholder that presents a Vehicle as sold. Preserve canonical Buyer, sale-price, tenant/Branch, authorization, history and source-ownership requirements.
- Minimum scope must be derived from the approved V2 Sale and deactivation rules: it must supply a trustworthy Sold state and prove the absence of all required open Garage, Sale, finance, refund and settlement positions. A dependency without an authoritative source remains UNKNOWN and blocks deactivation. This selection does not authorize pretending that unimplemented collections, refunds or settlement have no outstanding records.
- Document a concrete capability inventory, ownership, single source of truth, API/service extension path, migration order, transaction/lock protocol with concurrent obligation writers, and future Garage/Sales/Accounting/settlement integration before declaring architecture ready. Avoid duplicate entities or a temporary endpoint that later changes identity or bypasses the approved Sale workflow.
- The Phase 5 implementation and code-architecture gates remain blocked pending this design and repository-grounded verification. This records approved scope direction only; no new backend, API, schema, UI or migration has been implemented by this entry.

## Phase 5 UI approval — Buyer phone in existing Sale form

The user explicitly approved adding a small Buyer phone field to the existing Sale form to satisfy the already documented V2 requirement. This is a narrow approval for that visible UI change, not a redesign or an implementation-ready API contract. The submitted value must be mapped to the authoritative Sale/Buyer record and checked by the backend. Preserve current routes and form hierarchy; other missing fields or visible changes require their own scope review. See `PHASE-05-BLOCKER-RESOLUTION-DRAFT.md` for the remaining mapping and technical gates.

## Current V2 Business Decision Additions Referenced — Fund Credit form inputs

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#addition--fund-credit-form-captures-the-actual-account-and-source-reference).
- Technical impact: the existing Fund Credit API already requires `account_id` and `reference`; expose both in the current React form and pass them through unchanged. This is a narrowly approved form-field addition, not a UI redesign or an Accounting contract change.

## Current V2 Business Decision Additions Referenced — actual Sale date

- Canonical decision: [05 — Vehicle/Investor Finance Workflow](../../../docs-final-v2/05-vehicle-investor-finance-workflow.md#addition--sale-records-the-actual-sale-date).
- Technical impact: include the operator-entered actual Sale date in the authoritative Sale request and keep it distinct from server `recorded_at`. This narrow form addition supports correct later period attribution; it does not add Buyer collection or Investor Profit behavior.

## Phase 5 scope decision — online-only writes; offline sync is separate

The user approved keeping Phase 5 business writes online through the current cloud/backend API. Local financial writes, durable offline queues and synchronization are outside Phase 5 and require a separate system-wide design and approval. This decision does not change existing online permissions or assert that all users are always read-only while offline; it only excludes new offline-write/sync behavior from Phase 5.

## Phase 5 approved minimum Stock Sale and Buyer Receipt scope

The user selected the recommended minimum Buyer Receipt slice so the backend can determine whether a confirmed Sale still has an open receivable. This is a Phase 5 scope decision; detailed resource, serializer, accounting-link and transaction contracts remain technical architecture work.

- **Implement in Phase 5:** one authoritative confirmed Sale per eligible Stock Vehicle with Buyer name, required Buyer phone, agreed price and operator-entered actual Sale date; actual Buyer Receipts linked to that Sale and to exactly one Accounting-owned cash movement. Multiple partial Receipts follow the existing V2 limits; over-collection is rejected atomically. Never duplicate the cash event or accept demo data as a real Sale.
- **Deactivation prerequisite:** the linked Sale must be fully collected and every required Garage, finance, refund and settlement provider must return authoritative CLEAR. OPEN or UNKNOWN blocks deactivation. A missing provider cannot report CLEAR.
- **Defer:** full Sales management, Sale price correction, Buyer refund, CRM/customer directory, Investor Profit/Loss allocation and settlement remain outside this minimum slice and must be listed as later work. A Sale needing an unsupported correction/refund cannot pass the deactivation guard.
- This approval does not resolve the separate source-availability issue: this checkout still has no authoritative Garage Job or Investor settlement application. Until the minimum Phase 5 architecture includes trustworthy providers for those conditions (or explicitly denies deactivation while they are unavailable), deactivation remains blocked.

## Phase 5 scope decision — defer Investor-funded deactivation until settlement is clear

The user confirmed that an Investor-funded Vehicle remains active until its Investor settlement is completed. Phase 5 must check the authoritative settlement state and fail closed when it is open, unknown or unavailable. Investor Profit/settlement calculation and posting remain in Phase 8; Phase 5 must not create a partial or duplicate settlement workflow just to free a registration. Therefore deactivation for an Investor-funded Vehicle remains unavailable until Phase 8 provides the authoritative completed-settlement record.

## Repository-verified blocker — Accounting source links for Purchase and Sale

The current generic Accounting Receipt/Payment service settles only Accounting Income/Expense targets, and current `AccountingSourceLink` supports only Investor Fund Credit/Principal Return. V2 explicitly keeps Vehicle Purchase cost and Sale Buyer collection separate from Company Income/Expense. Phase 5 therefore needs typed same-Company Accounting source links for Purchase installments/refunds and Sale Buyer Receipts. Each real cash event must remain one immutable Accounting event plus one `AccountMovement`; domain totals derive from linked events, not a duplicated amount. A future Accounting migration must follow creation of source-domain rows to keep the migration graph acyclic. Exact source models, endpoint contracts, constraints, module-OFF behavior and cross-domain lock order remain technical architecture work; no generic Income/Expense target may be used as a workaround.

## Approved Phase 5 scope clarification — Garage Job checks deferred; deactivation stays blocked

On 2026-11-09, the user selected the minimal Phase 5 Sale/Buyer Receipt scope and explicitly chose not to add a Garage Job backend to Phase 5. Garage Job support remains in its planned later phase. This supersedes only the earlier Phase 5 scope request to implement every backend dependency needed to enable Vehicle deactivation; it preserves the already approved exception to the earlier broad Sales/Buyer-Receipt exclusion for this minimal slice, and it does not supersede the approved safety rule requiring proof that no open Garage Job exists.

- Phase 5 may implement the authoritative Sale and linked Buyer Receipt capability already approved, but it must not create a partial Garage Job model or report an absent Garage provider as CLEAR.
- Vehicle deactivation and registration reuse remain unavailable until the Garage phase provides a complete authoritative open-Job check. OPEN or UNKNOWN blocks. Preserve the existing Sold, finance, refund and Investor-settlement checks as independent prerequisites; Investor-funded Vehicle deactivation also remains blocked until Phase 8 provides authoritative completed settlement.
- Keep the current database/model guard against deactivation. Do not expose a deactivation endpoint or UI action that can bypass the missing Garage source.
- This is a scope and sequencing decision only. It does not make Sale/Receipt, Garage Job, or deactivation implemented, and it does not change the existing approved UI beyond separately approved fields.

## Phase 5 UI approval — named account for Buyer Receipt

On 2026-11-09, the user approved a compact Cash/Bank account selector in the existing Collection form for actual Buyer Receipts. Repository inspection confirms the current form records Sale, amount, date and a payment-method label but no named account UUID; the current Accounting Receipt serializer requires `account_id`.

- Populate the selector from same-Company active accounts the actor may use, submit the selected account UUID, and revalidate Company, account status, Branch authority, and module state on the server. A display method such as “Cash” or “Bank transfer” is not an account identity.
- Keep the existing form, route and visual composition; this approval covers only the compact account selector. Do not show receipt success until the typed Sale Receipt and its single Accounting cash movement both commit.
- This does not authorize routing a Stock Vehicle Buyer Receipt through the generic Accounting receipt endpoint, which targets Accounting Income. The Sale Receipt needs its own typed link to the Accounting event and exactly one `AccountMovement`; it must not create Company Income or duplicate cash.
- The required Accounting `source_reference` still needs a technical mapping for Sale Receipts. V2 requires an operator-supplied external reference for Garage receipts, but that Garage-specific rule is not automatically extended to Stock Vehicle Buyer Receipts. No additional reference field was approved here.

## Approved Q62 — required external reference for Stock Vehicle Buyer Receipts

On 2026-11-09, the user approved a required operator-supplied external reference in the existing Collection form for every actual Stock Vehicle Buyer Receipt, such as a bank transaction ID or Cash voucher number. This supersedes only the preceding Q61 unresolved-reference statement; the Q61 Cash/Bank account selector approval remains in force.

- Store the input on the typed Buyer Receipt source and copy it to the linked Accounting event's required `source_reference`. Keep the server-generated receipt UUID and Sale FK as identity; never use reference text as the relationship key.
- Preserve one actual receipt, one Accounting event and one `AccountMovement`; do not target Company Income. Apply the current partial-collection and over-receipt rules.
- The Garage-specific operator-reference uniqueness rule does not automatically transfer to Stock Vehicle Buyer Receipts. Duplicate-reference rejection and its scope remain BUSINESS DECISION REQUIRED.
- This adds one required field to the already approved Collection form only; no general Sale form redesign is approved by this entry.

## Approved Q63 — Buyer Receipt reference uniqueness scope

On 2026-11-09, the user chose to reject duplicate Buyer Receipt external references within the same Company and the same named Cash/Bank account, across Branches. The same reference may be used with a different account. This supersedes only Q62's unresolved duplicate-reference scope; the required external-reference input remains approved.

- Enforce this on Stock Vehicle Buyer Receipt records only. Do not widen the constraint to all Accounting events, Garage receipts, or other domains.
- Keep the reference as traceability data; use the receipt UUID, typed Sale FK and idempotency key for their separate identity/retry purposes.
- Exact normalization for matching (case and whitespace) remains to be locked before final DB constraint/API design.

## Approved Q64 — Buyer Receipt reference matching normalization

On 2026-11-09, the user chose to ignore reference letter case and leading/trailing whitespace for duplicate detection. Thus `BANK-37`, `bank-37`, and ` BANK-37 ` collide when submitted for the same Company and Cash/Bank account. This supersedes only Q63's unresolved normalization statement; Q63's Company/account scope remains unchanged.

- Apply a trimmed, case-insensitive comparison key only to typed Stock Vehicle Buyer Receipt references.
- Continue allowing the same normalized text on a different account. Keep the same-Company/account constraint across Branches.
- Preserve the external reference as traceability, not UUID identity or idempotency. Do not change normalization for other Accounting references or Garage receipts.

## Approved Q65 — Fund Credit external-reference uniqueness

On 2026-11-09, the user chose to reject duplicate Fund Credit references within the same Company and same Cash/Bank account, across Branches. Comparison trims leading/trailing whitespace and ignores case; the same reference may be used with another account.

- Apply this only to Investor Fund Credit source records. Preserve the Fund Credit UUID and typed Accounting link as identity/source relationship; reference text is traceability, not identity or an idempotency key.
- Repository evidence: `InvestorFundCredit` stores reference and Branch but has no account FK or uniqueness constraint. `AccountingSourceLink` links the Credit to an AccountingEvent, and the actual account is held on its `AccountMovement`. The schema must make the unique `(Company, actual account, normalized reference)` rule enforceable while preventing the account reference from diverging from the Accounting movement.
- Preserve one atomic Fund Credit + one Accounting capital inflow + one AccountMovement. This decision does not define whether one actual transfer may be split across multiple Investors' Fund Credits; that remains BUSINESS DECISION REQUIRED.

## Approved Q66 — one transfer funds one Investor Fund Credit — 2026-11-09

One actual Cash/Bank transfer may create a Fund Credit for one Investor only. Do not split one transfer among multiple Investors; record separate actual transfers for separate Investors. This supersedes only the Q65 unresolved transfer-allocation question.

- Preserve one Fund Credit, one typed Accounting capital inflow and one AccountMovement per actual transfer, in one transaction.
- Keep the existing same-Company/account normalized reference uniqueness and Branch provenance. Separate actual transfers may create separate credits for the same Investor.
- No shared transfer allocation or split-credit schema is required. Reference text remains traceability data, not entity identity or an idempotency key.
- Documentation only; application code and schema are unchanged.

## Approved Q67 — Fund Credit actual receipt date — 2026-11-09

Use the actual date money was received for the Fund Credit effective date. Late entry may be backdated to that actual date; future dating is prohibited.

- The Fund Credit, its Accounting capital-inflow event and AccountMovement use the same effective receipt date; creation/audit timestamp remains the real system entry time.
- Backdated entries change historical as-of ledger views and effective-date-based Investor periods. This matches the current `effective_at` flow and the service's existing future-date rejection; no application change is made here.
- The API's timezone and time-of-day representation for the approved business date remains a technical contract to specify.

## Approved Q68 — correct wrong-Investor Fund Credit attribution — 2026-11-09

If the actual transfer is valid but the Fund Credit was assigned to the wrong Investor, preserve the original credit and audit history and append a correction moving the Fund amount to the correct Investor. The same actual Cash/Bank movement remains recorded once; the correction creates no new receipt or movement.

- Keep the original Fund Credit and Accounting source link immutable. Model the attribution correction as a separate typed append-only record; do not reassign or duplicate the Accounting event.
- Preserve the one-transfer/one-Fund-Credit rule and original Branch provenance.
- Who may authorize a correction, whether partial corrections are allowed, and which effective date governs the correction remain BUSINESS DECISION REQUIRED.
- No code or schema was changed by this documentation update.

## Approved Q69 — Fund Credit correction role scope — 2026-11-10

A Branch Accountant may correct a wrong-Investor Fund Credit only when its original source Branch is within their authorized Branch scope. A same-Company Company-level Accountant may correct a Fund Credit from any Branch.

- This authority applies only to the append-only Investment attribution correction. It does not grant generic cross-Branch rights in other modules; Owner and Platform Back Office receive no new authority.
- Check authorization against the original Fund Credit's Company and source Branch, not a client-selected Branch or destination Investor.
- Partial-correction scope and correction effective-date treatment remain BUSINESS DECISION REQUIRED. No application code or schema changed.

## Approved Q70 — whole-credit wrong-Investor correction — 2026-11-10

Move the entire original Fund Credit to the correct Investor when correcting a wrong attribution. Do not partially split one credit across Investors. This supersedes only Q68/Q69's unresolved partial-correction statement and is consistent with Q66's one-transfer/one-Investor rule.

- Keep the original credit, audit history, Branch provenance and single Cash/Bank movement unchanged; the Company-wide Fund total does not change.
- Enforce the correction amount as equal to the full original Fund Credit amount. Preserve Q69's source-Branch/company-level authorization.
- The effective date assigned to the correction remains BUSINESS DECISION REQUIRED. No code or schema was changed.

## Approved Q71 — correction effective date — 2026-11-10

The wrong-Investor attribution correction is effective on the original Fund Credit's actual money-received date. Recalculate affected historical Investor calculations and preserve their earlier versions and audit history. The actual receipt/Cash/Bank movement remains unchanged.

- Keep the original Fund Credit effective date and creation timestamp; record a separate correction timestamp.
- Do not apply Company Profit rules to Investor Profit. How an already-paid or settled amount is adjusted remains a separate BUSINESS DECISION REQUIRED item.
- No code or schema was changed by this documentation update.

## Approved Q72 — prior Investor Profit payment after restatement — 2026-11-10

Preserve the old Investor calculation and actual payment, record the restatement difference as a separate audited adjustment, add underpaid Profit to a later Investor Profit amount, and deduct overpaid Profit from a later Investor Profit amount.

- Do not mutate or duplicate the original Cash/Bank movement. A later actual payout is a separate authorized payment.
- Keep the adjustment separate from Company Income/Expense and Company Profit.
- Handling an overpayment balance when no future Investor Profit is available or Exit occurs remains BUSINESS DECISION REQUIRED. No application code or schema changed.

## Approved Q73 — flexible Exit outcome for restatement overpayment — 2026-11-10

At Exit, the Company may either collect an unoffset historical Investor Profit overpayment before closing or allow Exit to complete without collection, according to the case.

- This applies only to overpayment adjustments from historical Profit restatement. It does not change ordinary Vehicle Loss or Fund principal Exit rules.
- Do not auto-debit Fund or create a payment event. Record an actual receipt only when money is received.
- The authorized decision-maker and whether a balance left unpaid is waived or remains recoverable after Exit remain BUSINESS DECISION REQUIRED. No code/schema changed.

## Approved Q74 — unpaid overpayment disposition after Exit — 2026-11-10

If Exit completes without collecting an unoffset historical Investor Profit overpayment, the Company may either keep the amount open for later collection or waive it with a recorded reason, selected case by case.

- Preserve the adjustment and Exit history. Neither disposition creates a Cash/Bank movement or Company Income/Expense.
- Record the selected disposition; a waiver requires a reason. Who may select or approve the disposition remains BUSINESS DECISION REQUIRED. No code/schema changed.

## Approved Q75 — post-Exit overpayment disposition authority — 2026-11-10

Branch Accountant may select open-balance or waiver only for an adjustment attributed to their authorized Branch. Same-Company Company-level Accountant may select for any Branch.

- This does not finalize a cross-Branch Exit; the existing Company-level-only cross-Branch Exit authority remains. It adds no cross-Branch permissions to other modules or new Owner/Platform Back Office rights.
- Validate the adjustment's source Branch and Company on the server. No code/schema changed.

## Approved Q76 — actual repayment permission after Exit — 2026-11-10

Branch Accountant may record actual repayment against an open post-Exit adjustment only for their authorized source Branch; same-Company Company-level Accountant may record it for any Branch.

- Record an actual cash movement only when money is received and link it to the open adjustment.
- This does not grant cross-Branch authority to finalize Exit or permission in other modules. Accounting event classification and typed source link remain to be locked.
- No application code/schema changed.

## Approved Q77 — Accounting classification of post-Exit repayment — 2026-11-10

Actual money received against an open post-Exit Investor Profit overpayment is recorded as a Cash/Bank Receipt linked to that adjustment. Reduce the open overpayment by the amount received; do not create Company Income or Company Profit.

- Preserve Q76's actor scope, the original Profit/payment and adjustment history, and the rule that no movement is recorded before actual receipt.
- Technical impact: a typed source link must connect the Accounting Receipt to the Investor adjustment. Exact model/API/transaction details remain architecture work; no application code/schema changed.

## Approved Q78 — partial and multiple post-Exit repayments — 2026-11-10

An open post-Exit Investor Profit overpayment may be repaid through partial and multiple actual repayments. Each actual Receipt reduces the open balance by the amount received; any remaining amount stays open.

- Preserve Q76 actor/Branch scope and Q77's Cash/Bank Receipt classification with no Company Income/Profit.
- Architecture impact: allow multiple typed receipts to link to one adjustment and derive its outstanding amount. Handling actual receipts that exceed the remaining amount remains unresolved; no application code/schema changed.

## Approved Q79 — edit presentation and audit retention — 2026-11-10

Saved post-Exit repayment entries may be edited by an authorized Accountant. Ordinary views show the latest value without displaying earlier versions; retain the original and corrections in backend audit history, with an optional note. Editing the entry does not change the actual Cash/Bank Receipt or movement.

- Preserve Q76-Q78 actor, classification, and partial/multiple repayment decisions.
- Technical impact: append an audited correction and render the latest effective value. Do not overwrite an actual money movement. Excess-receipt handling and typed source-link/model/API/transaction design remain open; no application code/schema changed.

## Approved Q80 — disposition of excess post-Exit repayment — 2026-11-10

When actual repayment exceeds the remaining open overpayment, the authorized Accountant chooses case by case to keep the excess open as due back to the Investor or record a separate actual refund after returning the money.

- Preserve the original Receipt at the actual amount received. Do not mark a refund before cash leaves; neither excess nor refund is Company Income/Profit.
- Technical impact: preserve the selected disposition and link any actual refund as a separate cash outflow. Typed source-link/model/API/transaction design remains open; no application code/schema changed.

## Approved Q81 — partial and multiple excess refunds — 2026-11-10

If excess repayment is kept open as due back to the Investor, it may be refunded in partial and multiple actual payments. Record each actual refund separately; the remaining due-back amount stays open until paid.

- Preserve Q76-Q80 authorization, original Receipt, case-specific disposition, audit, and no-Company-Income/Profit rules.
- Technical impact: link each actual refund outflow to the due-back source and derive the residual. No refund is recorded before actual payment; exact model/API/transaction design remains open. No application code/schema changed.

## Approved Q82 — full Vehicle prices and installment settlement — 2026-11-10

Record complete Purchase cost and agreed Sale price independently of payment timing. Permit partial/multiple seller payments, Buyer receipts, seller refunds and Buyer refunds, each as a separate actual linked cash event no greater than the current outstanding amount. A lower installment is valid and leaves the balance open; excess is rejected.

- Show full amount, paid/received, and remaining balance with a compact warning for a valid partial installment. For a Purchase correction that needs a seller excess refund, accept the correction only after the full excess has actually been received.
- Reuse this pattern for another module only when its authoritative total, typed obligation, and permissions are defined. No source, permission, or duplicate cash abstractions are added by this rule; exact APIs/schema remain architecture work.

## Approved Q83 — successful Sale-form Save confirms the actual Sale — 2026-11-10

A successful Save of the existing Sale form for an actual completed Vehicle sale creates the confirmed Sale and marks the Vehicle Sold. Buyer collection remains a separate state and may still be pending or partial.

- Do not add a second Confirm action or an independent manual Sold flag.
- Preserve the existing fail-closed deactivation checks: a confirmed Sale alone does not clear open or unknown Garage, financial, or Investor settlement positions.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q89 — block Purchase cost correction while Vehicle Management is OFF — 2026-11-10

Do not apply a cost correction to an existing Purchase while Vehicle Management is OFF, even if Accounting is ON. Wait until Vehicle Management is ON, preserving the existing Purchase, allocations, seller installments, and history in the meantime.

- The pre-OFF Seller payable installment exception remains unchanged.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q90 — block wrong-Investor Fund Credit correction while Investment is OFF — 2026-11-10

Do not correct an existing Fund Credit's Investor attribution while Investment is OFF, even if Accounting is ON. Wait until Investment is ON; preserve the original credit, Branch provenance, audit history, and single actual Cash/Bank movement.

- The correction changes attribution only and does not add or change a Cash/Bank event.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q91 — block standalone unused-principal return while Investment is OFF — 2026-11-10

When Investment is OFF, do not return unused Available Fund principal outside an Exit that had already started before the OFF transition. Wait until Investment is ON; keep Fund and Cash/Bank balances unchanged while blocked.

- Preserve the separate pre-OFF Exit settlement exception; actual money movement still requires Accounting ON.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q88 — block Buyer refunds while Vehicle Management is OFF — 2026-11-10

Block an actual Buyer refund against an existing Sale while Vehicle Management is OFF, even if Accounting is ON. Leave the Sale and refund obligation unchanged; create no Accounting event or Cash/Bank movement until Vehicle Management is ON.

- Preserve Q86's Buyer Receipt rule, Q87's Seller refund rule, and the separate pre-OFF Seller payable installment exception.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q87 — block Seller refunds while Vehicle Management is OFF — 2026-11-10

Block a Seller refund against a preexisting Vehicle Purchase while Vehicle Management is OFF, even if Accounting is ON. Keep the Purchase and its refund/correction position unchanged; create no Accounting event or Cash/Bank movement until Vehicle Management is ON.

- Preserve the separate pre-OFF Seller payable installment exception when Accounting is ON.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q86 — block Buyer Receipt while Vehicle Management is OFF — 2026-11-10

Do not record a Buyer Receipt against an existing Sale while Vehicle Management is OFF, even when Accounting is ON. Leave the Sale and receivable unchanged and create no Accounting event or Cash/Bank movement.

- A Buyer Receipt requires both Vehicle Management and Accounting to be ON.
- Preserve the separately approved pre-OFF Seller payable installment exception; this decision is limited to Buyer Receipt.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q84 — Branch permission for actual Buyer refunds — 2026-11-10

Branch Accountant may record an actual Buyer refund only for a Sale in their authorized Branch. A same-Company Company-level Accountant may record it for any Branch in that Company.

- This mirrors Q54's Branch boundary for seller refunds but applies only to actual Stock Vehicle Buyer refunds; it grants no generic cross-Branch permission.
- Validate the linked Sale's Company and original Branch server-side. Preserve the actual-cash-only, typed-link and partial/multiple refund rules.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q85 — Branch scope for Sale confirmation and Buyer Receipts — 2026-11-10

Branch Accountant may create/confirm a Sale and record its actual Buyer Receipts only for a Sale in their authorized Branch. Same-Company Company-level Accountant may do so for any Branch in that Company.

- The authority follows the Sale's server-owned Company/Branch; a submitted Branch value is not permission.
- Keep Buyer Receipt events separate from Sale confirmation and preserve Q84's separately scoped Buyer refund rule.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q92 — cap Seller refunds at net actual Purchase payments — 2026-11-10

The cumulative actual Seller refunds for one Purchase may not exceed the confirmed installments actually paid for that Purchase less earlier actual Seller refunds.

- Validate the cap under the Purchase lock and in the same transaction as the typed Accounting inflow; reject any excess without partial posting.
- Seller refund and Purchase cost correction remain separate manual actions linked to the same Purchase. Preserve the installment, refund, and Cash/Bank histories; no Company Income or supplier-credit balance is created.
- No application code, schema, API, or UI was changed by recording this decision.

## Current decision-status reconciliation — 2026-11-10

Earlier `BUSINESS DECISION REQUIRED` notes in this Phase 5 draft are retained as history. The following approved additions supersede those unanswered status statements:

- Purchase timing and seller terms: the approved Q39 decision allows purchase before full payment, including zero advance, requires full Purchase-cost source allocation, records the unpaid amount as Seller payable, requires Seller name and keeps Seller phone optional. Later decisions allow partial/multiple installments and define the permitted old-payable-only path while modules are OFF. The payment, typed-link, concurrency, API and migration contracts remain technical work.
- Buyer Receipt reference uniqueness and normalization: Q63 and Q64 decide Company + Cash/Bank-account scope across Branches, with trimmed, case-insensitive comparison. Typed source schema, database constraint, API and transaction remain technical work.
- Fund Credit allocation/correction: Q66 permits one transfer for one Investor credit; Q69–Q71 set correction authority, whole-credit amount and original receipt effective date. Q72–Q75 decide the handling and authority for a historical Profit overpayment after Exit.
- Seller refund cap: Q92 limits cumulative actual Seller refunds to net confirmed Purchase payments.
- Automatic demo/mock import: the approved Phase 5 scope does not automatically import demo records. A separately authorized historical import would require its own reviewed source and mapping; automatic import is not a current Phase 5 blocker.

Purchase/payment schema, typed Accounting links, lock ordering, concurrency, idempotency, endpoint/error contracts and migrations remain technical blockers. Vehicle deactivation remains blocked while Garage Job and Investor settlement checks lack authoritative providers.

## Approved Q93 — block Purchase cost correction while Investment is OFF — 2026-11-10

When Investment is OFF, reject a Purchase cost correction that changes Investor Fund use/allocation and wait until Investment is ON. Preserve the original Purchase, funding allocations, Seller installment/refund records, and history while blocked.

- Q89's separate Vehicle Management OFF block for Purchase cost correction remains in force. Actual Seller refunds retain their own module gates and the Q92 net-paid cap.
- Recheck Investment module revision inside the atomic correction command; create no partial correction or allocation change while OFF.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q94 — upward Purchase correction follows the original Purchase source split — 2026-11-10

For an upward Purchase cost correction, use that Purchase's originally recorded Investor Fund and Company Running Capital proportions. The split is Purchase-specific; do not hard-code 70:30 or substitute Investor Profit-share percentage. If Investor Fund cannot cover its proportional increase, Company Running Capital supplies the exact shortfall, subject to source-availability validation.

- Keep original allocation rows immutable and append exact fixed-precision adjustments so the total equals corrected Purchase cost. Downward correction remains governed by the separately approved proportional reduction and balanced-paise/Fund-first rule.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q95 — Purchase cost correction requires all three modules ON — 2026-11-10

Require Vehicle Management, Investment, and Accounting ON for any Purchase cost correction, including one that records no new cash movement. If any module is OFF, leave Purchase cost, source allocations, payable, installments, refunds, and history unchanged.

- This adds Accounting to Q89's Vehicle Management and Q93's Investment gates. It applies even when the correction itself is non-cash because it changes Accounting-owned Company Running Capital allocation.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q96 — Investment OFF blocks Buyer Receipt for Investor-funded Sale — 2026-11-10

Block a Buyer Receipt against an existing Investor-funded Sale while Investment is OFF, even if Vehicle Management and Accounting are ON. Wait until Investment is ON; leave the Sale receivable and Accounting records unchanged while blocked.

- Q86's Vehicle Management and Accounting requirements remain. This receipt gate is separate from the Buyer refund rule.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q97 — include audited Sale price correction in Phase 5 — 2026-11-10

Include an audited agreed-price correction for a confirmed Sale in Phase 5. Branch Accountant may correct only within the authorized Sale Branch; a same-Company Company-level Accountant may correct a Sale in any Branch in that Company.

- Preserve the confirmed Sale and actual Buyer Receipt/refund history; recalculate the Sale's current receivable/refund position under the existing V2 source rules.
- This supersedes the earlier Phase 5 scope text deferring Sale price correction and Buyer refunds. Other Sales, CRM, Garage, Investor Profit, and settlement boundaries remain as documented.
- Valid partial settlement remains supported with a compact remaining-balance warning; excess amounts remain rejected.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q98 — Sale price correction needs Vehicle Management and Accounting ON — 2026-11-10

Allow a Sale price correction when Vehicle Management and Accounting are ON, even when Investment is OFF. This is the user's repeated, latest Q98 answer and supersedes the earlier answer in this conversation that required all three modules.

- Keep the correction separate from Buyer Receipt, actual refund, Fund movement, or Profit payment.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q99 — Buyer refund may proceed while Investment is OFF — 2026-11-10

Allow an actual Buyer refund against an Investor-funded Sale when Vehicle Management and Accounting are ON, even if Investment is OFF.

- Preserve Q88's Vehicle Management OFF block. Q96's rule still blocks Buyer Receipts when Investment is OFF; the refund gate is different.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q100 — refresh derived Investor calculations from Sale sources — 2026-11-10

When an approved Sale price correction or actual Buyer refund is recorded while Investment is OFF, refresh affected Investor calculations from authoritative Sale, Buyer Receipt/refund, and Accounting source records. Recalculation creates no separate cash event or Investor Profit payment.

- Actual Cash/Bank events remain Accounting-owned. Investor Profit payments remain separate authorized actions with their own module and permission checks.
- No application code, schema, API, or UI was changed by recording this decision.

## Current Phase 5 scope and module-gate reconciliation — 2026-11-10

The later approved Phase 5 decisions Q95–Q100 supersede only the following older statements in this architecture:

- The earlier minimum-Sale scope paragraph that deferred Sale price correction and Buyer refunds: Q97 includes both in Phase 5 and assigns Sale correction to the Q85 Branch permission boundary.
- The earlier first Q98 response that required Investment ON for Sale price correction: the repeated, later Q98 answer requires Vehicle Management and Accounting ON; Investment may be OFF.
- Buyer Receipt and Buyer refund have deliberately different module gates: Q96 blocks Investor-funded Buyer Receipts while Investment is OFF; Q99 permits actual Buyer refunds while Investment is OFF when Vehicle Management and Accounting are ON.
- Q100 allows derived Investor calculations to refresh from their source records while Investment is OFF; it does not authorize Fund or Profit payment posting.

Existing Vehicle deactivation remains blocked while required authoritative Garage Job and Investor settlement providers are unavailable. Purchase/Sale typed Accounting links, endpoint/error contracts, transaction lock order, concurrency/idempotency, and migration sequence remain technical architecture work.

## Approved technical contract Q101 — Purchase installments are separate linked records — 2026-11-10

Record the full Vehicle Purchase cost once on the Purchase. Record every actual Seller installment as a separate payment record linked to that Purchase and to one separate Accounting payment/cash-movement event. Derive the remaining Seller payable from the Purchase, confirmed installments, and applicable approved corrections/refunds; do not maintain a manually editable paid-total or payable balance.

- A Purchase may therefore have multiple installment records, each with its own actual Accounting event.
- Preserve the approved atomic-write, current-outstanding validation, idempotency, module-gate and Company/Branch permission requirements. Exact FK/constraint layout, endpoint shape, lock order and migration DAG remain technical work.
- No application code, schema, API, or UI was changed by recording this contract.

## Approved scope and technical direction Q102 — direct Vehicle expenses — 2026-11-10

Phase 5 includes expenses entered directly against a Stock Vehicle. Each expense contributes once to that Vehicle's total cost; Garage Job-linked expenses remain deferred until the Garage phase.

- Keep one Sale record for the agreed price and allow multiple actual Buyer Receipt records linked to that Sale. Each actual Buyer Receipt uses the shared Accounting Cash/Bank movement owner once. Likewise, keep the Purchase cost once and record each actual Seller installment separately, linked to its Purchase and one Accounting movement.
- A direct Vehicle Expense is a typed Vehicle-owned source record. Any actual payment is separately recorded through Accounting and linked to that source. The common Accounting movement mechanism does not collapse Sale, Purchase, Vehicle Expense, Receipt, or Payment into one generic source record or endpoint.
- The expense amount/source-allocation representation, exact module gates, typed-link schema/API, concurrency and idempotency details remain to be finalized before implementation. Existing Expense/Payment, Investor Fund, Running Capital, Company/Branch permission, and module-gate rules continue to apply.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q103 — Vehicle cost funding and Company Expense boundary — 2026-11-10

For a direct cost of an Investor-funded Stock Vehicle, use available Investor Fund first; record any unfunded shortfall as Vehicle-linked Company Running Capital. Do not overdraw Investor Fund or classify the same Stock Vehicle-specific cost as Company Accounting Expense merely because Company Running Capital supplied part of it. A customer's Vehicle cost belongs on its Garage Job bill, which remains later Garage-phase scope.

- Q102's direct Stock Vehicle expense scope and once-only Accounting cash-movement ownership remain.
- This supersedes only the Q102 implementation wording that suggested applying generic Company Accounting Expense/Payment classification to Vehicle costs. Accounting still records actual Cash/Bank movement once, linked to the typed Vehicle cost source.
- Exact source-allocation schema, module gates, API/error contracts, concurrency/idempotency behavior and migration order remain open. No application code, schema, API, or UI was changed by recording this decision.

## Approved Q104 — module gates for direct Vehicle Expense — 2026-11-10

Require Vehicle Management and Investment ON to save a direct expense and its Investor Fund/Company Running Capital allocation for an Investor-funded Stock Vehicle. Accounting is required only when an actual Cash/Bank payment is recorded. If Accounting is OFF, save no cash event and wait to record the actual payment.

- This resolves the direct Vehicle Expense module gate left open in Q102 and listed as open technical detail under Q103. Its scope is only the Investor-funded Stock Vehicle Expense/source-allocation flow.
- Purchase funding and Purchase cost correction retain their separately approved module gates; do not generalize this rule to other operations.
- This supersedes Q102's unresolved direct-expense module-gate question. Typed allocation/payment schemas, API and error contracts, concurrency, idempotency, and migration order remain technical work.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q105 — Vehicle Expense payable and partial payments — 2026-11-10

Record the full direct Stock Vehicle Expense when incurred, independently of payment. Derive its unpaid payable from the full approved cost less confirmed linked actual payments. Allow zero, one, or multiple partial payments; reject overpayment. Each actual payment is a separate typed record linked to the Vehicle Expense and one Accounting Cash/Bank movement. Payment settles the payable and does not add the same cost to Vehicle total again.

- Example: ₹5,000 repair expense, ₹2,000 paid; Vehicle cost is ₹5,000 and payable is ₹3,000.
- Q103 source funding and Q104 module gates remain. Stock Vehicle cost is not Company Accounting Expense; customer Garage Job billing remains later-phase scope.
- This supersedes the Q102 ambiguity about whether direct Vehicle Expense must wait for full payment.
- Exact payable/payment model, typed Accounting source link, API/error contract, concurrency/idempotency and migration order remain technical work. No application code, schema, API, or UI was changed by recording this decision.

## Approved Q106 — shared payment account preference — 2026-11-10

Share the per-Accountant, per-Company last-successfully-saved Cash/Bank account preference between Seller installment and direct Vehicle Expense installment forms. The selected account remains editable. Only a successful payment updates the preference; an abandoned, failed, or rejected attempt does not.

- Store the actual account ID on each payment record and revalidate access on every posting. Preference is not authorization and does not change historical payments.
- This decision applies to these two Phase 5 forms only. Persistence mechanism and conflict/retry behavior for simultaneous successful payments remain technical design details.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q107 — required external reference for Vehicle Expense installments — 2026-11-10

Require a user-entered external reference (bank transaction ID or Cash voucher number) for every actual direct Stock Vehicle Expense installment. Store it on the typed payment source and linked Accounting event source_reference.

- The external reference is traceability text, not a payment UUID, foreign key, or idempotency key. It does not replace Q105 payment/outstanding validation or Q106 account selection.
- No duplicate-reference uniqueness or normalization behavior is approved; do not copy the Buyer Receipt or Fund Credit constraints without a separate decision.
- The form, schema, source-link, API/error, concurrency, idempotency and migration contracts remain technical work. No application code, schema, API, or UI was changed by recording this decision.

## Approved Q108 — Vehicle Expense payment reference uniqueness — 2026-11-10

Reject duplicate external references for actual direct Vehicle Expense installments within the same Company and same Cash/Bank account, across Branches. Trim leading/trailing whitespace and compare case-insensitively.

- This supersedes Q107's statement that no uniqueness or normalization rule had been approved for this source. Q107's required-reference rule remains.
- Apply this only to Vehicle Expense payment references; do not extend it to Seller installments, Buyer Receipts, Fund Credits, or other source types.
- The reference remains traceability text, not payment identity or idempotency. Enforce the comparison atomically with posting.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q109 — vendor refund precedes downward Vehicle Expense correction — 2026-11-10

If reducing a direct Vehicle Expense after actual payment would make confirmed net payments exceed corrected cost, require the vendor's actual excess refund to be received and recorded in Accounting before applying the correction. Preserve the original Expense and cash history; record the refund as a separate linked movement and append the correction afterward.

- Example: ₹5,000 cost, ₹2,000 paid, corrected cost ₹1,500; first receive and record the ₹500 vendor refund, then append the cost correction.
- No open vendor credit or balancing transaction is created while waiting. Q103 funding source and Q104–Q108 decisions remain.
- This resolves the refund-before-correction rule only. The source-allocation adjustment for the corrected cost remains open and must not be inferred.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q110 — Fund-first source reallocation after Vehicle Expense correction — 2026-11-10

After Q109's actual vendor refund and a permitted downward Vehicle Expense correction, calculate the new source allocation using available Investor Fund first, then Company Running Capital for the exact shortfall. Do not carry forward the original source ratio. Example: corrected ₹1,500 expense is ₹1,500 Fund + ₹0 Running Capital if enough Fund is available.

- Preserve prior allocations and append audited adjustments. Revalidate available Fund at commit.
- Q94's proportion-preserving correction rule remains Purchase-specific and is not changed by Q110.
- This resolves the Q109 source-allocation item only. Module gates for Vehicle Expense correction and exact technical transaction/API/migration contracts remain open.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q111 — Vehicle Expense correction module gates — 2026-11-10

After the actual vendor refund required by Q109 is recorded, applying the direct Vehicle Expense correction and Q110 source reallocation requires Vehicle Management, Investment, and Accounting all ON, even if no new cash moves. If any is OFF, leave cost, payable, allocations, and history unchanged.

- This is specific to applying a Vehicle Expense correction. Q104's Vehicle Management + Investment gate for new Expense/allocation save and Accounting gate for actual payments remain.
- Purchase/Purchase-correction gates remain separate.
- This resolves the Q110 module-gate item. Exact correction API/schema, lock order, idempotency and migrations remain technical work.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved clarification — Company-funded Stock Vehicle costs — 2026-11-10

When a direct Stock Vehicle cost has no Investor Fund source, assign the full amount to Vehicle-linked Company Running Capital; do not create an Investor Fund-use allocation. Customer Vehicle costs remain Garage Job/customer-bill scope for the later Garage phase. This clarifies the already approved Q103 answer and preserves the Investor Fund-first/exact-shortfall rule for Investor-funded Vehicles.

- The module gate and actor scope for a Company Running Capital-only Vehicle Expense remain unresolved business decisions.
- No application code/schema/API/UI change is made by this documentation clarification.

## Approved Q112–Q122 — Vehicle Expense decisions — 2026-11-10

- Branch Accountants may record direct Vehicle expenses, their installments, Vendor refunds, and cost/source corrections only for Vehicles in their authorized Branch. A same-Company Company-level Accountant may do each action in any Branch.
- For a direct Stock Vehicle cost without Investor Fund, use Company Running Capital only: Vehicle Management is required to record the cost, Investment is not required, and Accounting is required for actual payment.
- Actual Vendor refunds require Vehicle Management, Investment, and Accounting ON. No maximum refund amount based on prior Vendor payments is approved.
- One Vehicle may use only one Investor's Fund. Allow upward corrections for an additional Vendor bill; allocate the corrected cost Fund-first, then Company Running Capital for the exact shortfall, and derive the payable from corrected cost less actual payments.
- Downward correction requires all three modules even if no refund is needed. Apply it to the original Expense effective date and affected Investor calculation; retain the actual correction timestamp separately.
- Refund reference/duplicate policy and classification of a refund above net paid remain unresolved. These entries do not settle typed schema/API, locking, idempotency, or migration contracts.

## Approved Q118/Q123 — Vehicle Expense Vendor refunds — latest clarification — 2026-11-10

- An actual Vendor refund does not require an external reference and may reuse another refund's reference. This latest Q118 answer supersedes the earlier answer requiring a reference and duplicate blocking for refunds only; Q107/Q108 remain mandatory for Vehicle Expense installments.
- Record the full actual refund in Cash/Bank once. Apply to the Vehicle Expense only up to its remaining net actual payments. Provide a flexible option for the Accountant to assign any excess to another appropriate record; do not automatically classify excess as Company Income.
- This refines Q117's no-cap answer: the full actual receipt is allowed, while the Vehicle Expense application remains limited to net actual payments.
- The one-movement/multiple-destination typed allocation contract, API, transaction and idempotency details remain technical work. No application code/schema/UI change is made by this documentation addition.

## Approved Phase 5 blocker decisions Q124–Q132 — 2026-11-11

- **Q124, Q130, Q132 — Excess Vehicle Expense refund:** Record one actual receipt and one Cash/Bank movement for the full money received. Apply only the remaining net paid amount to the Vehicle Expense. Reconcile the excess to explicit, typed allocations. The Accountant may classify the excess as Company Income only by creating a separate Income event with a selected category and note, then applying the same actual Receipt to that Income. Do not edit an old Income event, auto-classify, or create a second movement. If no eligible destination exists, do not post the refund until one exists.
- **Q125, Q127, Q131 — pooled Fund authority:** Company-level Accountant alone creates and fully allocates an Investor-linked Vehicle Expense. No Branch-created pending draft may reserve pooled Fund. A Branch Accountant cannot create Investor-linked Vehicle Expense.
- **Q126 — Company Running Capital:** Record the exact Vehicle-linked Company source shortfall without requiring a pre-funded pool. This allocation is separate from actual Cash/Bank movement.
- **Q128–Q129 — Company-only Purchase:** Branch Accountant may create a Company Running Capital-only Purchase in an authorized Branch; Company-level Accountant may do so in any same-Company Branch. Require Vehicle Management + Accounting; Investment is not required. Investor Fund-funded Purchase requires all three modules.
- **Scope simplification:** defer additional automation/approval/posting workflows until the core system is ready. Preserve previously approved automation decisions as later work; do not make them a Phase 5 blocker.

### Typed API and persistence contract

- `VehiclePurchase`, `VehicleExpense`, and `VehicleSale` are Vehicle-owned source facts. `PurchaseInstallment`, `VehicleExpensePayment`, `SaleReceipt`, `SellerRefund`, `VehicleExpenseRefund`, and `BuyerRefund` are separate actual settlement facts. Each actual money event links to exactly one Accounting event and one AccountMovement through a typed, same-Company source link.
- Purchase and Expense source allocations use separate typed rows for Investor Fund and Company Running Capital and must reconcile exactly to the approved cost. Company Running Capital does not create a Cash/Bank event. Purchase allocations are reserved at creation and installment balance is derived from immutable linked settlement history.
- A Vehicle Expense refund has one parent actual receipt and child typed allocations to the original Expense (capped at remaining net paid amount) and an explicitly selected eligible destination. Company Income is represented by a separate new Income event plus an Accounting application from this same receipt for the selected excess. Child allocation sum equals the actual receipt amount. No free-form polymorphic source ID is permitted.
- Mutations use action-specific module gates, persisted Company/Branch authorization, an immutable source Branch for historical settlements, Company/module revision locks, source-row and outstanding-balance locks, idempotency, and one database transaction. Any failure rolls back source records, applications, links, movements, preferences, and idempotency response together.
- Preserve the current API error envelope (`detail`, `code`, `request_id`): validation 400, permission/module 403, scoped not-found 404, state/balance/idempotency conflict 409. Use stable conflict codes for `MODULE_STATE_CHANGED`, `IDEMPOTENCY_KEY_REUSED`, and source outstanding conflicts.
- Migration order is acyclic: Vehicle source facts first (depending on existing Accounting/Investment baselines), Investment Fund-use allocations next, Accounting typed links/Running Capital extensions after Vehicle records exist, then database guards. Fresh/replay PostgreSQL migration checks are required before release.
- Automation: no new approval automation is part of the Phase 5 core. Existing separately approved Company automation-mode decisions remain recorded for future work.

**Historical implementation status at the 2026-11-11 decision checkpoint:** Business decisions Q124–Q132 were resolved, while implementation and local verification were still outstanding. That dated statement is superseded for the approved Phase 5 core scope by the implementation and audit verification checkpoints below. Vehicle deactivation/registration reuse remains deferred until authoritative Garage Job and Investor settlement providers exist.

## Audit readiness and verification update — 2026-11-16

The approved Phase 5 core scope is **implemented and locally verified**. The four findings from the 2026-11-16 implementation audit are fixed: corrected Purchase payable caps, one Investor attribution per Vehicle, Company-level authority for pooled Fund increases during expense correction, and stable idempotency for omitted optional dates. The itemized report is [`output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md`](../../output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md).

Disposable PostgreSQL verification: full Django `apps` suite 343/343 passed; the Purchase, Expense and Sale API suites passed 24/24 after the expense suite moved to `TransactionTestCase`; fresh migration, migration-state, Django system and model/migration-drift checks passed. React passed 137/137 tests; configured lint and TypeScript/Vite build passed. The Vite main-chunk advisory remains at 614.29 kB.

The Phase 5 candidate is locally committed on `codex/phase5-investment-foundation` for audit-branch review. No remote push, merge or deployment is recorded by this checkpoint. Staging/production, hosted runtime grants and backup/restore remain `UNVERIFIED`. `virms-local-8002-pgdata` was not accessed.
