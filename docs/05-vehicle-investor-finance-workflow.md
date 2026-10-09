# 05 — VEHICLE / INVESTOR / FINANCE WORKFLOW

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH


## 1. PURPOSE & AUTHORITY

This document defines the operational/financial sequence between:

Investor
→ Investor Fund
→ Vehicle
→ Vehicle Expenses
→ Sale
→ Buyer Payments
→ Principal Recovery
→ Profit Distribution
→ Investor Settlement

Authority:
- 01 defines business rules.
- 02 defines roles/permissions.
- 03 defines modules.
- 04 defines entities, ledgers, relationships and sources of truth.
- 05 defines workflow/state transitions.

Latest explicitly locked decisions override older conflicting wording.


## 2. CORE FINANCIAL INVARIANTS

WF-001
Investor is global, not Tenant-owned.

WF-002
Investor Fund is global.
Vehicle-related fund movements retain Vehicle + Tenant context.

WF-003
One Vehicle → exactly one Investor.
One Investor → many Vehicles.

WF-004
Principal and Profit are separate.

Profit must never automatically become Principal.

WF-005
Normal operations must not create a negative Available Fund.

WF-006
Unreceived Buyer money must never be treated as:
- Received
- Recovered Principal
- Available Fund
- Paid Profit

WF-007
Historical financial truth must not be silently overwritten or deleted.

WF-008
Critical financial writes must be atomic and duplicate-safe.


## 3. INVESTOR & FUND WORKFLOW

Accountant may:
- Create Investor.
- Set Investor-specific profit percentage.
- Add Initial Fund.
- Add Additional Fund.
- Manage operational Investor finance.

Investor-specific percentage changes must preserve history.

System/Tenant default percentage configuration belongs to Back Office.

Fund position must distinguish:

- Total Principal Fund
- Available Fund
- Currently Used Fund
- Recovered Principal
- Profit Earned
- Profit Paid
- Profit Pending

Additional Fund creates a new historical fund transaction.


## 4. VEHICLE PURCHASE & CAPITAL

Before purchase:
- Investor must be valid.
- Investor must have sufficient Available Fund.
- Investor must not be blocked from new purchase by Exit Notice.
- Vehicle must have Tenant context.
- Vehicle must have one Investor.

Purchase workflow:

Validate
→ Create Vehicle/Purchase
→ Reduce Available Fund
→ Increase Currently Used Fund
→ Record Fund Ledger Entry
→ Vehicle = Purchased

Vehicle Capital Used:

Purchase Cost
+ Approved Vehicle Expenses
= Total Vehicle Cost


## 5. VEHICLE LIFECYCLE

Current lifecycle:

Purchased
→ In Work
→ Ready
→ Listed
→ Sold

Do not add unnecessary primary statuses in the current phase.

Vehicle sale status and Buyer collection status are separate.

A Vehicle may therefore be:

Sold + Pending/Partially Received

or:

Sold + Fully Received


## 6. VEHICLE EXPENSE WORKFLOW

Every current-scope operational Vehicle Expense belongs to a Vehicle.

Expense must use the Investor assigned to that Vehicle.

Workflow:

Vehicle Expense
→ Validate Vehicle/Investor/Fund
→ Reduce Available Fund
→ Increase Vehicle Capital Used
→ Record Fund Ledger Entry

Expense categories are dynamic and must not be permanently hard-coded.

No separate General Garage Expense workflow exists in the current scope.


## 7. SALE WORKFLOW

Current Sale types:

- Full Payment
- Partial Payment
- Credit Sale

Sale requires:
- Vehicle
- Buyer
- Agreed Total Sale Price
- Applicable Investor percentage
- Applicable Owner Split configuration

Buyer Phone Number is required but is not system identity and is not assumed globally unique.

On Sale confirmation:

Sale created
→ Vehicle = Sold
→ Profit/Loss calculated
→ Applicable percentage/configuration snapshot preserved
→ Collection state begins

Profit calculation uses the full Agreed Sale Price, not only the amount already received.


## 8. BUYER PAYMENT & RECEIVABLE

Each actual Buyer receipt must be recorded as a Sale Payment.

Amount Received
= Sum of valid Sale Payments

Amount Pending
= Agreed Sale Price − Amount Received

Collection states:

1. Pending / Partially Received
2. Fully Received

Fully Received means Buyer collection is complete.

It does NOT automatically mean Investor/Owner profit has been paid.


## 9. PRINCIPAL RECOVERY — LOCKED MODEL

Actual received Buyer money gradually recovers Vehicle Principal.

