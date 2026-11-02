# Phase 2 Frontend Foundation — Execution Report

**Observed:** 2026-11-02, Asia/Calcutta
**Status:** `PHASE_2_FULLY_COMPLETE_AND_ACCEPTED`, integrated on the local `codex/audit` line with P2-13–P2-22 role-navigation and Investor mock-data boundary corrections. The remote branch remains at the earlier baseline `f266803acd5e86caa2286fb8eae41df6cadfcb86` until a separately authorized push; staging is untouched.
**Scope:** Phase 2 React authentication, bounded Phase 1 API context, role presentation and final acceptance. Business modules remain demo/future work; production readiness is not claimed.

The final integrated React source passed **74/74** tests, configured `npm run lint`, and `npm run build`; isolated browser acceptance covered auth/context/session flows and widths 320, 390, 768, 1024 and 1440. The main-bundle advisory remains. No business-domain API or persisted business mutation was introduced. The remaining report sections retain historical candidate evidence and intermediate counts where explicitly dated.

## P2-12 Branch-context boundary — verified

- The Phase 1 Branch list serializer returns `id`, `tenant_id`, and `name`; it does not return role fields. The frontend parser previously reused the richer `/auth/me/` Branch-summary shape and rejected the actual paginated list response. A regression test reproduced the mismatch before the parser was corrected to use a separate `BranchListItem` contract.
- `/auth/me/` Branch summaries remain authenticated context only. `branches_truncated` is surfaced in the existing context menu. A full list query exists only as an explicit paginated hook; no current screen calls it because there is no supported business endpoint that accepts a Branch filter.
- The query hook uses the server-derived Company UUID, user/Company/page-scoped cache keys, and `AbortSignal`; Investor-only and truncated Company context do not activate the list query. Backend Branch list/detail remains the authority and filters to the user's effective Company/Branch grants.
- The mock Garage selector and mock `garageId` values remain unchanged and disconnected from Branch IDs. Business-screen Branch filters remain deferred until an approved endpoint defines the filter contract.
- P2-12 focused verification: `npm run test -- --reporter=dot src/api/__tests__/types.test.ts src/api/__tests__/queries.test.tsx src/api/__tests__/queryKeys.test.ts src/auth/__tests__/AuthRoutes.test.tsx` — **19 passed**. Full frontend suite — **31 passed**; TypeScript/Vite build and configured lint passed. `python manage.py test apps.tenants.tests.test_tenants.TenantIsolationTests.test_branch_reads_require_company_grant_and_effective_assignment --verbosity 2 --noinput` — **1 passed** on disposable PostgreSQL. The exact Phase 1 baseline's full accounts/tenants suite previously passed 199 tests on disposable PostgreSQL; it was not rerun for this frontend-only contract fix.
- Browser evidence from the isolated combined baseline confirms login, password change, `/auth/me/` Company/Branch context, session restore, logout and expiry; no unauthorized Branch-list request was made, no token was stored in browser storage, and no JavaScript page error occurred. This change does not alter those browser paths.
- **P2-12 status at that verification point: `P2-12_COMPLETE_AND_VERIFIED` for the Branch-context boundary.** Branch filtering in business screens remains intentionally deferred. Subsequent P2-13–P2-22 completion and acceptance are recorded at the end of this report.

## Baseline and dependency

- Worktree: `D:/VIRMS/tmp/phase1-consolidated-20261101`
- Published branch: `origin/codex/audit` at `f266803acd5e86caa2286fb8eae41df6cadfcb86`; parent Phase 1 correction baseline: `6ee3202f0432f19577f88a24b1d3c97ff2d36eef`. The remote SHA was verified after push.
- The exact P2-12-focused frontend tests (19/19), full frontend suite (31/31), targeted backend Branch-scope test (1/1), configured lint, TypeScript/Vite build, and `git diff --check` were run on the candidate before publication. They were not rerun on the exact published commit; these are local execution results, not GitHub CI evidence.
- Phase 1 dependency evidence remains separate: the parent Phase 1 correction candidate passed its 199-test accounts/tenants regression, fresh PostgreSQL migration replay through `accounts.0012_scope_end_monotonic`, Django checks and schema-drift check. See [the Phase 1 report](phase1-execution-progress.md).
- `staging` remains separate and was not updated. Production readiness and production host/proxy/cookie behavior are not claimed.

