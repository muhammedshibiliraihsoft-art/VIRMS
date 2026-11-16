# 01 — Business Rules

Vehicle Investment, Modification & Resale Management System<br>
Status: DRAFT V2 — requires business approval before becoming authoritative

## Authority and scope

This document defines the V2 business model. Document 02 defines permission, 03 module ownership, 04 persistent relationships, 05 Investor/Vehicle finance, 09 Company accounting and Owner distribution, and 10 Garage Jobs. Technical, UI, media and supporting documents cannot change these rules. The previous `docs-final/` set is a historical documentation baseline, not a parallel runtime rule set. There is no production V1 transaction cutover or dual calculation engine.

## Platform, Company and Branch

- The hierarchy is Platform → Company/Tenant → Branch/Garage/Location. Each independent Company is a Tenant and an isolation boundary. The current client has multiple Branches within one Company; the number of Branches is not a coded limit.
- One Company has one consolidated accounting system. Branches provide operational and reporting attribution, not separate Company identities, independent Tenant ledgers or Investor ownership.
- Relevant work, receipts, payments and expenses retain Company and Branch context. A Company-wide/common Expense may be entered through an operational Branch and marked with a common-company classification. Do not create a Head Office Tenant merely for that purpose.
- Company/Tenant isolation applies to every protected record, API, report, media item, background job and audit view. Branch membership never grants access to another Company.

## Vehicle and Garage business

- Each Vehicle/Stock record has one stable Company-wide identity. Current Branch/location and every movement are separate from identity. A transfer retains previous Branch work, costs and audit history on the same Vehicle.
- Vehicle Management is the sole owner of that Company-wide Vehicle aggregate, its identity, lifecycle, current Branch/location and movement history. Platform Core supplies UUID, Company and Branch scope primitives; it is not a second Vehicle writer.
- A funded Stock Vehicle has exactly one funding Investor; one Investor may fund many funded Stock Vehicles. The funding relationship belongs to Company and Vehicle, never to Branch.
- Vehicle identity does not change when its context changes. The same Vehicle may move from Investor-funded Stock activity to external-customer Garage work while retaining the same UUID and history. The Garage Job records its own context; historical Investor funding does not make every later Job Investor-funded.
- Investor responsibility has explicit ACTIVE and ENDED states. An authorized end operation records effective time, actor and reason, retains the relationship and its financial history, and does not itself settle or pay anything. Existing open obligations remain with their authoritative financial module until resolved.
- An external customer's Garage Job does not require an active Investor responsibility and does not affect a former Investor's Fund, principal, Profit, reconciliation or settlement after the responsibility ends.
- The current Stock Vehicle lifecycle is Purchased → In Work → Ready → Listed → Sold. Sold state and Buyer collection state are separate. A transfer does not create another Vehicle or reset its lifecycle.
- Approved Vehicle work/repair/modification, Labour and parts/material costs are traceable to the Vehicle and relevant Branch. Vehicle-level Labour cost and a worker's manual Labour Payment are distinct. Garage Job detail follows 10.
- The Company may actually contribute Running Capital for an approved Vehicle cost that Investor funds do not cover. Track the exact contributed amount per Vehicle and keep it separate from Investor principal, Investor Profit and Company Profit. Running Capital is not a fixed amount, interest-bearing advance, premium or additional return category. A recovery suggestion is editable; only an authorized confirmed actual recovery changes the capital position. No automatic Running-Capital Loss settlement exists.
- Garage (roadmap Phase 6) Jobs use only OPEN and COMPLETED. A Job starts OPEN; OPEN may become COMPLETED and a completed Job may be reopened. While COMPLETED, work, cost and charge entries cannot be added or changed; reopen first. A Job-specific contact is limited to Name and Phone and is not proof of Vehicle ownership or payer identity; phone is not an identity key. No reusable CRM, deduplication, merge or marketing workflow is included.
- A Garage receipt is an actual Company receipt with a required operator-supplied reference unique across all Branches of that Company; the same reference may be used by another Company. Cumulative valid receipts cannot exceed the applicable Job charge, and a charge cannot be reduced below valid receipts. Do not create automatic refund or customer-credit behavior for Garage.
- With Garage OFF, deny new Garage Jobs, optional Job expansion and unrelated new Garage charges. Authorized history reads remain available. Any action strictly needed to resolve an already-open financial obligation goes through its authoritative module and its normal role/object permission; Garage OFF does not create a generic settlement path.
- Phase 6 Garage cross-Branch mutation is default-deny. Same-Company prior-Branch history may be read by authorized users; no Company-level correction grant is introduced by the Garage workflow.

## Investor Fund and positive Vehicle result

- An Investor's principal Fund is an auditable Company-level position shared across that Company's Branches. Initial and additional capital, approved use, actual recovery, withdrawals/settlements and linked corrections are transactions; no user overwrites a balance. Principal and Profit remain distinct. Investor-financed purchase or Expense cannot silently overdraw Available Investor Fund; a Company Running Capital contribution is a separate actual source.
- The agreed Sale Price and valid consolidated Vehicle cost support positive-result arithmetic. A Sale may be fully paid, partially paid or on credit. Actual Buyer Payments, remaining receivable, and Buyer refund obligations are distinct from the Sale agreement. A Sale confirmation alone does not finalize Investor/Company Vehicle settlement.
- Final Investor/Company settlement of a Vehicle occurs only after the full agreed Buyer Sale amount is collected and any required Buyer refund position is resolved. Provisional calculations before collection are not final settlement or Paid transactions.
- For a normal positive Vehicle after full Buyer collection, reconcile actual Investor principal, identify the exact actual Company Running Capital contribution, and recover/reconcile that Company amount as capital before determining the remaining actual positive economic result. Approved Vehicle cost includes each cost once regardless of funding source; capital recovery is not a second expense, Profit, Company Income, Company Share or Garage Revenue. Apply the effective Investor positive-share agreement to the positive result. Investor Share becomes the Investor positive-Profit position; Company Share is the derived remainder and enters Company Accounting, never a direct Owner deal payout. Only confirmed actual recovery/payment changes financial truth. Investor percentage is configurable within 0%–100%, inclusive: the current business standard may be configured as 33%, but no Tenant or agreement is forced to use it. Do not hard-code a Company percentage. Preserve effective configuration and confirmed result snapshots.
- Ordinary eligible deal-level Investor Profit may be paid while an Investor is Active, before Exit, after the existing full-collection and principal-recovery gates and actual Accountant confirmation. Calculation, eligibility and Paid are separate. Monthly Interim Payout is a different advance stream, not earned deal Profit and not guaranteed additional Profit.

## Company result and Owner distribution

- The bounded Company financial layer records Company Share from Vehicle business, Garage Revenue, Other Company Income and Company Expenses. The conceptual result is Company Share + Garage Revenue + Other Company Income − Company Expenses = Company Profit/Loss. The same transaction cannot be counted twice merely because Accounting and a business module both reference it.
- Owner Distribution comes from Company-level distributable Profit, not directly from a Stock Vehicle deal. Supported configured periods are Half-yearly and Annual. A due period or suggested allocation never transfers money; actual distribution is human-confirmed and audited.
- Owner recipients and percentages remain configurable with effective history. The documented 48.5% / 51.5% split is the current standard configuration available for Company-level Owner Distribution, not hard-coded columns or a mandatory split for every Company. Recipients in an applicable positive distribution configuration have nonnegative percentages summing to 100%; exact posted allocations conserve the confirmed distributable amount using 09.

## Protected financial configuration and automation

- Platform Back Office alone administers protected Investor positive-share agreements, Owner distribution percentages, sensitive Company financial defaults and other protected business rates, including the configured Investor monthly rate where applicable. Each change requires backend action authorization, effective/versioned configuration and audit/history. Accountant/Operations uses the approved effective configuration for authorized transactions but cannot independently change protected percentages; Owner has authorized read visibility only. Configuration authority does not grant Platform Back Office routine Company transaction-posting authority. No separate protected business password exists; see 02 and supporting authentication/security.
- Five automation levels apply across modules: **1 Deterministic automatic calculation** from authoritative backend data; **2 Editable system suggestion** requiring review where editing is permitted; **3 Reminder/Due/Notification** without a financial event; **4 Human-confirmed consequential action** by the specifically authorized role, recorded as an actual event; **5 Manual exceptional handling** with explicit authorization, reason and history. The safe progression is **Calculate → Suggest → Remind → Human Confirm → Record**. A calculated value, suggestion, reminder, period end or Sale state never posts money or settles a position by itself. Level 5 covers Loss and other exceptional situations without an invented automatic formula. Apply the relevant level to each later feature rather than specifying every future automation now; authoritative calculations do not depend on AI.
- Hard-block invalid scope, permissions, Company/Branch relationships, funded Vehicle/Investor cardinality, duplicate or over-limit financial postings and corrupt data. Present warnings for unusual but potentially valid conditions; allow editable suggestions or specifically authorized manual exceptions with reason/history only within the existing financial bounds. Frontend workflow retains normal forms, transaction detail, search, reports and explicit confirmation while backend calculations remove manual arithmetic burden.

## Loss and exceptions

- New V2 Loss activity is manual. Record confirmed Loss, manually approved Investor impact, Company impact, reasons, adjustments and actual financial actions. Do not automatically allocate Loss using positive-profit percentages, create formula-derived Owner contribution obligations, or automatically settle Loss.
- The system may calculate safe totals and present a possible negative result for review, but an arithmetic indicator is not an approved Loss allocation or settlement posting. Running-Capital Loss handling is also manual.
- Security, Company isolation and invalid/corrupt data are hard blocks. Unusual but potentially legitimate business cases may use warnings, editable suggestions, authorized overrides or manual entries with reason and audit. This principle does not silently remove existing caps on new Buyer Payments, refunds, confirmed Profit Payments or other bounded obligations.

## Monthly Investor cycle and reconciliation

- Each Investor may have an individual configured Monthly Interim Payout rate and monthly cycle day. Rates such as 1% or 1.5% are examples, never global defaults. If a selected day does not occur in a month, use that month's last calendar day. Do not prorate daily.
- The cycle uses the eligible Investor principal position for that cycle. A top-up, principal withdrawal or monthly-rate change during an active cycle changes the next cycle's basis or rate, not the current one.
- A calculation or reminder may show Due/Suggested. It does not mark Paid. Authorized users may record actual payment, delay, skip, corrected date or correction with audit. Only actual confirmed payments enter reconciliation.
- Investor Profit reconciliation supports configured six-month or annual periods. It compares relevant earned Investor Profit with confirmed interim payments and other relevant confirmed Profit history to determine a remaining payable or Company-recoverable position. Human confirmation is required. A recoverable position can be reduced by direct repayment or explicitly recorded partial/multiple adjustments against future Investor Profit; no automatic silent netting.

## Investor exit, settlement and correction

