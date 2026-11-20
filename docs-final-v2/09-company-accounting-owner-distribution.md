# 09 — Company Accounting & Owner Distribution

Status: DRAFT V2 — Company finance source after approval

## Boundary and authority

Each Company/Tenant has one bounded accounting system covering its Branches. Accounting is the authoritative Company financial backbone for actual Company income, Expense, receipt, payment, Running Capital and Owner Distribution records. Investment owns Investor Fund and positive Investor entitlement; Garage owns work and customer charges. Accounting links to those source events without duplicating an economic amount or turning a Branch into another ledger-owning Company. Cross-Company postings or reporting are forbidden.

The current scope is the accounting needed for Vehicle resale and Garage operations, not a generic ERP. Cash/Bank basics and customer receivables are in scope where relevant; supplier payable and advanced inventory are not mandatory without a confirmed need. Applicable GST/Tax/Invoice details may be retained but no full tax suite is required.

## Company financial records

Record classified Company Income, Expense, actual Receipt and actual Payment with amount, Company, relevant Branch attribution, source, actor, timezone-aware time and history. Cash/Bank basics identify the real payment/receipt channel or position where required. They do not replace source transaction identity or permit manual balance overwrite. A Company-wide Expense may originate in an operational Branch and carry a common-company-expense category/label; it remains part of consolidated Company result. Branch filtering must identify that classification instead of silently pretending it is an independent Branch Company.

Garage owns the agreed customer charge and approved Job/work cost source. Accounting owns the actual Company receipt and the Company Garage Revenue representation. A Garage Job references the authoritative Accounting receipt event; it must not store or add a second receipt amount. Every Garage receipt has a required operator-supplied external reference unique across the Company's Branches; another Company may use the same reference. The cumulative valid receipts cannot exceed the applicable Job charge, and a charge cannot be reduced below valid receipts. Garage does not create automatic refund or customer-credit behavior. Outstanding Garage balance is derived from the authoritative Job charge and linked valid Accounting receipt/correction events. Buyer Sales and receipts for funded Stock Vehicles remain linked to the Stock Vehicle Sale workflow in 05. A receipt may appear in an Investment, Garage and Accounting view but must have one authoritative source and one economic cash effect. A due amount, agreed price, suggestion or reminder is not an actual receipt.

## Positive Vehicle Company Share

For a positive completed funded Stock Vehicle result, calculate the proposed Investor Share under the applicable effective configurable agreement and derive Company Share as the remainder of that approved positive result. The current business standard may be configured as 33% Investor Share, but no Tenant is forced to use it and no 33%, 65% or 67% share is hard-coded. Platform Back Office administers protected Investor positive-share agreement configuration; Accountant uses the approved effective value for authorized postings. The confirmed Company Share enters the Company financial layer and is not a direct Owner payment. Preserve the underlying Vehicle, Investor agreement snapshot, Sale, collection and any linked correction. Final Investor/Company Vehicle settlement requires full Buyer Sale collection and resolution of applicable refund positions.

Company Running Capital is the exact separately sourced actual Company contribution to an approved Vehicle cost. It is neither Company Share nor Investor principal, Company Profit, interest, premium or another return category. For a normal positive Vehicle after full Buyer collection, reconcile actual Investor principal, identify and recover/reconcile actual Vehicle-linked Company Running Capital as capital, then determine the remaining actual positive economic result for configured Investor/Company allocation. Approved Vehicle cost is counted once; recovered capital is not a second Expense, new Company Income, Company Share, Garage Revenue or Profit. An editable recovery suggestion does not change the open position; only a separately authorized confirmed actual recovery does. Partial collection may show provisional positions but cannot finalize Vehicle settlement. Loss treatment remains manual under 05.

## Company result and distributable Profit

The conceptual Company result is:

`Vehicle-business Company Share + Garage Revenue + Other Company Income − Company Expenses = Company Profit/Loss`

Keep source transactions and their classification traceable so the same Vehicle cost, Garage Job cost, receipt or Company Share does not enter this equation twice. Branch-filtered views use original attribution while Company totals consolidate all Branches. A Company Profit/Loss result is not automatically an Owner payable, and a calendar period ending does not transfer funds. The amount that is actually distributable requires a confirmed Company-level position.

**Approved rule:** A same-Company Company-level Accountant reviews Company income, expenses, and liabilities and confirms the amount available for each period. A negative Company result carries forward; only positive balance remaining after that Loss is covered may be considered for Owner Distribution. Verified positive Vehicle Company Share is recognized as Company Accounting Income under the approved addition below. This confirmation does not authorize automatic Owner payment.

**Implementation gap:** Persisted Company-period confirmation, carryforward history, Owner allocation snapshots, and actual Owner payment records remain required. Garage remains the owner of its customer charge and linked Accounting source; see the approved Garage revenue workflow and do not duplicate its receipts or costs.

## Owner allocation and payout

Owner Distribution occurs from confirmed Company-level distributable Profit on a configured Half-yearly/six-month or Annual/one-year period, separate from Investor six-month/annual Profit reconciliation and the three-month Investor Exit notice. Platform Back Office administers the protected effective recipient list and nonnegative percentages summing to exactly 100% of a positive Owners distribution pool, with specific backend action permission, version/history and audit. Accountant uses the effective approved split for authorized distribution confirmation; Owner has read visibility without protected-percentage mutation. The documented current standard configuration is 48.5% / 51.5%; it remains replaceable for the applicable Company and period, never hard-coded as two permanent Owner columns. A zero distributable amount produces no positive Owner allocation.

Use INR fixed-precision decimal arithmetic. Retain high precision for percentage intermediates, round final posted money to two decimal places with `ROUND_HALF_UP`, and avoid binary floating point. For an approved positive distribution amount, calculate each recipient's raw share at high precision and provisional two-decimal share with `ROUND_HALF_UP`. Compute the residual between the approved amount and sum of provisional shares. If positive, add one paise at a time to the recipient most under-allocated relative to raw share; if negative, subtract one paise at a time from a recipient most over-allocated, never allowing a negative allocation. Recompute differences after each step and break equal priorities using stable configured recipient order. Continue until every final allocation is nonnegative and the sum equals the approved distribution exactly. This rule has no fixed Owner count. Preserve the effective recipient/percentage snapshot for the confirmed period.

Calculated and Eligible are not Paid. Owner Distribution is human-confirmed as actual individual payments within authorized Company scope. A recipient's new confirmed payment must be positive and no greater than that recipient's current outstanding approved amount, with atomic concurrency and duplicate protection. A partial actual payment leaves the remainder payable; a reminder or suggested allocation cannot mark it Paid. Later legitimate correction retains original allocation and payment history and reconciles one current open position through linked adjustments/recoveries, without silent netting against Investor Fund or Company Running Capital.

Under 01's automation levels, backend-derived Company/Branch totals and exact approved-allocation arithmetic are Level 1 calculations. Proposed distributable amount once its approved basis exists, Owner allocation and Running Capital recovery are Level 2 editable suggestions where permitted. Period due, unpaid recipient position and other open Company obligations are Level 3 reminders/statuses. Actual Company receipts/payments, confirmed capital recovery, approved distribution and individual Owner payments are Level 4 human-confirmed events; protected percentage changes instead require Platform Back Office confirmation. Exceptional Company/Running-Capital Loss impacts and sensitive corrections are Level 5 manual decisions with reason and audit, followed by authorized confirmation for any actual financial event. Period close or a suggestion never automatically distributes money.

## Loss, corrections and audit

New Stock Vehicle Loss and Running-Capital Loss impacts remain manual under 01 and 05. Do not apply Owner distribution percentages to a negative Vehicle result or create automatic Owner loss-contribution obligations. Company accounting records the manually confirmed Company impact and actual financial transactions with reason/history. Corrections preserve original source, actor, time, values and classification; linked adjustments rather than silent deletion restore the current Company and recipient positions. Reports and caches are rebuildable from authoritative transactions.

## Approved Business Decision Additions

### ADDITION — Company Profit is distinct from Investor Profit and cash

**Status:** APPROVED BUSINESS DECISION<br>

**Effective documentation state:** Current V2 addition

**Rule**
- Company/Owner-side Profit/Loss is derived from recognized/committed Company Accounting Income minus recognized/committed Company Accounting Expense.
- Receipt and Payment remain separate actual cash events. Profit does not mean cash received, paid, distributed, or settled.
- Investor Profit remains Investment-owned and follows its separate approved Investor profit, reconciliation, and settlement rules.

**Scope**
- Company Accounting results and Company/Owner reports; Investor Profit remains within Investment.

