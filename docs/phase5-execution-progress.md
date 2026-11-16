# Phase 5 implementation and verification report

**Original implementation snapshot:** 2026-11-07, local isolated worktree (historical)<br>
**Current architecture readiness:** `READY_FOR_IMPLEMENTATION`<br>
**Current implementation status (verified 2026-11-16):** `PHASE_5_IMPLEMENTED_AND_VERIFIED_LOCALLY`<br>
**Approved Phase 5 core scope complete:** Yes, locally<br>
**Staging/production/deployment:** `UNVERIFIED`

> The initial implementation/API/UI/migration sections below record the 2026-11-07 partial snapshot. Subsequent dated sections record approved decisions. The 2026-11-16 audit-candidate checkpoint at the end supersedes earlier partial/not-started status statements and the 2026-11-15 test counts; historical observations are retained rather than rewritten.

## Repository and Git boundary

- Repository/worktree: `D:/VIRMS/tmp/phase5-investment-foundation-20261107`
- Branch: `codex/phase5-investment-foundation`
- Base commit: `50fb67c1c2256f6a164344344c8c2a12e04407f8` (approved local Phase 4 checkpoint)
- At the earlier implementation snapshot, Phase 5 changes were uncommitted. They are now locally committed for audit review on this branch; no remote push, merge, or deployment occurred.
- Existing dirty V2 decision additions in `docs-final-v2/` were present before this implementation work and were preserved.
- The `virms-local-8002-pgdata` database was not accessed. All database checks used the task-created PostgreSQL 15 container with `Mounts=[]` and `/var/lib/postgresql/data` on tmpfs; that disposable container was removed after validation.
- Staging/production database, runtime grants, deployment, hosted CI, and hosted API behavior remain `UNVERIFIED`.

## Implemented backend slices

### Investment (`apps/investment`)

- Company-scoped Investor UUID profiles and append-only, effective-dated Interim amount configuration.
- Immutable, Branch-attributed Investor Fund credits and principal returns.
- Fund summary derived from source credit and return-allocation records; Branch Accountants receive only their authorized Branch scope, while Company Accountants may access permitted Company-wide records.
- Principal return uses FIFO against the selected source Branch's unreturned credit lots. It cannot overdraw those lots.
- Fund credit/return requires Investment and Accounting modules enabled and creates one typed Accounting source link, one capital event, and one Cash/Bank movement in one transaction.
- Idempotency keys, Company/action/Branch checks, actor audit, database history guards, and UUID identities are enforced.
- No Investor Profit, loss offset, interim payment, reconciliation, or Exit settlement engine was added.

### Vehicle Management (`apps/vehicles`)

- Company-wide Vehicle UUID identity with same-Company current Branch.
- Registration normalization and active-only Company uniqueness are enforced by database constraints/triggers as well as API validation.
- Company Accountant may move a Vehicle between Branches through an atomic current-Branch update plus immutable movement record. Branch selection is not authorization.
- Vehicle create/read/update and Branch-movement APIs use idempotency, module gates, scoped policy, and audit history.
- Vehicle deactivation is unavailable; a Sold state and open Garage/Sales/finance dependencies cannot yet be verified.
- No Vehicle purchase, Investor responsibility linkage, Fund-use allocation, or Vehicle-linked Running Capital allocation was added.

### Accounting source linkage

- Accounting remains the owner of actual Cash/Bank events and `AccountMovement` rows.
- Capital inflow/outflow event types are distinct from Company Income, Expense, and Profit.
- `AccountingSourceLink` uses typed Investment source foreign keys. A successful Fund credit/return creates exactly one corresponding Accounting cash movement; failed writes roll back the source and cash records together.

### Shared mutation boundary

- Consequential Phase 5 writes acquire the actor/authentication guard and Company/Tenant lock, recheck immutable module-state revisions under that lock, then apply server-side Company/Branch/action policy and perform the transaction.
- A migration-order failure found during full regression was fixed in `apps/accounts/tests/test_scope_history_monotonic.py`: the historical `TransactionTestCase` now restores the full project migration graph on teardown, instead of leaving later tests with only Accounts/Tenants migrations. This changes test cleanup only, not production schema or authorization behavior.

## Current API surface

All endpoints are session-authenticated and Company-scoped under `/api/v1/tenants/{company_id}/`.

| Resource | Methods and path | Scope |
|---|---|---|
| Investor profiles | `GET, POST /investment/investors/`; `GET, PATCH /investment/investors/{investor_id}/` | Company identity; mutations require idempotency and Investment enabled |
| Interim configuration | `GET, POST /investment/investors/{investor_id}/interim-configurations/` | Append-only; Company-level Accountant manages the approved amount |
| Fund credit | `GET, POST /investment/fund/credits/` | Actual capital inflow; requires Branch, Cash/Bank account, amount, reference, timestamp; Investment + Accounting enabled |
| Fund summary | `GET /investment/fund/summary/` | Derived from credit and return records; Branch scope is enforced server-side |
| Principal return | `GET, POST /investment/fund/principal-returns/` | Actual capital outflow; limited to returnable source-Branch credit; Investment + Accounting enabled |
| Vehicle identity | `GET, POST /vehicle-management/vehicles/`; `GET, PATCH /vehicle-management/vehicles/{vehicle_id}/` | Vehicle Management enabled; Company and Branch scope enforced |
| Branch movement | `POST /vehicle-management/vehicles/{vehicle_id}/branch-movements/` | Company-level Accountant; append-only movement history |

