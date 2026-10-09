# 04 — Data Model & Relationships

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — CONCEPTUAL DATA TRUTH SOURCE OF TRUTH

## Identity, scope, and ownership

Every persistent business/system entity has an immutable backend-generated UUID (or equivalent opaque globally unique system identity). Human-readable names, phone numbers, registration numbers, labels and storage URLs are mutable attributes. Tenant-scoped records carry an unambiguous Tenant context directly or through an authoritative parent. Backend authorization follows 02.

| Entity / record | Scope and essential relationship |
|---|---|
| Tenant / Garage | System operational boundary; one Garage = one Tenant |
| User, Role, Permission | Global identity/system rules; User ↔ Tenant via explicit historical Membership |
| Business Owner / Profit Recipient | Global recipient identity; may receive Owner allocation rows |
| Investor | Global; one Investor → many Vehicles, Fund entries, agreements, exit requests and settlements |
| Investor Fund Ledger | Global Investor principal ledger; event retains Vehicle and Tenant context where applicable, including audited Investor loss recognition and actual Owner loss coverage |
| Investor Profit Entitlement/Payment | Separate from principal; linked to Investor, Vehicle/Sale, snapshot and context |
| Vehicle | Exactly one funding Investor and one current Tenant; one Vehicle → many expenses/media/history records |
| Vehicle Tenant History | Historical transfer/origin context, never overwritten by current Tenant changes |
| Expense Category | Tenant-scoped configurable entity |
| Vehicle Expense | Tenant-scoped through Vehicle; one expense → one Vehicle and related Fund effect |
| Buyer | Tenant-scoped; required phone is a string attribute, not unique identity |
| Sale | Tenant-scoped through Vehicle; one Vehicle → at most one normal authoritative Sale |
| Sale Payment | Actual receipt linked to one Sale; individually preserved with correction/reversal link |
| Buyer Refund Payable / Payment | Correction-created obligation to return excess Buyer money after a reduced Sale Price, and separate actual refund events; original Buyer receipts remain preserved |
| Investor Profit Agreement | Global Investor-specific effective percentage history |
| Owner Split Configuration | System or Tenant effective version; one configuration → many recipient allocation rows |
| Distribution Snapshot | Immutable Sale/Vehicle percentage and result snapshot with Investor and Owner allocation rows |
| Investor Exit Request / Settlement | Global Investor lifecycle/financial records, linked to relevant Tenant/Vehicle positions |
| Financial Correction / Adjustment Obligation | Linked immutable correction, reversal, Additional Payable, Recovery / Adjustment Obligation and actual settlement records; original posting remains preserved |
| Owner Contribution Return Payable | Linked obligation to return an actual Owner Loss Contribution after a Loss-to-Profit correction from the same Investor Fund; reserve only Fund money currently held, keep any uncovered amount payable, and record an actual Fund debit on payment |
| Labour / Labour Payment | Tenant-scoped Labour and independently recorded manual payments |
| Media Asset / Vehicle Publication | Tenant-scoped through Vehicle; publication is separate from core lifecycle |
| GST / Tax / Invoice information | Optional data linked to applicable transactions/records; no full accounting or tax suite |
| Configuration / Audit / Correction | System or Tenant scope as relevant, with actor, time, version and source links |

## Time integrity

Every persisted timestamp whose ordering, auditability, financial meaning, lifecycle meaning, or security meaning matters must represent an unambiguous point in time and be timezone-aware. This applies where relevant to creation and update events, Vehicle lifecycle changes, Sale confirmation, Buyer Payments, Fund Ledger and Principal Recovery movements, Profit/Loss snapshots, configuration and percentage effective times, Profit eligibility and payment, Investor Exit and Settlement, Owner loss contributions, corrections, audit and authentication/session events, Tenant Merge, and order-sensitive background jobs. Authoritative persistence must not use naive timestamps; storage may be normalized without imposing a business-specific display timezone, provided the exact instant remains unambiguous.

## Financial source of truth

