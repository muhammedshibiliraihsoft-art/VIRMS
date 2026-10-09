# 07 — UI / Navigation Structure

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — UI AND NAVIGATION SOURCE OF TRUTH

This document defines interface structure and state presentation. Roles follow 02; financial states follow 05; image behavior follows 08. UI visibility never grants permission.

## Application shell

- Preserve the approved SGTP reference shell layout and interaction pattern. Provide a reserved logo slot in the shell, plus reusable slots for navigation icons, header actions, and page content. Leave the logo slot unbranded; use VIRMS-specific labels and content when supplied. Do not copy SGTP logo or other SGTP brand assets.
- Desktop/laptop: a fixed left sidebar with compact and expanded states, usable icons when compact, clear active destination, account/profile area, sticky top header and independently scrollable main content.
- Tablet/phone: top header and fixed bottom navigation for the few highest-priority destinations. A More bottom sheet contains secondary destinations. Support safe areas, touch controls and no horizontal shell overflow.
- Top header shows current page and relevant Tenant context, authorized combined Owner context, search/notifications where useful, appearance and account controls. Do not show confidential finance globally without need.
- Use semantic tokens for Light, Dark and System appearance, including neutral, pending, success, warning and danger states. Long text, localization and RTL/LTR shell direction must not break the layout.

## UI reference baseline

The approved visual/layout interaction snapshot is repository `muhammedshibiliraihsoft-art/sgtp`, branch `frontend/parallel-foundation`, commit `9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`. It supplies direction for the clean application shell, compact/expanded desktop sidebar, top header, responsive composition, phone bottom navigation and More sheet, information density, cards/tables, themes, restrained motion, and loading/error/empty presentation. The approved VIRMS-specific shell variation above remains authoritative.

Reuse only visual structure, layout, interaction and responsive presentation. Do not copy SGTP branding/assets, tailoring labels, Shop/domain behavior, workflows, entities, APIs, permissions, Tenant assumptions or financial logic. VIRMS documents 01–08 and supporting documents always control product behavior. This pinned commit is a stable reference snapshot; later SGTP changes do not alter VIRMS requirements without formal approval.

## Role navigation

| Role | Primary navigation | Contextual/secondary views |
|---|---|---|
| Owner | Overview, Investors, Vehicles, Sales/Receivables, Reports | Fund, Expenses, Profit/Loss, Labour, Settlements, Audit, Owner AI; individual and combined authorized Tenant views; read-only presentation |
| Accountant | Overview, Investors/Fund, Vehicles, Sales/Receivables, Profit/Settlement | Expenses, Buyers, Labour, Media/Publication, Reports, Corrections/Audit within permission |
| Investor | Overview, Fund Position, My Vehicles, Exit/Settlement | Own profit and financial history; other Vehicles only through approved public view |
| Media | Eligible Vehicles, Images, Public Details, Publication | Public availability/status only; no finance or core lifecycle controls |
| Back Office | Tenant, Users/Access, Configuration, Administrative Audit | Controlled system administration, separated from daily operations |
| Labour | No navigation | No login |

Each module need not be a top-level destination. Use record-detail sections or tabs for related views and put lower-priority areas in More on mobile. Tenant selector appears only for Users with multiple authorized contexts; changing it does not grant access.

## Record details and financial state

- Vehicle detail groups Overview, current Tenant/history, Investor/purchase, core status/work, Expenses, Media/Publication, Sale/Buyer Payments, Finance, and Audit as authorized. Keep Sold separate from Buyer collection status.
- Investor detail groups global Fund Position/History, Vehicles across permitted Tenants, Profit, Exit/Settlement and Audit. Tenant labels on movements indicate context, not Investor ownership.
- Show Agreed Sale Price, Sale Applied Buyer Amount, Remaining Receivable, and Pending/Partially/Fully Received distinctly. After a Sale correction, also show gross confirmed Buyer Payments, actual refunds, any Buyer Refund Payable and its unpaid principal-backed portion so cash still owed back is not presented as applied Sale collection. Buyer Payment entry shows the current Remaining Receivable and rejects nonpositive or excess amounts with a clear validation error; frontend validation assists, while backend enforcement remains authoritative.
- Profit/Loss presentation distinguishes Calculated, Eligible and Paid. Before full collection or while a Buyer Refund Payable remains unpaid, new positive Profit payouts remain ineligible; show any earlier confirmed payout as historical Paid with its separate correction obligation. After full collection, principal recovery and any Buyer refund resolution, Investor payout becomes eligible; Owner payout is blocked until Investor payout is complete. Paid changes only after Accountant confirmation.
- Profit payout review shows recipient, Vehicle/Sale, calculated amount, eligible amount, already confirmed payments, Outstanding Eligible Entitlement, amount being recorded and remaining balance. It rejects nonpositive or excess payment and keeps Owner payout unavailable until the Investor payout is complete. Cancel leaves finance unchanged; backend validation remains authoritative.
- A loss view shows the deal loss, snapshotted Investor/Owners allocation percentages and amounts, actual Owner contribution status and remaining principal position, with an optional explanatory Loss Note. There is no loss-bearer selector. Do not imply calculated coverage is received or that unresolved principal is recovered.
- Exit UI shows Terms & Conditions acceptance, notice period, Available and Locked Principal, principal reconciliation, collections, unpaid Investor Profit, pending obligations, settlement payable and final Settlement state. Exceptional early closure is an audited Accountant action; Owner view is read-only. Do not show Settlement complete while a payable or obligation remains unresolved or the principal reconciliation does not match.
- Correction history shows original posting, linked correction/adjustment, corrected current position and status of any Additional Payable, Recovery / Adjustment Obligation, Owner contribution, Owner Contribution Return Payable or Buyer Refund Payable, including any return/refund amount awaiting Fund liquidity. Show a linked reclassification of an existing Buyer receipt between collected Profit and Principal Recovery without displaying another receipt. For Profit/Loss crossover corrections, show prior payout recovery and corrected Loss/Profit positions separately. Preserve an earlier Settlement closure in history while presenting a later correction-related unresolved position separately.

## Responsive, loading and input rules

- Dense desktop tables adapt to readable mobile lists/cards without hiding critical money or status. Large datasets use server-backed pagination and filters.
- Screens provide initial/loading, empty, validation, forbidden, not-found, session-failure, timeout and server-error states. Keep the shell stable; never show a blank screen, false success or endless spinner.
- Preserve entered data when a request fails where practical. Use explicit confirmation for consequential financial actions.
- Support keyboard navigation, visible focus, semantic buttons/links, accessible labels, suitable touch targets, correct phone/numeric input modes and mobile keyboard-safe forms.
- Image failures stay within the image region and do not block the Vehicle page.

## Security boundary

Never load another Investor's private finance into an Investor view or internal finance into Media/public views merely to hide it visually. Owner views read only within assigned scope. Backend authorization, Tenant isolation and public-safe API projection remain authoritative.