**Preserve unchanged**
- Company Share, Garage Revenue, Running Capital, Investor principal, Investor Profit, Owner Distribution, and actual cash events remain distinct and source-owned.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the statement in Company result and distributable Profit that this architecture does not decide cash-versus-accrual treatment, only as to whether already recognized/committed Accounting Income and Expense participate in Company Profit before Receipt or Payment. The later approved Company Share addition resolves Vehicle Company Share recognition; the Accountant-confirmed distributable amount and negative-result carryforward are also approved. This earlier addition still does not resolve any remaining unclassified Company income/expense source.

**Implementation impact**
- Compute the Company result from recognized/committed Accounting records; do not infer Income from a Receipt or Expense from a Payment.

### ADDITION — Verified Vehicle Company Share is recognized in Company Profit

**Status:** APPROVED BUSINESS DECISION — 2026-11-19

**Rule**
- When a same-Company Company-level Accountant verifies and confirms a completed positive Stock Vehicle result, recognize its positive Company Share automatically as Company Accounting Income in the Company Profit result.
- Use a typed link to the exact immutable `VehicleResultConfirmation`; use the Sale's Branch and Sale effective date. This recognition is not a Cash/Bank movement, Buyer Receipt, Company Running Capital recovery, or Owner payment.
- An Investor-funded result also requires Investment ON and its allocation-time agreement snapshot. Every Company Share recognition requires Vehicle Management and Accounting ON so confirmation and source recognition commit atomically. Company-funded results do not require Investment.
- A later verified confirmation for a changed source version must reverse any previously recognized Company Share exactly once and recognize the replacement amount, retaining both records and their audit history. Do not count two versions as two profits.
- Loss and break-even confirmations do not create positive Company Share Income. Apply the separately approved manual Loss rules. Company Share recognition does not by itself finalize distributable Profit or authorize Owner Distribution.

**Scope**
- Recognition of the residual Company Share from a verified positive Stock Vehicle result in Company Accounting Profit.

**Preserve unchanged**
- Investor Share remains Investment-owned and is not Company Income. Buyer proceeds, capital recovery, Expense, Income recognition, actual cash, Investor Profit, distributable Profit, and Owner Distribution remain distinct source records.
- An Accounting module OFF state blocks the atomic Company Share recognition; no partial Vehicle result confirmation may imply Company Profit recognition.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT in this document that recognition of Vehicle Company Share in Company Profit still required a business decision. Other unresolved Company revenue/expense recognition questions are unaffected.

**Implementation impact**
- Add a typed Accounting source relationship and a non-cash Company Share Income event. Create it in the same database transaction as result confirmation, enforce the Sale date/Branch and amount at the database boundary, and include signed current recognition events in Accounting Result. Never derive a duplicate event from the Buyer Receipt.

**Local implementation status:** implemented in the current worktree through a typed source link, transactional result confirmation, and signed Accounting Result inclusion. It remains subject to the Phase 8 acceptance gate and is not a Phase 8 completion claim.

### ADDITION — Company Profit reports use independent calendar windows

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Company/Owner Profit reporting supports monthly views, H1 January 1–June 30, H2 July 1–December 31, and Annual January 1–December 31.
- H1/H2 reports do not close, reset, consume, or prevent annual calculation; Annual is calculated independently from the entire calendar year.
- Report generation does not trigger settlement, Owner Distribution, Receipt, Payment, or Running Capital movement. These Company windows do not govern Investor Profit.

**Scope**
- Derived Company/Owner reports, consolidated and with permitted Branch filtering.

**Preserve unchanged**
- Investor reconciliation periods and Owner Distribution periods remain separately owned and governed.

**Supersedes**
- The later **ADDITION — Phase 8 Company distributable confirmation and Loss carryforward (2026-11-19)** supersedes the earlier unresolved confirmation/carryforward status. The H1/H2/Annual reporting windows above remain reporting periods; this addition does not make a report itself a close or payout.

**Implementation impact**
- Use derived date-filtered reporting; no period-close entity or automatic financial event follows from a report.

### ADDITION — Later Income/Expense corrections restate the original effective period

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Preserve the original Income/Expense, correction timestamp, and immutable linked reversal/replacement history.
- Report the corrected economic result in the original effective reporting period, not automatically as current-period Profit just because correction entry occurred later.
- Actual Receipt/Payment events and their Cash/Bank movements remain unchanged unless those events receive their own separately approved correction.

**Scope**
- Company Accounting correction history and Company Profit/Loss reports.

**Preserve unchanged**
- Audit trail and actual cash-event identity remain immutable; correction does not create a second economic Income or Expense.

**Supersedes**
- None. This adds the approved reporting-period treatment to existing linked correction history.

**Implementation impact**
- Apply the correction chain to the original effective period while retaining the later recorded correction time.

### ADDITION — Income and Receipt outstanding limits

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Income and Receipt are separate. One Income may have multiple partial Receipts.
- Reject any Receipt that exceeds the current outstanding Income or other approved target amount.
- Do not automatically create customer credit, unapplied receipt, or similar behavior.

**Scope**
- Company Income and actual Receipt records/applications.

**Preserve unchanged**
- A Receipt records actual money received and does not create or rewrite Income.

**Supersedes**
- None.

**Implementation impact**
- Validate outstanding amount atomically at the backend mutation boundary.

### ADDITION — Expense and Payment outstanding limits

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Expense and Payment are separate. One Expense may have zero, one, or multiple partial Payments, and each Expense-related Payment applies to that Expense.
- Reject cumulative valid Payments above the Expense's current outstanding amount.
- Do not automatically create unapplied payment, prepayment, supplier credit, refund, or balancing Expense behavior.

**Scope**
- Company Expense, actual Payment, and their application records.

**Preserve unchanged**
- A Payment records actual cash paid and does not create or rewrite Expense; unrelated financial movements remain outside this relationship.

**Supersedes**
- None.

**Implementation impact**
- Recheck outstanding amount under transaction/concurrency protection before committing each Payment.

### ADDITION — Paid Expense correction preserves cash history

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If an Expense has actual Payments, keep the Payment events and Cash/Bank movements immutable and preserve the original Expense and correction history.
- Reallocate applications through audited append-only correction/application records.
- Reject a replacement Expense that cannot cover already-applied Payments while no separately approved credit/refund rule exists. Do not create a balancing transaction.

**Scope**
- Corrections to paid or partially paid Company Expenses.

**Preserve unchanged**
- Actual cash history, audit, original record identity, and one-economic-Expense accounting remain intact.

**Supersedes**
- None. This narrows the permitted correction path without changing existing history requirements.

**Implementation impact**
- Correct atomically; append application reallocation history and leave actual Payment/movement rows unchanged.

### ADDITION — Negative Company Cash/Bank balances are permitted

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A negative Cash/Bank balance is allowed and represents Company debt, borrowed funds, or a deficit financial position.
- Do not infer or create a Loan, Interest, Expense, Credit, or other event solely from a negative balance. Balance remains derived from immutable movements.

**Scope**
- Company-owned Cash/Bank accounts and movement-based balances.

**Preserve unchanged**
- Payment authorization, Expense limits, audit, atomicity, source ownership, and account-movement immutability are unchanged.

**Supersedes**
- None.

**Implementation impact**
- Do not clamp or block an otherwise valid payment/transfer solely because the derived balance becomes negative.

### ADDITION — Reserve is optional and future-only in Phase 4

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Preserve Reserve as an optional future concept. Phase 4 adds no Reserve model, mutation API, approval workflow, release workflow, fixed percentage, or automatic amount.
- Reserve is not a fake Expense and does not rewrite historical Profit.

**Scope**
- Future retained-profit and distribution design only.

**Preserve unchanged**
- Company Profit, Expense, Payment, Owner Distribution, and later actual use of Company money remain separate concepts and events.

**Supersedes**
- None. No Phase 4 Reserve workflow is approved by this addition.

**Implementation impact**
- Do not persist, mutate, approve, or release Reserve in Phase 4.

### ADDITION — Owner has no ordinary Accounting mutation authority

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Owner may read, monitor, analyse, report, and audit within authorized Company/Branch scope, but may not perform ordinary Accounting mutations or financial finalization.

**Scope**
- Owner access to Company Accounting and Owner-facing reports.

**Preserve unchanged**
- Existing Owner read/report/audit visibility remains; Accountant and Platform permissions remain separately scoped.

**Supersedes**
- None. This confirms the existing read-only Owner boundary.

**Implementation impact**
- Keep Accounting mutation actions denied to Owner at the backend authorization boundary.

### ADDITION — Accounting categories use one Company-wide catalogue

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Categories form one Company-wide Accounting catalogue. Company-level Accountant manages it; Branch Accountants may use it but cannot manage it.
- Do not create Branch-, Vehicle-, or Job-specific Accounting category systems.

**Scope**
- Company Income and Expense classification.

**Preserve unchanged**
- Company isolation and historical category references remain. Existing archive/history safeguards remain unchanged.

**Supersedes**
- None.

**Implementation impact**
- Enforce Company scope and role on catalogue management; use the same active catalogue across Branches.