| Position | Authoritative record |
|---|---|
| Initial/additional principal | Valid Investor Fund Ledger credits |
| Principal use and recovery | Linked purchase/expense, actual Buyer recovery, Investor loss recognition and actual Owner loss-coverage Fund Ledger movements |
| Available Fund | Greater of zero or (Gross Fund Ledger Balance − outstanding Owner Contribution Return Payables − Buyer Principal Refund Reserves); Gross Fund Ledger Balance is net valid principal credits/debits before these reserves; cumulative Recovered Principal is not added again |
| Currently Used / Locked Principal | Sum of the Investor's nonnegative Outstanding Vehicle Principal positions, including deployed or financially unresolved Vehicle principal |
| Retained Owner Loss Contributions | Actual Owner Loss Contributions − actual contribution returns paid − amounts designated as Owner Contribution Return Payables |
| Outstanding Vehicle Principal | Original Vehicle Principal Used − net confirmed Buyer Principal Recoveries after linked allocation corrections − confirmed Investor Loss Recognition − Retained Owner Loss Contributions + principal correction increases − principal correction decreases; nonnegative |
| Recovered Principal | Cumulative net valid actual principal recovery/coverage movements with distinct sources and linked correction/refund adjustments; redeployment does not reduce it and original history remains visible |
| Purchase Cost | Vehicle purchase source record |
| Total Vehicle Expense | Valid individual Vehicle Expenses |
| Total Vehicle Cost | Purchase Cost + valid approved Vehicle Expenses |
| Agreed Sale Price | Sale record |
| Gross Buyer Cash Received | Valid confirmed Sale Payments − actual Buyer refunds; pending refund obligations do not erase historical receipts |
| Buyer Refund Payable | Greater of zero or (gross confirmed Sale Payments − actual Buyer refunds − corrected Agreed Sale Price) after a Sale correction |
| Sale Applied Buyer Amount | Gross Buyer Cash Received − outstanding Buyer Refund Payable; only this amount applies to corrected Sale collection |
| Receivable | Corrected Agreed Sale Price − Sale Applied Buyer Amount; nonnegative |
| Profit/Loss and recipient shares | Calculation from agreed Sale Price, Vehicle cost and applicable historical percentages; finalized in Distribution Snapshot |
| Profit Paid | Separate explicit payout transactions/confirmations |
| Settlement position | Settlement linked to authoritative Fund, Sale, payment, entitlement and correction history |

No independent editable balance or capital total may compete with these sources. Caches, projections, and reports must be rebuildable/reconcilable. Principal and Profit use separate records and never merge automatically.

Current authoritative money is INR. Persist final posted monetary amounts at two decimal places using fixed-precision decimal arithmetic and `ROUND_HALF_UP`; never use binary floating point as financial authority. Intermediate calculations may retain greater decimal precision. Allocation uses the historical percentage/configuration snapshot, derives Owners Pool from the rounded Investor share, and assigns any smallest-unit Owner allocation residual to the final recipient in the configured order so finalized allocations exactly equal authoritative Profit/Loss.

## Financial relationships and snapshots

