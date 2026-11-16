# Phase 5 — Blocker Resolution Draft

**Historical draft; latest state is superseded.** On 2026-11-11, Q124–Q132 and the code-level source/API/transaction/migration contracts were reconciled in the main Phase 5 architecture. Current state is `READY_FOR_IMPLEMENTATION`, while code remains `PHASE_5_IMPLEMENTATION_PARTIAL`. Use the main architecture and `docs/phase5-execution-progress.md` as the current decision record; this draft remains historical reference only.

## Reconciled decisions

- Q39 and the later seller-payable decisions have approved checkpoints: purchase may have zero upfront payment; seller payable is distinct from full funding allocation and actual cash; correction, refund, proportional sources, balanced paise and approval mode follow the canonical additions. Account preference is per Accountant and Company and only a successful seller payment updates it. No automatic demo import. Confirm each specific addition in `docs-final-v2/05-vehicle-investor-finance-workflow.md` and `01-business-rules.md`; never implement the historical conditional full-payment endpoint.
- The user subsequently included the smallest real Sale dependency and all authoritative checks required for safe Vehicle deactivation in Phase 5. Sale confirmation marks Sold; collection is a distinct status. User wants the remaining Sales/Collection/Refund functionality explicitly inventoried for later extension.
- Whole-system offline entry/sync is a separate cross-cutting requirement (`architecture/OFFLINE-SYNC-REQUIREMENT-AND-IMPACT.md`), not an implemented Phase 5 guarantee. Do not let a local queue become an unverified parallel financial authority.

## Verified current state

- `apps/vehicles/models.py`: `Vehicle` has Company, current Branch, registration and `is_active`, but no authoritative Sale or obligation sources. Active registration uniqueness is Company-scoped. Existing DB guards deny deactivation.
- `apps/investment` implements credit/return records; `AccountingSourceLink` in `apps/accounting/models.py` supports exactly one typed Fund-credit or principal-return source. Its existing trigger in `accounting.0005` checks event/source Company, Branch, amount, actor and event type. It cannot safely be reused unmodified as a Purchase installment/refund link.
- Accounting owns `AccountingEvent`, `AccountMovement`, `AccountingApplication`; existing Income/Expense Payment applications have their own target/type constraints. Seller payments/refunds must not masquerade as unrelated Expense Payment/Company Income or create a second cash movement.
- `SharedFormModal.tsx` uses mock defaults for Vehicle/Fund/Sale. The Sale form initializes vehicle, buyer and price but no Buyer phone; V2 requires Buyer phone. Existing Vehicle/Fund forms also omit real Branch/account/reference identities noted in `docs/phase5-execution-progress.md`. Do not invent IDs or silently discard fields.
- No authoritative Garage Job, Sales or Investor settlement apps were identified in this checkout. Existing records in a real database cannot be characterized from code alone. Database `virms-local-8002-pgdata`, staging and production were not accessed.

## Purchase, installment, refund and correction — proposed contract to resolve

**Ownership:** Vehicle owns Vehicle identity and Purchase fact; Investment owns credit lots and use allocations; Accounting owns Company Running Capital allocation history, actual seller cash events/movements and typed linkage. A typed Purchase payment/refund relation must support multiple payment and refund events for one Purchase while ensuring one Accounting event has one source. No free-form source reference is sufficient by itself.

**Acquisition:** In one transaction validate Company, original Branch, authorized Company Accountant, current module states, Vehicle and Investor/Fund availability; create one immutable purchase and complete approved Investor/Running Capital allocation totaling purchase cost. No allocation creates cash. FIFO and source boundaries follow approved V2. Prevent concurrent over-allocation and duplicate intent.

**Installment:** Explicitly select the actual authorized Cash/Bank account; Branch Accountant is limited to the original Purchase Branch, Company Accountant to the same Company. Accounting must create exactly one actual outgoing movement, typed to that Purchase installment, in the same transaction as the domain/source record and idempotency response. Lock and recalculate current payable before accepting a positive amount; reject excess. Existing pre-OFF payable exception and Accounting ON requirement follow the later V2 checkpoint.

**Refund:** Record the actual seller-returned money manually with one Accounting inflow and a typed link to the original Purchase and relevant refund context; no Company Income. A Branch Accountant may record it for an authorized Purchase Branch and a Company-level Accountant within the Company. Purchase cost correction remains Company-level Accountant only. The refund is a separate authorized command from correction. Verify precise refund cap and treatment of valid reversals before lock; no assumed supplier credit or automatic refund.

**Correction:** Manually append audited correction/reallocation; do not mutate original Purchase, installments or AccountMovement. Under locks, compute the accepted current position and verify actual net seller paid does not exceed corrected cost; actual prior refund must cover any required excess. Reduce funding allocations proportionally with the approved balanced-paise/Fund-first rule and reconcile exact amounts. Transaction, source reversal and FIFO lot release mechanics require design and concurrency proof; never insert balancing cash.

**Proposed resource boundary:** separate Purchase, Purchase installment, seller refund and Purchase correction commands/resources under Company scope. Exact URL names, request/response schema, request-idempotency ownership, typed FK layout, events, module-OFF checks and migration DAG are still OPEN; no endpoint is approved by this draft merely because it is named.

## Sale and safe Vehicle deactivation — fail-closed dependency design

- A Sale-owned authoritative record (Company/Branch/Vehicle, approved Buyer data, agreed price, confirmed state/history) is the Sold source. Sale confirmation is distinct from collection completion. Whether a minimal new Django app or existing approved owner provides it must be reconciled with V2 and later Sales delivery; do not add a second Vehicle identity or independently mutable Sold flag.
- Define narrow read contracts for: confirmed Sold; open Garage Jobs; open Sale/Buyer receivables and refunds; outstanding Vehicle-related finance; unresolved Investor/settlement obligations. Each returns **clear / open / unknown**, scoped to Company/Vehicle; unknown, unavailable, unimplemented or incomplete history blocks deactivation. A fabricated empty provider is forbidden.
- Deactivation service must check all providers and perform the active-state transition in one atomic protocol. All writers that could create or reopen an obligation need a shared Company/Vehicle lock order, including module-state and actor/scope checks. Existing DB deactivation denial must stay in place until its safe replacement and direct-write guards are designed and tested. Preserve prior registration and history; Company-scoped active-only uniqueness applies after successful deactivation.
- The missing authoritative Garage/Sales/settlement sources make this the primary current scope-expansion blocker. Defining only a check interface cannot establish the absence of real-world obligations. A minimum real provider must be specified and any historical-data completeness established before calling the feature functional. Later modules must extend the same sources rather than copy them.
- Inventory for later phases: full Garage work, Sales/Buyer collection/refund/corrections, Investor Profit/Loss/Exit and settlement. The exact minimum implemented subset and its handoff to those modules remain OPEN.

