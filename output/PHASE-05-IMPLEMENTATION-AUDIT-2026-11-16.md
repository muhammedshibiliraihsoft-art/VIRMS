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
