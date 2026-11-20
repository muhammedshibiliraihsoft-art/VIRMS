# VIRMS V2 Development Roadmap

**Status:**

CURRENT DEVELOPMENT ROADMAP

**Purpose:**

This roadmap defines the high-level implementation sequence for VIRMS V2 from development foundation through release readiness.

**Canonical business rules:**

`docs-final-v2/`

**Current architecture truth:**

`architecture/`

This roadmap defines implementation ORDER only. It does not replace business rules or architecture.

Current V2 documents define the target. Current implementation shows what exists. This roadmap defines sequence. Future phase architecture defines implementation structure. These are separate authorities.

## Development approach

Establish and accept the platform/authentication backend first. Then complete the shared frontend/authentication integration before starting later business capabilities, which must be delivered vertically with backend and frontend work progressing together:

`Business Rule → Phase Architecture → Data / Domain → Backend / API → Authorization → Tests → Frontend → Integration / Verification`

Before each phase, read the relevant V2 documents and current architecture truth, create or reconcile only that phase's architecture, and resolve its dependencies and business-decision boundaries. Close the phase with integration and verification before selecting the next one. Do not build all backend first or all frontend first.

Current branch snapshot (verified 2026-11-03): codex/audit and origin/codex/audit match at 73797b16aa35db776b5601fe1483c2be8de6c100. Phase 1 and Phase 2 acceptance details below are dated snapshots; Phase 3 status is current in this roadmap. The current local worktree also contains the uncommitted Phase 4 Company Accounting Foundation documented below. Git publication does not establish staging/production deployment or database-role permissions. The separate staging worktree was not modified during this documentation review. Main Operations business workflows, Vehicle/Investment, Garage, Sales, and Inventory domain APIs/models remain future work; Accounting is the Phase 4 exception described below.

## Roadmap

### Phase 1 — Platform Core + Authentication Foundation

**Goal:** Establish and accept the PostgreSQL-backed Company/Branch identity, account, authentication, session, authorization and minimum Django Admin foundation defined by `architecture/phase-01-platform-core-auth/`.

**Starts when:** The exact target worktree and backend baseline are verified, with isolated database and migration preflight.

**Ends when:** P1-19 and the Phase 1 acceptance gate pass on the exact target source, including A-level defects, required B-level blockers, disposable PostgreSQL regression, migration/cutover rehearsal and stable API contracts.

**Status:** ACCEPTED on the local audit integration line, 2026-11-02. `apps.accounts` + `apps.tenants` passed 210/210 tests on disposable PostgreSQL; fresh test-database replay applied migrations through `accounts.0012_scope_end_monotonic`; `manage.py check`, `makemigrations --check --dry-run`, and `git diff --check` passed. This is local source/test evidence, not staging, production or remote-CI evidence.

### Phase 2 — Frontend Foundation + Real Backend Integration

**Goal:** Complete the reusable React frontend foundation and connect it securely to the accepted Phase 1 Django backend while preserving the existing VIRMS UI. Use real authenticated Company/Branch data only where an accepted API contract exists; add no business-domain backend modules.

**Starts when:** Phase 1 acceptance passes on the exact target worktree and auth/session/Company/Branch API contracts are stable.

**Ends when:** Real login/password/logout/session handling, Company/Branch context, safe route/cache/error states and responsive/security validation pass; unsupported mock business data and real dashboards remain deferred.

**Status:** ACCEPTED on the local audit integration line, 2026-11-02. The React suite passed 74/74, production build and configured lint passed, and browser smoke covered login/context/logout/expiry and 320/390/768/1024/1440 widths on the isolated candidate. Business data remains mock-backed because no business API exists. Production origin/proxy/cookie behavior remains unverified; no staging integration or deployment is claimed.

**Decision boundary:** No new Phase 2 business decision is introduced. V2 financial/access decisions remain open for their owning future modules.

### Phase 3 — Main Operations Foundation

**Goal:** Establish the Main Operations Software as the primary Company workspace for Accountant / Operations, connected to the platform foundation and shared capabilities.