Allocation order:

Actual Buyer Payment
→ Outstanding Vehicle Principal first
→ Collected Profit portion after Principal recovery

Unreceived money never creates recovery.

Recovered Principal returns to the same Investor's global Fund.

If Investor is Active, recovered principal may be reused for another Vehicle or approved Vehicle Expense.

If Investor is in Exit Requested / Settlement Pending, recovered principal must not fund a new Vehicle.


## 10. RECOVERED PRINCIPAL MUST BE CUMULATIVE

Recovered Principal is historical cumulative recovery.

Reusing recovered money must NEVER reduce the previously recorded Recovered Principal value.

Example:

Vehicle A recovered principal = ₹2,00,000.

If the same ₹2,00,000 is later used for Vehicle B:

Vehicle A Recovered Principal = ₹2,00,000
Available Fund decreases
Vehicle B Currently Used Fund increases

Recovered Principal must NOT become ₹0.

Therefore:

Recovered Principal
= cumulative principal historically recovered

Available Fund
= principal currently available for deployment

Currently Used Fund
= principal currently deployed in Vehicles


## 11. PROFIT CALCULATION

Per Vehicle:

Profit / Loss
= Agreed Sale Price − Total Vehicle Cost

For positive Profit:

Investor Profit Share
= Profit × applicable Investor %

Owners Pool
= remaining Profit after Investor Share

Owner Shares
= Owners Pool × applicable Owner allocation %

Investor Share and Owner Shares both come from PROFIT, not directly from Sale Price.

Percentages must not be hard-coded.

Completed deals preserve the percentage/configuration snapshot used for that deal.


## 12. PROFIT COLLECTION STATES

The system automatically calculates:

- Total Profit
- Investor Entitlement
- Owners Pool
- Individual Owner Entitlements
- Amount collected toward Profit
- Amount still pending

Before full Buyer collection, calculated entitlements remain visible as pending/calculated values.

After full Sale collection, they become fully collected/eligible values.

Exact UI styling belongs to 07, but intended presentation is:

Pending/calculated → muted/grey
Fully collected/eligible → clear/green

Green/eligible does NOT mean Paid.


## 13. PROFIT PAYOUT MODE — CONFIGURABLE

Do NOT hard-code one payout-timing method.

Support controlled choice between:

MODE A — KEEP PENDING
Keep profit entitlement pending until full Buyer collection.

MODE B — ALLOW EARLY PAYOUT
After Vehicle Principal has been recovered, allow payout from profit money that has actually been collected.

Rules:
- Principal recovery always comes first.
- Unreceived profit cannot be paid.
- System must calculate each recipient's entitlement/outstanding amount.
- No forced recipient payout order is required.
- Payout may remain pending or be confirmed against eligible collected profit.


## 14. PROFIT PAYMENT REQUIRES EXPLICIT CONFIRMATION

Profit Paid must NEVER be set automatically merely because profit was calculated or collected.

System must automatically calculate the amount due.

Actual payout requires an explicit Accountant confirmation.

Conceptual flow:

Calculated Entitlement
→ Eligible Collected Amount
→ Review
→ Confirm Payment
→ Profit Paid

Before confirmation, status remains unpaid/pending.

Actual payment cannot exceed:
- Recipient outstanding entitlement
- Legitimately collected/eligible profit

Exact popup/UI design belongs to 07.


## 15. LOSS WORKFLOW

If:

Agreed Sale Price < Total Vehicle Cost

show:

Loss = Total Vehicle Cost − Agreed Sale Price

Current scope has NO separate:
- Investor-loss selector
- Owner-loss selector
- Shared-loss selector
- Loss allocation engine

Loss belongs to the Vehicle deal.

Allow an optional Loss Note/Explanation.

Example:
"Unexpected engine replacement increased final cost."

The note explains the loss but does not manually alter financial calculations.

Do not automatically create profit distributions for a negative-profit deal.


## 16. INVESTOR EXIT

Lifecycle:

Active
→ Exit Requested
→ Settlement Pending
→ Closed

Normal Exit requires:
- Terms & Conditions acceptance.
- Three-month notice.

After Exit Notice:
- New Vehicle purchase using that Investor Fund is blocked.
- Existing already-funded Vehicle work may continue.
- Existing approved expenses may continue.
- Sales/Receivable collection continues.
- Principal recovery continues.

Unsold Vehicle capital remains locked until actual recovery.

Notice expiry does not manufacture recovered money.


## 17. SETTLEMENT

