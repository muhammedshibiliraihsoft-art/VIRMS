# VIRMS — Phase 8–10 handoff

Snapshot: 2026-11-19, approximately 14:04 IST. This handoff was requested explicitly. The prior tracked goal was cleared by the user; do not recreate it or continue implementation until the user explicitly requests continuation. This file transfers context, not uncommitted file contents.

## Current Task
Complete and verify the approved Phase 8 integrated finance, Phase 9 main-system core, and Phase 10 investor portal in this exact worktree, preserving Phase 1–7 contracts and all unrelated dirty work. HIGH-RISK: financial, tenancy, migration and settlement work. The current request is handoff only. No commit, push, deploy, branch switch, staging/production database changes or unrelated cleanup authorized by handoff. Follow the user-provided and repository AGENTS.md rules; no invented business rules.

## Verified Current State
- VERIFIED FROM GIT: worktree `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`, HEAD `d57a92085344228e8bf1b86d0867ec1d57adf662`; substantial unstaged and untracked work, no staged changes. Exact pre-handoff status below.
- VERIFIED FROM REPOSITORY: phases 8–10 are INCOMPLETE. `apps/investment/services.py` blocks new ordinary vehicle profit payment with `PRINCIPAL_RECOVERY_REQUIRED`. Finance snapshots, Loss offsets, monthly Interim and partial portal surfaces exist. Owner allocation helper is calculation only, not payment or a complete distribution workflow.
- VERIFIED FROM TESTS: the ongoing disposable-PostgreSQL focused run completed 42/42 tests (finance calculations, four Loss-offset Sale tests, portal binding/API); details below. This is not integrated acceptance.
- VERIFIED FROM RUNTIME / DATABASE: prior focused test process used a disposable PostgreSQL test database and destroyed that test DB when done; no persistent production/staging runtime was checked. Disposable migration 0029 forward/reverse/reapply was run immediately before handoff, not as part of handoff. Recheck identity before any future database action.
- DOCUMENTATION CLAIM: architecture Phase 8/9/10 documents contain earlier success snapshots, not proof against this exact current tree. `README.md` has a dated 2026-11-03 branch snapshot and is stale for this worktree.
- INFERENCE: completing capital recovery requires integration across Fund credit, typed Accounting links, Vehicle Sale receipt/refund/correction, and all availability consumers; design and test that impact before implementation.
- UNVERIFIED: complete browser workflows, CI, deployed grants, staging/production, live data, full current React/backend suite, final security/role and concurrency audit.
- BUSINESS DECISION REQUIRED: none identified as newly required for the next read-only recovery design; do not infer missing rules. Latest explicit decision: same-Company Company-level Accountant alone confirms Investor principal and Company Running Capital recovery.