## Frontend compatibility and UI approval

Preserve working routes, roles, Company/Branch scope and layout. Feed selectors from server UUIDs, submit through typed services and invalidate affected queries only after backend success. Never present demo fallback as persisted real data; do not auto-import mock records or alter existing actual database data.

The mandatory V2 Buyer phone is absent from the current Sale form. **UI_CHANGE_APPROVED:** the user approved adding a small Buyer phone field to the existing Sale form. Map its entered value to the authoritative Sale/Buyer API contract, validate it server-side under the existing V2 rule, preserve entered input on validation errors, and never infer it from another identity or demo data. This approves that specific visible change only; the exact API schema and minimal Sale model are still open. The current Fund form likewise lacks account and reference; Vehicle form combines fields belonging to different domain actions. Produce a concrete per-field/UI mapping and obtain any necessary visible-change approval before implementing; do not guess values.

## Security, tests and remaining lock criteria

Each command rechecks Company/Branch membership, role, module revisions, source ownership and target account. Scope remembered payment-account preference to Accountant and Company; persist after successful payment only and validate on reuse. Actor/Company/idempotency semantics must match the implemented services; isolate the preference from financial truth.

Before `PHASE_5_CODE_ARCHITECTURE_READY_FOR_IMPLEMENTATION`: lock the exact typed schema and acyclic migrations after `accounting.0005`; precise request/response/errors, endpoint ownership, target caps and correction/refund semantics; provider completeness and cross-module locks; minimal real Sale and future compatibility; authorization and all module-OFF rules; frontend field mapping/approvals; regression and reversal-safe migration plans. Complete business questions before coding and label any unresolved rules `BUSINESS DECISION REQUIRED`.

Required verification when implementation is later authorized: fresh/replay and upgrade migrations on disposable PostgreSQL; preexisting Phase 1–4 regressions; two-actor competing Fund allocations, installments, corrections and obligation creation versus deactivation; same-key replay and changed-key behavior; failure injection proving zero partial financial writes; Company/Branch IDOR checks; pre-OFF obligations; UI error/no-false-success and reload persistence; current route/UI compatibility. No tests or runtime/database operations were performed for this draft.

## Approved input-scope update — Fund Credit form

On 2026-11-09, the user approved adding explicit Cash/Bank account selection and a required reference field to the existing Fund Credit form. This is limited to those controls; it does not authorize a broader React redesign. Repository evidence confirms the current `FundMovementCreateSerializer` already requires `account_id` and `reference`, and `create_fund_credit` already links that Fund credit to one typed Accounting capital inflow. Therefore this resolves the Fund Credit form-input mapping gap without proposing a new API field or duplicate cash event. The controls are not implemented yet. The separate Vehicle identity/purchase form mapping remains subject to its existing source/action contracts.

## Approved input-scope update — actual Sale date

On 2026-11-09, the user approved one Sale-date field in the existing Sale form and confirmed it may hold a past date when a Sale is entered later. The effective Sale date must remain distinct from server recording time. The existing form currently has no Sale date input. This approval does not authorize a broader Sale form redesign, Buyer collection or Profit implementation.

## Approved Phase 5 network boundary

On 2026-11-09, the user confirmed Phase 5 writes use the current online cloud/backend API. Offline financial entry and synchronization are a separate future system-wide phase, not part of Phase 5 implementation. This boundary does not alter existing online role permissions and does not make an unverified local cache authoritative.

## Approved Phase 5 minimum Sale/Buyer Receipt scope

On 2026-11-09, the user accepted the recommended minimum actual Buyer Receipt API as part of the Sale/deactivation slice. Phase 5 includes one authoritative confirmed Sale with Buyer name/required phone, agreed price and actual Sale date, plus linked actual Buyer Receipt events recorded once through Accounting. Multiple partial Receipts and over-receipt rejection follow the existing V2 Sale rules. Full Sales management, Sale price corrections, Buyer refunds, CRM and Investor Profit/settlement remain deferred and must be explicitly inventoried. A Sale with an outstanding receivable or unresolved correction/refund cannot pass the deactivation guard. Garage Job and Investor settlement source providers are still absent from this repository and remain architecture blockers; no provider may claim CLEAR without complete authoritative data.

## Approved settlement boundary for deactivation

On 2026-11-09, the user confirmed that an Investor-funded Vehicle stays active until its Investor settlement is completed. Phase 5 must not implement a partial Investor Profit or settlement workflow. Its deactivation guard must fail closed until an authoritative same-Company settlement source reports completion; because the current checkout has no such source, this condition is presently UNKNOWN and blocks deactivation. Phase 8 must provide the source before Investor-funded Vehicles become eligible.

## Approved Q60 — defer Garage Job backend; keep deactivation unavailable

On 2026-11-09, the user selected the minimal Phase 5 Sale/Buyer Receipt slice and chose to defer Garage Job backend work to the Garage phase. This supersedes only the earlier request to bring all deactivation dependency backends into Phase 5. It does not waive the V2 requirement to prove that no open Garage Job exists.

- Do not add a partial Garage Job model/provider in Phase 5.
- Do not expose Vehicle deactivation or registration reuse while the authoritative Garage Job provider is absent. An absent or incomplete provider is UNKNOWN and must block; it must never return CLEAR by default.
- Continue to enforce Sold, fully collected Sale, no outstanding finance/refund, and completed Investor settlement where applicable. The current checkout lacks Garage Job and Investor settlement sources, so deactivation remains blocked even after the minimal Sale/Buyer Receipt slice is implemented.
- Garage Job source ownership and the concurrency-safe obligation check must be completed with the Garage phase before deactivation can be enabled. Phase 8 remains the source for Investor settlement.

