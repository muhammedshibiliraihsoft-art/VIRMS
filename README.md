# VIRMS

Vehicle Investment, Modification & Resale Management System.

## Authority and current state

`/docs-final-v2/` is the current approved/target business and architecture direction; items explicitly marked `BUSINESS DECISION REQUIRED` remain unresolved. Current source code describes only what is implemented. `/docs-final/` and `/docs-legacy/` are historical/superseded. The four living maps under `/architecture/01`–`04` distinguish implemented state, V2 target, historical material and unresolved decisions. `/system-design/` and older architecture plans are V1-derived historical proposals unless explicitly reconciled with V2.

This checkout contains a **backend foundation only**. Investor, Vehicle, finance, media workflows, and the React frontend are not implemented. Starter demonstration behavior has been removed. Do not treat this foundation as a production release.

## Local backend setup

Use Python 3.12 and PostgreSQL. Copy `.env.example` to `.env`, set private local values, and never commit `.env`. `DATABASE_URL` may replace the individual `DB_*` settings. Install `requirements-dev.txt` in a private environment. Django does not create or migrate a database on startup.

Before applying migrations, verify the target is an isolated local/test database and inspect `python manage.py migrate --plan`. Then run `python manage.py migrate` explicitly. Existing starter migrations were replaced by foundation migrations; do not apply them to a database that has already run the old starter migrations without a separate reviewed migration path.

Run `python manage.py check` and `python manage.py test apps.accounts apps.tenants`. Start locally with `python manage.py runserver 127.0.0.1:8001`. The optional devcontainer requires private `VIRMS_LOCAL_DB_PASSWORD` and `VIRMS_LOCAL_SECRET_KEY` environment values and performs **no automatic migrations**.

## API foundation

Backend-controlled Django sessions use HttpOnly cookies and CSRF protection. Fetch `/api/v1/auth/csrf/` before unsafe browser requests. Login is by system-managed Login ID and password. Provisioned accounts must change the temporary password before normal API access. Account provisioning is restricted by current role and Tenant membership. Tenant API reads are membership-scoped. No public signup or generic account/Tenant CRUD endpoint exists.

Local file storage is confined to `.local-media/`. Non-local environments require private S3-compatible object storage configuration for the approved Cloudflare R2 boundary. No Vehicle image workflow is implemented yet.

The Dockerfile is optional packaging. It starts Gunicorn without applying migrations. Render staging configuration and production hosting resources are not created here.