No purchase, deactivation, Vehicle Profit, Loss, or settlement endpoint is exposed.

## React and data-flow status

No React source, route, navigation, layout, form, or visual UI was changed. Repository inspection found no Phase 5 Investment or Vehicle API consumer in `demo/react/src/api` or its components. Vehicle, Investor, and Fund pages still use the existing prototype data.

The current Vehicle form combines registration/model with a mock Garage, person/customer or Investor, classification, and purchase amount. The new API requires an actual server Branch UUID and gives Investor responsibility and purchase separate domain actions. The Fund-credit form also lacks the required Accounting Cash/Bank account and required reference. Silently dropping or guessing those values would corrupt identity or financial meaning; integrating these forms is therefore blocked until the approved UI contract can supply the required identities and fields. This requires no UI redesign as a goal, but cannot be completed by an API-only mapping with the current inputs.

The transitional backend and canonical prototype dataset are not yet unified at React runtime. No automatic mock import or demo seeding was added. End-to-end reload persistence through the browser is not claimed because React does not yet call these APIs.

## Migrations and database verification

- Fresh Django test databases applied the current migration graph successfully, including `investment.0001_initial`, `investment.0002_integrity_guards`, `accounting.0004_accountingsourcelink_and_more`, `accounting.0005_accountingsourcelink_investor_fund_credit_and_more`, and `vehicles.0001_initial`.
- On a separate empty database in the disposable PostgreSQL 15 tmpfs container, all migrations applied; `migrate investment zero` safely reversed the dependent Investment/Accounting source-link migrations; all migrations then reapplied. `migrate vehicles zero` and full reapply also passed.
- `showmigrations` showed all current migrations applied on the verification database. `migrate --check` found no pending migrations.
- `makemigrations --check --dry-run` reported no model/migration drift.
- Only empty-schema rollback/reapply was exercised. No rollback was attempted with Phase 5 financial or Vehicle history. Migration guards are present to refuse destructive reversal when protected source history exists; populated-history refusal for the new Phase 5 migrations is not independently demonstrated in this run.
- The observed Django phase-related apply sequence followed the dependency graph: Investment `0001/0002`, Accounting `0001`–`0005`, then Vehicle `0001`. The numbered architecture migration sequence is a dependency plan, not a guarantee of runtime application order.

## Tests and checks actually run

| Check | Result | Limits |
|---|---|---|
| `python manage.py test apps --verbosity 1` after the final test-harness fix | **311 tests passed** on disposable PostgreSQL; `System check identified no issues` | Does not prove React integration, browser reload persistence, staging, or production |
| Migration-sensitive Accounts/Accounting + Phase 5 concurrency batch | **31 tests passed** | Local disposable PostgreSQL only |
| Investment + Vehicle API suites and new concurrency test | **15 tests passed** | API/model/service scope covered; not a browser workflow |
| New principal-return concurrency test alone | **Passed** | Two Branch Accountants concurrently requested ₹40,000 returns against one ₹50,000 source credit; one request succeeded, one conflicted, one return/allocation and one capital outflow/movement were recorded |
| `python manage.py check` | **Passed** | Local configured environment |
| `python manage.py makemigrations --check --dry-run` | **Passed; no changes detected** | Model/migration state only |
| `python manage.py migrate --check` and `showmigrations` | **Passed; no pending migrations** | Disposable PostgreSQL only |
| Fresh apply + empty reverse/reapply | **Passed** | No populated Phase 5 rollback attempted |
| `python -m compileall -q apps/accounting apps/accounts apps/common apps/investment apps/vehicles` | **Passed** | Syntax compilation only |
| Phase 5 architecture JSON parse (`python -m json.tool`) | **Passed** | JSON syntax only |
| React `npm test` | **121 passed, 1 failed, 122 total** | Failure: `AppShellNavigation.test.tsx` expects flyout `maxHeight`/scroll style, but current inline `maxHeight` is empty. React source was unchanged in this Phase 5 worktree; UI was not altered to force this unrelated test green. |
| React `npm run lint` | **Passed** | Configured lint scope |
| React `npm run build` | **Passed** | TypeScript + Vite; Vite reports existing 611.49 kB main chunk advisory |
| `git diff --check` on scoped backend paths | **Passed** | Earlier dirty V2 Markdown additions have their own whitespace/line-ending warnings; they were not rewritten |

No human-like browser E2E was run for the Phase 5 APIs because the React application has no consumer for them yet. Existing Phase 1–4 browser behavior was not represented as newly re-tested by this report.

## Audit findings and remaining blockers

1. **BUSINESS DECISION REQUIRED — Q39:** seller payment timing for Vehicle purchase is unanswered. Do not create Vehicle purchase, purchase cash outflow, Fund-use allocation, or purchase-linked Running Capital until answered.
2. **DEPENDENCY BLOCKER — Vehicle deactivation:** authoritative Sold state and absence of open Garage Job, Sale, finance, or settlement do not exist in this slice. Keep the endpoint absent and registration active-only uniqueness enforced.
3. **INTEGRATION BLOCKER — current React forms:** missing Branch/Cash-account identities and combined domain fields cannot be safely mapped to the current APIs. React remains prototype-backed; browser persistence is not proven.
4. **SCOPE REMAINS:** automatic import, Investor Profit, Loss offset, Interim payment/reconciliation, and full Exit settlement remain unimplemented or outside Phase 5. Existing approved decisions must be used; no formula or policy was invented.
5. **REGRESSION FINDING — React sidebar flyout:** one UI test still fails on the flyout scroll/max-height contract. This is outside the Phase 5 backend slice and remains visible rather than being hidden or changed here.
6. **DEPLOYMENT EVIDENCE:** persistent 8002, staging/production schema, runtime DB role grants, hosted API, deployment, and hosted CI remain UNVERIFIED.

