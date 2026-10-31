# Phase 1 Execution Report — 2026-10-31

> **Status: PHASE 1 COMPLETE** for the local backend implementation and exit gate (P1-00 through P1-19). This does not mean the product is deployed or ready for production cutover.

## Worktree and Git state

- Project/worktree: `D:/VIRMS/tmp/reviewed-backend-baseline`
- Branch: `codex/reviewed-backend-baseline`
- HEAD at final audit: `9a7dcced3126fa1da55a91d398b9aa1426800869`
- Tracking state: one commit ahead of `origin/staging`; no commit or push was made.
- Worktree is dirty with the Phase 1 implementation, migrations, tests, and documentation. Some changes predate the final audit and ownership of unrelated dirty material is not established; it was preserved.
- The separate root checkout `D:/VIRMS` is also dirty and was not modified.
- No merge, deployment, frontend, Phase 2, staging, production, or persistent/shared database operation occurred.

## Verified implementation

| Area | Result |
|---|---|
| Identity and bootstrap | A normal Company account has one backend-generated User UUID and one Company. The same person in another Company uses a separate account. Login ID and email remain globally unique; login has no Company selector. Platform technical accounts do not receive implicit Company business authority. |
| P1-01–10 foundation | Supported Django/DRF runtime and dependency locks; audit and session epoch/lease controls; Company membership, scoped grants, Branch assignments and default-deny policy; private password change with atomic audit/session guarantees. |
| P1-11 provisioning | Provisioning authorizes against Company-scoped policy and atomically creates the independent account, membership, and scoped grant. Global business roles alone do not authorize it. |
| P1-12 lifecycle | Reset/status/revoke operate on the exact User UUID, resolve its one Company, and require the applicable scoped policy. Legacy global business roles alone cannot mutate another account. Temporary credentials, auth-epoch/session invalidation, and actor/subject/scope audit behavior are covered. |
| P1-13 login admission | Login attempts use bounded, shared PostgreSQL-backed admission with atomic behavior under concurrent processes. |
| P1-14 scoped reads | Company and Branch reads require effective membership/grants/assignments, return bounded pages, and hide or deny out-of-scope targets. |
| P1-15 Django Admin | Admin routes use scoped command adapters. Generic edits cannot bypass credential, role, membership, Company, or Branch safeguards. Safe password and temporary-credential flows are covered. |
| P1-16 HTTP boundary | Request IDs, safe correlated errors, and liveness/readiness probes are implemented and tested. |
| P1-17 migration/cutover rehearsal | Canonical Login ID and role-mapping operations require explicit reviewed mappings, authorization and operator re-authentication; replay is deterministic and idempotent. Migration locks/preflight prevent ambiguous identity cutover. A separate disposable PostgreSQL backup/restore rehearsal produced an exact fixture snapshot match. No live-data cutover was attempted. |
| P1-18 documentation | README setup/bootstrap instructions and architecture maps describe the verified backend flow and explicit deployment/data boundaries. Frozen `/docs-final-v2/` documents were not edited in this finalization. |
| P1-19 final audit | Full accounts/tenants regression, fresh migrations, schema-drift, lint, migration-plan, restore, read-query, and security review evidence is recorded below. |

## Data, API, and authorization flow

Login ID/password -> CSRF-protected Django session -> locked active User/auth-epoch check -> bounded session lease -> authorized request. Mutations pass through policy and command/service layers, use a transaction and stable locks, write scoped audit evidence, and affect only the identified account/Company. Password changes/resets rotate the epoch and invalidate required old sessions.

Current account API includes `POST /api/v1/auth/accounts/provision/`, UUID-targeted reset/status/revoke endpoints, session/password endpoints, and `GET /api/v1/auth/me/`. Tenant-backed Company and Branch list/detail reads are paginated and scope-filtered. Django Admin uses the same policy/service boundary. `/health/live/` and `/health/ready/` are operational probes. No observed production request trace was available to classify a current request as redundant; no request was removed on request-count grounds.

