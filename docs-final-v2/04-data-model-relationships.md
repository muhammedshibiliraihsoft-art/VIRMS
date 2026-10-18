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
| Funded Stock Vehicle | One stable Company-wide Vehicle identity, exactly one funding Investor, one current Branch/location and a history of movements |
| External Customer Vehicle | Company Garage Vehicle identity associated with customer work; no Investor requirement or Fund movement by default |
| Vehicle Movement | Source/current Branch, authorized action, time and history; does not duplicate or rewrite Vehicle identity |
| Garage Job / work entry | One Company, relevant Branch, Vehicle context, work, Labour/materials, charge/cost/status and history; stock versus external customer flow is explicit |
| Expense Category / Expense | Company classification with Branch attribution where relevant; approved Vehicle Expense belongs to one Vehicle and source funding is traceable |
| Buyer and Stock Vehicle Sale | Buyer identity within Company; Sale linked to one Stock Vehicle and current agreed price; Buyer phone is required but not unique identity |
| Buyer Payment / refund | Individual actual receipt and separately confirmed actual refund, each linked to Sale and correction history |
| Company Ledger / receipt / payment | Company financial source and linked classifications, with Branch attribution where relevant; source business events are not counted as another independent amount |
| Running Capital contribution/recovery | Actual Company-funded amount linked to one Stock Vehicle, source, Branch context, time and subsequent confirmed recovery; never Investor principal or Profit |
| Investor positive-share agreement / snapshot | Investor-specific effective percentage and completed positive-result snapshot, with Company Share derived as applicable remainder |
| Monthly Business Cycle / Interim Payout | Investor-specific cycle day, effective rate and eligible-principal basis; suggestion and confirmed actual payment are distinct |
| Investor reconciliation / recoverable | Configured six-month/annual period; earned Profit, confirmed earlier payments and one current payable/recoverable position with partial settlement history |
| Company result / Owner Distribution | Company period result, confirmed distributable amount, effective recipient split, proposed allocations and separately confirmed actual payments |
| Investor Exit / Settlement | Company-level lifecycle and financial closure spanning the Investor's Stock Vehicles in that Company |
| Media Asset / publication | Vehicle-linked with Company and current/relevant Branch context; publication separate from core lifecycle |
| Configuration / module state / audit / correction | Effective Company or Platform scope, version, actor, time, reason and linked original/current position |

An Investor, Fund, Stock Vehicle, Buyer, Job or Ledger record of one Company must never become another Company's record merely because a Platform user can see both. Whether one human Investor or Owner may have separate Company relationships does not authorize a cross-Company financial balance.

## Authoritative financial sources

| Position | Authoritative basis |
|---|---|
| Investor supplied principal | Confirmed initial/additional funding and linked corrections in the Company-scoped Investor Fund history |
| Investor Available/committed principal | Valid Fund use/recovery/settlement events and current reservations or unresolved positions; derived, never manually overwritten |
| Company Running Capital | Actual Company contribution and actual recovery events linked per Stock Vehicle, separate from Investor Fund |
| Stock Vehicle cost | Purchase cost plus valid approved Vehicle and Garage Job Expenses, counted once regardless of module view or source of funding |
| Sale price and Buyer receivable | Authoritative agreed Sale and individually confirmed Buyer payments/refunds, including linked Sale corrections and open refund payable |
| Positive Investor and Company Share | Agreed positive-result calculation under the applicable effective Investor percentage and completed snapshot; confirmed adjustments remain separate |
| Interim Paid | Only actual confirmed Monthly Interim Payout transactions, not reminders or suggestions |
| Investor recoverable | Confirmed interim overpayment relative to reconciled earned entitlement, less actual direct repayment and separately confirmed future-Profit adjustments; no duplicate or negative open position |
| Garage revenue | Actual external-customer Job charge/receipt and relevant receivable records, reconciled with Accounting without double entry of economic revenue |
| Company Profit/Loss and Owner distribution | Company-level classified sources, period result, approved distributable position, effective recipient split and confirmed distribution payments |
| Manual Loss impact | Explicit confirmed manual Investor/Company decisions and actual related transactions with reason; no automatic allocation or posting from a negative arithmetic result |

Reports, dashboards, caches and projections are derived and rebuildable; they cannot compete with their source transactions. Money is current INR, final posted amounts use fixed-precision decimal at two places with `ROUND_HALF_UP`, and binary floating point is not an authoritative money or percentage representation. Do not count one receipt, recovery, Expense, interim payment or Company Share twice because it appears in multiple views.

## Vehicle, Branch and module history

The Vehicle remains one Company identity through all Branch moves. Its current Branch changes by an audited movement; prior Jobs, Expenses and source Branch attribution remain on their original events. Authorized same-Company users may read previous-Branch history; cross-Branch editing follows 02. A module being OFF cannot delete historical events, break references or hide actions needed to resolve an open obligation. Re-enabling uses the retained records.

## Investor, Company and Owner relationships

One funded Stock Vehicle has one Investor. External customer Garage Vehicles have no required Investor relationship. Investor-specific positive percentages and monthly rates have effective history; a completed positive Vehicle allocation retains its applicable configuration snapshot. Company Share is a Company financial source, not an Owner receivable. Owner allocations use a separate Company-level distribution configuration and period snapshot. Historical percentage and actual payment events survive later configuration changes.

## Corrections, retention and integrity

Do not hard-delete a Sold Vehicle, finalized Sale, confirmed payment, financial correction, Fund transaction, movement, Job financial record, distribution or relevant audit history. A legitimate edit before finalization may be direct where safe; finalized/paid facts use linked correction, reversal or adjustment with source, actor, timezone-aware time, prior/new values and reason. Repeated corrections reconcile one current position from gross events, confirmed reversals, actual payments/refunds/recoveries and open adjustments. An amount already settled has no second economic effect. Financial writes enforce nonnegative authoritative open positions, Tenant/Branch consistency, atomicity and duplicate/concurrency protection.

## Unresolved financial definitions

- **BUSINESS DECISION REQUIRED:** Specify the exact eligible-principal basis for a Monthly Interim Payout and how an authorized partial principal withdrawal can occur without using locked/unrecovered capital.
- **BUSINESS DECISION REQUIRED:** Specify Buyer collection allocation and final settlement priority among Investor-funded principal, actual Company Running Capital and positive Profit when both funding sources exist; a provisional suggestion must not become an unauthorized posted allocation.
- **BUSINESS DECISION REQUIRED:** Specify manual Loss impact on Investor principal claim and Company money, and the precise Company distributable-Profit basis. Until then, no automatic formula may invent these positions.