This records approved scope and sequencing only. The code architecture remains blocked on the other contracts in this draft; no implementation is authorized by this entry.

## Approved Q61 — Buyer Receipt account selector in the existing Collection form

On 2026-11-09, the user approved adding a compact Cash/Bank account selector to the existing Collection form. The current form records a payment method string, which is not a named account identity; the Accounting Receipt serializer requires an `account_id`.

- Load same-Company active account options under the existing account and Branch scope; submit the selected account UUID and validate it again on the server.
- Keep the existing form and route. This approves only the account selector, not a broader redesign or a new reference input.
- A Buyer Receipt must use a typed Sale Receipt source and create exactly one Accounting cash movement. Do not target an Accounting Income event or create Company Income for the vehicle Sale.
- The required `source_reference` mapping for a Stock Vehicle Buyer Receipt remains a technical contract to settle. The V2 operator-supplied external-reference rule is specific to Garage receipts and is not silently applied here.

This is UI-scope approval only. The typed endpoint, source record/link, `source_reference` strategy, transaction, constraints and migration order remain to be locked; no code or API behavior changed.

## Approved Q62 — required external reference for Buyer Receipt

On 2026-11-09, the user approved a required operator-entered external reference (bank transaction ID or Cash voucher number) for each actual Stock Vehicle Buyer Receipt. This supersedes only Q61's unresolved reference-field question; Q61's named-account selector remains approved.

- Add the required reference to the existing Collection form and map it to the typed Sale Receipt record and linked Accounting event `source_reference`.
- Keep UUID plus the typed Sale relationship as record identity; a free-text reference is not a source link or idempotency key.
- Preserve a single linked Accounting event/AccountMovement and never classify a Vehicle Sale receipt as Company Income.
- Reference uniqueness and its scope are still BUSINESS DECISION REQUIRED; do not silently apply the Garage receipt uniqueness rule to Vehicle Buyer Receipts.

The external-reference input is approved; exact Sale Receipt/source-link schema, duplicate handling, transaction, validation, migration and API contracts remain to be locked. No code or API behavior changed.

## Approved Q63 — Buyer Receipt reference uniqueness by Company and account

On 2026-11-09, the user chose to reject a duplicate external reference for a Stock Vehicle Buyer Receipt when it is already used in the same Company and same named Cash/Bank account, regardless of Branch. The same text is allowed for a different account. This supersedes only Q62's unresolved uniqueness scope.

- Enforce the uniqueness rule only for Stock Vehicle Buyer Receipts, not all Accounting events or Garage receipts.
- The source reference is traceability, not the Sale Receipt identity or idempotency key.
- Exact case/whitespace normalization remains to be decided/locked as part of the typed source schema and validation contract. Do not introduce a migration constraint until that comparison rule is explicit.

## Approved Q64 — trim and case-insensitively compare Buyer Receipt references

On 2026-11-09, the user chose to remove leading/trailing whitespace and ignore case for duplicate comparison (`BANK-37`, `bank-37`, and ` BANK-37 ` are equivalent). This supersedes only Q63's unresolved normalization statement; its Company + account uniqueness scope across Branches remains.

- Use a normalized comparison key on typed Stock Vehicle Buyer Receipt records only.
- Keep the same normalized reference allowed on a different account; do not widen the constraint to all Accounting references or Garage receipts.
- Exact DB implementation (normalized column or functional unique index) belongs in the locked schema design; application code and migrations remain unchanged.

## Approved Q65 — Fund Credit reference uniqueness by Company and account

On 2026-11-09, the user chose to reject duplicate Fund Credit external references within the same Company and same Cash/Bank account, across Branches. Match after trimming outer whitespace and ignoring case; allow the same text on another account.

- Repository-verified gap: `InvestorFundCredit` holds a required reference and Branch but no account FK or duplicate-reference constraint. Its AccountingSourceLink points to an AccountingEvent whose AccountMovement owns the actual account.
- Define a database-enforceable normalized uniqueness key tied to the linked movement's actual Company/account, with integrity protection against account mismatch. Do not add an independent mutable source of truth.
- Keep the current atomic one-credit/one-capital-inflow/one-movement semantics. Whether one actual transfer may fund multiple Investor credits remains BUSINESS DECISION REQUIRED; do not infer this from the duplicate rule.

## Approved Q66 — transfer-to-Investor allocation — 2026-11-09

One actual Cash/Bank transfer is for one Investor Fund Credit only; a transfer must not be split across Investors. Each Investor credited from separate money movements requires a separate actual transfer and Fund Credit. This supersedes only the Q65 unresolved transfer-allocation statement.

- Preserve one Fund Credit + one Accounting capital inflow + one AccountMovement per actual transfer, atomically.
- The Company/account/reference uniqueness rule, Branch provenance and separate transfers to the same Investor remain unchanged.
- No application code, schema, API or UI change is authorized by this documentation update.

## Approved Q67 — Fund Credit effective date — 2026-11-09

Use the actual money-received date as Fund Credit effective date; allow a past date for late recording and reject future dates. This resolves the previously unspecified date-entry policy.

- Keep Fund Credit, linked Accounting capital inflow and AccountMovement aligned on the same effective receipt date; preserve the actual creation/audit timestamp.
- Repository evidence: `apps/investment/services.py` already permits past aware timestamps and rejects future Fund Credit movement timestamps. No code change was made for this documentation update.
- Lock timezone and time-of-day representation in the API contract; those are technical details, not additional business rules.

## Approved Q68 — wrong-Investor Fund Credit correction — 2026-11-09

For a valid actual transfer assigned to the wrong Investor, preserve the original credit and audit history and append a correction that moves the Fund amount to the correct Investor. Keep the original real Cash/Bank movement exactly once; do not create another receipt or movement.

- The correction must not mutate the original Fund Credit or its Accounting source link. Use a typed append-only correction record.
- Preserve original Branch provenance and the one-transfer/one-Fund-Credit rule.
- Correction authority, partial corrections and effective-date treatment remain BUSINESS DECISION REQUIRED; do not implement those behaviors by inference.