- Normal Exit requires recorded Terms & Conditions acceptance and three months' notice. The lifecycle is Active → Exit Requested → Settlement Pending → Closed. Exit Requested stops new funded Stock Vehicle purchases using that Investor Fund; already-funded approved work, Sales and collection may continue. Accountant may manage exceptional early closure with audit; Owner remains read-only.
- Available and committed/locked Investor principal, receivables, completed Vehicle positions, interim payments, earned Profit, recoverables, refunds and corrections remain separately visible in global Company-level Investor settlement. Neither notice expiry nor a status change creates cash. Final closure requires all canonical open positions, reconciliations and actual payments to resolve.
- Normal deal-level eligible Investor Profit can be paid before Exit. At final Investor settlement, after blocking positions resolve, pay remaining returnable Investor principal first, then any still-unpaid eligible Investor Profit. Previously retained confirmed Profit or interim payments cannot be paid again. Principal, Profit and Company Running Capital are not silently netted.
- Preserve original financial postings, configuration snapshots, actor, timezone-aware time, amount and reason. Corrections, adjustments, reversals, actual recoveries and actual refunds are linked events. Repeated corrections reconcile one current economic position without erasing history or duplicating a paid, recovered or refunded amount.

## Other approved scope and exclusions

- Owner, Accountant/Operations, Investor Portal, Media, Platform Back Office, reports, audit, public-safe Vehicle views and approved Vehicle images remain in scope. Labour remains a Company/Branch managed record with basic details, Active/Inactive state and manual payment history, without a Labour login or current payroll/attendance system.
- GST/Tax/Invoice data may be retained where applicable but a full tax suite is not required. Full Parts Inventory, barcode-heavy retail, manufacturing, broad CRM, generic ERP and automatic Loss settlement are outside the current baseline. BILLTECH is a business-process reference only.

## Genuine decisions pending

- **BUSINESS DECISION REQUIRED:** Define the precise eligible-principal basis and allowed active-cycle principal withdrawal constraints for Monthly Interim Payout. The next-cycle effect is already confirmed.
- **BUSINESS DECISION REQUIRED:** Define detailed manual financial treatment and approval authority for a confirmed Loss, including Investor principal and Company Running Capital impacts. The normal positive Running Capital capital-recovery sequence above is confirmed and does not supply a Loss waterfall.
- **BUSINESS DECISION REQUIRED:** Define the Company-level distributable Profit base and period close/carryforward treatment, and the exact relationship between ordinary deal-level Investor Profit payments and six-month/annual reconciliation. No confirmed payment may be counted twice.

## Approved Business Decision Additions

### ADDITION — Company Profit and Investor Profit are separate

**Status:** APPROVED BUSINESS DECISION<br>

**Effective documentation state:** Current V2 addition

**Rule**
- Company/Owner-side Profit/Loss is derived from recognized/committed Company Accounting Income minus recognized/committed Company Accounting Expense.
- Receipt and Payment are separate actual cash events. Profit does not mean cash received, paid, distributed, or settled.
- Investor Profit remains an Investment-domain concept and is not calculated using Company Profit reporting periods.

**Scope**
- Company Accounting result and Owner-side Company reports; Investment-owned Investor Profit and reconciliation are separate.

**Preserve unchanged**
- Company Share, Garage Revenue, common Expense, Running Capital, Investor Profit, Company distributable Profit and Owner Distribution retain their existing ownership and decision boundaries.

**Supersedes**
- None. Existing BDRs for source recognition, distributable-Profit basis, period close/carryforward, Loss, and Investor reconciliation remain unless explicitly resolved below.

**Implementation impact**
- Derive Company result from Accounting events. Never infer Income from Receipt or Expense from Payment.

### ADDITION — Company Profit reporting periods

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Company/Owner Profit reports use calendar H1 (January 1–June 30), H2 (July 1–December 31), and Annual (January 1–December 31) windows. Monthly views are also permitted.
- These are reporting windows only. Viewing H1 or H2 does not close, reset, consume, or prevent calculation of Annual Profit, and does not trigger settlement or distribution.
- Annual Profit is independently calculated from the complete calendar year. These Company periods do not apply to Investor Profit.

**Scope**
- Derived Company/Owner Profit and Loss reporting, including permitted Branch-filtered views.

**Preserve unchanged**
- Investor six-month/annual reconciliation and Owner Distribution remain separate domain workflows. Period end alone creates no financial event.

**Supersedes**
- None. Existing BDRs for Company distributable-Profit basis and period close/carryforward remain.

**Implementation impact**
- Use date-bounded derived reports; do not add period-close behavior from these reporting windows.

### ADDITION — Historical Income and Expense corrections restate their original period

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A later correction to recognized Income or Expense preserves the original record and immutable correction/reversal history, including the correction timestamp.
- The corrected economic result is reported in the original effective reporting period; entry of the correction does not automatically move it into current-period Profit.
- Actual Receipt and Payment events remain unchanged unless corrected through their own separately approved process.

**Scope**
- Company Accounting Income/Expense corrections and derived Company reporting.

**Preserve unchanged**
- Audit/history, linked correction identity, actual cash events, Cash/Bank movements, and source ownership remain protected.

**Supersedes**
- None. This specifies reporting treatment without replacing existing correction-history rules.

**Implementation impact**
- Reporting applies the current correction chain to the original effective period while retaining the later correction timestamp.

### ADDITION — Reserve remains a future-only concept

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Reserve is optional and future-compatible. Phase 4 adds no Reserve model, mutation API, approval workflow, release workflow, automatic percentage, or automatic amount.
- Reserve is not a fake Expense and must not rewrite historical Profit.

**Scope**
- Company Profit and any future retained-profit/Owner Distribution boundary.

**Preserve unchanged**
- Income, Expense, Receipt, Payment, Profit/Loss, and Owner Distribution remain distinct. Any later use of Company money remains a separately recorded actual event under its owning workflow.

**Supersedes**
- None. No existing Reserve implementation or approval authority is established by this addition.

**Implementation impact**
- Add no Phase 4 Reserve persistence or mutation path.

### ADDITION — Negative Cash and Bank balances are allowed

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A negative Cash or Bank balance is allowed and represents a Company debt, borrowed, or deficit financial position.
- Do not create a Loan, Interest, Expense, Credit, or other event solely because a balance becomes negative.
- Balances remain derived from immutable account movements.

**Scope**
- Company Cash/Bank account positions and reports.

**Preserve unchanged**
- Payment authorization, Expense limits, source ownership, audit, immutability, and transaction atomicity are unchanged.

**Supersedes**
- None.

**Implementation impact**
- Permit a negative derived balance without adding balancing records or editable balance fields.

### ADDITION — Income/Receipt and Expense/Payment remain separate

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- One Income may have zero, one, or multiple partial Receipts. A Receipt cannot exceed the current outstanding Income or other approved target amount; reject over-receipt.
- One Expense may have zero, one, or multiple partial Payments. Each Expense-related Payment is linked to its Expense; cumulative valid Payments cannot exceed the Expense outstanding amount; reject overpayment.
- Do not automatically create customer credit, unapplied receipts, prepayments, supplier credit, or balancing transactions.

**Scope**
- Company Accounting classification records, actual cash events, and their applications.

**Preserve unchanged**
- Income/Expense remain distinct from actual cash movement and do not acquire other modules' source ownership.

**Supersedes**
- None.

**Implementation impact**
- Enforce outstanding-target limits atomically at the authoritative backend command boundary.

### ADDITION — Accounting module OFF preserves settlement of existing obligations

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Company Accounting is OFF, deny new Income and Expense records, new accounts/categories, opening balances, and transfers.
- Authorized users may record a Receipt against an Income that existed before Accounting was disabled, a Payment against an Expense that existed before it was disabled, and only the audited correction/application reallocation necessary to resolve those existing obligations.
- These actions remain subject to the normal Company, Branch, role, object, and history rules. OFF does not delete or rewrite existing data.

**Scope**
- Company Accounting module availability and already-open Company Income/Expense obligations.

**Preserve unchanged**
- Other modules retain their own OFF behavior and unresolved minimum-action decisions. This does not create a generic settlement path or broaden cross-Branch permissions.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the minimum OFF-module action question, only for Company Accounting obligations as specified here. Other modules' minimum OFF actions remain unresolved unless separately approved.

**Implementation impact**
- Enforce a narrow Accounting OFF allowlist against records created before the OFF transition; preserve the ordinary Accounting permission and transaction checks.

### ADDITION — Company Profit testing edits its inputs, not its result

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- During Accounting workflow testing, authorized users may edit the underlying Income/Expense inputs before they are confirmed; the system recalculates the Company Profit/Loss result from those inputs.
- The calculated Company Profit/Loss amount itself is not manually overridden. Once the Accounting workflow is validated, the Profit report is read-only.
- Confirmed Income/Expense history remains protected; later changes use the approved linked correction/reversal process.

**Scope**
- Company Accounting test/validation workflow and derived Company Profit/Loss display.

**Preserve unchanged**
- Company Profit remains derived from Accounting Income minus Expense, separate from cash, Investor Profit, distributable Profit, and Owner Distribution. No period close or finalization is introduced.

**Supersedes**
- None. This clarifies the editable source inputs and read-only derived result without changing approved financial history rules.

**Implementation impact**
- Keep pre-confirmation Income/Expense inputs editable during testing; do not persist a manually editable Profit total or add an unapproved finalization event.

### ADDITION — Company Profit calendar reports use Asia/Kolkata dates

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Interpret the approved monthly, H1, H2, and annual Company Profit reporting windows using the `Asia/Kolkata` calendar date of each event's effective timestamp.
- Keep event timestamps timezone-aware and stored as UTC instants; this reporting timezone does not alter stored timestamps.

**Scope**
- Company/Owner Accounting Profit/Loss reports only.

**Preserve unchanged**
- Investor Profit periods and Owner Distribution periods remain separate. Reporting windows do not close/reset Profit or trigger settlement/distribution.

**Supersedes**
- None. This specifies the calendar timezone for the already approved Company reporting windows.

**Implementation impact**
- Convert period boundaries from `Asia/Kolkata` calendar dates to UTC instants for filtering authoritative `effective_at` values.

### ADDITION — A Cash/Bank opening balance may be negative

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A dated, reasoned opening balance may represent either a positive or negative starting Cash/Bank position.
- A negative opening position represents the same Company debt/borrowed/deficit position as any other negative balance; do not create a Loan, Interest, Expense, Credit, or other event solely to balance it.

**Scope**
- Initial Company Cash/Bank account positions and their opening movements.

**Preserve unchanged**
- Balances are derived from immutable movements. Opening balance remains separate from Income, Expense, Receipt, and Payment.

**Supersedes**
- None. This extends the approved negative-balance rule to an account's starting position.

**Implementation impact**
- Represent the opening movement's sign explicitly while retaining a dated, reasoned, fixed-precision opening event.

### ADDITION — Phase 4 Accounting Result and opening zero semantics

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 4 `Accounting Result` is a read-only derived report: recognized, committed Accounting Income minus recognized, committed Accounting Expense, grouped into the approved Asia/Kolkata monthly, H1, H2, or annual window.
- Only authoritative Accounting Income and Expense events and their valid immutable correction chains contribute. Receipt, Payment, Opening Balance, Transfer, Investor Profit, Owner Distribution, and demo/mock/local frontend values do not contribute.
- This bounded report is not final consolidated Company Profit. Company Share, Garage Revenue, and common Expenses participate only through their separately approved source-recognition contracts. Report viewing does not close, reset, consume, settle, or distribute a result.
- Opening Balance API input is signed. Store its absolute amount on the event and its signed effect on the movement. Zero creates no event or movement. An approved correction may reverse a prior nonzero opening event without a zero-value replacement.
- Opening Balance does not enter Accounting Result and creates no Income, Expense, Loan, Interest, Credit, Liability, or balancing event by itself.

