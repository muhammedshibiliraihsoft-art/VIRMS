# VIRMS

Vehicle Investment, Modification & Resale Management System.

## Authority and current state

`/docs-final-v2/` is the current approved/target business and architecture direction; items explicitly marked `BUSINESS DECISION REQUIRED` remain unresolved. Current source code describes only what is implemented. `/docs-final/` and `/docs-legacy/` are historical/superseded. The four living maps under `/architecture/01`–`04` distinguish implemented state, V2 target, historical material and unresolved decisions. `/system-design/` and older architecture plans are V1-derived historical proposals unless explicitly reconciled with V2.

Current branch snapshot (verified 2026-11-03): codex/audit and origin/codex/audit match at 73797b16aa35db776b5601fe1483c2be8de6c100. That committed baseline includes the accepted Phase 1 and Phase 2 foundations and the approved Phase 3 Company module-state foundation. Phase 1 passed 210/210 account/tenant tests on disposable PostgreSQL; Phase 2 passed 74/74 React tests, configured lint/build, and isolated browser acceptance. Phase 3 passed 232/232 Django account/tenant tests on disposable PostgreSQL 15 and 89/89 React tests; lint, build, system checks, and migration checks passed. Fresh schema apply, empty-state reverse/reapply, and populated-history reverse protection were verified. The current local worktree additionally contains the Phase 4 Company Accounting Foundation implementation, React Accounting API integration, tests, and documentation; those changes are uncommitted and are not present at the current HEAD/origin commit. Phase 4 local verification is recorded in [the execution report](docs/phase4-execution-progress.md). Staging/production runtime, deployed PostgreSQL role permissions, deployment, and hosted CI remain UNVERIFIED. Later Vehicle/Investment/Garage/Sales source-event integrations and final distributable-Profit/period-close behavior are outside this bounded Phase 4 slice; Garage remains Phase 6 after Phases 4 and 5.

## Local backend setup

Use Python 3.12 and PostgreSQL. Copy `.env.example` to `.env`, set private local values, and never commit `.env`. `DATABASE_URL` may replace the individual `DB_*` settings. Install `requirements-dev.txt` in a private environment. Django does not create or migrate a database on startup.

Before applying migrations, verify the target is an isolated local/test database and inspect `python manage.py migrate --plan`. Use the supported `python manage.py migrate` command. For an upgrade whose plan includes `accounts.0007_one_company_account`, pause all legacy account, membership, Company-role and Branch-scope writers before running the identity preflight; keep them paused until migration success is verified. Run `python manage.py check_account_identity_cutover` while writes are paused, then migrate. The automatic `pre_migrate` check rejects ambiguous identities, but it is read-only and does not lock out a concurrent legacy writer. A write racing after that check can let `0007` commit before successor `0010` rejects the upgrade. If migration fails, stop; do not bypass the failure or re-enable writers. Preserve the database, run the UUID preflight, and require reviewed operator remediation before retrying. Existing starter migrations were replaced by foundation migrations; do not apply them to a database that has already run the old starter migrations without a separate reviewed migration path.

Run `python manage.py check`, `python manage.py test apps.accounts apps.tenants`, and `python manage.py makemigrations --check --dry-run`. Start locally with `python manage.py runserver 127.0.0.1:8001`. The optional devcontainer requires private `VIRMS_LOCAL_DB_PASSWORD` and `VIRMS_LOCAL_SECRET_KEY` environment values and performs **no automatic migrations**.

## API foundation

Backend-controlled Django sessions use HttpOnly cookies and CSRF protection. Fetch `/api/v1/auth/csrf/` before unsafe browser requests. Login is by globally unique system-managed Login ID and password; email is also globally unique. There is no Company selector at login. A normal business User account belongs to one Company; the same person in another Company has a separate User UUID, credentials, sessions, roles, permissions, and history. Provisioned accounts must change the temporary password before normal API access.

Provisioning, reset, activate/deactivate, and revoke APIs use the Company-scoped account policy. Company and Branch reads are limited by active membership, CompanyRoleGrant, and effective BranchAssignment. Django Admin uses the corresponding scoped adapters and blocks generic security-field edits. No public signup, JWT, or generic Company mutation endpoint exists. See `docs/phase1-execution-progress.md` for the current verified route and regression inventory.

