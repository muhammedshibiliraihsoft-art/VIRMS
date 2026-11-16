# 07 — UI / Navigation Structure

Status: DRAFT V2 — UI and navigation source after approval

This document defines interface structure and state presentation. Roles follow 02; finance follows 05 and 09; Garage work follows 10; images follow 08. UI visibility never grants permission.

## Application shell and visual reference

Preserve the approved SGTP reference shell layout and interaction pattern with a reserved unbranded logo slot, reusable navigation icons, header actions and page content. Desktop/laptop uses a fixed left sidebar with compact/expanded states, active destination, account area, sticky top header and independently scrollable main content. Tablet/phone uses top header, a few high-priority bottom destinations and a More sheet for secondary destinations. Support safe areas, keyboard-safe forms, touch controls, responsive density, long localized text and RTL/LTR layout. Use Light, Dark and System semantic states without copying SGTP branding or business behavior.

The pinned visual reference is repository `muhammedshibiliraihsoft-art/sgtp`, branch `frontend/parallel-foundation`, commit `9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`. It is a stable layout/interaction snapshot only. Do not copy its logo, tailoring domain, Shop assumptions, entities, APIs, tenancy, permissions or finance.

## Company, Branch and module context

Show the current Company context and relevant Branch or authorized Company-wide context. A Vehicle detail keeps its Company-wide identity visible while current Branch and movement history are shown separately. A Branch selector filters authorized scope and never grants access. A disabled module does not appear as an ordinary new-work destination; authorized historical views and required open-position resolution paths remain discoverable. Re-enabling restores normal supported navigation without recreating data.

## Role navigation

| Role | Primary areas | Context and restriction |
|---|---|---|
| Owner | Overview, Company/Branch Reports, Investors, Vehicles, Accounting result, Garage, Sales | Fund, Running Capital, Owner Distribution, Settlements, Audit and Owner AI as authorized; read-only |
| Accountant / Operations | Overview, Accounting, Investors/Fund, Vehicles, Sales/Receivables, Garage Jobs, Investor reconciliation | Expenses, Buyers, Labour, Media, Owner Distribution confirmation, Reports and Corrections within explicit permission |
| Investor | Overview, own Fund Position, My Stock Vehicles, Interim Payouts, Profit/Reconciliation, Exit/Settlement | Own confirmed payments, recoverable and history; other Vehicles only through public view |
| Media | Eligible Vehicles, Images, Public Details, Publication | Public availability/status only; no Investor/Company finance or core lifecycle controls |
| Platform Back Office | Companies, Branches, Users/Access, Modules/Protected Financial Configuration, Platform Audit, authorized Financial Review | Protected Investor/Owner percentages, sensitive Company defaults and business rates require specific backend permission and audit; routine Company financial posting remains separate |
| Labour | None | No login |

Not every module needs a top-level destination. Use record details/tabs and mobile More for lower-priority destinations. Existing Investor Portal, Media, public-safe views, Reports, Audit, Owner and Accountant surfaces remain part of the product.

## Vehicle, Garage and finance details

- Stock Vehicle detail groups Company identity, current Branch/movement history, funding Investor, purchase, core lifecycle, Branch Jobs/work, approved Expenses, Running Capital, Sale/Buyer collection, positive Investor/Company result, media and audit according to permission. Historical Branch entries remain visible to authorized same-Company users; edit actions reflect original Branch and correction authority.
- External customer Garage Vehicle/Job detail shows customer, Branch, work, Labour/materials, charge, actual receipts, remaining balance, status/history and audit. It does not display an invented Investor Fund panel.
- Sale detail distinguishes agreed price, confirmed Buyer Payments, Sale Applied Buyer Amount, Remaining Receivable, correction-created Buyer Refund Payable and actual refunds. Sold is distinct from Pending/Partially/Fully Received. Pending refundable cash is not displayed as settled Sale revenue.
- Positive Vehicle result shows provisional versus confirmed Investor Share, Company Share and exact actual Running Capital contribution/recovery separately. After full collection, display Investor principal and Company capital reconciliation before the remaining positive-result allocation. Capital recovery is labelled as capital, never Company Income/Profit; Company Share links to Company accounting rather than an immediate Owner payout. A negative result leads to manual Loss review, confirmed impacts, reasons and actual actions; do not show an automatic loss-bearer allocation.
- Company result view distinguishes Vehicle Company Share, Garage Revenue, Other Income, Company Expenses, Branch filtering, Company-consolidated result, confirmed distributable Profit, suggested Owner allocation and actual payments. An ended period or suggestion is not Paid.
- Investor view distinguishes principal, committed/available positions, ordinary eligible deal Profit, Monthly Interim Due/Suggested and confirmed Paid history, six-month/annual reconciliation, payable/recoverable and partial future adjustments. A reminder cannot be presented as a payment. Ordinary deal Profit paid while Active is retained history and not duplicated at Exit.
- Exit view shows Terms acceptance, notice, unresolved Vehicles/Buyer balances, Fund and principal reconciliation, separate interim/Profit/recoverable positions, remaining Principal Settlement Payable and remaining eligible Profit. For final closure show principal payment first, then remaining eligible Profit, with all blocking positions resolved and actual payments recorded.
- Platform Back Office shows Company, Branch, module state, protected Investor positive-share agreements, Owner distribution percentages, sensitive Company financial defaults/business rates, accounts/memberships and audit. Changes require distinct protected-action confirmation and effective/version history. Financial Review is read-only unless a separate explicit Company action grant exists. Accountant uses effective configuration in transaction screens without independent protected-rate editing; Owner has authorized read visibility only. Module OFF still exposes permitted history and minimum open-position resolution paths.

## Normal manual workflow and failure states

