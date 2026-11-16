# VIRMS — Product and System Reference for Independent Review

Snapshot: 2026-11-09. Worktree: `D:/VIRMS/tmp/phase5-investment-foundation-20261107`; branch `codex/phase5-investment-foundation`; base `50fb67c1c2256f6a164344344c8c2a12e04407f8`. This snapshot includes uncommitted work. It does not describe a verified deployed environment. This document records repository facts and documented product direction; it does not recommend a deployment provider or architecture.

## Evidence and interpretation

- **Code:** current repository implementation. A React screen or navigation label does not by itself prove backend integration.
- **V2 target:** `docs-final-v2/` describes approved/target direction; entries explicitly marked unresolved remain open. Later approved additions can supersede a narrow earlier statement; consult the owning document in full.
- **Local report:** `docs/phase5-execution-progress.md` records prior local work and tests; its results were not rerun for this document.
- **Unknown:** production topology, usage volumes, customer counts, provider charges, backups and deployment are not verified. No production traffic estimates are present here.

## Product

VIRMS means Vehicle Investment, Modification & Resale Management System. It is intended to support companies managing vehicle investment, stock vehicles, garage work, sales, investor relationships and company accounting, alongside role-specific and public-safe access. A Company can have multiple Branches. Company is the data ownership boundary; Branch attributes operations and limits access. A Branch selector is not an authorization grant. Labour is an operational record, not a login role in the documented baseline.

## Portals and audiences

The repository describes five role-based authenticated surfaces plus a public-safe surface. These are logical audiences, not evidence of six separately deployed applications. Actual production user counts and traffic per surface are unknown.

| Surface | Intended audience and principal areas | Status evidence |
|---|---|---|
| Accountant / Operations workspace | Daily Company operations: accounting, investors/fund, vehicles, garage jobs, sales, collections, reports and corrections within scope | React workspace exists; Accounting API integration exists; many other screens use demo data |
| Owner | Company and Branch overview, reports, investor and vehicle information, accounting results, audit and authorized read-only analysis | V2 target; completeness and backend integration per screen not established by this review |
| Investor portal | Own fund position, stock vehicles, interim payments, profit/reconciliation, exit and settlement; public vehicle information separately | V2 target; not demonstrated as a fully integrated live portal |
| Media | Eligible vehicles, images, public details and publication | V2 target; full production integration not verified |
| Platform Back Office | Company, Branch, accounts, module states, protected configuration, platform audit and authorized review | Django Admin / platform foundation documented; individual future capabilities require verification |
| Public-safe vehicle views | Published eligible vehicle details and approved images without private financial data | V2 target; production implementation/traffic unverified |

V2 calls the Investor portal an early priority. It does not provide a measurement ranking expected visitor numbers. The user describes a main Company accountant as a primary daily user; branch and other authorized roles also exist in the product design. No traffic ranking should be inferred from navigation alone.

## Pages and workflows

The React navigation registry includes Dashboard/Overview; Vehicles (Stock / Investor and Customer Vehicles); Garage Jobs; Inventory (Items & Purchases, Stock Issues, Stock Reports); Investment Management (Investor Fund, Vehicle Sales, Collections, Sale Corrections & Refunds, Investor Profit & Interim, Reconciliation & Settlement); Company Accounting; Reports; settings and other navigation areas. See `demo/react/src/data/navigationRegistry.ts` for exact current entries and status badges. A registry status such as `implemented` denotes UI availability and does not establish persistence.

The V2 navigation document also describes Owner overview and reports, Investor private fund/vehicle/payout/exit views, Media publication views, Platform Company and user administration, and public-safe vehicle views. Vehicle detail may bring together current Branch and movement, work, expenses, sale, collections and history subject to role permissions. External customer Garage work uses a vehicle and job context without requiring an Investor relationship. Sale, actual collection, refund, and remaining receivable are distinct records or positions. These are product requirements, not proof that each current screen has a live backend.

## Business and financial boundaries

