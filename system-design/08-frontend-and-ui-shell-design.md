# 08 — Frontend and UI shell design

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/02, 03, 05, 07, 08 and production engineering standards. This is a React 19/Vite/TypeScript/Tailwind CSS v4/React Router/TanStack Query design contract, not production UI code.

## Shell and navigation contract

Follow docs-final/07's approved SGTP pinned visual reference for layout/interaction only, with an unbranded reserved logo slot and VIRMS content. Desktop uses a fixed compact/expanded left sidebar, active destination, account area, sticky top header and independently scrollable main. Tablet/phone uses top header, fixed bottom navigation for high-priority destinations and More sheet for secondary destinations; respect safe areas and mobile keyboard. Navigation is role-aware but does not authorize. Tenant selection is shown only for multiple authorized contexts and changing it re-queries scoped data; Owner's combined context shows only explicitly assigned Tenants. Investor global Fund context stays self-scoped.

Top header carries current page, context, search/notification controls where useful, appearance and account controls. Do not put private finance in a global header. Use semantic Light/Dark/System tokens; pending/success/warning/danger states; visible focus, keyboard access, accessible labels, safe touch targets and LTR/RTL resilient layout. Role routes are lazy-loaded where useful, with TanStack Query for server state and invalidation after confirmed mutations; local form state remains separate from server truth.

An Accountant change to an Investor-specific percentage appears in Owner-authorized change history/notification with old/new values, actor, time and scope. The notice is derived from the audited agreement version; delivery transport is an implementation choice and cannot become the source of the percentage.

| Role | High-priority navigation | Secondary/context views |
|---|---|---|
| Owner | Overview, Investors, Vehicles, Sales/Receivables, Reports | Fund, Expenses, Profit/Loss, Labour, Settlements, Audit, Owner AI; all read-only within assigned Tenants |
| Accountant | Overview, Investors/Fund, Vehicles, Sales/Receivables, Profit/Settlement | Expenses, Buyers, Labour, Media/Publication, Reports, Corrections/Audit |
| Investor | Overview, Fund Position, My Vehicles, Exit/Settlement | Own Profit/history; others only approved public catalog |
| Media | Eligible Vehicles, Images, Public Details, Publication | Public availability; no finance or core lifecycle controls |
| Back Office | Tenant, Users/Access, Configuration, Financial Review, Administrative Audit | Discoverable read-only finance details, controlled merge review |

No Labour navigation or login. A reused record-detail component receives a backend-authorized read model and permission hints, but backend endpoints independently enforce every field and command. Back Office Financial Review must reveal the full authorized finance scope in read-only mode; daily finance confirm/correction controls are absent/disabled and direct API writes remain denied.

## Shared screen states and consequential actions

Every route shows stable-shell initial/loading, empty, forbidden, not-found, session-expired, validation, timeout/offline and server-error states. Keep entered form data on recoverable failure. Image error stays within the image region. Repeated submit while pending is disabled for UX, while idempotency protects the backend. A consequential money action has a review panel showing actor/context, source record, amount, current cap, derived before/after positions, specific unresolved blockers and required reason; final success appears only after server confirmation. Do not let UI precomputed totals be authoritative.

Financial displays keep Cash Held, Sale Applied Amount, Remaining Receivable, refund payable/reserve, principal recovered/locked, calculated/eligible/paid Profit, recovery obligations and Owner contribution/return separately labeled. Correction history keeps original, linked adjustment and current target together. Settlement shows prior paid Profit, remaining principal, remaining eligible Profit and principal-first final payment order. Dense desktop tables become legible mobile cards/lists without hiding money or status; all large lists use server pagination.

## Base information architecture

For each page, the stated mode/action is limited by docs-final/02 and 07. Each route includes scoped loading/empty/error presentation, an audit/history affordance when historical records exist, and mobile card/detail adaptation. "Review" means read-only; "confirm" means an explicit backend command with a review step.

| Page | Purpose; primary actor/mode | Primary data and permitted actions | Sensitive/mobile/history notes |
|---|---|---|---|
| Dashboard | Role-specific overview; all authenticated roles read | Verified scoped summaries, alerts and navigation; no editable balance | Bounded cards and links; no broad finance in Media/Investor view |
| Investors | Global profile/portfolio; Accountant write, Owner/Back Office read, Investor self-read | Create Investor, view agreement/history and scoped Vehicles; Accountant percentage change with reason/audit | Global identity with Tenant provenance; mobile profile tabs |
| Investor Fund | Source movements and available/locked/recovered positions; Accountant commands, other authorized reads | Add capital and view linked movement detail; no manual balance edit | Mobile transaction list; source-event drill-down |
| Vehicles | Purchase, lifecycle and detail; Accountant write, role-limited read | One Investor/current Tenant, cost, status, history; operational lifecycle command | Media sees public-only detail; audit and Tenant transfer history |
| Expenses | Approved Vehicle cost; Accountant write, authorized read | Category, individual expense, linked Fund use and correction history | No general Garage expense or worker allocation action |
| Sales | Confirm Sale/current agreed price; Accountant write, authorized read | Buyer, Sale snapshot, collection and corrected current result | Sold remains distinct from collection; correction reason/review |
| Buyers | Tenant customer identity; Accountant write, authorized read | Contact, linked Sales; phone required but not unique | No cross-Tenant lookup or identity merge by phone |
| Receivables | Actual Buyer collection; Accountant confirm, authorized read | Applied amount, gross receipts, remaining receivable, explicit payment cap | Reject overpayment; mobile amount keypad and receipt history |
| Refunds | Correction-created obligation; Accountant actual confirmation, authorized read | Original payments, actual refunds, current payable, principal reserve | Open payable remains visible even at full applied collection; history and liquidity |
| Profit/Loss | Allocations, eligibility and payout; Accountant confirm, authorized read | Snapshot, corrected amount, actual paid/recovered, Owner coverage and gates | No payout before deal-level eligibility; Owner stage locked until Investor-side resolution |
| Settlement | Global Investor exit/final payment; Investor own request, Accountant manage, authorized read | Terms/notice, locked/available, blockers, separate principal/Profit and actual payments | Principal-first final payment; no false Closed state |
| Labour | Basic Tenant worker and manual payments; Accountant write, Owner read | Active/inactive, amount/date/note history | No payroll, attendance or Vehicle assignment |
| Media | Shared images/public fields; Accountant/Media limited write | Four-active-image count, primary, variants, publication/availability | No internal finance; local image failure/retry and audit |
| Reports | Verified summaries; Owner/Accountant/Investor within scope | Server filters, pagination, export only under explicit permission | Rebuildable values; mobile summary then detail |
| Audit | Event/correction trail; authorized read | Actor/time/reason/source and linked current position | Protect sensitive fields; mobile timeline |
| Administration | Tenant, users, memberships, defaults; Back Office write | Provision, deactivate/reactivate, restricted configuration review | Strong confirmation and historical access records |
| Back Office Financial Review | Administrative financial visibility; Back Office read-only | Investors/Funds, Vehicle finance, purchase/Expense, Buyer payment/refund, recovery, Profit/Loss, Owner coverage, Settlement, corrections/audit | Discoverable route; no ordinary finance mutation controls; backend denies direct writes |

Search results, breadcrumbs and context headers retain Tenant/global scope and never imply access to a hidden record. Audit links appear only for authorized records. Read-only states use clear labels without suggesting that a displayed calculated amount is already paid.

## Prototype decision

No non-production prototype is created in this design phase. The shell contract, responsive behavior, role map and page map are sufficiently explicit for later visual validation against the approved pinned reference.