## Current result

Verified backend foundations are implemented locally, but purchase/funding, safe deactivation, and React data integration are not complete. The Phase 5 architecture gate remains blocked and Phase 5 must not be marked complete. No Phase 5 commit or push was made.

## Business decision update — 2026-11-08

The earlier Q39 finding is historical. The Company approved purchase before full seller payment, including ₹0 advance; the full unpaid amount is seller payable, actual partial payments reduce it, and the purchase view warns when no seller advance has been paid. An existing pre-OFF purchase payable may receive installments while Investment or Vehicle Management is OFF if Accounting remains ON; new purchase/Fund-use is still denied. These decisions are appended to the current V2 documents.

Seller name is required on the Vehicle Purchase; seller phone is optional. The same decision is recorded in the current V2 workflow, data relationship, business-rule, and Accounting documents.

Seller installment actor scope is now recorded: Branch Accountant may pay only an authorized purchase Branch; Company-level Accountant may pay any Branch in the same Company.

Lender finance and EMI are explicitly excluded from Phase 5. The approved purchase flow covers seller payable and actual partial seller payments only; no lender loan, EMI, interest/fee, or finance-tag model is in scope. This decision is recorded in the canonical V2 Vehicle/Investor finance workflow and referenced in the Phase 5 architecture.

Q44 is resolved: record the full approved Investor Fund and Company Running Capital allocations when Vehicle Purchase is created, even if seller cash paid is ₹0; the Investor allocation is immediately committed/locked. Seller payable is only the unpaid purchase amount, and Accounting Cash/Bank moves only when an actual seller installment is paid. The decision is appended to the canonical V2 relationship, workflow, and Accounting documents and referenced in the Phase 5 architecture.

Q45 is resolved: if a purchase-cost correction would reduce cost below cumulative actual seller installments, require the seller's actual excess refund to be recorded in Accounting before accepting the correction. Keep the original purchase, installment, and cash-movement history immutable. The decision is appended to canonical V2 documents and referenced in the Phase 5 architecture; typed refund linkage and correction/reallocation contracts remain technical blockers.

Q46 is resolved: reduce Investor Fund and Company Running Capital allocations in the same proportion as the recorded purchase funding split; preserve immutable source history and existing Fund-credit FIFO attribution. The deterministic paise-rounding rule remains unresolved and blocks correction implementation.

Q47-Q48 are resolved: add one Company-wide Automation Approval setting in Settings, initially ON. ON requires approval for each consequential automated action; OFF permits already-approved automations to run under existing permissions. Pure calculations/read-only projections remain automatic. For calculation-based or materially consequential actions, add a compact Details/Note control beside Approve that opens a responsive, business-readable calculation/source summary. Toggle authority and treatment of pending items when the setting changes remain unresolved.

Q49 is resolved: only the same-Company Company-level Accountant may change the Company-wide automation setting; Branch Accountants, Owners, and Platform Back Office may not. The canonical roles document and architecture references record the boundary. Pending-item behavior when the mode changes remains open.

Q50 is resolved: turning approval mode OFF affects only future automated actions. Existing pending actions remain pending until separately approved or cancelled through their owning workflow; the toggle never bulk-executes or discards them. The rule is appended to the global and affected workflow documents.

Q51 is resolved: proportional source corrections use high-precision calculations, `ROUND_HALF_UP`, and balanced-paise reconciliation; ties use Investor Fund first, then Company Running Capital. The exact calculation is recorded in canonical V2 documents and the Phase 5 architecture.

Q52 is resolved: while Company-wide mode is OFF, only a workflow separately approved for automatic execution may skip per-action confirmation. All normal permissions, Company/Branch/module checks, source evidence, validation, atomicity, idempotency and audit remain; the toggle alone never authorizes a financial action. This narrowly supersedes Level 4 per-action confirmation for those approved automations only.

Q53 is resolved: an authorized Accountant manually records the actual seller refund and separately records the related Vehicle Purchase cost correction; both must link to the same Purchase. Neither record is generated automatically, and original installments/Cash/Bank movements remain unchanged. This decision is appended to the canonical workflow, data-relationship and Accounting documents and referenced in the architecture maps and Phase 5 architecture. Typed refund/correction models, endpoint contracts, payable derivation, validation/transaction order and idempotency remain technical blockers; no application behavior was implemented or re-tested by this documentation update.

This update is documentation only. No Purchase/payable/payment application, migration, API, or React integration was implemented or re-tested. The Phase 5 code architecture remains blocked pending the technical contract and the other dependencies described above. The 2026-11-07 test results are prior evidence, not a fresh run for this decision.

## Later scope decision — minimal Sale for safe Vehicle deactivation

The user selected the smallest real Sale capability and related authoritative checks needed for safe deactivation in Phase 5. The rest of the Sales, Collection and Refund workflows must be explicitly inventoried as later work, with a simple extensible API/service path. Confirmed Sale is the Sold source; unimplemented obligation providers are UNKNOWN, not proof of no outstanding obligations. See `architecture/phase-05-investment-vehicle-running-capital/PHASE-05-INVESTMENT-VEHICLE-RUNNING-CAPITAL-ARCHITECTURE.md` for the scope checkpoint and remaining architecture gates. This is a scope decision, not a claim that any Sale/deactivation backend exists or that Phase 5 is ready.