**Scope**
- Phase 4 Accounting Result reads and named Company Cash/Bank opening positions.

**Preserve unchanged**
- Investor Profit, distributable-Profit basis, period close/carryforward, and other operational source-recognition decisions remain separately owned or unresolved.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that blocks the bounded Accounting Income-minus-Expense report pending final Company Profit decisions, and any permission for a zero-value opening posting. This does not resolve full Company Profit.

**Implementation impact**
- Aggregate only committed Accounting Income/Expense correction chains; derive account balance from signed immutable movements.

### ADDITION — Phase 4 actual cash correction and future-date boundary

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Reallocating a correct actual Receipt/Payment from a wrong Income/Expense target changes append-only application history only. Keep the cash event and Cash/Bank movement unchanged; record actor, time, reason, and audit.
- Correcting a wrongly recorded actual Receipt/Payment uses a dedicated same-kind linked reversal and optional replacement. Preserve the original event; append the opposite movement and reverse its old application. A required replacement appends the corrected event, movement, and application atomically. Apply all current target limits and idempotency checks.
- A later real refund or recovery is a separate actual cash event, never a correction. Its business workflow remains deferred unless separately approved.
- Receipt, Payment, and Transfer `effective_at` cannot be later than current server time. Opening Balance may be historical but never future-dated. Planned future payments require a separate future scheduling model.

**Scope**
- Phase 4 actual cash event correction, application reallocation, and effective-date validation.

**Preserve unchanged**
- Receipt/Payment remain separate from Income/Expense; Company/Branch permissions and all existing caps remain enforced; no cross-Branch permission is broadened.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that all Receipt/Payment corrections are outside scope. Target-only reallocation and correction of an erroneous cash fact are distinct approved operations; later refund/recovery remains separate and unresolved.

**Implementation impact**
- Use dedicated cash correction and application reallocation commands; reject future actual cash dates server-side.

### ADDITION — Phase 4 correction outcomes follow the real event

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Every supported Phase 4 correction flow offers both outcomes: `ORIGINAL → REVERSAL` with no replacement, or `ORIGINAL → REVERSAL → REPLACEMENT` with a corrected same-kind record.
- Reversal-only is allowed only when the specific original record does not represent a distinct economic event (for example, a false or duplicate record); it must not erase a distinct real cash movement. If the event represented by that record occurred but its amount, account, effective date, Branch attribution, or other fact is wrong, a corrected same-kind replacement is required.
- A correct Receipt/Payment linked to the wrong Income/Expense uses audited application reallocation only; it does not use cash-event reversal or replacement. A later real refund or recovery remains a separate event and is not a correction.
- Opening Balance uses its dedicated signed correction semantics: a zero replacement means reversal-only and creates no zero-value event. Transfer correction may replace only a wrongly recorded real transfer; a separate later transfer remains a new authorized Transfer.

**Scope**
- Phase 4 corrections for Company Income, Company Expense, Receipt, Payment, Opening Balance, and Transfer records.

**Preserve unchanged**
- Original records and movements remain immutable; corrections append linked history. Company/Branch permissions, outstanding amount limits, one-economic-effect accounting, and refund/recovery separation remain in force.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 correction wording that leaves reversal-only versus reversal-and-replacement unspecified, or treats a wrongly recorded Transfer as reversal-only even when the real transfer occurred and its facts need correction. It does not convert a later separate Transfer into a correction.

**Implementation impact**
- Make the correction outcome explicit in each supported correction flow and validate it server-side; reject reversal-only when evidence says the real event occurred.

### ADDITION — Phase 4 correction requirements preserve approved reporting periods

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- For Income/Expense correction, the replacement retains the original `effective_at`; the corrected net economic result is restated into that original effective reporting period. Phase 4's Income/Expense correction does not move an entry to another reporting period by changing its effective date.
- For actual Receipt/Payment cash-fact correction, a replacement may correct the cash event's `effective_at`; the reversal neutralizes the original movement at the original instant, and the replacement is not future-dated. Receipt/Payment remain excluded from Accounting Result.
- Opening Balance correction retains the original account and effective instant. A misrecorded real Transfer may use a same-kind replacement with the corrected effective instant, subject to the actual-event date limit.
- Same-kind replacement remains required when a distinct real event occurred but its supported facts are wrong. A false/duplicate event with no distinct economic or cash effect may use reversal-only. Wrong-target-only Receipt/Payment correction remains application-only.

**Scope**
- Effective-date handling for Phase 4 Income/Expense, Receipt/Payment, Opening Balance, and Transfer correction flows.

**Preserve unchanged**
- Company Profit reporting periods, historical restatement, actual Receipt/Payment separation, immutable originals, and the rule that correction entry time does not turn old economic activity into current-period activity.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the preceding Phase 4 correction addition's undifferentiated reference to a wrong `effective date` as a replaceable fact for every event kind. Income/Expense effective period and Opening Balance effective instant stay fixed; actual cash/Transfer date correction follows the typed rules above.

**Implementation impact**
- Exclude `effective_at` from Income/Expense and Opening Balance replacement inputs; allow it only on the approved typed cash/Transfer correction contracts. If a business case must move recognized Income/Expense to a different period, treat that as a separate `BUSINESS_DECISION_REQUIRED` item rather than silently changing this rule.

### ADDITION — Monthly Interim is a fixed per-Investor amount

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Monthly Interim is a fixed INR amount configured separately for each Investor and monthly cycle, not a percentage calculated from eligible principal. Amounts may differ by Investor; illustrative amounts such as ₹500, ₹1,000, ₹2,000, or ₹3,000 are examples, not defaults.
- The amount can be set during the Investor create/edit workflow and edited later. A change made during an active cycle takes effect from the next cycle, preserving the already approved next-cycle timing for active-cycle configuration changes.
- An actual Monthly Interim payment remains an advance against that Investor's eventual Profit. The configured amount or a due/suggested value is not itself a payment. Actual payment requires the existing authorized confirmation and is reconciled against Investor Profit under the separately approved Investor reconciliation rules.
- Any amount exceeding the finally earned Investor Profit remains a recoverable position under the existing approved recovery rules; do not silently net it against another category or create an unapproved balancing event.

**Scope**
- Investment-owned, per-Investor Monthly Interim amount configuration and its cycle calculation.

**Preserve unchanged**
- Investor Profit remains separate from Company Profit. Existing cycle-day, no-proration, actual-payment confirmation, recovery, ordinary deal-level payout, and reconciliation controls remain. This does not decide permitted principal withdrawals or which deals participate in period reconciliation.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the rate-based Monthly Interim calculation and the unresolved eligible-principal basis for calculating its amount. This resolves only the amount basis; permitted active-cycle principal withdrawals and the reconciliation-period deal/payout relationship remain BUSINESS DECISION REQUIRED.

**Implementation impact**
- Read the cycle amount from the Investor's effective, auditable configuration; do not derive it from principal or create a payment from configuration. Retain the effective-cycle snapshot needed for historical reconciliation.

### ADDITION — Confirmed Monthly Interim is shown as Paid against Investor Profit

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- In the Investor's six-month or annual Profit reconciliation, each actual confirmed Monthly Interim advance is included in the `Paid` portion against Investor Profit.
- Show earned Investor Profit separately from the confirmed Interim amounts paid. Do not lower, overwrite, or relabel the earned-Profit figure as though the advance changed the Profit calculation.
- Only actual confirmed Interim payments count as Paid. A configured amount, due/suggestion, reminder, skipped amount, or unpaid amount does not.
- Calculate any remaining payable/recoverable position after applying these confirmed advances under the applicable reconciliation rules. An excess remains subject to the existing Company-recoverable rules; do not silently net it against another category.

**Scope**
- Display and reconciliation treatment of actual Monthly Interim payments in the Investor Profit account.

**Preserve unchanged**
- Monthly Interim remains an advance, not earned Profit or Investor principal. Keep actual payment history immutable and separate from the earned-Profit calculation. This does not decide which deals belong to a reconciliation period or how ordinary deal-level Profit payments interact with periodic reconciliation.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether confirmed Monthly Interim advances are included as Paid against the Investor's Profit entitlement at reconciliation. This does not resolve reconciliation-period deal inclusion or the treatment of ordinary deal-level Profit payouts.

**Implementation impact**
- The Investor Profit view should show gross earned Profit and confirmed Interim payments as distinct values, then show the remaining position. Reference the original payment records; do not create a duplicate payment or cash movement for display/reconciliation.

## Phase 5 Approved Business Decision Additions — Investor Fund, Vehicle periods and Loss

### ADDITION — Company pooled Fund and Branch credit provenance

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Investor Fund is one pooled balance for the Company. Every Fund credit requires a Branch source tag; the Branch is provenance and permission scope, not a separate Fund.
- A Branch Accountant may record and view only their authorized Branch's credits and amounts. A Company-level Accountant may work across Branches in the same Company.
- Company-level Accountant alone may allocate pooled Investor Fund to Vehicle purchases. A Branch Accountant may not spend pooled Fund.
- Vehicle funding consumes the Investor's older eligible Fund credits first (FIFO). Credit lots remain traceable, but later Vehicle Profit is not split by credit lot.

**Scope**
- Company Investment Fund, credit, use and principal-return source attribution.

**Preserve unchanged**
- Company isolation, immutable UUIDs, actual cash movement ownership in Accounting, Vehicle identity ownership in Vehicle Management, and no duplicate Income/Expense/Profit event.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether each Branch has a separate Investor Fund or whether Branches may see/use the pooled total, and whether a Branch Accountant can allocate another Branch's credits. It does not make Company Fund into Branch sub-ledgers.

**Implementation impact**
- Persist Branch on each credit/use provenance and enforce source-Branch scope on the backend; derive balances from immutable records.

### ADDITION — Vehicle-sale result determines Investor Profit period membership

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Investor Profit attributable to an Investor is derived from the actual result of the Stock Vehicle(s) funded for that Investor under the applicable agreement; do not apportion Profit by individual Fund credit lots.
- Attribute a Vehicle result to the Investor Profit period containing its Sale date. A later receipt completing collection does not move that result into the later period; when collection later completes, restate the original Sale period with audit history.
- A later Fund top-up does not change the attribution of an already sold Vehicle or split that Vehicle's result by credit date.

**Scope**
- Future Investment-owned Investor Profit and reconciliation periods; not Phase 5 Fund balance calculation.

**Preserve unchanged**
- Actual Buyer receipts remain separate cash events. Profit calculation/payment, settlement and period close remain outside Phase 5; a period report does not itself pay or settle.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the prior rule that profit attributable to a later Fund top-up must be held for the next Investor period, only where a Vehicle funded after the top-up is sold in the current period. This does not change the Investor-specific calendar setting.

**Implementation impact**
- Future period calculation must use Vehicle Sale effective date and confirmed Vehicle result; late collection triggers an audited restatement of that original period.

