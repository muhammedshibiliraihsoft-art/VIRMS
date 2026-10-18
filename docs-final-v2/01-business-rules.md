# 01 — Business Rules

Vehicle Investment, Modification & Resale Management System  
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
- A funded Stock Vehicle has exactly one funding Investor; one Investor may fund many funded Stock Vehicles. The funding relationship belongs to Company and Vehicle, never to Branch.
- An external customer's Garage Vehicle does not require an Investor and does not enter Investor-finance merely because it has a Garage Job. Stock-Vehicle work and external-customer work remain distinct even when they use the same Garage capability.
- The current Stock Vehicle lifecycle is Purchased → In Work → Ready → Listed → Sold. Sold state and Buyer collection state are separate. A transfer does not create another Vehicle or reset its lifecycle.
- Approved Vehicle work/repair/modification, Labour and parts/material costs are traceable to the Vehicle and relevant Branch. Vehicle-level Labour cost and a worker's manual Labour Payment are distinct. Garage Job detail follows 10.
- The Company may actually contribute Running Capital for an approved Vehicle cost that Investor funds do not cover. Track exact contributions per Vehicle and keep them separate from Investor principal and Profit. A suggested recovery on a positive result is editable; actual recovery requires confirmation. No automatic Running-Capital Loss settlement exists.

## Investor Fund and positive Vehicle result

- An Investor's principal Fund is an auditable Company-level position shared across that Company's Branches. Initial and additional capital, approved use, actual recovery, withdrawals/settlements and linked corrections are transactions; no user overwrites a balance. Principal and Profit remain distinct. Investor-financed purchase or Expense cannot silently overdraw Available Investor Fund; a Company Running Capital contribution is a separate actual source.
- The agreed Sale Price and valid consolidated Vehicle cost support positive-result arithmetic. A Sale may be fully paid, partially paid or on credit. Actual Buyer Payments, remaining receivable, and Buyer refund obligations are distinct from the Sale agreement. A Sale confirmation alone does not finalize Investor/Company Vehicle settlement.
- Final Investor/Company settlement of a Vehicle occurs only after the full agreed Buyer Sale amount is collected and any required Buyer refund position is resolved. Provisional calculations before collection are not final settlement or Paid transactions.
- For a positive completed Vehicle result, the applicable configurable Investor agreement determines Investor Share; Company Share is the remaining positive result under the approved allocation. Company Share enters Company finances and is not immediate Owner income. An Investor percentage is within 0%–100%, inclusive, and is not hard-coded; 33% is an example of a rate sometimes used, not a default. Effective configuration and confirmed result snapshots are retained.
- Ordinary eligible deal-level Investor Profit may be paid while an Investor is Active, before Exit, after the existing full-collection and principal-recovery gates and actual Accountant confirmation. Calculation, eligibility and Paid are separate. Monthly Interim Payout is a different advance stream, not earned deal Profit and not guaranteed additional Profit.

## Company result and Owner distribution

- The bounded Company financial layer records Company Share from Vehicle business, Garage Revenue, Other Company Income and Company Expenses. The conceptual result is Company Share + Garage Revenue + Other Company Income − Company Expenses = Company Profit/Loss. The same transaction cannot be counted twice merely because Accounting and a business module both reference it.
- Owner Distribution comes from Company-level distributable Profit, not directly from a Stock Vehicle deal. Supported configured periods are Half-yearly and Annual. A due period or suggested allocation never transfers money; actual distribution is human-confirmed and audited.
- Owner recipients and percentages remain configurable with effective history. The documented 48.5% / 51.5% split is the current standard configuration available for Company-level Owner Distribution, not hard-coded columns or a mandatory split for every Company. Recipients in an applicable positive distribution configuration have nonnegative percentages summing to 100%; exact posted allocations conserve the confirmed distributable amount using 09.

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
- **BUSINESS DECISION REQUIRED:** Define the settlement priority/allocation when both Investor-funded cost and Company Running Capital exist, and the manual financial treatment of a confirmed Loss. Do not infer these from the former automatic Loss formula.
- **BUSINESS DECISION REQUIRED:** Define the Company-level distributable Profit base and period close/carryforward treatment, and the exact relationship between ordinary deal-level Investor Profit payments and six-month/annual reconciliation. No confirmed payment may be counted twice.
