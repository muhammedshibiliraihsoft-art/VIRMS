# Phase 6 — Garage architecture തയ്യാറാക്കാനുള്ള പ്ലാൻ

**നില:** PLANNING ONLY — architecture lock ചെയ്തിട്ടില്ല; implementation തുടങ്ങിയിട്ടില്ല.  
**പരിശോധിച്ച worktree:** `D:/VIRMS/tmp/phase5-investment-foundation-20261107`, `codex/phase5-investment-foundation`, `26e509a1` (2026-11-17).  
**Risk:** HIGH-RISK — Company/Branch permission, Vehicle cost, Accounting receipt, concurrency എന്നിവയെ ബാധിക്കുന്നു.

## ലക്ഷ്യം

Phase 5 വരെ ഉള്ള Vehicle, Investment, Accounting പ്രവർത്തനങ്ങൾ ഉപയോഗിച്ച് Phase 6-ന്റെ **കുറഞ്ഞ, പ്രായോഗിക Garage scope** തീരുമാനിക്കുക. ആദ്യം architecture-ൽ ownership, data/API ബന്ധം, role/module gates, history, verification എന്നിവ ഉറപ്പാക്കുക; അതിനുശേഷം മാത്രം implementation slices നിശ്ചയിക്കുക. ഈ രേഖ business rule മാറ്റുകയോ Phase 6 നടപ്പാക്കിയെന്ന് അവകാശപ്പെടുകയോ ചെയ്യുന്നില്ല.

## നിലവിലെ അടിസ്ഥാനം — തെളിവിന്റെ പരിധി

| വിഷയം | ഇപ്പോഴത്തെ നില |
|---|---|
| Company/Branch, auth, module state | Repository-യിൽ backend foundation ഉണ്ട്; `garage` module code ഉണ്ട്. |
| Vehicle | Phase 5 backend Vehicle identity/movement, purchase, direct Stock Vehicle expense, Sale/Buyer cash flows എന്നിവയുണ്ട്. ഇവയാണ് Garage ഉപയോഗിക്കേണ്ട authoritative ബന്ധങ്ങൾ. |
| Accounting | Phase 4 ledger/cash foundation-ും Phase 5 typed source links-ഉം ഉണ്ട്. Garage receipt/revenue link പുതിയ contract ആയി രൂപകൽപ്പന ചെയ്യണം. |
| Garage/Labour backend | `apps/garage`/`apps/labour` ഇല്ല; Job/worker persistence, API, migrations എന്നിവ Phase 6-ൽ രൂപകൽപ്പന ചെയ്യേണ്ടതാണ്. |
| React Garage screens | `GarageJobsView`, `GarageJobDetailView` നിലവിലുണ്ട്; `App.tsx`-യിലെ Job/Garage state prototype data ഉപയോഗിക്കുന്നു. Backend integration ഇതുവരെ തെളിഞ്ഞിട്ടില്ല. |
| Vehicle deactivation | Open Garage Job പരിശോധിക്കുന്ന authoritative provider ഇല്ലാത്തതിനാൽ deactivation തടഞ്ഞിരിക്കുന്നു. Garage provider വന്നാലും Investor settlement ഉൾപ്പെടെയുള്ള മറ്റു തടസ്സങ്ങൾ സ്വയം മാറില്ല. |

Roadmap-ിലെ ചില dated status വാചകങ്ങൾ പഴയ snapshot ആണ്. Implementation truth-നായി current code/migrations വീണ്ടും പരിശോധിക്കണം; staging/production state ഈ പ്ലാൻ സ്ഥിരീകരിക്കുന്നില്ല.

## Phase 6-ൽ അടിസ്ഥാനമായി ഉൾപ്പെടുത്താൻ നിർദ്ദേശിക്കുന്നത്