### ADDITION — Investor Profit calendar is configurable per Investor

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Each Investor has an independent Profit calendar. A same-Company Company-level Accountant may set the calendar start date and period duration; six months is the default, and other month/year durations may be configured.
- A calendar change begins only at the next incomplete period boundary. Do not change a date inside an already completed calculation or overlap a new period with a completed period.
- Preserve completed reconciliations and actual payments unchanged; a new setting applies prospectively only.

**Scope**
- Future Investment period definitions, reconciliation windows and historical calculation versions.

**Preserve unchanged**
- Company Profit uses its separate calendar-year rules. Investor Profit does not inherit Company Profit periods, and period completion alone does not create a payment.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: any fixed Investor six-month/annual calendar or rolling anniversary wording, only for how an Investor may configure future period start and duration. Existing completed periods/payments remain unchanged.

**Implementation impact**
- Store append-only per-Investor calendar versions with effective boundary, actor and audit context; do not rewrite closed calculations.

### ADDITION — Investor Loss is tracked separately and offsets future Investor Profit

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Apply the Investor's applicable Vehicle agreement percentage to that Vehicle's loss result as the Investor loss share; do not debit ordinary new Fund credits for a loss.
- Keep each Investor loss share as an audited loss position. Offset it only against that Investor's other current/future Vehicle Profit, using a separate audited offset record. Keep gross Vehicle Profit visible and show the offset and net payable separately.
- If available current/future Vehicle Profit is insufficient, preserve the outstanding loss position for later Profit.
- At final Exit, if no future profitable Vehicle position remains, first use only eligible Available Fund to reduce the remaining loss. If a balance remains, collect it directly from the Investor. Exit remains open until the residual is resolved. Record any actual receipt in Cash/Bank linked to the loss settlement, not as new Company Income or Profit.
- Do not make Investor Fund negative or create an automatic Company Running Capital balancing event from an Investor loss.

**Scope**
- Future Investment Vehicle-result, Investor Profit offset and final Exit settlement workflows.

**Preserve unchanged**
- Each confirmed loss, offset, Fund debit and actual receipt is a distinct immutable linked fact. Phase 5 does not calculate or settle Investor Profit/Loss/Exit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the BDR that leaves whether Investor bears a Vehicle loss share, whether it can be offset from other Vehicle Profit, and how an uncovered balance is resolved at Exit unspecified. It supersedes any earlier proposal to debit new Fund credit or create a Running Capital balancing item for that same Investor loss.

**Implementation impact**
- Later implementation needs a versioned agreement snapshot, append-only Loss/offset/settlement records, current-position locking and an actual Cash/Bank source link for direct Exit repayment.

### ADDITION — Exit is flexible, prevents new Fund credit, and requires manual approval for cancellation

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Three months is the normal Exit notice shown to the user; the Company-level Accountant may extend the deadline by recording a new date and reason. There is no fixed maximum extension.
- An Investor may request cancellation at any time. Reactivation occurs only after the same-Company Company-level Accountant approves the cancellation request.
- Once Exit is requested, no new Fund credit or Vehicle purchase funding is accepted for that Investor. Existing eligible settlement work can continue under its separately approved rules; unresolved positions keep Exit open.
- The Investor may restore a cancelled Exit request to Active only through the approved cancellation action; no date-based automatic reopening or settlement is implied.

**Scope**
- Investment Exit lifecycle and new Fund/purchase gating.

**Preserve unchanged**
- No automatic payment, purchase, settlement, release of committed amount, or financial approval is inferred from a notice date. Full settlement rules remain separately owned by the Investment workflow.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: a fixed non-extendable three-month Exit deadline and any automatic cancellation/reactivation interpretation. It also supersedes any rule allowing a new Fund credit after Exit starts.

**Implementation impact**
- Store Exit requests, extensions and cancellation approvals as audited events; block new credit/use through backend state checks.

### ADDITION — Fund principal return is limited by Available Fund and source Branch

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- While an Investor is Active, principal may be returned only from that Investor's unallocated Available Fund. Principal committed to an unresolved Vehicle may not be returned.
- A Branch Accountant may return only available credit attributed to their authorized Branch. A Company-level Accountant may return eligible available principal from any Branch in the same Company.
- At Exit, only if no future Vehicle Profit remains, remaining loss may first be reduced from eligible Available Fund; an uncovered residual is a direct Investor payment and keeps Exit pending until received.

**Scope**
- Investment Fund principal returns and the future final Exit loss exception.

**Preserve unchanged**
- Fund remains Company-pooled; Branch attribution does not create separate balances. Actual return is a separate cash-outflow event. Do not infer a return/withdrawal while Fund is allocated to a Vehicle.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the active Investor principal-withdrawal eligibility and Branch authority questions, only for unallocated principal-return actions. This does not authorize withdrawal of Fund committed to a Vehicle.

**Implementation impact**
- Return API must identify the source Branch/credit lots, lock current eligible amount, reject excess and atomically append a Fund debit linked to one actual Accounting movement.

### ADDITION — Investor setting, Fund and Vehicle actions have distinct module gates

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Investor profile and settings require Investment ON.
- Vehicle create, Branch move and deactivate operations require Vehicle Management ON.
- Actual Fund credit requires Investment and Accounting ON.
- A Vehicle purchase funded by Investor Fund/Company Running Capital requires Investment, Vehicle Management and Accounting ON.
- If Investment turns OFF after an Exit has already begun, new credit and Vehicle funding stop. An already-started Exit may continue its approved accounting reconciliation/settlement actions through the same-Company Company-level Accountant only; actual cash movement additionally requires Accounting ON.

**Scope**
- Investment, Vehicle Management and Accounting module-state gates.

**Preserve unchanged**
- OFF does not delete or rewrite history, grant access, or allow a new root operation. Company/Branch authorization remains required.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Investment/Vehicle/Accounting module combination required for the listed Phase 5 actions and the handling of a pre-existing Exit after Investment OFF. Other-module OFF behavior remains unchanged.

**Implementation impact**
- Serialize each write with Company module-state revisions; preserve completed history and distinguish new posting from an already-open Exit action.


### ADDITION — Investor Loss offset and Company Running Capital recovery remain distinct

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- A Company may cover an approved Vehicle cost/loss shortfall from Company Running Capital when Investor Fund is insufficient. Record the exact Vehicle-linked amount as recoverable Company Running Capital; do not debit or make Investor Fund negative.
- Recover Company Running Capital first from actual proceeds of that same Vehicle when those proceeds are received; a calculation or pending sale is not recovery.
- Separately, the Investor's approved loss share remains an audited position that may offset that Investor's current/future Vehicle Profit through a distinct audited offset. If it is not fully offset, carry the remaining Investor loss position as previously approved.
- Do not silently merge the Company Running Capital recovery and Investor Profit offset into one record or count either as new Income/Expense/Profit. Their settlement remains separate.

**Scope**
- Future Investment loss accounting and Vehicle-linked Company Running Capital.

**Preserve unchanged**
- Actual cash movement is recorded only when money moves; Company Running Capital, Investor Fund, Vehicle cost and Investor Profit remain distinct.

**Supersedes**
- SUPERSEDES the immediately preceding Phase 5 addition phrase stating that no Company Running Capital event is created for a loss. The approved Company Running Capital shortfall rule remains; this narrows its distinction from the separate Investor loss-offset rule.

**Implementation impact**
- Keep separate typed ledgers and future recovery links; a future service must prevent duplicate recovery and requires an explicit reconciliation rule before posting overlapping loss claims.

### ADDITION — Vehicle purchase may be recorded before full seller payment

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle purchase may be recorded before the full seller payment is made. The unpaid purchase balance remains payable to the seller and may be paid through multiple partial payments.
- Record the complete approved purchase cost and its approved funding-source allocations once. A payment reduces the outstanding payable only when the actual payment is recorded.
- Do not classify purchase cost or seller payment as Company Income, Expense, or Profit. Accounting Cash/Bank changes only when money actually moves.

**Scope**
- Phase 5 Stock Vehicle purchase, its seller payable, and actual seller payments.

**Preserve unchanged**
- Investor Fund and Company Running Capital remain distinct sources; their combined purchase allocations equal the approved purchase cost. Existing Company, Branch, permission, audit, and correction boundaries remain.

**Supersedes**
- None in this business-rules document. The Q39 purchase-timing blocker is superseded in the canonical Vehicle/Investor workflow document.

**Implementation impact**
- Keep purchase recognition, payable balance, funding allocation, and actual cash payment as linked but distinct records. Do not create a cash movement for an unpaid amount.

### ADDITION — Seller identity is recorded on Vehicle purchase

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Seller name is required on each Vehicle purchase. Seller phone number is optional.

**Scope**
- Phase 5 Vehicle Purchase and its seller payable.

**Preserve unchanged**
- Seller identity is not Vehicle identity, Investor identity, or Garage Job customer/contact identity. This does not create a general vendor directory.

**Supersedes**
- None; the current Vehicle Purchase field set had not specified seller identity.

**Implementation impact**
- Validate a non-empty seller name at purchase creation and retain an optional phone number with the purchase record.

## Approved Business Decision Additions

### ADDITION — Company-wide automation approval mode

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Add one Company-wide Automation Approval setting in Settings; it applies across all modules. The initial mode is ON.
- When ON, each system-generated action that changes business state or posts a financial event must remain pending until an authorized person approves that specific action. When OFF, already-approved module automations may execute automatically under their existing domain rules and permissions.
- Pure calculations and read-only projections continue to update automatically in either mode; they do not create approval work by themselves.
- For calculation-based or materially consequential automation, place a compact rounded Details/Note control beside Approve. It opens a responsive popup showing the business-readable inputs/sources, calculation steps or formula, and resulting amount/outcome—not technical logs.

**Scope**
- Company settings and consequential automated actions across all modules; the approve/detail interaction appears in the relevant workflow where the proposed action is shown.

**Preserve unchanged**
- Module-specific authorization, Company/Branch scope, validation, audit history and approved business formulas remain mandatory in both modes. Disabling approval does not enable an unsupported or unauthorized action.

**Supersedes**
- None; this adds a Company-level rollout control while preserving the existing five automation levels.

**Implementation impact**
- Persist the setting with versioned/audited changes and enforce it in the backend at execution time. Toggle authority and treatment of already-pending actions still require explicit definition.

### ADDITION — Company Accountant alone controls automation approval mode

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Only a Company-level Accountant for that same Company may change the Company-wide Automation Approval setting.
- Branch Accountants, Owners, and Platform Back Office may not change this Company setting.

**Scope**
- Authorization for changing the Company-wide automation approval mode across modules.

**Preserve unchanged**
- Each automated action still requires its own domain permission, Company/Branch scope, validation, and audit. This setting cannot grant posting authority.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: authority to change the Company-wide Automation Approval setting.

**Implementation impact**
- Expose a dedicated same-Company Company-level Accountant action; enforce it in the backend and audit each version change.

### ADDITION — Automation mode changes do not auto-execute existing pending actions

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Turning Automation Approval OFF affects only consequential automated actions generated after the new mode takes effect.
- Actions already pending remain pending; each must be separately approved by an authorized role or cancelled through its owning workflow. A mode change must not batch-execute or erase pending actions.

**Scope**
- Company-wide automation-mode changes and all existing module-specific pending actions.