## Approved Fund Credit form inputs — 2026-11-09

The user approved adding Cash/Bank account selection and a required source reference to the existing Fund Credit form. The current API already requires `account_id` and `reference` and atomically records the actual capital inflow in Accounting, so this resolves the input-mapping decision only. The UI change and real-data React integration remain unimplemented. No application code, schema, API, or database was changed by this documentation update.

## Approved Sale-date input — 2026-11-09

The user approved one date field in the existing Sale form for the actual date the Vehicle was sold. It may be a past date when the Sale is recorded later; the effective Sale date must not be replaced with the server entry timestamp. This resolves the business date input for the minimal Sale capability only. Sale-date UI/API code and historical-period Profit behavior remain unimplemented.

## Phase 5 online/offline boundary — 2026-11-09

The user confirmed Phase 5 writes use the online cloud/backend API. Offline financial entry, a durable local write queue and synchronization are separate future system-wide work. Existing online permissions are unchanged; this does not impose an always-read-only rule on all users during outages. No offline/sync code was added.

## Approved minimum Sale/Buyer Receipt scope — 2026-11-09

The user selected the recommended minimal Sale/deactivation slice: confirmed Sale plus actual Buyer Receipts linked to Accounting, using the existing Buyer, price, collection-cap and Sale-date rules. Full Sale correction/refund and broader Sales workflows remain later work. A Sale with an open receivable or correction/refund obligation cannot be deactivated. The checkout still lacks authoritative Garage Job and Investor settlement applications; these remain blockers to enabling deactivation and must not be treated as clear merely because no API exists.

## Approved Investor-settlement deactivation boundary — 2026-11-09

The user confirmed Investor-funded Vehicles remain active until Investor settlement is complete. Investor Profit/settlement remains Phase 8; Phase 5 must not add a partial settlement workflow. The current checkout has no authoritative settlement source, so the deactivation guard must report UNKNOWN and block for these Vehicles until Phase 8 supplies it.

## Approved Q60 — Garage Job dependency remains outside Phase 5 — 2026-11-09

The user chose to implement only the approved minimal Sale/Buyer Receipt slice in Phase 5 and defer Garage Job backend work to its planned phase. This narrows the earlier Phase 5 scope expansion request; it does not relax the safety requirement. Vehicle deactivation and registration reuse must remain disabled until the Garage phase provides an authoritative, complete open-Job check. Missing Garage data is UNKNOWN, never CLEAR. Keep the existing database/model guard. Investor-funded Vehicles separately remain ineligible until Phase 8 provides authoritative completed settlement. This is a documentation checkpoint only; no backend, API, schema, React UI, or migration changed.

## Approved Q61 — Buyer Receipt account selector — 2026-11-09

The user approved adding a compact named Cash/Bank account selector to the existing Collection form. Repository evidence: the form currently has a payment-method label but no account UUID; the Accounting Receipt serializer requires `account_id`. The selector must use active, authorized same-Company account options and the server must revalidate scope. This approval covers only the account selector. The Buyer Receipt still needs its own typed Sale link and one Accounting movement; it must not post Company Income or use the generic Income-target receipt command. The Sale Receipt `source_reference` mapping remains a technical contract; the Garage-specific external-reference rule is not extended by assumption. Documentation only; no React/API/schema changes were made.

## Approved Q62 — required Buyer Receipt external reference — 2026-11-09

The user approved a required operator-supplied bank transaction ID or Cash voucher number for every actual Stock Vehicle Buyer Receipt. Add this field to the existing Collection form and map it to the typed Sale Receipt source and Accounting `source_reference`; preserve UUID plus the Sale FK as identity and one actual Accounting cash movement. This supersedes only Q61's unresolved reference-field question; Q61's account-selector approval is unchanged. Duplicate-reference uniqueness/scope remains undecided and must not be borrowed from the Garage-specific rule. Documentation only; no app code, API, schema, React UI, or migration changed.

## Approved Q63 — Buyer Receipt reference uniqueness — 2026-11-09

The user chose to reject a duplicate Stock Vehicle Buyer Receipt reference when the same Company and Cash/Bank account already have that reference, across Branches. The same text may be used with another account. This supersedes only Q62's unresolved uniqueness scope. Exact case/whitespace normalization remains open. Documentation only; no code, API, schema, UI or migration changed.

## Approved Q64 — Buyer Receipt reference normalization — 2026-11-09

The user chose to trim leading/trailing whitespace and compare Buyer Receipt references without case sensitivity. `BANK-37`, `bank-37`, and ` BANK-37 ` therefore match for uniqueness within the same Company and Cash/Bank account across Branches; the same normalized value may be used on a different account. This supersedes only Q63's normalization blocker. Documentation only; no code or migration changed.

## Approved Q65 — Fund Credit reference uniqueness — 2026-11-09

The user chose to reject repeated Investor Fund Credit references in the same Company and same Cash/Bank account across Branches, trimming outer whitespace and ignoring case; the same reference may be used on another account. Repository evidence: `InvestorFundCredit` has no account FK or uniqueness constraint; the account is available only through its linked Accounting movement. The architecture must define how the database enforces this scope without divergent account fields. Whether one real transfer may fund multiple Investor credits remains unresolved. Documentation only; no code/schema/UI change.

## Approved Q66 — one actual transfer per Investor Fund Credit — 2026-11-09

