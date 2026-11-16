# 04 — Data Model & Relationships

Status: DRAFT V2 — conceptual data source after approval

## Identity, Company ownership and attribution

Every persistent business/system record uses an immutable backend-generated UUID or equivalent opaque globally unique identity. Names, phone numbers, registration numbers, Branch names, labels and storage URLs are editable attributes, not identity. Financially or legally meaningful timestamps are timezone-aware and denote an unambiguous instant.

| Concept | Scope and essential relationship |
|---|---|
| Platform | Control plane containing independent Companies; no shared Company financial ledger |
| Company / Tenant | Business ownership and data-isolation boundary; one Company has many Branches and one consolidated accounting system |
| Branch / Garage / Location | Operational attribution inside one Company; may be current Vehicle location or origin of a Job, Expense, receipt or other transaction |
| User, Role, Membership | System identity with explicit historical Company and Branch assignments; identity alone gives no business-data access |
| Business Owner / distribution recipient | Company-authorized recipient with effective, versioned Owner distribution configuration |
| Investor and Investor Fund | Company-level investment relationship across its Branches; one Investor may fund many Stock Vehicles; Fund and agreement do not belong to a Branch |
| Vehicle aggregate | Vehicle Management-owned immutable Company-wide UUID, lifecycle, current Branch/location and movement history; Platform Core supplies shared identity/scope primitives but is not a Vehicle writer |
| Investor responsibility | Vehicle-side Company/Vehicle-to-Investor responsibility reference with ACTIVE/ENDED state, effective time, actor, reason and retained history; ending is not a Fund, payment or settlement event |
| Funded Stock Vehicle context | One Vehicle aggregate with at most one active funding-Investor responsibility; Investment owns the Investor/Fund and financial events |
| External-customer Garage context | The same Vehicle UUID may later support a customer Garage Job after Investor responsibility ends; the Job needs no active Investor and no former-Investor financial effect |
| Vehicle Movement | Vehicle Management-owned source/current Branch, authorized action, time and history; does not duplicate or rewrite Vehicle identity |
| Garage Job / work entry | One Company, relevant Branch, Vehicle UUID, explicit per-Job context, OPEN/COMPLETED status with reopen history, work, Labour/materials, Job cost, customer charge and history; links to Accounting receipt identifiers without storing a second receipt |
| Job service-contact context | Job-scoped Name and Phone only; not proof of legal Vehicle ownership or payer identity; phone is not a unique key; no CRM or deduplication lifecycle; requiredness follows a verified workflow contract |
| Expense Category / Expense | Company classification with Branch attribution where relevant; approved Vehicle Expense belongs to one Vehicle and source funding is traceable |
| Buyer and Stock Vehicle Sale | Buyer identity within Company; Sale linked to one Stock Vehicle and current agreed price; Buyer phone is required but not unique identity |
| Buyer Payment / refund | Individual actual receipt and separately confirmed actual refund, each linked to Sale and correction history |
| Company Ledger / receipt / payment | Accounting-owned actual Company receipt/payment and Garage Revenue source, with Branch attribution; each Garage receipt requires an operator-supplied reference unique Company-wide across Branches; a Garage Job references the authoritative event and does not create a second cash record |
| Running Capital contribution/recovery | Exact actual Company-funded amount linked to one Stock Vehicle, source, Branch context, time and subsequent separately confirmed capital recovery; never Investor principal, Profit or Company Income |
| Investor positive-share agreement / snapshot | Investor-specific protected effective percentage configured by Platform Back Office and completed positive-result snapshot, with Company Share derived as applicable remainder; current business standard may be configured as 33% without forcing every Company |
| Monthly Business Cycle / Interim Payout | Investor-specific cycle day, effective rate and eligible-principal basis; suggestion and confirmed actual payment are distinct |
| Investor reconciliation / recoverable | Configured six-month/annual period; earned Profit, confirmed earlier payments and one current payable/recoverable position with partial settlement history |
| Company result / Owner Distribution | Company period result, confirmed distributable amount, effective recipient split, proposed allocations and separately confirmed actual payments |
| Investor Exit / Settlement | Company-level lifecycle and financial closure spanning the Investor's Stock Vehicles in that Company |
| Media Asset / publication | Vehicle-linked with Company and current/relevant Branch context; publication separate from core lifecycle |
| Configuration / module state / audit / correction | Effective Company or Platform scope, version, actor, time, reason and linked original/current position; protected Investor/Owner percentages and business rates are changed only through authorized Platform Back Office actions |

An Investor, Fund, Stock Vehicle, Buyer, Job or Ledger record of one Company must never become another Company's record merely because a Platform user can see both. Whether one human Investor or Owner may have separate Company relationships does not authorize a cross-Company financial balance.

## Authoritative financial sources

| Position | Authoritative basis |
|---|---|
| Investor supplied principal | Confirmed initial/additional funding and linked corrections in the Company-scoped Investor Fund history |
| Investor Available/committed principal | Valid Fund use/recovery/settlement events and current reservations or unresolved positions; derived, never manually overwritten |
| Company Running Capital | Actual Company contribution and separately confirmed capital recovery events linked per Stock Vehicle, separate from Investor Fund, Profit, Company Income and Company Share |
| Stock Vehicle cost | Purchase cost plus valid approved Vehicle and Garage Job cost sources, counted once regardless of module view or source of funding; an Accounting payment/settlement reference does not create a second cost |
| Sale price and Buyer receivable | Authoritative agreed Sale and individually confirmed Buyer payments/refunds, including linked Sale corrections and open refund payable |
| Positive Investor and Company Share | After full Buyer collection, reconciled Investor principal and exact Company Running Capital contribution/recovery are capital positions; the remaining actual positive economic result is allocated under the effective Investor percentage and completed snapshot, with confirmed adjustments separate and no capital recovery counted again as Profit |
| Interim Paid | Only actual confirmed Monthly Interim Payout transactions, not reminders or suggestions |
| Investor recoverable | Confirmed interim overpayment relative to reconciled earned entitlement, less actual direct repayment and separately confirmed future-Profit adjustments; no duplicate or negative open position |
| Garage charge / receivable | Garage-owned agreed Job charge; outstanding is derived from the charge and linked valid Accounting receipts/corrections |
| Garage receipt / revenue | Accounting-owned actual Company receipt and Company Garage Revenue representation linked to the Garage Job; the same receipt has one cash effect |
| Labour | Approved Vehicle/Job Labour cost is distinct from a worker's actual Company/Branch Labour Payment |
| Company Profit/Loss and Owner distribution | Company-level classified sources, period result, approved distributable position, effective recipient split and confirmed distribution payments |
| Manual Loss impact | Explicit confirmed manual Investor/Company decisions and actual related transactions with reason; no automatic allocation or posting from a negative arithmetic result |

Reports, dashboards, caches and projections are derived and rebuildable; they cannot compete with their source transactions. Money is current INR, final posted amounts use fixed-precision decimal at two places with `ROUND_HALF_UP`, and binary floating point is not an authoritative money or percentage representation. Do not count one receipt, recovery, Expense, interim payment or Company Share twice because it appears in multiple views.

## Vehicle, Branch and module history

Vehicle Management owns one Company identity through all Branch moves and context changes. Its current Branch changes by an audited movement; prior Jobs, Expenses and source Branch attribution remain on their original events. Authorized same-Company users may read previous-Branch history. Phase 6 Garage cross-Branch mutation is default-deny; no cross-Branch correction grant is added. With Garage OFF, new Jobs, Job expansion and unrelated new charges are denied; authorized history remains readable and existing-obligation actions remain with the authoritative module and its normal permission. Re-enabling uses retained records.

## Investor, Company and Owner relationships

One funded Stock Vehicle has one active Investor responsibility. That responsibility can be explicitly ended with effective time, actor and reason; the relationship and financial history remain, and open obligations are resolved by their authoritative module. Ending does not permit later customer Garage work on the same Vehicle UUID to affect the former Investor. External-customer Garage work does not require Investor responsibility. Investor-specific positive percentages and protected monthly rates have effective history administered by Platform Back Office; Accountant uses their approved effective values without independently changing protected configuration. A completed positive Vehicle allocation retains its applicable configuration snapshot. Company Share is a Company financial source, not an Owner receivable. Owner allocations use a separate Platform Back Office-managed Company-level distribution configuration and period snapshot. Historical percentage and actual payment events survive later configuration changes. Configuration confirmation and actual Company financial posting are distinct actions with distinct permissions.

## Corrections, retention and integrity

Do not hard-delete a Sold Vehicle, finalized Sale, confirmed payment, financial correction, Fund transaction, movement, Job financial record, distribution or relevant audit history. A legitimate edit before finalization may be direct where safe; finalized/paid facts use linked correction, reversal or adjustment with source, actor, timezone-aware time, prior/new values and reason. Repeated corrections reconcile one current position from gross events, confirmed reversals, actual payments/refunds/recoveries and open adjustments. An amount already settled has no second economic effect. Financial writes enforce nonnegative authoritative open positions, Tenant/Branch consistency, atomicity and duplicate/concurrency protection.

## Unresolved financial definitions

- **BUSINESS DECISION REQUIRED:** Specify the exact eligible-principal basis for a Monthly Interim Payout and how an authorized partial principal withdrawal can occur without using locked/unrecovered capital.
- **BUSINESS DECISION REQUIRED:** Specify manual Loss impact on Investor principal claim and Company money, and the precise Company distributable-Profit basis. Until then, no automatic formula may invent these positions.

## Approved Business Decision Additions

### ADDITION — Income, Expense, Receipt, and Payment have distinct source meanings

**Status:** APPROVED BUSINESS DECISION<br>

**Effective documentation state:** Current V2 addition

**Rule**
- Company Profit/Loss is derived from recognized/committed Accounting Income minus recognized/committed Accounting Expense.
- Receipt and Payment are actual cash events, separate from Income and Expense. One Income may have multiple partial Receipts and one Expense may have multiple partial Payments.
- Reject a Receipt or cumulative Expense Payments that exceed the target's current outstanding amount. Do not create automatic customer credit, unapplied receipt, prepayment, supplier credit, or balancing transactions.

**Scope**
- Company Accounting records, applications, and Company/Branch result projections.

