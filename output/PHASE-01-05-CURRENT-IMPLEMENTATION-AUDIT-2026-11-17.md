# VIRMS Phase 1–5 — നിലവിലെ ഫീച്ചർ ഓഡിറ്റ്

**തീയതി:** 2026-11-17
**പരിശോധിച്ച worktree:** D:/VIRMS/tmp/phase5-investment-foundation-20261107
**Branch / commit:** codex/phase5-investment-foundation / 26e509a1e80ca43a6ae360863b2eeddb24a06e0c
**Local remote-tracking ref:** origin/codex/audit ഇതേ commit-ലാണ്.
**പരിധി:** Phase 1–5 source/docs; Phase 5 API/UI; നിലവിലുള്ള CI/test രേഖകൾ; 2026-11-17-ലെ local database migration rehearsal, migration, readiness/API browser smoke.

## വിധി

ഈ turn-ൽ ശേഷിച്ച രണ്ട് B-തലത്തിലുള്ള തടസ്സങ്ങളും പരിഹരിച്ചു:

- **F-01:** ഉപയോക്താവ് Option 1 തിരഞ്ഞെടുത്തു. Q100 Investor calculation refresh Phase 8-ലേക്ക് ഔദ്യോഗികമായി മാറ്റി. Phase 5 Sale correction, Buyer refund, Accounting source event എന്നിവ തുടരും; Investor Profit കണക്കാക്കലോ പണമടയ്ക്കലോ Phase 5-ൽ ഉണ്ടാകില്ല. Canonical V2 രേഖകളും Phase 5 architecture-വും append-only decision ആയി പുതുക്കി.
- **F-02:** virms_local_8002-ൽ Phase 5 migrations ഇല്ലാത്തതിനാൽ readiness 503 ആയിരുന്നു. Backup എടുത്ത് പരിശോധിച്ചു; backup-ന്റെ പകർപ്പിൽ migration rehearsal നടത്തി; തുടർന്ന് അതേ Phase 5 migrations local DB-യിൽ പ്രയോഗിച്ചു. Readiness 200 ആയി, Investor Fund API view browser-ൽ load ചെയ്തു.

**ഈ audit-ൽ A-തലത്തിലുള്ള data-loss, security, അല്ലെങ്കിൽ duplicate-money defect സ്ഥിരീകരിച്ചില്ല.** Phase 5 production-ൽ verified ആണെന്ന് ഇതിൽ പറയുന്നില്ല. README publication checkpoint-നുള്ള C findingയും bundle-size advisoryയും തുറന്നുതന്നെയാണ്.

## കണ്ടെത്തലുകൾ

| ID | Severity | നില | സംഗ്രഹം |
|---|---|---|---|
| F-01 | B | **പരിഹരിച്ചു** | Q100-ന്റെ Phase 5/Phase 8 പരിധി Option 1 പ്രകാരം രേഖപ്പെടുത്തി |
| F-02 | B | **പരിഹരിച്ചു — local only** | Persistent local DB migrations, readiness, Investor Fund API view സ്ഥിരീകരിച്ചു |
| F-03 | C | തുറന്നിരിക്കുന്നു | README-യിലെ publication checkpoint പഴയതാണ് |
| F-04 | D | അറിയിപ്പ് | Vite main-chunk size advisory തുടരുന്നു |

### F-01 — Q100 Investor calculation refresh timing

Q100-ന്റെ പഴയ വാചകം Phase 5 Sale correction/refund കഴിഞ്ഞ് Investor calculation refresh ആവശ്യപ്പെട്ടു. Phase 5 architecture Investor Profit calculation-നെ അടുത്ത ഘട്ടത്തിലേക്ക് മാറ്റിയിരുന്നു. Phase 5 source model-ൽ Investor agreement ശതമാനത്തിന്റെ effective snapshot ഇല്ല; UI profit calculation refresh നടക്കുന്നില്ലെന്ന് കാണിച്ചിരുന്നു.