## Local Platform bootstrap and existing-data cutover

First verify that the database is a disposable/local target and inspect `python manage.py migrate --plan`. Create the explicitly selected Platform superuser interactively, then bootstrap one Company and its Back Office scope:

```powershell
python manage.py createsuperuser
python manage.py bootstrap_platform_admin --user-id "USER_UUID" --company-name "COMPANY_NAME" --company-slug "company-slug" --operation-id "STABLE_OPERATION_UUID"
```

Use `--company-id "COMPANY_UUID"` instead of the name/slug when the Company already exists. The command rechecks the selected operator with a hidden interactive password prompt. It accepts no password argument. Reusing an operation UUID is safe only for the same intent.

For an existing database, do not auto-split multi-Company accounts or guess legacy role mappings. Back up and inspect real migration history and rows first; rehearsal tests prove only disposable fixtures. Migration `accounts.0009_canonical_login_id` deliberately stops before changing data if existing Login IDs need reviewed normalization or collision resolution. If the database is at `accounts.0008_loginattempt_login_retry_after_idx`, prepare a reviewed UUID-based manifest and use `canonicalize_legacy_login_ids --manifest "PATH_TO_REVIEWED_MANIFEST" --actor-user-id "PLATFORM_UUID" --apply --maintenance-confirmed` during a controlled maintenance window. This command is valid only after `accounts.0008` and before `accounts.0009`; it also requires a hidden interactive operator password.

After schema migration, `map_legacy_company_roles --manifest "PATH_TO_REVIEWED_MANIFEST" --actor-user-id "PLATFORM_UUID"` validates the explicit legacy role mapping without writes. Review its output and manifest, stop account/scope writers, then use `--apply --maintenance-confirmed` for the approved cutover. Apply also requires a hidden interactive password. Both mapping commands bind rows by UUID, audit the result, and fail closed on incomplete/conflicting input. Never put passwords or other secrets in command arguments or manifests.

Run these upgrade procedures only against an explicitly isolated local database until an independent deployment review authorizes a real environment. No existing production/staging database state was used to verify this implementation.

Local file storage is confined to `.local-media/`. Non-local environments require private S3-compatible object storage configuration for the approved Cloudflare R2 boundary. No Vehicle image workflow is implemented yet.

The Dockerfile is optional packaging. It starts Gunicorn without applying migrations. Render staging configuration and production hosting resources are not created here.

## Current local Phase checkpoint — 2026-11-07

Phase 4 Company Accounting Foundation is now recorded in local commit 50fb67c1c2256f6a164344344c8c2a12e04407f8 on the isolated Phase 5 base line. Phase 4 verification is documented in docs/phase4-execution-progress.md. This current checkpoint supersedes only the earlier statement above that the Phase 4 implementation remains dirty/uncommitted on this local line. No remote push, staging/production deployment, or hosted database verification is asserted.

Phase 5 is being prepared in a separate worktree. Its code-level design is currently PHASE_5_CODE_ARCHITECTURE_BLOCKED by the unresolved seller-payment timing decision Q39; no Phase 5 application code or database migration has been applied in this worktree at this checkpoint.

## Phase 5 implementation checkpoint — 2026-11-07

This later local checkpoint supersedes only the preceding Phase 5 statement that no Phase 5 code or migration had been applied. On isolated branch `codex/phase5-investment-foundation` at base commit `50fb67c1c2256f6a164344344c8c2a12e04407f8`, the unlocked backend slices now include Company-scoped Investor/interim records, Branch-attributed Fund credits and principal returns, Company-wide Vehicle identity and Branch movement, and typed Accounting links for actual capital Cash/Bank movements. The current work is local and uncommitted.

**Historical implementation snapshot as of 2026-11-07:** Phase 5 was partial and blocked by Q39; deactivation depended on authoritative Garage/Sales/financial lifecycle sources; React Vehicle/Investor/Fund screens still used mock state. The latest architecture/decision checkpoint below supersedes the Q39 blocker statement. No React UI, route, or visual layout had been changed at that earlier snapshot. Investor Profit, Loss offsets, Exit settlement, automatic mock import, and staging/production integration were not implemented or verified at that time. See [Phase 5 execution evidence](docs/phase5-execution-progress.md) and the [Phase 5 code architecture](architecture/phase-05-investment-vehicle-running-capital/PHASE-05-INVESTMENT-VEHICLE-RUNNING-CAPITAL-ARCHITECTURE.md). The disposable PostgreSQL test instance used no persistent mount; `virms-local-8002-pgdata` was not accessed.