**Preserve unchanged**
- Each action retains its owning module, actor permissions, Company/Branch scope, validation and audit history. Changing mode does not reverse already committed events.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: what happens to already-pending actions when Company-wide Automation Approval mode changes.

**Implementation impact**
- Store pending actions independently of the current mode and apply the policy version/effective time at generation and approval; never auto-run old pending work merely because the mode changed.

### ADDITION — Approval OFF permits only explicitly approved automation to auto-post

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Company-wide Automation Approval is OFF, a consequential financial posting may execute without per-action confirmation only if that specific automation is already explicitly approved for automatic execution in its owning workflow.
- When the setting is ON, each consequential automated action requires separate approval. Existing pending actions remain pending as specified above.

**Scope**
- Per-action confirmation for explicitly approved automations across modules.

**Preserve unchanged**
- Both modes retain operation-specific role authorization, Company/Branch scope, module gates, input validation, atomicity, idempotency and audit. OFF does not invent a business rule, create a financial event without real source evidence, or change manual actions that are not configured for automation.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Level 4 requires a separate human confirmation for every consequential financial event, only for a workflow explicitly approved for automatic execution while Company-wide Automation Approval is OFF. Manual actions and all unsupported or unapproved automations remain human-confirmed or blocked under their existing rules.

**Implementation impact**
- Keep explicit workflow approval separate from the Company mode toggle. The backend may skip per-action confirmation only after checking the workflow's approved-automation configuration and all existing authorization/data-integrity guards.

### ADDITION — Fund Credit uses the actual receipt date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Fund Credit's effective date is the date the money was actually received. An Accountant may enter a past actual receipt date when recording it late; a future effective date is not allowed.

**Scope**
- Investor Fund Credits and their linked Accounting capital-inflow/Cash/Bank movement.

**Preserve unchanged**
- The immutable record-creation/audit timestamp continues to show when the entry was made. The effective receipt date does not rewrite the actual time the system recorded the entry.

**Supersedes**
- None; this resolves the previously unspecified late-entry and future-date handling for Fund Credits.

**Implementation impact**
- Keep the Fund Credit and its linked Accounting movement on the same actual-receipt effective date; preserve a separate creation timestamp. Backdated entries affect historical ledger views and the Investor's effective-date-based calendar. The API's timezone and time-of-day representation remains a technical contract to lock.

### ADDITION — Correcting a Fund Credit assigned to the wrong Investor

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If the actual transfer was received correctly but its Fund Credit was assigned to the wrong Investor, preserve the original record and audit history and append an audited correction that moves the Fund amount from the wrong Investor to the correct Investor.
- Keep the real Cash/Bank movement recorded exactly once; the attribution correction does not create another receipt or cash movement.

**Scope**
- Correction of the Investor attribution for an existing confirmed Fund Credit when the actual incoming transfer remains valid.

**Preserve unchanged**
- Fund Credit and Accounting history remain append-only. Preserve the one-transfer/one-Fund-Credit rule, original Branch provenance, and Accounting's ownership of the actual Cash/Bank movement.

**Supersedes**
- None; this specifies the previously unresolved correction behavior for a Fund Credit posted to the wrong Investor.

**Implementation impact**
- Use an append-only typed attribution-correction record linked to the original Fund Credit; do not edit or delete the original credit or reassign its Accounting movement. Correction authority, partial-correction scope and the correction's effective-date treatment remain to be decided before implementation.

### ADDITION — Branch authority for wrong-Investor Fund Credit correction

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may correct a Fund Credit only when its source Branch is within that Accountant's authorized Branch scope.
- A Company-level Accountant may correct a Fund Credit from any Branch within the same Company.

**Scope**
- Authorization for the append-only correction that changes a valid Fund Credit's Investor attribution without changing its actual Cash/Bank movement.

**Preserve unchanged**
- Enforce Company isolation and the original Fund Credit's Branch provenance. This Investment correction authority does not grant cross-Branch permission in other modules; Owner and Platform Back Office receive no new correction authority.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: who may authorize a wrong-Investor Fund Credit attribution correction.

**Implementation impact**
- Authorize against the original source Fund Credit's Branch for Branch Accountants and same-Company scope for Company-level Accountants. Never trust a client-selected Branch as authorization.

### ADDITION — Wrong-Investor Fund Credit correction moves the whole credit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A wrong-Investor attribution correction moves the entire original Fund Credit amount to the correct Investor. Do not split one Fund Credit between Investors.

**Scope**
- The append-only attribution correction for a valid actual transfer recorded against the wrong Investor.

**Preserve unchanged**
- Keep the original Fund Credit and audit history, its Branch provenance, and its single actual Cash/Bank movement. This correction changes attribution only and creates no second receipt.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether a wrong-Investor Fund Credit correction may move only part of the original credit. This follows the approved Q66 rule that one actual transfer funds one Investor only.

**Implementation impact**
- The correction record must reference the original Fund Credit and equal its full amount; reject partial attribution splits. Preserve Q69's Branch Accountant source-Branch limit and Company-level Accountant same-Company scope. The correction effective date remains unresolved.

### ADDITION — Wrong-Investor Fund Credit correction uses the original receipt date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The correction is effective on the original Fund Credit's actual money-received date. Recalculate the affected historical Investor calculations and preserve their prior versions and audit history.
- Do not change the actual Cash/Bank movement or its original receipt date.

**Scope**
- Effective date and historical calculation treatment for a full wrong-Investor Fund Credit attribution correction.

**Preserve unchanged**
- Keep the original Fund Credit, accounting movement, creation/audit timestamps, and prior calculation history. This does not apply Company Profit rules to Investor Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which effective date governs a wrong-Investor attribution correction.

**Implementation impact**
- Append the correction with a link to the original actual receipt date and recompute affected Investor periods with immutable calculation/revision history. How an already-paid or settled amount is adjusted remains a separate BUSINESS DECISION REQUIRED item.

### ADDITION — Restatement differences remain separate Investor adjustments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When a wrong-Investor correction restates a historical Investor calculation, preserve the prior calculation and actual payment records and record the resulting difference as a separate audited adjustment.
- If more Profit was due than was paid, add the unpaid difference to a later Investor Profit amount. If more was paid than the corrected calculation allows, deduct that overpayment from a later Investor Profit amount.

**Scope**
- Historical Investor Profit restatement differences caused by a Fund Credit attribution correction, and their application to later Investor Profit.

**Preserve unchanged**
- Do not rewrite or duplicate an actual Cash/Bank payment. Profit and its restatement adjustment remain separate from Company Income/Expense and Company Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: how an already reconciled/paid Investor Profit amount is adjusted after historical recalculation.

**Implementation impact**
- Keep the original calculation, payment, revised calculation, and separate adjustment linked in audit history. Any later cash payment remains a distinct authorized actual movement. Handling an unpaid overpayment balance when no future Profit is available or Exit occurs remains BUSINESS DECISION REQUIRED.

### ADDITION — Investor Exit may handle historical Profit overpayment flexibly

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- At Investor Exit, the Company may either collect the outstanding historical Profit overpayment before closure or allow the Exit to complete without collecting it, based on the case.

**Scope**
- Unoffset overpayment adjustments caused by an audited historical Investor Profit restatement after a wrong-Investor Fund Credit correction.

**Preserve unchanged**
- This flexibility does not alter ordinary Vehicle Loss, Fund principal, or other Exit settlement rules. No actual repayment is recorded unless money is received; no automatic Fund debit or cash event is created.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Exit must remain open until a historical Profit overpayment is collected in full.

**Implementation impact**
- Provide the approved case-specific Exit outcome without automatic recovery or write-off. The role authorized to choose, and whether an unpaid amount remains open or is waived after closure, remain BUSINESS DECISION REQUIRED.

### ADDITION — Unpaid restatement overpayment may remain open or be waived

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If the Company completes Investor Exit without collecting the outstanding historical Profit overpayment, it may either keep the amount as an open balance for later collection or waive it with a recorded reason. The choice is case-specific.

**Scope**
- Disposition after Exit of an unoffset overpayment adjustment caused by historical Investor Profit restatement.

**Preserve unchanged**
- Preserve the adjustment and Exit audit history. A waiver does not create a Cash/Bank movement or Company Income/Expense; an open balance is not automatically collected.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an unpaid residual after Exit must remain recoverable or may be waived, as left open by Q73.

**Implementation impact**
- Record the selected disposition and, for waiver, the reason. Which role may select or approve each disposition remains BUSINESS DECISION REQUIRED.

### ADDITION — Role authority for post-Exit restatement overpayment disposition

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may select the open-balance or waiver disposition only for an adjustment attributed to their authorized Branch.
- A Company-level Accountant may select the disposition for any Branch within the same Company.

**Scope**
- Authorization to retain open or waive an unpaid historical Investor Profit restatement overpayment after Exit.

**Preserve unchanged**
- This is specific to this Investment adjustment. It does not change Company isolation, the existing Company-level-only authority to complete cross-Branch Investor Exit, or permissions in other modules. Owner and Platform Back Office receive no new authority.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which Accountant role may select or approve the post-Exit overpayment disposition.

**Implementation impact**
- Authorize against the adjustment's original source Branch for Branch Accountants and same-Company scope for Company-level Accountants. A Branch Accountant disposition does not finalize an Exit spanning multiple Branches.

### ADDITION — Authority to record later repayment of an open post-Exit adjustment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record actual repayment of an open historical Profit overpayment only for an adjustment attributed to their authorized Branch.
- A Company-level Accountant may record repayment for an adjustment from any Branch within the same Company.

**Scope**
- Actual repayment collection against an open post-Exit Investor Profit restatement adjustment.

**Preserve unchanged**
- Record a cash movement only when money is actually received. This authority does not grant cross-Branch access to other modules or alter authority to finalize Exit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which role may record actual repayment against an open post-Exit restatement adjustment.

**Implementation impact**
- Link the actual receipt to the open adjustment and enforce same-Company/source-Branch permission. The Accounting event classification and typed source-link contract remain to be locked.

### ADDITION — repayment of post-Exit Investor Profit overpayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an Investor actually repays an open historical Investor Profit overpayment after Exit, record the amount received as an actual Cash/Bank Receipt and reduce the open overpayment by that received amount.
- This repayment is not new Company Income or Company Profit.

**Scope**
- Actual repayment against an open post-Exit Investor Profit restatement adjustment and its Accounting cash record.

**Preserve unchanged**
- Preserve the original Profit calculation, actual prior Profit payment, restatement adjustment, Exit history, and Q76 actor scope. Record no cash movement before actual receipt.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: Accounting classification of an actual post-Exit repayment of historical Investor Profit overpayment, only as to whether it is Company Income/Profit.

**Implementation impact**
- Record one actual Cash/Bank Receipt linked to the open adjustment; do not create Company Income. The typed source-link/API contract remains implementation design work.

### ADDITION — partial and multiple repayments of post-Exit overpayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An open post-Exit historical Investor Profit overpayment may be repaid through partial and multiple actual repayments.
- Each actual repayment reduces the open balance by the amount received; any remainder stays open for later repayment.

**Scope**
- Repayment schedule and outstanding balance for an open post-Exit Investor Profit restatement adjustment.

