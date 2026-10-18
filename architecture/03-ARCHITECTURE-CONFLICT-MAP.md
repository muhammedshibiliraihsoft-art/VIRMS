# 03 — Architecture Conflict Map

## 0. Verification header

- Repository/worktree: `D:/VIRMS`, dirty `staging`; reviewed 2026-10-19. Tracked documentation HEAD `b4a40772edec567297e96d72bf037df73ea0cae6`. Backend and architecture files inspected locally are untracked.
- **CURRENT APPROVED/TARGET:** the intended V2 architecture in `/docs-final-v2/`, per explicit current user direction and `docs-final-v2/01`'s statement that `/docs-final/` is a previous baseline. This does **not** fill V2's open business decisions or claim formal final-lock status.
- **CURRENT IMPLEMENTED:** source-inspected account/Tenant Django foundation only. **HISTORICAL / SUPERSEDED:** V1 `/docs-final/`, `/docs-legacy/` and V1-derived technical assumptions. **PROPOSED:** no alternative business architecture is added here.
- **UNVERIFIED:** tests, database/migration ledger, deployed API, production history. **BUSINESS DECISION REQUIRED:** V2's explicitly open money/access meanings. Repo governance text still naming V1 is an active documentation conflict, not a reason to silently reinstall V1 as target.

## 1. Three-truth comparison

```mermaid
flowchart LR
  V2[V2: current intended target] --> G{Compare}
  CODE[Django: current partial implementation] --> G
  V1[V1 + legacy: historical / superseded] --> G
  GOV[README / AGENTS / design: stale V1 references] --> G
  G --> M[Conflicts, gaps and decisions]
```

Folder names, DRAFT/FINAL labels and commit recency alone do not determine the current target. Here the **latest explicit user direction** selects V2 for architecture mapping, and V2 itself calls V1 historical. The V2 header still says business approval is required before becoming authoritative; therefore **target selection is settled for these maps**, while formal document-governance reconciliation and unresolved V2 behavior remain outstanding. If a future instruction removes that explicit target or makes it genuinely ambiguous, mark `AUTHORITY CONFLICT — USER / BUSINESS CONFIRMATION REQUIRED` rather than guessing.

## 2. Canonical truth matrix

| Topic | CURRENT APPROVED/TARGET V2 | CURRENT IMPLEMENTED / tests | HISTORICAL / SUPERSEDED or stale text | Classification/action |
|---|---|---|---|---|
| Authority | V2 intended target; 01 says previous `/docs-final/` is historical baseline; 02/04/05/09/10 own V2 meanings | Code cannot choose product authority | `AGENTS.md`, README, `system-design/00`, `architecture/00` still declare V1 sole authority | `DOC_STALE`, `CONFLICT-001`; update governance only with separate authorization |
| Isolation | Platform→Company/Tenant→Branch; Company hard boundary, Branch within Company; module/action/object/field scope | Generic Tenant, global role and Tenant membership; no Branch/module state | V1 Garage=Tenant, Tenant-scoped Garage operations | `PARTIAL_IMPLEMENTATION`, `CONFLICT-002`; do not treat code as V1 approval |
| Investor/Vehicle | Fund relationship at Company level across Branches; one Investor per funded Stock Vehicle; external customer Vehicle requires none | No Investor, Fund, Vehicle or Garage model/API | V1 global cross-Garage Investor/Fund, one Investor for every Vehicle | `RULE_SUPERSEDED` for target; `CONFLICT-003` compatibility review |
| Money and Owner | Actual Company Running Capital separate; positive Investor/Company Share; Company-level period Owner Distribution; manual Loss | No finance tables/routes/tests | V1 per-deal Owner Pool, formula Loss/Owner contribution, no Company Accounting/Running Capital | `RULE_SUPERSEDED`; V2 `BUSINESS DECISION REQUIRED` in affected areas |
| Protected rates | Platform Back Office changes Investor agreements, monthly rate, Owner split and sensitive defaults; Accountant confirms authorized transactions | No protected financial configuration | V1 Accountant could change Investor-specific percentage | `RULE_SUPERSEDED`; actor boundary implementation gap |
| API and frontend | V2 Company/Branch/module-scoped backend, Garage independent of Investment, source-linked Accounting; React target | Account/Tenant routes only; test files present but unrun; no React | V1-derived System Design routes/diagrams and roadmap | `DOC_STALE` for business shape, `PARTIAL_IMPLEMENTATION` |
| Existing production history | V2 text says no production V1 cutover needed | No tracked app code or live DB inspected | README describes replaced starter migrations | `UNVERIFIED`, `CONFLICT-005`; cannot infer live data state |

No `SYSTEM_DEFECT` or `TEST_STALE` is declared without code/runtime/test evidence proving one. The present business-target mismatch is primarily **missing implementation**, not proof the V2 target is wrong.

## 3. Active conflict register

### CONFLICT-001 — Governance references still nominate superseded V1