## Approved Q69 — attribution-correction authority — 2026-11-10

Branch Accountant may correct only Fund Credits in their authorized source Branch; Company-level Accountant may correct any Fund Credit within the same Company.

- This permission applies only to the Investor attribution correction. It does not grant generic cross-Branch access to other modules or new rights to Owner/Platform Back Office.
- Validate the original Fund Credit's Company and Branch from server-side records. No code/schema/API permission changed in this documentation update.
- Partial-correction scope and correction effective-date treatment remain open decisions.

## Approved Q70 — whole-credit correction amount — 2026-11-10

The wrong-Investor attribution correction moves the full original Fund Credit amount; partial attribution splits are not allowed. This supersedes only the Q68/Q69 partial-correction uncertainty and follows Q66's one-transfer/one-Investor rule.

- Preserve original Fund Credit, audit, Branch provenance and the single actual Cash/Bank movement. Company-wide Fund does not increase or decrease from this correction.
- Enforce correction amount equality to the full original credit. Preserve Q69's role scope.
- Correction effective-date treatment remains open; no code/schema/API/UI changes were made.

## Approved Q71 — wrong-Investor correction effective date — 2026-11-10

Use the original Fund Credit's actual money-received date as the correction effective date. Recalculate affected historical Investor calculations and retain prior versions and audit history. The original cash event and movement are unchanged.

- Keep the correction's recorded timestamp separate from the effective date.
- Treatment of already-paid or settled amounts is not decided here and remains a separate business decision. No implementation change was made.

## Approved Q72 — restated Investor Profit and prior payment — 2026-11-10

Preserve the previous calculation and actual payment, and create a separate audited adjustment for the restatement difference. Add underpaid Profit to a later Investor Profit amount; deduct overpaid Profit from a later Investor Profit amount.

- The adjustment is not a Cash/Bank movement or Company Income/Expense. Any later payout is recorded as a separate actual payment.
- If future Investor Profit is unavailable or Exit occurs before an overpayment is offset, the remaining treatment is still a business decision. No code/schema/API/UI changed.

## Approved Q73 — flexible Exit for historical Profit overpayment — 2026-11-10

At Exit, permit a case-specific choice either to collect an unoffset historical Investor Profit overpayment before closing or to close Exit without collecting it.

- Applies only to overpayment after historical Investor Profit restatement; ordinary Vehicle Loss and principal Exit rules are unchanged.
- Do not create an automatic Fund debit or cash event. Any actual repayment remains an actual Accounting movement.
- Who chooses and whether the unpaid residual is waived or remains recoverable after Exit remain BUSINESS DECISION REQUIRED.

## Approved Q74 — post-Exit restatement overpayment status — 2026-11-10

If Exit completes with an uncollected historical Investor Profit overpayment, the case may retain an open balance for later collection or waive it with a recorded reason.

- Keep the disposition auditable; do not create a cash movement or Company Income/Expense from leaving the balance open or waiving it.
- The role authorized to select/approve the disposition remains BUSINESS DECISION REQUIRED. No implementation was made.

## Approved Q75 — post-Exit disposition role scope — 2026-11-10

Branch Accountant may select open or waived disposition for an adjustment from their authorized Branch; Company-level Accountant may select for any Branch within the same Company.

- A Branch Accountant cannot finalize an Exit spanning Branches. Preserve existing cross-Branch Exit authority and all other module role boundaries.
- Validate against the original adjustment Branch and Company server-side. No code/schema/API/UI changed.

## Approved Q76 — later collection actor scope — 2026-11-10

Branch Accountant may record repayment of an open post-Exit restatement adjustment only in their authorized source Branch; Company-level Accountant may do so for any Branch within the same Company.

- Record an Accounting movement only for actual money received and link it to the open adjustment.
- Exact Accounting event classification and typed source link remain unapproved design contracts. No code/schema/API/UI changed.

## Approved Q77 — post-Exit overpayment repayment classification — 2026-11-10

The user chose an actual Cash/Bank Receipt linked to the open overpayment adjustment; the received amount reduces that open balance and does not become Company Income/Profit.

- This resolves the business classification only. The typed same-Company Accounting source link, model/API contract, and transaction implementation remain architecture work.
- Preserve Q76 role scope and do not create a Receipt before actual money is received. No application code/schema/API/UI changed.

## Repository-verified Accounting source-link contract gap

- `AccountingEvent` has generic `RECEIPT` and `PAYMENT` kinds, but the existing `create_receipt_or_payment` service requires the target to be an Accounting `INCOME` or `EXPENSE`, respectively. A Vehicle Sale is not Company Income and a Vehicle Purchase cost is not Company Expense under V2; sending those through the generic endpoint would misclassify business meaning.
- Current `AccountingSourceLink` supports only Investor Fund Credit and Investor Principal Return. It cannot yet link a Sale Buyer Receipt, Vehicle Purchase seller installment, or seller refund.
- The Phase 5 design therefore needs an explicit typed same-Company source relationship for each new cash event. Accounting must create the one immutable event and one `AccountMovement`; the source module must retain the source relationship/obligation and derive its open amount from those events. Do not create a second cash amount or use free-form `source_reference` as record identity.
- Keep the migration graph acyclic: create source-domain records without an Accounting FK first; add typed Accounting source-link FKs in a later Accounting migration. One outer transaction must own source record/application, event, movement, audit and idempotency response.
- The exact source table/relationship choice, constraints, module-state rules for pre-existing payable settlement, serializer/error contract, lock order and test plan remain open architecture work. No application code was changed for this finding.

## Frontend input gap for the approved Buyer Receipt slice

Repository evidence: the current `collection` form collects Sale, amount, a generic method label and date; it does not collect a named Accounting Cash/Bank account UUID. `method = Cash/Bank transfer` cannot identify which of multiple active Company accounts receives the money. The existing Accounting receipt serializer requires `account_id`, and the Phase 5 Sale Receipt must create one movement in that named account. The approved Fund Credit account field applies only to Fund Credit; it does not yet approve a visible field in the Collection form. Add an explicit Collection account input only after the UI scope is approved, or keep real Buyer Receipt submission unavailable. No safe mapping from method label to account exists.