Use familiar compact forms, fields, tables, search, filters, transaction pages, detail/history views and reports. Under 01's five levels, show backend-calculated important results, clearly labelled editable suggestions, distinct Due/reminder states, and explicit review/confirmation for consequential actions; manual exceptions expose reason/history. Never present a suggestion, due state or period end as Paid or settled, or replace the workflow with a single opaque auto-settlement control. Show inputs and decision-relevant values, with expandable breakdown when useful rather than every mathematical intermediate by default: manual-style business workflow without manual calculation burden. Show loading, empty, validation, forbidden, missing, session failure, timeout and server error states without a blank screen or false success. Preserve entered form data when practical. Dense desktop tables become readable mobile views without hiding critical money or status. Support keyboard/focus/accessibility and suitable touch targets. Image failure stays within its region and never blocks Vehicle text or finance.

## Security boundary

Never fetch another Company's private data into a UI merely to hide it. Investor views contain only that Investor's authorized private data; Media/public views receive no internal finance. Company/Branch/module/backend authorization remains authoritative even when a UI control is absent.

## Approved Business Decision Additions — post-Exit repayment editing

- Provide an edit action for a saved post-Exit repayment entry using the existing UI patterns. The normal entry/list view shows the latest value and need not show earlier values.
- Keep the original and correction history in the backend audit trail; a correction note may be entered. Editing the entry must not change the actual Cash/Bank Receipt or movement.
- Enforce Q76's existing Company/Branch authorization. This is a presentation and correction-flow rule, not a new permission.

### ADDITION — excess post-Exit repayment choices

- In the saved repayment edit flow, let the authorized Accountant choose whether an excess above the open amount stays open as due back to the Investor or is returned through a separately recorded actual refund.
- Keep the displayed Cash/Bank Receipt at the full amount actually received. Show the selected excess disposition and current balance; normal views may show the latest value only while preserving prior corrections in backend audit history.
- Never mark a refund paid before its actual Cash/Bank outflow. Do not show the excess as Company Income/Profit.

### ADDITION — partial excess refunds

- If an excess amount remains due back to the Investor, let the authorized Accountant enter partial refunds more than once.
- Show each actual refund separately and the remaining amount due back. Update the balance only after the corresponding Cash/Bank outflow succeeds.

### ADDITION — Purchase/Sale installment balance and warning

- Show the full Purchase cost or agreed Sale price separately from paid/received-to-date and the current remaining payable, receivable or refund amount.
- Accept a valid installment below the current balance and show a small inline warning/status with the amount still outstanding; do not treat a valid partial payment as an error.
- Block an amount above the current outstanding balance with a clear inline validation message. Apply the same pattern to partial refunds and show their remaining refundable amount; update only after the actual cash movement succeeds.
- Reuse this UI pattern in another module only when its full source amount, typed obligation, and permissions are defined.

### ADDITION — shared account prefill for Phase 5 installment forms

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Prefill both Seller installment and direct Vehicle Expense installment forms with the current Accountant's last successfully saved Cash/Bank account in this Company.
- Keep the account selector editable for each payment. Do not update the remembered selection when a form is abandoned or its save fails.

**Scope**
- Existing Phase 5 installment forms only; no route or form redesign.

**Preserve unchanged**
- Display a permitted named account and revalidate it server-side. The preference does not grant access or alter the account stored on prior payments.

**Supersedes**
- None; this applies the existing Seller-payment preference to the Vehicle Expense installment form.

**Implementation impact**
- Use the shared preference as a convenience default and preserve the existing selector/error/loading behavior.

### ADDITION — required external reference on Vehicle Expense payment

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- The direct Vehicle Expense installment form requires a bank transaction ID or Cash voucher reference for every actual payment.

**Scope**
- Existing Phase 5 Vehicle Expense installment form.

**Preserve unchanged**
- Keep the existing form composition and compact responsive layout. Cash/Bank account remains prefilled from the shared per-Accountant preference and editable. Do not treat the external reference as the payment's identity.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the Vehicle Expense payment form needs an operator-entered external reference.

**Implementation impact**
- Add a compact required reference field and show validation beside it; preserve entered data on request failure.

### ADDITION — show duplicate Vehicle Expense reference validation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- If a Vehicle Expense installment reference duplicates an existing reference for the same Company and Cash/Bank account, show an inline validation error and do not submit/post the payment.
- Treat leading/trailing spaces and letter case as equivalent.

**Scope**
- Existing direct Vehicle Expense installment form only.

**Preserve unchanged**
- Keep the required external reference field, selected Cash/Bank account, entered amount, and other form values visible after validation failure. This does not change reference validation on other forms.

**Supersedes**
- SUPERSEDES EARLIER Q107 WORDING: duplicate references were allowed/not governed for this payment form.

**Implementation impact**
- Display the server's duplicate-reference validation beside the reference field; do not show payment success.

### ADDITION — Vehicle Expense refund excess destination and partial cost warnings (Q124–Q131)

- In the refund form, show the full actual amount, the amount that may be applied to the selected Vehicle Expense, and the excess separately. Require the Accountant to choose an eligible destination for the excess; do not default or auto-select Company Income. If there is no eligible destination, explain that the destination record must be created before posting.
- If the Accountant selects Company Income, require a separate Income category and note before posting, show the Company Profit effect, and link the actual Receipt to that new Income record. Never edit or silently reuse an older Income event.
- Show a compact, non-blocking warning when a Purchase or Vehicle Expense is only partly paid; keep full cost, paid amount, and remaining payable distinct. Reject an installment above the currently displayed outstanding balance and refresh after a concurrent balance conflict.
- Show Company-only and Investor-funded source choices only to actors authorized for the corresponding allocation. Do not expose pooled company Fund balances to a Branch Accountant who lacks that scope.