## Skills actually used

- `test-driven-development` — reproduced the missing cancellation propagation with failing tests before implementing the fix.
- `security-and-hardening` — reviewed session, CSRF, Company/Branch scope and sensitive-query cache boundaries.
- `code-review-and-quality` — checked changed files, UI preservation, dependency audit and final verification evidence.

## Implemented

- Kept `demo/react` as the Vite/React 19/TypeScript application. No Next.js application was introduced.
- Added login, first-password-change, session-loading and session-unavailable UI; connected login, password change, logout and session restore to the Phase 1 Django session API.
- Added a typed same-origin API client with CSRF bootstrap/header, `credentials: include`, no-store reads, request IDs, response validation, safe error mapping, `Retry-After` handling and no automatic mutation retries.
- Added TanStack Query with memory-only state, identity/scope-aware keys, conservative read retries and cancellation/cache clearing at logout, 401/session expiry and authorization-scope changes.
- Final adversarial review found that those cancellations were not reaching the underlying HTTP fetch. The query `AbortSignal` now flows from TanStack Query through `/auth/me/` and Branch reads to `fetch`; an aborted request remains an abort instead of becoming a retryable network error. This closes the in-flight stale-response/cache risk documented in the [TanStack Query cancellation guide](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation).
- Displayed the authenticated Login ID and verified Company/role/bounded Branch context in the existing shell. The Company/Branch and role display is presentation only; backend policy remains authoritative. Platform users navigate to Django Admin.
- Added a Company Branch query hook for owner/accountant/media roles. No prototype business page currently accepts an authoritative Branch filter, so the hook is not wired to the synthetic Garage selector. The app displays the bounded Branch summaries already returned by `/auth/me/`.
- Kept Vehicle, Investor/Fund, Garage, Inventory, accounting, reports and dashboard business values synthetic/reference data. No new business endpoint or persisted-write success was added. Local-only actions now say that their changes were not saved to the backend.

## UI preservation

The candidate `demo/react` tree was compared with `D:/VIRMS/demo/react`: 74 source files were present in the source snapshot; 8 existing files differ in the candidate (`package.json`, lockfile, Vite config, `src/main.tsx`, `src/App.tsx`, `src/components/AppShell.tsx`, `src/components/TopBar.tsx`, and `src/components/dashboard/DashboardHeader.tsx`). The code differences are for dependency/test setup, auth routing, API proxying, authenticated identity/context props and truthful prototype actions. Existing business pages, route keys, navigation grouping, Sidebar, cards and tables were not rebuilt or redesigned. The TopBar now presents required authenticated Company/role/Branch context and Dashboard greeting uses the real Login ID; these are the limited integration-driven content changes.

Only authentication/loading/error UI was newly created. No Next.js code was copied into the React app. The separate `demo/accountant-ui-demo` was not used as an API source.

## API call classification

| Call | Classification | Current use |
|---|---|---|
| `GET /api/v1/auth/csrf/` | REQUIRED | Fetched when no CSRF cookie exists before an unsafe request. |
| `POST /api/v1/auth/login/` | REQUIRED | Login form; creates the backend session. |
| `GET /api/v1/auth/me/` | REQUIRED | Session bootstrap/restore and post-login/password-change verification; supplies bounded Company/Branch context. |
| `POST /api/v1/auth/password/change/` | CONDITIONAL | Required for accounts whose backend state requires first-password change. |
| `POST /api/v1/auth/logout/` | REQUIRED | User logout; uncertain network outcome is not shown as server success. |
| `GET /api/v1/tenants/{company_uuid}/branches/` | CONDITIONAL | A typed, gated query hook exists for authorized Company context; no synthetic Garage selector is mapped to Branch IDs and current screens do not trigger this call. |
| Provision/reset/status/revoke and all future business APIs | CONDITIONAL / NOT CALLED | No React caller was added. |

## Validation actually run

