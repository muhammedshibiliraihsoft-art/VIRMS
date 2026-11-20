# Phase 8 — സംയോജിത ധനക്കണക്ക്, Settlement, തിരുത്തലുകൾ, Company Accounting

**സ്ഥിതി:** `DRAFT — SCOPE ONLY`

**അർത്ഥം:** ഇത് scope കരടാണ്. അന്തിമ ബിസിനസ് നിയമങ്ങളുടെ അംഗീകാരമോ implementation architecture lock-ഓ അല്ല.

**Roadmap സ്ഥിതി:** `NOT STARTED`.

## ലക്ഷ്യം

Phase 4–7-ൽ ഉള്ള യഥാർത്ഥ Accounting, Investment, Vehicle, Garage, Sale, Buyer Collection രേഖകൾ ചേർത്ത് Investor-ന്റെയും Company-യുടെയും കണക്കുകൾ തയ്യാറാക്കുക. ഒരു ഇടപാട് രണ്ടുതവണ കണക്കാകരുത്. യഥാർത്ഥ പണമിടപാട് അധികാരമുള്ള വ്യക്തി സ്ഥിരീകരിച്ചാൽ മാത്രമേ രേഖപ്പെടുത്താവൂ.

## Phase 8-ൽ ഉൾപ്പെടുത്തേണ്ടത്

1. **ഉറവിട രേഖകൾ ബന്ധിപ്പിച്ച കണക്കുകൾ**
   - Cash/Bank movement-ന്റെ യഥാർത്ഥ രേഖ Accounting-ൽ തുടരും. Phase 5–7-ലെ Fund, Purchase, Vehicle Expense, Garage Job cost, Sale, Buyer receipt/refund, Sale correction എന്നിവ നിലവിലുള്ള typed links വഴി ഉപയോഗിക്കുക.
   - Company ആകെ കണക്ക് എല്ലാ Branch-ുകളും ചേർത്ത് കാണിക്കാം. എന്നാൽ ഓരോ രേഖയുടെയും Company, Branch, Investor, Vehicle ബന്ധവും പഴയ ചരിത്രവും നിലനിർത്തണം.
   - ഒരേ പണമിടപാടിന് രണ്ടാമത്തെ Cash/Bank movement ഉണ്ടാക്കരുത്.

2. **Vehicle മൂലധനവും പോസിറ്റീവ് ഫലവും**
   - യഥാർത്ഥ Buyer collection, അംഗീകരിച്ച Purchase/Expense cost, Investor principal, ആ Vehicle-നോട് ബന്ധിപ്പിച്ച Company Running Capital എന്നിവ വേർതിരിച്ച് കണക്കാക്കുക.
   - Running Capital recovery-യെ Investor principal-ിലോ Profit-ിലോ കലർത്തരുത്. പണം യഥാർത്ഥത്തിൽ ലഭിച്ചോ നൽകിയോ എന്ന് പ്രത്യേകം രേഖപ്പെടുത്തുക.
   - Investor share-ിന് ബാധകമായ agreement snapshot ഉപയോഗിക്കുക. Q100 പ്രകാരം Sale price correction/refund വന്നാൽ ബന്ധപ്പെട്ട Investor കണക്ക് source രേഖകളിൽ നിന്ന് പുതുക്കാം; ഈ refresh സ്വയം payment അല്ലെങ്കിൽ Cash/Bank movement സൃഷ്ടിക്കില്ല.

3. **Investor Profit, Interim, കാലയളവിലെ reconciliation**
   - Earned Profit, യഥാർത്ഥമായി അടച്ച deal-level Profit, Monthly Interim payment, corrections എന്നിവ reconciliation-ൽ ഉൾപ്പെടുത്തുക.
   - `Calculated`, `Eligible`, `Paid`, `Recoverable` എന്നീ നിലകൾ വേർതിരിക്കുക. Period അവസാനിച്ചതുകൊണ്ടോ കണക്കുണ്ടായതുകൊണ്ടോ payment നടന്നതായി കാണിക്കരുത്.
   - Deal ഏത് Profit period-ൽ വരണം, deal-level payment-ും ആറുമാസ/വാർഷിക reconciliation-ും എങ്ങനെ ഒത്തുചേരണം എന്നത് തീരുമാനമായശേഷം മാത്രമേ അന്തിമ payable/recoverable തുക നിശ്ചയിക്കാവൂ.
   - അംഗീകരിച്ച partial/multiple repayment, ഭാവിയിലെ Profit-ിൽ സ്ഥിരീകരിച്ച offset, Exit കഴിഞ്ഞുള്ള തുറന്ന overpayment എന്നിവ രേഖപ്പെടുത്തുക. മൗനമായ netting പാടില്ല.

