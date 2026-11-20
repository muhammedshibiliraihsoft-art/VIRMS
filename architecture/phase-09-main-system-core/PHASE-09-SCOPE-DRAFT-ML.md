# Phase 9 — Main VIRMS System Core Complete: scope

**സ്ഥിതി:** `DRAFT — SCOPE ONLY`. Roadmap-ൽ Phase 9 `NOT STARTED` ആണ്. ഈ രേഖ code പൂർത്തിയായതായി പ്രഖ്യാപിക്കുന്നില്ല.

## ലക്ഷ്യം

Phase 1–8-ൽ അംഗീകരിച്ച പ്രധാന പ്രവർത്തനങ്ങൾ Main VIRMS System-ൽ പരസ്പരം ബന്ധപ്പെടുത്തി, യഥാർത്ഥ data ഉപയോഗിച്ച് സുരക്ഷിതമായി പ്രവർത്തിക്കുന്നുവെന്ന് ഉറപ്പാക്കുക. Phase 9 ഒരു പുതിയ finance കണക്കിന്റെ ഉടമയല്ല; core system-ന്റെ സംയോജിത acceptance ഘട്ടമാണ്.

## പരിധിയിൽ ഉൾപ്പെടുത്തേണ്ടത്

1. **Platform-ും Back Office-ും:** Login/session, Company/Branch തിരിച്ചറിയൽ, roles, module state, account administration, ആവശ്യമായ protected configuration എന്നിവ നിലവിലെ approved പരിധിയിൽ പ്രവർത്തിക്കുന്നതായി പരിശോധിക്കുക.
2. **Main Operations:** Investor/Fund, Vehicle/Purchase/Expense, Garage Jobs/Stock cost, Sales/Buyer collection, Accounting, Phase 8 finance/settlement എന്നിവയിലെ ആവശ്യമായ end-to-end പ്രവാഹങ്ങൾ യഥാർത്ഥ API-യും database-ഉം ഉപയോഗിച്ച് പ്രവർത്തിക്കുന്നതായി ഉറപ്പാക്കുക.
3. **ഒരേ സാമ്പത്തിക സത്യം:** Accounting Cash/Bank movement ഒറ്റത്തവണ മാത്രം; Investor Fund, Company Running Capital, Vehicle cost, Garage charge, Sale, Profit, settlement എന്നിവ അവയുടെ യഥാർത്ഥ source-ിൽ നിന്നുതന്നെ വരണം. Branch-നെ വേറൊരു Company Fund ആയി കണക്കാക്കരുത്.
4. **അധികാരവും സ്വകാര്യതയും:** Company isolation, Branch scope, Investor/Owner/Media/Back Office read-write പരിധി, module OFF behavior, object-level access എന്നിവ API-യിലും UI-യിലും പരിശോധിക്കുക.
5. **സ്ഥിരതയും ചരിത്രവും:** correction/history, concurrent writes, retry/idempotency, duplicate reference, partial payment/refund, page reload-ൽ persisted state, migration replay എന്നിവയിൽ core workflow തകരരുത്.
6. **ഉപയോഗക്ഷമത:** നിലവിലെ routes/navigation/UI composition നിലനിർത്തി desktop, tablet, mobile-ൽ loading, empty, error, disabled നിലകളും പ്രധാന workflows-ഉം പരിശോധിക്കുക. Backend mutation പരാജയപ്പെട്ടാൽ വിജയിച്ചതായി കാണിക്കരുത്.
7. **Acceptance രേഖ:** ഓരോ core workflow-ക്കും പരിശോധിച്ച code/API/DB/browser തെളിവ്, ശേഷിക്കുന്ന risk, CI/runtime നില എന്നിവ രേഖപ്പെടുത്തുക. Local verification, CI, staging, production എന്നിവയുടെ തെളിവുകൾ വേർതിരിക്കുക.

## ആരംഭവും പൂർത്തീകരണവും

- **ആരംഭം:** Roadmap പറയുന്നതുപോലെ Phase 1–8 ഓരോന്നും തങ്ങളുടെ നിർവചിച്ച end condition-ൽ എത്തിയിരിക്കണം. Phase 8-ലെ തീരുമാനമാകാത്ത exception-ുകൾ approved core flow-നെ ബാധിക്കുന്നിടത്ത് Phase 9 acceptance തടയും.
- **പൂർത്തീകരണം:** Main Operations-ന്റെ ആവശ്യമായ core workflows യഥാർത്ഥ data-യിൽ ഉപയോഗിക്കാനാകണം; critical integration, permissions, cash/data integrity, migration, regression checks വിജയിക്കണം. അപ്പോഴാണ് ആദ്യത്തെ പ്രത്യേക user-facing portal-ായ Phase 10-ന് വേണ്ട backend നില ഉറപ്പാകുന്നത്.
- **Status rule:** തെളിവുള്ള local completion-നെ staging/production completion ആയി രേഖപ്പെടുത്തരുത്. Roadmap status മാറ്റുക യഥാർത്ഥ acceptance കഴിഞ്ഞ് മാത്രം.

## പരിധിക്ക് പുറത്തുള്ളത്

- Phase 8-ലെ തീരാത്ത business decision-ുകൾക്ക് പുതിയ നിയമം സൃഷ്ടിക്കൽ.
- Investor Portal-ന്റെ പ്രത്യേക UI/API (Phase 10), Owner Platform (Phase 11), Media/public portal-ുകളുടെ അധിക വികസനം.
- UI redesign, offline financial writes, deployment-ready എന്ന പ്രഖ്യാപനം തെളിവില്ലാതെ നടത്തൽ.

## Phase 8–10 ഒരുമിച്ചുള്ള പ്രവർത്തനക്രമം

Phase 8 implementation-നും Phase 9 acceptance checklist-നും Phase 10 portal design/read API തയ്യാറെടുപ്പിനും ഒരേ work programme-ൽ പ്രവർത്തിക്കാം. എന്നാൽ Phase 9 `COMPLETE` എന്ന് പറയാൻ Phase 8 end condition വേണം; Phase 10-ൽ financial position ഉപയോക്താവിന് കാണിക്കാൻ അതിന്റെ authoritative backend position ആദ്യം ഉറപ്പാകണം. Calendar/Profit സംബന്ധിച്ച തുറന്ന തീരുമാനങ്ങൾ ബാധിക്കുന്ന portal view-ുകൾ നിശ്ചിത payout ആയി കാണിക്കരുത്.

## അടിസ്ഥാന രേഖകൾ

- `planning/V2-DEVELOPMENT-ROADMAP.md` — Phase 9 goal, starts/ends, Phase 10 dependency.
- `docs-final-v2/02-user-roles-permissions.md`, `03-system-modules.md`, `07-ui-navigation-structure.md`.
- `architecture/phase-08-integrated-finance/PHASE-08-INTEGRATED-FINANCE-ARCHITECTURE.md` — Phase 8 integration boundary and decision gates.
