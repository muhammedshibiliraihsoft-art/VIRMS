# VIRMS Phase 5 — നടപ്പാക്കിയ ഭാഗത്തിന്റെ പരിശോധന

2026-11-16 · `codex/phase5-investment-foundation` · Phase 4 base `50fb67c1` · isolated local worktree

## നിലവിലെ വിധി

**ഈ audit-ൽ കണ്ടെത്തിയ നാല് code പ്രശ്നങ്ങളും local worktree-ൽ തിരുത്തി, disposable PostgreSQL-ൽ പരിശോധിച്ചു.** ഇത് Phase 5 മുഴുവൻ production-ready ആണെന്നോ staging/production പരിശോധിച്ചെന്നോ അർത്ഥമാക്കുന്നില്ല.

| മുൻഗണന | ആദ്യം കണ്ടെത്തിയ പ്രശ്നം | ഇപ്പോഴത്തെ പരിഹാരം | തെളിവ് |
|---|---|---|---|
| A | Purchase ₹10,000-ൽ നിന്ന് ₹9,000 ആയി തിരുത്തിയിട്ടും ₹9,500 seller installment കടന്നുപോയിരുന്നു. | Installment സൃഷ്ടിക്കുന്ന transaction-ൽ നിലവിലെ corrected cost − യഥാർത്ഥ payments + യഥാർത്ഥ refunds കണക്കാക്കി payable പരിശോധിക്കുന്നു. അധിക തുക 409 ആയി നിരസിക്കും; കൃത്യമായ ബാക്കി അനുവദിക്കും. | `test_company_funded_purchase_cost_correction_preserves_history` |
| A | അതേ Vehicle-ന്റെ Expense Investor A-യുടേയും Purchase Investor B-യുടേയും ഫണ്ടിൽ സേവ് ചെയ്യാമായിരുന്നു. | Purchase-ും Expense-ും ഒരേ Vehicle-ന്റെ നിലവിലുള്ള Investor attribution പരിശോധിക്കുന്നു. വ്യത്യസ്ത Investor-ന്റെ Fund allocation 409 `VEHICLE_INVESTOR_MISMATCH` ആയി തടയുന്നു. Vehicle row lock ഉപയോഗിച്ച് ഒരേ സമയം വരുന്ന write-ുകൾ serial ആക്കുന്നു. | `test_same_vehicle_cannot_receive_another_investors_purchase_fund` |
| A | Branch Accountant Vehicle Expense correction വഴി pooled Investor Fund allocation കൂട്ടാമായിരുന്നു. | Expense correction-ൽ Fund allocation വർധിക്കുന്നുവെങ്കിൽ `vehicle.expense.fund` Company-only permission server-ൽ നിർബന്ധിക്കുന്നു. Branch Accountant-ന് Fund allocation കുറയ്ക്കാനും സാധാരണ correction ചെയ്യാനും കഴിയും; pooled Fund വർധന Company-level Accountant മാത്രം ചെയ്യുന്നു. | `test_branch_expense_correction_cannot_increase_pooled_fund_allocation` — യഥാർത്ഥ transaction boundary-കളിൽ 10 Expense API tests പാസായി |
| B | Optional തീയതി ഒഴിവാക്കിയ Sale/payment/refund request retry ചെയ്തപ്പോൾ idempotency body മാറി 409 വരാമായിരുന്നു. | Omitted timestamp idempotency key-ന്റെ canonical body-യിൽ സ്ഥിരമായി `null` ആക്കുന്നു; ആദ്യ write-ൽ മാത്രമാണ് യഥാർത്ഥ തീയതി default ചെയ്യുന്നത്. | Purchase installment/refund, Sale, Buyer receipt/refund retry പരിശോധനകൾ ഒരേ record ID-യും ഒരൊറ്റ cash event-ഉം ഉറപ്പാക്കി |

## പരിശോധന