## Branch / Worktree
Pre-write snapshot (before this file was created):
```text
## codex/phase5-investment-foundation
 M apps/accounting/models.py
 M apps/accounting/services.py
 M apps/accounting/views.py
 M apps/accounts/audit.py
 M apps/accounts/policy.py
 M apps/investment/models.py
 M apps/investment/serializers.py
 M apps/investment/services.py
 M apps/investment/tests/test_api.py
 M apps/investment/tests/test_concurrency.py
 M apps/investment/urls.py
 M apps/investment/views.py
 M apps/vehicles/models.py
 M apps/vehicles/services.py
 M apps/vehicles/tests/test_purchase_api.py
 M apps/vehicles/tests/test_sale_api.py
 M apps/vehicles/tests/test_sale_concurrency.py
 M apps/vehicles/urls.py
 M apps/vehicles/views.py
 M architecture/01-DATA-FLOW.md
 M architecture/02-API-FLOW.md
 M architecture/04-CHANGE-IMPACT-COMPATIBILITY.md
 M demo/react/src/App.tsx
 M demo/react/src/__tests__/investorDataBoundary.test.tsx
 M demo/react/src/api/__tests__/accountingApi.test.ts
 M demo/react/src/api/__tests__/phase5Api.test.ts
 M demo/react/src/api/accountingApi.ts
 M demo/react/src/api/phase5Api.ts
 M demo/react/src/api/queryKeys.ts
 M demo/react/src/components/__tests__/AppShellNavigation.test.tsx
 M demo/react/src/components/shared/CompanyAccountingView.tsx
 M demo/react/src/components/shared/CompanyResultView.tsx
 M demo/react/src/components/shared/Phase5WorkspaceView.tsx
 M demo/react/src/components/shared/ReportShell.tsx
 M demo/react/src/components/shared/__tests__/Phase5WorkspaceView.test.tsx
 M docs-final-v2/02-user-roles-permissions.md
 M docs-final-v2/05-vehicle-investor-finance-workflow.md
 M docs-final-v2/09-company-accounting-owner-distribution.md
 M planning/V2-DEVELOPMENT-ROADMAP.md
?? apps/accounting/migrations/0018_company_share_recognition.py
?? apps/accounting/migrations/0019_vehicle_company_share_guards.py
?? apps/accounting/migrations/0020_remove_accountingevent_acct_event_type_ck_and_more.py
?? apps/accounting/migrations/0021_accountingsourcelink_investor_vehicle_profit_payment_and_more.py
?? apps/accounting/migrations/0022_investor_profit_payment_guards.py
?? apps/accounting/migrations/0023_investor_interim_accounting_source.py
?? apps/accounting/migrations/0024_interim_payment_guards.py
?? apps/investment/finance.py
?? apps/investment/migrations/0008_investoraccountbinding.py
?? apps/investment/migrations/0009_investorprofitshareagreement.py
?? apps/investment/migrations/0010_vehicleresultconfirmation.py
?? apps/investment/migrations/0011_investorexitrequest_investorexitrequesthistory_and_more.py
?? apps/investment/migrations/0012_phase8_integrity_guards.py
?? apps/investment/migrations/0013_investorprofitcalendarconfiguration.py
?? apps/investment/migrations/0014_profit_calendar_integrity_guards.py
?? apps/investment/migrations/0015_company_share_recognition.py
?? apps/investment/migrations/0016_investorvehicleprofitpayment.py
?? apps/investment/migrations/0017_investor_profit_loss_offset.py
?? apps/investment/migrations/0018_profit_loss_offset_integrity_guards.py
?? apps/investment/migrations/0019_investorinterimpayment.py
?? apps/investment/migrations/0020_investor_profit_period_reconciliation.py
?? apps/investment/migrations/0021_investor_profit_period_guards.py
?? apps/investment/migrations/0022_exit_notice_extension.py
?? apps/investment/migrations/0023_exit_notice_extension_guards.py
?? apps/investment/migrations/0024_exit_notice_audit_details.py
?? apps/investment/migrations/0025_result_kind_sign_guard.py
?? apps/investment/migrations/0026_vehicle_result_audit_amounts.py
?? apps/investment/migrations/0027_loss_suggestion_snapshot.py
?? apps/investment/migrations/0028_loss_suggestion_guards.py
?? apps/investment/migrations/0029_loss_offset_profit_dates.py
?? apps/investment/portal.py
?? apps/investment/tests/test_phase8_finance.py
?? apps/investment/tests/test_portal_binding_api.py
?? apps/vehicles/migrations/0010_vehiclepurchase_investor_share_agreement_and_more.py
?? architecture/phase-08-integrated-finance/
?? architecture/phase-09-main-system-core/
?? architecture/phase-10-investor-portal/
?? demo/react/src/components/shared/InvestorPortalView.tsx
?? demo/react/src/components/shared/InvestorProfitReviewView.tsx
?? demo/react/src/components/shared/Phase8ReadinessView.tsx
?? demo/react/src/components/shared/__tests__/CompanyResultView.test.tsx
?? demo/react/src/components/shared/__tests__/InvestorPortalView.test.tsx
?? demo/react/src/components/shared/__tests__/InvestorProfitReviewView.test.tsx
?? demo/react/src/components/shared/__tests__/Phase8ReadinessView.test.tsx
?? docs/antigravity-back-office-ui-brief.md
?? output/PHASE-01-05-CURRENT-IMPLEMENTATION-AUDIT-2026-11-17.md
```
No staged diff was reported. After writing, this `CODEX_HANDOFF.md` is additionally untracked unless independently changed. The unrelated worktrees including `D:/VIRMS` on `staging` and `D:/VIRMS/tmp/audit-consolidation-20261102` on `codex/audit` are distinct: do not assume local-only files exist there or on another machine.

