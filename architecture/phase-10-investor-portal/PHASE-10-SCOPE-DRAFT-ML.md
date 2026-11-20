# Phase 10 — Investor Portal: scope

**സ്ഥിതി:** `DRAFT — SCOPE ONLY`. Roadmap-ൽ Phase 10 `NOT STARTED` ആണ്. Phase 9 acceptance-ഉം ആവശ്യമായ Phase 8 financial positions-ഉം ഇതിന്റെ തുടക്ക വ്യവസ്ഥകളാണ്.

## ലക്ഷ്യം

Investor-ന് സ്വന്തം Company-യിലെ അനുവദിച്ച Fund, Stock Vehicle, Interim, Profit/reconciliation, recoverable, Exit/settlement വിവരങ്ങൾ സുരക്ഷിതമായി കാണാനും സാധാരണ Exit request നൽകാനും പ്രത്യേക portal ഒരുക്കുക. ധനകാര്യ കണക്കിന്റെ owner Investment/Accounting/Vehicle/Garage source-ുകൾ തന്നെയാണ്; portal അത് തിരുത്തുന്ന മറ്റൊരു ledger ആകരുത്.

## പരിധിയിൽ ഉൾപ്പെടുത്തേണ്ടത്

1. **Identity, access:** Login ചെയ്ത Investor account-നെ server-side Company-ക്കും Investor record-നും ബന്ധിപ്പിക്കുക. ആ ബന്ധം ഏത് existing account model/API ഉപയോഗിച്ച് enforce ചെയ്യാമെന്ന് implementation architecture-ൽ പരിശോധിക്കുക. Request-ൽ വന്ന `investor_id` മാത്രം വിശ്വസിച്ച് private data നൽകാൻ പാടില്ല.
2. **Overview, Fund:** സ്വന്തം സ്ഥിരീകരിച്ച Fund credits, returns, available/committed principal, വ്യക്തമായ balance/history എന്നിവ കാണിക്കുക. മറ്റൊരു Branch-ിലോ Investor-ിലോ ഉള്ള സ്വകാര്യ data പുറത്തുവരരുത്; സ്വന്തം Company-wide position-ന്റെ authorized പരിധി മാത്രം.
3. **My Stock Vehicles:** തനിക്കു ബാധകമായ Stock Vehicles, status, അംഗീകരിച്ച Vehicle result/collection സ്ഥിതി, അനുവദിച്ച ചരിത്രം എന്നിവ കാണിക്കുക. മറ്റുള്ള Vehicle-ുകൾ approved public view വഴിയേ കാണിക്കാവൂ; internal cost അല്ലെങ്കിൽ മറ്റൊരു Investor identity വെളിപ്പെടുത്തരുത്.
4. **Interim, Profit, reconciliation:** സ്വന്തം Monthly Interim due/paid history, earned Profit, confirmed payments, നിലവിലെ period/reconciliation സ്ഥിതി, open recoverable എന്നിവ വേർതിരിച്ച് കാണിക്കുക. `Calculated`, `Eligible`, `Paid` ഒന്നായി കാണിക്കരുത്. തീരുമാനമാകാത്ത eligibility/period നിയമങ്ങളിൽ ഉറപ്പായ തുക കാണിക്കരുത്.
5. **Exit, settlement:** Terms & Conditions സമ്മതത്തോടെ സാധാരണ Exit request സമർപ്പിക്കാം; മൂന്നു മാസ notice, നിലവിലെ നില, നീട്ടിയ deadline, തീരാത്ത obligations, യഥാർത്ഥ settlement history എന്നിവ കാണാം. Exit-cancellation request നൽകാം; അതേ Company-യിലെ Company-level Accountant approve ചെയ്താൽ മാത്രമേ reactivation ഉണ്ടാകൂ. Investor-ന് settlement സ്വയം confirm ചെയ്യാനാകില്ല.
6. **Responsive UI:** V2 navigation അനുസരിച്ച് Overview, Fund Position, My Stock Vehicles, Interim Payouts, Profit/Reconciliation, Exit/Settlement എന്നിവ ഉപയോഗിക്കുക. നിലവിലെ design tokens/routes-നോട് ചേർന്ന mobile-friendly loading, empty, error, stale-data states ഒരുക്കുക.
7. **Backend contract:** Portal read responses ആവശ്യമായ fields മാത്രം നൽകണം; pagination/filtering server-side authorization മറികടക്കരുത്. Exit/cancellation request-ുകൾ idempotent, audited, Company-scoped commands ആയിരിക്കണം. Page reload-ൽ അതേ canonical backend state വരണം.

## ആരംഭവും പൂർത്തീകരണവും

- **ആരംഭം:** Phase 9 Main System core acceptance പൂർത്തിയാകണം; portal-ന് വേണ്ട Investor positions Phase 8-ൽ authoritative sources-ിൽ നിന്ന് ലഭിക്കണം.
- **പൂർത്തീകരണം:** Investor-ന് സ്വന്തം അനുവദിച്ച Fund, Vehicle, confirmed history, payout/reconciliation, recoverable, Exit/settlement വിവരങ്ങൾ backend authorization-ോടെ കാണുകയും normal Exit request നൽകുകയും ചെയ്യാൻ കഴിയണം. മറ്റൊരു Investor-ന്റെ data-യിലേക്കുള്ള read/write access തടയണം.
- **തീരുമാന gate:** Interim eligibility/withdrawal, deal Profit/period reconciliation എന്നിവ തീരാത്തിടത്ത് ബാധിച്ച view/action നിശ്ചിത ഫലം സൂചിപ്പിക്കരുത്. Phase 8-ലെ ഓരോ approved calculation/payment status-ും portal-ൽ അതേ അർത്ഥത്തിൽ മാത്രം കാണിക്കുക.

## പരിധിക്ക് പുറത്തുള്ളത്

- Fund credit, Vehicle funding, Profit/Interim payment, Loss allocation, reconciliation approval, Exit closure എന്നിവ Investor സ്വയം രേഖപ്പെടുത്തൽ.
- മറ്റൊരു Investor-ന്റെയോ Company-യുടെയോ സ്വകാര്യ data, Company-wide Accounting/Owner reports, internal Garage/Vehicle cost details.
- സ്വതന്ത്ര editable financial ledger, auto payout, Owner/Media/Back Office portal വികസനം, offline financial write.

## സുരക്ഷയും പരിശോധനയും

Investor-to-record binding, Company boundary, IDOR, list/detail/filter access, stale session, module state, duplicate Exit request, approval-required cancellation, source correction കഴിഞ്ഞുള്ള refresh, responsive/reload behavior എന്നിവ focused backend/API/browser checks-ൽ തെളിയിക്കുക. Portal view source-നോട് വ്യത്യസ്തമായ balance സൃഷ്ടിക്കരുത്. CI, staging, production നിലകൾ പ്രത്യേകം രേഖപ്പെടുത്തുക.

## അടിസ്ഥാന രേഖകൾ

- `planning/V2-DEVELOPMENT-ROADMAP.md` — Phase 10 goal, starts/ends, decision boundary.
- `docs-final-v2/02-user-roles-permissions.md`, `03-system-modules.md`, `05-vehicle-investor-finance-workflow.md`, `07-ui-navigation-structure.md`.
- `architecture/phase-08-integrated-finance/PHASE-08-INTEGRATED-FINANCE-ARCHITECTURE.md` — authoritative financial positions and open decisions.