## Approved Q78 — partial and multiple post-Exit repayments — 2026-11-10

The user chose to allow partial and multiple actual repayments against one open post-Exit Investor Profit overpayment; each received amount reduces the open balance and the remainder stays open.

- Preserve Q76 role scope and Q77's Cash/Bank Receipt classification without Company Income/Profit.
- Still unresolved: handling if actual receipts exceed the remaining balance, plus the typed same-Company Accounting source link/model/API/transaction contract. No code/schema/API/UI changed.

## Approved Q79 — saved-entry editing with audit retention — 2026-11-10

The user chose an edit action for saved post-Exit repayment entries. Ordinary views show the current value only; backend audit history retains the original and corrections, and a note may be added. The actual Cash/Bank Receipt and movement are not changed by editing the entry.

- This preserves the earlier immutable-financial-history rule while allowing a normal edit experience.
- It does not decide what to do when actual repayment exceeds the open balance. The typed Accounting source link/model/API/transaction design remains open. No application code/schema/API/UI changed.

## Approved Q80 — excess repayment disposition — 2026-11-10

The user chose a per-case Accountant decision: keep repayment above the open amount as a balance due back to the Investor, or record a separate actual refund after paying it back. Preserve the original Receipt and do not create Company Income/Profit.

- This resolves excess disposition only. Exact typed same-Company source relationships, Accounting outflow classification/API/transaction, concurrency and idempotency details remain architecture work. No application code/schema/API/UI changed.

## Approved Q81 — partial and multiple excess refunds — 2026-11-10

The user chose to allow partial and multiple actual refunds for excess repayment kept due back to the Investor. Record each actual payment separately and keep the remainder open.

- This does not change the original Receipt or Q80 disposition. No refund is recorded before actual payment; typed Accounting source-link/outflow/API/transaction design remains open. No code/schema/API/UI changed.

## Approved Q82 — full Purchase/Sale amounts and installments — 2026-11-10

The user confirmed full Vehicle Purchase cost and Sale price are recorded independently of settlement timing; seller/Buyer settlements and Purchase/Sale refunds may be partial/multiple, with each actual event no greater than the current outstanding amount. Lower amounts are valid and leave an open balance; excess is rejected and the UI shows a compact pending warning.

- Purchase correction requiring excess seller refund remains blocked until the full required refund is actually recorded. The source-specific typed links, accounting outflow/receipt APIs, and transaction/concurrency contracts remain technical work. No code/schema/API/UI changed.

## Approved Q83 — Sale form Save confirms the actual Sale — 2026-11-10

The user confirmed that a successful Save of the existing Sale form for an actual completed Vehicle sale creates a confirmed Sale and marks the Vehicle Sold. Buyer collection remains separate and may still be pending or partial.

- No separate Confirm button or independent manual Sold flag is needed for this minimal flow.
- This does not enable deactivation: the Garage Job and Investor settlement providers remain absent, and every required open or unknown obligation continues to block deactivation.
- The Sale form must not report success until the authoritative backend Sale record is saved. No application code or schema changed by this decision entry.

## Approved Q84 — Branch permission for actual Buyer refunds — 2026-11-10

The user chose the same Branch boundary as the seller-refund rule: Branch Accountant may record an actual Buyer refund only for a Sale in their authorized Branch; Company-level Accountant may record for any Branch within the same Company.

- This permission is limited to actual Stock Vehicle Buyer refunds and does not create a generic cross-Branch Sales permission.
- Check Company and original Sale Branch server-side. Keep the refund linked to its Sale and actual Cash/Bank outflow.
- No application code or schema changed by this decision entry.

## Approved Q89 — module-OFF rule for existing Purchase cost correction — 2026-11-10

When Vehicle Management is OFF, block an audited cost correction to an existing Purchase even if Accounting is ON. Keep the Purchase, source allocations, seller installments, and history unchanged until Vehicle Management is ON.

- Preserve the separate pre-OFF Seller payable installment exception.
- No application code or schema changed by this decision entry.

## Approved Q90 — module-OFF rule for wrong-Investor Fund Credit correction — 2026-11-10

When Investment is OFF, block an audited correction moving an existing Fund Credit from the wrong Investor to the correct Investor, even if Accounting is ON. Keep the original credit, Branch provenance, audit history, and actual Cash/Bank movement unchanged until Investment is ON.

- No new credit or second Cash/Bank event is created by this correction.
- No application code or schema changed by this decision entry.

## Approved Q91 — module-OFF standalone unused-principal return — 2026-11-10

When Investment is OFF, block a standalone return of unused Available Fund principal if no Exit/settlement had already started before the OFF transition. Keep the Fund unchanged until Investment is ON.

- Preserve the separate rule for completing a pre-OFF Exit; actual movement still requires Accounting ON.
- No application code or schema changed by this decision entry.

## Approved Q88 — module-OFF rule for existing Sale Buyer refunds — 2026-11-10

When Vehicle Management is OFF, block actual Buyer refunds against existing Sales even if Accounting is ON. Keep the Sale/refund obligation unchanged and create no Accounting event or movement until Vehicle Management is ON.

- Preserve Q86 Buyer Receipt and Q87 Seller refund rules as separate rules, and do not change the pre-OFF Seller payable installment exception.
- No application code or schema changed by this decision entry.

## Approved Q87 — module-OFF rule for existing Purchase Seller refunds — 2026-11-10

When Vehicle Management is OFF, block a Seller refund against an existing Purchase even if Accounting is ON. Keep the Purchase and its refund/correction balance unchanged and create no Accounting event or movement until Vehicle Management is ON.

- Preserve the separate pre-OFF Seller payable installment exception.
- No application code or schema changed by this decision entry.

## Approved Q86 — module-OFF rule for existing Sale Buyer Receipts — 2026-11-10

When Vehicle Management is OFF, block Buyer Receipts against existing Sales even if Accounting is ON. Keep the Sale's outstanding receivable unchanged and create no Accounting event or movement.