The user chose that one actual Cash/Bank transfer may create a Fund Credit for one Investor only; one transfer must not be split across multiple Investors. Separate actual transfers may create separate Fund Credits, including multiple credits for the same Investor. This supersedes only Q65's unresolved transfer-allocation question. Preserve one Fund Credit + one Accounting capital inflow + one AccountMovement per transfer, Branch provenance and the approved normalized Company/account/reference uniqueness. Documentation only; no application code, API, schema, UI or migration changed.

## Approved Q67 — Fund Credit actual receipt date — 2026-11-09

The user chose to use the date money was actually received as the Fund Credit effective date. Late entry may use that past date; a future effective date is prohibited. The linked Accounting capital-inflow movement uses the same effective date, while the system creation/audit timestamp remains the actual entry time. Repository evidence: `apps/investment/services.py` accepts past aware timestamps and rejects future Fund Credit timestamps. Timezone and time-of-day representation remain technical API-contract details. Documentation only; no application code, API, schema, UI or migration changed.

## Approved Q68 — correct Fund Credit assigned to the wrong Investor — 2026-11-09

The user chose to preserve the original Fund Credit and append an audited correction moving its amount from the wrong Investor to the correct Investor when the actual transfer itself is valid. The real Cash/Bank movement remains recorded once; no duplicate receipt or movement is created. Repository evidence: `InvestorFundCredit` rejects updates/deletes, and the current AccountingSourceLink has a one-to-one link from the AccountingEvent to the Fund Credit. A typed append-only correction record is required; correction authority, partial corrections and effective-date treatment remain BUSINESS DECISION REQUIRED. No code/schema/API/UI changes were made.

## Approved Q69 — Fund Credit correction authority — 2026-11-10

The user chose: Branch Accountant may correct a Fund Credit only within their authorized source Branch; Company-level Accountant may correct a Fund Credit in any Branch of the same Company. This authority applies only to wrong-Investor attribution correction and does not create a generic cross-Branch permission. Owner and Platform Back Office gain no new rights. Partial-correction scope and correction effective-date treatment remain open. Documentation only; no application code/schema/API/UI changes.

## Approved Q70 — full-credit wrong-Investor correction — 2026-11-10

The user chose to move the full original Fund Credit amount to the correct Investor; a correction may not split one transfer/credit across Investors. This supersedes only Q68/Q69's open partial-correction question and follows Q66. Preserve the original credit, one actual Cash/Bank movement, Branch provenance and Q69 role scope. The correction effective date remains unresolved. Documentation only; no code/schema/API/UI changes.

## Approved Q71 — correction effective date — 2026-11-10

The user chose the original Fund Credit's actual money-received date as the effective date of a wrong-Investor attribution correction. Recalculate affected historical Investor calculations with audit history and preserve the earlier versions. The original Cash/Bank movement does not change. Treatment of already-paid or settled amounts remains a separate BUSINESS DECISION REQUIRED item. Documentation only; no code/schema/API/UI changes.

## Approved Q72 — restatement difference after prior Investor Profit payment — 2026-11-10

The user chose to preserve the prior Investor calculation and actual payment, record the restatement difference as a separate audited adjustment, add any underpayment to a later Investor Profit amount, and deduct any overpayment from a later Investor Profit amount. No previous Cash/Bank movement changes; any later actual payout is separate. Treatment when future Profit is unavailable or Exit occurs before an overpayment is offset remains unresolved. Documentation only; no application code/schema/API/UI changes.

## Approved Q73 — flexible Exit outcome for restatement overpayment — 2026-11-10

The user chose to allow either collection of the unoffset historical Investor Profit overpayment before Exit closure or completion of Exit without collection, according to the case. This applies only to the restatement adjustment, not normal Vehicle Loss or principal Exit rules. No automatic Fund debit or cash event; actual repayment must be separately recorded. Who selects the outcome and whether an unpaid balance is waived or remains recoverable after Exit remain unresolved. Documentation only; no code/schema/API/UI changes.

## Approved Q74 — disposition of unpaid overpayment after Exit — 2026-11-10

The user chose case-by-case handling after Exit without collection: retain the amount as an open balance for later collection, or waive it with a recorded reason. This only concerns historical Investor Profit restatement overpayment. It does not create cash or Company Income/Expense. The role allowed to select/approve the disposition remains unresolved. Documentation only; no application code/schema/API/UI changes.

## Approved Q75 — role authority for post-Exit overpayment disposition — 2026-11-10

The user chose: Branch Accountant may select open/waived disposition only for an adjustment from their authorized Branch; Company-level Accountant may select for any Branch in the same Company. A Branch Accountant cannot finalize an Exit spanning Branches. This is specific to the restatement overpayment and grants no general cross-Branch access. Documentation only; no application code/schema/API/UI changes.

## Approved Q76 — actual repayment permission after Exit — 2026-11-10

The user chose: Branch Accountant may record actual repayment against an open post-Exit adjustment only for its authorized source Branch; Company-level Accountant may record for any Branch in the same Company. Record actual cash movement only on receipt. Exact Accounting event classification and typed source link remain to be locked. Documentation only; no application code/schema/API/UI changes.

## Approved Q77 — post-Exit overpayment repayment classification — 2026-11-10

The user chose: record money actually received against an open post-Exit historical Investor Profit overpayment as a Cash/Bank Receipt linked to that adjustment; reduce the open amount by the amount received; do not create Company Income/Profit. This resolves the business classification only. Typed source-link/model/API/transaction details remain architecture work. Documentation only; no application code/schema/API/UI changes.

## Approved Q78 — partial and multiple post-Exit repayments — 2026-11-10