### ADDITION — Used Accounting categories are archived, not deleted

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The Company-level Accountant may add or archive categories in the Company-wide Accounting catalogue.
- A used category must not be hard-deleted; preserve its identity and historical Income/Expense references.

**Scope**
- Company Income/Expense category lifecycle and existing Accounting records.

**Preserve unchanged**
- Branch Accountants may use but cannot manage the shared catalogue. Category labels remain Company-wide; no initial labels are inferred here.

**Supersedes**
- None.

**Implementation impact**
- Preserve archived category records so historical classification remains readable; do not cascade-delete posted Accounting history.

### ADDITION — Cross-Branch correction is limited to Company Accounting

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Company-level Accountant may perform authorized Accounting corrections across Branches within the same Company.
- A Branch Accountant remains limited to their authorized Branch.

**Scope**
- Accounting correction actions only.

**Preserve unchanged**
- Company isolation, BranchAssignment semantics, default-deny, linked financial history, and Garage/Vehicle/Investment/Sales/other-module cross-Branch boundaries.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the pending permission question in docs-final-v2/02-user-roles-permissions.md about whether an Accountant may correct another Branch, only for a Company-level Accountant correcting Accounting records. Manual Loss authority and non-Accounting cross-Branch permissions remain unresolved or default-deny.

**Implementation impact**
- Add no generic permission bypass; apply an explicit Accounting-only action rule.

### ADDITION — Accounting OFF preserves settlement of existing Income/Expense

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Company Accounting is OFF, an authorized user may record a Receipt against an Income that existed before the OFF transition and a Payment against an Expense that existed before the transition.
- An audited correction/application reallocation is allowed only when needed to resolve one of those existing obligations under the approved correction rules.
- New Income/Expense, Cash/Bank account or category management, opening balances, and transfers remain unavailable while OFF.

**Scope**
- Company Accounting module availability and existing receivable/payable records.

**Preserve unchanged**
- Receipt and Payment remain actual cash events. Company isolation, normal Accountant/Branch permissions, immutable history, and no new obligation creation remain enforced.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Accounting-specific minimum OFF-action question referenced in 02. Other-module OFF obligations remain separate and unresolved unless approved there.

**Implementation impact**
- The command must prove the target Income/Expense predates OFF, apply the ordinary role/Company/Branch checks, and serialize safely with the module-state change.

### ADDITION — Company Profit inputs are editable during testing; result is derived

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- During Accounting workflow testing, authorized users may edit the underlying Income/Expense inputs before confirmation; the system recalculates Company Profit/Loss from those inputs.
- Do not allow direct manual editing/override of the calculated Profit/Loss amount. Once the Accounting workflow is validated, the Profit report is read-only.
- Changes to confirmed Income/Expense records continue through linked, audited correction/reversal history.

**Scope**
- Accounting entry/testing workflow and derived Company/Owner Profit/Loss view.

**Preserve unchanged**
- Company Profit remains separate from cash, Investor Profit, distributable Profit, and Owner Distribution. This does not finalize Profit or close a reporting period.

**Supersedes**
- None. This distinguishes editable accounting inputs from the derived Profit result without changing confirmed financial history.

**Implementation impact**
- Keep test-time editing on Income/Expense inputs and preserve the result as a shared derived value; do not introduce a manual Profit balance.

### ADDITION — Company Profit reporting uses Asia/Kolkata calendar dates

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Use `Asia/Kolkata` calendar dates for monthly, H1, H2, and annual Company/Owner Profit reporting windows.
- Keep event instants stored timezone-aware in UTC; use the Asia/Kolkata date only to determine which Company reporting window contains an `effective_at` timestamp.

**Scope**
- Derived Company Accounting Profit/Loss reports only.

**Preserve unchanged**
- Investor Profit reconciliation and Owner Distribution use their own approved rules. Report generation creates no close, settlement, distribution, Receipt, or Payment.

**Supersedes**
- None. This defines the timezone interpretation of already approved Company report periods.

**Implementation impact**
- Convert local calendar period boundaries to UTC instants for backend filtering and aggregation.

### ADDITION — Negative opening balances are valid

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A dated and reasoned opening position for a Company Cash/Bank account may be negative as well as positive.
- A negative opening balance represents Company debt/borrowed/deficit position and creates no Loan, Interest, Expense, Credit, or other balancing event by itself.

**Scope**
- Initial Cash/Bank account balance and its opening movement.

**Preserve unchanged**
- Account balances remain derived from immutable signed movements. Opening balance is not Income, Expense, Receipt, or Payment.

**Supersedes**
- None. This extends the approved negative-balance decision to opening positions.

**Implementation impact**
- Support either sign for the opening movement while keeping the opening record dated, reasoned, fixed-precision, and auditable.

### ADDITION — Phase 4 Accounting Result and signed Opening Balance API

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- `Accounting Result` is a read-only Phase 4 report of recognized, committed Accounting Income minus recognized, committed Accounting Expense for monthly, H1, H2, or annual Asia/Kolkata reporting windows.
- Include only authoritative committed Accounting Income/Expense and their valid immutable correction chains. Exclude Receipt, Payment, Opening Balance, Transfer, Investor Profit, Owner Distribution, and demo/mock/local frontend values.
- This bounded report is not final consolidated Company Profit. Company Share, Garage Revenue, and common Expenses participate only through their separately approved source-recognition contracts. Viewing a report does not close, reset, consume, settle, or distribute an amount.
- Opening Balance input is signed. Store the event amount as positive absolute magnitude and its movement as the signed financial effect. A zero input creates no event or movement. An approved correction may append a reversal-only action for a prior nonzero opening event without a zero-value replacement.
- Opening Balance is neither Income nor Expense and does not enter Accounting Result. A negative position alone creates no Loan, Interest, Expense, Credit, Liability, or other balancing event.

**Scope**
- Phase 4 Accounting Result API and Company Cash/Bank opening movements.

**Preserve unchanged**
- Cash balances derive from immutable movements. Investor Profit, Owner Distribution, distributable-Profit basis, period close/carryforward, and unresolved operational recognition remain separate.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording blocking the bounded Accounting Result pending full Company Profit decisions, and any wording permitting a zero opening posting. This does not resolve final Company Profit.

**Implementation impact**
- Add a scoped no-store read projection over committed Accounting event correction chains; exclude cash movements and all non-Accounting/mock sources.

### ADDITION — Owner posting is no longer a Phase 4 BDR

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Owner remains read-only for ordinary Accounting: read, monitor, analyse, report, and audit are allowed within scope; all ordinary financial mutations and confirmations are denied.

**Scope**
- Phase 4 Accounting API and Owner-facing Accounting access.

**Preserve unchanged**
- Owner Distribution and protected configuration retain their separate existing boundaries.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 plan wording that Owner posting is deferred for a later business decision. The current rule is read-only, with no Owner posting permission.

**Implementation impact**
- Keep Owner read endpoints scoped and explicitly deny every Accounting mutation action.

### ADDITION — Phase 4 Receipt/Payment correction and future cash-event rules

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- **Wrong target only:** if the actual Receipt/Payment is correct but linked to the wrong Income/Expense, call an application-reallocation action. Append a negative application for the old link and a positive application for the correct target, with actor, timestamp, reason, and audit. Do not reverse, edit, or recreate the Receipt/Payment; do not change its Cash/Bank movement.
- **Wrong cash fact:** if the Receipt/Payment amount, account, effective date, or another cash fact was recorded incorrectly, use a dedicated correction command. Preserve the original; append a linked reversal, opposite AccountMovement, and reversal of the old application. If a corrected event is required, append a same-kind replacement, its correct movement, and its application. A Receipt remains a Receipt and a Payment remains a Payment. Record reason, actor, `recorded_at`, and immutable links. All writes are atomic and idempotent; never update or delete the original.
- Required routes are `POST /api/v1/tenants/{company_id}/accounting/receipts/{event_id}/corrections/` and `POST /api/v1/tenants/{company_id}/accounting/payments/{event_id}/corrections/`. Require `reason`; replacement values are required when creating a replacement and may include `amount`, `account_id`, same-kind target ID, `effective_at`, `description`, and `source_reference`. Company, event kind, and historical actor identity cannot change. Use `Idempotency-Key`.
- Target-only reallocation is `POST /api/v1/tenants/{company_id}/accounting/applications/{application_id}/reallocations/` with `{new_target_event_id, reason}`. It changes application history only and follows the existing same-Company and Branch authorization rules.
- After every correction/reallocation, enforce `total active Receipt applications <= current Income amount` and `total active Payment applications <= current Expense amount`. Revalidate Company, Branch, module state, account activity, authorization, concurrency, and idempotency. Reject invalid targets/caps without partial writes; do not invent balancing transactions.
- A later actual refund or recovery is a separate real cash event, not a correction. Phase 4 does not create an unapproved refund/recovery workflow.
- Actual Receipt, Payment, and Transfer requests, including corrected replacement cash events, require `effective_at <= current server time`. They represent money already moved, not plans. Opening Balance uses signed `signed_amount`, persists `abs(signed_amount)` on the event and `signed_amount` on its movement, rejects zero without creating an event, permits an approved historical date, and rejects a future date. Opening Balance is not Income/Expense and is excluded from Accounting Result.