**Starts when:** Phase 2 provides the preserved authenticated frontend and real Company/Branch/account context.

**Ends when:** The core operational workspace can host authorized business capabilities and their vertical user flows.

**Status:** COMPLETE — the approved Company module-state foundation is committed and pushed on codex/audit at 73797b16aa35db776b5601fe1483c2be8de6c100; fetched local and origin heads matched on 2026-11-03. Staging/production runtime and deployed PostgreSQL role permissions remain UNVERIFIED. No GitHub CI run/status was present at inspection.

The approved Phase 3 slice establishes versioned Company module state, scoped Platform Back Office administration, an authenticated Company-scoped read API, and the React shared query boundary. The approved 14-code catalog includes Audit and Corrections; audit capture remains cross-cutting. React passed 89/89 tests, lint, and production build; Django passed 232/232 account/tenant tests on disposable PostgreSQL 15, system checks, and migration drift checks. Fresh migration apply, empty-state reverse/reapply, and populated-history reverse protection were verified. No business workflows or financial APIs were added. This is not staging/production runtime or deployed-role evidence. Garage remains Phase 6 after Phases 4 and 5.

### Phase 4 — Accounting Foundation

**Goal:** Establish the Company accounting backbone and source-event links needed by Investment, Garage, Sales, Running Capital, receipts, payments, and expenses.

**Starts when:** Phases 2–3 establish Company/Branch boundaries and the Main Operations foundation.

**Ends when:** Implemented business events can be represented and reconciled in Company accounting without duplicate economic entries.

**Status:** COMPLETE — bounded Company Accounting Foundation locally implemented and verified. The 2026-11-03 statement below is historical; the work was committed as `50fb67c1` on 2026-11-07 and is the Phase 5 worktree base. Remote publication, staging/production deployment, and deployed database-role permissions remain UNVERIFIED.

**Decision boundary:** The remaining Company Share/Garage Revenue/common Expense recognition, distributable-Profit basis, and period close/carryforward decisions do not block this bounded Accounting Foundation. They continue to block only the dependent source integrations or final Profit/close behavior; Investor Profit remains Investment-owned.

**Implementation boundary:** Django Accounting persistence, Company/Branch authorization, append-only corrections and cash movements, Accounting APIs, and the existing React Accounting surface are integrated and locally verified. Future Vehicle/Investment/Garage/Sales modules do not yet create their own source events in Accounting; those vertical integrations remain in their roadmap phases. The implementation and verification evidence is in [the Phase 4 execution report](../docs/phase4-execution-progress.md).

### Phase 5 — Investment, Vehicle, and Running Capital

**Goal:** Deliver the Investor/Fund and stable Company Vehicle flows, approved costs, and separately tracked actual Company Running Capital through the operational workspace.

**Starts when:** Platform, Main Operations, and required Accounting foundations are in place.

**Ends when:** Authorized funding and Vehicle positions can be recorded and connected to the correct Company, Branch, Investor, and accounting sources.

**Status:** COMPLETE — locally implemented and verified 2026-11-15; the four follow-up audit findings were fixed and locally reverified 2026-11-16. Current verification: backend 343 tests, React 137 tests, migration/system checks, lint and build passed on disposable/local tooling. Staging/production and deployment remain UNVERIFIED.

**Decision boundary:** No unresolved business decision blocks the approved Phase 5 core scope. Vehicle deactivation/registration reuse is deliberately deferred until Garage and Investor settlement state can be checked authoritatively. Investor Profit/Exit settlement remains Phase 8 scope.

### Phase 6 — Garage, Jobs, and Labour Scope

**Goal:** Deliver stock-Vehicle work and external-customer Garage work with their separate financial and operational relationships.

**Starts when:** Phase 5 establishes Vehicle identity and Company/Branch boundaries.

Phase 4 Accounting and Phase 5 Vehicle/Investment contracts must be inspected and reused; Garage must not create parallel Vehicle, Investor or receipt identity owners. Locked Garage business rules are recorded in `docs-final-v2/`. The implementation architecture and local verification evidence are recorded in [the Phase 6 audit](../architecture/phase-06-garage-jobs/PHASE-06-GARAGE-JOBS-ARCHITECTURE.md).

