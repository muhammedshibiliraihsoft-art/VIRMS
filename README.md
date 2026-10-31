# VIRMS

Vehicle Investment, Modification & Resale Management System.

## Authority and current state

`/docs-final-v2/` is the current approved/target business and architecture direction; items explicitly marked `BUSINESS DECISION REQUIRED` remain unresolved. Current source code describes only what is implemented. `/docs-final/` and `/docs-legacy/` are historical/superseded. The four living maps under `/architecture/01`–`04` distinguish implemented state, V2 target, historical material and unresolved decisions. `/system-design/` and older architecture plans are V1-derived historical proposals unless explicitly reconciled with V2.

This checkout contains the completed **Phase 1 backend foundation** for accounts, Company/Branch scope, authentication, authorization, Django Admin adapters, and migration/cutover tooling. Investor, Vehicle, finance, media workflows, and the React frontend are not implemented. Do not treat Phase 1 completion as a production release.

## Local backend setup

Use Python 3.12 and PostgreSQL. Copy `.env.example` to `.env`, set private local values, and never commit `.env`. `DATABASE_URL` may replace the individual `DB_*` settings. Install `requirements-dev.txt` in a private environment. Django does not create or migrate a database on startup.

Before applying migrations, verify the target is an isolated local/test database and inspect `python manage.py migrate --plan`. Then run `python manage.py migrate` explicitly. Existing starter migrations were replaced by foundation migrations; do not apply them to a database that has already run the old starter migrations without a separate reviewed migration path.

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