**Scope**
- Phase 4 Company Accounting cash events, their applications/movements, and Opening Balance input validation.

**Preserve unchanged**
- Company isolation, BranchAssignment, default-deny, same-Company cross-Branch correction only for Company-level Accountants, Branch Accountant assignment limits, immutable history, fixed-precision INR, current overpayment/over-receipt caps, and the approved Accounting Result contract.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Phase 4 plan's statement that Receipt/Payment correction/refund is wholly outside Phase 4, only for correction of a wrongly recorded cash fact. A wrong target alone uses application reallocation. A later real refund/recovery remains separate and future/BDR.
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: any Phase 4 API wording that allows a zero Opening Balance event or future-dated actual Receipt, Payment, or Transfer.

**Implementation impact**
- Keep separate domain commands for Income/Expense correction, cash-fact correction, and application-only reallocation. Enforce amount caps and date/ownership/scope checks within the atomic service transaction.

### ADDITION — Phase 4 correction choices, OFF eligibility, and account archive rule

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Every supported Phase 4 correction workflow must offer two explicit outcomes: reverse the original with no replacement, or reverse the original and append a corrected same-kind replacement. Reversal-only is valid only when the specific original record does not represent a distinct economic event (for example, a false/duplicate record); it must not erase a distinct real cash movement. If the event represented by that record occurred but its recorded Income, Expense, Receipt, Payment, Opening Balance, or Transfer facts are wrong, a replacement is required.
- A correct Receipt/Payment linked to the wrong Income/Expense uses application reallocation only. Preserve the actual cash event and AccountMovement; append the old-application reversal and new application. Do not present cash reversal as a way to move an otherwise correct receipt/payment to another target.
- If an Income/Expense still has active Receipt/Payment applications, reject reversal-only. The actual cash applications must first be reallocated through the audited application flow, or safely reversed and reapplied to a same-kind replacement in the same atomic correction. Reject if the cash history cannot remain attached to a valid target without exceeding current limits.
- For a Company-level Accountant, a corrected replacement may be attributed to any Branch in the same Company or Company-wide (`null`) where supported. A Branch Accountant must keep the replacement in the same Branch as the original authorized record and cannot reattribute across Branches. A reversal retains original attribution. This Accounting-specific rule gives no cross-Branch authority in other modules.
- While Accounting is OFF, correction and application reallocation are allowed only when every affected root entry (the original event and its Income/Expense target obligation) was recorded strictly before the current Accounting `DISABLED.effective_from`, and the action is necessary to resolve that same pre-OFF event/obligation. A replacement row recorded after OFF is permitted only as an append-only child in that correction chain; it cannot introduce a new root obligation, a post-OFF target, or unrelated cash activity. If the module-state and entry timestamps are equal or cannot establish ordering, fail closed.
- A named Cash/Bank account cannot be archived if any historical Accounting event or AccountMovement references it, even when its current derived balance is zero. Archive also requires a locked zero-balance check. Preserve the account and all movement/event history; no hard deletion is allowed.
- Transfer correction follows the same false-event versus misrecorded-real-event distinction: reverse only if the transfer did not happen; if it happened with wrong recorded facts, append a linked same-kind replacement. A separate later transfer remains a new authorized Transfer. A real refund/recovery remains a separate workflow and is not a correction.

**Scope**
- Phase 4 Company Income/Expense corrections, Receipt/Payment corrections and reallocation, Opening Balance and Transfer corrections, Branch scope, Accounting OFF exception, and named Cash/Bank account archive.

**Preserve unchanged**
- Original financial events and movements are immutable; changes are append-only and atomic. Outstanding Income/Expense limits, one economic effect, Company isolation, BranchAssignment, Owner read-only, idempotency, and concurrency controls remain. No new refund/recovery rule is introduced.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that treated a corrected cash fact's replacement as merely optional without distinguishing false events from real-but-misrecorded events; the Transfer wording that allowed only reversal when a real transfer's facts need correction; the zero-balance-only account archive condition; and the OFF exception that checked only one pre-OFF event/obligation rather than every affected root entry and target.

**Implementation impact**
- Use an explicit correction outcome in each supported command; validate event existence, kind, actual movement, same-Company Branch reattribution, OFF revision chronology, and account history inside the atomic transaction. Reject unsafe or ambiguous cases without partial writes.

### ADDITION — Phase 4 OFF settlement and correction-child targets

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- When Accounting is OFF, the already approved ordinary settlement exception remains: an authorized user may create a Receipt for an Income recorded before OFF or a Payment for an Expense recorded before OFF. The event, AccountMovement, and first AccountingApplication are one normal settlement transaction and do not require the Receipt/Payment itself to predate OFF.
- For a correction or application reallocation while OFF, all affected original root events and original root Income/Expense obligations must have been recorded before that OFF revision. A newly appended reversal, application correction, or replacement may be recorded after OFF only as linked history in that eligible correction. In an Income/Expense correction, reapplication to the replacement child target is allowed atomically; a standalone reallocation cannot use a post-OFF target.
- A Receipt/Payment created under the current OFF revision through the ordinary settlement exception cannot be corrected/reallocated while that same revision remains OFF. Re-enable first; then normal Accounting correction permissions apply.
- Company-level Accountant correction may change replacement Branch only within the same Company or to Company-wide where supported. Branch Accountant remains bound to the original authorized Branch. This is not a generic cross-Branch grant.

**Scope**
- Phase 4 Accounting OFF settlement, correction/reallocation target validation, and correction Branch scope.

**Preserve unchanged**
- New Income/Expense, account/category management, Opening Balance, and Transfer remain denied while OFF. The original Income/Expense effective instant stays fixed so its corrected result remains in the original reporting period.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: any Phase 4 correction text that blocks the application row required by ordinary OFF settlement, rejects a post-OFF correction-child target in the same atomic correction, or applies the correction-only pre-OFF root test to ordinary settlement.

**Implementation impact**
- Separate ordinary settlement from correction/reallocation command predicates and preserve correction-child links and original effective-period grouping.

### ADDITION — Phase 4 Income/Expense and cash-event effective-date boundaries

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A corrected Income/Expense replacement retains the original `effective_at` and restates its net result into the original effective reporting period. Phase 4 does not change an Income/Expense effective date through its correction command.
- A wrong actual Receipt/Payment cash date may be corrected only through that event's typed correction command: the reversal retains the original instant and the same-kind replacement may carry the corrected actual instant, never a future one. This does not change Company Accounting Result because Receipt/Payment are not Income/Expense.
- Opening Balance correction keeps its original account and effective instant. A real but misrecorded Transfer may use a same-kind replacement with the corrected actual date, not later than server time.
- If an operator needs to move recognized Income/Expense into a different reporting period, stop and obtain a separate business decision. Do not silently make the correction timestamp or another date the period basis.

**Scope**
- Phase 4 correction timestamps and effective-period grouping.

**Preserve unchanged**
- Company Profit reports remain independent calendar windows; actual cash events stay separate from Income/Expense; correction timestamp remains the time the correction was recorded.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the preceding Phase 4 correction addition's undifferentiated treatment of a wrong effective date as a replaceable fact for all event kinds. Income/Expense and Opening Balance retain their original effective instant; actual cash/Transfer use only their typed correction rules.

**Implementation impact**
- Omit `effective_at` from Income/Expense and Opening Balance replacement serializers; permit it only on typed Receipt/Payment/Transfer replacement contracts with the documented boundaries.

## Phase 5 Approved Business Decision Additions — Investment source linkage

### ADDITION — Investor capital receipt is a typed non-income Accounting inflow

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- When Investor money is actually received, record one Accounting capital-inflow event and exactly one positive Cash/Bank AccountMovement; link it by a typed immutable UUID relationship to the Investment-owned Fund credit.
- This is Investor capital, not Company Income, Expense or Profit. Fund balance remains Investment-owned and derives from Fund events; Accounting owns actual Cash/Bank balance.
- An actual Investor principal return is linked to its source credit and one negative Accounting capital outflow. It is not Company Expense/Profit.
- A Vehicle purchase cash outflow, when Q39 payment timing is approved, links to the Vehicle Purchase and is posted exactly once. Investor Fund and Company Running Capital allocations are source allocations, not duplicate cash events or expenses.
- A direct Investor payment of an Exit loss obligation is a real Receipt/Cash-Bank event linked to that obligation; it does not create new Company Income/Profit.

**Scope**
- Phase 5 Investment-to-Accounting source contracts and later Vehicle purchase/Exit loss links.