**Preserve unchanged**
- Apply Q77: each actual receipt is linked to the adjustment and is not Company Income/Profit. Apply Q76's role and Branch limits. Do not record a receipt before money is received.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the open post-Exit overpayment may be repaid in partial or multiple actual receipts.

**Implementation impact**
- Derive the remaining open amount from the adjustment and its linked valid actual receipts. Behavior when received amounts exceed the open balance remains unresolved.

### ADDITION — editing a saved post-Exit repayment entry

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An authorized Accountant may edit a saved post-Exit repayment entry through an edit action. The ordinary entry view shows the latest value; it need not display earlier versions.
- Preserve the original value and each correction in backend audit history. An explanatory note may be added when useful.
- Do not rewrite the actual Cash/Bank Receipt or movement. Any change to actual money received must be represented by a separately recorded actual cash event or approved correction process.

**Scope**
- User-facing editing and audit treatment of a saved post-Exit Investor Profit overpayment repayment entry.

**Preserve unchanged**
- Q76's role/Branch authorization, Q77's Receipt classification, Q78's partial/multiple repayment rule, and immutable actual cash history remain in force.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether a saved post-Exit repayment entry may be edited and whether its prior values must appear in the ordinary entry view.

**Implementation impact**
- Provide a current-value edit experience backed by append-only correction/audit history. Keep actual Receipt amount and movement immutable; the excess-receipt case remains unresolved.

### ADDITION — disposition of an excess post-Exit repayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If an actual Investor repayment exceeds the open post-Exit Profit overpayment, the authorized Accountant may choose case by case to retain the excess as an open amount due back to the Investor, or record a separate actual refund when the excess is returned.
- Preserve the original full Cash/Bank Receipt. A refund is recorded only after money is actually paid back; neither the excess nor its refund creates Company Income/Profit.

**Scope**
- Disposition of money received above the remaining open post-Exit Investor Profit overpayment.

**Preserve unchanged**
- Q76's role/Branch scope, Q77's Receipt classification, Q78's partial/multiple repayments, Q79's audit-preserving edit behavior, and immutable actual Receipt/refund movements remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: what to do with an actual repayment received above the open overpayment balance.

**Implementation impact**
- Let the authorized Accountant choose the per-case disposition. Persist excess due back to the Investor or link a separate actual refund outflow; preserve a typed audit/source link. Exact model/API contract remains architecture work.

### ADDITION — partial and multiple refunds of excess repayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An excess amount kept open as due back to the Investor may be refunded in partial and multiple actual payments.
- Record each actual refund separately. Each payment reduces the open amount due back; any remainder stays open.

**Scope**
- Actual return of excess Investor repayment retained as an amount due back to the Investor under Q80.

**Preserve unchanged**
- Preserve Q76-Q80 role, Receipt, disposition, audit, and immutable Cash/Bank movement rules. A refund is recorded only after money is paid back and does not create Company Income/Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an excess amount due back must be refunded in one payment or may be returned partially and repeatedly.

**Implementation impact**
- Link each actual refund outflow to the same due-back balance and derive its remaining amount from the individual recorded payments.

### ADDITION — record full Vehicle price before installments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Record the full approved Vehicle Purchase cost or agreed Sale price on its Purchase or Sale source record, regardless of whether any money has been paid or received.
- Permit partial and multiple actual installments against the source-specific seller payable, Buyer receivable, or refund payable. An installment may not exceed the current amount outstanding; an installment below the outstanding amount is valid and leaves the remainder open.
- Permit partial and multiple actual Buyer and seller refunds, each recorded only when money actually moves. An in-progress seller refund does not satisfy the existing requirement to receive the full excess before accepting a purchase-cost correction.
- Apply this installment pattern to another module only when that module has an authoritative full amount, a typed source obligation, and defined role/Branch permissions.

**Scope**
- Phase 5 Vehicle Purchase, Sale, seller payments/refunds, Buyer receipts/refunds, and equivalent already-defined source-owned obligations.

**Preserve unchanged**
- Purchase cost, agreed Sale price, source allocation, Company Income/Expense/Profit, and actual Cash/Bank events retain distinct meanings. Q76-Q81 permissions, refund history and correction audit remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Sale/Purchase refunds may be paid in installments and whether an installment below the full outstanding amount is valid. Existing source-specific total-price and overpayment rules remain in force.

**Implementation impact**
- Derive each source's open amount from its authoritative total and linked valid actual events; reject overpayment rather than clamping it. Keep a partial amount open until further actual installments or refunds settle it.

### ADDITION — saving the Sale form confirms the completed Sale

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A successful Save of the existing Sale form records the actual completed Sale as confirmed and makes it the authoritative Sold event for that Vehicle.
- Sale confirmation is independent of Buyer collection. The Buyer may still owe some or all of the agreed price.

**Scope**
- Phase 5's minimal Stock Vehicle Sale record and its Sold state.

**Preserve unchanged**
- Buyer Receipts remain separate actual Cash/Bank events. Sale confirmation does not imply full collection, Investor settlement, or eligibility for Vehicle deactivation while another required position remains open or unknown.

**Supersedes**
- None; this clarifies that successful Save of the existing Sale form confirms the actual Sale.

**Implementation impact**
- Persist a successful Sale-form creation as confirmed; keep collection status separate and do not add an independent manual Sold flag.

### ADDITION — Vehicle Management OFF blocks Buyer Receipts for existing Sales

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Buyer Receipt against a Stock Vehicle Sale may be recorded only while both Vehicle Management and Accounting are ON.
- If Vehicle Management is OFF, block a Buyer Receipt even when Accounting is ON; do not create an Accounting cash event or movement for it.

**Scope**
- Buyer Receipts against Sale records created before Vehicle Management was turned OFF.

**Preserve unchanged**
- Existing Sale and receivable history remain intact while blocked. This does not alter the separately approved pre-OFF Seller payable installment exception; new Sales remain blocked while Vehicle Management is OFF.

**Supersedes**
- None; this sets the module-OFF rule for Buyer Receipts without changing Seller payable handling.

**Implementation impact**
- Check the current Vehicle Management and Accounting module states before the Receipt command; do not record cash while either required module is OFF.

### ADDITION — Vehicle Management OFF blocks Seller refunds for existing Purchases

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Vehicle Management is OFF, block recording a Seller refund against an existing Vehicle Purchase even when Accounting is ON.
- Resume that linked refund workflow only after Vehicle Management is ON; do not create an Accounting event or AccountMovement while the command is blocked.

**Scope**
- Actual Seller refunds linked to Vehicle Purchases recorded before Vehicle Management was turned OFF.

**Preserve unchanged**
- Existing Purchase and funding history remain intact. This does not change the separately approved exception permitting installments on a pre-OFF Seller payable when Accounting is ON.

**Supersedes**
- None; this defines module-OFF handling for Seller refunds without changing the Seller payable installment exception.

**Implementation impact**
- Recheck Vehicle Management state on each Seller refund write; reject while OFF without posting any Accounting event or movement.

### ADDITION — Vehicle Management OFF blocks Buyer refunds for existing Sales

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Vehicle Management is OFF, block an actual Buyer refund against an existing Sale even when Accounting is ON.
- Resume the linked refund workflow only after Vehicle Management is ON; do not create an Accounting event or AccountMovement while the refund is blocked.

**Scope**
- Actual Buyer refunds linked to Stock Vehicle Sales recorded before Vehicle Management was turned OFF.

**Preserve unchanged**
- Existing Sale and refund obligation history remain intact. Q86 Buyer Receipt and Q87 Seller refund module-OFF rules remain separate; the pre-OFF Seller payable installment exception is unchanged.

**Supersedes**
- None; this defines Vehicle Management module-OFF behavior for Buyer refunds.

**Implementation impact**
- Recheck Vehicle Management and Accounting state on each Buyer refund write; reject while either required module is OFF without posting a cash event or movement.

### ADDITION — Vehicle Management OFF blocks existing Purchase cost corrections

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Vehicle Management is OFF, do not apply a Purchase cost correction to an existing Vehicle Purchase, even when Accounting is ON.
- Wait until Vehicle Management is ON before recording the audited correction.

**Scope**
- Corrections to the recorded cost of an existing Vehicle Purchase.

**Preserve unchanged**
- Retain the original Purchase and its history. This does not allow a new Purchase while Vehicle Management is OFF and does not change the pre-OFF Seller payable installment exception when Accounting is ON.

**Supersedes**
- None; this clarifies that the Purchase cost correction itself, as well as its linked Seller refund, waits for Vehicle Management to be ON.

**Implementation impact**
- Recheck Vehicle Management state at Purchase cost-correction write time; reject without changing Purchase allocations or history while OFF.

### ADDITION — Investment OFF blocks wrong-Investor Fund Credit corrections

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Investment is OFF, do not correct an existing Fund Credit that was attributed to the wrong Investor, even when Accounting is ON.
- Wait until Investment is ON before applying the audited attribution correction.

**Scope**
- Attribution correction of a preexisting Fund Credit to the correct Investor.

**Preserve unchanged**
- Preserve the original Fund Credit, its Branch provenance, audit history, and the single actual Cash/Bank movement. This does not alter the Company-wide Fund total or allow a new Fund Credit while Investment is OFF.

**Supersedes**
- None; this clarifies the Investment module-OFF behavior for wrong-Investor attribution corrections.

**Implementation impact**
- Recheck Investment state at correction write time; reject without changing credit attribution or cash history while OFF.

### ADDITION — Investment OFF blocks return of unused Fund principal outside Exit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Investment is OFF, do not return an Investor's unused Available Fund principal if no Exit request/settlement had already started before the OFF transition.
- Wait until Investment is ON before recording that standalone principal return.

**Scope**
- Return of available, unallocated Investor Fund principal when the Investor has no preexisting Exit in progress.

**Preserve unchanged**
- Preserve the Fund balance and original credit history while blocked. This does not change the previously approved rule allowing a Company-level Accountant to complete an Exit that had already started before Investment was turned OFF, with Accounting ON for actual money movement.

**Supersedes**
- None; this clarifies the Investment module-OFF rule for standalone unused-principal returns outside an existing Exit.

**Implementation impact**
- Recheck Investment state and pre-OFF Exit eligibility before principal-return writes; reject without changing Fund or Cash/Bank balances when Investment is OFF and no qualifying Exit was already open.

### ADDITION — Seller refunds cannot exceed net actual Purchase payments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The cumulative actual Seller refunds linked to a Vehicle Purchase cannot exceed the net amount actually paid to that Seller for the Purchase.
- Calculate the remaining refundable amount from confirmed Purchase installments less actual Seller refunds already received. Reject a refund above that amount.

**Scope**
- Actual Seller refunds linked to Vehicle Purchase payments.

**Preserve unchanged**
- A Seller refund remains a separately recorded actual Cash/Bank event. A Purchase cost correction is a separate manually authorized action linked to the same Purchase; neither action is inferred from the other.
- Preserve confirmed installments and their Accounting movements; do not create Company Income or an invented supplier-credit balance.

**Supersedes**
- None; this sets the maximum actual Seller refund against previously paid Purchase amounts.

**Implementation impact**
- Under the Purchase mutation lock, recompute confirmed net payments and prior actual refunds before posting; enforce the cap atomically.

### ADDITION — Investment OFF blocks Purchase cost correction

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- While Investment is OFF, do not apply a Vehicle Purchase cost correction that changes Investor Fund use/allocation. Wait until Investment is ON.