**Ends when:** Garage work can operate with Investment enabled or disabled and approved costs/revenue link to their authoritative sources.

**Status:** COMPLETE LOCALLY — implementation and local automated/browser verification passed 2026-11-18. CI, staging/production runtime and deployment remain UNVERIFIED; see the local implementation checkpoint at the end of this roadmap.

### Phase 7 — Sales, Buyers, and Collection

**Goal:** Deliver Stock Vehicle Sales, Buyer records, actual collections, receivables, and applicable refund positions.

**Starts when:** Vehicle, funding, Garage-cost, and Accounting foundations are available.

**Ends when:** Sales and collection positions remain separately traceable and provide verified source events for downstream financial flows.

**Status:** COMPLETE LOCALLY — integrated implementation and local automated/browser verification passed 2026-11-18. GitHub CI, staging/production runtime, and deployment remain UNVERIFIED; see the [Phase 7 implementation architecture and evidence](../architecture/phase-07-sales-buyers-collection/PHASE-07-SALES-BUYERS-COLLECTION-ARCHITECTURE.md).

### Phase 8 — Integrated Finance, Settlement, Corrections, and Company Accounting

**Goal:** Join actual collection to principal and Running Capital recovery, eligible Investor and Company shares, reconciliation, settlement, Company result, Owner Distribution, corrections, and audit.

**Starts when:** Phases 4–7 provide the necessary authoritative source events.

**Ends when:** Implemented positive financial flows reconcile across modules, and unresolved exceptional behavior remains blocked from invented outcomes.

**Status:** IN PROGRESS — INCOMPLETE LOCALLY; ACCEPTANCE BLOCKED

**Decision boundary:** Sale-date deal Profit placement, manual Vehicle Loss confirmation, Available-Fund withdrawal, Company-level cross-Branch Profit/settlement correction, pre-OFF Exit continuation, manual Company distributable confirmation, negative-result carryforward, verified Vehicle Company Share recognition, and ordinary Investor Vehicle Profit payment authority have approved rules in V2. Typed Company Share recognition and a narrow deal-level Investor Profit payment are implemented locally. Interim payment, period reconciliation/Loss-offset/Exit-settlement records, and Company period/Owner Distribution records remain missing; do not infer amounts or post cash.

### Phase 9 — MAIN VIRMS SYSTEM CORE-COMPLETE

**Goal:** Confirm the core platform, minimum Back Office, Main Operations, integrated core modules, Accounting backbone, authorization boundaries, and critical integration checks are complete for the implemented core workflows.

**Starts when:** Phases 1–8 have reached their defined end conditions.

**Ends when:** The Main VIRMS operational system is usable for its required core workflows and is ready for the first separate user-facing portal.

**Status:** BLOCKED — PHASE 8 INCOMPLETE; INTEGRATED ACCEPTANCE NOT RUN

### Phase 10 — Investor Portal

**Goal:** Deliver the first major separate user-facing system after Main System core completion, focused on each Investor's permitted self-service and read views, plus the approved normal Exit request.

**Starts when:** Phase 9 is complete and the required Investor positions are available through authorized sources.

**Ends when:** Investors can access their own permitted Fund, Vehicle, confirmed history, payout/reconciliation, recoverable, Exit, and settlement status information under backend authorization.

**Status:** BLOCKED — PHASE 9 ACCEPTANCE AND PHASE 8 FINANCIAL POSITIONS INCOMPLETE

**Decision boundary:** The private portal must reflect the approved Sale-date Profit periods, confirmed Interim-as-Paid rule, Available-Fund rule, and Exit/cancellation workflow. A deal-level Investor Profit payment command and typed Accounting link now exist locally; period reconciliation, Interim payment, and Exit settlement remain incomplete. The portal may show actual recorded deal payments but must not show unreconciled amounts as payable.