**Preserve unchanged**
- Phase 4 Income/Expense, Receipt/Payment, account movement, immutable history, idempotency and correction rules. Company Profit remains derived only from recognized Accounting Income/Expense; Investor Profit remains Investment-owned.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether Investor Fund credit is Company Income or only a cash event with an Investment principal link. It does not resolve seller-payment timing or authorize extra Company-wide ledger categories.

**Implementation impact**
- Add typed source-link relations and capital event kinds with same-Company integrity, one-to-one cash effect, atomic write and duplicate protection. Do not use source_reference as entity identity.


### ADDITION — Vehicle-linked Running Capital is not a duplicate expense or Fund debit

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- An approved Company Running Capital shortfall allocated to a Vehicle is a separate recoverable capital source, linked to that Vehicle. It does not create Company Expense or Company Profit and does not debit Investor Fund.
- When actual proceeds from that same Vehicle are received, the approved Company Running Capital recovery may be recorded against that capital position. Record one actual Cash/Bank movement for the real money and link the recovery to it; no receipt/recovery calculation creates cash by itself.
- Investor loss share offsets against Investor Profit are separately owned by Investment and must not be represented as Company Expense, Income, or a second Accounting cash movement.

**Scope**
- Accounting treatment of Vehicle-linked Company Running Capital and future Investor loss integration.

**Preserve unchanged**
- Accounting owns Cash/Bank events; Vehicle cost is recorded once; Company Profit derives from Accounting Income/Expense. Phase 5 does not implement future Sale proceeds or loss settlement.

**Supersedes**
- SUPERSEDES the immediately preceding Phase 5 addition phrase disallowing any Company Running Capital event for a Vehicle loss shortfall. It preserves the rule that the event is not an Investor Fund debit or Company Income/Expense.

**Implementation impact**
- Use typed links and a separate capital-position record; link a recovery to an actual received event without adding a second cash movement.

### ADDITION — Vehicle seller payable and partial payments are supported

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle purchase may create a seller payable for the unpaid portion of its complete approved purchase cost.
- The payable is linked to the Vehicle purchase and may be reduced by one or more actual partial seller payments. Payments cannot exceed the current outstanding payable.
- Accounting records one Cash/Bank outflow for each actual installment. No outflow is recorded for the unpaid balance, and purchase cost or payment is not Company Income, Expense, or Profit.

**Scope**
- Phase 5 Vehicle Purchase and its actual seller payments only; this does not add a general supplier directory or general supplier-payables workflow.

**Preserve unchanged**
- Accounting remains the owner of actual Cash/Bank events and movements. Vehicle cost and funding-source allocations remain separate, with the full purchase cost counted once. Existing Accounting role and Branch authorization rules remain in force.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the general statement that supplier payables are not mandatory without a confirmed need, only for Vehicle Purchase seller payables. Other supplier-payables use remains out of scope.

**Implementation impact**
- Add a typed purchase-payment relationship and derive the remaining payable from linked actual payments; preserve atomicity, idempotency, and append-only cash history.

### ADDITION — Seller payable settlement with zero advance and module OFF

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle purchase may begin with ₹0 paid; the full approved cost is seller payable, and the purchase view warns that no seller advance has been paid.
- Actual installments on an existing purchase payable may continue when Investment or Vehicle Management is OFF, provided Accounting is ON and the purchase/payable predates OFF. No new purchase or Fund-use allocation is permitted by this exception.
- Accounting OFF receives no new exception for Vehicle seller payments from this decision.

**Scope**
- Vehicle seller payable and its Accounting-owned actual Cash/Bank installments.

**Preserve unchanged**
- Each actual payment creates one linked cash effect and reduces only the outstanding payable; purchase cost and funding allocations remain distinct. Existing Income/Expense OFF rules are unchanged.

**Supersedes**
- None in this Accounting document; the new rule narrows the Phase 5 purchase module gate only for settlement of an existing payable.

**Implementation impact**
- Check the pre-OFF purchase and payable identity and Accounting ON state in the installment transaction; derive the zero-advance warning without creating an Accounting event.

### ADDITION — Vehicle seller payable identifies the seller

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Each Vehicle seller payable is associated with the required seller name on its Vehicle Purchase; seller phone is optional.
- This rule covers only Vehicle purchases and does not establish a general supplier directory or payable ledger.

**Scope**
- Accounting display/linkage for Vehicle Purchase seller payables and actual payments.

**Preserve unchanged**
- Accounting owns actual Cash/Bank events; Vehicle Purchase owns its cost and seller identity. Existing Company and Branch access controls remain.

**Supersedes**
- None; seller identity was not previously specified for this payable.

**Implementation impact**
- Expose the linked purchase seller name in payable/payment reads; never identify a seller by free-form source-reference alone.

### ADDITION — Seller installment posting follows Accounting Branch authority

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may post an actual Vehicle seller payment only for a payable attributed to their authorized Branch.
- Company-level Accountant may post for any Branch in the same Company.

**Scope**
- Accounting cash outflows that settle Phase 5 Vehicle Purchase seller payables.

**Preserve unchanged**
- Accounting owns actual Cash/Bank movement. This does not expand pooled Fund-use, purchase creation, or cross-Branch authority in other modules.

**Supersedes**
- None; payment actor scope for this new source type was not previously specified.

**Implementation impact**
- Apply existing Branch Accounting scope to the purchase's attributed Branch, with Company-level cross-Branch scope limited to the same Company.

### ADDITION — Purchase funding allocation is separate from Cash/Bank settlement timing

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Vehicle Purchase records its full Investor Fund and Company Running Capital allocations at purchase creation, including when no seller cash has yet been paid.
- The unpaid seller amount remains a payable linked to the purchase; it is not a second source allocation. Only an actual seller installment creates one Accounting Cash/Bank movement.

**Scope**
- Accounting representation of Phase 5 Vehicle purchase source allocations and seller payments.

**Preserve unchanged**
- Accounting owns actual account movements; allocations and payables do not create cash, Income, Expense, or Profit. Existing Company/Branch permissions and event history remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether Investor Fund and Company Running Capital allocations are recorded only as seller installments are paid. Allocations are recorded at purchase; actual movement remains payment-timed.

**Implementation impact**
- The purchase transaction writes source allocations without AccountMovement; each later actual seller payment atomically writes its typed Accounting event and one negative AccountMovement.

### ADDITION — Seller refund is required before reducing purchase cost below payments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When a purchase correction would make cumulative actual seller installments exceed corrected cost, require the seller's actual excess refund to be recorded in Accounting before accepting the correction.
- A promised refund or seller credit is not a Cash/Bank receipt. Existing payments and movements remain unchanged; preserve the correction and allocation history.

**Scope**
- Accounting records linked to Phase 5 Vehicle Purchase seller installments and purchase-cost correction.

**Preserve unchanged**
- Accounting remains the source of actual Cash/Bank events. Purchase funding allocation is not a cash event or Income/Expense/Profit; lender finance and EMI remain excluded.

**Supersedes**
- None; this resolves the previously unspecified paid-purchase correction case only.

**Implementation impact**
- Provide an explicit typed relationship from the actual Accounting refund receipt to the purchase correction; validate it atomically with corrected cost and allocation history.

### ADDITION — Purchase correction adjusts Fund and Running Capital proportionally

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A downward purchase-cost correction reduces Investor Fund and Company Running Capital allocations in the same proportion as the recorded source split.
- Do not rewrite original source allocations, seller installments, or Cash/Bank movements; append audited correction/reallocation records. Apply the existing FIFO rule within the Fund allocation.

**Scope**
- Accounting linkage for Vehicle Purchase cost corrections and the separately owned Investment Fund / Running Capital source histories.

**Preserve unchanged**
- Accounting records actual seller refunds and payments. Purchase allocations do not create Cash/Bank movement, Income, Expense, or Profit.

**Supersedes**
- None; this specifies the source split for a corrected purchase cost.

**Implementation impact**
- The correction transaction must retain source-proportional totals and link the actual refund; a sub-paisa rounding rule remains to be specified.

### ADDITION — Purchase source correction balances paise deterministically

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Use high-precision proportional calculations and round each Fund/Running Capital adjustment to two decimals with `ROUND_HALF_UP`.
- Reconcile the residual one paise at a time to the most under-allocated source (or subtract from the most over-allocated), recalculating each step. Ties use Investor Fund first, then Company Running Capital; the final sum must exactly equal the correction.

**Scope**
- Accounting linkage and exact totals for corrected Vehicle Purchase source allocations.

**Preserve unchanged**
- Accounting owns actual refund Cash/Bank events; these allocation adjustments create no second movement or Income/Expense/Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: paise rounding for proportional Fund/Running Capital source corrections.

**Implementation impact**
- Reuse the established balanced-paise method with the approved stable source order; validate exact totals transactionally.