Settlement must consider the Investor's global position across relevant Tenants:

- Available Principal
- Currently Used / Locked Principal
- Recovered Principal
- Profit Earned
- Profit Paid
- Profit Pending
- Pending Receivables
- Unsold Vehicles
- Corrections
- Final Balance

Settlement order conceptually:

Recover/resolve Principal
→ Resolve applicable Profit
→ Final Settlement
→ Closed

Investor must not be financially closed while required unresolved financial positions remain.


## 18. EXCEPTIONAL EARLY CLOSURE

Exceptional Early Closure is not Investor self-service.

Latest authority:

Accountant / Operations Admin
→ initiate/manage
→ mandatory audit

Owner:
→ read/view/audit only

Early Closure does not override:
- Locked Vehicle capital
- Actual recovery requirements
- Pending receivables
- Settlement requirements


## 19. FINANCIAL CORRECTIONS

Accountant may perform legitimate controlled corrections.

Never silently overwrite/delete old financial truth.

Preserve as applicable:
- Original value/record
- Corrected value/record
- Changed by
- Date/time
- Reason
- Investor
- Vehicle
- Tenant
- Sale/Payment reference

Use reversal/compensating entries for transaction-style financial corrections where appropriate.


## 20. TRANSACTION SAFETY

The following must be atomic/idempotent where applicable:

Vehicle Purchase
→ Vehicle + Fund Debit + Ledger Entry

Vehicle Expense
→ Expense + Fund Debit + Cost Effect + Ledger Entry

Sale Confirmation
→ Sale + Sold State + Profit Snapshot

Buyer Payment
→ Payment + Received/Pending Position + Principal Recovery + Fund Entry

Profit Payment
→ Confirmation + Payment Record + Paid/Pending Update

Settlement
→ Validation + Settlement Entries + Lifecycle Update

Timeout/retry must not create duplicate financial transactions.


## 21. TENANT CONTEXT

Investor = Global
Investor Fund = Global
Vehicle = Tenant-scoped

Relevant financial movements retain:
- Investor
- Vehicle
- Tenant context

Vehicle Tenant movement must preserve historical Tenant context.

Tenant changes must never rewrite historical financial truth.


## 22. CURRENT NON-SCOPE

Do not introduce:

- Dedicated Cash Account module
- Dedicated Bank Account module
- Cash-vs-Bank ledger
- General Garage Expense module
- Full Accounting suite
- Payroll
- Attendance
- Labour Vehicle Assignment
- Labour Work-Type workflow
- Worker-level Vehicle costing
- Full CRM
- Separate Loss Allocation engine
- Normal Tenant Merge workflow
- AI-generated financial truth


## 23. END-TO-END FLOW

Investor Setup
→ Initial/Additional Fund
→ Vehicle Purchase
→ Vehicle Expenses
→ Ready
→ Listed
→ Sale
→ Profit/Loss Calculation
→ Buyer Payment(s)
→ Principal Recovery
→ Recovered Principal / Available Fund
→ Collected Profit
→ Pending or Eligible Profit
→ Explicit Profit Payment Confirmation
→ Settlement where applicable


## 24. NON-NEGOTIABLE RULES

1. One Vehicle = One Investor.
2. One Investor may fund many Vehicles.
3. Investor/Fund are global.
4. Principal ≠ Profit.
5. Profit never automatically becomes Principal.
6. Unreceived money is never available/recovered money.
7. Actual Buyer payments recover Principal first.
8. Recovered Principal is cumulative history.
9. Reusing recovered money never reduces Recovered Principal.
10. Available Fund and Recovered Principal are different values.
11. Profit uses full Agreed Sale Price.
12. Investor + Owner shares both come from Profit.
13. Profit payout timing is configurable: Pending or Early Eligible Payout.
14. Profit Paid always requires explicit confirmation.
15. Loss is shown at deal level with optional note; no separate loss-allocation engine.
16. Percentage changes never rewrite completed deals.
17. Exit Notice blocks new Vehicle purchase, not legitimate existing commitments.
18. Locked capital remains locked until actual recovery.
19. Owner remains operationally read-only.
20. Accountant is the normal operational finance authority.
21. Financial history must remain auditable.
22. Critical financial operations must be atomic and duplicate-safe.


## 25. DOCUMENT STATUS

05 — VEHICLE / INVESTOR / FINANCE WORKFLOW

Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH

This document is authoritative for workflow only.

Implementation must use 01–04 for business definitions, permissions,
module boundaries, entity relationships and data-source details instead
of duplicating or inventing those rules here.
