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

This roadmap now describes the local `codex/audit` integration line. Phase 1 and Phase 2 acceptance evidence below is from the isolated integration snapshot; no remote push or staging update is claimed. The original dirty audit worktree and the separately dirty `staging` worktree are preserved. Current source still has no business-domain APIs/models for Main Operations, Garage, Accounting, Investment, Sales or Inventory.

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

**Status:** ACCEPTED on the local audit integration line, 2026-11-02. The React suite passed 74/74, production build and configured lint passed, and browser smoke covered login/context/logout/expiry and 320/390/768/1024/1440 widths on the isolated candidate. Business data remains mock-backed because no business API exists. Production origin/proxy/cookie behavior remains unverified; no staging or remote integration is claimed.

**Decision boundary:** No new Phase 2 business decision is introduced. V2 financial/access decisions remain open for their owning future modules.

### Phase 3 — Main Operations Foundation

**Goal:** Establish the Main Operations Software as the primary Company workspace for Accountant / Operations, connected to the platform foundation and shared capabilities.

**Starts when:** Phase 2 provides the preserved authenticated frontend and real Company/Branch/account context.

**Ends when:** The core operational workspace can host authorized business capabilities and their vertical user flows.

**Status:** COMPLETE — approved Company module-state foundation implemented and verified locally; staging/production remain unverified.

The approved Phase 3 slice establishes versioned Company module state, scoped Platform Back Office administration, an authenticated Company-scoped read API and the React shared query boundary. The approved 14-code catalog includes Audit and Corrections; audit capture remains cross-cutting. On the local `codex/audit` worktree, React passed 89/89 tests, lint and production build; Django passed 232/232 account/tenant tests on disposable PostgreSQL 15, system checks and migration drift checks. Fresh migration apply, empty-state reverse/reapply and populated-history reverse protection were verified. No business workflows or financial APIs were added. This is not staging/production runtime evidence and no deployment is claimed. The preserved Garage design candidate is not Phase 3 under this roadmap; Garage remains Phase 6 after Phases 4 and 5.

### Phase 4 — Accounting Foundation

**Goal:** Establish the Company accounting backbone and source-event links needed by Investment, Garage, Sales, Running Capital, receipts, payments, and expenses.

**Starts when:** Phases 2–3 establish Company/Branch boundaries and the Main Operations foundation.

**Ends when:** Implemented business events can be represented and reconciled in Company accounting without duplicate economic entries.

**Status:** NOT STARTED

**Decision boundary:** `BLOCKED BY BUSINESS DECISION` — Company distributable-Profit basis and period close/carryforward; foundational accounting work can proceed within the defined source-event boundaries.

### Phase 5 — Investment, Vehicle, and Running Capital

**Goal:** Deliver the Investor/Fund and stable Company Vehicle flows, approved costs, and separately tracked actual Company Running Capital through the operational workspace.

**Starts when:** Platform, Main Operations, and required Accounting foundations are in place.

**Ends when:** Authorized funding and Vehicle positions can be recorded and connected to the correct Company, Branch, Investor, and accounting sources.

**Status:** NOT STARTED

**Decision boundary:** `BLOCKED BY BUSINESS DECISION` — Monthly Interim eligible-principal basis and withdrawal limits.

### Phase 6 — Garage, Jobs, and Labour Scope

**Goal:** Deliver stock-Vehicle work and external-customer Garage work with their separate financial and operational relationships.

**Starts when:** Phase 5 establishes Vehicle identity and Company/Branch boundaries.

Phase 4 Accounting and Phase 5 Vehicle/Investment contracts must be inspected and reused; Garage must not create parallel Vehicle, Investor or receipt identity owners. Locked Garage business rules are recorded in `docs-final-v2/`; detailed Garage implementation planning is deferred until these roadmap dependencies are accepted.

**Ends when:** Garage work can operate with Investment enabled or disabled and approved costs/revenue link to their authoritative sources.

**Status:** NOT STARTED

### Phase 7 — Sales, Buyers, and Collection

**Goal:** Deliver Stock Vehicle Sales, Buyer records, actual collections, receivables, and applicable refund positions.

**Starts when:** Vehicle, funding, Garage-cost, and Accounting foundations are available.

**Ends when:** Sales and collection positions remain separately traceable and provide verified source events for downstream financial flows.

**Status:** NOT STARTED

### Phase 8 — Integrated Finance, Settlement, Corrections, and Company Accounting

**Goal:** Join actual collection to principal and Running Capital recovery, eligible Investor and Company shares, reconciliation, settlement, Company result, Owner Distribution, corrections, and audit.

**Starts when:** Phases 4–7 provide the necessary authoritative source events.

**Ends when:** Implemented positive financial flows reconcile across modules, and unresolved exceptional behavior remains blocked from invented outcomes.

**Status:** NOT STARTED

**Decision boundary:** `BLOCKED BY BUSINESS DECISION` — deal Profit versus period reconciliation; manual Loss impact and confirmation authority; distributable-Profit basis and period close; cross-Branch correction authority; minimum settlement actions while a module is OFF. Unaffected confirmed positive flows may proceed.

### Phase 9 — MAIN VIRMS SYSTEM CORE-COMPLETE

**Goal:** Confirm the core platform, minimum Back Office, Main Operations, integrated core modules, Accounting backbone, authorization boundaries, and critical integration checks are complete for the implemented core workflows.

**Starts when:** Phases 1–8 have reached their defined end conditions.

**Ends when:** The Main VIRMS operational system is usable for its required core workflows and is ready for the first separate user-facing portal.

**Status:** NOT STARTED

### Phase 10 — Investor Portal

**Goal:** Deliver the first major separate user-facing system after Main System core completion, focused on each Investor's permitted self-service and read views, plus the approved normal Exit request.

**Starts when:** Phase 9 is complete and the required Investor positions are available through authorized sources.

**Ends when:** Investors can access their own permitted Fund, Vehicle, confirmed history, payout/reconciliation, recoverable, Exit, and settlement status information under backend authorization.

**Status:** NOT STARTED

**Decision boundary:** `BLOCKED BY BUSINESS DECISION` — unresolved Interim eligibility/withdrawal and Profit/reconciliation behavior; affected views or actions must not imply a decided outcome.

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