The user chose to allow partial and multiple actual repayments against one open post-Exit Investor Profit overpayment. Each amount actually received reduces the open balance; any remainder stays open. Handling of receipts above the remaining amount and the typed source-link/model/API/transaction contract remain unresolved. Documentation only; no application code/schema/API/UI changes.

## Approved Q79 — edit saved post-Exit repayment entry — 2026-11-10

The user chose to allow editing a saved repayment entry. Normal views show the latest value without displaying earlier values; the backend audit history retains the original and corrections, and a note may be added. Editing does not change the actual Cash/Bank Receipt or movement. Excess-receipt behavior and typed source-link/model/API/transaction design remain unresolved. Documentation only; no application code/schema/API/UI changes.

## Approved Q80 — excess post-Exit repayment disposition — 2026-11-10

The user chose a case-by-case disposition for repayment above the open overpayment: keep the excess open as an amount due back to the Investor, or record a separate actual refund after it is paid. Keep the full actual Receipt and do not create Company Income/Profit. The exact typed source-link/Accounting outflow/API/transaction design remains unresolved. Documentation only; no application code/schema/API/UI changes.

## Approved Q81 — partial and multiple excess refunds — 2026-11-10

The user chose to allow partial and multiple actual refunds of excess repayment kept due back to the Investor. Record every actual refund separately and reduce the due-back balance only by the amount paid; keep any remainder open. Documentation only; no application code/schema/API/UI changes.

## Approved Q82 — full Purchase/Sale amounts and installments — 2026-11-10

The user chose to record complete Purchase cost and agreed Sale price independently of payment timing. Seller payments, Buyer receipts and Purchase/Sale refunds may be partial/multiple actual events, never above the current outstanding balance; lower installments are valid and leave a remainder. Show a compact warning for the remainder. Reuse only for other modules with defined full source amounts, typed obligations and permissions. Documentation only; no application code/schema/API/UI changes.

## Approved Q124–Q132 — Vehicle Expense refund allocation and Phase 5 funding — 2026-11-11

- Q124/Q123: receive the actual Vendor refund in full once, apply only up to the Vehicle Expense's remaining net actual payments, and explicitly allocate all excess; block posting if there is no eligible destination. No automatic Company Income.
- Q130/Q132: if the Accountant classifies excess as Company Income, create a separate Income event with selected category and note, then apply the same actual Receipt to it. Do not mutate an existing Income event or create another cash movement. This records the excess as Company Profit once. Repository fact: a Receipt applied to an existing Income settles its balance and does not change the Income amount.
- Q125/Q127/Q131: only the same-Company Company-level Accountant may create and fully allocate Investor-linked Vehicle Expenses using pooled Fund; no Branch Accountant draft/reservation. Branch Accountants cannot create Investor-linked Vehicle Expense.
- Q126/Q128/Q129: Company-only Purchase/Expense uses Vehicle-linked Company Running Capital without pre-funding. A Branch Accountant may create Company-only costs only in an authorized Branch; a Company-level Accountant may act in any same-Company Branch. Company-only Purchase requires Vehicle Management + Accounting; Investment is not required. Investor-Fund Purchase requires all three modules.
- Additional automation/approval/posting flows are deferred until core workflows are ready. Existing approved automation decisions remain documented as future work. This is not a blocker for the essential Phase 5 flows.

## Approved Q133–Q134 — Fund Credit correction with prior use/return — 2026-11-11

The user approved recording the full audited wrong-Investor attribution correction even if the Fund Credit already has Vehicle use or principal-return history. Keep the original Fund-use/return records and real cash movements unchanged; the Accountant manually prepares/reviews affected Investor calculations. Do not automatically restate or post historical Profit, settlement, overpayment or cash adjustments in Phase 5. The correction continues to use the original money-received date and does not create another Accounting movement. This supersedes Q71's automatic recalculation only where the corrected credit has linked use/return history. Documentation decision recorded; source implementation and focused verification remain pending.

## Phase 5 architecture readiness checkpoint — 2026-11-11

The code-level target contract now records the previously approved Purchase, payable, correction, direct Vehicle Expense, Sale/Buyer receipt/refund, source-allocation, module-gate, concurrency, idempotency, typed-link, API error, and migration rules. The JSON architecture status is `READY_FOR_IMPLEMENTATION`; implementation is still `PHASE_5_IMPLEMENTATION_PARTIAL`. Vehicle deactivation remains deferred until Garage/financial status providers are authoritative. Demo/mock data import and additional automation are not required for the core slice.

This checkpoint records decisions and a target contract only. Application code was not changed by this documentation checkpoint; no API/UI/database behavior or tests are newly verified by this entry. Implementation, focused tests, fresh/replay PostgreSQL migrations, and disposable browser validation remain outstanding. `virms-local-8002-pgdata`, staging, and production remain untouched/unverified.

## Phase 5 implementation and local verification checkpoint — 2026-11-15

### Current result

The approved Phase 5 core scope is implemented and verified on the isolated local worktree `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`, HEAD `50fb67c1c2256f6a164344344c8c2a12e04407f8`. Phase 5 changes and prior dirty work remain uncommitted; no commit, push, merge, or deployment occurred. The user-provided Q133–Q134 answer is implemented: preserve prior Fund-use/principal-return rows and actual cash movements, flag manual review, and do not automatically restate historical Investor Profit/settlement or create cash adjustments.