## Phase 8–10 local implementation checkpoint — 2026-11-19

Current inspected worktree: `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`, HEAD `d57a92085344228e8bf1b86d0867ec1d57adf662`. This is a dirty local implementation; no commit or push is implied.

- **Phase 8:** partial source implementation exists for versioned Vehicle-result confirmation, Sale-date gross Investor-period projection, calendar configuration, typed non-cash Company Share Income recognition, Company Accounting Result read, an immutable deal-level Investor Profit payment with one typed Accounting cash movement, Investor portal identity, and Exit request/cancellation. Interim payments, persisted period reconciliation/Loss offsets, final Exit settlement, Company period confirmation/carryforward records, and Owner allocation/payment remain incomplete. Deal payment requires Vehicle Management, Investment, and Accounting ON, is Branch-scoped, idempotent, and capped to the current confirmed share. Their business rules noted above are approved; Phase 8 is not complete.
- **Phase 9:** the acceptance matrix inventories the core journeys. Focused tests and local checks do not establish full core-workflow browser acceptance. Phase 9 remains blocked on Phase 8 and its integrated acceptance run has not occurred.
- **Phase 10:** bound self-profile, Investor portal read/request views, and Accountant binding management are implemented in part. The server-paginated `portal/self/fund-history/` exposes only the bound Investor's Fund credits, principal returns, Vehicle commitments, and linked commitment adjustments; it excludes cash-account details and external references. Attribution corrections that intersect historical use/return mark both Investors for manual review and suppress derived totals. Vehicle costs, protected agreement percentages, Sale prices, and Buyer balances remain excluded. The portal now shows its own recorded deal Profit payments while keeping periods `NOT_RECONCILED`; payable, Interim-paid, recoverable, and final settlement positions remain unavailable. Phase 10 is incomplete.

Latest local verification on disposable PostgreSQL, 2026-11-19: after adding the deal payment's Vehicle Management revision, two focused API/concurrency tests passed and fresh test-database migrations applied. A preceding focused backend run passed 36 sale/payment/finance/portal tests before that final revision addition. Django `check`, `makemigrations --check --dry-run`, Python compilation, and `git diff --check` passed. The full React suite passed 231 tests across 39 files; configured lint passed; production build passed with a 751.70 KB main-chunk warning. These checks do not replace authenticated integrated browser acceptance. CI, staging, production and deployment remain unverified. Details: [Phase 8 architecture](../architecture/phase-08-integrated-finance/PHASE-08-INTEGRATED-FINANCE-ARCHITECTURE.md), [Phase 9 matrix](../architecture/phase-09-main-system-core/PHASE-09-CORE-ACCEPTANCE-MATRIX.md), and [Phase 10 architecture](../architecture/phase-10-investor-portal/PHASE-10-INVESTOR-PORTAL-ARCHITECTURE-PLAN.md).

### Phase 11 — Owner Platform

**Goal:** Deliver the Owner's authorized read-only oversight and analysis surface over available Company information.

**Starts when:** Investor Portal is complete and the relevant authorized Company reporting and audit sources are available.

**Ends when:** The Owner can use permitted read-only oversight without ordinary operational or financial mutation.

**Status:** NOT STARTED

### Phase 12 — Media and Publication Surface

**Goal:** Deliver authorized Vehicle images, public-safe fields, publication, and availability workflows.

**Starts when:** Main System Vehicle identity and approved media boundaries are available.

**Ends when:** Approved public-facing Vehicle information can be published without exposing private Company or Investor finance.

**Status:** NOT STARTED

### Phase 13 — Reporting, Dashboard, and Audit Refinement

**Goal:** Complete the permission-scoped reporting and dashboard views, audit access, and corrections visibility needed across approved surfaces.

**Starts when:** Core modules and the relevant Investor, Owner, and Media sources are integrated.

**Ends when:** Reports and projections reconcile to their authoritative sources and respect Company, Branch, role, and privacy boundaries.

**Status:** NOT STARTED

**Decision boundary:** `BLOCKED BY BUSINESS DECISION` — any report or distribution view that depends on the unresolved Company distributable-Profit basis or cross-Branch correction authority.