- `npm run test -- --reporter=dot` — **30 tests passed across 6 files**. The signal-propagation regression was first run RED (4 targeted assertions failed), then the focused suite passed **24/24** after the fix.
- `npm run lint` — **passed** for `src/api`, `src/auth`, the entry point and touched shell components. `src/App.tsx` is covered by TypeScript build and browser checks but is excluded by the focused lint configuration; project-wide lint cleanliness is not claimed.
- `npm run build` — TypeScript and Vite production build passed. Vite reports the main JavaScript chunk at **593.99 kB** (500 kB advisory threshold; 155.18 kB gzip).
- `npm audit --json` and `npm audit --omit=dev --json` — **0 reported vulnerabilities** for the generated lockfile.
- Backend: `python manage.py test apps.accounts apps.tenants --verbosity 1` — **199 passed** on disposable PostgreSQL 15.19.
- Fresh disposable PostgreSQL migration replay applied migrations through `accounts.0012_scope_end_monotonic`; `python manage.py check` passed; `python manage.py makemigrations --check --dry-run` reported no changes; migration plan had no pending operations.
- Browser integration against the candidate Django server and disposable DB verified CSRF, wrong-password error, login, mandatory password change, `/auth/me/` context, reload/session restore, logout, and Platform redirect to working Django Admin. After the cancellation fix, a fresh browser run again verified login, mandatory password change, Company/Branch context, no auth-token storage, zero automatic Branch-list calls and zero page errors. Owner/Accountant Branch reads were confined to their Company; foreign Branch detail returned 404. Investor context showed only its own Company and direct unauthorized Branch access was denied.
- Keyboard/accessibility smoke checked Login and password-change labels, focus order, password mismatch alert linkage, and 44 px controls at 320 px. Existing application routes Vehicles, Garage Jobs, Inventory, Investor Fund, Accounting, Reports and Overview opened successfully.
- At widths 320, 390, 768, 1024 and 1440 px, there was no new overflow relative to the original snapshot. The original UI already measured 432 px document width at 320/390 px; that existing narrow-screen overflow was preserved, not corrected in this UI-frozen phase.
- No browser JavaScript page errors were observed. Expected auth bootstrap 401 and denied cross-scope 404 responses were handled.
- Request audit: the development server's React StrictMode issued two initial anonymous `/auth/me/` 401 checks; a production-build preview issued exactly one. After login, `/auth/me/` supplied context and the Investor page made zero automatic Branch-list requests. No duplicate request was observed in the production build.
- Temporary Django and Vite servers were stopped and the disposable PostgreSQL container was removed after runtime validation. The existing service on port 8001 and unrelated containers were not touched.

## Final adversarial audit and deferrals

- The review caught and fixed an A-level cache-isolation risk before final acceptance: cancelled Branch/auth queries could leave their HTTP fetch running. Regression-first evidence showed the missing signal propagation (4 targeted failures); after the fix, the signal is passed and logout cancellation aborts the pending request before the cache is cleared. Targeted and full frontend tests pass.
- **A — Must fix now:** none found in the reviewed Phase 2 scope.
- **B — Should fix now:** none found in the reviewed Phase 2 scope.
- **C — Deferred:** production host/proxy/cookie-origin settings remain unconfigured and unverified; they require the selected hosting topology. Branch filters for business pages remain deferred until an approved backend business endpoint accepts Branch scope. The existing 320/390 px overflow and the Vite bundle-size advisory are recorded for a separately authorized UI/performance task.
- **D — Informational:** project-wide lint is not claimed. The focused lint command covers the Phase 2 integration and touched shell; full-project lint coverage remains unverified and outside this UI-preservation task.

The API client has no business API or local mock endpoint calls, and no auth token is stored in local/session storage. Role display and route guards do not authorize API access. Existing synthetic Garage UUIDs are not translated to Branch UUIDs. No A-level or material B-level Phase 2 issue remains in the tested candidate.

## Documentation, Git and release boundary

