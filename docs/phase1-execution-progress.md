# Phase 1 Backend Foundation — Verification Record

## Current local integration status — 2026-11-02

Phase 1 account and Company/Branch foundation is integrated with the Phase 2 React foundation on the local `codex/audit` line. The exact integrated source passed `python manage.py test apps.accounts apps.tenants --verbosity 1 --noinput` — **210/210 passed** on disposable PostgreSQL; fresh test-database replay applied migrations through `accounts.0012_scope_end_monotonic`; `manage.py check` and `makemigrations --check --dry-run` passed. A final regression covers blank Admin login identifiers against source/global admission budgets. No staging, production or shared database was used; the local integration has not been pushed.

The candidate-specific snapshot below records the earlier 199-test verification and is retained as dated evidence, not the final integrated test count.

## Corrections after candidate commit `cac26195`

This section describes the current local, uncommitted Phase 1 correction candidate. The 172-test result in the historical snapshot below predates these corrections.

- Current worktree: `D:/VIRMS/tmp/phase1-consolidated-20261101`, branch `codex/phase1-consolidated`, starting and current HEAD `cac26195611432b44b2cc594aad5f2f0e208b69a`; all correction files below are uncommitted and unstaged.

- `/auth/me` returns a current Investor's own Company context without adding Investor to the Company/Branch business-read policy. Existing role aggregates remain; additive `company_wide_roles` and each Branch's `roles` preserve role-to-scope provenance. Platform Back Office remains a separate top-level role. Clients must not infer a Branch permission from the aggregate role list; backend authorization remains authoritative.
- Accounts migration 0012 adds PostgreSQL guards for membership, Company grant, Branch assignment and legacy role history. Once `effective_until` is finite it may be shortened but not extended or removed, even while still future. Existing supported administrative commands only end scope or create new rows; no writer extending a finite end was found. Legacy history is preserved and new authority requires a new row.
- Platform bootstrap recognizes finite-current as well as open-current role/membership intervals and rejects future or overlapping current scope for review. Failure rolls back newly created Company state.
- Concurrent supported service operations are serialized by existing parent locks. The database has no general exclusion constraint on overlapping finite inserts; approved Phase 1 administrative writes use the service boundary and legacy overlap requires reviewed treatment. The previously accepted 0007 cutover risk still requires pausing legacy writers.
- **Correction gate — PASS:** `python manage.py test apps.accounts apps.tenants --verbosity 1 --noinput` ran 199 tests on disposable PostgreSQL 15.19 in 416.317 seconds: 199 passed, 0 failed, 0 skipped. Django reported no system-check issues.
- **Fresh migration — PASS:** on isolated database `virms_b2` at `127.0.0.1:55443`, `python manage.py migrate --noinput` applied all migrations from an empty schema through `accounts.0012_scope_end_monotonic`; `showmigrations accounts tenants` showed every migration applied and `migrate --plan` reported no pending operations. PostgreSQL reported version 15.19.
- **Upgrade and schema — PASS:** the full suite includes `test_upgrade_preserves_history_and_allows_future_end_now`, which migrates existing history through 0012 and verifies valid future-to-now closure. `python manage.py check` reported no issues; `python manage.py makemigrations --check --dry-run` reported no changes.
- **Static checks — PASS:** isort `--check-only`, Black `--check`, flake8 on all changed Python files, and `git diff --check` passed.
- **Performance — PASS for the tested synthetic fixture:** `/auth/me` remained bounded at 1, 25, 75 and 250 Branches; the 250-Branch case returned 20 summaries with truncation set. The final test run also measured paginated Branch reads at 6 queries for both 1 and 25 rows (20-row page). This is not production-load evidence.
- **Final adversarial re-audit — PASS:** the independent reviewer found no A-level or additional material B-level defect after these changes. The accepted legacy 0007 preflight/write race remains a **C operational cutover risk**: pause every legacy identity, membership, Company-role and Branch-scope writer from before preflight until migration success; on failure preserve the database and do not bypass the guard.
- No staging/production/shared database validation, commit, push, merge or deployment is claimed. A later Phase 2 React foundation candidate is recorded separately in [the Phase 2 report](phase2-execution-progress.md); neither candidate is integrated into staging. Staging was not modified.