- `python manage.py test apps --verbosity 1` — **343/343 വിജയിച്ചു**; disposable PostgreSQL 15-ൽ, Django system check ശുദ്ധം. Test run 703.463 സെക്കൻഡ്.
- `python manage.py test apps.vehicles.tests.test_purchase_api apps.vehicles.tests.test_expense_api apps.vehicles.tests.test_sale_api --verbosity 1` — `TransactionTestCase` മാറ്റത്തിന് ശേഷം **24/24 വിജയിച്ചു**.
- Expense API tests-ൽ **10/10** യഥാർത്ഥ API transaction boundary-കളിൽ പാസായി. ഇതിൽ correction കുറയ്ക്കൽ, Branch Accountant വർധന തടയൽ, Company-level Accountant വർധന എന്നിവ ഉൾപ്പെടുന്നു.
- Disposable DB-യിൽ `python manage.py migrate --noinput`, `python manage.py migrate --check`, `python manage.py check`, `python manage.py makemigrations --check --dry-run` — വിജയിച്ചു; migration drift ഇല്ല.
- `npm test -- --run` — **137 tests / 22 files വിജയിച്ചു**.
- `npm run lint` — വിജയിച്ചു.
- `npm run build` — വിജയിച്ചു. Main bundle 614.29 kB; Vite-ന്റെ 500 kB advisory നിലനിൽക്കുന്നു.

## മാറ്റത്തിന്റെ പരിധിയും നിലനിൽക്കുന്ന കാര്യങ്ങളും

- ഈ നാല് പരിഹാരങ്ങൾ service validation, authorization, idempotency canonicalization, regression tests എന്നിവയിലാണ്. പുതിയ database schema/migration ഇല്ല; request/response field contract മാറ്റിയിട്ടില്ല.
- Company/Branch/tenant scope നിലനിർത്തി. Fund increase അധികാരം Company-level Accountant-ന് മാത്രം. Retry പരിശോധനയിൽ ഒരു യഥാർത്ഥ Cash/Bank event മാത്രമാണ് സൃഷ്ടിച്ചതെന്ന് സ്ഥിരീകരിച്ചു.
- Disposable DB `virms-phase5-fix-1116` tmpfs-ൽ മാത്രം. `virms-local-8002-pgdata`, staging, production, deployment, live customer data, hosted grants, backup/restore എന്നിവ **UNVERIFIED** ആണ്.
- Vehicle deactivate/registration reuse, Investor Profit/settlement, Garage Job, offline financial writes/sync എന്നിവ പഴയ scope അനുസരിച്ച് deferred ആണ്; ഈ audit അവയ്ക്ക് പുതിയ behavior ചേർത്തിട്ടില്ല.
- Worktree-ൽ മുൻപ് ഉണ്ടായിരുന്ന uncommitted Phase 5 മാറ്റങ്ങൾ നിലനിർത്തി. Commit/push/deploy ഒന്നും ചെയ്തിട്ടില്ല.

## Post-audit follow-up — 2026-11-17

### കണ്ടെത്തലും പരിഹാരവും

Read-only diff review-ൽ refund excess-നെ നിലവിലുള്ള Company Income event-ിലേക്ക് ചേർക്കാനുള്ള option പുതിയ local change-ൽ വന്നതായി കണ്ടെത്തി. V2 Q123/Q124/Q132 പ്രകാരം നിലവിലുള്ള Income event മാറ്റാതെ സൂക്ഷിക്കണം; Accountant വ്യക്തമായി തിരഞ്ഞെടുത്ത category/കുറിപ്പ് ഉപയോഗിച്ച് പുതിയ Income event സൃഷ്ടിച്ച്, അതേ യഥാർത്ഥ refund receipt അതിനോട് link ചെയ്യണം. അതിനാൽ നിലവിലുള്ള event തിരഞ്ഞെടുക്കുന്ന mode-ും അതിനാവശ്യമായ model/schema മാറ്റം, balance/concurrency code, test എന്നിവയും നീക്കി. API/UI ഇനി പുതിയ Income event മാത്രമേ സൃഷ്ടിക്കൂ. Database migration ആവശ്യമില്ല. Q117 അനുസരിച്ച് മുമ്പ് പണമടച്ചിട്ടില്ലാത്ത നേരിട്ടുള്ള ചെലവിനും യഥാർത്ഥ refund രേഖപ്പെടുത്താനായി UIയിലെ പഴയ തടസ്സവും നീക്കി.