The core implementation includes Company-scoped Investor profiles and Fund operations; Vehicle identity and Branch movement; Purchase, complete source allocation, seller payable and actual partial payments/refunds/corrections; direct Vehicle Expenses, source allocations, payable/installments/refunds/corrections; confirmed Vehicle Sale, Buyer receipts/refunds/price correction; typed same-Company Accounting links; exact Company Running Capital allocations; transactional module/permission checks and idempotency; and API-backed React Investor/Fund/Vehicle workspaces. No demo/mock records are imported. Phase 5 financial writes are online-only.

### Verification evidence

| Check | Result | Evidence boundary |
|---|---|---|
| `python manage.py test apps --verbosity 1` | **330 passed**; Django system check clean | Full Django suite on `codex_phase5_verify` in disposable PostgreSQL 15 (`codex-phase5-disposable`, host port 55439, no persistent mount) |
| `python manage.py test apps.vehicles.tests.test_concurrency --verbosity 2` | **2 passed** | Added after the full run: proves concurrent Purchase requests cannot over-allocate one Investor Fund, and a Vehicle Management OFF revision that wins the Company lock rejects a Purchase that observed the older enabled revision; source/use/extra cash rows remain absent |
| Fresh schema `python manage.py migrate --noinput` | **Passed** through `vehicles.0007_sale_date_wall_clock_guard` and all dependent migrations | Empty disposable database `codex_phase5_final` only |
| `python manage.py check` | **Passed** | Same explicit disposable PostgreSQL target |
| `python manage.py makemigrations --check --dry-run` | **Passed; no changes detected** | Model/migration state only |
| `python manage.py migrate --check` | **Passed** before and after replay | No pending migrations |
| Reverse/reapply `investment.0007_fund_credit_attribution_correction` | **Passed** | Empty disposable schema; no populated-history rollback attempted |
| React `npm test -- --run` | **132 passed across 22 files** | Includes Phase 5 API contracts, role navigation, workspace states and no false-success behavior |
| `npm run lint` | **Passed** | Project-configured lint scope; build also type-checks the React application |
| `npm run build` | **Passed** | TypeScript + Vite; main bundle is 614.10 kB and triggers the existing >500 kB advisory |
| Local browser persistence workflow | **Passed** | In the disposable local app, created Investor records and Fund Credit, corrected attribution, reloaded, and observed correct Investor plus correction history. This is a local workflow, not a hosted-runtime check. |
| `git diff --check` | **Passed on the Phase 5/status-document paths** | Full-tree check still reports trailing whitespace in the already-dirty canonical `docs-final-v2/` additions; this checkpoint did not edit those lines. |
| `virms-local-8002-pgdata` | **Not accessed** | Test databases lived in the disposable tmpfs-backed container only |

The container and local app were used only for verification; synthetic records do not represent production/customer information. Staging/production database state, deployed runtime grants, hosted API behavior, deployment, and backup/restore in hosted environments remain `UNVERIFIED`.

## Audit corrections in progress — 2026-11-15

The earlier local verification checkpoint does not establish verification of the current dirty worktree. The ongoing correction adds account-scoped normalized Fund Credit reference enforcement, traverses Investor list pages, and returns a scope-filtered Running Capital expense total across pages. It also repairs Company-only Purchase/Expense correction failures and implements Fund-first Investor-linked Expense allocation. Historical financial source rows and Cash/Bank events remain retained. The new `accounting.0012` migration rejects existing duplicate references instead of silently changing history; `vehicles.0009` preserves Investor attribution when the available Fund is zero.

On disposable PostgreSQL, the new migrations applied from a fresh schema and empty reverse/reapply was exercised; a preexisting synthetic Fund Credit was backfilled and guarded against unsafe reversal. Focused checks covered duplicate references, concurrent duplicate requests, expense totals over 21 rows including a correction, and Company-only Purchase correction. React checks covered Investor pagination, Fund-first form submission and the paginated total. Full current-tree backend regression and a real browser/API persistence workflow remain pending; hosted runtime, database migration and deployment remain unverified.

### Later verification and Branch selection — 2026-11-16

The prior full backend run completed 337 tests successfully on disposable PostgreSQL before the final Fund Credit key-validation trigger and Phase 5 Branch endpoint changes. Those later changes have focused PostgreSQL tests, including Company/Branch scope, foreign Company and unauthenticated requests, duplicate reference, and concurrent duplicate attempts. The current React suite ran 137 tests successfully and the configured lint scope passed without warnings; the production build passed with a 614.29 kB main-chunk advisory.

An isolated local browser session created an Investor and a Fund Credit and confirmed both after reload. Reusing the same reference with different case displayed an error and retained the form. The browser session exposed missing Company-wide Branch choices; the Phase 5 Branch API now supplies authorized choices, with the existing account-context Branch endpoint unchanged. These are local synthetic-data checks, not hosted-runtime verification. Full backend regression after the final endpoint/trigger changes, broader browser workflows, staging/production migration and deployment remain unverified.

After the final Branch endpoint and key validation changes, `python manage.py test apps.investment apps.vehicles apps.tenants --verbosity 1` passed all 73 tests on disposable PostgreSQL. This supplements the earlier full 337-test run; it does not claim that the entire suite was rerun after those final changes.

The isolated browser also registered a synthetic Vehicle, created a zero-advance Company-funded Purchase, reloaded, and showed the persisted Vehicle, seller, cost and payable. Seller payment, direct Expense, Sale and refund browser workflows have not been independently exercised in this check.

A later isolated browser check recorded a ₹2,000 seller installment against the ₹10,000 synthetic Purchase and showed ₹8,000 payable after reload. It also created a ₹500 Company-funded direct Vehicle Expense and showed it after reload. Sale and refund browser workflows remain unverified by this check.