- This applies to Buyer Receipts only; preserve the separately approved pre-OFF Seller payable exception.
- No application code or schema changed by this decision entry.

## Approved Q85 — Branch scope for Sale confirmation and Buyer Receipts — 2026-11-10

Branch Accountant may create/confirm a Stock Vehicle Sale and record its actual Buyer Receipts only within their authorized Sale Branch. A same-Company Company-level Accountant may perform both actions for any Branch in that Company.

- The permission uses server-owned Sale Company/Branch. It does not change Q84's Buyer refund permission or grant generic cross-Branch access.
- No application code or schema changed by this decision entry.

## Approved Q92 — cap Seller refunds at net actual Purchase payments — 2026-11-10

The total actual Seller refunds linked to a Purchase cannot exceed the confirmed actual installments for that Purchase less actual Seller refunds already received. Recompute and enforce the cap while holding the Purchase mutation lock, atomically with the typed Accounting inflow. Reject excess without partial posting.

- Refund and Purchase cost correction remain separate manually initiated actions linked to the same Purchase; keep confirmed payment/refund and Cash/Bank history.
- No application code, schema, API, or UI was changed by this decision entry.

## Current decision-status reconciliation — 2026-11-10

Earlier `BUSINESS DECISION REQUIRED` notes in this draft are retained as history. These approved answers supersede their unresolved status:

- Buyer Receipt reference uniqueness and normalization: Q63–Q64 resolve the same-Company, same-Cash/Bank-account scope across Branches and trimmed, case-insensitive comparison. Typed source schema, database constraint, API and transaction remain technical work.
- Fund Credit transfer and correction: Q66 resolves one actual transfer per Investor credit; Q69–Q71 resolve correction authority, full-credit-only amount and original receipt effective date. Q72–Q75 resolve restatement overpayment handling and post-Exit disposition authority.
- Purchase/Seller terms and refunds: Q39 and its approved additions resolve zero advance, payable, full funding allocation and Seller identity fields; Q92 caps cumulative actual Seller refunds at net confirmed Purchase payments.
- Demo/mock import: approved Phase 5 scope does not automatically import demo records. A separately authorized historical import would need its own reviewed source and mapping, so automatic mock import is not a current Phase 5 blocker.

Remaining blockers are technical: typed Purchase/installment/refund Accounting links, payable and correction contract, lock order, concurrency/idempotency, API/error contracts and migration sequence. Vehicle deactivation remains dependency-blocked until authoritative Garage Job and Investor settlement checks exist.

## Approved Q93 — Purchase correction requires Investment ON — 2026-11-10

While Investment is OFF, do not apply a Vehicle Purchase cost correction that changes Investor Fund use/allocation; wait until Investment is ON. This supplements Q89's existing Vehicle Management OFF block. Actual Seller refund remains separately gated by Q87 and capped by Q92.

- Preserve Purchase, allocation, installment, refund and Cash/Bank history while blocked; reject atomically with no partial correction.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q94 — upward Purchase correction follows Purchase-specific source proportions — 2026-11-10

Use the original actual Investor Fund/Company Running Capital allocation proportions for an upward Purchase cost correction. Do not hard-code a universal ratio or apply the Investor Profit-share percentage. If Investor Fund is insufficient for its proportional increment, Company Running Capital covers the exact shortfall under source-availability validation.

- Append fixed-precision source adjustments that reconcile exactly to corrected cost; preserve the approved downward-correction and balanced-paise rules.
- No application code, schema, API, or UI was changed by recording this decision.

## Approved Q95 — Purchase correction requires all three modules ON — 2026-11-10

Vehicle Management, Investment, and Accounting must all be ON for a Purchase cost correction, including a correction with no new cash movement. This adds Accounting to Q89/Q93; while any is OFF, keep Purchase, allocation, payable, and history unchanged.

## Approved Q96 — block Investor-funded Sale Buyer Receipt while Investment is OFF — 2026-11-10

Do not record a Buyer Receipt against an existing Investor-funded Sale while Investment is OFF, even if Vehicle Management and Accounting are ON. Keep the receivable unchanged and wait until Investment is ON. Q86's separate Vehicle Management/Accounting gates remain.

## Approved Q97 — Sale price correction is in Phase 5 — 2026-11-10

Include audited correction of a confirmed Sale price in Phase 5. Branch Accountant is limited to the authorized Sale Branch; a same-Company Company-level Accountant may act across that Company's Branches. Recompute the Sale's payable/receivable from the corrected Sale and existing actual settlement records.

- This supersedes the earlier Phase 5 scope text deferring Sale price corrections and Buyer refunds. It does not bring in full CRM, Garage, Investor Profit, or settlement.

## Approved Q98 — Sale correction gate — 2026-11-10

Sale price correction requires Vehicle Management and Accounting ON. Investment may be OFF. This repeated, latest answer supersedes the earlier same-turn answer requiring all three modules.

## Approved Q99 — Buyer refund gate — 2026-11-10

An actual Buyer refund may be recorded when Vehicle Management and Accounting are ON, even if Investment is OFF. Q96 still blocks Buyer Receipts against Investor-funded Sales while Investment is OFF.

## Approved Q100 — Investor calculation effect while Investment is OFF — 2026-11-10

Refresh affected Investor calculations from authoritative Sale, Receipt/refund, and Accounting sources after an approved Q98 correction or Q99 actual refund. This recalculation creates no separate cash event or Investor Profit payment.

## Current Q95–Q100 status

The older Sale scope deferral and the first Q98 module-gate answer are historical and superseded by the decisions above. Valid partial Purchase/Sale settlement continues to show a compact remaining-balance warning; excess remains rejected. Technical contracts, schema/migration order, locks, idempotency, API errors and unavailable deactivation providers remain to be completed and verified.

## Approved technical contract Q101 — Purchase and Seller installments — 2026-11-10

Store full Purchase cost once. Each actual Seller installment is a separate record linked to the Purchase and one Accounting payment/cash-movement event. Derive the remaining payable from authoritative Purchase, installment, correction and refund records rather than editing a paid-total field.

- This resolves the Purchase-vs-installment record shape at the conceptual level.
- Exact typed foreign keys, database constraints, request/response/error schema, lock ordering, idempotency handling and acyclic migration sequence remain open.