**Preserve unchanged**
- Company and Branch identity, source-module ownership, immutable UUIDs, and one economic source counted once remain unchanged.

**Supersedes**
- None. This clarifies the relationship among the existing record types.

**Implementation impact**
- Keep classification records, cash-event identities, applications, and derived reports as separate data relationships.

### ADDITION — Company Profit periods are derived calendar reports

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Company/Owner Profit reports support monthly views, H1 January 1–June 30, H2 July 1–December 31, and Annual January 1–December 31. Annual is independently calculated over the full calendar year.
- Report generation does not close, reset, consume, settle, distribute, or prevent another period calculation. Company period rules do not apply to Investor Profit.
- A later Income/Expense correction restates the corrected economic result into its original effective reporting period while retaining the correction timestamp and immutable history.

**Scope**
- Derived Company/Owner result views, including authorized Branch attribution.

**Preserve unchanged**
- Reports remain derived and rebuildable; Investor reconciliation, Company distributable-Profit rules, and financial history remain distinct.

**Supersedes**
- None. Existing BDRs for distributable basis and period close/carryforward remain.

**Implementation impact**
- Do not create persistent Profit-period or close records solely for these reporting windows.

### ADDITION — Reserve has no Phase 4 persisted record

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Reserve is an optional future concept. Phase 4 adds no Reserve model, mutation or approval/release workflow, automatic percentage, or automatic amount.
- Reserve is not an Expense and cannot rewrite historical Profit.

**Scope**
- Future Company retained-profit and distribution design.

**Preserve unchanged**
- Existing financial-event ownership, audit history, and Company/Branch boundaries remain unchanged.

**Supersedes**
- None.

**Implementation impact**
- Do not add Reserve tables, foreign keys, or mutation endpoints in Phase 4.

### ADDITION — Negative account position remains movement-derived

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Cash/Bank balances may be negative, representing Company debt, borrowing, or deficit. A negative balance alone creates no Loan, Interest, Expense, Credit, or other event.

**Scope**
- Company Cash/Bank accounts and their movement-derived balances.

**Preserve unchanged**
- Actual account movements remain immutable and auditable; account balance is not manually overwritten.

**Supersedes**
- None.

**Implementation impact**
- Permit negative derived totals without synthetic balancing records.

### ADDITION — Paid Expense correction preserves application history

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an Expense with actual Payments is corrected, preserve the original Expense, each Payment event, each Cash/Bank movement, and the correction history.
- Reallocate Payment applications through audited append-only correction/application records.
- Reject a replacement Expense that cannot cover its already-applied Payments when no separately approved credit/refund rule exists. Do not create a balancing transaction.

**Scope**
- Company Accounting Expense, Payment, AccountMovement, application, and correction relationships.

**Preserve unchanged**
- Actual cash-event identity, Company/Branch ownership, immutable financial history, and one economic Expense remain unchanged.

**Supersedes**
- None. This specifies the relationship and correction path without replacing existing generic history rules.

**Implementation impact**
- Reallocation changes application history only; it does not rewrite Payment or movement rows and must commit atomically.

### ADDITION — Used Accounting categories are archived, not deleted

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The Company-level Accountant may add or archive entries in the Company-wide Accounting category catalogue.
- A category that has been used must not be hard-deleted; preserve its identity and historical record references.

**Scope**
- Company Income/Expense category relationships and historical Accounting records.

**Preserve unchanged**
- Branch Accountants may use but not manage the shared catalogue. Company isolation and the no Branch-, Vehicle-, or Job-specific category system remain unchanged.

**Supersedes**
- None.

**Implementation impact**
- Retain archived category records referenced by history; do not cascade-delete Accounting records through category removal.

### ADDITION — Company Profit report dates use Asia/Kolkata

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Group Company Profit/Loss records into the approved calendar reporting windows using `Asia/Kolkata` dates derived from each event's effective timestamp.
- Persist timezone-aware event instants in UTC; reporting conversion does not rewrite event identity or time history.

**Scope**
- Derived Company/Owner Profit/Loss reports.

**Preserve unchanged**
- Investor Profit and Owner Distribution periods remain separate. Profit remains derived from recognized/committed Accounting Income/Expense.

**Supersedes**
- None. This fixes the timezone for the approved Company reporting windows.

**Implementation impact**
- Convert Asia/Kolkata report boundaries to UTC instants before querying effective timestamps.

### ADDITION — Negative opening positions remain signed account movements

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An account's dated, reasoned opening position may be positive or negative and is represented by its signed opening movement.
- A negative opening position does not create a synthetic Loan, Interest, Expense, Credit, or other balancing record.

**Scope**
- Company Cash/Bank opening events and movement-derived account balance.

**Preserve unchanged**
- Opening balance is not Income, Expense, Receipt, or Payment. Account movements remain immutable and balance is never manually overwritten.

**Supersedes**
- None. This extends the approved negative-balance relationship to the initial account position.

**Implementation impact**
- Validate the opening event and its signed movement atomically; retain fixed-precision amounts and movement history.

### ADDITION — Accounting OFF settlements reference pre-existing obligations

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- While Accounting is OFF, permitted Receipt/Payment events and any necessary audited application correction must reference Income/Expense records that existed before the OFF transition.
- OFF does not remove or rewrite those source records or their history.

**Scope**
- Relationships between Company Income/Expense obligations and their later Receipt/Payment applications.

**Preserve unchanged**
- Each Receipt/Payment remains an actual cash event and is linked to its authoritative Income/Expense; Company/Branch ownership and immutable history remain enforced.

**Supersedes**
- None. The Accounting-specific OFF permission is detailed in 02 and 09.

**Implementation impact**
- Preserve the obligation's creation identity/time so the backend can reject settlement actions against obligations created after OFF.

### ADDITION — Profit testing edits do not create a second source of truth

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- During workflow testing, authorized edits apply to the underlying Income/Expense inputs; Company Profit/Loss is recalculated from those records.
- Do not create a separately editable or persisted Company Profit amount. Confirmed Income/Expense changes continue to use linked, audited correction history.

**Scope**
- Company Accounting source records and derived Company Profit/Loss projections.

**Preserve unchanged**
- Company Profit remains distinct from cash, Investor Profit, distributable Profit, and Owner Distribution. Testing does not close a period or finalize Profit.

**Supersedes**
- None. This reinforces the existing canonical source-of-truth and correction-history boundaries.

**Implementation impact**
- Keep the Company Profit value derived from Accounting records; test-time edits must not create another mutable financial total.

### ADDITION — Phase 4 Accounting Result and Opening Balance representation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 4 `Accounting Result` is read-only and derives from committed recognized Accounting Income minus committed recognized Accounting Expense, including valid immutable correction chains.
- Exclude Receipt, Payment, Opening Balance, Transfer, Investor Profit, Owner Distribution, and local/mock data from the result. Use the approved Asia/Kolkata reporting windows and authorized Branch filter. The result is not final consolidated Company Profit; operational sources participate only through separately approved recognition contracts.
- Opening Balance input is signed. `AccountingEvent.amount` stores positive absolute magnitude; `AccountMovement.delta` stores the signed account effect. Zero creates no financial event or movement. Opening events never participate in Accounting Result.

**Scope**
- Phase 4 Accounting events, Cash/Bank movements, and result projection.

**Preserve unchanged**
- Company ownership, Branch attribution, immutable history, derived balances, and separate Investment/Owner domains.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that leaves the bounded Accounting Result undecided pending full Company Profit rules, and any wording that permits a zero-value opening event. Full source recognition and distribution remain unresolved.

**Implementation impact**
- Persist account effect only in signed movement rows; calculate the result from Accounting Income/Expense records only.

### ADDITION — Accounting cash correction versus target reallocation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- When an actual Receipt/Payment is correct but points to the wrong Income/Expense, append a reversal of the old `AccountingApplication` and a new application to the correct target. Preserve the cash event and `AccountMovement` exactly; record actor, timestamp, reason, and audit history.
- When the actual Receipt/Payment fact is wrong, preserve the original event and append a linked same-type reversal, an equal/opposite movement, and a reversal of its application. Append an optional corrected same-type replacement with its movement and application when needed. Commit atomically and retain idempotency/history. Never convert Receipt to Payment or vice versa.
- Recheck all active Receipt applications against current Income amount and all active Payment applications against current Expense amount. Reject correction/reallocation that exceeds a target's current outstanding amount. Preserve Company, Branch, account activity, module-state, and authorization checks.
- A later real refund/recovery is not a correction and requires its own separately approved workflow; do not invent it here.
- Actual Receipt, Payment, and Transfer events have `effective_at <= server_now`. Opening Balance accepts signed `signed_amount`; store `abs(signed_amount)` as event amount and the signed amount as movement delta. Zero creates no event. Opening Balance may be historical but not future-dated and is excluded from Accounting Result.

**Scope**
- Phase 4 AccountingEvent, AccountMovement, AccountingApplication, correction and reallocation relationships.

**Preserve unchanged**
- Append-only financial history, immutable source identity, one economic cash effect, over-receipt/overpayment limits, and separate accounting result semantics.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Phase 4 architecture statement that Receipt/Payment corrections are wholly outside scope. It now distinguishes wrong-target application reallocation from correction of a wrong cash fact. Refund/recovery behavior remains future/BDR.

**Implementation impact**
- Implement separate application reallocation and Receipt/Payment correction commands with deterministic locks and one database transaction; validate actual event dates against server time.

### ADDITION — Phase 4 correction lineage, Branch attribution, and account archive safety

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Supported Phase 4 corrections append an immutable same-kind reversal and may append a corrected same-kind replacement. Use reversal-only only when the specific record does not represent a distinct economic event (for example, a false/duplicate record); do not erase a distinct real cash movement. When the event represented by that record occurred but its facts are wrong, append the replacement. A wrong Receipt/Payment target is corrected through application history only, leaving the cash event and account movement unchanged.
- An Income/Expense with active Receipt/Payment applications cannot be reversed alone. Reallocate those real cash applications to a valid target through the audited application flow, or include their safe reapplication to the same-kind replacement atomically; reject the correction if neither is possible.
- An authorized Company-level Accountant may give a corrected replacement another Branch in the same Company or Company-wide attribution where supported. A Branch Accountant's replacement remains in the original authorized Branch. Reversal rows retain the original source attribution; reattribution applies only to the replacement record.
- While Accounting is OFF, only root entries and target obligations whose immutable `recorded_at` precedes the current Accounting `DISABLED.effective_from` are eligible for correction or application reallocation. A correction/replacement row may be recorded later only as linked history for that eligible pre-OFF chain; no post-OFF root obligation or target may be created or used.
- A Cash/Bank account may be archived only if its derived balance is zero and it has no historical Accounting event or AccountMovement referencing it. Any transaction history blocks archive even when the current balance is zero or the activity was later reversed.