At the original Phase 2 planning snapshot, the referenced `architecture/05-SYSTEM-STRUCTURE-MAP.md` and `planning/V2-DEVELOPMENT-ROADMAP.md` were absent from that worktree. During later local consolidation, the roadmap was verified from the preserved staging worktree and recorded at `planning/V2-DEVELOPMENT-ROADMAP.md`; `architecture/05-SYSTEM-STRUCTURE-MAP.md` remains absent. The seven approved Garage decision documents under `docs-final-v2/` were subsequently updated as a separate roadmap/business-rule reconciliation; that did not add Phase 2 application behavior. The security supporting document records the approved six-character minimum, numeric-only and mixed-character password acceptance, and common-password/user-similarity validators.

Git publication at this initial audit snapshot: commit `f266803acd5e86caa2286fb8eae41df6cadfcb86` was pushed to `origin/codex/audit`; the verified remote SHA matched. Its parent is `6ee3202f0432f19577f88a24b1d3c97ff2d36eef`. No staging update, merge, deployment or Phase 3 work was performed. Acceptance was pending at that snapshot; the completion audit below supersedes that status.

## Initial independent P2-13–P2-22 audit — 2026-11-02 (superseded by the completion audit below)

Audit target: published source SHA `f266803acd5e86caa2286fb8eae41df6cadfcb86`; working source was unchanged. `origin/codex/audit` still matched this SHA; `origin/staging` remained `95384cdd9fdd548f4b434891ef353147ab2a04d2`. Existing documentation-only edits in the audit worktree were preserved.

| Task | Result | Repository/test evidence and remaining work |
|---|---|---|
| P2-13 | `PARTIAL` | Company roles are rendered in the authenticated TopBar and Platform Back Office redirects to Django Admin. The navigation registry is static and there is no role/navigation matrix test. V2 defines role authorities, but the current demo/business-page-to-role presentation mapping is not specified well enough to infer without making up which demo pages each role should see. No client-side role check is used as authorization. |
| P2-14 | `VERIFIED_DONE` | QueryClient has memory-only state, identity/scope/page keys, conservative read retries and no mutation retries. Auth lifecycle cancels/clears queries; query AbortSignal reaches fetch. Existing query-key, logout, expiry, scope-change and abort tests are in the passing suite. |
| P2-15 | `VERIFIED_DONE` | API errors normalize 400/401/403/404/409/429/5xx/network errors, request IDs and Retry-After; 401 dispatches session expiry except login/CSRF/me. Forms surface errors; prototype action notices explicitly say changes were not saved to the backend. Covered by client/error and auth tests in the passing suite. |
| P2-16 | `VERIFIED_DONE` | Authenticated shell uses server Login ID, one untruncated Company context, Company-wide role provenance, bounded Branch summaries and `branches_truncated`. Company/Branch IDs come from API context; frontend selection is not an authorization source. P2-12 boundary remains intact. |
| P2-17 | `VERIFIED_DONE` | Business screens continue to consume synthetic/reference data. API inventory shows no business API callers; local actions are labeled prototype/local and not saved. Garage IDs are not mapped to Branch IDs. |
| P2-18 | `PARTIAL` | Browser observed anonymous `/login` and Platform Admin redirection to Django Admin. Auth form exposes labels and a disabled-until-valid submit. This pass did not run the required 320/390/768/1024/1440 viewport, keyboard, focus, contrast and authenticated tenant-route browser matrix. Credentials were unavailable; no password was guessed or entered. |
| P2-19 | `VERIFIED_DONE` | On this published source checkout: `npm run test -- --reporter=dot` — 31/31; `npx --no-install tsc --noEmit` — passed; `npm run lint` — passed for configured scope; `npm run build` — passed with existing >500 kB bundle advisory. `git diff --check` — passed for current documentation edits. |
| P2-20 | `VERIFIED_DONE` | Plan/report classify auth/session/context as Phase 1-backed and business modules as demo/future; each future module is deferred for missing approved backend/API/data authority. No new business API was found. |
| P2-21 | `VERIFIED_DONE` | Living docs were updated for published commit/parent, remote SHA, staging boundary, approved 6-character password policy and current task evidence. Historical planning snapshots remain labeled as historical. |
| P2-22 | `NOT_READY` | Fresh audit found no A-level security defect in reviewed source, but P2-13 role-presentation mapping and P2-18 browser/a11y coverage remain incomplete. Final Phase 2 acceptance is not passed. |