### ഇപ്പോൾ നടത്തിയ പരിശോധന

- Phase 5 React targeted test: **9/9 വിജയിച്ചു**.
- React full suite: **138/138 വിജയിച്ചു, 22 files**.
- Configured `npm run lint`: വിജയിച്ചു.
- `npm run build`: വിജയിച്ചു; 614.29 kB main chunk-നുള്ള Vite advisory നിലനിൽക്കുന്നു.
- `python -m compileall -q apps/vehicles apps/accounting`: വിജയിച്ചു.
- Disposable credentials ഉപയോഗിച്ച `python manage.py check`: വിജയിച്ചു, Django system check-ൽ issue ഇല്ല.
- `makemigrations --check --dry-run`: `No changes detected`; എന്നാൽ configured dummy PostgreSQL-ലേക്ക് connect ചെയ്യാൻ കഴിയാത്തതിനാൽ migration-history consistency പരിശോധിച്ചിട്ടില്ല.
- Django database/API tests, fresh/replay PostgreSQL migrations, post-fix browser/API workflow, remote CI: ഇതുവരെ **UNVERIFIED**. Docker daemon pipe-ലേക്കുള്ള docker ps-ന് permission denied ലഭിക്കുകയും local PostgreSQL listener ഇല്ലാതിരിക്കുകയും ചെയ്തതിനാൽ database പരിശോധന നടത്താൻ കഴിഞ്ഞില്ല. Persistent volume/database-ൽ മാറ്റം വരുത്തിയില്ല.

### Git, CI, അടുത്ത നടപടി

Phase 5 worktree: `codex/phase5-investment-foundation`, HEAD `388ec8bf`; `origin/codex/audit`-യുടെ നിലവിലെ അടിസ്ഥാന commit-നോട് പൊരുത്തപ്പെടുന്നു. ഈ follow-up-ലെ code, test, UI, audit report, disposable PostgreSQL ഉപയോഗിക്കുന്ന GitHub Actions workflow എന്നിവ local-ലാണ്; commit/push/deploy ഇതുവരെ ചെയ്തിട്ടില്ല. `D:/VIRMS`-ലെ `staging`-ഉം വേറിട്ട dirty `codex/audit` worktree-ഉം മാറ്റിയിട്ടില്ല. Docker Engine-ലേക്കുള്ള അനുമതി ഈ പരിശോധനയിലും ലഭിച്ചില്ല; അതിനാൽ പുതിയ local PostgreSQL container സൃഷ്ടിക്കുകയോ DB/API tests നടത്തുകയോ ചെയ്തിട്ടില്ല. അടുത്ത സുരക്ഷിത നടപടി: ഇവ മാത്രം stage ചെയ്ത് diff പരിശോധിക്കുക, local commit സൃഷ്ടിക്കുക, അംഗീകരിച്ച `codex/audit` ലക്ഷ്യത്തിലേക്ക് push ചെയ്യുക, തുടർന്ന് GitHub Actions-ൽ backend/PostgreSQL, React, lint, build ഫലങ്ങൾ സ്ഥിരീകരിക്കുക.

### Final local verification update — 2026-11-17

മുകളിലെ follow-up ഭാഗം ആദ്യം എഴുതിയ സമയത്തെ നിലയാണ് രേഖപ്പെടുത്തുന്നത്. താഴെയുള്ള പുതിയ പരിശോധനാഫലങ്ങൾ അതിലെ `UNVERIFIED` നില പുതുക്കുന്നു.