**Scope**
- Phase 4 AccountingEvent, AccountingApplication, AccountMovement, Branch attribution, module-state eligibility, and named account archive relationships.

**Preserve unchanged**
- Company-wide account ownership, same-Company Branch constraints, immutable history, movement-derived balances, and Accounting-specific permissions remain. This does not authorize hard deletion, unarchive, refunds, or recovery events.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that leaves correction outcome choice and replacement Branch attribution unspecified; the account-archive rule that permits archival based only on a zero current balance; and the OFF exception wording that does not require all affected root records and targets to predate OFF.

**Implementation impact**
- Enforce archive eligibility from immutable account history as well as a locked zero-balance check. Preserve original branch on reversals; validate any replacement Branch against actor authority and Company ownership; compare root `recorded_at` with the immutable module-state revision's `effective_from`.

### ADDITION — Accounting events and applications retain module-state revision identity

**Status:** APPROVED ARCHITECTURE DECISION
**Effective documentation state:** Current V2 technical architecture clarification

**Rule**
- Each Phase 4 `AccountingEvent` and append-only `AccountingApplication` stores a protected reference to the immutable Company `CompanyModuleState` revision used by the command that wrote it. `AccountMovement` inherits this provenance through its required event link.
- Create the event/application and capture the current revision in one transaction while holding the same Company/Tenant row lock used by the module-state transition. The referenced revision must belong to the event's Company and have `module_code="accounting"`; neither reference nor version is client-supplied.
- When Accounting is OFF, determine whether a root event predates the current disabled revision by revision ordering (`root.module_state_revision.version < disabled_revision.version`), not by wall-clock comparison alone. Every affected original root event and root obligation must pass this test. A correction child written during OFF may reference the disabled revision and may be a target only inside that same eligible atomic correction chain.
- A normal Receipt/Payment settlement allowed while OFF references the current disabled revision. It is ordinary settlement against a pre-OFF root obligation, not a correction; it does not qualify for correction during that same OFF revision.
- Missing, cross-Company, wrong-module, or otherwise inconsistent revision references fail closed for correction/reallocation. Preserve `recorded_at` and `effective_from` as audit/report timestamps; they are not the sole authorization ordering proof.

**Scope**
- Phase 4 AccountingEvent, AccountingApplication, AccountMovement provenance and the module-OFF ordering check.

**Preserve unchanged**
- Existing CompanyModuleState schema and monotonic immutable revision history; no new field is added to the tenants table. No business module gains a different OFF exception.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: any Phase 4 implementation interpretation that relies only on comparing application-server `recorded_at` with module-state `effective_from` to prove pre-OFF ordering. The business cutoff remains pre-OFF; immutable revision ordering is its concurrency-safe proof.

**Implementation impact**
- Add the protected revision foreign key to the initial Accounting schema for events and applications, depending on the existing tenants module-state migration. No backfill is needed while no Accounting persistence table exists; imported rows without a valid revision must be rejected or explicitly migrated before use.

### ADDITION — Investor Monthly Interim amount is configuration, not a principal formula or payment

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- The Investment domain owns a fixed INR Monthly Interim amount configured per Investor and effective monthly cycle. The amount is not derived as a rate times Fund or eligible principal.
- Keep the effective amount/configuration distinct from confirmed Interim payment records. A configured amount, due value, or suggestion creates no payment or cash movement. Confirmed Interim payments remain advances against eventual Investor Profit and are reconciled under the approved Investor rules.
- Preserve configuration/effective-cycle and actual-payment history so later changes do not rewrite prior cycles. Any excess over finally earned Investor Profit follows the existing explicit recoverable/adjustment history; no silent cross-category netting is introduced.

**Scope**
- Investment-owned Investor configuration, monthly-cycle calculation, actual Interim payment relationships, and later Investor Profit reconciliation.

**Preserve unchanged**
- Company/Branch ownership, Company isolation, Investor Profit ownership, actual payment confirmation, append-only correction/history rules, and Company Accounting's ownership of Company cash/ledger events. Principal withdrawal limits and period-reconciliation deal/payout inclusion remain unresolved where already identified.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the relationship row and BDR requiring an eligible-principal basis for calculating a rate-based Monthly Interim amount. It does not resolve active-cycle principal withdrawal limits or reconciliation-period deal inclusion and ordinary payout interaction.

**Implementation impact**
- Model the effective per-Investor amount separately from payment/application records; any schema/API shape remains subject to the Phase 5 code architecture. Do not duplicate cash ownership in Investment or Company Accounting.

### ADDITION — Interim payment history is a Paid component of Investor Profit reconciliation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Investor Profit reconciliation references each actual confirmed Monthly Interim payment as an amount already Paid against Investor Profit. Keep the earned-Profit value and the paid advance as separate linked facts.
- Do not count a configured monthly amount or an unconfirmed suggestion as Paid. Showing an Interim payment in the Profit reconciliation must not create another economic payment, Fund movement, or Company cash movement.
- Derive the remaining payable/recoverable position only after applying the approved reconciliation scope and its confirmed payment records; do not rewrite the original Profit or payment history.

**Scope**
- Relationship between Investment-owned earned Investor Profit, confirmed Interim payment records, and the Investor's reconciliation projection.

**Preserve unchanged**
- Payment ownership, Company isolation, immutable payment/cash history, and distinct Investor principal, earned Profit, and Company Accounting records. Which deals belong to a period and how ordinary deal-level Profit payouts are included remain unresolved.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether a confirmed Monthly Interim advance is represented as Paid against Investor Profit in the reconciliation relationship. No period-membership or ordinary-payout rule is superseded.

**Implementation impact**
- Link the reconciliation projection to the existing confirmed payment identity and display it in the Paid component without issuing a second financial event. Keep final reconciliation scope subject to the remaining business decisions.

## Phase 5 Approved Business Decision Additions — Investment and Vehicle relationships

### ADDITION — Investor Fund is pooled with immutable Branch-attributed lots

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Store one Company Fund ledger; every credit has a required same-Company Branch provenance. This Branch tag is not a separate balance.
- Fund credits are immutable positive lots. Vehicle use is an immutable allocation to the same Investor's eligible credit lots in FIFO order; credit provenance remains traceable but does not split later Vehicle Profit.
- Available Fund is derived from valid credits less use and actual eligible returns; do not persist independently editable balance/KPI totals.
- An active Investor principal return can use only unallocated Available Fund and must identify same-Company source credit(s). Branch Accountant scope follows the source Branch; Company-level Accountant may act across Branches.

**Scope**
- Investment-owned Investor, Fund credit/use/return records and derived Fund ledger.

**Preserve unchanged**
- Stable UUID identity; Company/Tenant isolation; Branch is attribution; Accounting alone owns actual Cash/Bank events; no automatic Profit, Income, Expense or settlement event.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether Fund is duplicated per Branch, whether Branch tags are merely display-only, or whether Fund use can be assigned by an independently editable total. No other module ownership is superseded.

**Implementation impact**
- Link credit lots to use/return rows by immutable foreign keys and derive balances with server-side selectors under row locks.

### ADDITION — Vehicle source relationship and one-time purchase cost

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Vehicle Management owns one Company-wide Vehicle UUID and current Branch. Every Investment, Accounting, Garage, Sales or Media reference uses that UUID; Branch movement appends history and never creates a replacement Vehicle.
- Investor identity/responsibility and Fund use belong to Investment and reference the Vehicle UUID; purchase cost belongs to the Vehicle purchase source and contributes to Vehicle cost once.
- For a Vehicle purchase, Investor Fund allocations plus exact Company Running Capital allocation must equal the complete approved purchase cost. Investor Fund allocation is limited to one Investor per Stock Vehicle and consumes that Investor's eligible credit lots FIFO.
- No Fund-credit amount is additionally recorded as Company Income/Expense/Profit. A single real purchase cash event is Accounting-owned; source allocations do not create extra cash movements.
- Registration is unique per Company among active Vehicles. A sold Vehicle is not automatically inactive. Registration reuse requires manual deactivation only after it is confirmed Sold and has no open Job, financial, or settlement position.

**Scope**
- Vehicle Management identity/movement/purchase source, Investment funding, Accounting Running Capital, and future Garage/Sales references.

**Preserve unchanged**
- Vehicle contact information is not ownership/payer identity. Garage Job Name/Phone is Job context. Status and total cost remain derived from their business sources. History and old Branch attribution are preserved.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether Vehicle purchase cost is a separate duplicate from Investment/Running Capital source allocations and whether registration reuse can follow Sale automatically. The seller-payment timing of purchase itself remains Q39 BUSINESS DECISION REQUIRED.

**Implementation impact**
- Model purchase once, immutable funding allocations and one typed Accounting source link; use same-Company constraints and defer deactivation until Sale/Garage/finance providers can prove the preconditions.

### ADDITION — Actual Fund cash events use typed Accounting links

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Investor Fund credit creates one Accounting capital inflow and one positive Cash/Bank movement, linked to the Fund credit; it is neither Company Income nor Profit.
- An actual principal return creates one Accounting capital outflow and one negative Cash/Bank movement, linked to the source credit return; it is not Company Expense or Profit.
- Typed source relationships must use UUID foreign keys and enforce same-Company ownership. Do not use source_reference text as record identity or create a second cash event for the same receipt/payment.

**Scope**
- Investment Fund credit/return and Company Accounting Cash/Bank source history.

**Preserve unchanged**
- Accounting owns actual account balance; source module owns Fund principal; immutable source events, idempotency, tenant scope and atomic writes remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether Investor capital is represented as Company income or a linked capital-inflow source. It does not define a Company Profit formula or a Vehicle seller-payment workflow.

**Implementation impact**
- Add a typed source-link table and capital event kinds; validate source/event/movement consistency inside a single transaction.


