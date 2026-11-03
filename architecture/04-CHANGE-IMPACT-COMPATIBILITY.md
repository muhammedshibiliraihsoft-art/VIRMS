# 04 — Change Impact & Compatibility

> Local integration state — 2026-11-02: `codex/audit` contains the accepted Phase 1/2 integration, including P2-13–P2-22 role-navigation and Investor mock-data boundary corrections. Phase 1 passed 210/210 account/tenant tests on disposable PostgreSQL; Phase 2 passed 74/74 React tests, configured lint/build, and isolated browser acceptance. Role/menu/data-boundary corrections added no business API or schema. The narrow-screen dashboard tab overflow and TopBar decorative-avatar accessibility finding were corrected without redesigning desktop hierarchy; the Vite bundle advisory is deferred. Remote remains at `f266803acd5e86caa2286fb8eae41df6cadfcb86` pending separately authorized push; staging is untouched, production proxy/cookie behavior remains unverified. Roadmap Phase 3 is Main Operations Foundation (not started); Garage is Phase 6 after Phases 4 and 5. See [roadmap](../planning/V2-DEVELOPMENT-ROADMAP.md) and [Phase 2 report](../docs/phase2-execution-progress.md).

> Phase 3 checkpoint — 2026-11-03: Company module-state model/migration, scoped Admin command, read-only metadata API and React shared query are implemented and verified locally. React passed 89/89 tests, lint and build; Django passed 232/232 account/tenant tests on disposable PostgreSQL, fresh migration apply/reversal checks and schema-drift checks. Deployment runtime remains unverified. UI pages, route identities and business workflows were not changed.

> Phase 1 corrections candidate after `cac26195`: `/auth/me` adds scoped role fields while preserving existing routes and fields. Migration 0012 adds end-time guards to four authorization history tables; it also forbids extending or removing a still-active finite end, so a new interval must use a new row. Supported Phase 1 administrative writes use parent locks for overlap prevention; no database-wide exclusion constraint is claimed. The existing legacy 0007 cutover writer-pause requirement remains. See [the execution report](../docs/phase1-execution-progress.md).

> Earlier candidate snapshot — 2026-11-01: the Phase 1 backend passed 172/172 accounts/tenants tests on disposable PostgreSQL 15.19 and preserved released migration 0007 before the subsequent B1/B2/B3 corrections. Current correction status and the final 199-test result are in [the execution report](../docs/phase1-execution-progress.md). The legacy preflight/write race requires the accepted writer pause and recovery procedure; no shared database or deployment was used.

> Correction audit: current scoped lifecycle, same-row temporal authorization, bounded uniform login admission, safe required lifecycle reasons and audit Branch scope are recorded in [docs/phase1-audit-corrections.md](../docs/phase1-audit-corrections.md). Earlier completion/test-count statements below are historical snapshots.

## 2026-10-31 verified compatibility state

Phase 1 account, Company/Branch authorization and migration safeguards are implemented through P1-19. One normal Company business User UUID is protected to exactly one Company; another Company uses an independent UUID account. Existing database rows are unverified and the migration refuses ambiguous multi-Company accounts; no auto-split is performed. Global `login_id` and email uniqueness are locked, with no Company selector. Platform technical identity remains separate. Finance/product modules and deployment remain outside this Phase 1 result.

## Historical 2026-10-31 implementation snapshot

The 2026-10-19 snapshot below is historical. The current local Phase 1 candidate has passed fresh PostgreSQL migration replay, the accounts/tenants regression, a supported legacy upgrade, explicit role/login mapping tests, restore rehearsal, audit privilege and Admin bypass tests, and bounded Company/Branch read query checks. The Phase 2 candidate separately adds React session/authentication and bounded Company/Branch context integration; it does not implement V2 finance or business modules. Evidence is in `docs/phase1-execution-progress.md` and `docs/phase2-execution-progress.md`. Initial migrations were not rewritten. Existing production history, role configuration, cleanup scheduling, staging/production runtime and deployment remain unverified.

## 0. Verification header