A subsequent isolated browser check confirmed the synthetic Vehicle Sale at ₹15,000, recorded a ₹3,000 Buyer receipt, and showed ₹12,000 receivable after reload. Buyer and seller refund browser workflows remain unverified.

A later browser check recorded a ₹500 seller refund and verified the resulting ₹8,500 payable after reload. It corrected the synthetic Sale price to ₹2,000 and observed ₹1,000 Buyer refund payable, then submitted a ₹500 Buyer refund; the persisted refund row was verified in the disposable database. Browser verification of the Buyer refund after reload did not complete due to a navigation timeout.

The subsequent reload exposed a Sale refund parser mismatch: refund records lack the payment-only `reference` field. The client now parses typed refunds separately; the API regression, lint and build passed, and the same synthetic Sale displayed the remaining ₹500 Buyer refund payable after reload.

Final local React validation after the refund parser change: 137 tests across 22 files passed; lint passed with Phase 5 workspace included; TypeScript/Vite build passed with the existing main-chunk size advisory. Purchase, Expense and Sale refund responses are parsed according to their actual source shapes. These checks do not verify staging, production, hosted backups or real customer data.

## Phase 5 audit fixes and regression verification — 2026-11-16

The four issues recorded in `output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md` are fixed in the current local worktree: seller installments now respect the latest corrected Purchase cost and actual refund/payment totals; a Vehicle cannot receive Investor Fund from a different Investor across its Purchase/Expense records; increasing a pooled Fund allocation during Vehicle Expense correction requires Company-level Accountant authorization; and retries with omitted optional timestamps retain a stable idempotency request body.

Verification on the disposable PostgreSQL 15 container `virms-phase5-fix-1116`:

- `python manage.py test apps --verbosity 1`: 343 tests passed in 703.463 seconds. This full run preceded only a test-harness adjustment from `TestCase` to `TransactionTestCase`; the underlying implementation was unchanged by that adjustment.
- After that adjustment, `python manage.py test apps.vehicles.tests.test_purchase_api apps.vehicles.tests.test_expense_api apps.vehicles.tests.test_sale_api --verbosity 1`: 24 tests passed. The 10 Expense tests ran with actual transaction boundaries, including the decrease/deny/increase Fund correction sequence.
- Fresh `migrate --noinput`, `migrate --check`, `check`, and `makemigrations --check --dry-run` passed; no migration changes were introduced by these four fixes.
- React: 137 tests passed; configured lint and TypeScript/Vite build passed. The existing main-chunk size advisory remains.

The audit fixes do not change the approved schema, public request/response fields, module permissions outside the pooled-Fund increase check, or cash-event ownership. Existing dirty Phase 5 work remains uncommitted. The disposable tmpfs database was used; `virms-local-8002-pgdata`, staging and production were not accessed. No commit, push, merge or deploy occurred. See the audit report for the issue-by-issue evidence and remaining verification boundaries.

### Deferred scope and remaining limitations

- Vehicle deactivation/registration reuse remains unavailable until the Garage phase supplies authoritative open-Job state and Investor settlement state is available. Missing providers are UNKNOWN, never CLEAR. This is a deliberately deferred dependency, not a blocker to the approved Phase 5 core scope.
- Investor Profit calculation/payment, historical Profit reconciliation workflow, full Exit settlement, Owner distribution, Garage Jobs, offline financial writes/sync, demo-data import, and additional automation are not part of this Phase 5 implementation.
- The Vite bundle-size advisory is informational. Staging/production/deployment readiness is not claimed.

## Phase 5 audit-candidate checkpoint — 2026-11-16

The approved Phase 5 core scope is locally committed on `codex/phase5-investment-foundation` and prepared for review toward `codex/audit`. No remote push occurred. The 2026-11-15 checkpoint above is superseded for current test counts by this audit run.

- Fixed and regression-tested the four findings in `output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md`: corrected Purchase payable cap; same-Investor attribution across each Vehicle's Purchase/Expense; Company-level authority for increases to pooled Fund allocations during expense correction; stable retry identity when optional timestamps are omitted.
- `python manage.py test apps --verbosity 1`: 343/343 passed on disposable PostgreSQL 15. After adjusting the Expense test class to use actual transaction boundaries, Purchase/Expense/Sale API suites passed 24/24; all 10 Expense API tests passed.
- Fresh disposable migration apply, `migrate --check`, `check`, and `makemigrations --check --dry-run` passed; no new migration was needed for the four fixes.
- React: 137/137 tests passed; configured lint and TypeScript/Vite build passed. The 614.29 kB main-chunk advisory remains.
- Phase 3 remains complete in its approved foundation scope. Phase 4's bounded Accounting Foundation is the local base commit `50fb67c1`; remote publication has not been reverified. Staging/production, deployment and hosted grants remain `UNVERIFIED`.
- Vehicle deactivation/registration reuse remains deferred until authoritative Garage and Investor-settlement state exists. Investor Profit/Exit settlement remains Phase 8; offline writes/sync and additional automation remain outside Phase 5.

## Phase 5 audit branch publication checkpoint — 2026-11-16

The Phase 5 candidate was pushed as a normal fast-forward to `origin/codex/audit`. GitHub commit comparison confirmed the remote ref at `2ddbbce26bf43a25313190bf7266996d43243476`. This history includes the Phase 4 base commit and Phase 5 implementation commit. Staging/production deployment was not performed. The separate local `codex/audit` worktree's 17 pre-existing dirty paths were left untouched.