### ADDITION — Company Running Capital shortfall is separate from Investor loss offset

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- An approved Company shortfall funding of Vehicle cost/loss is a Vehicle-linked Company Running Capital use, recoverable first from actual proceeds of that same Vehicle. It is not Investor Fund debit or a Company Expense by itself.
- Investor loss share is a separate audited obligation/offset against that Investor's other current/future Vehicle Profit; do not use Fund credits for ordinary loss offset.
- The Company Running Capital use and Investor loss-offset records must stay separate. Actual cash movement is recorded only once when money moves.

**Scope**
- Future Vehicle loss, Company Running Capital and Investor Profit relationships.

**Preserve unchanged**
- Accounting owns Cash/Bank movement; Investment owns Fund and Investor loss/Profit; Vehicle Management owns Vehicle identity and cost sources. Phase 5 does not post Loss offsets or Company Running Capital recovery.

**Supersedes**
- SUPERSEDES the immediately preceding Phase 5 addition phrase forbidding any Company Running Capital source for an Investor/Fund shortfall. It does not authorize a duplicate cost, Fund debit, or cash movement.

**Implementation impact**
- Preserve separate source UUIDs and link a future same-Vehicle recovery to the actual proceeds event; do not merge it with the Investor loss Profit-offset chain.

### ADDITION — Vehicle purchase payable is separate from actual Cash/Bank payment

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- The Vehicle purchase record owns the complete approved purchase cost. Any unpaid part is an outstanding seller payable linked to that purchase.
- One or more actual partial seller payments may be linked to the same purchase. The outstanding payable is derived from the approved purchase cost less valid linked payments; it cannot be overpaid.
- Each actual payment creates its Accounting Cash/Bank effect once. The payable and purchase funding allocations do not create additional cash movements.

**Scope**
- Vehicle Management purchase source, Accounting seller-payment events, and purchase funding allocations.

**Preserve unchanged**
- Vehicle UUID remains the stable identity; Investment owns Fund credit/use; Accounting owns actual Cash/Bank movements; the complete Vehicle purchase cost is counted once.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Q39 seller-payment timing, which is now approved as purchase-before-full-payment with a linked payable and partial payments.

**Implementation impact**
- Use immutable typed links between purchase and actual payment records; derive the remaining payable under transaction/row-lock protection.

### ADDITION — Seller identity belongs to Vehicle Purchase

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Vehicle Purchase stores a required seller name and an optional seller phone number. Seller identity remains attached to the purchase and payable history.

**Scope**
- Vehicle Purchase data and its linked seller payable/payments.

**Preserve unchanged**
- Vehicle UUID remains the Vehicle identity; Investor and Garage customer/person records remain separate. No general Vendor aggregate is introduced by this decision.

**Supersedes**
- None; the prior purchase relationship did not specify seller identity fields.

**Implementation impact**
- Store seller name and optional phone on the immutable purchase record; do not reuse Vehicle, Investor, or Job-contact IDs.

### ADDITION — Purchase allocations precede seller cash settlement

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- At purchase creation, Investor Fund and Company Running Capital allocations together cover the full approved purchase cost, including when seller cash paid is ₹0. The Investor allocation is immediately committed/locked to that purchase.
- Seller payable is a separate purchase-to-seller obligation derived from the full cost less valid actual seller installments; it is not another source allocation.
- These allocations do not create an Accounting Cash/Bank movement. Accounting records a movement only for an actual seller payment.

**Scope**
- Relationships among VehiclePurchase, Investor Fund use, Company Running Capital allocation, seller payable, and Accounting movements.

**Preserve unchanged**
- Vehicle purchase cost is stored once; Investment owns Fund credits/use; Company Running Capital remains a separate source; Accounting owns actual Cash/Bank movements. No lender finance or EMI relationship is introduced.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether funding allocations wait for seller payment or are recorded at purchase creation. Purchase allocations are recorded at creation; cash settlement remains a separate later event.

**Implementation impact**
- Keep allocation rows and actual seller-payment rows as separate immutable relationships; derive Available Fund and seller payable from their respective source histories.

### ADDITION — Purchase correction below paid installments requires a recorded refund

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Do not accept a purchase-cost correction that would put cumulative actual seller installments above corrected cost until the seller has returned the excess and Accounting has recorded that actual receipt.
- Keep original purchase, seller-payment, and Cash/Bank movement records immutable; retain an audited correction and allocation history.

**Scope**
- VehiclePurchase, source allocations, seller payable, seller installments, and the related Accounting receipt.

**Preserve unchanged**
- The purchase owns one cost; Investor Fund and Company Running Capital allocations are distinct; Accounting owns actual Cash/Bank movements.

**Supersedes**
- None; this adds the missing relationship rule for a correction after seller payment.

**Implementation impact**
- The correction service must compare corrected cost with cumulative valid installments and require the linked actual refund before append-only correction/reallocation.

### ADDITION — Corrected purchase cost retains its funding-source proportion

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Reduce the Investor Fund and Company Running Capital portions in the same proportion as the recorded purchase funding-source split when purchase cost is corrected downward.
- Keep the original allocation rows immutable and append audited compensating allocation history; within the Investor Fund portion, use the approved FIFO credit-lot attribution rule.

**Scope**
- VehiclePurchase cost, Investor Fund use allocations, Company Running Capital allocations, and their correction history.

**Preserve unchanged**
- One purchase cost and its source allocations reconcile exactly; seller Cash/Bank movements remain separate and immutable.

**Supersedes**
- None; this resolves source reduction for a corrected purchase cost.

**Implementation impact**
- Recompute corrected source totals from append-only adjustment rows. A sub-paisa proportional-rounding rule remains unresolved.

### ADDITION — Purchase-source adjustment uses balanced-paise rounding

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Calculate proportional source adjustments at high precision, round each to two decimals with `ROUND_HALF_UP`, then balance the residual so adjustments equal the total correction exactly.
- Allocate residual paise to the most under-allocated source (or remove from the most over-allocated), recomputing after each paise. Ties use the fixed order Investor Fund, then Company Running Capital.

**Scope**
- Purchase correction source-allocation records.

**Preserve unchanged**
- The original source ratio, append-only history, and FIFO allocation of Investor Fund credit lots.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: proportional purchase-source paise rounding.

**Implementation impact**
- Persist two-decimal source adjustments whose exact sum matches the purchase-cost correction.

### ADDITION — Seller refund and Purchase correction are manually linked history

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An Accountant manually records the actual seller refund and the related Purchase correction; both must be explicitly linked to the same VehiclePurchase.
- Preserve original seller installments and Cash/Bank movements. Do not create a refund or correction automatically.

**Scope**
- VehiclePurchase, actual seller payments/refunds, cost correction, and source-allocation correction history.

**Preserve unchanged**
- Accounting owns actual cash movements; VehiclePurchase owns its cost and seller obligation; Investment and Accounting retain their own source allocations.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether refund/correction entries should be manual and Purchase-linked.

**Implementation impact**
- Use distinct typed refund and correction records, linked to one Purchase; derive payable from the valid linked history rather than manually stored mutable balance.

### ADDITION — Buyer Receipt reference uniqueness uses trimmed case-insensitive matching

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Stock Vehicle Buyer Receipt external reference is duplicate when its value matches another reference for the same Company and same Cash/Bank account after removing leading/trailing whitespace and ignoring letter case. This applies across Branches; the same normalized text may be used for a different account.

**Scope**
- Typed Stock Vehicle Buyer Receipt records and the uniqueness constraint protecting their external reference.

**Preserve unchanged**
- The Sale Receipt UUID and typed Sale relationship are record identity; the external reference is traceability data. This rule does not apply to every Accounting event or to Garage receipts.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: exact case and surrounding-whitespace comparison for the Buyer Receipt uniqueness rule.

**Implementation impact**
- Enforce a normalized reference key with the same-Company and Cash/Bank-account uniqueness scope, across Branches. Keep the original typed source and its Accounting event in one atomic write.

### ADDITION — Fund Credit external-reference uniqueness is account-scoped

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An Investor Fund Credit reference is duplicate within the same Company and same Cash/Bank account, across Branches, after trimming leading/trailing whitespace and ignoring case. The same normalized reference may be used with a different account.

**Scope**
- Investment-owned Fund Credit source records and their typed Accounting capital-inflow relationship.

**Preserve unchanged**
- The Fund Credit UUID remains record identity; Accounting owns the actual movement and the linked account. Reference text does not replace the typed source relationship. This rule does not apply to other Accounting references.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Fund Credit references require duplicate rejection, including comparison normalization and account/Company scope.

**Implementation impact**
- The current Fund Credit table lacks `account_id`, while the actual account is on the linked Accounting movement. The implementation architecture must define a database-enforceable normalized uniqueness key tied to that same movement account and same Company, without allowing the two account identities to diverge.

### ADDITION — One transfer funds one Investor Fund Credit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- One actual Cash/Bank transfer may create a Fund Credit for one Investor only. Do not split one transfer among multiple Investors' Fund Credits. Each Investor must have a separate actual transfer recorded for that Investor's Fund Credit.

**Scope**
- Investor Fund Credit source records and their linked Accounting capital-inflow movement.

**Preserve unchanged**
- Each Fund Credit remains linked to one Accounting capital inflow and one actual `AccountMovement`, with Branch provenance and the existing Company/account/reference duplicate rule. Separate actual transfers may still create separate credits for the same Investor.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether one actual transfer may fund multiple Investors' Fund Credits, as left open by Q65.

**Implementation impact**
- Keep the typed source relationship one-to-one for each actual transfer and Fund Credit. No split-allocation table or shared-transfer-to-many-Investors mapping is required. This does not make the external reference a record identity or idempotency key.

### ADDITION — Fund Credit effective date is the actual receipt date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Use the date money was actually received as the Fund Credit effective date. Late entry may use a past date; future-dated Fund Credits are prohibited.

**Scope**
- The Fund Credit and its linked Accounting capital-inflow and Cash/Bank movement records.

**Preserve unchanged**
- Keep the system's record-creation/audit timestamp separate and unchanged. The effective date is not the entry timestamp.

**Supersedes**
- None; the allowed backdating and future-date policy was previously unspecified.