### ADDITION — Company-wide approval mode governs Accounting automation

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The Company-wide Automation Approval setting in 01 governs consequential Accounting automation. ON requires the authorized role to approve each proposed posting; OFF allows only already-approved automation to execute under existing Accounting rules and permissions.
- Calculation details for material automated postings appear in a compact responsive popup beside Approve, in business language.

**Scope**
- Accounting-created financial events and other consequential Accounting automation.

**Preserve unchanged**
- Cash/Bank events remain distinct from Income, Expense, Profit and source allocations. Existing Accountant permissions, Company/Branch limits, validation, idempotency, corrections and audit remain in force.

**Supersedes**
- None; this adds a rollout control without changing existing Accounting event meaning.

**Implementation impact**
- Enforce approval mode in the Accounting service transaction. Persist approver, policy revision, calculation basis and outcome; do not let the UI alone authorize a posting.

### ADDITION — Pending Accounting automation remains pending after mode changes

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Turning Company-wide Automation Approval OFF does not execute existing pending Accounting actions. Each pending posting must still be separately approved by an authorized role or cancelled in its owning workflow.

**Scope**
- Pending Accounting automation, including proposed financial postings.

**Preserve unchanged**
- Actual posting continues to require the relevant Accounting permission, validation, Cash/Bank/source linkage, idempotency and audit.

**Supersedes**
- None; this applies the global pending-action rule to Accounting.

**Implementation impact**
- Preserve pending state and policy version across mode changes; do not bulk-post or delete pending Accounting work.

### ADDITION — Accounting auto-posting requires explicit workflow approval

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Company-wide Automation Approval is OFF, an Accounting financial posting may skip per-action confirmation only when that specific workflow is explicitly approved for automatic posting.
- When the mode is ON, each consequential automated posting awaits separate authorized approval.

**Scope**
- Accounting-owned automated financial postings.

**Preserve unchanged**
- Accounting still requires real source evidence, correct Cash/Bank movements, operation-specific permission, Company/Branch scope, validation, atomicity, idempotency and audit. Manual postings remain human-confirmed.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Level 4 human confirmation for every Accounting posting, only for workflows explicitly approved to auto-post while Company-wide Automation Approval is OFF.

**Implementation impact**
- Require a separately approved workflow policy and check it in the Accounting transaction; the global mode switch alone is insufficient.

### ADDITION — Vehicle Purchase seller refund is manually entered and linked

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An Accountant manually records the actual seller refund in Accounting and links it to the same Vehicle Purchase as the manually entered cost correction.
- Do not generate a refund, Income, Expense, or correction automatically. Preserve the original seller payment and each actual Cash/Bank movement.

**Scope**
- Accounting Cash/Bank receipts for seller refunds linked to Phase 5 Vehicle Purchase corrections.

**Preserve unchanged**
- A refund is actual returned cash, not Company Income or Profit. The Purchase correction is separately owned and retains its own audit/source-allocation history.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether seller refund and related Purchase correction are automated or manually entered and linked.

**Implementation impact**
- Require an explicit typed Purchase refund link on the actual Accounting event; update the derived payable only from linked valid events.

### ADDITION — Investor overpayment recovery is a Receipt, not Company Income

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Money actually received from an Investor against an open post-Exit historical Profit overpayment is recorded as a Cash/Bank Receipt linked to that adjustment.
- Reduce the open overpayment by the amount actually received. Do not record this repayment as Company Income or Company Profit.

**Scope**
- Accounting treatment for actual repayment of a post-Exit Investor Profit restatement overpayment.

**Preserve unchanged**
- Preserve actual Cash/Bank movement ownership in Accounting, the open Investor adjustment and Exit audit history, and the separate Company Income/Expense source rules. No Receipt is created before money is actually received.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether this specific post-Exit Investor overpayment repayment is Company Income/Profit. This does not classify other Investor receipts or Company transactions.

**Implementation impact**
- Use a typed Accounting source relationship to the overpayment adjustment; do not attach this Receipt to an Income record. The exact schema/API contract remains architecture work.

### ADDITION — partial actual Receipts for Investor overpayment recovery

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An open post-Exit Investor Profit overpayment may be repaid through partial and multiple actual Cash/Bank Receipts.
- Each actual Receipt reduces the open overpayment by the received amount; any unpaid balance remains open.

**Scope**
- Accounting Receipt handling for actual repayments against a post-Exit Investor Profit restatement adjustment.

**Preserve unchanged**
- Q77's treatment as a Receipt rather than Company Income/Profit, Accounting ownership of actual Cash/Bank movements, and Q76's authorized role scope remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether one post-Exit overpayment recovery must be paid in full at once or may have partial/multiple actual Receipts.

**Implementation impact**
- Link each actual Receipt to the same typed adjustment source and derive its remaining balance. Treatment of an actual amount exceeding the balance remains unresolved.

### ADDITION — edit presentation for post-Exit repayment entries

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An authorized Accountant may edit a saved post-Exit repayment entry. Normal Accounting views show the latest value and do not need to display earlier versions.
- Keep the original and corrections in backend audit history; an explanatory note may be added.
- Do not overwrite the actual Cash/Bank Receipt or movement when editing the repayment entry.

**Scope**
- Accounting-facing presentation and correction history for a post-Exit Investor Profit overpayment repayment.

**Preserve unchanged**
- Accounting remains the owner of actual Cash/Bank movements. Q76 role scope, Q77's Receipt classification/no-Income rule, and Q78 partial/multiple repayments remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether ordinary Accounting views must show earlier repayment-entry values after editing.

**Implementation impact**
- Use an audit-preserving correction flow for edits; maintain the same immutable actual movement. The typed source-link/API contract remains open.

### ADDITION — excess Investor repayment and actual refund

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If an actual Cash/Bank Receipt from an Investor exceeds the remaining open post-Exit Profit overpayment, the authorized Accountant chooses case by case to retain the excess as an open amount due back to the Investor or record a separate actual refund when returned.
- Preserve the original full Receipt. Record the refund as a separate actual cash outflow only when paid; neither the excess nor the refund is Company Income/Profit.

**Scope**
- Accounting records for an excess repayment against an open post-Exit Investor Profit restatement adjustment.

**Preserve unchanged**
- Accounting owns each actual Cash/Bank movement; Q76-Q79 authorization, source, classification, partial-repayment and audit-history decisions remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: disposition and Accounting treatment of repayment received above the open overpayment balance.

**Implementation impact**
- Create one Receipt for actual money received and a separate linked cash outflow only for an actual refund. Keep the refundable excess distinct from Company Income and Expense; exact typed source-link/API contract remains open.

### ADDITION — partial and multiple actual refunds of excess repayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An excess repayment retained as due back to an Investor may be refunded in partial and multiple actual Cash/Bank payments.
- Record each actual refund separately; each reduces the amount due back by the amount paid. Keep any remaining amount open.

**Scope**
- Accounting cash outflows for returning excess post-Exit Investor Profit repayment to the Investor.

**Preserve unchanged**
- Preserve the original full Receipt and Q76-Q80 permissions/classifications/audit history. No refund event is recorded before money is paid; neither the excess nor the refund is Company Income/Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an amount due back after excess repayment must be refunded all at once.

**Implementation impact**
- Link each actual refund cash outflow to the due-back source and derive its residual from actual refunds. Exact typed source-link and Accounting event/API shape remain architecture work.

### ADDITION — Purchase/Sale totals and actual settlement installments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Record the full Vehicle Purchase cost and full agreed Sale price independently of Cash/Bank settlement timing.
- Accounting records each actual seller payment, Buyer receipt, seller refund and Buyer refund as a separate linked cash event when that money moves. Partial and multiple installments are allowed against the relevant current payable, receivable or refund payable; an amount above the outstanding balance is rejected, while a lower amount leaves the remainder open.
- A Purchase correction that requires a seller excess refund remains unaccepted until the full required refund has actually been received and recorded, even if partial refund receipts are allowed.

**Scope**
- Accounting Cash/Bank movements and settlement balances linked to Phase 5 Vehicle Purchase and Sale.

**Preserve unchanged**
- The Purchase/Sale source owns its complete amount and obligation; Accounting owns the actual movement. Neither the price, funding allocation, receipt nor refund is duplicated as Company Income/Expense/Profit. Q76-Q81 Investor repayment rules remain separately scoped.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Vehicle Purchase/Sale refund settlements may use partial/multiple events and whether partial installments below the open amount are allowed.

**Implementation impact**
- Link each actual event to its typed Purchase/Sale obligation, recalculate the outstanding balance atomically, and show a valid partial remainder without generating a balancing event.

### ADDITION — Accounting must be ON for Purchase and Sale corrections

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Accounting must be ON for a Purchase cost correction, including a correction that creates no new actual Cash/Bank movement.
- Accounting must be ON for a Sale price correction; that correction also requires Vehicle Management, while Investment may be OFF.