One normal business User UUID cannot span Companies. Company membership/grants and Branch assignments are the authorization source; old global business roles do not grant Company lifecycle authority. Django `is_staff`/`is_superuser` does not silently grant ordinary Company business authority. Platform technical/break-glass actions remain explicit.

## Database and migration boundary

Migrations after the original app foundations add audit/session controls, scoped grants, Branch scope, one-Company account enforcement, and canonical Login ID integrity. The PostgreSQL guard rejects a second Company for an ordinary account, including direct SQL. Canonicalization preflight takes a table lock through trigger installation; ambiguous/colliding historical identities fail closed. Mapping does not merge or auto-split accounts and preserves UUID/history where the reviewed mapping allows it.

The final full run began with an empty disposable PostgreSQL 15.19 database and applied all migrations. A separate restore rehearsal restored a fixture containing a User, Company, membership and grant; its source/restore fixture snapshots matched exactly. These checks do not establish what is in any existing database. Existing/staging/production rows, credentials, database privileges, backup policies, and live cutover state remain unverified.

## Validation actually run

- Final disposable run: `D:/VIRMS/tmp/phase1-clean-runtime/Scripts/python.exe D:/VIRMS/output/phase1-execution-2026-10-31/run_disposable_checks_selectable.py p1-19-final-full-regression`
  - Verified an empty `virms_phase1_isolated` database on PostgreSQL 15.19, loopback-only in a `--tmpfs`, `--rm` Docker container.
  - Django `check`: passed; fresh full migration replay: passed.
  - `apps.accounts` + `apps.tenants`: **129 tests passed** in 538.412 seconds.
  - `makemigrations --check --dry-run`: no changes detected.
  - Disposable container stopped and removed. Evidence: `D:/VIRMS/output/phase1-execution-2026-10-31/p1-19-final-full-regression.json`.
- Formatting/static checks: Black semantic check over 76 application Python files and the new migration: clean; `isort --check-only apps core`: passed; `flake8 apps core`: passed; `git diff --check`: clean. Git emitted only line-ending normalization warnings for existing working-copy files.
- Scoped-read audit on disposable PostgreSQL: Company list held at 6 queries and Branch list at 8 queries from 1 to 25 rows; response was limited to 20 rows. PostgreSQL EXPLAIN compiled both selectors. This is a bounded regression check, not a production-scale load test. Evidence: `p1-19-scoped-read-metrics.json`.
- Migration-plan probe: fresh plan/apply/post-plan succeeded; post-plan had no pending operations. `check --deploy` exited successfully with one informational `security.W021` warning: `SECURE_HSTS_PRELOAD` is not enabled. Configure it for a public deployment when the deployment domain/security policy is established. Evidence: `p1-19-migration-plan.json`.
- Restore rehearsal: PostgreSQL 15.19 disposable source/restore databases; restore exit 0 and exact fixture snapshot equality. Evidence: `p1-17-restore-rehearsal.json`.
- Focused lifecycle, provisioning, concurrency, Admin bypass, mapping, migration-race, stale-session, HTTP-boundary, and cross-Company isolation tests also ran as part of the final 129-test suite; earlier focused runs are recorded in the same output directory.

## Risks and release boundary

- **A — Must fix now:** No unresolved Phase 1 implementation defect was found in the final local audit.
- **B — Before any live cutover:** Inspect a protected backup and real database migration ledger/data. The migration deliberately refuses multi-Company business accounts or canonical Login ID collisions; a reviewed mapping/decision is needed if preflight finds them. No records are auto-split.
- **B — Before production:** Configure least-privilege database roles, operational session-lease cleanup scheduling, public-domain security settings including HSTS preload as appropriate, and backup/restore operations in the target environment. These were not provisioned here.
- **Informational:** The final suite tests `apps.accounts` and `apps.tenants`; it is the Phase 1 backend regression suite, not proof of frontend integration, external consumers, production behavior, or the entire product.

No finance/product modules, frontend, Phase 2, staging/production database changes, deployment, commit, or push are included in this Phase 1 completion claim.