### Phase 14 — Optional AI and Automation

**Goal:** Add only approved read-only AI assistance or optional automation after required business systems and verified data boundaries exist.

**Starts when:** Required core and user-facing systems are stable, with authorized data sources available.

**Ends when:** Any included assistance remains within approved read-only or explicitly confirmed automation boundaries; otherwise record it as deferred.

**Status:** OPTIONAL / DEFERRED

### Phase 15 — V2 Release Readiness / Production Readiness

**Goal:** Verify the intended required V2 scope, integration, authorization and security, critical tests, migration/data readiness, and deployment/operations readiness for a production-release decision.

**Starts when:** Required phases are complete and optional/deferred scope is recorded.

**Ends when:** Readiness evidence is reviewed, unresolved business decisions have not been implemented through guessed behavior, and the system is ready for a production-release decision. This phase does not claim that production deployment has occurred.

**Status:** NOT STARTED

## Codex Working Rule

When starting any roadmap phase:

1. Read the current relevant `docs-final-v2/` documents.
2. Read the current living architecture maps; if they are absent or stale, establish/reconcile the current architecture truth before phase design.
3. Inspect the current implementation.
4. Identify the exact phase boundary.
5. Create or reconcile only the architecture needed for that phase.
6. Identify any `BUSINESS DECISION REQUIRED` blockers.
7. Implement the phase vertically.
8. Test and verify integration.
9. Update roadmap status only after evidence exists.

Historical or deleted pre-V2 documents are not current authority and must not be restored as current requirements.

## Phase 5 Monthly Interim business-decision update — 2026-11-04

The Monthly Interim amount is now approved as a fixed, individually configured amount per Investor, set or edited only by that Company's Company-level Accountant. This supersedes the eligible-principal calculation question and the former Platform Back Office-only authority for this field. Permitted active-cycle principal withdrawals and the Investor reconciliation-period deal/payout relationship remain BUSINESS DECISION REQUIRED. Phase 5 remains NOT STARTED; this roadmap note does not lock a code architecture or authorize implementation. See the [canonical Investor finance decision](../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions) and [role decision](../docs-final-v2/02-user-roles-permissions.md#approved-business-decision-additions).

## Phase 5 Interim-as-Paid reconciliation decision — 2026-11-04

