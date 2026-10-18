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
| Platform Back Office | Companies, Branches, Users/Access, Modules/Configuration, Platform Audit, authorized Financial Review | Platform administration separated from routine Company financial posting; financial review only within authorized scope |
| Labour | None | No login |

Not every module needs a top-level destination. Use record details/tabs and mobile More for lower-priority destinations. Existing Investor Portal, Media, public-safe views, Reports, Audit, Owner and Accountant surfaces remain part of the product.

## Vehicle, Garage and finance details

- Stock Vehicle detail groups Company identity, current Branch/movement history, funding Investor, purchase, core lifecycle, Branch Jobs/work, approved Expenses, Running Capital, Sale/Buyer collection, positive Investor/Company result, media and audit according to permission. Historical Branch entries remain visible to authorized same-Company users; edit actions reflect original Branch and correction authority.
- External customer Garage Vehicle/Job detail shows customer, Branch, work, Labour/materials, charge, actual receipts, remaining balance, status/history and audit. It does not display an invented Investor Fund panel.
- Sale detail distinguishes agreed price, confirmed Buyer Payments, Sale Applied Buyer Amount, Remaining Receivable, correction-created Buyer Refund Payable and actual refunds. Sold is distinct from Pending/Partially/Fully Received. Pending refundable cash is not displayed as settled Sale revenue.
- Positive Vehicle result shows provisional versus confirmed Investor Share, Company Share and actual Running Capital contribution/recovery separately. Company Share links to Company accounting rather than an immediate Owner payout. A negative result leads to manual Loss review, confirmed impacts, reasons and actual actions; do not show an automatic loss-bearer allocation.
- Company result view distinguishes Vehicle Company Share, Garage Revenue, Other Income, Company Expenses, Branch filtering, Company-consolidated result, confirmed distributable Profit, suggested Owner allocation and actual payments. An ended period or suggestion is not Paid.
- Investor view distinguishes principal, committed/available positions, ordinary eligible deal Profit, Monthly Interim Due/Suggested and confirmed Paid history, six-month/annual reconciliation, payable/recoverable and partial future adjustments. A reminder cannot be presented as a payment. Ordinary deal Profit paid while Active is retained history and not duplicated at Exit.
- Exit view shows Terms acceptance, notice, unresolved Vehicles/Buyer balances, Fund and principal reconciliation, separate interim/Profit/recoverable positions, remaining Principal Settlement Payable and remaining eligible Profit. For final closure show principal payment first, then remaining eligible Profit, with all blocking positions resolved and actual payments recorded.
- Platform Back Office shows Company, Branch, module state/configuration, accounts/memberships and audit. Financial Review is read-only unless a separate explicit Company action grant exists. Module OFF still exposes permitted history and minimum open-position resolution paths.

## Normal manual workflow and failure states

Use familiar compact forms, fields, tables, search, filters, transaction pages and reports. Automation reduces arithmetic; show inputs, results and decision-support values, with detailed breakdown available when useful rather than every intermediate field by default. Consequential financial actions need explicit review/confirmation. Show loading, empty, validation, forbidden, missing, session failure, timeout and server error states without a blank screen or false success. Preserve entered form data when practical. Dense desktop tables become readable mobile views without hiding critical money or status. Support keyboard/focus/accessibility and suitable touch targets. Image failure stays within its region and never blocks Vehicle text or finance.

## Security boundary

Never fetch another Company's private data into a UI merely to hide it. Investor views contain only that Investor's authorized private data; Media/public views receive no internal finance. Company/Branch/module/backend authorization remains authoritative even when a UI control is absent.