- Repository/worktree: `D:/VIRMS`, dirty `staging`; reviewed 2026-10-19. Tracked documentation HEAD `b4a40772edec567297e96d72bf037df73ea0cae6`; inspected backend and architecture files are untracked.
- **CURRENT APPROVED/TARGET:** V2 business architecture in `/docs-final-v2/`, selected by explicit current user direction and V2/01's historical-baseline statement. V2's marked open decisions are not supplied by this map.
- **CURRENT IMPLEMENTED:** source-inspected Phase 1 account/Tenant/Branch foundation plus the Phase 3 module-state configuration/read foundation. Phase 3 migrations and backend behavior were verified on a disposable database; persistent or deployed schema/runtime remain UNVERIFIED. **HISTORICAL / SUPERSEDED:** V1 `/docs-final/`, `/docs-legacy/` and V1-derived design assumptions. **PROPOSED:** no extra business behavior or compatibility mechanism is chosen here.
- **UNVERIFIED:** staging/production runtime and prior released data. **BUSINESS DECISION REQUIRED:** specific V2 financial/access meanings below. Governance files now use the V2 authority model; System Design bodies remain historicalized and unreconciled. See [03](03-ARCHITECTURE-CONFLICT-MAP.md).

## 1. Purpose and state classification

This map asks what a V2-target change affects and which **valid current implemented** paths must survive. Missing V2 modules are implementation gaps, not valid V1 financial flows to preserve. A documented V2 target does not mean a transaction can be implemented where V2 itself leaves its economic basis or actor undecided. No migration, adapter, dual-read/write strategy or deployment action is inferred from uninspected runtime data.

## 2. One-view change gate

```mermaid
flowchart LR
  C[V2 target change] --> A[Approved target + open decisions]
  A --> I[Current implemented evidence]
  I --> H[Historical V1 / real data check]
  H --> X[Conflict map: 03]
  X --> D[Data ownership: 01]
  X --> P[API callers: 02]
  D --> G[Scope, history + compatibility gate]
  P --> G
  G --> V[Separately authorized implementation / verification]
  V --> U[Update affected living maps]
```

The right lane is a future review sequence, not authorization to implement anything in this task.

## 3. Domain dependency and change-impact matrix

| Change area | Data/API/consumer impact | Security, history and compatibility check | State/classification |
|---|---|---|---|
| Session, role and Tenant foundation | Current auth, provision/reset/status and Tenant list/detail; future V2 client | Preserve CSRF/session, first-login gate, current role/membership denial; add Company/Branch/module/object scope without caller-ID grants | CURRENT IMPLEMENTED partial; `SECURITY_SCOPE_REVALIDATION_REQUIRED` |
| Platform→Company/Tenant→Branch | Company membership, Branch assignment/movement, enabled module, every protected route/report/cache | Company isolation, prior-Branch records, cross-Branch correction authority, module OFF obligations; inspect actual DB before migration | CURRENT APPROVED/TARGET; `PARTIAL_IMPLEMENTATION`; `CONFLICT-002/004` |
| Investor and Fund | Company-scoped Investor relationship and one Fund across that Company's Branches | Never join Funds across Companies; source-linked actual use/recovery; assess real V1 data if present | CURRENT APPROVED/TARGET; `HISTORY_PRESERVATION_REQUIRED` if data exists |
| Funded Stock Vehicle versus external Garage Vehicle | One Investor only for funded Stock; Garage Job can exist without Investment | Stable Company Vehicle identity, Branch movement, Job cost once, Investor-less external customer path | CURRENT APPROVED/TARGET; `DATA/API/UI MIGRATION` need UNVERIFIED |
| Investor capital and Company Running Capital | Exact actual source contributions/recoveries, Stock Vehicle cost, Sale | No Investor/Company money netting, no cost/recovery duplicate; full collection gate for final positive settlement | CURRENT APPROVED/TARGET; finance high risk |
| Buyer Sale/payment/refund | Company Buyer, agreed price, actual bounded receipt, refund payable and actual refund | Original events immutable; no overcollection/double Fund or Company credit, atomic cap checks | CURRENT APPROVED/TARGET; finance high risk |
| Investor positive Share and Company Share | Effective protected agreement/snapshot, Company Accounting link | Platform changes rate; Accountant confirms money; Company Share not per-deal Owner payout; avoid hard-coded 33% | CURRENT APPROVED/TARGET; actor/snapshot check |
| Company Accounting, Garage Revenue and Owner Distribution | One classified Company source/ledger, Branch attribution, period result, recipients/payments | No duplicate economic event; positive Company-level allocation exact; distributable base/recognition/period close BDR | CURRENT APPROVED/TARGET; `BUSINESS_DECISION_REQUIRED` |
| Monthly interim, reconciliation and Exit | Due/Suggested versus Paid, ordinary deal Profit history, recoverable/payable, principal-first final closure | Eligible-principal/withdrawal and period/deal inclusion BDR; never pay retained amount twice | CURRENT APPROVED/TARGET; `BUSINESS_DECISION_REQUIRED` |
| Manual Loss and correction | Negative indicator, approved impact, reason and actual linked events | No V1 formula Loss/Owner contribution; impact/confirmation/cross-Branch authority BDR | CURRENT APPROVED/TARGET; `BUSINESS_DECISION_REQUIRED` |
| Media/public and module availability | Vehicle Company/Branch scope, private R2 original, public-safe response, module state | Do not expose private finance or lose history when module OFF; minimum open-obligation actions BDR | CURRENT APPROVED/TARGET; privacy/access high risk |