**Implementation impact**
- The linked records must share the actual receipt effective date. A backdated entry changes as-of ledger history and effective-date reporting, while its creation audit time remains current. The timezone/time-of-day encoding of the business date remains a technical contract.

### ADDITION — Wrong-Investor Fund Credit correction preserves one cash movement

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an actual transfer is valid but its Fund Credit is attributed to the wrong Investor, retain the original credit and append an audited correction that moves the amount from the wrong Investor to the correct Investor.
- Do not create a second Accounting receipt or Cash/Bank movement for that attribution correction.

**Scope**
- Typed Investment correction records and derived Investor Fund balances for an incorrectly attributed confirmed Fund Credit.

**Preserve unchanged**
- The original Fund Credit UUID, source Branch, Accounting capital-inflow event and AccountMovement remain preserved and immutable. The Company-wide Fund total does not gain a second receipt.

**Supersedes**
- None; the correction path for a valid transfer attributed to the wrong Investor was previously unspecified.

**Implementation impact**
- Add a typed append-only attribution correction linked to the original credit; do not mutate the original Investor FK or AccountingSourceLink. Authorization, partial-correction behavior and effective-date treatment remain BUSINESS DECISION REQUIRED.

### ADDITION — retain linked Fund-use and principal-return history on attribution correction (Q133–Q134)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A full correction of a Fund Credit's wrong Investor attribution may be recorded after the credit has linked Vehicle use and/or principal-return activity.
- Keep the original Fund-use and principal-return records and actual Cash/Bank movements unchanged. Do not automatically reassign, edit, reverse, or recreate them as part of the Fund Credit correction.
- An Accountant manually reviews and prepares affected Investor calculations. The system must not automatically restate or post historical Investor Profit, settlement, overpayment, or cash adjustments for this case.

**Scope**
- Typed, audited attribution correction and its linked-history behavior for a confirmed Fund Credit.

**Preserve unchanged**
- Original Fund Credit identity, amount, Branch provenance, AccountingSourceLink, AccountMovement, use/return history and actual payments. The attribution correction creates no second cash event.

**Supersedes**
- SUPERSEDES Q71's automatic historical Investor-calculation recalculation for a corrected credit with prior linked use or principal-return activity. Apply the correction using the original receipt effective date; manual calculation preparation does not rewrite cash history.

**Implementation impact**
- Persist the old/new Investor attribution and audit evidence in an append-only typed correction. Return an explicit manual-review indication when linked use/return rows exist. Do not automate downstream Profit/settlement effects in Phase 5.

### ADDITION — Branch scope for Fund Credit attribution corrections

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may post the approved attribution correction only for a Fund Credit whose source Branch is within their authorized Branch scope. A Company-level Accountant may post it for any Branch in the same Company.

**Scope**
- Authorization for the typed append-only correction of a valid Fund Credit assigned to the wrong Investor.

**Preserve unchanged**
- The original Fund Credit Branch remains provenance and is not changed by the correction. This is an Investment-specific scope rule, not a general cross-Branch permission.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: authorization scope for wrong-Investor Fund Credit corrections.

**Implementation impact**
- Bind the correction to the original Fund Credit and revalidate its Company and source Branch in the service/transaction. Partial corrections and effective-date treatment remain unresolved.

### ADDITION — Fund Credit attribution correction is whole-credit only

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Move the entire original Fund Credit amount from the incorrectly attributed Investor to the correct Investor. Partial attribution correction that splits one transfer across Investors is not allowed.

**Scope**
- Amount semantics for the append-only wrong-Investor Fund Credit correction.

**Preserve unchanged**
- Original Fund Credit, source Branch, Accounting event, and AccountMovement remain unchanged and auditable. The correction creates no cash movement and does not change Company-wide Fund total.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether partial attribution correction is permitted, as left open by Q68 and Q69. This is limited to the wrong-Investor correction and follows Q66's one-transfer/one-Investor rule.

**Implementation impact**
- Store a correction amount equal to the full referenced Fund Credit amount and reject a smaller or split amount. Keep Q69 authorization scope. The effective date of this correction remains unresolved.

### ADDITION — Attribution correction takes the original Fund Credit effective date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A wrong-Investor attribution correction is effective on the original Fund Credit's actual receipt date. Recalculate affected historical Investor calculations and preserve previous versions and audit history.
- The correction does not alter the original Cash/Bank movement or its effective date.

**Scope**
- Effective dating and historical Investor calculation versions for a full-credit attribution correction.

**Preserve unchanged**
- Preserve the original Fund Credit, source Branch, Accounting event/movement, and actual creation timestamps. Investor Profit remains separate from Company Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: the effective date to apply to a wrong-Investor Fund Credit correction, as left open by Q68-Q70.

**Implementation impact**
- Store correction effective date from the original credit and retain a separate correction-recorded timestamp. Recalculate affected Investor periods without deleting prior calculation history. Treatment of already-paid/settled amounts remains a separate BUSINESS DECISION REQUIRED item.

### ADDITION — Historical Investor Profit restatement uses separate adjustments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Preserve prior Investor calculations and actual payments when a historical period is recalculated after a Fund Credit attribution correction. Store the difference as a separate audited adjustment.
- Add any underpayment to a later Investor Profit amount; deduct any overpayment from a later Investor Profit amount.

**Scope**
- Data relationship between a historical calculation revision, the actual prior payment, the resulting adjustment, and later Investor Profit.

**Preserve unchanged**
- Prior actual Cash/Bank movements remain immutable. The calculation adjustment is not a second payment, Company Income/Expense, or Company Profit event.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: how a previously reconciled/paid Investor Profit amount is carried after historical restatement.

**Implementation impact**
- Keep calculation versions, payment links, and restatement adjustment history distinct. Do not silently change historical payment amounts. Treatment of an unoffset balance when future Profit is unavailable or Exit occurs remains BUSINESS DECISION REQUIRED.

### ADDITION — Exit outcome may be flexible for historical Profit overpayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- At Investor Exit, a historical Investor Profit overpayment may either be collected before closure or remain unpaid while Exit is completed, according to the case.

**Scope**
- Unoffset audited adjustment caused by restating historical Investor Profit after a Fund Credit attribution correction.

**Preserve unchanged**
- Preserve the adjustment and actual payment history. Do not automatically debit Investor Fund or create a Cash/Bank event. Other loss and principal Exit rules remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Exit must remain open until this historical Profit overpayment is fully collected.

**Implementation impact**
- Retain an explicit Exit outcome and adjustment history. Authority to choose the outcome and the remaining unpaid balance's status after closure remain BUSINESS DECISION REQUIRED.

### ADDITION — Record the disposition of unpaid restatement overpayment at Exit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Exit completes without collection of an unoffset historical Investor Profit overpayment, retain it as an open balance for later collection or waive it with a recorded reason, selected case by case.

**Scope**
- Post-Exit status of the overpayment adjustment created by historical Investor Profit restatement.

**Preserve unchanged**
- Keep the adjustment and Exit decision in audit history. Neither open-balance status nor waiver creates or changes a Cash/Bank movement or Company Income/Expense.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: post-Exit disposition of the unpaid overpayment residual, as left open by Q73.

**Implementation impact**
- Store a distinct disposition (open for later collection or waived) and waiver reason; the role authorized to select/approve it remains BUSINESS DECISION REQUIRED.

### ADDITION — Branch scope for post-Exit overpayment disposition

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may set open or waived disposition only for an adjustment attributed to their authorized Branch. A Company-level Accountant may do so for any Branch within the same Company.

**Scope**
- Authorization relationship for post-Exit disposition of a historical Investor Profit restatement overpayment.

**Preserve unchanged**
- The original adjustment Branch remains the authorization source. This does not authorize a Branch Accountant to finalize an Exit spanning Branches or to make cross-Branch corrections in other modules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: post-Exit overpayment disposition actor scope.

**Implementation impact**
- Bind disposition history to the underlying adjustment and source Branch; validate the actor's same-Company role/Branch assignment server-side.

### ADDITION — Repayment against an open post-Exit adjustment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record an actual repayment only against an open post-Exit adjustment whose source Branch is within their authorized scope. A Company-level Accountant may record it for any Branch in the same Company.

**Scope**
- The relationship between an open historical Investor Profit overpayment adjustment and a later actual repayment.

**Preserve unchanged**
- Keep the overpayment adjustment and Exit disposition history. The actual repayment is recorded only upon receipt of money and does not change the original Profit payment.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: role scope for collecting an open post-Exit adjustment.

**Implementation impact**
- A typed repayment source link must settle the open adjustment without rewriting its history. Exact Accounting event classification and source-link schema remain technical/business contract work.

### ADDITION — post-Exit repayment reduces the open Profit overpayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An actual repayment against an open post-Exit Investor Profit overpayment is a Cash/Bank Receipt linked to that adjustment. Reduce the open overpayment by the amount actually received.
- Do not classify the repayment as Company Income or Company Profit.

**Scope**
- Data relationship between the post-Exit restatement overpayment, its actual repayment receipt, and the derived open balance.

**Preserve unchanged**
- Preserve original Profit and payment history, the immutable adjustment/disposition history, Q76's Company/Branch authorization, and the rule that a movement exists only when money is actually received.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an actual post-Exit overpayment repayment is Company Income/Profit; its source-link schema remains unresolved implementation design.

**Implementation impact**
- Link the single actual Receipt and Cash/Bank movement to the open adjustment, then derive its remaining balance without rewriting prior records or creating Income.

### ADDITION — partial repayment applications against an open adjustment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- One open post-Exit historical Investor Profit overpayment may have partial and multiple actual repayment receipts.
- Each actual receipt reduces the open adjustment by the amount received. The unpaid remainder remains open.

**Scope**
- Relationship and balance derivation between an overpayment adjustment and its actual repayment Receipts.

**Preserve unchanged**
- Q77's receipt classification and no-Company-Income/Profit rule, Q76's source-Branch authorization, and immutable adjustment/receipt history remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether partial or multiple receipts can settle one open post-Exit adjustment.

**Implementation impact**
- Preserve a separate typed link for each actual receipt and derive the remaining open balance from valid linked receipts. Excess-receipt handling remains unresolved.

