# AR-8 — Phase 8 implementation map

**Purpose:** Give the next agent an ordered list of unfinished Phase 8 workflows. This is a plan, not evidence of completion. Snapshot: 2026-11-19, `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`, HEAD `d57a92085344228e8bf1b86d0867ec1d57adf662`. The worktree is dirty; verify its current state before editing and preserve every existing change.

## Authority and execution

Read applicable `AGENTS.md`, `README.md`, V2 finance/Company/role rules, affected code, and relevant `architecture/01`–`04` maps. Code and tests prove implementation; a handoff or this plan does not. Work in order **R → E → O → acceptance**. Finish and validate the authorized workflow before starting the next under current project rules. No commit, push, merge, deploy, persistent DB changes, destructive Git action, or repeated whole-repo audit.

## Reuse; do not implement twice

| Existing source | Already supplies | Missing boundary |
|---|---|---|
| `apps/vehicles/services.py`, `apps/investment/services.py` | Vehicle result, manual Loss offsets, Investor calendar/interim/deal payments, Exit request/notice | Period snapshots are **not** confirmed payable; ordinary Profit payment still has unconditional `PRINCIPAL_RECOVERY_REQUIRED`. |
| `apps/investment/models.py`, `fund_position.py`, `selectors.py`, migration `0030_vehicle_capital_recovery.py` | Partial recovery, credit-lot/refund classification prototype | Latest edits unverified; API/UI, reserve/refund integration and cross-consumer balance incomplete. |
| `apps/accounting/finance.py`, `apps/investment/finance.py` | Company carryforward and exact Owner split arithmetic (`allocate_owner_distribution`) | No confirmed Company period, protected Owner snapshot or actual payout workflow. |
| `CompanyResultView.tsx`, `Phase8ReadinessView.tsx`, `Phase5WorkspaceView.tsx` | Existing UI structure | Wire actual confirmed positions/actions; preserve design and routes. |

Inspect only affected diff and direct dependencies. Before changing untracked migration 0030, establish whether any database that must be preserved already applied its earlier form. If unknown, use an additive migration. Earlier test reports predate latest recovery edits.

## R — Recovery and Buyer refund

Build on existing recovery records, not a parallel ledger. One Buyer receipt has one Accounting movement. Confirm source-linked Investor principal and Company Running Capital recovery, exact credit-lot allocations, Company/Investor/Vehicle ownership, receipt/capital caps, audited correction history and retry safety. Investor-only partial receipts may recover principal; mixed-funded positive settlement follows the approved full-collection/principal-first rule. Reconcile SQL `investment_credit_available` with Python `investor_fund_position`; choose one authoritative balance contract and make Fund summary, Purchase/Expense use, principal return, portal and DB guards agree.

For Sale correction, reserve only principal-backed Buyer refund money **actually held in Fund**; uncovered refund remains payable. Company Accountant specifies the Investor-principal portion of **each actual partial refund, including zero**. Debit Fund lots actually held, retain recovery provenance, create one Buyer refund Accounting movement and preserve classification history. Company Accountant separately decides mixed-funded Loss per case. Preserve approved Vehicle+Accounting ON, Investment OFF Buyer-refund exception. Never infer a split or treat an obligation as cash already paid.

Expose authenticated same-Company Accountant recovery/refund review and confirmation through existing API/UI patterns. Replace unconditional Profit-payment gate only after locked checks of collection, recovered principal/Company capital, refund state, confirmed result, retained payments/offsets, permissions and module state. Preserve partial Profit payment and its single typed Accounting movement.

**Done when:** Investor-only partial and mixed full recovery, correction, reserve, actual partial refund, redeployed credit, replay and concurrent writers cannot overstate Fund or duplicate cash; existing successful Profit-payment test works without weakening; blocked cases stay blocked. Run focused PostgreSQL service/API/guard/concurrency and affected React tests once this workflow is integrated.

## E — Investor obligations, Exit and adjustments

Reuse period snapshots, paid deal/interim events, Loss offsets and Exit history. Add authoritative confirmed payable/recoverable positions with correction/version history; count each actual payment, offset and recovery once. An open recovery is not received cash. Preserve Sale-date period attribution.

Company Accountant settles across all Company Branches from a current locked, version-checked position: principal first; confirmed residual Loss through Available Fund or direct Investor Receipt **without Company Income**; remaining Profit. Support approved partial movements, audited closure, pre-OFF Exit continuation while Accounting ON and explicit post-Exit repayment/refund/waiver adjustments. One cash event creates one typed Accounting movement. Do not auto-net categories or invent waiver authority/caps.

**Done when:** two-Branch and cross-Company cases, insufficient Fund, partial direct receipt, remaining Profit, open obligations, pre-OFF, post-Exit correction, stale request, retry and concurrent writers have focused PostgreSQL/API checks; UI shows confirmed current and historical positions.

## O — Company period and Owner distribution

Use Accounting sources and existing carryforward helper; Accounting Result alone is not distributable confirmation. Persist non-overlapping Company periods, reviewed liabilities, Accountant-confirmed distributable amount and negative carryforward with source/version and correction history. A later positive period covers carryforward first. Do not invent the Accountant's liability judgment formula.

Use protected effective Owner recipient/percentage configuration, exact 100% validation and immutable snapshot at confirmation. Reuse `allocate_owner_distribution` for paise-exact allocations. Persist Owner allocations and actual partial payouts through one typed Accounting movement each. Company Owner is read-only. Wire `CompanyResultView.tsx` and replace relevant `Phase8ReadinessView.tsx` placeholders with actual review, history and payout states.

**Done when:** negative-to-positive periods, overlap/late corrections, config changes, exact rounding, partial cap, stale source, cross-Company/role denial, retry and concurrency pass focused PostgreSQL/API and affected React checks; payouts cannot exceed confirmed allocations.

## Acceptance and documentation — once

At each workflow boundary, run only focused checks for changed financial logic, guards, auth and UI. After R, E and O pass, run **one** consolidated disposable-PostgreSQL migration/schema and related financial/security regression, React test/lint/build and authenticated browser pass with reload and relevant responsive widths. Verify DB identity and that tests were actually discovered. Run a bounded final audit of cash uniqueness, Fund/reserve, tenant access, corrections, migration compatibility and old flows. Investigate failures; do not repeat broad suites after micro-edits. Update affected living docs **once at Phase 8 close**, based on verified truth. Phase 9/10 are separate downstream work.

## Business decision and immediate handoff

**BUSINESS DECISION REQUIRED:** Company-only Purchase later funded by Investor Expense lacks an authoritative historical Investor agreement snapshot; prior Company Share recognition may need correction. Current confirmation fails closed. Do not choose a later rate or rewrite historical Income without an approved rule. This blocks that case, not independent R/E/O work. Identify any other missing authority precisely and continue independent work.

**Next action:** verify current recovery migration/model/refund test consistency and disposable DB identity, then finish **R** end to end. Keep Profit-payment gate until recovery, refund reserve and concurrency checks establish eligibility.