## Current correction-gate file set

- Fixes: `apps/tenants/selectors.py`; `apps/accounts/management/commands/bootstrap_platform_admin.py`; `apps/accounts/migrations/0012_scope_end_monotonic.py`.
- Regression coverage: `apps/accounts/tests/test_auth_context_roles.py`, `test_b3_bootstrap_temporal.py`, `test_scope_concurrency.py`, `test_scope_history_monotonic.py`, `apps/accounts/tests/test_a2_identity_preflight.py`, `apps/tenants/tests/test_tenants.py`, and the integrated `apps/accounts/tests/test_final_defects.py`.
- Verified-current-state documentation: `architecture/01-DATA-FLOW.md`, `architecture/02-API-FLOW.md`, `architecture/04-CHANGE-IMPACT-COMPATIBILITY.md`, and this report.

## Prior candidate snapshot (historical)

> **Prior candidate gate: PHASE_2_ENTRY_READY for isolated Phase 2 development.** On 2026-11-01, the owner accepted the A2 migration cutover risk with the required legacy-writer pause described below. This acceptance does not authorize a database cutover, staging integration or deployment. The remaining sections record the earlier snapshot before commit `cac26195`.

## Candidate identity and boundaries

- Repository: D:/VIRMS
- Candidate worktree: D:/VIRMS/tmp/phase1-consolidated-20261101
- Branch: codex/phase1-consolidated
- Exact base and current HEAD: 948df94b8e2cee0fe12075181d9fe602cd708ed9
- The original D:/VIRMS dirty staging worktree and the older dirty tmp/reviewed-backend-baseline worktree were not changed.
- Candidate changes are uncommitted and confined to Phase 1 backend, tests, configuration and verification documentation. No commit, push, merge, staging integration or deployment occurred.

## Verified fixes

- **A1 — PASS:** only failed credentials increment the identifier failure budget; successful API and Django Admin logins clear the exact identifier state. Source/global counters remain bounded all-attempt admission budgets before password hashing. Other identifiers and source/global protection are not cleared by an identifier success.
- **A2 — PASS for the supported migrate path:** manage.py migrate preflights legacy identity before released migration 0007. Successor 0010 validates already-classified Platform identities and fails closed. Platform policy, selectors and Admin scope deny authority to identities with Company business-role/grant history. Existing UUIDs and history are preserved; no account split or automatic identity mapping occurs.
- **A3 — PASS:** ending an active membership, role grant or Branch assignment sets its end to now, including finite future expiry. Future-start rows are rejected; already-ended rows are idempotent; one audit event is emitted for the transition.
- **B1 — PASS:** /auth/me returns at most 20 stably ordered Branch summaries per Company with branches_truncated; paginated Branch reads retain full authorized access and query count stays bounded at 1, 25, 75 and 250 Branches.
- **Additional Phase 1 security fix:** WhiteNoise now runs inside Django SecurityMiddleware. Before the fix, dynamic HTTP redirected while static HTTP returned 200 without nosniff/HSTS. After the fix, static HTTP redirects and forwarded HTTPS static responses return 200 with the configured security headers.
- **Additional Platform identity fix:** Company role-grant commands reject Platform accounts; Django Admin form and autocomplete choices exclude Platform memberships. Provisioning and explicit legacy mapping paths already require Company-kind targets.

## Remaining material finding