## Phase 5 decision and architecture checkpoint — 2026-11-11

Q124–Q132 are now recorded in the canonical V2 rules and Phase 5 architecture. The code-level target contract is `READY_FOR_IMPLEMENTATION`; the application remains **PARTIAL** until the approved Purchase, Vehicle Expense, Sale/Receipt, and React API slices are implemented and verified. This supersedes the prior Q39-only blocker statement above. Vehicle deactivation remains deferred until the Garage/financial dependency records exist. Automatic mock-data import, offline financial writes, and additional automation/approval workflows are outside the current core slice. Q130/Q132 routes excess Vehicle Expense refunds to Company Income only when the Accountant explicitly classifies it: a separate Income event and the same actual Receipt are linked; no second Cash/Bank movement or edit of a prior Income event is allowed.

## Phase 5 local implementation and verification checkpoint — 2026-11-15

The approved Phase 5 core scope is implemented and locally verified in `D:/VIRMS/tmp/phase5-investment-foundation-20261107` on `codex/phase5-investment-foundation`, based on Phase 4 checkpoint `50fb67c1c2256f6a164344344c8c2a12e04407f8`. This checkpoint supersedes the earlier partial/not-started status statements above; those dated sections remain historical. Phase 5 code and documentation remain uncommitted and unpushed.

Verification on disposable PostgreSQL only: full Django `apps` suite 330/330 passed, followed by 2 targeted Vehicle Purchase concurrency/module-OFF race tests; fresh schema migration apply, `manage.py check`, `makemigrations --check --dry-run`, `migrate --check`, and reverse/reapply of `investment.0007_fund_credit_attribution_correction` passed. React suite passed 132/132 across 22 files; configured lint and production build passed. Vite reports a 614.10 kB main-chunk advisory. A local browser workflow created Investors and a Fund Credit, corrected its Investor attribution, then reloaded and confirmed the corrected owner and append-only correction history persisted.

Phase 5 includes Investor/Fund, Vehicle identity/movement, Purchase and seller payable/installments/refunds/corrections, direct Stock Vehicle expenses and settlements/refunds/corrections, Sale and Buyer receipts/refunds/corrections, typed Accounting links, Company Running Capital allocations, and incremental React API integration. Q133–Q134 preserve prior use/return rows and actual cash movements; when those linked rows exist, the UI flags manual review and does not automatically recalculate historical Profit/settlement.

Vehicle deactivation/registration reuse remains deliberately deferred until authoritative Garage Job and Investor settlement providers exist. Investor Profit/Exit settlement, offline financial writes/sync, additional automation, staging/production database/runtime, and deployment remain outside or unverified. `virms-local-8002-pgdata` was not accessed.

## Phase 5 audit-candidate checkpoint — 2026-11-16

This checkpoint supersedes the earlier uncommitted Phase 5 status above. The approved Phase 5 core scope and the four audit fixes are verified locally. The full backend suite passed 343/343; focused Purchase/Expense/Sale tests passed 24/24; React passed 137/137; migration/system checks, configured lint, and build passed. The Phase 5 candidate is locally committed on `codex/phase5-investment-foundation` for audit-branch review. No remote push, merge, or deployment occurred. Review the [Phase 5 execution record](docs/phase5-execution-progress.md), [implementation audit](output/PHASE-05-IMPLEMENTATION-AUDIT-2026-11-16.md), and [code architecture](architecture/phase-05-investment-vehicle-running-capital/PHASE-05-INVESTMENT-VEHICLE-RUNNING-CAPITAL-ARCHITECTURE.md).

## Phase 5 audit branch publication — 2026-11-16

The candidate was pushed as a normal fast-forward to `origin/codex/audit`. GitHub commit comparison verified the remote ref at `2ddbbce26bf43a25313190bf7266996d43243476`; the pushed history includes the Phase 4 base commit and the Phase 5 implementation commit. This publication did not deploy to staging/production. The separate local `codex/audit` worktree still has pre-existing dirty changes and was not modified; reconcile them before further local branch operations.