**തീരുമാനം:** ഉപയോക്താവ് Option 1 തിരഞ്ഞെടുത്തതിനാൽ Q100 refresh Phase 8-ലേക്ക് മാറ്റി. Phase 5-ൽ Sale correction, Buyer refund, അവയുമായി ബന്ധപ്പെട്ട യഥാർത്ഥ Accounting movement എന്നിവ ഇപ്പോഴുള്ള module gate-ുകളും typed source link-ുകളും അനുസരിച്ച് തുടരും. Phase 5 Investor Profit കണക്കാക്കുകയോ പണമടയ്ക്കുകയോ settlement നടത്തുകയോ ചെയ്യില്ല. Q98/Q99 source/cash നിയമങ്ങളും Q133–Q134 manual-review നിയമവും മാറ്റമില്ലാതെ തുടരും.

ഈ തീരുമാനം [business rules](../docs-final-v2/01-business-rules.md), [Vehicle/Investor workflow](../docs-final-v2/05-vehicle-investor-finance-workflow.md), [Phase 5 architecture](../architecture/phase-05-investment-vehicle-running-capital/PHASE-05-INVESTMENT-VEHICLE-RUNNING-CAPITAL-ARCHITECTURE.md) എന്നിവയിൽ append-only ആയി ചേർത്തു. Phase 5 UI-യിലെ profit calculation refresh നടക്കുന്നില്ലെന്ന സന്ദേശം ഈ scope-നോട് ശരിയായി പൊരുത്തപ്പെടുന്നു.

### F-02 — Local database schema/readiness

**മുൻ നിരീക്ഷണം:** Django server Phase 5 worktree-ൽ നിന്ന് 127.0.0.1:8001-ൽ പ്രവർത്തിച്ചു. virms_local_8002 PostgreSQL 15 database-ുമായി ബന്ധം സ്ഥാപിക്കാനായി; health/live 200 ആയിരുന്നു, health/ready 503. Read-only migration plan-ൽ Vehicle, Investment, Accounting Phase 5 migrations pending ആയിരുന്നു. Login credential തെറ്റാണെന്ന് തെളിവില്ല.

**സംരക്ഷണ നടപടി:** persistent local DB-യുടെ custom-format backup repository-യ്ക്ക് പുറത്തു സൃഷ്ടിച്ചു:

- സ്ഥലം: C:/Users/Admin/AppData/Local/VIRMS/backups/virms_local_8002_pre_phase5_20261117_153842.dump
- SHA-256: 596D8E1CA5A5EC820BB41B01CB4FAAF12BA3F0DBE9C0AF55F83B77DFFCA53E03
- PostgreSQL 15 pg_restore --list backup വായിക്കാനാകുമെന്ന് സ്ഥിരീകരിച്ചു.

Backup-നെ virms-phase5-disposable-20261117 disposable container-ിലെ വേറിട്ട rehearsal database-ലേക്ക് restore ചെയ്തു. തുടർന്ന് migration ആദ്യം ആ disposable DB-ൽ പരിശോധിച്ചു. Restore-ിന് മുമ്പും ശേഷവും Accounts user, Tenant, Branch എണ്ണം 3/1/1 ആയിരുന്നു. migrate, check, makemigrations --check --dry-run വിജയിച്ചു; migration drift കണ്ടെത്തിയില്ല.

ശേഷം Phase 5 migrations persistent local virms_local_8002 database-ൽ മാത്രം പ്രയോഗിച്ചു. python manage.py check പിഴവില്ലാതെ വിജയിച്ചു; python manage.py migrate --check-ൽ pending migration ഇല്ലായിരുന്നു. പരിശോധിച്ച പട്ടികകളിലെ എണ്ണം: Accounts user 3, Tenant 1, Branch 1, Fund Credit 0, Vehicle Purchase 0, Accounting Event 0. നിലവിലെ account/scope data നിലനിർത്തി; പുതിയ financial record ഒന്നും സൃഷ്ടിച്ചില്ല.