## Approved Q102 — direct Vehicle expenses and shared Accounting movements — 2026-11-10

Phase 5 includes direct expenses attached to a Stock Vehicle; Garage Job-linked expenses remain deferred until the Garage phase. A valid direct Vehicle Expense is counted once in that Vehicle's total cost.

- Preserve one authoritative Sale with multiple Buyer Receipt records and one authoritative Purchase with multiple Seller installment records. Each actual cash receipt/payment uses Accounting's shared Cash/Bank movement owner exactly once and links back to its typed business source.
- Direct Vehicle Expense has a Vehicle-owned source identity; actual payments remain Accounting-owned and linked. Reusing Accounting for cash movements does not mean using one generic Sale/Purchase/Expense endpoint or duplicating source records.
- Unresolved before implementation: direct Vehicle Expense source-allocation representation and module gates, typed Accounting links, request/response/error contracts, transaction and idempotency behavior, and migration order.

## Approved Q103 — Vehicle cost funding and accounting classification — 2026-11-10

- Direct Investor-funded Stock Vehicle cost uses available Investor Fund first. The exact uncovered shortfall is Company Running Capital linked to that Vehicle; Investor Fund cannot be overdrawn.
- Do not classify the same Stock Vehicle-specific cost as Company Accounting Expense solely because Company Running Capital funds a shortfall. Actual Cash/Bank movement remains recorded once by Accounting through a typed link to the Vehicle cost source.
- Customer Vehicle costs belong on a customer Garage Job bill. Garage Job cost/billing remains deferred to the Garage phase; no customer Vehicle billing workflow is added to Phase 5.
- This supersedes Q102 wording only where it implied direct Stock Vehicle costs use generic Company Accounting Expense/Payment classification. The Q102 direct Vehicle cost scope and shared Accounting cash-movement owner remain.
- Exact module gates, typed allocation/link schema, endpoint and validation contract, locks, idempotency, and migration sequencing remain unresolved technical work.

## Approved Q104 — direct Vehicle Expense module gates — 2026-11-10

Saving a direct expense and its Investor Fund/Company Running Capital source allocation for an Investor-funded Stock Vehicle requires Vehicle Management and Investment ON. Accounting is required for actual Cash/Bank payment only; with Accounting OFF, save no payment event or cash movement.

- This resolves the Q102/Q103 module-gate question for the Investor-funded direct Stock Vehicle Expense/source-allocation example.
- Do not extend this gate to Purchase or Purchase correction; their all-three-module rules remain.
- Technical work remains: typed models/source links, API and validation contracts, concurrency/idempotency, and migration order.

## Approved Q105 — direct Vehicle Expense payable — 2026-11-10

Record the full direct Stock Vehicle Expense when incurred, even if unpaid or only partially paid. Derive the open payable from the full cost less confirmed linked actual payments. Permit partial and multiple installments; reject overpayment. Each actual installment is linked to the Vehicle Expense and produces exactly one Accounting Cash/Bank movement. The payment does not add cost again.

- The ₹5,000 / ₹2,000 example leaves a derived ₹3,000 payable while total Vehicle cost remains ₹5,000.
- Preserve Q103 source allocation, Q104 module gates, and the separate Company Expense classification. Garage Job-linked customer billing remains deferred.
- This resolves Q102's open question whether Vehicle Expense waits for full payment.
- Remaining technical work: source-owned payable/payment models, typed Accounting link, API/error contract, transactions/locks, idempotency, and migration order.

## Approved Q106 — share account preference across Phase 5 installment forms — 2026-11-10

Use one preference per Company and authenticated Accountant across Seller installment and direct Vehicle Expense installment forms. Prefill from the last successfully committed payment; let the Accountant change it. Failed, rejected, or abandoned attempts do not update the preference.

- The payment record stores its own actual account ID. Validate current account status and authorization at posting; preference does not grant access.
- Other forms are outside Q106. Technical persistence, concurrent-success ordering, and retry behavior remain open.

## Approved Q107 — required reference for Vehicle Expense payments — 2026-11-10

Each actual partial/full payment of a Phase 5 direct Vehicle Expense requires an operator-supplied external reference such as a bank transaction ID or Cash voucher number. Store it on the typed payment source and linked Accounting event source_reference; retain payment UUID/typed relationship as identity.

- No duplicate-reference uniqueness or normalization rule is included.
- This does not alter Q105 payable limits, Q106 account preference, or the separate Fund Credit/Buyer Receipt reference rules.
- Remaining: typed models/link, API validation/error contract, transaction/locking and idempotency behavior, migrations.

## Approved Q108 — normalized Vehicle Expense payment reference uniqueness — 2026-11-10

Enforce a unique normalized external reference per Company and Cash/Bank account across Branches for direct Vehicle Expense payments. Trim surrounding whitespace and ignore case. Reject the duplicate before payment posting.

- This supersedes Q107's earlier open/no-uniqueness wording for this source only; Q107 still requires the user-supplied reference.
- Do not apply this uniqueness rule to other payment/receipt types.
- Implement the normalized constraint/locking atomically with the payment and Accounting movement; exact schema and migration remain technical work.

## Approved Q109 — actual vendor refund before downward Vehicle Expense correction — 2026-11-10

Do not apply a downward Vehicle Expense correction if its corrected amount would be below net actual payments. First require the vendor's excess refund to be received and recorded as a separate Accounting inflow linked to the Expense; then append the cost correction. Preserve all original Expense and payment history.

- The ₹5,000 / ₹2,000 paid / ₹1,500 corrected case requires an actual linked ₹500 refund first.
- Do not create an open vendor credit or balancing Company Expense.
- Source-allocation reduction after correction remains unresolved and requires its own decision/contract.

## Approved Q110 — recompute corrected Vehicle Expense source allocation — 2026-11-10

After a Q109-compliant actual vendor refund, recalculate the corrected direct Vehicle Expense from available Investor Fund first; Company Running Capital supplies the exact shortfall. Do not preserve the old expense's source ratio. Append audited allocation adjustments and retain the original history.

