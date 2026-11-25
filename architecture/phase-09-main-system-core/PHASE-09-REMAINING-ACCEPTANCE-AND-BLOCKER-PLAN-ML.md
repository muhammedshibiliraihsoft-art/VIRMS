# Phase 9 — ശേഷിക്കുന്ന acceptance പരിശോധനയും blocker പരിഹാരവും

തീയതി: 25 നവംബർ 2026. Worktree: `D:\VIRMS\tmp\phase9-baseline-review-d2efd314`; detached HEAD `253b2f091b936fd1772e7805ce7951bf53f1f33a`. നിലവിലുള്ള staged, unstaged, untracked മാറ്റങ്ങൾ സംരക്ഷിക്കുക. പ്രവർത്തനം തുടങ്ങുമ്പോൾ identity, database, runtime വീണ്ടും സ്ഥിരീകരിക്കുക.

## Scope ഉം തെളിവിന്റെ അർത്ഥവും

J02–J09 പൂർത്തിയാക്കാനുള്ള താഴെപ്പറയുന്ന പരിശോധനകളും സ്ഥിരീകരിച്ച defect-ന്റെ ചെറിയ repair-ഉം മാത്രം. **PARTIAL എന്നത് തെളിവ് അപൂർണ്ണമാണ്; സ്വതേ code defect ആണെന്നല്ല.** Test PASS മാത്രം live browser journey PASS അല്ല. Phase 10, പുതിയ finance rules, UI redesign, commit, push, merge, deploy എന്നിവ പുറത്താണ്. UI/card മാറ്റത്തിന് മുൻപ് ഉപയോക്താവിന്റെ മുൻകൂർ അനുമതി ആവശ്യമാണ്. ഓരോ പ്രശ്നവും രേഖപ്പെടുത്തി സ്വതന്ത്രമായ അടുത്ത പരിശോധനയിലേക്ക് പോകുക; ആവർത്തിച്ച full audit നടത്തരുത്.

മുമ്പത്തെ audit റിപ്പോർട്ട്: selected backend tests 21/21 PASS; login, Fund, Vehicle Details, Garage empty state, Accounting UI കണ്ടു; system check, migration dry-run, diff check PASS. ഈ രേഖ എഴുതുമ്പോൾ tests വീണ്ടും ഓടിച്ചിട്ടില്ല. Test evidence date, command, count, database, result audit സമയത്ത് വീണ്ടും പരിശോധിച്ച് മാത്രം acceptance-ന് ഉപയോഗിക്കുക.

## സുരക്ഷിതമായ test setup

- Frontend `127.0.0.1:5174`, backend `127.0.0.1:8001`, disposable PostgreSQL container `virms-p9-closure-20261124`, database `virms_phase9_closure`, port `55441` എന്നിവയുടെ process worktree, DB connection, Company, role എന്നിവ ഉറപ്പാക്കുക. Disposable ആണെന്നത് പേര് മാത്രം നോക്കി തീരുമാനിക്കരുത്.
- നിലവിലെ `p9_acceptance_1125` test login ഉപയോഗിക്കുക; password ഈ രേഖയിൽ സൂക്ഷിക്കരുത്. ആവശ്യമെങ്കിൽ ഉപയോക്താവ് നൽകിയ നിലവിലെ credentials ഉപയോഗിക്കുക. Test transactions disposable DB-ൽ മാത്രം; ഓരോ write-നും test identifier ചേർത്ത് audit രേഖയിൽ സൂക്ഷിക്കുക.
- Backend പരിശോധനയ്ക്ക് Python 3.12, repository pin Django 5.2.18 ഉറപ്പാക്കുക. Test runner സൃഷ്ടിക്കുന്ന database-ന്റെ പേര് ആദ്യം പരിശോധിച്ച് നിലവിലുള്ളത് overwrite ചെയ്യരുത്. ഒരിക്കൽ സൃഷ്ടിച്ച test records അനുമതിയില്ലാതെ നീക്കരുത്.

## Journey അനുസരിച്ചുള്ള കാരണവും നടപടിയും

### J02 — Investor Fund: PARTIAL

**കാരണം:** live credit, allocation, summary കണ്ടു; live partial principal return-ന്റെ persisted history, Accounting movement ഇതുവരെ തെളിയിച്ചിട്ടില്ല. Existing tests credit idempotency, return cap, rollback പരിശോധിക്കുന്നു.

**നടപടി:** disposable Investor-ന് fund credit രേഖപ്പെടുത്തി, purchase allocation-നുശേഷം അനുവദനീയമായ partial principal return ചെയ്യുക. UI reload-നുശേഷം credit, allocation, return, source link, AccountMovement എന്നിവ കണ്ടെത്തി credit/return ഓരോന്നിനും ഒരേ cash effect ഉറപ്പാക്കുക. Summary-യിൽ credits − returned − used − reserve എന്ന നിലവിലുള്ള service semantics-നോട് ലഭ്യമായ തുക താരതമ്യം ചെയ്യുക; പുതിയ formula നിർമിക്കരുത്. Failure ഉണ്ടെങ്കിൽ owning service, permissions, transaction trace ചെയ്ത് മാത്രം fix.