**Scope**
- Purchase cost corrections that change Company Running Capital allocation and confirmed Sale price corrections that change an Accounting-linked receivable/refund position.

**Preserve unchanged**
- Accounting remains the owner of actual Cash/Bank movements. Corrections do not create a cash event merely by changing a source amount or Sale price.

**Supersedes**
- None; this supplements the existing Purchase and Sale correction gates.

**Implementation impact**
- Reject a correction while Accounting is OFF; do not change payable/receivable or linked allocation history.

### ADDITION — Investment-OFF rules for Sale receipts and refunds

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Do not post a Buyer Receipt against an Investor-funded Sale while Investment is OFF, even if Vehicle Management and Accounting are ON.
- An actual Buyer refund may be recorded while Investment is OFF if Vehicle Management and Accounting are ON.

**Scope**
- Actual Buyer Receipts and Buyer refunds linked to Investor-funded Stock Vehicle Sales.

**Preserve unchanged**
- Each received or refunded amount is an actual Accounting-owned Cash/Bank event linked once to its Sale source. The Buyer Receipt gate differs from the Buyer refund gate.

**Supersedes**
- None; this defines Accounting posting eligibility for the separate Investment-OFF receipt and refund cases.

**Implementation impact**
- Enforce the exact required module set per action before posting; never reuse a receipt command for a refund.

### ADDITION — Sale corrections refresh derived Investor calculations only

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- An approved Sale price correction or actual Buyer refund recorded while Investment is OFF refreshes derived Investor calculations from Sale and Accounting source records.
- The recalculation itself creates no separate cash event or Investor Profit payment.

**Scope**
- Accounting-linked Sale corrections/refunds and their effect on derived Investor calculations while Investment is OFF.

**Preserve unchanged**
- Actual cash remains represented by its own immutable Accounting event and movement. Any Investor Profit payment remains a separately authorized actual transaction.

**Supersedes**
- None; this defines the accounting boundary for derived recalculation during Investment-OFF.

**Implementation impact**
- Preserve the typed Sale/Accounting links and recalculate projections from them; do not infer a Profit payment from the recalculation.

### ADDITION — Accounting records actual Vehicle Expense payments once

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- For a direct Vehicle Expense included in Phase 5, Accounting remains the owner of any actual Cash/Bank payment. Each actual payment is linked to its Vehicle Expense; the Vehicle domain does not create a second cash movement.
- Preserve the Expense and Payment as separate records. Multiple partial Payments follow the existing Accounting outstanding-amount validation.

**Scope**
- Actual Cash/Bank outflows linked to Phase 5 direct Vehicle Expenses. Garage Job-linked expense flows remain deferred to the Garage phase.

**Preserve unchanged**
- Existing Accounting ownership of Cash/Bank accounts and movements, Expense/Payment separation, category ownership, authorization, audit, and module rules. This does not decide a new Company Profit classification for Vehicle expenses.

**Supersedes**
- None; this clarifies Accounting's actual-movement role for the approved direct Vehicle Expense scope.

**Implementation impact**
- Add a typed link from each Vehicle Expense payment to its source and create exactly one Accounting payment event and one Cash/Bank movement for each actual payment.

### ADDITION — Stock Vehicle cost is not a Company Accounting Expense

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct cost of an Investor-funded Stock Vehicle is assigned first to available Investor Fund; any uncovered shortfall is a separate Vehicle-linked Company Running Capital source.
- Do not create a second Company Accounting Expense for that same Vehicle-specific cost solely because Company Running Capital covers the shortfall. Record each actual Cash/Bank movement once through Accounting and link it to its typed Vehicle cost source.
- A customer's Vehicle cost is billed through its Garage Job, which remains deferred to the Garage phase.

**Scope**
- Accounting classification boundary and actual cash-movement ownership for direct Phase 5 Stock Vehicle costs; future Garage Job customer charges.

**Preserve unchanged**
- Accounting remains the owner of actual Cash/Bank movements. Company Running Capital remains distinct from Company Expense/Profit. This earlier note predates the approved Company Share recognition addition; that addition supersedes its Company Share portion while preserving source ownership and leaving unrelated source rules unchanged.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION WORDING: treating a direct Stock Vehicle cost as a generic Company Accounting Expense/Payment by default. This resolves only Stock Vehicle-specific costs; it does not resolve general Company Expense recognition.

**Implementation impact**
- Link the actual outflow to the Vehicle cost source without creating a duplicate Company Expense or Cash/Bank movement. Do not route customer Vehicle costs through Phase 5; use the later Garage source.

### ADDITION — Accounting gate applies at actual Vehicle Expense payment

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct Investor-funded Stock Vehicle Expense and its Investor Fund/Company Running Capital source allocation may be saved with Vehicle Management and Investment ON, even if Accounting is OFF.
- Accounting must be ON to record the actual Cash/Bank payment. No Accounting payment, event, or movement is created when the Expense/allocation is saved without actual payment.

**Scope**
- Accounting module gate for actual payments of Phase 5 direct Stock Vehicle expenses; the non-cash Vehicle cost/source allocation is recorded by its owning workflow.

**Preserve unchanged**
- Accounting still owns Cash/Bank accounts and every actual movement. Q103 continues to classify Stock Vehicle cost separately from Company Accounting Expense and Company Running Capital separately from Company Expense/Profit. Purchase and Purchase correction gates remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER Q102 UNRESOLVED GATE: whether Accounting must be ON when the direct Vehicle Expense/source allocation is first saved. It remains required for actual payment.

**Implementation impact**
- Keep the non-cash cost/source allocation write separate from the later Accounting payment command; require Accounting at the point money actually moves.

### ADDITION — actual payments settle the Vehicle Expense payable

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Record the full direct Stock Vehicle Expense when incurred; actual payment may be zero, partial, or multiple installments.
- Derive the remaining Vehicle Expense payable from the full approved cost less confirmed linked payments. Reject payments above the current outstanding amount.
- Each actual installment is a separate Accounting Cash/Bank payment linked to the Vehicle Expense. Paying the payable does not create another Company Expense or increase Vehicle total cost again.

**Scope**
- Accounting actual-payment records for direct Phase 5 Stock Vehicle Expenses and the linked Vehicle-owned payable.

**Preserve unchanged**
- Q103 keeps Stock Vehicle cost separate from Company Accounting Expense and uses Investor Fund then Company Running Capital for the approved cost source. Q104 requires Accounting ON only for actual payment. Accounting still owns actual Cash/Bank movements.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION AMBIGUITY: whether an approved Vehicle Expense must be fully paid before recording or may remain open for partial/multiple actual payments.

**Implementation impact**
- Expose a typed Vehicle Expense payment source link and create one Accounting cash movement for each actual installment; derive the payable from source history.

### ADDITION — remembered payment account is a shared per-Accountant preference

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- The Cash/Bank account preference is shared by Seller installment and direct Vehicle Expense installment forms for the same Accountant within the Company.
- Store the account actually used on each successful payment. Update the preferred account only after the payment commits; keep the choice editable for each new payment.

**Scope**
- User-specific convenience default for the two Phase 5 actual-payment forms.

**Preserve unchanged**
- Accounting owns each actual Cash/Bank movement. The preferred account is not an authorization grant, does not replace the account ID on a payment, and does not rewrite financial history.

**Supersedes**
- None; this extends the prior per-Accountant Seller-payment preference to direct Vehicle Expense installments.

**Implementation impact**
- Keep preference persistence separate from financial posting; revalidate the selected account and actor's authority on every actual payment.

### ADDITION — operator reference for actual Vehicle Expense installments

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Each actual payment against a direct Phase 5 Stock Vehicle Expense requires an operator-supplied external reference, such as a bank transaction ID or Cash voucher number.
- Record the same reference on the typed Vehicle Expense payment and the linked Accounting event's source_reference.

**Scope**
- Actual Cash/Bank outflows settling direct Vehicle Expense payables.

**Preserve unchanged**
- Accounting remains the owner of actual Cash/Bank movements; each installment creates one movement. Reference text is not record identity. No duplicate-reference uniqueness or normalization rule is added. Buyer Receipt and Fund Credit reference rules remain separately scoped.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an operator-supplied reference is required for a Vehicle Expense installment.

**Implementation impact**
- Validate a nonblank reference before the atomic payment write and preserve the value across the typed source link and Accounting event.

### ADDITION — unique external references for Vehicle Expense payments

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Reject a Vehicle Expense installment whose operator-supplied external reference duplicates another Vehicle Expense payment reference for the same Company and Cash/Bank account, across Branches.
- Trim leading/trailing whitespace and compare case-insensitively.

**Scope**
- Accounting-linked actual payments against direct Phase 5 Stock Vehicle Expenses.

