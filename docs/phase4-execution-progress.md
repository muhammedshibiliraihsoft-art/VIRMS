# Phase 4 — Company Accounting Foundation Execution Report

| Field | Verified value |
|---|---|
| Evidence date | 2026-11-03 |
| Status | `PHASE_4_IMPLEMENTATION_COMPLETE_LOCAL` for the bounded Company Accounting Foundation |
| Repository | `D:/VIRMS/tmp/audit-consolidation-20261102` |
| Branch / baseline | `codex/audit`, local HEAD and `origin/codex/audit` at `73797b16aa35db776b5601fe1483c2be8de6c100` before these local Phase 4 changes |
| Git state | Phase 4 implementation and documentation changes are local and uncommitted. No commit, push, merge, or deployment occurred. |

## Delivered scope

- Added the Django Accounting domain with Company-owned accounts and categories, Income, Expense, Receipt, Payment, Opening Balance, Transfer, applications, account movements, correction lineage, and idempotency records.
- Added Company/Branch-scoped DRF resources and backend policy enforcement for the Phase 4 Accounting roles and operations. Financial writes use service-level transactions, persisted module-state revision checks, deterministic row locking where needed, and duplicate-submission protection.
- Added append-only correction/reallocation behavior, fixed-precision amount validation, account/category archival guards, and a read-only Accounting Result derived from committed Accounting Income and Expense.
- Connected the existing React Accounting surfaces to the shared API/query layer. Existing route identities and page composition remain; the Accounting controls/forms were added within the approved surface without a visual redesign.
- Responsive browser checks found a 10px page-level overflow at 320px caused by the shared TopBar's brand text plus utility actions. A narrow-width rule now hides only the redundant wordmark at widths up to 340px; the brand icon and every utility action remain. No page-level overflow remains at 320px after the fix.
- Verified a Company Income create through the local browser/API path returned HTTP 201 and the same record remained visible after browser reload and reopening the register, backed by the disposable local Docker PostgreSQL database.

## Confirmed decision outcomes

- An account with any event or movement history cannot be archived, even if its current derived balance is zero. Archival requires zero balance and no history.
- Module OFF and financial writes serialize through the persisted module-state revision and Company/Tenant lock. A stale write fails closed with a conflict; the service does not silently retry a financial intent.
- When Accounting is OFF, correction/reallocation applies only to eligible pre-OFF root records and targets. Ordinary Receipt/Payment settlement against an eligible pre-OFF obligation is a separate allowed flow.
- Every supported correction form offers both `REVERSE_ONLY` and `REVERSE_AND_REPLACE`. Backend validation selects a permitted outcome based on the actual event and its history; reversal-only cannot erase a distinct real economic/cash movement.

## Verification performed

### Django and database

- `python manage.py test apps.accounting.tests apps.accounts.tests apps.tenants.tests --verbosity 1` — **288/288 passed** on disposable Docker PostgreSQL. This full regression run occurred before the final concurrent-correction race test was added.
- `python manage.py test apps.accounting.tests.test_concurrency --verbosity 1` — **6/6 passed** after adding the concurrent-correction race test. This includes both module-OFF/write orderings, bounded concurrent applications, correction serialization, and archive/history serialization.
- Four focused API boundary tests — **4/4 passed**: OFF timestamp equality fails closed; application reallocation preserves the actual cash movement; OFF reallocation is limited to pre-OFF records; zero-balance account archival succeeds only without history. These tests overlap the broader test runs and must not be added as a separate unique-test count.
- `python manage.py check` — no system issues.
- `python manage.py makemigrations --check --dry-run` — no model/migration drift.
- `python manage.py migrate --plan` — no pending migration operations in the disposable local test database.

### React

- `npm test -- --run` — **19 test files / 101 tests passed** after the responsive TopBar adjustment.
- `npm run lint` — passed for the configured project paths, including `TopBar.tsx`. The changed `CompanyAccountingView.tsx` is outside the configured lint glob; a direct TypeScript parser and React Hooks lint check for that file reported **0 errors / 0 warnings**.
- `npm run build` (`tsc && vite build`) — passed. Vite reported a 611.46 kB main bundle, above its 500 kB advisory threshold; the Accounting async chunk was 48.25 kB.

### Browser and source checks

- Local browser smoke verified Company Income read/create, HTTP 201, and visibility after reload/reopening the register. This is local disposable-DB evidence only.
- Browser responsive checks covered the Accounting tools modal, Income form, and correction form at 1440px, 768px, 390px, and 320px. Dialogs and controls stayed within the viewport. After the TopBar fix, the Company Income page and correction flow had no document-level horizontal overflow at 320px; the ledger's own table remains horizontally scrollable within its designated container.
- The local Accounting tab reported no browser console warnings or errors during the final inspection.
- `git diff --check` reported no whitespace errors in tracked changes; an explicit trailing-whitespace scan reported none in the Phase 4 documentation files, including this untracked report.
- No staging/production database, deployed runtime, PostgreSQL runtime-role grants, GitHub CI run, or production behavior was inspected or verified.