## Existing Uncommitted Work
39 tracked files had unstaged changes at snapshot, plus numerous untracked files listed above; all must be preserved. `apps/investment/*`, `apps/vehicles/*`, `apps/accounting/*`, `apps/accounts/policy.py`, React components/API/tests and V2/architecture docs include ongoing finance/portal work. Untracked migrations accounting 0018–0024, investment 0008–0029 and vehicles 0010 are locally necessary to the ongoing implementation; do not delete or apply to a persistent DB. The untracked Antigravity brief and Phase 1–5 audit output have other-task history/ownership not verified; leave them alone. A handoff does not transfer these files to another checkout.

## Files Changed
- This handoff operation creates only `CODEX_HANDOFF.md`.
- Existing work: `apps/investment/services.py`, `finance.py`, `portal.py`, `models.py`, `urls.py` implement partial finance, result/offset, period and portal flows; `apps/vehicles/services.py` owns current Vehicle/receipt and fund allocation; `apps/accounting/models.py` and services own cash events and typed links.
- `apps/investment/migrations/0029_loss_offset_profit_dates.py` is an untracked migration removing a former date-order guard; earlier migrations include snapshots, audit and constraints. `demo/react/src/components/shared/Phase5WorkspaceView.tsx`, `InvestorProfitReviewView.tsx`, `InvestorPortalView.tsx` provide partial UI.
- `architecture/phase-08-integrated-finance/`, `phase-09-main-system-core/`, `phase-10-investor-portal/`, V2 05/09 and architecture 01/02/04 contain scope/decisions and local checkpoint claims. Verify claims against current code.

## Completed Work
Locally observed implementation, not phase completion: editable Investor/Company Loss confirmation with audit and separately stored suggested split; same Investor current unpaid Profit offset including earlier/same-day/future Sale, with stale offsets excluded from current calculations and marked for review; Investor period calculation snapshots and restatement tracking; partial/repeated Interim payments; Portal binding and restricted self views; Exit request/cancellation/notice extension; typed Company share recognition. See respective services/models and architecture Phase 8 checkpoint. Certain portions were tested only in focused tests, not end-to-end browser acceptance.

## Pending Work
1. Trace and implement authoritative principal and Company Running Capital recovery from actual Buyer receipts: single existing cash effect, typed links, Company-accountant confirmation, Fund availability, partial collection, corrections, refund reserves, idempotency, concurrency and reversible migrations. Preserve `PRINCIPAL_RECOVERY_REQUIRED` gate until all its prerequisites are verifiably satisfied. `InvestorFundCredit` currently has an Accounting capital-inflow relationship; naively creating another cash event duplicates receipts.
2. Complete Investor period confirmed payable/recoverable and restatement, final Exit settlement, post-Exit recovery/repayment/refund/waiver in accordance with current V2 rules and decisions; distinguish confirmed calculation from actual paid cash.
3. Complete Company period confirmation, negative carryforward and actual Owner Distribution with protected split snapshots and partial payouts; no automatic Owner payments.
4. Finish Phase 9 authoritative dashboard/detail data and integration; audit existing demo-derived `App.tsx` state before replacing it. Finish Phase 10 own-only payable/recoverable/settlement projection and UI with privacy restrictions.
5. Complete fresh/replay and historical migration checks on verified disposable Postgres, focused/related regressions including concurrency and role/tenant tests, React tests/lint/build and authenticated browser reload/responsive acceptance; consolidated risk audit and reconcile roadmap/architecture only after proof. CI, staging and production unverified; no deployment without explicit authorization.
6. One earlier React Phase5WorkspaceView test expecting successful Profit payment is reported to fail because the payment gate is intentionally closed; verify against current tree after implementing recovery. Do not remove/weaken it merely to pass.