### Current final-audit findings

- **A — Must fix now:** none found in the reviewed frontend/API/cache boundaries.
- **B — Should fix before acceptance:** P2-13 needs either an approved role-to-demo-navigation presentation matrix with tests, or an explicit accepted deferral; P2-18 needs the prescribed responsive/accessibility/browser evidence.
- **C — Deferred:** production origin/proxy/cookie topology; synthetic business modules and business-page Branch filters; existing 320/390px UI overflow; Vite bundle-size advisory.
- **D — Informational:** configured lint omits legacy `App.tsx`; no project-wide lint claim is made.

No source, tests, migrations, UI or package configuration changed during this audit. No commit, push, merge, staging update, deployment or Phase 3 work occurred.

## P2-13–P2-22 completion and final acceptance — 2026-11-02

**Candidate identity:** `D:/VIRMS/tmp/phase1-corrections-isolated-20261102`, branch `codex/phase1-corrections-isolated`, HEAD/base `f266803acd5e86caa2286fb8eae41df6cadfcb86`. It descends from the verified Phase 1 parent `6ee3202f0432f19577f88a24b1d3c97ff2d36eef`. The isolated worktree was dirty with unstaged Phase 2 changes; nothing was staged, committed or pushed. `origin/codex/audit` remained at `f266803acd5e86caa2286fb8eae41df6cadfcb86`; `origin/staging` remained at `95384cdd9fdd548f4b434891ef353147ab2a04d2`.

### P2-13 — `VERIFIED_DONE`

- V2 role state is presentation-only; Django remains the authorization authority. No role rule, API, migration or backend policy changed.
- Owner and Accountant retain their existing Company dashboard views and business navigation. Owner Distribution is now present for Owner and Accountant as the existing read-only governance notice; no distribution action or persistence was added.
- Investor-only dashboard subviews fail closed to Overview; dashboard, Fund, and Stock/Vehicle demo data are replaced with explicit Investor-scoped API placeholders. Direct Company dashboard query strings, direct Vehicle detail routes, and stale active routes are guarded. Investor governance notices omit report links that the Investor route policy denies.
- `Vehicles`/`All Vehicles` and `Settings` shortcuts now resolve to their registered primary routes. Media receives no unrelated business route because the current repository has no safe Media screen/API; its implementation remains future work.
- Regression tests cover role navigation, Owner Distribution, aliases, dashboard query handling, shared mock-data suppression, Investor direct-route denial, role-change route hiding and nonfunctional report-link suppression.

**Verified role presentation matrix (menu and prototype rendering only; the backend remains the authorization authority):**

| Role | Visible navigation in this candidate | Current page/data boundary |
|---|---|---|
| Owner | Dashboard, Vehicles, Garage Jobs, Investment Management, Company Accounting, Reports, Appearance & Theme. No Sale Corrections & Refunds item. | Company prototype views; ordinary write controls are hidden. Owner Distribution is a read-only governance notice. |
| Accountant / Operations Admin | Owner areas plus Sale Corrections & Refunds. | Company prototype views; write controls open local-only demo actions. Nothing is persisted to the backend. |
| Investor | Dashboard, Stock / Investor, Investor Fund, Investor Profit & Interim, Reconciliation & Settlement, Appearance & Theme. | Dashboard, Vehicle and Fund show Investor-scoped API placeholders; Profit/Interim and Reconciliation show read-only governance notices. No Company accounting, Garage, or Company report pages. |
| Media | Appearance & Theme only. | No Media page/API exists in this candidate, so no unrelated business/mock-data screen is exposed. |
| Platform / unknown role | No Company business navigation. | Platform Back Office remains outside this Company shell; unrecognized/missing roles fail closed to no business workspace. |

Branch context remains informational: prototype Garage identifiers are not translated to authorized Branch identifiers and do not filter these local sample views.

### P2-14 through P2-17 — `VERIFIED_DONE`