## Scope boundaries and remaining risks

- Future Vehicle, Investment, Garage, and Sales modules do not yet originate their own source events in Accounting. Those vertical integrations remain in their respective roadmap phases; Phase 4 establishes the Accounting persistence/API boundary for them to consume.
- Final consolidated Company Profit source recognition, distributable Profit, period close/carryforward, Investor Profit, Owner Distribution, and unrelated-module OFF/cross-Branch behavior remain outside this bounded phase.
- Staging/production deployment and the deployed PostgreSQL role's privileges remain `UNVERIFIED`.
- The uncommitted Phase 4 work is not present on `origin/codex/audit`; this report does not imply a commit or push.

## No unrelated work

No unrelated dirty work was reset, cleaned, stashed, restored, or discarded. No staging/production database or service was changed. No application behavior outside the confirmed Phase 4 Accounting scope was intentionally modified.

## Phase 4 final audit checkpoint — 2026-11-04

**Local bounded-scope status remains `PHASE_4_IMPLEMENTATION_COMPLETE_LOCAL`.** This checkpoint adds verification after the approved account-archive, module-OFF race, pre-OFF correction, and correction-choice decisions. It does not claim deployment or production readiness.

### Audit fixes and evidence added

- Added reverse guards to Accounting migrations `0001_initial`, `0002_history_and_archive_guards`, and `0003_relation_integrity`. If any Accounting catalogue, event, application, movement, or idempotency row exists, rollback raises `IrreversibleError` before schema/history triggers can be removed or Accounting data dropped. Empty-schema downgrade and reapply remain supported. Forward schema is unchanged.
- Added migration tests for populated rollback rejection without partial rollback, and for empty rollback/reapply.
- Added a PostgreSQL role test using an isolated NOLOGIN role with only `SELECT`/`INSERT` grants; `UPDATE`, `DELETE`, and `TRUNCATE` against append-only event, application, movement, and idempotency history are rejected. This proves the tested role grants in the local disposable test database only; it does not verify any deployed Django runtime role or inherited production role membership.
- Added and ran both Receipt-versus-Accounting-OFF lock orderings. The stale request fails with conflict when OFF wins; a Receipt holding the Company lock commits against the prior enabled revision before OFF can commit. No silent financial retry was introduced.

### Verification run on 2026-11-04

- `python manage.py test apps.accounting.tests apps.accounts.tests apps.tenants.tests --verbosity 1` — **296/296 passed** on the isolated local PostgreSQL 15 test container. Django created and removed its test database. This includes the new migration rollback, role-grant, and concurrency tests.
- `python manage.py check` — no issues.
- `python manage.py makemigrations --check --dry-run` — no model/migration drift.
- Created a uniquely named database inside the isolated audit PostgreSQL container, applied all repository migrations with `python manage.py migrate --noinput`, then ran `python manage.py migrate --check --plan` — all migrations applied; **no planned migration operations**. This database is not the app's existing persistent `devdb`, staging, or production database.
- `npm test -- --run` — **19 test files / 101 tests passed**.
- `npm run lint` — passed for the configured lint paths.
- `npm run build` (`tsc && vite build`) — passed, including TypeScript checking. Vite retains its advisory warning that the main minified bundle is 611.46 kB (over 500 kB); the Accounting async chunk is 48.25 kB.
- `git diff --check` — exit 0. Git emitted line-ending conversion warnings for pre-existing changed files; no whitespace errors were reported.
- Existing browser evidence remains the 2026-11-03 local smoke: Company Income create returned HTTP 201 and remained visible after reload. No frontend source changed in this final audit checkpoint; no new browser session was run on 2026-11-04.

### Final audit limits

- **Verified from repository/local tests:** Phase 4's bounded Company Accounting persistence, API/policy boundary, React Accounting integration, correction history, role and Branch policy tests, module-state ordering, migrations, and related Phase 1–3 account/tenant regressions.
- **UNVERIFIED:** actual staging/production PostgreSQL runtime identity, ownership, inherited role memberships and grants; hosted CI; deployment; live service/database behavior. The local NOLOGIN role test is not a substitute for inspecting deployed grants.
- Vehicle, Investment, Garage, and Sales source-event integration and final consolidated/distributable Profit, period close/carryforward, Investor Profit, and Owner Distribution remain outside this bounded Phase 4 delivery.
- Work remains uncommitted on the local `codex/audit` worktree; no commit, push, merge, or deployment occurred.

## Phase 4 retry-safety follow-up checkpoint — 2026-11-04