**Preserve unchanged**
- Q107 external reference remains required for each installment. Reference is not payment identity or idempotency. Buyer Receipt, Fund Credit, and other source reference rules remain separately scoped.

**Supersedes**
- SUPERSEDES EARLIER Q107 WORDING: whether duplicate Vehicle Expense payment references are allowed and how they are compared.

**Implementation impact**
- Enforce Company/account normalized uniqueness atomically with payment posting and its single Accounting movement.

### ADDITION — record vendor refund before downward Vehicle Expense correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- When a Vehicle Expense reduction would leave actual payments above the corrected cost, require the vendor to return the excess and record the actual Accounting Cash/Bank inflow before applying the correction.
- The vendor refund is a separate actual movement linked to the Vehicle Expense; it is not Company Income. Preserve the original payments and append the cost correction only after refund receipt.

**Scope**
- Accounting actual inflow and Vehicle Expense correction ordering for a paid direct Stock Vehicle Expense.

**Preserve unchanged**
- Accounting remains owner of actual movements. Q103 keeps the Vehicle cost separate from Company Accounting Expense; Q105 payment history remains immutable. No prepayment, supplier credit, or balancing event is inferred.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether to allow a downward Vehicle Expense correction before the excess refund is actually received.

**Implementation impact**
- Require a linked confirmed refund event before permitting a correction that would otherwise overstate paid amount versus corrected cost.

### ADDITION — Vehicle Expense correction reallocation uses current Fund-first order

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- After the required actual vendor refund is recorded, reallocate a corrected direct Vehicle Expense using available Investor Fund first; Company Running Capital covers only the exact shortfall.
- Do not preserve the original source ratio for Vehicle Expense correction. Keep the source allocation and actual cash-movement histories, and append audited adjustments.

**Scope**
- Company Running Capital / Investor Fund source adjustments after a downward direct Stock Vehicle Expense correction.

**Preserve unchanged**
- Company Running Capital remains distinct from Company Expense/Profit. Q94's proportional rule remains specific to Purchase corrections; Q103 Fund-first and Q109 refund-before-correction rules remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q109 IMPLEMENTATION ITEM: how to recalculate source allocations after Vehicle Expense correction.

**Implementation impact**
- Validate current Fund availability and append a balanced source correction without changing the original Expense, actual vendor refund, or payment movements.

### ADDITION — Accounting gate for Vehicle Expense correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- After Q109's actual vendor refund is recorded, require Vehicle Management, Investment, and Accounting ON to correct a direct Vehicle Expense and reallocate its Investor Fund/Company Running Capital sources, even if correction creates no new cash event.
- If any module is OFF, do not change the cost or its source allocation.

**Scope**
- Accounting-related gate for applying a corrected Stock Vehicle Expense and its source history.

**Preserve unchanged**
- Accounting remains owner of actual Cash/Bank movements. Q104's new-Expense and actual-payment gates, Q109 refund order, and Q110 allocation order remain separate. Purchase correction gate remains unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q110 IMPLEMENTATION ITEM: whether Accounting must be ON for a non-cash Vehicle Expense correction.

**Implementation impact**
- Validate all module revisions and correction invariants inside one transaction; no cash event is created by the correction itself.

### ADDITION — Company-funded Stock Vehicle cost classification

**Status:** APPROVED BUSINESS DECISION CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- If a Stock Vehicle direct cost has no Investor Fund source, assign the whole cost to Company Running Capital for that Vehicle. It is not an Investor Fund use and is not, by itself, a generic Company Accounting Expense.

**Scope**
- Accounting/source classification for direct costs of Company-funded Stock Vehicles.

**Preserve unchanged**
- Investor-funded Stock Vehicle costs use Investor Fund first and Company Running Capital for any exact shortfall. Accounting records actual Cash/Bank movement once. Customer Vehicle costs remain Garage Job/customer bill scope.

**Supersedes**
- None; this records the already approved Q103 clarification for the no-Investor-Fund case.

**Implementation impact**
- Record the Vehicle cost and its full Company Running Capital source separately from Company Income/Expense and actual payment movement.

### ADDITION — Vehicle Expense permissions, refund, and correction outcomes (Q112–Q122)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may add direct Vehicle expenses, pay their installments, record Vendor refunds, and correct cost/source allocation only for a Vehicle in the Accountant's authorized Branch. A same-Company Company-level Accountant may act in any Branch in that Company.
- A cost with no Investor Fund source is entirely Vehicle-linked Company Running Capital; for that cost, Vehicle Management is required to record it, Investment is not required, and Accounting is required only for actual payment.
- Actual Vendor refunds require Vehicle Management, Investment, and Accounting ON. No maximum based on prior Vendor payments is approved.
- Permit upward Expense correction for a valid additional Vendor bill; use available Investor Fund first and Company Running Capital for the exact shortfall, then derive the payable from corrected cost and actual payments. One Vehicle may use only one Investor's Fund.
- A downward correction requires all three modules even if no refund is required. Apply a correction to the original Expense effective date and affected historical Investor calculation; record the correction timestamp separately.

**Scope**
- Direct Stock Vehicle cost source, actual payment/refund movement, payable, correction, and derived Investor result.

**Preserve unchanged**
- Company Running Capital is not Company Income/Expense or Investor principal. Accounting records each actual Cash/Bank movement once. Q109 requires actual Vendor refund first whenever net payments exceed corrected cost. Company Profit period rules do not apply to Investor Profit.

**Supersedes**
- None; this adds the approved Vehicle Expense permissions, gates, and correction outcomes.

**Implementation impact**
- Keep Vehicle cost, source allocations, actual Accounting movements, and corrections separate and linked. Exact treatment of refunds exceeding net payments remains unresolved.

### ADDITION — Vehicle Expense refund reference and excess handling (Q118/Q123)

**Status:** APPROVED BUSINESS DECISION — LATEST CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Vendor refund for a Vehicle Expense does not require an external reference and may reuse a reference from another refund.
- Record the whole actual inflow once through Accounting. Apply to the Vehicle Expense only up to its remaining net actual payments. Offer the Accountant a flexible option to assign excess to another appropriate record; do not automatically classify that excess as Company Income.

**Scope**
- Accounting treatment and source allocation for direct Vehicle Expense Vendor refunds.

**Preserve unchanged**
- Q107/Q108 required unique references remain for outgoing Vehicle Expense installments only. Q117 permits receiving the full actual refund; Q123 limits the portion applied to the Expense. Q109 requires the applicable actual refund before a downward correction that would otherwise exceed net payments.

**Supersedes**
- SUPERSEDES EARLIER Q118 ANSWER: mandatory external reference and duplicate rejection for Vendor refunds only.
- SUPERSEDES EARLIER Q123 DETAIL only where it required a fixed excess record type/reason; destination is selected manually from an appropriate record.

**Implementation impact**
- Use one Accounting cash event with reconciled source allocations; preserve actual cash truth and avoid a duplicate movement or invented Company Income.

### ADDITION — Phase 5 Vehicle refund destinations and Company Running Capital (Q124–Q131)

- Record one actual Cash/Bank receipt for the full Vehicle Expense refund. Reconcile its amount through typed allocations: the original Expense may receive no more than its remaining net actual payments; the rest must go to an Accountant-selected eligible record. If no eligible destination exists, block the refund posting until one exists. Never auto-classify the excess as Company Income.
- If the Accountant explicitly classifies an excess as Company Income, create a separate Company Income event with an Accountant-selected category and note, then link the actual Receipt to it. This increases Company Profit once. Do not edit an existing Income event or auto-classify the excess. This follows Q132 and the existing rule that Income and Receipt are separate.
- Company Running Capital allocation is a separate Vehicle-linked source record for the exact cost shortfall; it is not a Company Expense and does not itself create a Cash/Bank movement. A real payment creates one Accounting event and one movement.
- Only a Company-level Accountant may allocate pooled Investor Fund to Vehicle Purchase or Investor-linked Vehicle Expense. Company-only Purchase/Expense remains available to an authorized Branch Accountant for their Branch; company-level scope remains same-Company only.

### ADDITION — Phase 8 Company distributable confirmation and Loss carryforward (2026-11-19)

**Status:** APPROVED BUSINESS DECISIONS. Implementation remains separately verifiable.

- A same-Company Company-level Accountant reviews recognized income, expense and outstanding liabilities, then manually confirms the period's distributable amount. A derived Company result or period end alone does not authorize an Owner payout.
- Carry a negative Company period result forward. Only a positive amount remaining after that carried Loss is resolved may be considered for Owner Distribution. Preserve original periods, confirmations, adjustments and actual payments as separate audited records.
- No automatic Owner allocation or Cash/Bank movement follows from a calculation, negative result, or period boundary.

**Supersedes:** Earlier unresolved period Loss carryforward and confirmation authority. The exact source recognition and remaining period-close mechanics still require implementation-specific validation against authoritative Accounting and Vehicle/Garage sources.
