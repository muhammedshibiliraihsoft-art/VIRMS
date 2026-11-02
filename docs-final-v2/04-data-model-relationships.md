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