### J03 — Vehicle: PARTIAL

**കാരണം:** P9-TEST-001 Details, ₹700 purchase, ₹100 Investor Fund, ₹600 Running Capital കണ്ടു. Seller installments/refunds, expense correction, Branch move എന്നിവയുടെ മുഴുവൻ live history പരിശോധിച്ചിട്ടില്ല.

**നടപടി:** disposable Vehicle purchase, partial seller payment, direct expense, correction, അനുവദനീയമായ refund, Branch move ഓരോന്നും API/UI വഴി പരിശോധിക്കുക. Reload ചെയ്ത് ഒരേ Vehicle identity, correction version, original source Branch, current cost, ഒരിക്കൽ മാത്രം cash movement എന്നിവ DB-യുമായി താരതമ്യം ചെയ്യുക. Branch permission ഇല്ലെങ്കിൽ `UNVERIFIED`, fabricated data ഒഴിവാക്കുക.

### J04 — Garage: PARTIAL

**കാരണം:** DB-യിൽ live Job ഇല്ല; empty-state, stock-cost, external-job, partial-receipt focused tests തെളിവാണ്; UI മുതൽ persisted flow വരെ തെളിവല്ല.

**നടപടി:** disposable stock Job സൃഷ്ടിച്ച് expense ഒരിക്കൽ മാത്രം Vehicle-ലേക്ക് link ചെയ്യുക; external Customer Job-ൽ charge, partial receipt, cost, correction/refund പരിശോധിക്കുക. Investment OFF-ൽ external flow അനുവദിക്കുന്ന നിലവിലെ policy അനുസരിച്ച് പരിശോധിക്കുക. Saved Job, source link, movement, reload/history പരിശോധിക്കുക; retry duplicate posting ഉണ്ടാക്കരുത്.

### J05 — Sale: PARTIAL

**കാരണം:** disposable DB-യിൽ Sale ഇല്ല. Correction history, concurrent refund cap tests PASS ആയിരുന്നു; live receipt/refund journey തെളിവില്ല.

**നടപടി:** test Vehicle വിറ്റ് partial Buyer receipt രേഖപ്പെടുത്തുക; unpaid receivable Paid ആകുന്നില്ലെന്ന് പരിശോധിക്കുക. Price correction വഴി refund obligation ഉണ്ടാക്കി actual refund രേഖപ്പെടുത്തുക; obligation, paid തുക വേർതിരിച്ച് source links, cash movements, history/reload, same-key retry പരിശോധിക്കുക. Destructive correction വേണ്ട.

### J06 — Accounting: PARTIAL

**കാരണം:** live ₹200 recognized result, ₹60 net cash, event register കണ്ടു; ഓരോ J02–J05 source-ലും നിന്നുള്ള end-to-end trace പൂർത്തിയായിട്ടില്ല.

**നടപടി:** മുകളിലെ test writes-ൽ ഓരോ actual transfer-നും source row → typed AccountingSourceLink → AccountingEvent → AccountMovement പരിശോധിക്കുക. Company/Branch scope, correction/reversal history, inflow/outflow, duplicate movement absence പരിശോധിക്കുക. Recognized result-നെ cash അല്ലെങ്കിൽ Owner payout ആയി കണക്കാക്കരുത്.

### J07 — Main finance: BLOCKED for P9-TEST-001

**സ്ഥിരീകരിച്ച കാരണം:** P9-TEST-001 purchase-ന്റെ `investor_share_agreement_id`, `investor_share_percentage_snapshot` രണ്ടും NULL. Vehicle Details historical agreement ഇല്ലെന്ന് കാണിക്കുന്നു; Investment service snapshot ഇല്ലെങ്കിൽ manual review ആവശ്യപ്പെടുന്നു. ഈ test record-ന്റെ data blocker ആണ്; ഇതുമാത്രം മുഴുവൻ finance engine തകരാറാണെന്ന തെളിവല്ല. നിലവിലെ agreement പിന്നീടുള്ളതാണെങ്കിൽ അത് പഴയ purchase terms ആയി കരുതരുത്.