- **Classification/area:** `DOC_STALE`; authority and documentation. `AGENTS.md`, modified README, `system-design/00-authority-and-design-contract.md`, `architecture/00-architecture-authority-and-delivery-model.md` and roadmaps still nominate `/docs-final/` as current. V2/01 calls that set historical, and the current user expressly classifies V2 as target.
- **Current implemented behavior:** no code can settle documentation authority; local backend is partial.
- **Why it matters:** future work may apply V1 money, Tenant or permission rules by following an old pointer.
- **Resolution for this task:** V2 is **CURRENT APPROVED/TARGET** in these four maps; V1 is **HISTORICAL / SUPERSEDED**. Do not edit governance/business documents without authorization. Formal governance text and any V1-derived System Design need a separately approved reconciliation before implementation relies on them.
- **Implementation authorized:** NO. **Status:** OPEN stale-document conflict. Target selection itself is not ambiguous after explicit user direction; this is not a request for the user to reconfirm it.

### CONFLICT-002 — Company/Branch/module target versus Tenant-only foundation

- **Classification/area:** `PARTIAL_IMPLEMENTATION`; identity, tenancy, authorization and API. V2 requires Company membership, relevant Branch assignment, enabled-module gate, role/action and object/field scope. Current source has User, RoleAssignment, TenantMembership, active Tenant list/detail and account management; no Branch or module state/checks.
- **Historical influence:** V1 Garage=Tenant design may have shaped the foundation, but generic `Tenant` code alone does not prove a V1 business implementation.
- **Why it matters:** a future financial/Job route built on Tenant membership alone could cross Branch/module boundaries or misassign Company money.
- **Resolution:** implement V2 scope only through a separately authorized task after source/schema/runtime review; preserve valid current auth/account behavior. **Status:** OPEN implementation gap. Missing implementation is not evidence V1 remains authoritative.

### CONFLICT-003 — V1-derived finance/design assumptions versus V2 economics

- **Classification/area:** `RULE_SUPERSEDED` for current target plus `BREAKING_CHANGE_RISK` if real V1 data/consumers exist. V1 treats Garage as Tenant, Investor/Fund as global, Owner payout as per-deal and Loss as percentage allocated. V2 makes Company the Tenant, Fund Company-level, Company Share a source of Company Accounting, Owner distribution a Company period action and Loss manual. V2 also adds Running Capital, Garage Jobs, interim payout/reconciliation and module state.
- **Current implementation:** no financial model/API to refactor was found. `/system-design/01`–`/19`, earlier `/architecture/` foundation/roadmap and diagram are V1-derived; their V1 business shapes are historical, though stack/technical practices may still be usable after revalidation.
- **Why it matters:** copying V1 formulas or permission actors would produce wrong V2 money and isolation behavior. A deployed V1 cutover remains **UNVERIFIED**.
- **Resolution:** use V2 as target, block affected actions on V2 BDRs, and reconcile technical design before those implementations. No migration or dual engine is prescribed by this documentation task. **Status:** OPEN design drift and future compatibility risk.

### CONFLICT-004 — V2 has explicit unresolved business meaning

- **Classification/area:** `BUSINESS_DECISION_REQUIRED`, not an architecture implementation choice. V2 marks eligible principal/withdrawal limits; interim versus deal/period reconciliation; manual Loss effects and actor; Company distributable-Profit definition; cross-Branch correction authority; Platform support private-finance read; and minimum settlement actions while module OFF as unresolved.
- **Current implementation:** none of these financial or module-control actions exists locally.
- **Why it matters:** a calculation, suggestion or historical V1 formula cannot supply an approved V2 economic/permission outcome.
- **Resolution:** keep affected implementation blocked or manual only where V2 explicitly permits it until business decisions are recorded. Other defined V2 target boundaries remain describable. **Status:** OPEN.

### CONFLICT-005 — Application history, tests and runtime evidence absent

- **Classification/area:** `UNVERIFIED`; schema/release/history. Backend source and migrations are untracked; tests were inspected but not run; live PostgreSQL, migration ledger, API, deployment and production transaction history were not checked.
- **Competing claims:** modified README says starter migrations were replaced; V2/01 and V2/06 say no production V1 cutover or dual calculation engine is required. These are documentation claims, not observed environment state.
- **Resolution:** verify environment and actual history before any migration, compatibility or release decision. Do not invent existing customers/data, and do not assume zero records. **Status:** OPEN evidence gap.

## 4. Superseded rule and current/previous delta register