**Runtime smoke:** health/live, health/ready രണ്ടും HTTP 200 നൽകി. Local browser-ലെ Investor Fund view Backend API വഴി തുറന്ന് ശൂന്യമായ record നില ശരിയായി കാണിച്ചു; Investor, Vehicle Management, Accounting modules OFF ആയിരുന്നു. Financial write ഉണ്ടായില്ല. പുതുതായി load ചെയ്ത tab-ൽ service unavailable പിശക് ഉണ്ടായില്ല; browser console error/warning query ശൂന്യമായിരുന്നു.

ഈ പരിശോധന യഥാർത്ഥ user password/login credential സ്ഥിരീകരിച്ചിട്ടില്ല. Browser-ൽ ഇതിനകം ഉണ്ടായിരുന്ന signed-in test account ഉപയോഗിച്ച് API view മാത്രം വായിച്ചു.

### F-03 — README publication checkpoint

README-യിലെ publication commit വിവരം നിലവിലെ local branch/ref-ുമായി പൊരുത്തപ്പെടുന്നില്ല. ഇത് B-തലത്തിലുള്ള runtime അല്ലെങ്കിൽ data-integrity blocker അല്ലാത്തതിനാൽ ഈ പരിഹാരത്തിൽ മാറ്റിയിട്ടില്ല. ഈ turn-ൽ remote GitHub ref പരിശോധിക്കുകയോ push ചെയ്യുകയോ ചെയ്തിട്ടില്ല.

### F-04 — Bundle advisory

മുൻ build രേഖയിൽ Vite main chunk 614.29 kB എന്ന് രേഖപ്പെടുത്തി; 500 kB advisory limit കടന്നിരുന്നു. ഇത് build failure അല്ല, ഈ runtime തകരാറിന്റെ കാരണവുമല്ല. പിന്നീട് performance ജോലിയിൽ പരിശോധിക്കാം.

## പരിശോധിച്ച Phase 5 പ്രവർത്തനങ്ങൾ

Repository source-ലും മുമ്പ് രേഖപ്പെടുത്തിയ test/CI തെളിവിലും താഴെപ്പറയുന്ന പ്രവർത്തനങ്ങൾ ഉൾപ്പെടുന്നു:

- Investor profile, Branch-tagged Fund credit, Fund use/return, attribution correction.
- Vehicle identity/Branch movement, Purchase, seller payable/installment/refund/correction.
- Stock Vehicle direct expense, partial payable/payment, refund/correction.
- Sale, Buyer Receipt/refund, Sale-price correction.
- Accounting typed source link, Running Capital allocation, role/module gate, transaction/idempotency.
- React Phase 5 workspace-ന്റെ backend API ബന്ധിപ്പിക്കൽ.

Phase 5-ൽ Investor Profit/Exit settlement, Garage Job expense, Garage/open-settlement വിവരങ്ങൾ ആവശ്യമായ Vehicle deactivation, offline financial write/sync, demo-data automatic import എന്നിവയില്ല. Vehicle deactivation/registration reuse ആവശ്യമായ authoritative Garage, settlement provider-ുകൾ ലഭിക്കുന്നതുവരെ deferred ആണ്.

## Security, data, old workflow

- Phase 5 migration-ന് മുമ്പ് backup, disposable restore/rehearsal എന്നിവ വിജയിച്ചു.
- Local DB-യിലെ നിലവിലുള്ള user/Tenant/Branch എണ്ണം മാറിയില്ല. Migration local development DB-ൽ മാത്രം നടന്നു; hosted DB-ൽ അല്ല.
- Investor Profit calculation Phase 8 വരെ മാറ്റിയതിനാൽ Phase 5-ൽ പുതിയ money transfer അല്ലെങ്കിൽ Profit posting automation ചേർത്തിട്ടില്ല.
- Staging/production, hosted role grants, deployment, hosted backup/restore: **UNVERIFIED**.

## Test/CI evidence

**ഈ turn-ൽ നടത്തിയ പരിശോധനകൾ**