**Scope**
- Cost correction of an existing Vehicle Purchase and its Investor Fund allocations.

**Preserve unchanged**
- Preserve the original Purchase, allocations, Seller installments, actual refunds, and correction history while blocked.
- The existing Vehicle Management OFF rule for Purchase correction remains in force. An actual Seller refund remains a separate action subject to its Vehicle Management/Accounting module gates and approved net-paid cap.

**Supersedes**
- None; this adds the Investment module-OFF condition to the separately approved Vehicle Management condition.

**Implementation impact**
- Recheck Investment state and revision inside the Purchase correction transaction; reject without changing Purchase cost, allocations, or linked records while OFF.

### ADDITION — upward Purchase correction follows the original funding split

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an approved correction increases a Vehicle Purchase cost, allocate the increase using that specific Purchase's originally recorded Investor Fund and Company Running Capital proportions. The proportions are Purchase-specific; do not hard-code a universal 70:30 split or substitute the Investor Profit-share percentage.
- If the Investor Fund cannot cover its proportional increase, Company Running Capital supplies the exact shortfall, subject to the approved Purchase source-allocation and availability checks.

**Scope**
- Upward correction of an existing Vehicle Purchase and its source allocations.

**Preserve unchanged**
- Preserve the original Purchase allocation and append a correction with before/after source totals. The Investor Profit-share agreement remains separate from Purchase financing.
- Preserve the previously approved proportional decrease and balanced-paise/Fund-first rounding rule for downward corrections.

**Supersedes**
- None; this defines how an upward cost correction adds source allocations.

**Implementation impact**
- Calculate the incremental source amounts from the Purchase's stored allocation proportions using fixed-precision money; enforce the exact revised Purchase total and record any Investor Fund shortfall as Company Running Capital.

### ADDITION — all three modules must be ON for Purchase cost correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle Purchase cost correction requires Vehicle Management, Investment, and Accounting all to be ON, including a correction that records no new actual Cash/Bank movement.
- If any of these modules is OFF, wait until it is ON; do not change Purchase cost, source allocations, seller payable, or correction history.

**Scope**
- Manual audited correction to an existing Vehicle Purchase and its Investor Fund/Company Running Capital allocations.

**Preserve unchanged**
- Q89's Vehicle Management gate and Q93's Investment gate remain in force. Actual Seller refunds remain separate and follow their own gate and net-paid cap.

**Supersedes**
- None; this adds the Accounting module gate to Q89 and Q93.

**Implementation impact**
- Check the current Company module revisions for all three modules in the atomic correction command; reject without partial writes if any is OFF.

### ADDITION — Investment OFF blocks Buyer Receipts for Investor-funded Sales

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Do not record a Buyer Receipt against an existing Investor-funded Vehicle Sale while Investment is OFF, even if Vehicle Management and Accounting are ON. Wait until Investment is ON.

**Scope**
- Actual Buyer Receipts against an already confirmed Sale of an Investor-funded Stock Vehicle.

**Preserve unchanged**
- Q86 separately requires Vehicle Management and Accounting to be ON. This rule applies only to Buyer Receipts; the distinct Buyer refund rule is in Q99.

**Supersedes**
- None; this defines the Investment module-OFF condition for Buyer Receipts against Investor-funded Sales.

**Implementation impact**
- Recheck Investment, Vehicle Management, and Accounting revisions at posting; create no Sale Receipt or Cash/Bank movement while a required module is OFF.

### ADDITION — Phase 5 includes audited Sale price correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Include audited Sale price correction in Phase 5. A Branch Accountant may correct a Sale only within their authorized Branch; a same-Company Company-level Accountant may correct a Sale from any Branch in that Company.
- Keep the confirmed Sale, Buyer Receipts/refunds, and actual Cash/Bank events traceable; recompute the current receivable/refund position under the existing V2 Sale rules.

**Scope**
- Correcting the agreed price of a confirmed Phase 5 Stock Vehicle Sale.

**Preserve unchanged**
- Sale confirmation and Buyer Receipt retain Q85's Branch scope. Corrections do not create, change, or delete actual cash events. The approved partial-installment warning and excess rejection remain in force.

**Supersedes**
- SUPERSEDES EARLIER PHASE 5 SCOPE STATEMENT: Sale price correction was deferred. Later approvals include Sale price correction and Buyer refunds in Phase 5; other Sales/CRM deferrals remain unchanged.

**Implementation impact**
- Use an audited linked correction, enforce the Sale's Company/Branch scope server-side, and recalculate the current Sale position from authoritative linked events.

### ADDITION — Sale price correction requires Vehicle Management and Accounting ON

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Sale price correction requires Vehicle Management and Accounting ON. Investment may be OFF; that status alone does not block the Sale correction.

**Scope**
- Audited price correction to a confirmed Sale of an Investor-funded Stock Vehicle.

**Preserve unchanged**
- Q97's Sale correction role scope remains in force. This is the user's latest Q98 answer and replaces the earlier same-turn response that required Investment to be ON as well.

**Supersedes**
- SUPERSEDES EARLIER Q98 RESPONSE: the first answer requiring all three modules ON. The repeated Q98 answer requires Vehicle Management and Accounting ON; Investment OFF does not block the correction.

**Implementation impact**
- Recheck Vehicle Management and Accounting revisions at correction time. Do not treat the Sale correction as a Buyer Receipt, refund, Fund posting, or Profit payment.

### ADDITION — Buyer refunds do not require Investment ON

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Buyer refund against an Investor-funded Sale may be recorded when Vehicle Management and Accounting are ON, even if Investment is OFF.

**Scope**
- Actual partial or full Buyer refunds against an existing Investor-funded Stock Vehicle Sale.

**Preserve unchanged**
- Vehicle Management and Accounting remain required for the actual refund. Q96's Buyer Receipt rule still requires Investment ON; the refund rule does not authorize a Buyer Receipt while Investment is OFF.

**Supersedes**
- None; this defines Investment-OFF behavior for Buyer refunds without changing the separate Buyer Receipt gate.

**Implementation impact**
- Record the actual refund through the Sale and Accounting source records. Refresh Investor calculations from those sources under Q100; do not create an Investor Profit payment as a side effect of recalculation.

### ADDITION — refresh Investor calculations from Sale source records while Investment is OFF

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- If an approved Sale price correction or actual Buyer refund is recorded while Investment is OFF, refresh Investor calculations from the authoritative Sale, receipt, refund, and Accounting source records.
- Do not create or post an Investor Profit payment as part of that recalculation.

**Scope**
- Derived Investor calculations affected by the Q98 Sale price correction or Q99 Buyer refund while Investment is OFF.

**Preserve unchanged**
- Actual Cash/Bank events remain Accounting-owned; the Q96 Buyer Receipt gate still applies. Recalculation alone creates no separate cash event or settlement.

**Supersedes**
- None; this defines the derived-calculation effect for the approved Q98/Q99 operations while Investment is OFF.

**Implementation impact**
- Recompute affected derived views from current source history. Do not infer an Investor Profit payment from a changed calculation.

### ADDITION — Phase 5 direct Vehicle expenses; Garage Job expenses deferred

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 5 includes expenses entered directly against a Stock Vehicle, such as repair, service, or transport costs. Costs entered against a Garage Job remain in the later Garage phase.
- Include each approved direct Vehicle Expense once in that Vehicle's total cost; actual Cash/Bank movements remain separately recorded through Accounting and linked to their originating record.

**Scope**
- Direct Vehicle Expense entry and Vehicle cost aggregation in Phase 5; Garage Job-linked cost entry in the later Garage phase.

**Preserve unchanged**
- Existing Expense/Payment separation and partial-payment limits remain. Vehicle Expense, Investor Fund, Company Running Capital, Company Income/Expense, and actual Cash/Bank movements retain distinct ownership and meaning.

**Supersedes**
- None; this defines Phase 5 scope for direct Vehicle expenses and leaves Garage Job costs deferred.

**Implementation impact**
- Provide a Vehicle-linked expense source and connect actual cash events to Accounting once. Do not create a second cash movement or a partial Garage Job workflow.

### ADDITION — Vehicle cost funding and customer-bill boundary

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- For a direct cost of an Investor-funded Stock Vehicle, apply available Investor Fund first. Record any uncovered shortfall as a separate Company Running Capital contribution linked to that Vehicle; do not overdraw Investor Fund.
- Do not also classify the same Stock Vehicle-specific cost as Company Accounting Expense solely because Company Running Capital covered part of it.
- A cost of a customer's Vehicle belongs on that customer's Garage Job bill. Garage Job expense/billing remains deferred to the Garage phase.

**Scope**
- Funding and classification of direct Phase 5 Stock Vehicle costs, plus the customer-vehicle Garage boundary.

**Preserve unchanged**
- Q102 Phase 5 direct Vehicle Expense scope remains. Actual Cash/Bank movements remain Accounting-owned and recorded once. Garage Job and customer billing workflows remain deferred; existing Company result rules for other sources remain in force.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION WORDING: applying the generic Company Accounting Expense/Payment classification automatically to a direct Stock Vehicle cost. This does not remove the requirement to record actual money movements through Accounting.

**Implementation impact**
- Store Vehicle cost and its Investor Fund/Company Running Capital source allocation separately from Company Income/Expense. Link any actual cash movement once to the typed Vehicle cost source; enforce available Fund and exact Company shortfall atomically.

### ADDITION — module gates for direct Stock Vehicle Expense

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Saving a direct expense and its Investor Fund/Company Running Capital source allocation for an Investor-funded Stock Vehicle requires Vehicle Management and Investment ON.
- Accounting is required when an actual Cash/Bank payment is recorded. If Accounting is OFF, the expense and source allocation may be saved without creating a cash event; actual payment must wait.

**Scope**
- Phase 5 direct Investor-funded Stock Vehicle Expense creation, source allocation, and actual payment module gates.

**Preserve unchanged**
- Q103's Investor Fund-first and exact Company Running Capital shortfall rule remains. Vehicle Purchase funding still follows its separate all-three-module gate; Purchase cost correction remains gated by Vehicle Management, Investment, and Accounting. Customer Vehicle billing remains Garage-phase scope.

**Supersedes**
- SUPERSEDES EARLIER Q102 UNRESOLVED GATE: which modules must be ON to save a direct Vehicle Expense/source allocation. This does not change the separate module gate for actual cash movement.

**Implementation impact**
- Validate Vehicle Management and Investment revisions for the expense/allocation write. Validate Accounting at actual payment posting and create no Accounting event while it is OFF.

### ADDITION — record full Vehicle Expense and derive unpaid payable

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Record the full approved direct Stock Vehicle Expense when the bill/cost is incurred, regardless of how much has been paid.
- Derive the unpaid payable from the full Vehicle Expense less its confirmed actual linked payments. Allow partial and multiple payments; reject any payment above the current outstanding amount.
- Count the approved Vehicle Expense once in Vehicle total cost. Later payments settle the payable and do not add the same cost to Vehicle total a second time.

**Scope**
- Direct Phase 5 Stock Vehicle Expenses and their partial/multiple actual payment settlements.