## Locked Decisions
- V2 `docs-final-v2/05-vehicle-investor-finance-workflow.md` §§2–4: distinguish actual Buyer receipts, principal recovery, Running Capital and profit; no duplicate cash; corrected refund reserves and history; profit payout requires full collection, principal recovery and refund resolution.
- User confirmed recovery confirmation Company-level Accountant only; recorded in Phase 8 architecture “Confirmed follow-up decisions”. Existing same-Branch vs Company roles for Loss offsets remain in `apps/accounts/policy.py` and V2.
- Investor Loss share is suggested from agreement, editable by authorized Company Accountant and explicitly confirmed with reason; no automatic Fund debit. Offset against same Investor's current/future unpaid Vehicle profit, including another vehicle, preserves gross and records separate audited offset. On Exit, user-approved exceptional rules in V2 apply.
- Monthly Interim can be paid in parts up to monthly cap; Company Accountant or authorized payment-Branch Accountant. Portal binding is one active account per Investor profile per Company and one profile per account. All policy details require source reconciliation; user decisions do not prove implementation.

## Data Flow
Observed partial flow: React Vehicle financial position / Investor review -> tenant-scoped Vehicle and Investment API -> permission/module checks and current-source fingerprint -> immutable Vehicle result / offset / period snapshot -> source projections update UI. Sale receipts create typed Accounting Cash/Bank movement; offsets and reconciliation snapshots create no cash movement. `InvestorPortalView` -> `portal/self/` resolves server-side active binding -> own-source projection, omitting Accountant reason and sensitive payment details. Principal recovery is not yet connected: Fund availability derives from credit lots minus return allocations, use allocations and use adjustments; see `apps/investment/services.py:_available_credit`, `fund_summary`, `apps/vehicles/services.py:_available_credit`, `apps/investment/portal.py`.

## API Flow
Paths under `/api/v1/tenants/{company_id}/`:
- `investment/investors/{id}/profit-periods/` GET REQUIRED for Company Accountant period review; `profit-period-reconciliations/` POST CONDITIONAL on explicit confirmation.
- `investment/vehicle-results/{loss_id}/profit-loss-offsets/` GET/POST CONDITIONAL on viewing/confirming a Loss offset; Company/Branch scope remains relevant.
- `investment/portal/self/`, fund/interim histories CONDITIONAL on Investor portal use, server-bound identity. Exit request/review/extension and binding routes CONDITIONAL on explicit actions.
- `investment/vehicle-results/{id}/profit-payments/` POST CONDITIONAL, currently blocked for new payments pending principal recovery. Vehicle Sale/receipt/refund and Accounting movement routes remain authoritative; inspect `apps/vehicles/urls.py` / `apps/accounting/urls.py` before modification.
- No call identified as safely REDUNDANT or DUPLICATE; other calls UNKNOWN until traced. Preserve idempotency keys and source identity.

## Database / Migration Impact
Untracked local migrations listed in Git status create/guard binding, result versions, profit payments/offsets, Interim payments, period snapshots, Exit notice and typed Accounting sources. Migration 0029 replaces the Loss-offset scope trigger function and has reverse SQL. `makemigrations --check --dry-run` previously reported no changes; verify again only during authorized continuation. Existing append-only rows, tenant scope, credit lot provenance and historical audit are essential. Principal recovery schema/link/adjustment design is not yet implemented; do not apply any migration to persistent environments from this handoff.

## Security / Auth / Tenant Impact
`apps/accounts/policy.py` defines Company-only and Branch actions; `apps/investment/portal.py:_self_binding` derives investor identity server-side. Preserve Company isolation, Branch assignments, current module revision checks, consented role policies and private projection boundary. User's Company-only recovery decision is recorded but not implemented. Full role/IDOR audit remains UNVERIFIED. Never include credentials in handoff.