Use `NO_COMPATIBILITY_IMPACT` or `LOCAL_INTERNAL_CHANGE` only after tracing actual consumers. Other possible classifications are `BACKWARD_COMPATIBLE_CHANGE`, `COMPATIBILITY_ADAPTER_REQUIRED`, `DATA_MIGRATION_REQUIRED`, `API_MIGRATION_REQUIRED`, `UI_ROUTE_MIGRATION_REQUIRED`, `HISTORY_PRESERVATION_REQUIRED`, `SECURITY_SCOPE_REVALIDATION_REQUIRED`, `BREAKING_CHANGE_APPROVAL_REQUIRED`, and `BUSINESS_DECISION_REQUIRED`. None automatically mandates a mechanism without evidence of deployed data/callers.

## 4. Valid current workflow protection

| CURRENT IMPLEMENTED path | Current entry/data/permission | Protection and evidence limit |
|---|---|---|
| CSRF → Login ID/password → Django session → `/auth/me/` | LoginAttempt throttle, active User, effective role/Tenant IDs and first-login flag | Preserve session, generic failure, password replacement and reset safety while extending V2 context. Account/tenant tests passed on disposable PostgreSQL. |
| Account provisioning | `/accounts/provision/`; atomic User/RoleAssignment/TenantMembership/AccountSecurityEvent; Back Office Owner/Accountant or Accountant Investor/Media within active Tenant membership | Preserve UUID/history and authorized temporary-credential path; reassess Platform/Company/Branch permissions for V2. Live behavior UNVERIFIED. |
| Password reset, deactivation/reactivation | Target lock, manager authority across current target roles/Tenants, history/event | Preserve out-of-scope denial and old-session safety; no assumption that Admin and API audit are identical. |
| Tenant list/detail | Allowed role and active membership-filtered active Tenant queryset; read-only API | Preserve no unauthorized Tenant disclosure; a current Tenant-only response is insufficient as complete V2 Company/Branch context. |
| Company module-state configuration/read | Platform Admin managed-Company form → locked command + `module.configure` audit; `GET /api/v1/tenants/{company_id}/module-state/` uses `visible_companies` | Immutable version history, expected-version conflicts, no Branch query authorization, fixed metadata-only response; passed PostgreSQL tests on a disposable database. |

No Investor, Stock Vehicle, Garage Job, Company Accounting, financial, public catalog or media flow is currently implemented as an end-to-end valid workflow. Business records remain demo data; the module-state React query is metadata only. Their V2 boundaries are target obligations, not legacy behavior. Record confirmed defects as `SYSTEM_DEFECT`; the module-state backend regression suite passed on disposable PostgreSQL, while deployed runtime remains unverified.

## 5. Historical V1 versus V2 target change gate

**HISTORICAL / SUPERSEDED V1:** Garage=Tenant; global cross-Garage Fund; Accountant Investor-specific rate changes; Owner Profit allocated directly per Vehicle deal; Loss allocated through Profit percentages and Owner contribution. **CURRENT APPROVED/TARGET V2:** Company=Tenant with Branches, Company-scoped Fund, Platform Back Office protected rates, exact Company Running Capital, Company Accounting, Company-level periodic Owner Distribution and manual Loss. External customer Garage work can exist without Investment. These are different ownership, permission and economic contracts, not a safe terminology swap.

`AGENTS.md`, README and older governance/roadmap documents now distinguish V2 target from current implementation and historical V1. The System Design set is explicitly historicalized, but its body has not been V2-reconciled; do not rely on it without section-level review. `CONFLICT-001` is resolved as a documentation-authority conflict; `CONFLICT-003` continues to track historical business/design differences and compatibility risk. V2 document headers still say draft/approval required, so these maps **do not claim formal final lock** or fill its BDRs. Actual V1 deployment/data/cutover need is **UNVERIFIED**. The draft statement that no production V1 transaction cutover is needed must be checked against real history before migration decisions. No dual engine, backfill, adapter or rollback method is specified here.

## 6. Frontend↔backend, schema and history compatibility