| HISTORICAL / SUPERSEDED V1 rule or reference | CURRENT APPROVED/TARGET V2 replacement | Previous implemented behavior | Search/compatibility guard |
|---|---|---|---|
| Garage = Tenant | Company = Tenant; Branch/Garage is within Company | V1 deployed behavior UNVERIFIED | Search `Garage = Tenant`, Tenant resolver and transfer paths; no automatic data migration assumption. |
| Global Investor/Fund across Garages | Company-level Investor/Fund across that Company's Branches | V1 financial data UNVERIFIED | Search global Fund assumptions; prevent cross-Company balances. |
| Every Vehicle has one Investor | Funded Stock Vehicle one Investor; external customer Garage Vehicle need not have one | Vehicle implementation absent | Search unconditional Investor FK/permission assumptions. |
| Accountant changes Investor-specific percentage | Platform Back Office protects Investor positive-share agreement/rates; Accountant uses effective value | No agreement endpoint | Search Accountant config mutation assumptions. |
| Deal-level Owner Pool and percentage Loss | Company-level period Owner Distribution; new V2 Loss manual | No finance implementation | Search Owner pool/loss-share/contribution formulas; do not import them into V2. |
| No Company Accounting, Running Capital or Garage Jobs in V1 core | V2 Company Accounting, separate Running Capital and independent Garage Job workflow | No local implementation | V1 module list/roadmap is not a complete V2 module list. |

`docs-legacy/` remains non-authoritative historical material. Git commits show V1 freeze `24b7300` and V2 documentation additions `d8edb38`/`b4a4077`. Chronology alone did not choose V2; explicit project intent and V2's own authority statement did. No prior deployed business flow or data shape was verified.

## 5. Diagram, test and duplicate-source drift

| Evidence | Current status / drift | Required guard |
|---|---|---|
| `architecture/diagrams/virms-foundation-and-delivery-flow.mmd`, V1 roadmaps | Phase sequence may be useful, but labels/source basis point to V1 | Treat business/module conclusions as HISTORICAL / SUPERSEDED until reconciled. |
| `system-design/01` context, `/03` tenancy, `/05` finance, `/07` API | Technical design derived from V1, not a V2 contract | Do not copy global Fund, Garage Tenant or per-deal Owner/Loss semantics into V2. |
| `apps/accounts/tests/test_users.py`, `apps/tenants/tests/test_tenants.py` | Selected account/Tenant assertions present; execution UNVERIFIED; no V2 Branch/module/finance tests | `PARTIAL_IMPLEMENTATION`, not automatic `TEST_STALE` or V2 coverage. |
| Current Account/Tenant model plus future Company/Branch sources | Risk of treating generic Tenant membership as complete Company/Branch permission | One authoritative Company/Branch scope path; no duplicate grants from caller IDs. |
| Investment, Garage and Accounting views of the same money | V2 defines separate module ownership with source links | One actual economic event; Company ledger references source without double posting. |
| Monthly interim, ordinary deal Profit and period reconciliation | V2 distinct streams; precise reconciliation still BDR | Do not relabel an interim advance as earned deal Profit or count a payment twice. |

No test execution or runtime defect was performed/proven here. No conflict was marked resolved by a code commit. A stale design reference should be corrected under separate authorization rather than silently treated as approved V2 technical detail.

## 6. Security and ownership conflict guard

V2 hard boundary is Company. Branch is within-Company scope/attribution and module state gates ordinary actions. A Platform administrator's cross-Company platform capability does not automatically include private Company finance. Protected configuration permission does not confer Accountant posting permission. Media cannot read internal finance; Investor self-view cannot read another Investor; Owner is read-only. Current Tenant-only API coverage is narrower than those target controls. `CONFLICT-002/004` govern any affected route. Public views must use safe publication fields and never serialize internal Vehicle/Investor records.

## 7. Business decisions required and verification status

1. Monthly Interim Payout: eligible-principal basis and active-cycle principal withdrawal limit (`docs-final-v2/01`, `/04`, `/05`).
2. Investor reconciliation: deal inclusion and ordinary eligible deal Profit versus monthly interim versus six-month/annual settlement; prevent double payment (`/01`, `/05`).
3. Manual Loss: exact Investor principal/Company Running Capital and Company accounting impact, confirmation actor and closure consequences (`/01`, `/02`, `/04`, `/05`).
4. Company distributable Profit: recognition basis for Company Share, Garage Revenue/common Expenses, period close/carryforward and actual distributable amount (`/01`, `/04`, `/09`).
5. Company-level correction across Branches: exact action authority and scope (`/02`, `/10`).
6. Platform Back Office support: conditions for private Company finance read beyond explicit Company assignment (`/02`).
7. Module OFF: minimum permitted settlement actions for already-open obligations (`/02`, `/06`).

These are **BUSINESS DECISION REQUIRED** for the affected behavior, not evidence V2 ceases to be current target. The authority mismatch in repository instructions is a separate `DOC_STALE` governance issue. **UNVERIFIED:** actual tests, database, deployment, production V1 data/cutover. **CURRENT IMPLEMENTED:** only local source-inspected foundation. **PROPOSED** additional architecture: none. Evidence includes all V2 documents, old V1/legacy documents, governance/design files, current code/tests and the Git commits above.