## Concurrency / Transaction / Idempotency
Financial actions have existing transactional/idempotency and PostgreSQL guard mechanisms; inspect `apps/investment/services.py`, `apps/vehicles/services.py`, and corresponding migrations. Fund lot allocation locks credits; recovery must serialize against funding, withdrawals, corrections/refunds, concurrent/retried requests and not duplicate events. Comprehensive recovery concurrency/rollback proof is MISSING.

## Tests / Validation Actually Run
- Just completed process (started before handoff): `manage.py test apps.investment.tests.test_phase8_finance apps.vehicles.tests.test_sale_api.VehicleSaleApiTests.test_confirmed_investor_loss_offsets_future_profit_once_without_cash_movement apps.vehicles.tests.test_sale_api.VehicleSaleApiTests.test_confirmed_investor_loss_offsets_earlier_unpaid_profit apps.vehicles.tests.test_sale_api.VehicleSaleApiTests.test_confirmed_investor_loss_offsets_same_day_unpaid_profit apps.vehicles.tests.test_sale_api.VehicleSaleApiTests.test_cross_branch_loss_offset_requires_company_accountant apps.investment.tests.test_portal_binding_api --verbosity 1`: 42 tests passed, disposable PostgreSQL test database; tests scope only.
- Immediately before handoff: targeted React `npm test -- --run src/components/shared/__tests__/Phase5WorkspaceView.test.tsx -t 'offset'`: 1 passed, 16 skipped by filter; `npx tsc --noEmit` passed; `git diff --check` passed with CRLF warnings; investment migration 0029 forward/reverse/reapply on disposable local DB and `makemigrations --check --dry-run` passed. These are prior work, not operations performed to prepare this handoff.
- Earlier project docs report broader tests; they are historical claims, not fresh proof of current full tree. No browser, full current suite, CI or hosted deployment verified here. No additional mutating checks were started for handoff.

## Known Problems / Risks
- A — new deal Profit payment remains deliberately blocked; authoritative recovery and correction/refund logic missing.
- A — final settlement, Company period/carryforward and Owner payout are incomplete; do not mark phases complete.
- B — Investor Portal final payable/recoverable missing, Phase 9 dashboard/detail partly demo-backed, integrated browser and role acceptance unverified.
- B — previously confirmed offset becoming stale is now excluded with review status; historical resolution and full cross-period restatement require verification.
- D — extensive uncommitted work exists only locally; CRLF Git warnings, older docs contain stale historical snapshots.

## Regression / Old Flow Risk
Avoid breaking old phase 4–7 cash/accounting paths, source links and typed constraints, Branch authorization, Fund FIFO, old credits/corrections, investor privacy, Exit pre-OFF rule, partial payments/refunds, prior immutable snapshots, idempotent replay and UI reload. Correcting recovery must not duplicate cash, overdraw Fund, silently change old history, or unlock payouts on stale/refundable funds.

## Documentation Status
Phase 8 architecture contains the recent recovery authority and stale-offset notes. Phase 9 matrix has dated historical descriptions (some reconciliation lines superseded by newer Phase 8/10 updates); verify/reconcile only after code changes. V2 describes target, not proof of completion. This handoff documents the verified snapshot only.

## Exact Next Safe Step
Only after an explicit continuation request: inspect current worktree and prior dirty diffs, then map existing Fund credit/source-link database guards and every availability consumer against actual Buyer receipt/correction/refund flow; design the Company-accountant-only transactional recovery with focused failing tests before changing code. Preserve payout gate until full recovery/refund verification.

## Do Not Touch
Do not clean/reset/stash/switch branches, discard work, touch sibling worktrees, production/staging databases or secrets, commit/push/deploy, redesign UI, change unrelated docs, or start another phase without authorization.

## Resume Checklist
Read global and applicable repository/nested AGENTS.md; read this entire handoff; verify repo/worktree/branch/HEAD; inspect status, staged/unstaged/untracked diffs and relevant files; preserve dirty work; compare handoff with current repository and report contradictions; continue only explicitly requested and confirmed scope with required checks and approvals.
