> ⚠️ LEGACY — NON-AUTHORITATIVE — DO NOT IMPLEMENT

> This document is retained only for historical reference.
> `/docs-final/` is the sole VIRMS implementation source of truth.
> Any older `LOCKED`, `FINAL`, or `AUTHORITATIVE` wording below is historical
> and is superseded by the current `/docs-final/` documentation.

# PROMPT — CREATE `07 — UI / NAVIGATION STRUCTURE`

Create the architecture document:

`07 — UI / Navigation Structure`

for the Vehicle Investment, Modification & Resale Management System.

The output is an architecture/source-of-truth document, NOT frontend implementation code.

Keep it concise, structured, implementation-ready, and optimized for fast Codex reading with minimal unnecessary token usage.

Use tables/matrices where they reduce repetition.

---

## AUTHORITATIVE PROJECT SOURCES

Use the current approved project documents as the business source of truth:

- 01 — Business Rules
- 02 — User Roles & Permissions
- 03 — System Modules
- 04 — Data Model & Relationships
- 05 — Vehicle / Investor / Finance Workflow
- Authentication / Account Security standards
- Production Engineering / Performance / Reliability standards where relevant

Do not invent or modify business rules.

If older wording conflicts with a newer explicitly locked rule, use the latest locked rule.

`06 — Branch & Labour Architecture` is not required as a prerequisite for this document.

---

# EXTERNAL UI SHELL REFERENCE — READ ONLY

Use this existing project only as the visual/system-shell reference:

Repository:
`https://github.com/muhammedshibiliraihsoft-art/sgtp.git`

Branch:
`frontend/parallel-foundation`

Reference baseline inspected:
`9ff32bc30d94744cfa0c432e4bb1c57d4182a20c`

Inspect it read-only.

If necessary, use a temporary shallow clone of that branch only.

Never:
- modify the SGTP repository
- commit to it
- push to it
- import its business rules into this project

Important reference areas include:

- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/index.css`
- relevant shell/navigation components
- role/workspace navigation variants
- responsive behavior
- theme/i18n shell behavior

---

# REFERENCE BOUNDARY — CRITICAL

Reuse/adapt the SGTP frontend only for:

- overall authenticated application shell
- software-style layout
- desktop sidebar behavior
- top-header structure
- mobile/tablet navigation pattern
- More bottom-sheet pattern
- account/profile menu pattern
- navigation active/disabled states
- responsive shell behavior
- semantic design-token approach
- Light/Dark architecture
- locale/RTL/LTR-ready shell concepts
- loading behavior that keeps the shell stable

DO NOT copy SGTP-specific:

- Tailoring business logic
- Shop business rules
- Clients/Designs/Measurements/Materials workflows
- SGTP route names
- SGTP permission rules
- backend contracts
- API behavior
- database concepts
- page-specific body layouts
- branding/content

The new system must look and behave like the same family of professional business software, but its actual navigation and pages must represent the Vehicle Investment system.

---

# 1. APPLICATION SHELL

Define the standard authenticated shell.

## Desktop / Laptop

Preserve the reference interaction model:

- fixed left sidebar
- compact/collapsed state
- expanded/pinned state
- hover/focus peek behavior where appropriate
- icons remain usable when collapsed
- labels visible when expanded
- subtle active navigation state
- account/profile section at sidebar bottom
- sticky top header
- main scrollable content area

The exact dimensions may follow/adapt the reference shell unless a project-specific usability reason requires a change.

Do not redesign this into a website-style header/menu layout.

This must feel like installed business software.

## Tablet / Mobile

Preserve the reference interaction model:

- top header
- fixed bottom navigation
- only highest-priority destinations in the bottom bar
- `More` opens a bottom sheet for secondary destinations/actions
- safe-area support
- no horizontal shell overflow
- touch-friendly controls

Do not simply shrink the desktop sidebar.

---

# 2. TOP HEADER

Define responsibilities for the shared top header.

Support as applicable:

- Current page/module context
- Current Tenant/Garage context where relevant
- Global/combined business context for authorized Owner views
- Search entry point where useful
- Notifications entry point
- Language selector where enabled
- Light/Dark/System appearance control
- User/account access
- Sidebar expansion control on desktop when required

Do not place confidential finance information in the global shell unnecessarily.

---

# 3. ROLE-AWARE NAVIGATION

Navigation must derive from 02 — User Roles & Permissions and 03 — System Modules.

Current authenticated roles:

1. Owner
2. Accountant / Operations Admin
3. Investor
4. Media User
5. Back Office Admin

Labour has no login and therefore no Labour-user navigation.

Public Vehicle API is an external access channel, not an authenticated navigation role.

Create a concise Role → Primary Navigation → Secondary Navigation matrix.

---

# 4. OWNER NAVIGATION

Owner is:

`View + Monitor + Analyse`

Owner remains operationally read-only.

Navigation must provide authorized access to relevant:

- Dashboard / Business Overview
- Investors
- Investor Fund positions
- Vehicles
- Vehicle Expenses / Costs
- Sales & Receivables
- Profit / Distribution
- Labour
- Reports & Analytics
- Audit / History
- Settlements
- Owner AI Assistant
- relevant configuration/history views where read permission exists

Support:

- individual authorized Tenant view
- combined authorized business view
- filters by Tenant, Investor, Vehicle, date/status/payment/settlement where applicable

Never expose normal operational create/edit actions merely because Owner can view the data.

---

# 5. ACCOUNTANT NAVIGATION

Accountant is the main operational user.

Provide efficient access to:

- Dashboard
- Investors
- Investor Fund
- Vehicles
- Vehicle Expenses
- Sales & Receivables
- Profit / Distribution operations
- Buyers
- Labour
- Investor Exit / Settlement
- Reports
- applicable Audit / Correction history
- Media/Publication operations where authorized

The exact grouping should minimize navigation clutter.

A module does not need to become a separate top-level navigation item if it is better represented as a sub-view within its authoritative parent module.

---

# 6. INVESTOR NAVIGATION

Investor navigation must remain simple and self-scoped.

Include appropriate access to:

- Overview
- Fund Position
- My Vehicles
- Recovered Principal
- Profit Earned / Paid / Pending
- Sale/Settlement information
- Financial history
- Exit Request / Exit Status

Investor financial data is read-only.

Other Vehicles may expose only approved public-level information.

Never expose another Investor's private finance.

---

# 7. MEDIA USER NAVIGATION

Media User navigation must remain limited to approved public-facing Vehicle operations.

Possible areas:

- Vehicles eligible for media/publication work
- Vehicle photos/media
- Public Vehicle details
- Publication status

Do not expose:

- Investor Fund
- Purchase Cost
- Internal Vehicle Expenses
- Profit/Loss
- Investor Share
- Owner Shares
- Settlements
- Financial Corrections
- protected configuration

---

# 8. BACK OFFICE NAVIGATION

Back Office is a separate administrative workspace/surface.

It should use the same shell family but have its own navigation tree.

Include:

- Tenant / Garage Administration
- Owner / Accountant account provisioning
- User & Access Administration
- System Configuration
- Tenant/default configuration
- protected business defaults
- relevant administrative audit/history

Back Office is not the daily Accountant interface.

Do not duplicate daily operational finance modules into Back Office without an actual administrative requirement.

---

# 9. TENANT / GARAGE CONTEXT UX

Garage = Tenant.

Tenant context must be explicit where operationally relevant.

Rules:

- UI context never replaces backend Tenant authorization.
- Changing a Tenant selector never grants access.
- Owner may view individual authorized Tenants or combined authorized business data.
- Operational users may access only explicitly authorized Tenant scope.
- Investor identity and Investor Fund remain global and must not be presented as owned by a Tenant.
- Vehicle views may show current Tenant and relevant historical Tenant context where required.

Define where Tenant context appears in the shell and when a selector is available.

Avoid unnecessary selectors for users who have only one valid operational context.

---

# 10. NAVIGATION HIERARCHY

Use 03 — System Modules to produce a compact final navigation hierarchy.

Do not mechanically make every module a sidebar item.

Use:

- Primary destinations
- contextual sub-navigation/tabs
- secondary items inside `More`
- record-detail subviews

to keep navigation clean.

The application should remain usable even as future modules are added.

---

# 11. FINANCIAL UI STATES FROM 05

Define UI-state conventions at architecture level.

The system must visibly distinguish:

### Buyer Collection

- Agreed Sale Price
- Amount Received
- Amount Pending
- Pending / Partially Received
- Fully Received

### Vehicle Finance

- Purchase Cost
- Vehicle Expenses
- Total Vehicle Cost
- Recovered Principal
- Still Unrecovered Principal
- Profit / Loss

### Investor Fund

Keep visually distinct:

- Total Principal Fund
- Available Fund
- Currently Used Fund
- Recovered Principal

Critical:

`Recovered Principal` is cumulative historical recovery.

Reusing recovered principal on another Vehicle must reduce Available Fund/increase Currently Used Fund as appropriate, but must never visually reduce the historical Recovered Principal value.

---

# 12. PROFIT / DISTRIBUTION UI STATES

Automatically calculated values may include:

- Total Profit
- Investor entitlement
- Owners Pool
- Individual Owner entitlements
- collected profit position
- pending profit position

Clearly distinguish:

1. Calculated / Pending
2. Collected / Eligible
3. Confirmed Paid

Suggested semantic presentation:

- Calculated/Pending → muted/neutral state
- Fully collected/Eligible → positive/success state
- Paid → separate explicit completion state

Do not equate `Eligible` with `Paid`.

Exact colors must use semantic design tokens rather than scattered hard-coded hex values.

---

# 13. PROFIT PAYMENT UX

Profit Paid must never happen automatically.

When an authorized Accountant records payout:

Calculated entitlement
→ Eligible amount
→ Review / Confirmation
→ Confirm Payment
→ Paid

The review/confirmation interaction should display enough information to prevent accidental payment, including as applicable:

- Recipient
- Vehicle / Sale
- Calculated entitlement
- Eligible amount
- Amount being recorded as paid
- outstanding amount after payment

Cancel must leave financial state unchanged.

Do not design the backend transaction in this document.

---

# 14. PROFIT PAYOUT MODE UX

05 permits controlled configuration between:

### KEEP PENDING
Profit payout stays pending until full Buyer collection.

### ALLOW EARLY PAYOUT
After Principal recovery, actually collected profit may become eligible for confirmed payout.

UI must show the current applicable mode/status without hard-coding one universal behavior.

Only authorized configuration/operational surfaces may expose relevant controls.

Unreceived money must never appear payout-eligible.

---

# 15. LOSS UX

If a Vehicle deal is negative:

Show a clear `Loss` state.

Support an optional:

`Loss Note / Explanation`

The note is descriptive only.

It must not alter financial calculations.

Do not create a separate Investor-vs-Owner loss allocation UI.

---

# 16. INVESTOR EXIT UX

Include architecture for:

- Terms & Conditions before normal Exit Request
- explicit acceptance
- three-month notice information
- Exit Requested state
- Settlement Pending state
- Closed state
- locked capital visibility
- unsold Vehicle visibility
- Pending Receivable visibility
- Settlement position

Exceptional Early Closure:

- managed by Accountant
- audited
- Owner view-only
- not Investor self-service

---

# 17. VEHICLE DETAIL INFORMATION ARCHITECTURE

Define logical information groups, not pixel-perfect layouts.

A Vehicle detail experience should make applicable information discoverable without creating one oversized page.

Potential groups:

- Overview
- Purchase / Investor
- Work / Status
- Expenses
- Media / Publication
- Sale
- Buyer / Payments
- Finance
- History / Audit

Use tabs/sections/contextual navigation where appropriate.

Do not invent unsupported business fields.

---

# 18. INVESTOR DETAIL INFORMATION ARCHITECTURE

Define logical subviews such as:

- Overview
- Fund Position
- Fund History
- Vehicles
- Profit
- Exit / Settlement
- History / Audit

Investor Fund is global.

Tenant context on individual movements is traceability information, not Investor ownership.

---

# 19. RESPONSIVE SHELL MATRIX

Provide a concise matrix for:

- Desktop / large laptop
- Small laptop
- Tablet landscape
- Tablet portrait
- Phone
- narrow phone / approximately 360px

Define:

- Sidebar vs Bottom Navigation
- Top Header behavior
- More navigation
- table/list adaptation
- page actions
- modal/sheet behavior
- safe-area behavior

Do not use desktop-only assumptions.

---

# 20. TABLE / LIST BEHAVIOR

Business records may become large.

Define reusable rules:

- server-backed pagination/filter/search where data scale requires it
- avoid rendering huge unbounded tables
- preserve useful density on desktop
- mobile should use compact responsive representation without hiding critical financial truth
- long IDs/names/phone numbers/status labels must not break layout
- destructive or financial actions need deliberate confirmation

Do not duplicate backend authorization in presentation logic.

---

# 21. LOADING / EMPTY / ERROR STATES

Every routed screen must define safe states for:

- Initial loading
- Page/route lazy loading
- Empty data
- Validation error
- API error
- Unauthorized / 403
- Not found / 404
- Session/authentication failure

Requirements:

- shell remains stable during page loading
- no blank white screen
- no infinite spinner
- no false success
- user-entered form data should not be lost unnecessarily
- image failure must not crash the whole page

---

# 22. ACCESSIBILITY & INPUT RULES

Support:

- keyboard navigation
- visible focus states
- accessible navigation labels
- proper button/link semantics
- adequate touch targets
- mobile inputs at least 16px where needed to avoid browser zoom
- correct numeric/phone input modes
- IDs/registration/phone values treated as strings where required
- long translations
- RTL/LTR-capable shell
- dynamic text height without clipping

---

# 23. THEME / DESIGN SYSTEM

Follow the SGTP shell's semantic-token approach, adapted for this product.

Define semantic concepts for:

- canvas
- sidebar
- header
- surfaces
- borders
- primary/secondary
- text/muted text
- success
- warning
- danger
- info
- pending/neutral

Support:

- Light
- Dark
- System

Do not couple business meaning to one hard-coded brand color.

Keep the interface minimal, clean, professional, and software-oriented.

Avoid unnecessary heavy animation.

---

# 24. SECURITY BOUNDARY

Navigation visibility is UX only.

Frontend must never be treated as the security authority.

Hidden buttons/routes do not grant or revoke permission.

Backend authorization and Tenant isolation remain authoritative.

Sensitive values must not be loaded merely to hide them in the UI.

---

# 25. OUTPUT FORMAT

Produce the final document:

`07 — UI / Navigation Structure`

Use this concise structure:

A. Purpose & Reference Boundary  
B. Application Shell  
C. Role Navigation Matrix  
D. Final Navigation Hierarchy  
E. Tenant Context UX  
F. Desktop Navigation  
G. Tablet / Mobile Navigation  
H. Record Detail Information Architecture  
I. Financial Status Presentation  
J. Profit / Payment / Loss UX  
K. Exit / Settlement UX  
L. Responsive Matrix  
M. Loading / Empty / Error States  
N. Accessibility / Theme / i18n  
O. Security Boundary  
P. Non-Scope  
Q. Locked UI / Navigation Invariants  
R. Document Status

Keep the document compact.

Prefer rules, matrices, and short bullets over explanatory essays.

Do not output React code, CSS code, API schemas, database schemas, or backend implementation.

Do not reproduce rules already fully defined in 01–05 unless they directly affect UI/navigation.

Mark the completed document:

Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH FOR UI / NAVIGATION STRUCTURE