### ADDITION — edited repayment values retain backend correction history

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A saved post-Exit repayment entry may be edited by an authorized Accountant; ordinary views use the latest value and need not show earlier versions.
- Preserve the original entry and every correction in backend audit history. A note may accompany a correction.
- The actual Cash/Bank Receipt and movement are not overwritten by editing the repayment entry.

**Scope**
- Version/history relationship for post-Exit Investor Profit overpayment repayment entries and their actual receipts.

**Preserve unchanged**
- The adjustment, Exit decision and actual Receipt history remain auditable; Q76-Q78 authorization, Receipt classification and partial-repayment rules are unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the ordinary view must display prior repayment-entry values after an edit.

**Implementation impact**
- Persist each correction append-only and derive the current entry view from the latest effective correction. Keep actual movement identity and amount unchanged.

### ADDITION — excess post-Exit repayment disposition

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an actual repayment exceeds the remaining open overpayment, the authorized Accountant chooses whether the excess stays open as an amount due back to the Investor or is returned through a separately recorded actual refund.
- Keep the original Receipt at its actual amount. Record a refund outflow only when the refund is actually paid; do not create Company Income/Profit.

**Scope**
- Data relationships for an excess Investor repayment, its open refundable amount or actual refund, and the original Cash/Bank Receipt.

**Preserve unchanged**
- Q76-Q79 authority, Receipt, partial-repayment, audit-display and immutable-movement rules remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: disposition of repayment received above the open post-Exit overpayment.

**Implementation impact**
- Store an auditable case disposition; link any later actual refund as a distinct cash outflow to the same source. Keep all records within the same Company and authorized Branch scope.

### ADDITION — partial refund applications against excess repayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An excess repayment retained as due back to the Investor may be paid back through partial and multiple actual refunds.
- Each actual refund is a separate Cash/Bank outflow linked to the due-back amount. The remaining amount stays open until further actual refunds are recorded.

**Scope**
- Relationship between the due-back balance for excess Investor repayment and separate actual refund payments.

**Preserve unchanged**
- The original Receipt remains at the actual received amount. Q76-Q80 authority, disposition, no-Income/Profit, edit-history and movement rules remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an excess due-back amount requires one full refund or may have partial/multiple actual refunds.

**Implementation impact**
- Store every actual refund movement independently and derive the open due-back amount from linked actual refunds; no refund is posted before payment.

### ADDITION — full source amount and partial settlement relationships

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Vehicle Purchase cost and agreed Sale price are stored in full on their source records before or independently of actual settlement.
- A source-owned payable, receivable, or refund payable may be settled by partial and multiple linked actual cash events. Each installment must be positive and no greater than the current outstanding amount; a smaller installment leaves a derived open remainder.
- Actual Buyer and seller refunds may also be partial/multiple. A seller's partial refund does not satisfy a Purchase correction that requires the full excess refund before the correction is accepted.

**Scope**
- Purchase/Sale source totals, actual seller payments, Buyer receipts, and actual linked refunds; equivalent modules only where a typed source obligation and permissions already exist.

**Preserve unchanged**
- Full source cost/price remains distinct from Cash/Bank movements, Investor Fund, Running Capital, Income, Expense and Profit. Existing refund/correction, Company/Branch and immutable history rules remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Purchase/Sale refund obligations may have partial/multiple actual settlement events and whether a below-balance installment is valid.

**Implementation impact**
- Keep source totals authoritative and derive open balances from typed linked events; reject an installment above the current outstanding balance without silently clamping it.

### ADDITION — Sale form Save creates the confirmed Sold source

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A successful Save of the existing Sale form creates the authoritative confirmed Sale record that makes its Vehicle Sold.
- The Sale record and its Buyer Receipt records are separate relationships; confirming the Sale does not imply that its receivable is fully collected.

**Scope**
- Phase 5 Stock Vehicle Sale source and its relationship to Vehicle Sold state and Buyer collection.

**Preserve unchanged**
- Keep one authoritative Sale source per eligible Vehicle and retain its Company, Branch, Buyer, agreed price, actual Sale date, and history. Keep each Buyer Receipt linked to that Sale and to its own actual Accounting movement.

**Supersedes**
- None; this clarifies when the authoritative Sale source becomes confirmed.

**Implementation impact**
- Set the Sale source to confirmed on successful authorized creation; do not derive Sold from a receipt or a duplicate Vehicle flag.

### ADDITION — Buyer refund permission follows the Sale's Branch provenance

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record an actual Buyer refund only against a Sale from their authorized Branch. A Company-level Accountant may record it for any Branch in the same Company.

**Scope**
- Authorization relationship for actual Buyer refunds against Stock Vehicle Sale obligations.

**Preserve unchanged**
- Keep each refund linked to the authoritative Sale and its original Company/Branch. The actual Cash/Bank movement remains separate and is recorded only when money is returned.

**Supersedes**
- None; this establishes the source-Branch authorization for Buyer refunds without changing the Sale or refund data ownership.

**Implementation impact**
- Derive the authorized Branch from the linked Sale on the server; do not accept a client-selected Branch as the refund source.

### ADDITION — Sale and Buyer Receipt mutations follow Sale Branch provenance

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may create/confirm a Sale and record its actual Buyer Receipts only when the Sale belongs to their authorized Branch.
- A Company-level Accountant may perform those actions for any Branch in the same Company.

**Scope**
- Relationships among the Stock Vehicle Sale, its original Company/Branch, and the actual Buyer Receipt records.

**Preserve unchanged**
- The Sale remains the authoritative Sold source. Buyer Receipts remain individually linked actual Cash/Bank events; receipt authorization does not alter Q84's separate Buyer refund permission.

**Supersedes**
- None; this specifies mutation authority using the Sale's existing Branch provenance.

**Implementation impact**
- Validate the Sale's Company and original Branch against the authenticated actor on the server for Sale create/confirm and Buyer Receipt writes.

### ADDITION — module-OFF Buyer Receipt leaves the existing Sale balance open

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Vehicle Management is OFF, no Buyer Receipt may be linked to a preexisting Sale, even if Accounting remains ON.
- The existing Sale and its outstanding receivable remain unchanged; no Accounting event or AccountMovement is created while the Receipt is blocked.

**Scope**
- Data relationship between a pre-OFF Stock Vehicle Sale, its Buyer Receipts, and Accounting movements.

**Preserve unchanged**
- Existing Sale history and open balance remain available for later review. This does not change the separately approved Seller payable installment exception or the requirement that Accounting be ON for any actual cash movement.

**Supersedes**
- None; this clarifies module-OFF behavior for Buyer Receipts only.

**Implementation impact**
- Require both Vehicle Management and Accounting to be ON for a Buyer Receipt; leave the Sale receivable untouched when the command is rejected.

### ADDITION — module-OFF Seller refund leaves the Purchase unchanged

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Vehicle Management is OFF, do not create a Seller refund record or linked Accounting event for an existing Purchase, even if Accounting is ON.
- Leave the Purchase and its existing history unchanged until Vehicle Management is ON and the refund command can be accepted.

**Scope**
- Data relationship between a pre-OFF Vehicle Purchase, an actual Seller refund, and its Accounting movement.

**Preserve unchanged**
- Keep the separately approved pre-OFF Seller payable installment exception when Accounting is ON. A blocked refund creates no Accounting cash inflow or movement.

**Supersedes**
- None; this specifies module-OFF behavior for Seller refunds only.

**Implementation impact**
- Require Vehicle Management and Accounting ON for a Seller refund; do not mutate the Purchase/refund balance or Accounting ledger when rejected.

### ADDITION — module-OFF Buyer refund leaves the Sale unchanged

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Vehicle Management is OFF, do not create a Buyer refund record or linked Accounting event against an existing Sale, even if Accounting is ON.
- Leave the Sale, Buyer refund obligation, and existing history unchanged until Vehicle Management is ON.

**Scope**
- Relationship between a pre-OFF Sale, its Buyer refund obligation, and actual Accounting outflow.

**Preserve unchanged**
- Existing Sale/collection data remains unchanged. Q86 Buyer Receipt and Q87 Seller refund rules remain separate; no Accounting movement is recorded for the blocked Buyer refund.

**Supersedes**
- None; this clarifies module-OFF behavior for Buyer refunds only.

**Implementation impact**
- Require both Vehicle Management and Accounting ON to record an actual Buyer refund; reject without changing the Sale or refund balance when either is OFF.

### ADDITION — module-OFF Purchase cost correction leaves the Purchase unchanged

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Vehicle Management is OFF, do not append a cost correction to an existing Purchase, even if Accounting is ON.
- Keep the recorded Purchase cost, source allocations, and history unchanged until Vehicle Management is ON.

**Scope**
- Purchase cost correction and its effect on Purchase source/funding relationships.

**Preserve unchanged**
- Preserve the original Purchase and all funding/payment history. Seller payable installment treatment remains its separate approved pre-OFF exception.

**Supersedes**
- None; this defines the module-OFF rule for existing Purchase cost corrections.

**Implementation impact**
- Require Vehicle Management to be ON before adding the correction; do not mutate Purchase allocations or correction history when rejected.

### ADDITION — module-OFF Fund Credit correction preserves original attribution

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Investment is OFF, do not append a wrong-Investor attribution correction to an existing Fund Credit, even if Accounting is ON.
- Keep the original Fund Credit and its current Investor attribution unchanged until Investment is ON.

**Scope**
- Relationship between an existing Fund Credit, its Investor attribution correction, and the linked actual Accounting movement.

**Preserve unchanged**
- Preserve the original credit, its Company/Branch provenance, and exactly one actual Cash/Bank movement. No new cash event is needed to correct attribution.

**Supersedes**
- None; this sets the Investment module-OFF rule for Fund Credit attribution corrections.

**Implementation impact**
- Require Investment ON before adding the correction; when OFF, leave Fund totals, credit attribution, and Accounting history untouched.

### ADDITION — module-OFF unused-principal return preserves Fund history

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- While Investment is OFF, do not create a principal-return allocation or Accounting cash event for an Investor with unused Available Fund and no Exit already in progress before the OFF transition.
- Keep the Fund and its available amount unchanged until Investment is ON.

**Scope**
- Standalone return of unused Investor Fund principal outside a preexisting Exit workflow.

**Preserve unchanged**
- Preserve the original Fund Credits and their Branch provenance. The previously approved pre-OFF Exit settlement exception remains separate and unchanged.