**Current frontend:** authenticated React context uses `/auth/me/`; Phase 3 adds a role-gated `module-state` API service/query keyed by user+Company and a zero-render workspace bootstrap. Business pages still read their existing demo data. **V2 target:** each future route/API client sends authenticated context; backend validates Company membership, Branch assignment, module state, role/action, object and field scope; authoritative Django transaction records one source event; response drives authorized scoped TanStack Query refresh. A UI route or hidden control is not permission. Before an API shape change, enumerate real current callers, fields, error handling and cache keys; do not copy V1 representative routes without V2 revalidation.

**Current schema:** local account/Tenant/Branch migration history plus `tenants.0003_company_module_state`; fresh apply, empty-state reverse/reapply and populated-history reverse protection were verified on disposable PostgreSQL. Persistent, staging and production migration ledgers remain unverified. Before altering Tenant identity, adding business models or moving Fund ownership, inspect actual migration state, existing rows, writers/readers, external consumers, historical data and release order. Never rewrite a released migration merely for neatness. Preserve V2 immutable financial, Job, movement, configuration and distribution source history once implemented.

**Current permission:** account/Tenant/Branch paths use existing scoped policies. The module-state read uses `visible_companies`; configuration uses the Platform-only `module.configure` action and managed-Company Admin scope. This metadata foundation does not yet enforce module state on business operations; each V2 business endpoint must add its own Company/Branch/module/action/object checks. Platform configuration authority does not confer ordinary Company finance posting; Platform private-finance support beyond explicit Company assignment is a BDR. Module OFF must retain authorized history and required open-position settlement without inventing which actions are permitted.

## 7. Regression and evidence map

| Area | Direct focused check when implemented | Transitive / current gap |
|---|---|---|
| Auth/Company/Branch/module | Existing session/CSRF, provisioning/reset, Company isolation and Branch access regressions; new module-state command/API/Admin/concurrency tests | Combined React and PostgreSQL backend regressions passed locally; no business module OFF/ON enforcement exists yet |
| Stock/Garage/Accounting | Funded Stock one Investor, external Vehicle none, Job cost/charge source, one Company receipt/economic effect | Running Capital, Company Share, Garage Revenue and reports; no current code/tests |
| Buyer/Investor finance | Positive bounded Buyer receipt/refund, actual principal/Company capital reconciliation, protected agreement snapshot | Deal Profit, interim, reconciliation, settlement and correction; BDRs for some positions |
| Owner/manual Loss | Company period approved amount and balanced-paise Owner allocation; specifically authorized actual payments; manual Loss no auto-allocation | Historical snapshots, correction and actual recovery; distributable/impact authority BDR |
| Media/public | Four active images, private original, Company/Branch field scope and safe public schema | Branch movement, module state and publication cache; no current code/tests |
| Migration/release | Fresh migration replay, actual upgrade path, backup/restore, health/readiness | Database and deployment UNVERIFIED; no cutover claim |

Future high-risk work follows current target and current implementation → previous verified behavior where relevant → `CONFLICT-` check → Data/API/consumer/security/history impact → business decision and approval gate → separately authorized implementation → focused and transitive verification → only affected map/current-state updates. No test or deployment action is performed by this documentation change.

## 8. Remaining conflicts, decisions and verification

- `CHANGE-RISK-001` **A:** unreconciled V1-derived System Design body content can reintroduce wrong V2 ownership/finance rules (`CONFLICT-003`). It is historicalized; require section-level V2 and implementation review before relying on it for a phase.
- `CHANGE-RISK-002` **A for business routes:** Company/Branch foundations and Company module-state metadata are now source-implemented, but no business endpoint consumes module state yet (`CONFLICT-002`); building financial routes on Tenant-only checks would be unsafe.
- `CHANGE-RISK-003` **A for affected actions:** monthly eligible-principal and withdrawal, period/deal reconciliation, manual Loss impact/actor, Company distributable amount/period close, cross-Branch correction, Platform support private read and module-OFF minimum settlement actions are **BUSINESS DECISION REQUIRED** (`CONFLICT-004`).
- `CHANGE-RISK-004` **B:** source untracked and runtime/data history **UNVERIFIED** (`CONFLICT-005`); do not assume empty production or an existing V1 cutover.

Evidence: all 13 V2 documents, particularly 01/02/04/05/06/09/10 and supporting standards; historical V1 and legacy documents; current `core/`, `apps/accounts/`, `apps/tenants/`, migrations and tests; repository governance and V1-derived design; Git documentation history. **CURRENT IMPLEMENTED:** source inspected only. **CURRENT APPROVED/TARGET:** V2 intent, with BDRs. **HISTORICAL / SUPERSEDED:** V1 business shape. **PROPOSED:** no new business rules. **UNVERIFIED:** tests, DB, API runtime, frontend integration, deployment and prior production data.