1. **Job foundation:** നിലവിലുള്ള Company Vehicle UUID-നെ refer ചെയ്യുന്ന Branch Job; Stock work, external-customer work എന്നീ context-ുകൾ; OPEN/COMPLETED status, reopen, work/history, actor/time. Garage സ്വന്തം Vehicle identity സൃഷ്ടിക്കരുത്.
2. **Work and cost:** Job work entries, approved parts/materials/Labour total cost. Stock Job cost നിലവിലെ Vehicle total cost-ിൽ **ഒരിക്കൽ മാത്രം** ചേരുന്ന typed relationship; Phase 5 direct Vehicle Expense-നെ duplicate ചെയ്യരുത്. External customer cost അതിന്റെ Job/bill-ൽ കാണണം. Investor Fund-use സ്വയം ഉണ്ടാകരുത്.
3. **External-customer charge and collection:** Job-ന്റെ agreed charge, partial receipts, derived outstanding balance. Actual cash movement-ും Garage Revenue source-ഉം Accounting-owned ആയിരിക്കണം; ഒരേ receipt-ന് ഒറ്റ cash effect. Charge-നെ receipt ആയി കാണിക്കരുത്.
4. **Basic Labour:** Company/Branch worker record, Active/Inactive, manual payment amount/date/optional note/history. Worker payment Job cost-ിലേക്ക് സ്വയം allocate ചെയ്യരുത്.
5. **Existing UI integration:** നിലവിലെ Garage list/detail/navigation സംരക്ഷിച്ച് real API data-യിലേക്ക് മാറ്റുക. Demo data സ്വയം DB-യിലേക്ക് import ചെയ്യരുത്. Save വിജയിച്ചശേഷം മാത്രം success; reload ചെയ്താലും അതേ record കാണണം.
6. **Open-Job provider:** Vehicle deactivation guard-ന് authoritative OPEN Job result നൽകുന്ന contract. Job ഇല്ലെന്നത് തെളിയിക്കാനാവാത്ത അവസ്ഥ `UNKNOWN` ആയി തുടരുകയും deactivation തടയുകയും വേണം.

## Architecture എഴുതുന്നതിന്റെ ക്രമം

| പടി | തീരുമാനിക്കേണ്ട / രേഖപ്പെടുത്തേണ്ട ഫലം | പൂർത്തിയായതായി കാണാനുള്ള തെളിവ് |
|---|---|---|
| 1. Baseline | നിലവിലെ Vehicle, Accounting, module-state, React Job consumers, migrations, permissions എന്നിവയുടെ source map | Implemented / prototype / V2 target വേർതിരിച്ച inventory |
| 2. ചെറിയ business-decision gate | **RESOLVED 2026-11-17:** External Job-ൽ Name നിർബന്ധം, Phone ഐച്ഛികം; വേറെ genuine conflict കണ്ടെത്തിയാൽ മാത്രം ചോദിക്കുക | തീരുമാനം canonical Garage V2-ൽ രേഖപ്പെടുത്തി; ബാധിത schema/API validation ഇതനുസരിച്ച് lock ചെയ്യാം |
| 3. Ownership & data model | Job, work, charge, cost, worker, typed Accounting link, Vehicle reference, Branch history; unique constraints, corrections, retention | ഒരേ Vehicle/cost/receipt രണ്ട് owners-ൽ ഉണ്ടാകാത്ത relationship map |
| 4. Permission & module matrix | Stock/customer Job actions, Branch scope, Owner read-only, Garage OFF, Investment OFF, Accounting cash gate | Server-side action-by-action table; cross-Branch mutation default-deny |
| 5. API & transaction contract | List/detail/create/work/cost/status/charge/receipt/Labour; error codes, idempotency, lock order, concurrent receipt cap, rollback | ഓരോ write-നും source owner, request→response, duplicate/retry outcome വ്യക്തമാകണം |
| 6. UI contract          | Existing routes/forms/list-detail-നെ backend calls-ുമായി map ചെയ്യുക; loading/error/partial-paid/permission states | Mock→real മാറ്റത്തിന്റെ affected-components map; പഴയ Company/Vehicle flows സംരക്ഷണം |
| 7. Implementation slices | Job foundation → work/status → cost & Vehicle link → external charge/Accounting receipt → Labour → React integration | ഓരോ slice-നും migration, focused regression, browser workflow gate |