**Supersedes**
- None; this specifies how Investment module-OFF affects unused-principal returns that are not part of an already-open Exit.

**Implementation impact**
- Do not add return allocations or AccountMovement rows while this return is blocked; retain the derived Fund balance from existing source history.

### ADDITION — Seller refund amount is capped by net Purchase payments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Total actual Seller refunds linked to a Vehicle Purchase must not exceed confirmed actual installments for that Purchase less actual Seller refunds already received.
- A refund must reference the Purchase and create only the corresponding one actual Accounting cash event and movement.

**Scope**
- Relationships among Vehicle Purchase, confirmed Seller installments, actual Seller refunds, and Accounting Cash/Bank events.

**Preserve unchanged**
- Purchase cost correction remains a separate audited record; actual Seller refunds do not silently rewrite Purchase cost or installment history.
- Purchase amount, funding allocations, Company/Tenant boundary, and Accounting ownership remain unchanged.

**Supersedes**
- None; this defines the cumulative cap for actual Seller refunds.

**Implementation impact**
- Derive the remaining refundable amount from linked immutable payment/refund events and enforce it under transaction and concurrency locks; do not store an independently editable refund balance.

### ADDITION — preserve Purchase allocations while Investment is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Do not add a cost-correction/allocation-adjustment record for a Vehicle Purchase while Investment is OFF if it changes Investor Fund use. Wait until Investment is ON.

**Scope**
- Purchase cost and Investor Fund-use/allocation relationships.

**Preserve unchanged**
- Keep original Purchase cost and source-allocation history unchanged while blocked. Q89 separately blocks Purchase cost correction while Vehicle Management is OFF.
- Actual Cash/Bank Seller refunds remain separate, immutable Accounting events and require their own approved module gates.

**Supersedes**
- None; this adds the Investment OFF condition for changes to Investor Fund use.

**Implementation impact**
- Validate the current Investment module revision before appending any Purchase correction or allocation adjustment; fail atomically with no partial record when OFF.

### ADDITION — upward Purchase correction uses the Purchase's recorded source proportions

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An upward Vehicle Purchase cost correction adds Investor Fund and Company Running Capital allocations in the proportions originally recorded for that Purchase. Do not apply a universal ratio or an Investor Profit-share percentage.
- If the Investor Fund cannot cover its proportional increase, record the exact shortfall from Company Running Capital, subject to approved source-availability checks.

**Scope**
- Purchase cost corrections and their Investor Fund-use and Company Running Capital allocation relationships.

**Preserve unchanged**
- Preserve original allocation records; append a correction and allocation adjustment. Downward correction follows its separately approved proportional reduction and balanced-paise rule.
- Company, Branch, Investor, and Accounting source ownership remain unchanged.

**Supersedes**
- None; this completes the source-allocation rule for upward Purchase corrections.

**Implementation impact**
- Derive source amounts from the Purchase's immutable original split and append exact adjustments in the same transaction; ensure the total allocations equal corrected cost.

### ADDITION — Purchase cost correction requires all source modules ON

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Require Vehicle Management, Investment, and Accounting ON for every Purchase cost correction, including one with no new cash event. The correction changes Vehicle cost and Investor Fund/Company Running Capital allocation relationships.

**Scope**
- Existing Vehicle Purchase cost, payable, and source-allocation correction relationships.

**Preserve unchanged**
- Keep original Purchase, allocation, Seller payment/refund, and Cash/Bank history. Q89 and Q93 remain in force; actual Seller refunds retain their separate gates.

**Supersedes**
- None; this adds the Accounting module-OFF case to the existing Q89/Q93 rules.

**Implementation impact**
- Reject atomically if any affected module is OFF; create no partial correction or allocation record.

### ADDITION — Investor-funded Sale Receipts require Investment ON

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Buyer Receipt against an Investor-funded Sale requires Investment, Vehicle Management, and Accounting ON. If Investment is OFF, retain the Sale receivable and wait.

**Scope**
- Sale-to-Buyer-Receipt relationship and the linked Accounting movement for an Investor-funded Stock Vehicle.

**Preserve unchanged**
- Q86's Vehicle Management and Accounting requirements remain. The separate Buyer refund gate is defined by Q99.

**Supersedes**
- None; this adds the Investor module gate for this Sale receipt relationship.

**Implementation impact**
- Create neither the Buyer Receipt nor its Accounting event/movement while Investment is OFF.

### ADDITION — Sale price correction is an audited Phase 5 relationship

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 5 includes an audited correction linked to a confirmed Sale. Keep the original Sale and actual Buyer Receipt/refund events; derive the current receivable or refund payable from the corrected agreed price and valid linked events.
- A Branch Accountant may correct within the Sale's authorized Branch; a same-Company Company-level Accountant may correct across that Company's Branches.

**Scope**
- Confirmed Stock Vehicle Sale price, correction history, linked Buyer receipts/refunds, and derived outstanding position.

**Preserve unchanged**
- Sale and cash-event identity/history remain separate. No correction creates a second receipt or refund; Q85 role scope remains Sale-specific.

**Supersedes**
- SUPERSEDES EARLIER PHASE 5 SCOPE STATEMENT: Sale price corrections were deferred. Other Sales, CRM, Garage, and settlement boundaries remain unchanged.

**Implementation impact**
- Append a typed Sale correction and recalculate derived payable/receivable from the Sale and linked actual cash records.

### ADDITION — Sale correction and Buyer refund module gates

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Sale price correction requires Vehicle Management and Accounting ON; Investment may be OFF.
- An actual Buyer refund requires Vehicle Management and Accounting ON; Investment may be OFF.
- A Buyer Receipt against an Investor-funded Sale still requires Investment ON under Q96.

**Scope**
- Existing Investor-funded Sale corrections, actual Buyer refunds, and Buyer Receipts.

**Preserve unchanged**
- Actual refund/receipt cash events remain linked to Accounting and the Sale; no Investor Fund or Profit payment is created merely by recalculating a Sale position.

**Supersedes**
- None; these are distinct module gates for Sale correction, Buyer refund, and Buyer Receipt.

**Implementation impact**
- Enforce each command's own module-state set; do not infer the Buyer Receipt gate from the Buyer refund gate.

### ADDITION — Investor calculations refresh from authoritative Sale sources

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- When a Q98 Sale correction or Q99 Buyer refund is recorded while Investment is OFF, refresh derived Investor calculations from authoritative Sale, Receipt/refund, and Accounting records.
- Recalculation does not create a separate cash event or Investor Profit payment.

**Scope**
- Derived Investor views affected by Sale corrections or Buyer refunds entered while Investment is OFF.

**Preserve unchanged**
- Actual cash remains owned and recorded by Accounting; Investor Profit payments remain distinct authorized events.

**Supersedes**
- None; this resolves only the derived-calculation behavior for the approved Investment-OFF Sale operations.

**Implementation impact**
- Recompute affected views from linked source history without a new Fund/Profit posting.

### ADDITION — Direct Vehicle Expense and Accounting movement relationship

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Phase 5 direct Vehicle Expense belongs to one Stock Vehicle and contributes once to that Vehicle's total cost. Garage Job-linked expenses remain deferred until the Garage phase.
- Accounting remains the source of truth for actual Cash/Bank movement. Link each actual receipt/payment movement to its typed originating source; do not duplicate the movement in Vehicle Management or Sale/Purchase records.
- When an expense is paid in partial installments, retain the Expense and each actual linked Payment as separate records under the existing Expense/Payment rules.

**Scope**
- Phase 5 direct Vehicle expenses, Vehicle cost aggregation, and typed links to actual Accounting movements; Garage Job expense relationships are later-phase scope.

**Preserve unchanged**
- Sale, Purchase, Vehicle Expense, Accounting event, Cash/Bank movement, Investor Fund, and Company Running Capital remain distinct records with their existing ownership. The same Accounting movement mechanism does not imply one generic domain endpoint or merge source identities.

**Supersedes**
- None; this clarifies the direct Vehicle Expense relationship without changing Garage ownership or other module boundaries.

**Implementation impact**
- Define typed Vehicle Expense-to-Accounting links and use the existing accounting movement owner for actual money; keep domain records and partial installments individually identifiable.

### ADDITION — Vehicle Expense funding sources and customer billing boundary

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct cost attached to an Investor-funded Stock Vehicle uses available Investor Fund first. Record any uncovered amount as Vehicle-linked Company Running Capital; never overdraw the Investor Fund.
- This Vehicle cost and its funding allocation are not a Company Accounting Expense merely because the Company supplies the shortfall.
- A cost incurred for a customer's Vehicle belongs to the customer's Garage Job bill and remains later Garage-phase scope.

**Scope**
- Relationships among a Phase 5 Stock Vehicle Expense, Investor Fund use, Company Running Capital, actual Accounting movements, and future Garage Job costs.

**Preserve unchanged**
- Keep Vehicle Expense, Investor Fund source allocation, Company Running Capital, Accounting cash movement, and any later customer Job charge as distinct records. Q102's once-only actual movement rule and Garage deferral remain.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION WORDING: treating a direct Vehicle Expense as a generic Company Accounting Expense/Payment by default. Accounting still owns actual Cash/Bank movements; this decision does not remove or duplicate them.

**Implementation impact**
- Model the Vehicle cost and source allocations explicitly; link actual outflow through one typed Accounting movement. Customer Vehicle cost needs the later Garage Job relationship.

### ADDITION — module gates for Vehicle Expense source allocation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct Investor-funded Stock Vehicle Expense and its source allocation may be saved when Vehicle Management and Investment are ON.
- Accounting must also be ON to record an actual Cash/Bank payment. Saving the Vehicle cost/allocation while Accounting is OFF creates no Accounting event or movement.

**Scope**
- Module-state requirements for the Vehicle Expense/source-allocation relationship and its separate actual payment relationship.

**Preserve unchanged**
- Q103 source order remains Investor Fund first and exact Company Running Capital shortfall second. Purchase and Purchase correction gates remain their separately approved rules. Every actual cash movement remains Accounting-owned and recorded once.

**Supersedes**
- SUPERSEDES EARLIER Q102 UNRESOLVED GATE: module-state requirements for saving a direct Vehicle Expense and source allocation. It does not supersede any Purchase or Purchase-correction gate.