| പരിശോധന | ഫലം | തെളിയിക്കുന്ന പരിധി |
|---|---|---|
| python manage.py migrate --plan | Phase 5 pending graph പരിശോധിച്ചു | Read-only plan |
| Fresh backup + PostgreSQL 15 pg_restore --list | വിജയിച്ചു | Backup വായിക്കാനാകും |
| Backup clone restore-ന് ശേഷം disposable DB migrate | വിജയിച്ചു | Existing-schema rehearsal |
| Disposable clone rollback to accounting.0003_relation_integrity, then reapply | വിജയിച്ചു; 3/1/1 account/scope counts നിലനിർത്തി | Phase 5 financial/Vehicle rows ശൂന്യമായിരുന്നു; populated-history rollback പരിശോധിച്ചിട്ടില്ല |
| Disposable DB python manage.py check | പിഴവില്ല | Django system check |
| Disposable DB makemigrations --check --dry-run | No changes detected | Model/migration drift കണ്ടെത്തിയില്ല |
| Local virms_local_8002 migrate | Phase 5 migrations വിജയിച്ചു | ഈ local DB മാത്രം |
| Local python manage.py check, migrate --check | വിജയിച്ചു; pending migration ഇല്ല | Local runtime schema |
| health/live, health/ready | രണ്ടും HTTP 200 | Liveness/readiness |
| Browser Investor Fund API smoke | Backend API view load ചെയ്തു; empty state ശരി; console error/warning ഇല്ല | Read-only browser/API |

ഈ turn-ൽ backend, React full test suites വീണ്ടും പ്രവർത്തിപ്പിച്ചിട്ടില്ല. മുമ്പത്തെ GitHub Actions run 44049709283 commit 26e509a1-ൽ വിജയിച്ചതായി രേഖപ്പെടുത്തിയിട്ടുണ്ട്, പക്ഷേ അത് ഈ turn-ലെ rerun അല്ല. പഴയ disposable test തെളിവിനെ staging/production തെളിവായി കണക്കാക്കാനാവില്ല.

## Git / ഫയൽ മാറ്റങ്ങളുടെ പരിധി

- Branch, HEAD, local origin/codex/audit reference: 26e509a1e80ca43a6ae360863b2eeddb24a06e0c.
- apps/vehicles/tests/test_concurrency.py മുമ്പേ modified ആയിരുന്നു; ഈ audit അതിൽ മാറ്റം വരുത്തിയില്ല.
- ഈ turn-ൽ Phase 5 architecture, രണ്ട് canonical V2 decision രേഖകൾ, execution progress രേഖ, audit report എന്നിവ പുതുക്കി.
- Application source, test, migration ഫയലുകൾ മാറ്റിയില്ല. Local DB migration Git source മാറ്റമല്ല.
- Commit, push, merge, deploy നടത്തിയില്ല.

## അന്തിമ വിലയിരുത്തൽ

- **B blockers:** F-01, F-02 പരിഹരിച്ചു. Phase 5 scope Option 1-നോട് പൊരുത്തപ്പെടുന്നു; local database readiness പ്രവർത്തിക്കുന്നു.
- **A findings:** ഈ audit-ൽ സ്ഥിരീകരിച്ചില്ല.
- **Phase 5 പൂർത്തിയായോ:** നേരത്തെയുള്ള approved Phase 5 core implementation verification നിലനിൽക്കുന്നു. ഈ update Q100 timing Phase 8-ലേക്ക് മാറ്റി, local runtime schema സ്ഥിരീകരിച്ചു. എല്ലാ ഉപയോക്തൃ login-കളും, എല്ലാ browser workflow-കളും, staging/production-വും പുതുതായി പരിശോധിച്ചിട്ടില്ല.
- **മറ്റു തുറന്ന കാര്യങ്ങൾ:** F-03 README publication checkpoint (C); F-04 bundle advisory (D); Garage/deactivation, Investor Profit/settlement deferred scope.
- **Staging/production:** UNVERIFIED.