- Purchase and Vehicle Expense fund effects must link to the corresponding source records and Investor Fund Ledger entries.
- Investor-specific Profit Agreements have effective history; one applicable agreement applies at the relevant Sale calculation point.
- Owner Split Configuration uses recipient allocation rows. The allocation percentages for an applicable configuration form a complete valid split; do not encode only fixed Owner 1/Owner 2 amount columns. Current standard is 48.5% / 51.5% of Owners Pool.
- Investor percentage is inclusive 0%–100%. Owner recipient percentages are nonnegative and sum to exactly 100% of Owners Pool; a positive Owners Pool requires at least one configured recipient, and a zero Owners Pool produces no Owner allocation for that deal. Both 0% and 100% Investor boundaries are valid.
- At authoritative Sale confirmation, snapshot agreed price, valid cost, result, Investor percentage, Owner configuration/version, and per-recipient positive-profit or loss allocations. Later settings changes never mutate completed snapshots.
- Calculated entitlement, eligibility, and actual payment are separate. A negative result creates loss allocation facts, not positive-profit payouts. Investor-borne loss is an audited reduction of the principal claim, not a receipt. Each Owner-borne share is a source-tagged actual contribution into the same Investor Fund before that share of outstanding principal is treated as resolved.
- Sale Payment, actual Buyer refund and Principal Recovery are distinct but traceably linked events. A sold Vehicle can retain a receivable, Buyer Refund Payable, unpaid profit, or unresolved principal. A refund obligation is created only by an authorized correction, never by accepting a new payment above Remaining Receivable.
- A Buyer Principal Refund Reserve is the principal-backed part of an outstanding Buyer Refund Payable that had previously credited the Investor Fund but is no longer applied to the corrected Sale. Reserve only Fund money actually held; an uncovered amount remains payable and blocks final Settlement. Actual refund of that principal-backed part records a linked Fund debit and reduces the reserve and Buyer Refund Payable; the collected-Profit part has no Investor Fund debit. Preserve the original receipt and its allocation history.
- A confirmed Buyer refund must satisfy `0 < Refund Amount <= Outstanding Buyer Refund Payable` and be duplicate/concurrency-safe. Its linked principal-backed and collected-Profit components must reconcile to the amount actually refunded. An unpaid Buyer Refund Payable keeps corrected Profit payout ineligible and blocks final Settlement.
- A cost or Sale correction that changes the principal-first use of an already confirmed Buyer Payment records a linked allocation adjustment between collected Profit and Buyer Principal Recovery. The original receipt is preserved; the net valid principal allocation determines Outstanding Vehicle Principal, while the Fund reconciles through a linked credit/debit or a Buyer Principal Refund Reserve pending actual refund. No new Buyer receipt or duplicate recovery is created.
- A valid new Sale Payment is greater than zero and cannot exceed current Remaining Receivable. A valid new Profit Payment is greater than zero and cannot exceed the recipient's current Outstanding Eligible Entitlement. Enforce both limits atomically under concurrency; neither receivable nor outstanding entitlement may become negative.
- Settlement may span multiple Tenants because Investor identity and Fund are global.
- Buyer recovery and Owner loss coverage remain separately traceable, even when both contribute to resolving a Vehicle principal position. Allocation calculation alone never creates a Fund credit. Final Settlement cannot close while required Owner coverage is unpaid or other positions remain unresolved.
- Current Investor Principal Claim = valid initial/additional Investor principal − confirmed principal settlements paid to the Investor − confirmed Investor Loss Recognition + principal claim increases from linked corrections − principal claim decreases from linked corrections. Owner Loss Contributions cover a shortfall and credit the Fund but do not increase this Investor claim. It must reconcile to Gross Fund Ledger Balance + Currently Used / Locked Principal − outstanding Owner Contribution Return Payables − Buyer Principal Refund Reserves, equivalently Available Fund + Currently Used / Locked Principal − any combined reserve amount not covered by the Gross Fund Ledger Balance.
- A Loss-to-Profit correction may leave an Owner Contribution Return Payable larger than the current Gross Fund Ledger Balance because previously contributed money was redeployed. Record the correction and full payable without inventing liquidity or making Available Fund negative. The uncovered amount stays unresolved until actual Fund money permits recorded payment; final Investor Settlement remains blocked.
- Outstanding Eligible Investor Profit = sum across the Investor's deals of the greater of zero or (corrected current Eligible Investor Profit Entitlement − confirmed valid Investor Profit Payments). An Additional Payable representing that same positive difference labels the amount and is not added again.
- Once all Vehicle principal and required positions resolve and Owner Contribution Return Payables and Buyer Refund Payables are actually paid, Principal Settlement Payable equals Available Fund and must equal Current Investor Principal Claim; mismatch remains unresolved. Investor Settlement Payable = Principal Settlement Payable + Outstanding Eligible Investor Profit. Obligations owed by the Investor and return/refund payables are recorded and settled separately, with no automatic netting.
- Each confirmed Principal Settlement payment has a linked Investor Fund Ledger debit and reduces both Available Fund and Current Investor Principal Claim by its amount. A calculated payable or status change has no Fund effect.
- Settlement closure requires resolved Locked Principal, Vehicle principal, Buyer receivables and Buyer Refund Payables, required Profit positions, Owner Loss Contributions and correction obligations, a reconciled principal position, and recorded payment of all settlement payables.

## Retention, correction, and integrity

- Preserve Investor/Fund, Vehicle/Tenant transfer, Expense, Sale, Buyer Payment, Profit Snapshot, Profit Payment, Settlement, Labour Payment, Membership, Configuration and Audit history. Closing, inactivating, transferring, or consolidating does not hard-delete historical identity.
- Corrections use linked reversal/adjustment or equivalent immutable history with actor, time, previous/new values, original snapshot, reason, and source reference. Before payout, the linked adjustment changes current outstanding entitlement without erasing the original calculation. After payout, preserve confirmed payments and record the difference between corrected entitlement and confirmed payments as Additional Payable, Recovery / Adjustment Obligation, or zero. Actual settlement of an obligation is a separate authoritative event.
- Profit-to-Loss, Loss-to-Profit, and amount-changing corrections use the original deal's historical percentage/configuration snapshot. Correction-created unresolved adjustments remain open even if an earlier Settlement closure is preserved historically.
- For Profit-to-Loss, corrected positive-Profit Entitlement is zero; confirmed prior Profit Payments become Recovery / Adjustment Obligations, while corrected Loss allocations are recorded separately. For Loss-to-Profit, reverse Investor Loss Recognition through a linked principal adjustment and create separate Owner Contribution Return Payables for actual prior contributions; reserve only Fund money currently held and record an actual same-Fund debit on payment. Corrected Profit is then allocated from the original snapshot. Do not silently net these positions.
- Enforce one Investor per Vehicle, Tenant consistency of linked records, valid controlled percentages, nonnegative normal Available Fund, valid Sale Payment totals, and unique/idempotent critical operations at backend/database boundaries.
- Buyer and Labour are not automatically merged by name or phone. Vehicle registration and Garage name are not identity.
- Public Vehicle access uses a dedicated approved-safe projection; never expose private fields by serializing an internal entity.

## Current non-scope

No Cash/Bank account entities, cash-versus-bank operational ledger, General Garage Expense, Labour login/Vehicle assignment/Work-Type assignment/payroll/attendance, full CRM, manual loss-bearer selector, or normal user-facing Tenant Merge entity/workflow.
