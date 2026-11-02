# Phase 2 Frontend Foundation — Execution Report

**Observed:** 2026-11-02, Asia/Calcutta
**Status:** `PHASE_2_READY_FOR_ACCEPTANCE`
**Scope:** React authentication and Phase 1 API integration only. This is a local candidate result, not a staging integration or release.

## P2-12 Branch-context boundary — verified

- The Phase 1 Branch list serializer returns `id`, `tenant_id`, and `name`; it does not return role fields. The frontend parser previously reused the richer `/auth/me/` Branch-summary shape and rejected the actual paginated list response. A regression test reproduced the mismatch before the parser was corrected to use a separate `BranchListItem` contract.
- `/auth/me/` Branch summaries remain authenticated context only. `branches_truncated` is surfaced in the existing context menu. A full list query exists only as an explicit paginated hook; no current screen calls it because there is no supported business endpoint that accepts a Branch filter.
- The query hook uses the server-derived Company UUID, user/Company/page-scoped cache keys, and `AbortSignal`; Investor-only and truncated Company context do not activate the list query. Backend Branch list/detail remains the authority and filters to the user's effective Company/Branch grants.
- The mock Garage selector and mock `garageId` values remain unchanged and disconnected from Branch IDs. Business-screen Branch filters remain deferred until an approved endpoint defines the filter contract.
- P2-12 focused verification: `npm run test -- --reporter=dot src/api/__tests__/types.test.ts src/api/__tests__/queries.test.tsx src/api/__tests__/queryKeys.test.ts src/auth/__tests__/AuthRoutes.test.tsx` — **19 passed**. Full frontend suite — **31 passed**; TypeScript/Vite build and configured lint passed. `python manage.py test apps.tenants.tests.test_tenants.TenantIsolationTests.test_branch_reads_require_company_grant_and_effective_assignment --verbosity 2 --noinput` — **1 passed** on disposable PostgreSQL. The exact Phase 1 baseline's full accounts/tenants suite previously passed 199 tests on disposable PostgreSQL; it was not rerun for this frontend-only contract fix.
- Browser evidence from the isolated combined baseline confirms login, password change, `/auth/me/` Company/Branch context, session restore, logout and expiry; no unauthorized Branch-list request was made, no token was stored in browser storage, and no JavaScript page error occurred. This change does not alter those browser paths.
- **P2-12 status: COMPLETE AND VERIFIED for the Branch-context boundary.** Branch filtering in business screens remains intentionally deferred; the Phase 2 final acceptance audit is the next task.

## Baseline and dependency

- Worktree: `D:/VIRMS/tmp/phase1-consolidated-20261101`
- Branch and base HEAD: `codex/phase1-consolidated`, `cac26195611432b44b2cc594aad5f2f0e208b69a`
- The Phase 1 corrections and Phase 2 frontend are uncommitted and unstaged in this candidate. The pre-existing Phase 1 files remain part of the worktree and were preserved.
- Phase 1 dependency: the current candidate, including its uncommitted corrections, passed the 199-test accounts/tenants regression, fresh PostgreSQL migration replay through `accounts.0012_scope_end_monotonic`, Django checks and schema-drift check. Details are in [the Phase 1 report](phase1-execution-progress.md).
- `D:/VIRMS` staging and `D:/VIRMS/tmp/reviewed-backend-baseline` were not modified. No remote fetch was used to make a remote-state claim.

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

README, the current data/API/compatibility maps, this report and the Phase 2 plan now describe the verified candidate and its explicit limits. `docs-final-v2/` was not changed because business rules did not change. Referenced `architecture/05-SYSTEM-STRUCTURE-MAP.md` and `planning/V2-DEVELOPMENT-ROADMAP.md` do not exist in this worktree and were not created from stale plan references.

Final Git state remains dirty and unstaged; all Phase 1 and Phase 2 candidate work is preserved. No commit, push, merge, staging integration, deployment or Phase 3 work was performed.