- Query cancellation/cache isolation, API error and request-ID handling, bounded Company/Branch context, and prototype-only business data were re-audited. P2-12 Branch context remains informational; mock Garage IDs are not mapped to Branch IDs.
- Source and request inventory show no new business API calls. Prototype business data/actions remain local and are not described as persisted.
- Re-ran `python manage.py test apps.accounts apps.tenants --verbosity 1 --noinput` — **199/199** passed on disposable PostgreSQL 17.11; Django created and dropped its test database. A separate fresh disposable database replayed all migrations through `accounts.0012_scope_end_monotonic`. `manage.py check` passed and `manage.py makemigrations --check --dry-run` reported no changes.

### P2-18 — `VERIFIED_DONE` for Phase 2 regression scope

- Candidate Vite (`127.0.0.1:5175`) was connected to the candidate Django server (`127.0.0.1:8014`) and dedicated disposable PostgreSQL 17.11 database `virms_p2_browser_20261102_a1`. Synthetic Owner and Investor users exercised CSRF/session login and authenticated `/auth/me/` Company/Branch context. Investor navigation omitted Company Accounting and Reports, and Investor dashboard rendered its scoped-data placeholder instead of shared Company metrics. No user account or the 8002 database was used; the synthetic session was logged out, the temporary database was dropped, and both candidate servers were stopped.
- Owner and Investor screens were checked at 320, 390, 768, 1024 and 1440 CSS px. The Owner dashboard initially overflowed because its tab strip kept its intrinsic width; it now scrolls within the available width. `document.scrollWidth` did not exceed the viewport at any checked width. Desktop tab-strip dimensions remain unchanged. The synthetic activity table retains its own horizontal scrolling.
- The previous axe scan found a `label-content-name-mismatch` caused by the visible `OP` avatar initials inside the context button. The initials are now marked decorative; the live accessibility tree no longer exposes `OP` while retaining the visible `All Garages` name. The full browser accessibility tree, login labels/alerts, and no-console-error state were rechecked after the fix.
- Keyboard check on the 320 px Investor view: mobile drawer opens with focus on Close; reverse Tab reaches Log Out; Tab returns to Close; Escape closes and restores focus to the opener. Component tests also cover the focus trap and focus restoration.

### P2-19 — `VERIFIED_DONE`

- Role/navigation regression suite — **31 passed across 6 files**, including Investor data-boundary, direct-route, narrow-tab-strip and decorative-avatar cases.
- `npm run test -- --reporter=dot` — **74 passed across 13 files**.
- `npm run build` — TypeScript and Vite production build passed; main chunk **605.33 kB** (158.00 kB gzip), above the 500 kB advisory threshold.
- `npm run lint` — passed for the package's configured scope (`src/api`, `src/auth`, entrypoint, AppShell, TopBar and DashboardHeader); no project-wide lint claim.
- `npm audit --json` — 0 vulnerabilities; `git diff --check` — passed (Git reports line-ending conversion warnings only).

### P2-20 through P2-22 — `VERIFIED_DONE`

- The dependency map keeps session/auth/Company/Branch context on Phase 1 APIs. Vehicles, Garage, Investor/Fund, Inventory, Sales/Collections, Accounting, Reports, dashboard aggregates and Media workflows remain deferred until their approved backend/data/API contracts exist. No API was invented.
- README, living architecture maps, this report, and the Phase 2 Markdown/JSON plan were updated to match the accepted local candidate and no-push state. At Phase 2 acceptance, `/docs-final-v2/` business rules were not changed; subsequent Garage business decisions were recorded separately in the current canonical docs.
- Fresh adversarial audit found no unresolved A-level or material B-level issue in P2 scope. Backend authorization, Tenant boundaries, cache isolation, session lifecycle, business/mock boundaries, route presentation, build/test/lint, and documented deferrals were rechecked.

### Final findings

- **A — Must fix now:** none.
- **B — Should fix before acceptance:** none.
- **C — Deferred:** production host/proxy/cookie topology; future business APIs and authorized Branch filters; Vite main-bundle advisory.
- **D — Informational:** configured lint intentionally excludes legacy `App.tsx`; project-wide lint cleanliness is unverified.

**Final status:** `PHASE_2_FULLY_COMPLETE_AND_ACCEPTED` for the local candidate. This does not publish it: no commit, push, merge, staging update, deployment or Phase 3 work occurred.