- **B — A2 concurrent cutover writer:** the read-only pre_migrate scan is not atomic with released migration 0007. A legacy Company-role write after the scan can let 0007 commit an immutable Platform classification; successor 0010 then rejects the upgrade. A PostgreSQL regression reproduces this sequence: UUID, role history and memberships remain, and the migration stops before 0010; no automatic repair is attempted. Runtime authorization fails closed for the ambiguous identity.
- **Required cutover procedure:** stop every legacy account, membership, Company-role and Branch-scope writer before running check_account_identity_cutover and migrate; keep writers paused until the complete migration succeeds. On failure, do not bypass the error or re-enable writers; preserve the database, review the reported UUIDs and obtain explicit mapping/remediation.
- **Owner disposition:** accepted by the user's “ok” response on 2026-11-01, specifically with all legacy account, membership, Company-role and Branch-scope writers paused before preflight and until migration success. This accepts the documented operational boundary for isolated Phase 2 entry; it does not authorize running a cutover or any staging/production action. No live or shared database was used to make that decision.

## Final adversarial re-audit

- A fresh-context, read-only reviewer re-checked the latest authentication, migration-preflight, Platform grant command/Admin changes and their regression coverage. It found no remaining A-level defect and no additional material B beyond the concurrent A2 cutover-writer risk above. It confirmed the early migration-prefix regression and Platform grant restrictions are covered. This was an internal independent review; no external cloud auditor or second model was invoked.

## Migration and data evidence

- Disposable PostgreSQL 15.19 only. Fresh replay applied all accounts/tenants migrations through 0011; the migration plan then had no pending operations.
- Upgrade tests cover the legacy 0006 prefix, the supported pre-0007 manage.py migrate guard, the concurrent post-scan write above, a valid earlier accounts.0003 prefix before CompanyRoleGrant exists, and preservation of UUID/role/membership history. Released migration 0007 was not edited.
- Model/schema drift check passed: makemigrations --check --dry-run reported no changes.
- A disposable pg_dump -Fc / pg_restore rehearsal produced identical source and restore snapshots for User, Company, membership, role/grant scope and migration ledger.
- Runtime-role privilege test denied direct audit-record UPDATE/DELETE/TRUNCATE for a disposable PostgreSQL role. This does not verify any staging/production role configuration.
- With 50,000 synthetic LoginAttempt rows, the cleanup EXPLAIN changed from sequential scan + external sort (~30.16 ms) to the candidate expiry index scan (~1.91 ms), with no external sort. This is representative synthetic evidence, not a production load test.

## Tests and checks

- Full command: python manage.py test apps.accounts apps.tenants --verbosity 1 --noinput — **172 collected, 172 passed, 0 failed, 0 skipped**, PostgreSQL 15.19, 189.613 seconds. Django system checks reported no issues.
- Final focused group — **4/4 passed**: valid earlier migration prefix, A2 concurrent writer failure/data preservation, Platform role-grant Admin choices, and direct Platform grant denial.
- Production middleware ordering regression — **1/1 passed**. Additional focused A1/A2/A3/B1, login-admission, migration-upgrade and runtime-role tests also passed; their cases are included in the full suite.
- manage.py check: passed. manage.py migrate --plan: no pending operations. manage.py makemigrations --check --dry-run: no changes detected.
- isort --check-only, flake8, Black checks on changed Python files, and git diff --check: passed.
- manage.py check --deploy: exit 0 with informational security.W021 because HSTS preload is not enabled. Domain and deployment policy remain unset; this is not configured speculatively.
- A fresh Dockerfile build could not fetch packages in the isolated no-network build. The local cached runtime image has the same requirements/lock hashes and a recorded successful pinned pip-install layer; pip check passed. An offline image containing the exact candidate source completed collectstatic, ran as UID 999 (virms), passed manage.py check, served /health/live/ and hashed Admin CSS, and verified HTTP redirect plus HTTPS nosniff/HSTS behavior. No external registry was accessed.

## Documentation and release scope

- README migration guidance and this candidate report describe the required identity cutover writer pause and current acceptance status. /docs-final-v2/ canonical target documents were not changed.
- At this Phase 1 snapshot, no frontend, finance, Vehicles, Garage, Sales, Collections, Accounting, dashboard or custom Back Office implementation was included. The subsequent React authentication/context integration is documented separately in `docs/phase2-execution-progress.md`.
- No staging/production/shared database, push, merge, commit or deployment was touched.