**Implementation impact**
- Check Vehicle Management + Investment at Expense/allocation save; check Accounting at actual-payment posting. Do not create partial cash records while Accounting is OFF.

### ADDITION — Vehicle Expense and partial payable relationship

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct Stock Vehicle Expense stores its full incurred amount once, whether paid, partially paid, or unpaid.
- The Expense owns a derived payable equal to the approved cost minus confirmed linked actual payments. One Expense may have zero, one, or multiple partial payments; cumulative payments cannot exceed its current outstanding amount.
- Each actual payment is a separate record linked to that Vehicle Expense and to one Accounting Cash/Bank movement. Payment does not add the same expense to Vehicle cost again.

**Scope**
- Relationship between the direct Vehicle Expense, its derived payable, partial/multiple payment records, and actual Accounting movements.

**Preserve unchanged**
- Q103 funding-source allocation and the distinction from Company Accounting Expense remain. Q104's Vehicle Management + Investment save gate and Accounting actual-payment gate remain. Customer Garage Job charges remain later-phase scope.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION AMBIGUITY: whether a Vehicle Expense is only recorded after full payment. It clarifies that the Vehicle Expense source may remain open with a derived payable.

**Implementation impact**
- Use one Vehicle Expense source, separately linked payment applications, and one Accounting movement per actual payment; derive the outstanding amount atomically.

### ADDITION — Vehicle Expense installment requires external reference

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Every actual payment installment for a direct Phase 5 Stock Vehicle Expense requires an operator-supplied external reference, such as a bank transaction ID or Cash voucher number.
- Keep the external reference on the typed Vehicle Expense payment and its linked Accounting event. It is traceability text, not record identity or an idempotency key.

**Scope**
- Actual partial and full installments settling direct Stock Vehicle Expenses in Phase 5.

**Preserve unchanged**
- Each payment remains a distinct record linked to its Vehicle Expense and one actual Accounting Cash/Bank movement. Q105 outstanding balance/cap and Q106 shared account preference remain.
- This decision does not impose duplicate-reference uniqueness or normalization rules, and does not change Buyer Receipt or Fund Credit reference rules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether a direct Vehicle Expense installment requires an operator-supplied external reference.

**Implementation impact**
- Require a nonblank external reference per installment; store it with the typed source and map it to AccountingEvent.source_reference without using it as a foreign key.

### ADDITION — Vehicle Expense payment reference uniqueness

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Reject a duplicate external reference for direct Vehicle Expense payments within the same Company and same Cash/Bank account, across all Branches.
- Compare after trimming leading/trailing spaces and ignoring letter case.

**Scope**
- Operator-supplied external references on actual direct Vehicle Expense installment payments.

**Preserve unchanged**
- The payment UUID and typed Vehicle Expense relationship remain record identity; the external reference remains traceability text. Q107's required-reference rule remains. No rule is added for Sale Receipts, Fund Credits, Seller installments, or other payment sources.

**Supersedes**
- SUPERSEDES EARLIER Q107 WORDING: no duplicate-reference uniqueness or normalization rule was approved for Vehicle Expense payments. This new rule applies only to the scope above.

**Implementation impact**
- Enforce normalized uniqueness by Company and Cash/Bank account across Branches without using the reference as a foreign key or idempotency key.

### ADDITION — actual vendor refund precedes downward Vehicle Expense correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A downward correction that would make confirmed Vehicle Expense payments exceed corrected cost is blocked until the vendor actually returns the excess and Accounting records the linked cash inflow.
- Preserve the original Expense, payment events, and refund event as separate source-linked records; then append the Expense correction.

**Scope**
- Relationship among a direct Stock Vehicle Expense, actual partial/multiple payments, actual vendor refund, and subsequent downward correction.

**Preserve unchanged**
- Q105 payable remains derived from source history. Q103 source allocation, Q104 module gates, and Q107/Q108 reference rules remain separate. No credit/prepayment is created for an unreceived refund.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether a Vehicle Expense correction may create an open vendor-refund balance before money is returned.

**Implementation impact**
- Enforce the refund-before-correction invariant inside the correction transaction; do not rewrite confirmed cash events or their history.

### ADDITION — recompute Vehicle Expense sources after correction

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- After a Q109-compliant Vehicle Expense correction, reallocate the corrected cost using available Investor Fund first and Company Running Capital for any exact shortfall.
- Preserve the original allocations; record the revised split as appended correction/allocation history. Do not preserve the old source ratio for Vehicle Expense corrections.

**Scope**
- Relationships among the corrected Vehicle Expense, available Investor Fund, Company Running Capital, and appended allocation adjustment.

**Preserve unchanged**
- Q94's original-source-proportion rule remains limited to Purchase corrections. Q103 Fund-first/Company-shortfall ordering, Q109 actual-refund-before-correction, and immutable cash history remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q109 IMPLEMENTATION ITEM: how the Vehicle Expense source allocation changes after cost correction.

**Implementation impact**
- Recheck Fund availability atomically at correction time and append source adjustments that reconcile exactly to corrected Vehicle cost.

### ADDITION — correction gate for Vehicle Expense source history

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Applying a Q109-compliant downward Vehicle Expense correction and Q110 source reallocation requires Vehicle Management, Investment, and Accounting ON, even when no cash moves in the correction command.
- If any is OFF, preserve the original Expense, payable, allocations, refund, and payment relationships unchanged.

**Scope**
- Corrected direct Stock Vehicle Expense and appended Investor Fund/Company Running Capital allocation history.

**Preserve unchanged**
- Q104 creation/payment gates apply to their separate operations. Q109 actual vendor refund must precede the correction; Q110 Fund-first reallocation remains. Purchase correction rules are separate.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q110 IMPLEMENTATION ITEM: required module set for applying the expense correction/reallocation.

**Implementation impact**
- Validate all three module states/revisions in one atomic correction command; do not append partial allocation or correction rows.

### ADDITION — Company-funded Stock Vehicle cost source

**Status:** APPROVED BUSINESS DECISION CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct Stock Vehicle cost with no Investor Fund source is fully linked to Company Running Capital. It has no Investor Fund allocation.

**Scope**
- Source relationship for non-Investor-funded Stock Vehicle costs.

**Preserve unchanged**
- Investor-funded costs use available Investor Fund first and Company Running Capital only for the exact shortfall. Customer Vehicle costs remain Garage Job scope.

**Supersedes**
- None; this records the already approved Q103 clarification for costs without an Investor Fund source.

**Implementation impact**
- Keep Vehicle cost, optional Investor Fund allocation, and Company Running Capital movement as distinct typed records; the no-Investor case links the full source amount to Company Running Capital.

### ADDITION — Vehicle Expense refund, Fund count, and historical correction (Q116–Q122)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle may use only one Investor's Fund. A direct cost without Investor Fund source remains Company Running Capital only.
- An actual Vendor refund is linked to its Vehicle Expense and requires Vehicle Management, Investment, and Accounting ON. No upper refund cap based on prior Vendor payments is approved.
- Upward Vehicle Expense corrections are allowed; recalculate available Investor Fund first, then Company Running Capital for the exact shortfall. Update the derived payable from corrected cost and actual payments.
- A downward correction requires all three modules even when no refund is needed. Apply the correction to the original Expense effective date and affected historical Investor calculation, while preserving the correction timestamp separately.

**Scope**
- Typed Vehicle Expense, source allocation, Vendor refund, payable, and correction relationships.

**Preserve unchanged**
- Original cost, actual payments/refunds, and source history remain append-only. Accounting owns actual Cash/Bank movements. Company Profit periods do not govern Investor Profit periods.

**Supersedes**
- None; these decisions add the missing scope around Q109–Q111 correction handling.

**Implementation impact**
- Derive balances from linked typed records. Classification of a Vendor refund exceeding net payments and the external-reference/duplicate rule for actual Vendor refunds remain open for clarification. A single Investor Fund per Vehicle is consistent with multiple credit records belonging to that same Investor.

### ADDITION — Vehicle Expense refund reference and excess allocation (Q118/Q123)

**Status:** APPROVED BUSINESS DECISION — LATEST CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vendor refund for a direct Vehicle Expense has no mandatory external reference and no duplicate-reference rejection.
- Record the actual Cash/Bank inflow once. Link to the Vehicle Expense only the amount supported by net actual payments; allow the Accountant to route any excess to another appropriate record. Never create a second movement or automatic Company Income for the excess.

**Scope**
- Source relationships and amount allocation for actual Vehicle Expense Vendor refunds.

**Preserve unchanged**
- Required/normalized references for Vehicle Expense installments under Q107/Q108 remain. Q117 allows the full actual refund to be received; Q123 governs how it is allocated. Q109 remains in force.

**Supersedes**
- SUPERSEDES EARLIER Q118 ANSWER: a required and unique external reference for Vendor refunds only. It does not affect expense installment references.
- SUPERSEDES EARLIER Q123 DETAIL only as to forcing one fixed record type/reason for the excess; manual destination selection remains available.

**Implementation impact**
- Model one actual cash event with linked amount allocations whose total reconciles to the cash received; detailed typed relationship/API design remains technical work.

### ADDITION — Phase 5 Vehicle refund and funding records (Q124–Q131)

- A Vehicle Expense refund is one immutable typed source record and one Accounting Cash/Bank inflow. Child allocations reconcile exactly to its actual amount; one allocation applies only up to the Expense's remaining net actual payments, and any excess needs an explicitly selected eligible destination. If none is available, reject the posting until a destination record is created.
- Allowed excess destinations must be typed same-Company relationships, not a free-form source ID. If the Accountant classifies an excess as Company Income, create a separate Income event with the selected category/note and link the actual Receipt to it; preserve all existing Income events unchanged. Never auto-classify or silently create an Income event.
- Investor Fund allocations and Company Running Capital allocations are separate typed source records linked to Vehicle Purchase/Expense costs. Their total must equal the approved cost; actual Cash/Bank movement is a different record and is created only for money actually received or paid.
- Company Running Capital is recorded as a Vehicle-linked exact shortfall without a pre-funded pool. Company-only Purchase does not require an Investor record. Investor-linked Expense and pooled-Fund Purchase/Expense allocation require a Company-level Accountant; Company-only Purchase/Expense may be recorded by a Branch Accountant within their authorized Branch.