4. **Investor Exit കണക്കും settlement-ും**
   - Investor-ന്റെ എല്ലാ Branch-ുകളിലെയും Fund, committed/available principal, Vehicle, Buyer collection/refund, Interim, Profit, Running Capital ബന്ധം, corrections, തുറന്ന ബാധ്യതകൾ എന്നിവ പരിശോധിക്കുക.
   - Cross-Branch Exit കണക്കും അന്തിമ settlement-ും അതേ Company-യിലെ Company-level Accountant മാത്രമേ പൂർത്തിയാക്കൂ.
   - Exit status മാറുന്നതുകൊണ്ട് മാത്രം payment ആയി കണക്കാക്കരുത്. ബാധകമായ കണക്കുകളും ബാധ്യതകളും തീർത്ത്, യഥാർത്ഥ principal/Profit payment രേഖപ്പെടുത്തിയശേഷം മാത്രമേ settlement പൂർത്തിയാകൂ.

5. **Company result, Owner Distribution**
   - Vehicle Company Share, Garage Revenue, മറ്റു Company Income, Company Expense എന്നിവയുടെ source history നിലനിർത്തി Company Profit/Loss കണക്കാക്കുക. Investor Profit, Company cash balance, Company Profit എന്നിവ വേർതിരിക്കുക.
   - Distributable Profit-ന്റെ അടിസ്ഥാനവും കാലയളവും അംഗീകരിച്ചശേഷം മാത്രം Owner allocation നിർദ്ദേശിക്കുക. യഥാർത്ഥ payment അധികാരമുള്ള Accountant സ്ഥിരീകരിച്ചാൽ മാത്രമേ `Paid` ആകൂ.
   - Owner Distribution-നെ Investor Profit reconciliation-ിൽ നിന്ന് വേറിട്ട് സൂക്ഷിക്കുക.

6. **Corrections, audit, concurrency**
   - Sale, payment, cost, allocation, reconciliation, payout എന്നിവയുടെ യഥാർത്ഥ രേഖകൾ ഇല്ലാതാക്കരുത്. തിരുത്തൽ പഴയ രേഖയോട് link ചെയ്ത് നിലവിലെ ബാക്കി വീണ്ടും കണക്കാക്കുക.
   - Q133–Q134 പ്രകാരം ഉപയോഗിച്ചോ തിരികെ നൽകിയോ കഴിഞ്ഞ Fund Credit-ന്റെ Investor attribution തിരുത്തുമ്പോൾ പഴയ Fund-use-ും യഥാർത്ഥ Cash/Bank movement-ും മാറ്റരുത്. ബാധിച്ച കണക്കുകൾ Accountant കൈയോടെ പരിശോധിക്കണം; സ്വയം വീണ്ടും വിഭജിക്കുകയോ payment മാറ്റുകയോ ചെയ്യരുത്.
   - Duplicate request, ഒരേസമയം നടക്കുന്ന പ്രവർത്തനം, അനുവദിച്ച പരിധി കടക്കുന്ന തുക എന്നിവ transaction, idempotency, server-side permission, Company isolation എന്നിവ ഉപയോഗിച്ച് തടയുക.

7. **API, നിലവിലെ React UI**
   - നിലവിലെ routes, navigation, permissions എന്നിവ നിലനിർത്തി source രേഖകൾ, കണക്കാക്കിയ തുക, ബാക്കി, correction history, സ്ഥിരീകരണ നടപടി എന്നിവ വ്യക്തമായി കാണിക്കുക.
   - നിർദ്ദേശിത കണക്കും യഥാർത്ഥ payment/financial posting-ും വേർതിരിക്കുക. യഥാർത്ഥ posting അധികാരമുള്ള വ്യക്തിയുടെ സ്ഥിരീകരണത്തിനു ശേഷമേ ഉണ്ടാകൂ.

## ഇനിയും തീരുമാനിക്കേണ്ട ബിസിനസ് കാര്യങ്ങൾ

ഇവയ്ക്ക് അനുമാനിച്ച് നിയമം ഉണ്ടാക്കരുത്. ബന്ധപ്പെട്ട payment, period close, settlement എന്നിവ പൂർത്തിയാക്കുന്നതിന് മുമ്പ് തീരുമാനം രേഖപ്പെടുത്തണം. ഇവയെ ആശ്രയിക്കാത്ത, source വ്യക്തമായ positive flow-ുകൾ വേർതിരിച്ച് നടപ്പാക്കാം.