- Disposable PostgreSQL `virms_phase5_final`-ൽ `python manage.py test apps.accounting.tests apps.vehicles.tests --verbosity 1` പ്രവർത്തിപ്പിച്ച് **97/97 ടെസ്റ്റും വിജയിച്ചു**. Django system check പ്രശ്നങ്ങളൊന്നും കണ്ടെത്തിയില്ല; ടെസ്റ്റ് പൂർത്തിയായപ്പോൾ താൽക്കാലിക test database നീക്കം ചെയ്തു.
- പുതിയ disposable database-ൽ `python manage.py migrate --noinput` വിജയിച്ചു. `vehicles` migration `0008` വരെ തിരിച്ചിറക്കി `0009` വീണ്ടും പ്രയോഗിച്ച് നിലവിലെ നില പരിശോധിച്ചു. `python manage.py makemigrations --check --dry-run` — `No changes detected`.
- `npm test -- --run` — **22 ഫയലുകളിലായി 138 ടെസ്റ്റുകളും വിജയിച്ചു**. `npm run lint` വിജയിച്ചു. `npm run build` വിജയിച്ചു; 614.29 kB main chunk-ിനുള്ള Vite advisory നിലനിൽക്കുന്നു.
- ബ്രൗസറിലെ ലോക്കൽ smoke: Vite `127.0.0.1:5173` ഈ Phase 5 worktree-ൽ നിന്ന് പ്രവർത്തിച്ചു; backend `127.0.0.1:8001` പ്രവർത്തിച്ച് `virms_local_8002` ഡാറ്റാബേസിലേക്ക് കണക്റ്റ് ചെയ്തിരുന്നു. Root dashboard തുറന്നു; Investor Fund Phase 5 സ്ക്രീൻ API mode-ൽ എത്തി, പക്ഷേ “The service is temporarily unavailable” എന്ന് കാണിച്ചു; module നിലകൾ OFF ആയി കാണപ്പെട്ടു. UI-യിലെ പൂജ്യം കണക്കുകൾ യഥാർത്ഥത്തിൽ രേഖകളില്ലെന്ന തെളിവായി കണക്കാക്കരുത്.
- ശരിയായ VIRMS DB-യിൽ 3 `accounts_user` രേഖകളുണ്ടായിരുന്നു. `accounts` migration നില `0012_scope_end_monotonic` വരെയാണ്; നിലവിലെ Phase 5-ലെ `investment`, `vehicles`, `accounting` migrations ബാക്കിയായിരുന്നു. ഈ DB-യിൽ migration നടത്തിയില്ല, login form പൂരിപ്പിച്ചില്ല, ബിസിനസ് രേഖകൾ എഴുതിയില്ല. Browser unavailable സന്ദേശത്തിന്റെ കൃത്യമായ HTTP/exception കാരണം രേഖപ്പെടുത്തിയിട്ടില്ല; schema-version വ്യത്യാസം ഒരു സാധ്യതയാണെങ്കിലും അത് **സ്ഥിരീകരിക്കാത്ത inference** ആണ്. ഈ database-ൽ migration നടത്താൻ backup/authorization വേണം.
- `git diff --check` വിജയിച്ചു. Source change Q132 അനുസരിച്ച് പുതിയ Income record സൃഷ്ടിക്കുന്നു; പഴയ Income target തിരഞ്ഞെടുക്കാനുള്ള വഴിയില്ല, പുതിയ schema migration ഇല്ല.
- `.github/workflows/phase5-verification.yml` GitHub-hosted runner-ിലെ disposable PostgreSQL-ൽ migration-ഉം `apps` test suite-ഉം പ്രവർത്തിപ്പിക്കുന്നതാണ്. GitHub Actions ഇതുവരെ ഓടിയിട്ടില്ല; അതിനാൽ **remote CI UNVERIFIED** ആണ്. ഇനിയും stage, commit, push, deploy ചെയ്തിട്ടില്ല.

`codex/audit`-ലേക്ക് അംഗീകരിച്ച push നടത്തുകയും CI ഫലം ഉറപ്പാക്കുകയും ചെയ്യുന്നതിന് മുമ്പ് workflow, മുഴുവൻ diff, Git ancestry എന്നിവ വീണ്ടും പരിശോധിക്കണം.