- Adversarial frontend review found that `accountingMutation` generated a fresh random key and continued posting when `sessionStorage` could not preserve the pending idempotency key. That could turn an ambiguous network retry into a duplicate financial record.
- Changed the Accounting API client to fail closed before sending a mutation when browser retry storage is unavailable. A focused test first reproduced the unsafe behavior, then verified that unavailable storage sends no request and that a retry after an ambiguous network failure reuses the same key.
- Added React component coverage for Income/Expense, Receipt/Payment, opening balance/transfer, account/category creation, correction choice, API failure behavior, Branch selection, query invalidation, and success handling.
- Re-ran the complete React suite after the API-client change: **20 test files / 113 tests passed**. Configured lint passed. `npm run build` (`tsc && vite build`) passed; the existing 611.46 kB main-bundle advisory remains.
- Re-ran `python manage.py test apps.accounting.tests apps.accounts.tests apps.tenants.tests --verbosity 1` against the verified local Docker PostgreSQL container: **296/296 passed**. `python manage.py check` reported no issues and `makemigrations --check --dry-run` found no drift.
- Applied all migrations to a uniquely named scratch database in the same local Docker container, then ran `python manage.py migrate --check --plan`; all migrations applied and no operations remained. The scratch database was dropped afterward.
- Existing browser reload evidence remains the local Company Income smoke recorded above and in the 2026-11-04 checkpoint. No UI layout, route, visual design, schema, or business rule changed in this follow-up; staging/production and deployed database-role evidence remain `UNVERIFIED`.

## Correction-form coverage follow-up — 2026-11-04

- Expanded component coverage to verify that the shared correction form presents both approved outcomes for every supported event type: Income, Expense, Receipt, Payment, Opening Balance, and Transfer.
- Focused Accounting component tests passed **16/16**. The final React run passed **20 test files / 119 tests**, `npm run lint` passed for configured paths, and `npm run build` (`tsc && vite build`) passed. The 611.46 kB main-bundle advisory remains.
- This follow-up changed test coverage only; backend source and schema were unchanged after the verified **296/296** backend run and scratch migration replay above.

## Post-implementation browser and navigation verification — 2026-11-04

- A fresh browser run used a uniquely named local Docker PostgreSQL scratch database and a synthetic test Accountant. Created Company categories, a named Bank and Cash account, a Branch-tagged Income and Expense, partial and final Receipts/Payments, an opening balance, and an internal transfer through the React UI. The Income stayed visible after browser reload and reopening the register.
- Browser/API evidence: Income `₹1,000.00` less Expense `₹700.00` produced Accounting Result `₹300.00`; actual Receipt/Payment records did not inflate or reduce that recognized result. A Receipt of `₹601.00` against `₹600.00` outstanding and a Payment of `₹501.00` against `₹500.00` outstanding each returned HTTP `409` and remained unsaved. Two valid partial Receipts and two valid partial Payments completed their respective targets.
- Opening balance and transfer appeared as separate events. The paired transfer changed Bank/Cash balances from `₹5,000/₹0` to `₹4,500/₹500`; subsequent receipts/payments updated the correct account balances. Once an account had movement history, the UI disabled Archive and showed “Accounts with any history cannot be archived.”
- Browser verification found the quick-section `Accounting` shortcut was silently rejected by the role route guard even though the backend Accounting summary route existed. Added a narrow route-visibility alias for roles that already have the Company Accounting group. The regression test failed before the guard change, passed afterward (**14/14** focused role-navigation tests), and the browser then opened the backend Accounting Result summary from the quick nav. No layout or route identity changed.
- Re-ran the complete Django regression suite against a dedicated local Docker PostgreSQL test database: **296/296 passed** in 445.5 seconds; Django reported no system issues. The test database was destroyed by Django. The uniquely named browser scratch database was then dropped and verified absent; no `test_virms_p4_e2e_*` database remained. Local Django/Vite servers were stopped and ports 8001/5174 were verified closed.
- Re-ran React tests: **20 files / 119 tests passed**. Configured `npm run lint` passed. `npm run build` (`tsc && vite build`) passed; the main bundle is 611.51 kB (existing 500 kB advisory), and `CompanyAccountingView` is 48.34 kB. TypeScript checking covered the changed route guard and tests; the repository lint configuration does not include `src/data/`.
- The browser captured React “uncontrolled input to controlled” warnings during account/category form creation. Repository tracing identified the cause: `openForm()` omitted initial `kind`, `label`, and `account_type` values. These fields now start as empty strings, and a component regression test verifies both Add account and Add category interactions do not emit that warning. This does not change layout or form meaning. The prior 2026-11-03 “no warnings” inspection remains historical for that earlier session.
- After this fix, the focused Accounting component suite passed **18/18**, and the complete React suite passed **20 files / 121 tests**. Configured lint passed. `npm run build` (`tsc && vite build`) passed; the existing main-bundle advisory remains at 611.51 kB. The already completed backend regression run remains **296/296**; no backend source or schema changed in this frontend-only follow-up.
- Staging/production, deployed database grants, hosted CI, and deployment remain unverified. No commit, push, merge, or deployment occurred.