- Vehicle Management owns Company-wide vehicle identity; movement changes Branch context while retaining history. Investment owns investor and fund relationships. Garage owns jobs and work; Accounting owns actual Company cash/bank events.
- Company Income and Expense are distinct from actual Receipts and Payments. Capital inflow/outflow and Running Capital are distinct from Company income/profit. Investor profit and Company/Owner profit are separate concepts.
- Financial sources, corrections, approvals, historical effective dates, identity and permissions must be read from canonical V2 additions and architecture documents; older passages can be superseded on a specific topic. Do not infer an approved calculation from a mock screen.
- Source transactions are intended to be authoritative; dashboards and reports are derived views. Company isolation and authorized Branch scope apply to APIs, reporting, search and files.

## Application and technology

V2 specifies a provider-neutral modular monolith: React 19, Vite, TypeScript, Tailwind, React Router and TanStack Query on the frontend; Python, Django and Django REST Framework on the backend; PostgreSQL for relational persistence. Cloudflare R2 via an S3-compatible adapter is the documented target for files; the README says local media is confined to `.local-media/` and no Vehicle image workflow is implemented at that checkpoint. Production application hosting is unselected. Render free tier is named as a staging target in V2; repository README says staging configuration and production hosting resources have not been created. These are document claims, not live deployment evidence.

The React client uses `/api/v1/` and development Vite proxies it to a loopback Django server. Production same-origin routing has not been established by this review. Django sessions use cookies and CSRF protection per README. Server-side Company, Branch, module, action and object checks are the authorization boundary.

## Conceptual data relationships

Platform → Companies → Branches and scoped Users/roles. A Company has Investor identities and Fund history; Vehicle Management owns Vehicle UUIDs and movement history. An Investor can fund multiple Vehicles; the target relationship allows a Vehicle's Investor responsibility to end while history remains. Vehicles may have Garage Jobs, work/costs and Sales. Accounting records actual receipts/payments and cash/bank movements, linked to their authoritative source where supported. Corrections and audit records retain history. This is a conceptual map: consult `docs-final-v2/04-data-model-relationships.md` and actual models/migrations for exact fields, constraints and implementation status.

## Current local implementation boundary

README records accepted local Phase 1–3 foundations and a local Phase 4 Accounting checkpoint at base commit `50fb67c1`; Phase 4 verification details are in `docs/phase4-execution-progress.md`. The Phase 5 local report describes partial, uncommitted backend slices for Investor profiles, interim configuration, Branch-attributed fund credits and principal returns, Vehicle identity/movement, and typed Accounting capital-event links. It marks Phase 5 partial/blocked; purchase/funding allocation, Vehicle deactivation and React Investment/Vehicle integration are not complete at that report's checkpoint. The report says local tests used disposable PostgreSQL and did not access `virms-local-8002-pgdata`; it does not prove current production state.

React Accounting consumes backend APIs; Phase 5 Vehicle/Investor/Fund React screens remain prototype-driven according to the execution report. Existing demo/mock records must not be assumed to represent persisted production records. Roadmap and Phase 5 documents may contain historical or superseded checkpoints; use their latest specific additions and the current source.

## Data volume, deployment and recovery facts available

No verified tenant count, concurrent user count, per-portal traffic, data volume, request rate, availability objective, RPO/RTO, provider invoice, actual backup schedule, restore test, or production runtime grants were established during this documentation task. A local Docker volume name identifies storage but does not establish the existence of a backup. No cloud, database, Docker, or live service was inspected for this document.

## Source index

- `README.md`; `planning/V2-DEVELOPMENT-ROADMAP.md`; `docs/phase4-execution-progress.md`; `docs/phase5-execution-progress.md`.
- `docs-final-v2/01-business-rules.md` through `10-garage-jobs-workflow.md`, especially 02 roles, 03 modules, 04 relationships, 05 investor/vehicle finance, 06 technical architecture, 07 navigation, 08 media and 09 accounting.
- `architecture/01-DATA-FLOW.md` through `04-CHANGE-IMPACT-COMPATIBILITY.md`; `architecture/phase-05-investment-vehicle-running-capital/`.
- `demo/react/src/data/navigationRegistry.ts`, `demo/react/src/api/`, `apps/accounts/`, `apps/tenants/`, `apps/accounting/`, `apps/investment/`, `apps/vehicles/`, `core/settings.py` and migrations.