Confirmed Monthly Interim payments are included as Paid against Investor Profit at reconciliation; earned Profit remains separately displayed and is not rewritten by the advance. This resolves only the treatment/display of Interim advances. Period deal inclusion and ordinary deal-level payout interaction remain BUSINESS DECISION REQUIRED. Phase 5 remains NOT STARTED. See the [canonical Investor finance addition](../docs-final-v2/05-vehicle-investor-finance-workflow.md#approved-business-decision-additions).

## Phase 5 implementation checkpoint — 2026-11-07

This later local implementation checkpoint supersedes only the earlier roadmap notes above that Phase 5 remains `NOT STARTED`. Status is **IMPLEMENTATION PARTIAL / BLOCKED** on local branch `codex/phase5-investment-foundation`, based on Phase 4 checkpoint `50fb67c1c2256f6a164344344c8c2a12e04407f8`; the work is uncommitted and has not been pushed. Investor/interim persistence, Fund credit and principal-return API, Vehicle identity and Branch-movement API, and typed Accounting capital links are implemented and locally verified against disposable PostgreSQL.

Vehicle purchase/funding and Running Capital allocation remain blocked by Q39; safe deactivation and React form/list integration remain blocked by missing authoritative dependencies and incompatible current fields/IDs. Investor Profit/Loss/Exit settlement and mock-data import are not implemented. Phase 5 is not complete, and Phase 6 should not be marked started from this partial checkpoint. See [Phase 5 execution evidence](../docs/phase5-execution-progress.md). No staging/production readiness is inferred.

## Phase 5 local implementation and verification checkpoint — 2026-11-15

This current checkpoint supersedes the 2026-11-07 partial/blocked implementation checkpoint above and the earlier NOT STARTED decision notes. The approved Phase 5 core scope is **COMPLETE on the local worktree** `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`; changes remain uncommitted and unpushed. Local evidence: Django `apps` suite 330/330 on disposable PostgreSQL plus 2 targeted Purchase concurrency/module-OFF race tests; React suite 132/132; configured lint/build pass; fresh migration apply, schema/system checks, `investment.0007` reverse/reapply pass; local browser reload preserved Fund Credit attribution correction. Details and limits are in [the Phase 5 execution report](../docs/phase5-execution-progress.md).

The remaining Garage Job and Investor settlement sources block only Vehicle deactivation/registration reuse. Investor Profit/Exit settlement belongs to Phase 8. Offline financial writes, added automation, and staging/production/deployment are not included or verified. Phase 6 may proceed using Phase 5's Vehicle identity and accounting contracts; no claim is made that Phase 6 has started.

## Phase 5 audit-candidate checkpoint — 2026-11-16

This checkpoint supersedes the 2026-11-15 verification counts above and the earlier Phase 4 status statement. The approved Phase 5 core scope, including four audit fixes, is locally verified and committed on `codex/phase5-investment-foundation` for review. The exact commands, results, scope exclusions and external verification limits are recorded in [`docs/phase5-execution-progress.md`](../docs/phase5-execution-progress.md) and [`output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md`](../output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md). No remote push or deployment occurred. The Phase 4 base commit is part of this candidate's history; remote branch state must be refreshed before any push.

## Phase 5 audit branch publication — 2026-11-16

The candidate was pushed as a normal fast-forward to `origin/codex/audit`. GitHub commit comparison verified the remote ref at `2ddbbce26bf43a25313190bf7266996d43243476`. The pushed history includes the Phase 4 base commit and Phase 5 implementation. No staging/production deployment is asserted. The separate local `codex/audit` worktree retains its pre-existing dirty changes and was not modified.

## Phase 6 local implementation and verification checkpoint — 2026-11-18

Phase 6's approved Garage, Customer Job and Labour scope is **COMPLETE LOCALLY** on worktree `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`, based on `26e509a1e80ca43a6ae360863b2eeddb24a06e0c`. The worktree remains dirty and changes are uncommitted/unpushed. Implementation includes Company/Branch-scoped Garage Jobs and history, Stock Vehicle cost links, external-customer charges/receipts/costs/payments/refunds and corrections, Labour records/payments, typed Accounting links, module/role enforcement, idempotency and transaction guards.

Verification on disposable PostgreSQL: 131 Garage/Accounting tests and 278 Accounts/Tenants/Investment/Vehicle regression tests passed; Django system and migration-drift checks passed; React passed 198 tests across 35 files, lint and production build. The local browser E2E recorded a ₹50 partial cost payment and a ₹70 workshop refund, allocated ₹50 to the cost and ₹20 to a separately selected Income record, then reloaded and verified persisted payment/refund history. Direct database queries confirmed exactly one cash movement for the payment and one for the refund, plus one ₹20 Income application with no extra cash movement. The same refund remained visible at 390px and 320px without horizontal document overflow.

This checkpoint does not establish CI, staging, production or deployment readiness, and no persistent user database was migrated. Final Company Profit recognition and period-close behavior remain outside Phase 6 under V2 `09`; Investor Profit/Exit settlement remains Phase 8. No commit, push or deployment was performed.

## Phase 7 local implementation and verification checkpoint — 2026-11-18

Phase 7 is **COMPLETE LOCALLY** on worktree `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, branch `codex/phase5-investment-foundation`. The pre-existing Sale/receipt/refund/correction flows were integrated with Phase 6 Stock Vehicle costs; this completion adds saved Sale correction history to the API response and React views so the audit trail remains visible after reload. No business rule, permission, route, database schema, or migration changed.

On disposable PostgreSQL, `python manage.py test apps.vehicles.tests.test_sale_api apps.garage.tests.test_api --verbosity 1` passed 57 tests and `python manage.py test apps.vehicles.tests.test_sale_concurrency --verbosity 1` passed 3 Sale concurrency tests for concurrent receipts, refunds, and correction versions. Django system/schema-drift checks passed; React passed 200 tests across 35 files, lint, and production build. A local browser workflow verified Sale, partial receipt, price correction, partial refund, persisted history after reload, and a 390 px viewport without horizontal overflow. Direct disposable-database inspection confirmed one cash movement each for the actual receipt and refund. Full evidence and limits are in the [Phase 7 architecture record](../architecture/phase-07-sales-buyers-collection/PHASE-07-SALES-BUYERS-COLLECTION-ARCHITECTURE.md). CI, staging/production, and deployment remain UNVERIFIED. No persistent user database was modified and no commit or push was performed.

## Phase 8–10 Investor period reconciliation snapshot — 2026-11-19

The Company Accountant can now confirm a Sale-date Investor period calculation with an expected source fingerprint and reason. Each confirmation is a versioned immutable Investment record with the prior snapshot link and module revisions. Actual deal Profit paid, Monthly Interim paid and confirmed non-cash Loss offsets remain separate inputs. The current signed calculation position and later restatement delta are shown as calculations only; confirmation does not create a payable, recovery, Fund debit, Accounting movement or final settlement. A changed source requires a new reasoned confirmation, preserving earlier history.

**Verification in the current worktree:** the focused Vehicle Sale API regression passed on disposable PostgreSQL after applying fresh migrations; it covers Company Accountant permission, Branch denial, same-source replay, one cash movement for the later actual deal payment only, immutable snapshot history, and version-2 restatement after a -₹100 source change. The regression now also verifies that the Investor self projection shows only its own current snapshot, marks it stale after a further payment, and exposes no internal reason/source fingerprint/actor ID or cash effect. Two targeted React/API files passed 29 tests; `npx tsc --noEmit` passed. CI, full integrated Phase 9 browser acceptance, staging, production and deployment remain UNVERIFIED.

**Still blocking Phase 8–10 completion:** final Investor Exit/settlement and post-Exit adjustment repayment/refund/waiver outcomes; principal and Running Capital recovery; Company period close and negative carryforward; protected Owner split snapshots, exact allocation and actual partial payment; private Investor payable/recoverable and final settlement projection; Phase 9 full backend integration in sample-backed Dashboard/older Vehicle detail; full role-based integrated browser acceptance and responsive reload proof. The current worktree remains dirty and uncommitted; no push, deployment or persistent user database change occurred.

## Phase 8–10 Monthly Interim payment slice — 2026-11-19

Q135's approved rule now has an implementation slice: Monthly Interim may be paid in partial/repeated actual transfers, with the Investor's effective configured amount as the Company-wide monthly cap across Branches. The payment is append-only, stores the selected Cash/Bank account and Branch, links to exactly one typed Accounting outflow, and carries actor/module revision plus audit evidence. The period projection and bound Investor portal show Interim Paid separately from deal Profit paid, without claiming final reconciliation. The Investor-only history endpoint is paginated and resolves identity from the active Company binding.

**Verified locally:** on the disposable PostgreSQL test database, `python manage.py test apps.investment.tests --verbosity 1` passed 41 tests, including fresh schema creation through `accounting.0024`, module and Branch boundaries, repeat/idempotency, monthly cap and concurrent cap enforcement, source-linked cash effects, and portal privacy. Targeted React portal/API tests passed 32 tests. The test database was destroyed by Django after the run. CI, browser-wide Phase 9 acceptance, staging, production, and deployment remain `UNVERIFIED`.

**Remaining Phase 8–10 work:** persisted period reconciliation/restatement and recoverable history, Investor Exit settlement, principal/Running-Capital recovery, Company period confirmation with Loss carryforward, Owner allocation/payment records, integrated end-to-end acceptance, full UI/browser reload and responsive verification. Phases 8–10 remain incomplete and the existing worktree stays dirty/uncommitted; no commit, push, deployment, or persistent user database change occurred.