## നിർബന്ധമായ safety checks

- Company/Branch ID client-ൽ നിന്നു കിട്ടുന്നതു മാത്രം authorization അല്ല; membership, effective Branch assignment, role, module, object scope backend പരിശോധിക്കണം.
- Garage Investment OFF ആയാലും external-customer Job നടത്താൻ കഴിയണം. Stock financial source മാറ്റം owning Investment/Vehicle operation മാത്രം ചെയ്യണം.
- OPEN↔COMPLETED transition history നിലനിർത്തണം; COMPLETED Job-ൽ work/cost/charge edit ചെയ്യാൻ reopen ആവശ്യമാണ്.
- External Job receipts Company-wide unique external reference, current charge cap, same-Company typed link, Accounting cash effect once, concurrent request safety എന്നിവ പാലിക്കണം. Existing Vehicle Sale/Buyer receipt നിയമങ്ങൾക്കൊപ്പം ഇവ കലർത്തരുത്.
- Garage OFF-ൽ പുതിയ Job/optional expansion/new charge തടയണം; authorized history വായിക്കാൻ കഴിയണം. Existing obligation തീർക്കൽ owning Accounting rule അനുസരിച്ചായിരിക്കണം.
- Garage provider മാത്രം വന്നതുകൊണ്ട് Vehicle deactivation/registration reuse തുറക്കരുത്; Sale, finance/refund, Investor settlement എന്നീ മറ്റു authoritative guards വേറെയും ആവശ്യമാണ്.

## ഇപ്പോൾ ഉൾപ്പെടുത്താത്തത്

Full Parts Inventory, payroll, attendance, worker-to-Vehicle costing, CRM/customer deduplication, generic refund/credit, automatic Investor settlement, new UI redesign, automation engine എന്നിവ basic Garage architecture-ന്റെ നിർബന്ധമായ തുടക്കമല്ല. നിലവിലെ V2-approved automation mode ഭാവിയിൽ ഒരു Garage action യഥാർത്ഥത്തിൽ automate ചെയ്യുമ്പോൾ മാത്രം അതിന്റെ policy contract-ൽ ചേർക്കണം.

## Architecture lock gate

ഈ plan-ന്റെ ഫലം ഒരു Phase 6 code-level architecture document ആയിരിക്കണം. അതിൽ schema ownership, source links, endpoints, authorization, module-OFF behavior, transaction/idempotency, migration order, current React integration, tests, unresolved decisions എന്നിവ കൃത്യമായി രേഖപ്പെടുത്തണം. 2026-11-17-ലെ V2 cross-check-ൽ basic Garage scope-ന് വലിയ business തീരുമാനം ബാക്കിയില്ല; Company Profit-ിലെ Garage Revenue recognition പിന്നീട് integrated finance scope-ലാണ്, Job charge/receipt രേഖപ്പെടുത്തൽ അതിനായി തടയേണ്ടതില്ല. ശേഷിക്കുന്ന source-contract technical design തീർന്നിട്ട് മാത്രം `READY_FOR_IMPLEMENTATION` എന്ന് അടയാളപ്പെടുത്തുക. അതുവരെ Phase 6 roadmap status `NOT STARTED`/architecture in progress എന്ന നിലയിൽ മാത്രം കാണിക്കുക.

**Sources:** [V2 Garage workflow](../../docs-final-v2/10-garage-jobs-workflow.md), [V2 modules](../../docs-final-v2/03-system-modules.md), [V2 data relationships](../../docs-final-v2/04-data-model-relationships.md), [V2 UI](../../docs-final-v2/07-ui-navigation-structure.md), [roadmap](../../planning/V2-DEVELOPMENT-ROADMAP.md), [Phase 5 architecture](../phase-05-investment-vehicle-running-capital/PHASE-05-INVESTMENT-VEHICLE-RUNNING-CAPITAL-ARCHITECTURE.md).