**പരിഹാരം:** ആദ്യം ആ purchase സമയത്ത് യഥാർത്ഥത്തിൽ നിലവിലുണ്ടായിരുന്ന agreement/date/percentage-ന്റെ authoritative evidence കണ്ടെത്തുക. ഇല്ലെങ്കിൽ `BUSINESS DECISION REQUIRED` രേഖപ്പെടുത്തി ഈ record-ന്റെ reconciliation നിർത്തുക; NULL നേരിട്ട് update ചെയ്യുകയോ share ഊഹിക്കുകയോ ചെയ്യരുത്. സ്വതന്ത്ര acceptance പരിശോധനയ്ക്ക് യഥാർത്ഥ historical record മാറ്റാതെ, disposable DB-യിൽ ആദ്യം agreement സൃഷ്ടിച്ച് തുടർന്ന് പുതിയ Investor-funded Vehicle purchase ചെയ്യുക; purchase-time snapshot ഉണ്ടെന്ന് ഉറപ്പാക്കുക. Sale, collection, result confirmation, partial payout, period reconciliation, stale source rejection, Loss/Exit/Owner position എന്നിവ നിലവിലുള്ള Phase 8 services വഴി പരിശോധിക്കുക. Snapshot correction/backfill ആവശ്യമെങ്കിൽ impact report, history compatibility, approved business decision, migration/rollback plan എന്നിവയ്ക്കുശേഷം മാത്രം.

### J08 — Main UI: PARTIAL

**കാരണം:** Dashboard, Vehicles, Vehicle Details, Fund, Garage, Accounting live browser-ൽ തുറന്നു; മുഴുവൻ required routes, errors, refresh/logout/login, 320/390/768/1024/1440 viewport sweep പരിശോധിച്ചിട്ടില്ല. Reports page Demo എന്ന് അടയാളപ്പെടുത്തിയതാണ്; പുതിയ Reports ഈ scope-ൽ ഇല്ല.

**നടപടി:** നിലവിലുള്ള UI, colors, KPI composition സംരക്ഷിച്ച് required routes-ൽ API values, loading, empty, 403/409/500/network, module OFF, reload, logout/login പരിശോധിക്കുക. 3/4-card pages-ൽ അഞ്ച് widths പരിശോധിച്ച് overflow/clipping രേഖപ്പെടുത്തുക. Browser viewport tooling ലഭ്യമല്ലെങ്കിൽ `UNVERIFIED` ആയി രേഖപ്പെടുത്തുക. Confirmed data wiring defect മാത്രം minimal fix; UI മാറ്റം ഉപയോക്താവിന്റെ അനുമതിക്ക് ശേഷം.

### J09 — Negative matrix: PARTIAL

**കാരണം:** selected module OFF, cross-company Garage, owner restriction, rollback, concurrency cap tests വിജയിച്ചു; എല്ലാ role/Branch/module combinations-നും server-side evidence ഇല്ല.

**നടപടി:** cross-Company ID, unauthorized Branch, Owner/Investor/Media/Back Office write, module OFF, stale version, retry conflict, concurrent cap, failed transaction rollback ഓരോന്നിനും ആവശ്യമായ focused existing test അല്ലെങ്കിൽ disposable API check നടത്തുക. Denied request data ചോർത്തുന്നില്ല, mutation/partial cash artifacts ഇല്ലെന്ന് പരിശോധിക്കുക. ഇതിനകം ബാധകമായ passing test വീണ്ടും ഓടിക്കേണ്ടതില്ല; test name, command, result, environment തെളിവായി രേഖപ്പെടുത്തുക.

## നടപ്പാക്കൽ ക്രമവും അന്തിമ തീരുമാനം

1. Runtime/DB identity ഉറപ്പാക്കി test login പ്രവർത്തിക്കുന്നതായി പരിശോധിക്കുക.
2. J02 → J03 → J04 → J05 → J06 live disposable journeys നടത്തുക; ഓരോ ഘട്ടത്തിന്റെയും source, cash, reload തെളിവ് ശേഖരിക്കുക.
3. J07-ന് പുതിയ valid agreement test fixture ഉപയോഗിക്കുക; P9-TEST-001 historical blocker വേറെയായി രേഖപ്പെടുത്തുക.
4. J08 responsive/error പരിശോധനയും J09-ലെ ശേഷിക്കുന്ന negative checks-ഉം നടത്തുക. പ്രശ്നം കണ്ടാൽ severity, exact reproduction, root cause/evidence, affected path രേഖപ്പെടുത്തി അടുത്ത സ്വതന്ത്ര check തുടരുക.
5. Confirmed defect-ുകൾക്ക് മാത്രം ചെറിയ repair; money/auth/tenant/schema/shared API മാറ്റത്തിന് impact report, ബാധകമായ approval gate പാലിക്കുക. Fix ചെയ്ത path-ന്റെ focused regression മാത്രം വീണ്ടും ഓടിക്കുക.
6. ഒറ്റ final report: branch/SHA/worktree, environment, J01–J09 status, commands/counts, live vs automated evidence, defects, blockers, UI/financial impact. എല്ലാ ആവശ്യമായ തെളിവും unresolved acceptance blocker ഇല്ലാതെയും മാത്രം `PHASE9 LOCALLY ACCEPTED`; അല്ലെങ്കിൽ `PARTIAL/UNVERIFIED` അല്ലെങ്കിൽ `BLOCKED` കാരണം സഹിതം. Local acceptance deployment claim അല്ല.