- Deal-level Investor Profit ഏത് reconciliation കാലയളവിൽ ചേരണം; deal-level payment-ും period payment-ും തമ്മിൽ ഇരട്ട payment എങ്ങനെ ഒഴിവാക്കണം.
- Profit/Interim കണക്കിന് വേണ്ട eligible principal അടിസ്ഥാനവും അനുവദിക്കാവുന്ന principal withdrawal പരിധിയും.
- Vehicle Loss Investor-ന്റെയും Company Running Capital-ന്റെയും Company കണക്കിന്റെയും മേൽ എങ്ങനെ ബാധിക്കണം; Loss സ്ഥിരീകരിക്കാനുള്ള കൃത്യമായ role.
- Company distributable Profit-ന്റെ കൃത്യമായ അടിസ്ഥാനം, period close/carryforward, Company Share, Garage Revenue, പൊതുചെലവുകളുടെ കണക്കാക്കൽ.
- Investment/Vehicle/Accounting module OFF ആയിരിക്കുമ്പോൾ മുമ്പേ ഉണ്ടായ obligation-ുകൾ തീർക്കാൻ അനുവദിക്കേണ്ട കുറഞ്ഞ പ്രവർത്തനങ്ങളും module gates-ും.
- Garage/Investment-ിലെ ഓരോ Branch correction-ും ആർക്കാണ് ചെയ്യാൻ കഴിയുക. എല്ലാ module-ുകൾക്കും ബാധകമായ പൊതുവായ cross-Branch അനുമതി ഉണ്ടാകരുത്.

## Phase 8-ന്റെ പരിധിക്ക് പുറത്തുള്ളത്

- Phase 1–7-ൽ അംഗീകരിച്ച source-record പ്രവാഹങ്ങൾ വീണ്ടും നിർമ്മിക്കൽ; Phase 7 പൂർത്തിയായിട്ടില്ലെന്നു കരുതൽ.
- മനുഷ്യന്റെ സ്ഥിരീകരണമില്ലാത്ത payment, അംഗീകരിക്കാത്ത Loss allocation, ഉറപ്പായ Investor return, സ്വയം Owner payout.
- Investor Portal, Phase 9-ന് ശേഷമുള്ള ജോലികൾ, offline financial entry, sync സംവിധാനം.
- API request എണ്ണം മാത്രം കുറയ്ക്കാൻ നിലവിലെ API മാറ്റൽ.

## ആരംഭ വ്യവസ്ഥകളും പൂർത്തീകരണ മാനദണ്ഡങ്ങളും

**തുടങ്ങുന്നതിന് മുൻപ്:** Phase 4–7-ന്റെ നിലവിലെ implementation, API, migrations, permissions, typed source links എന്നിവ പരിശോധിച്ച് verified നില രേഖപ്പെടുത്തുക. മുകളിൽ തുറന്നിരിക്കുന്ന തീരുമാനങ്ങൾ Phase 8 architecture lock-ിന് മുമ്പ് വ്യക്തമാക്കുക.

**Phase 8 പൂർത്തിയായതായി കണക്കാക്കാൻ:**

- അംഗീകരിച്ച positive flow-ുകൾ Company/Branch പരിധിയിൽ ശരിയായി ഒത്തുചേരുകയും principal, Running Capital, Investor/Company result, Interim, corrections, Owner allocation എന്നിവ ഇരട്ടിയായി കണക്കാകാതിരിക്കുകയും വേണം.
- ഓരോ യഥാർത്ഥ വരവ്/ചെലവിനും ഒരു Accounting cash movement മാത്രം ഉണ്ടാകണം; retry/concurrency സമയത്ത് അത് ഇരട്ടിയാകരുത്.
- Investor Exit, Loss, correction, Company period close, Owner payout എന്നിവ അംഗീകരിച്ച തീരുമാനങ്ങളും അധികാരപരിധിയും audit history-യും അനുസരിച്ച് പ്രവർത്തിക്കണം.
- Backend/API, DB/migration, React reload persistence, tenant/Branch authorization, concurrency/idempotency regression എന്നിവ പരിശോധിക്കണം.
- രേഖകൾ verified implementation-നോട് പൊരുത്തപ്പെടണം; തീരുമാനമാകാത്ത exceptional behavior-ന് automatic rule കെട്ടിച്ചമയ്ക്കരുത്.

## പരിശോധിച്ച രേഖകൾ

- `planning/V2-DEVELOPMENT-ROADMAP.md` — Phase 8 ലക്ഷ്യം, dependency, തീരുമാനം ആവശ്യമായ ഭാഗങ്ങൾ.
- `docs-final-v2/02-user-roles-permissions.md` — role, Company/Branch access, module gates.
- `docs-final-v2/04-data-model-relationships.md` — canonical data ബന്ധങ്ങൾ.
- `docs-final-v2/05-vehicle-investor-finance-workflow.md` — Investor/Vehicle finance, Profit, Interim, Loss, Exit, Q100, Q133–Q134.
- `docs-final-v2/09-company-accounting-owner-distribution.md` — Company result, distributable Profit, Owner Distribution.
- `architecture/phase-07-sales-buyers-collection/PHASE-07-SALES-BUYERS-COLLECTION-ARCHITECTURE.md` — Phase 7 source boundaries, status.