- Q94's proportional rule remains limited to Purchase corrections.
- This resolves the source-allocation rule for corrected Vehicle Expenses. Correction-specific module gates and technical model/API/lock/idempotency/migration work remain.

## Approved Q111 — all three modules required for Vehicle Expense correction — 2026-11-10

After Q109's actual vendor refund, Vehicle Management, Investment, and Accounting must all be ON to apply the Expense correction and Q110 source reallocation, even if no new cash movement is created. If any module is OFF, leave Expense, payable, allocation, and history untouched.

- Q104 new-Expense and actual-payment gates remain distinct. Purchase correction gates are unchanged.
- This resolves the Q110 module-gate question only; technical endpoint, transaction, lock, idempotency, and migration work remain.

## Approved clarification — Company-funded Stock Vehicle costs — 2026-11-10

A direct Stock Vehicle cost with no Investor Fund source is fully assigned to Vehicle-linked Company Running Capital; no Investor Fund use is created. Customer Vehicle costs remain later Garage Job/customer-bill scope. This clarifies Q103 without changing Investor-funded Vehicle source ordering.

- The module gate and actor scope for this Company Running Capital-only expense remain BUSINESS DECISION REQUIRED.

## Approved Q112–Q122 — Vehicle Expense decisions — 2026-11-10

The user approved the following business rules: Branch Accountants may add/pay/refund/correct direct Vehicle expenses only within their authorized Branch; the same-Company Company-level Accountant may act across that Company's Branches. Company Running Capital-only Vehicle costs do not require Investment, while their actual payments require Accounting. Actual Vehicle Expense Vendor refunds require Vehicle Management + Investment + Accounting, with no cap based on prior payments. One Vehicle may use only one Investor's Fund. Upward corrections are allowed with Fund-first/Company Running Capital shortfall allocation. Downward corrections require all three modules even when no refund is required. Corrections restate the original Expense effective date and retain a separate recorded timestamp.

- Still unresolved business items: reference/duplicate behavior for actual Vendor refunds; treatment of refund amounts exceeding net actual payments.
- Technical schema/API/error/transaction/concurrency/idempotency/migration work remains separate and is not submitted as a user business question.



## Approved Q118/Q123 — Vehicle Expense Vendor refunds — latest clarification — 2026-11-10

Latest Q118 answer: no external reference is required for a Vendor refund, and duplicate references are allowed for refunds. This supersedes the earlier Q118 answer for refunds only; Q107/Q108 installment reference controls remain.

Latest Q123 answer: record the actual receipt once; apply only up to the Expense's net actual payments; offer the Accountant a flexible manual option to assign any excess to another appropriate record. Do not automatically classify it as Company Income. This refines Q117: no cap on receiving the actual refund, but the Expense application is capped at its net payments.

- Business decisions Q118 and Q123 are resolved. Technical blocker: define a typed, idempotent, transactional source-allocation contract for one actual cash movement split between the Vehicle Expense refund and a selected excess destination, without duplicate movement.

## Q123 technical contract candidate — 2026-11-10

Repository evidence: `AccountingSourceLink.event` is one-to-one and currently accepts exactly one Fund Credit or Principal Return source. `AccountingApplication` links Accounting events and is not an approved generic cross-domain source allocator. Neither establishes the approved Q123 split between a Vehicle Expense refund and another selected record.

A candidate contract is one typed supplier-refund source for the entire actual receipt, linked to exactly one Accounting event and one Cash/Bank movement; immutable amount-bearing child allocations separately identify the Vehicle Expense refund and the Accountant-selected other valid destination. The allocation sum must equal the actual receipt; the Expense portion must not exceed net actual payments. Do not create an additional Accounting movement or silently classify the excess as Company Income. The exact supported excess destination types and their typed relationships must be derived from existing domain ownership and validated before this candidate is locked; no generic free-form source identifier is approved here.

The eventual command must revalidate same-Company and source Branch permissions, all three required module states, current Expense net payments, destination authority and account state in one transaction. It must serialize against competing refunds and corrections, enforce fixed-precision amounts and replay the same idempotency key without a second cash movement. A failed validation or write rolls back the entire command. Corrections retain the original receipt, movement and allocation history.

This candidate does not define saving an unallocated excess, an automatic category, or a new supplier credit. Request/response/error schema, the actual Accounting event/source type, destination provider contracts, migration dependencies and database constraints remain OPEN. Existing Fund Credit and Principal Return source links and Q66 one-transfer/one-Investor-Credit rule remain unchanged. This is an architecture proposal, not evidence of implementation or a READY status.

## Repository-grounded transaction and retry constraints — 2026-11-10

The current `execute_domain_mutation` locks the actor and then Company, compares observed and current module revisions, checks the server-derived Branch permission, and checks an idempotency record scoped by Company, actor and key. A matching method/path/body hash replays the stored response; a mismatched request yields `IDEMPOTENCY_KEY_REUSED`. The operation and response record share the outer transaction. This is repository evidence for the existing Investment/Vehicle paths, not proof that Purchase, Seller refund, Sale or Vehicle Expense paths exist.

The new Purchase/Expense/Sale commands must preserve this protocol and the existing lock order. After the Company lock, lock all affected domain roots and Cash/Bank accounts in a deterministic order; re-read payable, net paid/refunded amounts, Fund availability and permitted destination from authoritative records under those locks. Create source record, any Accounting event, exactly one actual movement for the actual cash event, valid allocations and idempotency result in the same atomic transaction. Concurrent module OFF must serialize with the Company lock and be checked using the applicable action-specific gates. A replay must never post a second movement. No source allocation or correction alone creates cash.

For Seller Purchase refunds, Q92 limits cumulative actual refunds to net actual Seller payments; Q123's treatment of a direct Vehicle Expense supplier refund is separate and must not weaken the Purchase cap. Zero-advance purchases remain valid under Q39. Mock-data import is excluded by the approved decision and is not a Phase 5 delivery blocker.

These constraints reduce ambiguity but do not lock the exact per-domain foreign keys, deferred constraints, API errors, destination provider definitions or migration order. Vehicle deactivation remains fail-closed until authoritative dependency providers exist. This section is a technical draft, not evidence of tests or runtime behavior.
