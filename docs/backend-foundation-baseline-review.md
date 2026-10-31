# Reviewed backend foundation baseline â€” 2026-10-31

This local preservation baseline is an incomplete foundation, not a production release or Phase1 completion. User authorized source review, limited fixes and local Git save; no push/merge/deployment.

## Changes and validation

- Added outermost Django never_cache to provision/reset API views. Payloads, permissions, routes, ORM models and migration definitions unchanged.
- Removed existing trailing whitespace in setup.cfg (no configuration value change).
- Excluded tmp/ and output/ from Docker build context to avoid packaging nested worktrees and evidence.
- Added a database-free dispatched API regression test: 1 test with two route subcases. It failed for both missing headers before fix and passed after fix. It proves unauthenticated responses carry no-store, not successful DB-backed credential delivery.
- Added no-store assertions to existing successful provision/reset PostgreSQL tests; these were NOT EXECUTED because no verified PostgreSQL target is available. Existing 17 foundation tests likewise not run.
- Django system check executed as part of isolated configuration test run: no issues, 0 silenced; unused DB setup explicitly skipped. No real credentials or .env read.
- Source syntax/targeted credential-signature scan and exact file-copy verification performed for baseline. No real password, private key or token signature detected; this is not an exhaustive secret audit.

## Remaining findings before release

A: Global business roles lack Company-specific grant model. Admin raw forms and API-only first-password gate do not enforce complete V2 scope. Password-change/login versus reset concurrency is incomplete. These require approved Phase1 scoped services, epoch, row locking, Admin adapters and PostgreSQL tests; they were not silently redesigned for preservation.

A before release: Django5.1.4 unsupported. Deliberate supported dependency upgrade remains P1-01, not part of this baseline.

B: Finite future grant intervals differ from target half-open semantics; explicit migration mapping is required before changing effective access. Production Docker collectstatic local settings versus hashed manifest and unconditional forwarded HTTPS-header trust require Phase1 environment verification. Limiter concurrent admission, audit append-only protection and required role lifecycle changes remain Phase1 work.

## Evidence and exclusions

Original local staging HEAD ed114b2667a707034b01bc58211d58aa70013314. Baseline branch based on cached staging95384cdd9fdd548f4b434891ef353147ab2a04d2. Existing source inventory in output/p1-00-baseline-gate-2026-10-31/baseline-manifest.json; pre-edit56-file ZIP snapshot retained locally under output/backend-review-2026-10-31 (not committed).

Capture only selected backend/config/migrations/tests, README/LICENSE and this report. Exclude unrelated historical deletions, frontend demos, generated artifacts, output/, tmp/, handoff, editor files, private environments/credentials/media and DB volumes. Do not restore deleted architecture authority or invent missing03-DEPENDENCIES.md.

## Architecture and next step

No schema/data/tenant permission change performed. Security response headers and Docker build exclusions are the only runtime/packaging changes. Phase1 v1.1 remains target strategy, not implemented truth. After local baseline, verify an isolated PostgreSQL target/ledger and complete P1-00 validation before P1-01. Do not treat a local save as database/test/runtime approval.

Checks completed: flake8 apps core passed; Black --check and isort --check-only on the three changed Python files passed (format check run outside restricted sandbox after sandbox processes stalled). git diff --cached --check verified after setup whitespace correction.