**Preserve unchanged**
- Q103 Investor Fund-first/Company Running Capital shortfall source allocation remains; the Vehicle cost is not a Company Accounting Expense. Q104 module gates remain. Actual cash movement is recorded once through Accounting; customer Garage Job expenses remain deferred.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION AMBIGUITY: whether a direct Vehicle Expense must be fully paid before it is recorded or may have a source-owned open payable. It does not change Q103's separation from Company Accounting Expense.

**Implementation impact**
- Store the full Vehicle Expense once, derive its outstanding payable from linked confirmed payments, and keep each actual payment as a separate typed Accounting-linked event.

### ADDITION — Vehicle Expense correction waits for actual vendor refund

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- If reducing a direct Vehicle Expense after actual payments would mean that more was paid than the corrected cost, do not apply the cost correction until the vendor has actually refunded the excess and Accounting has recorded that refund.
- Keep the original Vehicle Expense and payment history; record the actual vendor refund as its own linked Accounting movement.

**Scope**
- Downward correction of a Phase 5 direct Stock Vehicle Expense after actual payment has occurred.

**Preserve unchanged**
- Q105 full-cost/payable and partial-payment rules, Q103 funding-source distinctions, Q104 module gates, and Q107/Q108 payment-reference rules remain. No supplier credit or balancing Company Expense is inferred.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether a Vehicle Expense correction creating an overpayment may proceed before the vendor's actual refund is received.

**Implementation impact**
- Validate net confirmed payments/refunds before the correction; reject atomically until the required refund cash event is recorded. Preserve the original event and append the correction.

### ADDITION — reapply Investor Fund-first rule after Vehicle Expense correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- After a permitted Vehicle Expense cost correction, calculate the corrected source allocation anew using the existing order: available Investor Fund first, then Company Running Capital for the exact shortfall.
- Do not preserve the original Investor Fund/Running Capital ratio for a Vehicle Expense correction. If enough Investor Fund is available, allocate the corrected cost to Investor Fund; otherwise use the Fund up to availability and Company Running Capital for the remainder.

**Scope**
- Source reallocation after a downward correction to a direct Phase 5 Stock Vehicle Expense, after Q109's required actual vendor refund is recorded.

**Preserve unchanged**
- Preserve original source allocations and append audited adjustments. Q94's proportion-preserving rule applies to Vehicle Purchase corrections only and remains unchanged. Q103 no-overdraft and actual-movement rules remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q109 IMPLEMENTATION ITEM: how to reduce Investor Fund and Company Running Capital allocation after a corrected Vehicle Expense.

**Implementation impact**
- Revalidate available Fund at correction commit, allocate Fund first, apply only the exact shortfall to Company Running Capital, and append fixed-precision adjustment records without rewriting history.

### ADDITION — all modules required for Vehicle Expense correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- After Q109's required actual vendor refund is recorded, a Vehicle Expense cost correction and its Q110 Fund/Running Capital reallocation require Vehicle Management, Investment, and Accounting all ON—even if the correction itself makes no new Cash/Bank movement.
- If any module is OFF, do not change the Expense, payable, source allocations, or history.

**Scope**
- Downward correction of a direct Investor-funded Stock Vehicle Expense and its source allocation after an actual vendor refund.

**Preserve unchanged**
- Q104's Vehicle Management + Investment gate for saving a new Expense/allocation, with Accounting required for actual payment, remains. Q109 refund-before-correction and Q110 Fund-first reallocation remain. Purchase and Purchase-correction gates remain their separate rules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q110 IMPLEMENTATION ITEM: module gate for applying the corrected Vehicle Expense and reallocation after refund.

**Implementation impact**
- Recheck all three module revisions inside the correction transaction; reject atomically with no partial correction if any is OFF.

### ADDITION — Company-funded Stock Vehicle costs

**Status:** APPROVED BUSINESS DECISION CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- If a Stock Vehicle direct cost has no Investor Fund source, fund the entire cost from Company Running Capital linked to that Vehicle. Do not create or consume an Investor Fund allocation for it.
- Customer Vehicle costs remain Garage Job/customer-bill costs for the later Garage phase.

**Scope**
- Source classification for direct Stock Vehicle costs with no Investor Fund allocation.

**Preserve unchanged**
- Q103 Investor Fund-first plus exact Company Running Capital shortfall remains for Investor-funded Stock Vehicle costs. Actual Cash/Bank movement remains Accounting-owned and is recorded once.

**Supersedes**
- None; this makes explicit the already approved Q103 answer for a Stock Vehicle with no Investor Fund source.

**Implementation impact**
- Represent the full direct Vehicle cost as Company Running Capital when no Investor Fund source is assigned; do not require a synthetic Investor allocation.

### ADDITION — Company-funded Stock Vehicle expense module gate (Q115)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- For a direct Stock Vehicle expense funded entirely by Company Running Capital, Vehicle Management must be ON to record the cost. Investment need not be ON when no Investor Fund is used. Accounting must be ON for an actual payment.

**Scope**
- Direct expenses of Stock Vehicles with no Investor Fund source.

**Preserve unchanged**
- Investor-funded expense gates from Q104 remain Vehicle Management + Investment for cost/source records, with Accounting required for actual payment. Customer Vehicle expenses remain Garage Job scope.

**Supersedes**
- None; this decides the module gate for the Q103 Company-funded case.

**Implementation impact**
- Gate the cost record by Vehicle Management; require Accounting only for a cash movement and do not require an Investor Fund write.

### ADDITION — Vendor refund module gate and amount (Q116–Q117)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Recording an actual Vendor refund against a Vehicle Expense requires Vehicle Management, Investment, and Accounting all ON.
- No maximum refund amount based on prior Vendor payments is approved. Do not cap a recorded actual refund by the amount previously paid without a separate rule.

**Scope**
- Actual Vendor refunds linked to direct Phase 5 Stock Vehicle Expenses.

**Preserve unchanged**
- Q109 still requires an actual refund to be recorded before a downward correction would reduce the Expense below net actual payments. Q111 correction gates remain.

**Supersedes**
- None; these are the approved module and amount rules for Vehicle Expense Vendor refunds.

**Implementation impact**
- Require all three module states at refund posting. Handling or classifying an amount greater than net payments remains unresolved.

### ADDITION — One Investor Fund per Vehicle and upward Vehicle Expense correction (Q119–Q120)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Use only one Investor's Fund for a Vehicle.
- Allow a direct Vehicle Expense to be corrected upward when an additional Vendor bill is established. Recalculate source allocation Fund-first from available Investor Fund, then assign the exact shortfall to Company Running Capital; update the derived payable to the corrected amount.

**Scope**
- Investor Fund source count for a Vehicle and upward corrections to direct Stock Vehicle Expenses.

**Preserve unchanged**
- Q103/Q110 Fund-first order, no Fund overdraft, and separate Company Running Capital remain. The one-Fund rule does not merge Investor Fund with Company money.

**Supersedes**
- None; this resolves the multiple-Investor and upward-correction questions for this scope.

**Implementation impact**
- Reject a second Investor Fund source for a Vehicle; append a cost correction and source-allocation adjustment rather than overwriting history.

### ADDITION — Downward correction gate without Vendor refund (Q121)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Even when a downward Vehicle Expense correction does not require a Vendor refund because no actual payment has been made, require Vehicle Management, Investment, and Accounting all ON.

**Scope**
- Downward direct Vehicle Expense corrections where Q109's refund condition is not triggered.

**Preserve unchanged**
- Q111's same three-module gate after a required Vendor refund remains. Q104's gate for creating a new Expense is unchanged.

**Supersedes**
- None; this adds the no-refund correction case to the approved correction gate.

**Implementation impact**
- Validate all three module states before applying the cost and source-allocation correction.

### ADDITION — Historical effective date for Vehicle Expense correction (Q122)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Apply a Vehicle Expense correction to the original Expense effective date and the affected historical Investor calculation period; separately retain the actual correction timestamp in audit history.

**Scope**
- Historical effect of direct Vehicle Expense corrections on derived Investor calculations.

**Preserve unchanged**
- Actual Vendor refund keeps its true receipt date and Accounting movement. Investor period rules remain separate from Company Profit calendar windows.

**Supersedes**
- None; this defines the effective-period treatment for Vehicle Expense corrections.

**Implementation impact**
- Keep effective date and correction-recorded timestamp distinct; recalculate the affected Investor result from source records without altering historical cash movements.

### ADDITION — Vehicle Expense refund reference and excess allocation (Q118/Q123)

**Status:** APPROVED BUSINESS DECISION — LATEST CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Vendor refund against a direct Vehicle Expense does not require an operator-entered external reference. Do not reject it for a missing reference or duplicate reference.
- Record the full actual cash received once. Apply only the amount supported by the remaining net actual payments as a Vehicle Expense refund; let the Accountant choose another appropriate record for any excess. Do not automatically classify the excess as Company Income.

**Scope**
- Actual Vendor refunds against Phase 5 direct Stock Vehicle Expenses, including a refund larger than the net amount previously paid.

**Preserve unchanged**
- Q107/Q108 external-reference requirements and uniqueness apply to Vehicle Expense installments only. Q117 permits actual refunds without a cap based on prior payments; Q123 limits the amount applied to the Vehicle Expense and routes excess separately. Q109 actual refund-before-correction rule remains.

**Supersedes**
- SUPERSEDES EARLIER Q118 ANSWER: requiring an external reference and duplicate-reference rejection for Vehicle Expense Vendor refunds only. Payment-reference rules remain unchanged.
- SUPERSEDES EARLIER Q123 DETAIL only where it required one fixed record type/reason for the excess; the Accountant selects another appropriate record through the provided option.

**Implementation impact**
- Preserve one actual Cash/Bank movement and provide a manual destination choice for the excess portion. Do not create a second cash event or automatic Company Income; typed allocation/API details remain technical work.

### ADDITION — Phase 5 Vehicle funding and refund destinations (Q124–Q131)

**Status:** APPROVED BUSINESS DECISIONS

- If an actual Vehicle Expense refund is greater than the remaining amount that can be applied to that Expense, every rupee of the actual receipt must be allocated to explicitly selected eligible records. If no eligible destination exists, do not save/post the refund until the destination record is available. Never auto-classify the excess as Company Income.
- The Accountant may explicitly classify an excess as Company Income only by creating a separate Income record with an explicit category and note, then linking the actual Receipt to that record. This increases Company Profit once; never edit the old Income event or create this classification automatically.
- Investor Fund allocation for a Vehicle Purchase or Investor-linked Vehicle Expense is Company-level Accountant-only. No pending Branch Accountant draft may reserve pooled Fund.
- A Company Running Capital-only Vehicle Purchase may be created by a Branch Accountant for their authorized Branch or by a Company-level Accountant for any Branch in that Company. It requires Vehicle Management + Accounting; Investment is not required.
- Record the exact Company Running Capital amount needed for the Vehicle cost; no pre-funded Company pool is required. Actual cash remains a separate Accounting movement and is recorded only when money moves.
- Company-only Vehicle Purchase uses Vehicle Management + Accounting. A Purchase using Investor Fund requires Vehicle Management + Investment + Accounting.
- An Investor-funded Vehicle Expense is created and fully allocated by a Company-level Accountant. A Branch Accountant cannot create that Investor-linked expense.
