# Phase 3 — Main Operations Foundation: Code Architecture Draft

**Architecture status:** `PHASE_3_CODE_ARCHITECTURE_READY_FOR_IMPLEMENTATION`.
**Implementation status (2026-11-03):** the approved module-state foundation is implemented and verified locally on disposable PostgreSQL. React, backend regression, fresh migration, empty-state reverse/reapply, and populated-history reverse protection passed. No staging/production runtime was used or verified.

**Repository snapshot:** `D:/VIRMS/tmp/audit-consolidation-20261102`, branch `codex/audit`, HEAD `223e8191d5821e8eb6114a2c78ed710a6a33efc8`. The architecture and implementation are maintained on the local `codex/audit` branch; no push or deployment has occurred.

## 1. Scope and authority

The approved Phase 3 scope is the smallest Platform Core foundation that makes Company module availability configurable and readable:

1. Persist versioned module state against the existing Company identity (`apps.tenants.Tenant`).
2. Allow only an authorized Platform Back Office operator to change it through the existing Django Admin control plane and tenant command/persistence conventions.
3. Expose a read-only Company-scoped DRF projection and consume it from the authenticated React workspace.
4. Treat absent configuration as `UNCONFIGURED`; it must never imply enabled.
5. Keep Accounting, Investment, Garage, Vehicle, Sales, Inventory, Receivables, Payroll, CRM and other business workflows for their roadmap phases.

The design was approved for implementation on 2026-11-03. Existing React pages, layouts, styles, route keys, query parameters and DEMO behavior remain frozen. Authentication redesign, new roles, company/branch policy expansion, automatic defaults and module-specific history/open-obligation exceptions are out of scope.

## 2. Evidence labels and verified baseline

- **VERIFIED_FROM_REPOSITORY at design baseline (2026-11-02):** Phase 3 was `NOT STARTED`; the roadmap names it Main Operations Foundation but does not define code-level deliverables. Phase 4 is Accounting, Phase 5 Investment/Vehicle, and Phase 6 Garage. The roadmap status was updated to `IN PROGRESS` on 2026-11-03 after implementation approval.
- **VERIFIED_FROM_BACKEND:** `Tenant` is the Company identity, has UUID identity, and is referenced by `Branch.tenant`. `Tenant` deletion is already protected by existing foreign keys and Platform Admin offers no delete path.
- **VERIFIED_FROM_BACKEND:** The backend is a Django 5.2 + DRF modular monolith. Existing URLs are rooted at `/api/v1/auth/` and `/api/v1/tenants/`. Tenant reads use `IsAuthenticated` plus `visible_companies`; Branch reads use `visible_branches`.
- **VERIFIED_FROM_BACKEND:** `apps.tenants.commands` uses locked actor rows, a locked Company row, `require_action`, and private persistence primitives. Primitives require an atomic block, validate models, and write `AccountSecurityEvent` in the same transaction.
- **VERIFIED_FROM_BACKEND:** `AccountSecurityEvent` is append-only. Its action and metadata keys are strict allowlists. `require_action` denies any non-null `module` today and rejects unknown actions. `PLATFORM_ACTIONS` is the existing Platform Back Office action allowlist.
- **VERIFIED_FROM_BACKEND:** Audit immutability is enforced beyond model methods: `apps/accounts/migrations/0003_audit_immutability.py` installs a PostgreSQL UPDATE/DELETE trigger and revokes UPDATE/DELETE/TRUNCATE from PUBLIC; current tests exercise raw SQL UPDATE and queryset DELETE denial.
- **VERIFIED_FROM_BACKEND:** `managed_companies()` limits Django Admin scope to Companies where the active Platform Admin has current membership. Existing `TenantAdmin` and `BranchAdmin` are scoped adapters; `save_model` delegates to commands rather than performing ordinary direct model writes.
- **VERIFIED_FROM_DATA_FLOW:** The React `App` still owns mock business records in local state initialized by `mockData.ts`. The shared `requestApi` client, React Query client, auth Company context, and user/Company query-key pattern already exist. `AuthContext` cancels/removes non-auth cache on identity/scope changes.
- **VERIFIED_FROM_REPOSITORY:** Navigation has separate `id`, display `label`, `routeKey`, and `DataSourceStatus` (`backend` / `demo`). `routeKey` is used as runtime selection identity. Aggregate Dashboard/Reports views span modules. DEMO is data-source truth, not module configuration or permission.
- **DOCUMENTATION_CLAIM:** V2 assigns module-state ownership to Platform Core, configuration authority to Platform Back Office, requires versioned Company configuration, and makes backend enforcement authoritative. It does not define a generic Phase 3 open-obligation exception.
- **INFERENCE:** With no Phase 3 business-operation endpoint, a reusable access helper would have no real call-site. Phase 3 should establish the state and policy contract but should not ship an unused generic helper or claim that business operations are already module-gated.

Evidence pointers: `planning/V2-DEVELOPMENT-ROADMAP.md`; `docs-final-v2/02-user-roles-permissions.md`; `docs-final-v2/03-system-modules.md`; `apps/tenants/models/tenant.py`; `apps/tenants/selectors.py`; `apps/tenants/admin_scope.py`; `apps/tenants/admin.py`; `apps/tenants/commands.py`; `apps/tenants/primitives.py`; `apps/accounts/policy.py`; `apps/accounts/audit.py`; `apps/accounts/models/users.py`; `core/urls.py`; `demo/react/src/auth/AppRoutes.tsx`; `demo/react/src/auth/AuthContext.tsx`; `demo/react/src/api/*`; `demo/react/src/data/navigationRegistry.ts`.

## 3. Ownership and exact boundaries

| Concern | Owner in current architecture | Phase 3 boundary |
|---|---|---|
| Company identity and module configuration | `apps.tenants` (Platform Core) | Add one Company-scoped revision model; do not create a second Company/Tenant identity or new Django app. |
| Branch identity and scope | `apps.tenants.Branch` and existing selectors/policy | Module configuration is Company-wide. No Branch FK, Branch query parameter, or Branch-based authorization is added. Selecting a Branch never authorizes access. |
| Policy/action authorization | `apps.accounts.policy.require_action` | Add one narrowly named `module.configure` Platform action for the admin command. Do not add roles or broaden Company business roles. |
| Audit | `apps.accounts.audit.record_event` and append-only `AccountSecurityEvent` | Extend its allowlists and reuse it as the authoritative configuration-change audit. Do not create another audit ledger. |
| Admin adapter | `apps.tenants.admin` | Use a protected custom Django Admin action/view that calls a command. Keep configuration revision rows read-only and non-deletable in ordinary Admin CRUD. |
| Read API | `apps.tenants.views` / serializers / URLs | Read-only DRF projection under the existing Tenant route prefix; use the same visible-Company selector as Company metadata reads. |
| Workspace API/cache | `demo/react/src/api` and React Query | Add one typed read query keyed by authenticated user and Company. Do not create a second mutable business-data store. |
| Business records and operations | Later owning modules | No business model, posting, financial calculation, mutation endpoint or module-specific OFF exception in Phase 3. |

## 4. Company module catalog and state semantics

Store only explicit `ENABLED` or `DISABLED` revisions. `UNCONFIGURED` is represented by the absence of any revision for that Company/module pair; it is not a database state row. There are no default rows, seed-time enables or implicit defaults. All three states are returned by the read projection. Unknown codes are not in the catalog and fail closed in admin validation and any later operation policy.

The module catalog is a single explicit backend allowlist, using stable machine codes rather than labels. On 2026-11-02, the user approved all 13 entries presented in the initial catalog proposal and then approved the omitted V2 Audit and Corrections row as the 14th code. The codes below are stable lower-snake-case identifiers derived one-to-one from those approved labels; they are identifiers, not new business meanings:

| Candidate code | V2 module/capability label |
|---|---|
| `accounting` | Accounting |
| `investment` | Investment |
| `garage` | Garage |
| `investor_portal` | Investor Portal |
| `vehicle_management` | Vehicle Management |
| `vehicle_expense_management` | Vehicle Expense Management |
| `sales_receivables` | Sales and Receivables |
| `media_vehicle_publication` | Media / Vehicle Publication |
| `public_vehicle_access` | Public Vehicle Access |
| `labour` | Labour |
| `reports_dashboard` | Reports and Dashboard |
| `audit_corrections` | Audit and Corrections |
| `gst_tax_invoice` | GST / Tax / Invoice capability |
| `owner_ai_assistant` | Owner AI Assistant |

`platform_core` is excluded because it hosts identity, scope, authorization and this configuration control plane; making the platform boundary tenant-toggleable would be unsafe. Platform Back Office remains the configuration authority, not a Company module code. Do not add visual navigation groups, DEMO status, report cards, or Branch names as module codes. No cross-module enablement dependency matrix is defined in Phase 3.

The user approved `audit_corrections` as a Company module-state code. This state controls availability of the Audit and Corrections capability when its owning workflows are implemented. It never controls whether platform audit events are captured or retained: `AccountSecurityEvent` and other required append-only audit/history remain cross-cutting and recorded regardless of this code's state. Access to audit information still follows existing permission boundaries. A later owner must define any capability-specific OFF exceptions before exposing correction operations; Phase 3 adds no correction workflow or exception engine.

Only immediate server-time changes are in this design. The Admin caller cannot submit an arbitrary effective timestamp. A need for scheduled/future-dated module changes requires a separate explicit decision and a changed temporal model.

Configuration means “Company has set this module state”; it does not assert that all UI surfaces or APIs for that module have been implemented. An `ENABLED` state alone never creates a business endpoint, grants a role, or authorizes an operation.

## 5. Model and relationship design

Add `CompanyModuleState` under `apps/tenants/models/module_state.py`, exported by `apps/tenants/models/__init__.py`.

| Field | Type / rule |
|---|---|
| `id` | UUID primary key inherited from `TimestampedUUIDModel`; immutable identity. |
| `tenant` | `ForeignKey(Tenant, on_delete=PROTECT, related_name="module_states")`; this is the existing Company identity. |
| `module_code` | `CharField(max_length=40)` backed by the approved explicit module catalog. |
| `state` | `CharField(max_length=8)` with explicit `enabled` / `disabled` choices only. |
| `version` | Positive integer with a database check `version >= 1`; starts at 1 per Company/module pair and increases by one per effective change. |
| `effective_from` | Server-generated timezone-aware timestamp for the immediate state transition. Each next revision's start time is the previous revision's exclusive end; the current revision has an implicit open end. |
| `changed_by` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT)` identifying the Platform Back Office actor for this revision. |
| timestamps | `created_at`, `updated_at` from the existing UUID/timestamp base. Revision rows are append-only; both timestamps remain creation metadata. |

There is no Branch FK and no duplicate Tenant/company UUID. `Tenant` and actor use `PROTECT` so historical configuration cannot disappear through normal relational deletion. `AccountSecurityEvent` remains the source for reason and before/after audit details; do not duplicate the reason as a second independently editable field on the state row.

Database invariants:

1. Unique `(tenant, module_code, version)` for all revisions.
2. Check `version >= 1`, `state` is one of the stored states, and `module_code` is in the approved 14-code catalog. Adding a module later requires a reviewed catalog/schema migration.
3. No `CASCADE`, delete action, or Admin edit path for historical revisions. Reject row `UPDATE`/`DELETE` with a PostgreSQL trigger and revoke `UPDATE`, `DELETE`, and `TRUNCATE` from PUBLIC, following the existing audit-immutability convention. The supported write is `INSERT` only. Add a model-level `save()`/`delete()` guard for ordinary ORM paths as defense in depth. The actual runtime database role and its ownership/inherited grants must be verified before rollout; repository settings configure a DB user but do not prove its deployed privileges.

The model is append-only: current state is the greatest version for a Company/module pair; there is no mutable current pointer and no stored `effective_until`. A later row's `effective_from` derives the prior interval's exclusive end. The command is the only supported insert path, locks the Company row, assigns `MAX(version)+1`, and requires `now > previous.effective_from`; same-time/backdated writes fail with a retryable conflict. The unique revision key protects concurrent duplicate versions. No future scheduling is in this design; the Admin caller cannot submit an arbitrary effective timestamp. A need for scheduled/future-dated module changes requires a separate explicit decision and a changed temporal model.

## 6. Mutation path: Admin → command → primitive → database + audit

There is no DRF write endpoint in Phase 3. The mutation path is:

`Django Admin authenticated POST + CSRF` → scoped Admin view/form → `apps.tenants.commands.set_company_module_state(...)` → fresh actor check and `require_action(..., "module.configure", company=tenant)` → `apps.tenants.primitives._set_company_module_state(...)` → version rows + `record_event(action="module.configure", ...)` in one atomic transaction.

Admin adapter design:

- Add a Company module-state history ModelAdmin. Its queryset is restricted to `managed_companies(request.user)`; view is Platform Admin only; standard add/change/delete are disabled.
- Add a small custom Admin configuration view (not a React page) that first selects a managed Company and a catalog code, then shows current state/version and a desired state plus required reason. The form has a server-rendered `expected_version`; it is not an authorization token.
- Reject cross-Company UUIDs, unsupported codes, empty/overlong reason, missing state, malformed version and direct edit/delete attempts. Use existing Django Admin CSRF and permission wrappers.
- The custom view never calls `CompanyModuleState.save()` directly. It only invokes the command. The record list is read-only history.

Command sequence:

1. Enter `locked_users(actor.pk)` to use the existing fresh-user/transaction locking convention; reject stale actor credentials/epoch as existing tenant commands do.
2. Lock the requested `Tenant` with `select_for_update()` and call `require_action` for `module.configure`. This action belongs in `PLATFORM_ACTIONS`; the existing policy still requires a current Company membership, active Platform identity, and active Company. Do not exempt suspended Companies without an approved rule.
3. Validate `module_code` against the catalog and `state` against the two persistent states. Require a non-empty reason within the current audit bound (500 characters).
4. Read the latest `CompanyModuleState` row, if present, after the Company lock. If the desired state already equals the current state, return a semantic no-op: no new version, timestamp, or audit event. This makes retries/repeated submissions duplicate-safe.
5. If the desired state differs, compare `expected_version` with the latest version (0 when unconfigured). A stale mismatch returns an Admin conflict and writes nothing. This prevents an old form from silently overwriting a newer operator decision.
6. Generate `now` on the server. Insert a new immutable row with `version = previous version + 1` (or 1), `effective_from = now`, and `changed_by = actor`. Never update or delete the prior version.
7. In the same atomic transaction, write one append-only `AccountSecurityEvent`: action `module.configure`, Company=Tenant, resource=new revision, actor, reason, request ID, and scalar metadata `{module_code, previous_state, new_state, version, effective_from}`. Use `UNCONFIGURED` as `previous_state` for first configuration. Extend `ACTIONS` and `METADATA_KEYS` only for these exact values.
8. Return the persisted revision to the Admin adapter. A failure at any step rolls back the insert and event together. Convert stale/known uniqueness races to a controlled conflict only after rolling back to a savepoint/transaction; never continue using a broken transaction.

Concurrency/idempotency: Company row lock serializes module-state writes for one Company using existing lock conventions; the latest revision is read after obtaining the lock and the unique revision key is defense in depth. Same-target duplicate POST is a no-op. Stale different-target POST conflicts. No additional idempotency table/key is needed for this set-state command. `X-Request-ID` is correlation only, not authorization or idempotency. Do not serialize or lock other Companies.

## 7. Authorization and tenant/Branch rules

- **Write:** Platform Back Office only, using existing `is_platform_admin_actor`, `managed_companies`, current membership and `require_action`. Add `module.configure` to the explicit Platform action allowlist. Do not let `is_staff`/`is_superuser` alone grant Company access.
- **Admin scope:** `CompanyModuleStateAdmin.get_queryset` and Company selector use only `managed_companies`. An actor authorized for one Company cannot choose or infer another Company's state through a crafted UUID.
- **Read:** use the existing Company-read projection contract: `visible_companies(request.user).filter(pk=company_id)` before fetching module rows. The existing selector handles current Company membership and role/Branch visibility. A non-visible Company returns the same 404 behavior as existing Tenant detail/Branch scope, avoiding UUID enumeration. Do not add a Branch selector; state is Company-wide.
- **No permission expansion:** no new Company role or branch-level grants. API read stays metadata-only and does not include financial data or private audit reason. Normal module operations remain inaccessible because Phase 3 adds no business operations.
- **Future enforcement contract:** every later protected operation must authorize current Company and relevant Branch/resource/object/field scope, then require the owning module to be registered and configured `enabled`, then check its existing role/action policy. Unknown/unconfigured/disabled fails closed for ordinary new operations. Historical reads and open-obligation actions are decided by each owning module under approved V2 rules. Do not add a generic exception engine here.

This is a policy contract only. Current `require_action(module=...)` rejects non-null module and stays unchanged in Phase 3 because there is no real protected business call-site. First later business slice must integrate a narrowly scoped module-availability check and tests at its actual service/API boundary before claiming runtime enforcement.

## 8. Read API contract

Add one read-only endpoint under existing Tenant routes:

`GET /api/v1/tenants/{company_id}/module-state/`

No `POST`, `PATCH`, `PUT`, or `DELETE` route is added. No query parameter is part of the contract; reject unexpected parameters (including `branch_id`) with the existing safe 400 error shape rather than treating them as authorization context. The endpoint uses `IsAuthenticated`, resolves Company via `visible_companies`, then reads only that Company's rows. Use a bounded plain DRF serializer/projection because the `UNCONFIGURED` response rows are synthesized and are not database records. The response is not paginated: its size is bounded by the approved module catalog.

Proposed response (the code values must match the locked catalog):

```json
{
  "company_id": "<uuid>",
  "modules": [
    {
      "code": "accounting",
      "state": "unconfigured",
      "version": null,
      "effective_from": null
    },
    {
      "code": "garage",
      "state": "disabled",
      "version": 2,
      "effective_from": "2026-11-02T10:30:00Z"
    }
  ]
}
```

Include one row per catalog code in stable code order. For a configured row return the greatest revision number; omit actor/reason and historical rows. History is an Admin/audit concern, not a Company workspace financial API. Use the current API error contract: 401 for unauthenticated, scoped 404 for non-visible/unknown Company, 400 for unexpected query parameters, and 405 for unsupported methods; safe error bodies include `code` and `request_id`. Unknown codes are not queried by client parameter and are absent from the catalog response.

## 9. React consumption and UI preservation

Add a typed `module-state` query using the existing `requestApi`, React Query client and `AuthContext.currentCompany`:

- `moduleApi.ts` calls only `tenants/{companyId}/module-state/` and runtime-validates the response. Use the existing safe session-cookie client.
- Query key includes `user.id` and `currentCompany.id`, e.g. `['companies', userId, companyId, 'module-state']`; no Branch key because the state is Company-wide. Do not persist this permission-adjacent metadata in local storage.
- Query is enabled only for authenticated Company context **and** when the current Company role has the existing `owner`, `accountant`, or `media` read grant represented by `hasCompanyBranchReadRole(user)`. This mirrors `visible_companies`; Investor-only context must not issue the request or receive a predictable scoped 404. Do not broaden backend visibility. Platform accounts continue using the existing `/admin/` redirect. Reuse existing auth-scope query cancellation/removal on user/Company changes. Keep the existing 30-second stale time, but override the shared client’s `refetchOnWindowFocus: false` for this query to `true`; module configuration can change in the separate Admin session. Do not add polling. Any stale value affects presentation only; backend operations remain authoritative.
- The default protected workspace in `demo/react/src/auth/AppRoutes.tsx` mounts a zero-render bootstrap that starts `useCompanyModuleStates()`; later backend-backed leaves subscribe to that same query. Keep `App.tsx` directly renderable in its existing standalone tests. The response is cached shared metadata, not a page-specific store. **Do not use it to re-label `DataSourceStatus`, remove a DEMO badge, hide/reorder any route, or change any existing page in Phase 3.** Current DEMO pages and mock interactions remain visibly and semantically DEMO.
- If module metadata is missing, unconfigured or failed to load, any future backend-backed operation affordance must fail closed. A read-query error must not globally disable the authenticated shell or existing DEMO routes. Frontend state is presentation only; the backend is authoritative.
- Do not assign a module to aggregate Overview/Reports or infer ownership from navigation groups. Future capability mapping attaches to a concrete domain operation/leaf only. Keep all `id`, `label`, `routeKey`, detail-route identities and query parameters unchanged.

## 10. Migration, rollback and compatibility

1. Add `tenants.0003_company_module_state` depending on current `tenants.0002_platform_scope` and the swappable User model. It creates only the append-only revision table, unique/check constraints, and PostgreSQL UPDATE/DELETE row trigger; it revokes UPDATE/DELETE/TRUNCATE from PUBLIC and refuses migration reversal when state history exists. A restricted runtime-role test grants only SELECT/INSERT and checks mutation/truncate denial. The unique `(tenant, module_code, version)` index supports both history lookup and reverse latest-version lookup, so do not add a duplicate index without query evidence. No other app migration is needed for the audit allowlist change.
2. Ship no data migration, module defaults, demo-to-backend migration, business-record backfill or Company/Branch rewrite. Existing Companies begin unconfigured.
3. Deploy additive schema before code that reads it. The Admin mutation and API projection are introduced after migration; old auth, Tenant, Branch and React routes remain compatible.
4. Adding a module code later requires an explicit catalog/type update and a migration that extends the code constraint. It must not auto-enable existing Companies.
5. Rollback before any state rows exist may reverse the migration after the code is disabled. After state rows/audit events exist, rollback is forward-compatible code disablement: remove/disable the Admin and API consumers but preserve the table and audit history. Do not drop populated state or remove audit action/metadata allowlist values as a rollback shortcut.
6. No production/staging migration or deployment is authorized by this architecture task.
7. Before any real-environment rollout, verify the configured application DB role is not the table owner and does not inherit `UPDATE`, `DELETE`, or `TRUNCATE` on the state/audit tables. This privilege verification is not established by the current repository configuration.

## 11. Implementation files in the current worktree

**Backend:**

- `apps/tenants/models/module_state.py`
- `apps/tenants/models/__init__.py`
- `apps/tenants/migrations/0003_company_module_state.py`
- `apps/tenants/commands.py` (new command boundary)
- `apps/tenants/primitives.py` (atomic persistence primitive)
- `apps/tenants/exceptions.py` (stale/concurrent state conflict)
- `apps/tenants/admin.py` (read-only history and scoped custom configuration view)
- `apps/tenants/admin_forms.py`
- `apps/tenants/templates/admin/tenants/companymodulestate/change_list.html` and `configure_module_state.html` for the scoped Admin entry point and expected-version submission
- `apps/accounts/policy.py` (`module.configure` only)
- `apps/accounts/audit.py` (exact action/metadata allowlist additions)
- `apps/tenants/serializers/module_state.py`, `apps/tenants/views/module_state.py`, `apps/tenants/urls.py` (read only)
- `apps/tenants/tests/test_module_state.py` (focused command, API, Admin, constraints, role-grant and concurrency cases)

**Frontend:**

- `demo/react/src/api/types.ts`
- `demo/react/src/api/moduleApi.ts`
- `demo/react/src/api/queries.ts` and `demo/react/src/api/queryKeys.ts`
- `demo/react/src/auth/AppRoutes.tsx` (zero-render query bootstrap in the default protected workspace; leave `App.tsx` and its rendered JSX/layout untouched)
- `demo/react/src/api/__tests__/moduleApi.test.ts`, `moduleQueries.test.tsx`, and the Company query-key case in `queryKeys.test.ts`

**Must remain untouched:** approved React page/component layout, styles/tokens, dashboard/report formulas, `demo/react/src/data/mockData.ts`, route paths/query parameters/`routeKey` strings, auth/session design, existing financial/business models, prior migrations, staging/production data, unrelated dirty work, and Git history.

## 12. Test architecture and current verification

Focused tests are now authored. Before the foundation is considered complete, run them in the isolated local PostgreSQL/React environments required by the repository:

### Backend model/service/transaction

- UUID identity, protected Company/actor FKs, known-code/state checks, positive version, unique version sequence, trigger rejection of revision UPDATE/DELETE, and restricted-runtime-role denial of UPDATE/DELETE/TRUNCATE.
- First configuration creates version 1 and one audit event; each transition appends the next version while preserving old rows; repeated same-state submit is a no-op with no duplicate audit.
- Missing state resolves to `UNCONFIGURED`, never enabled; unknown code is denied.
- Admin form requires a reason and `expected_version`; stale version conflicts without row/audit change.
- `record_event` failure rolls back the new revision. Module revision UPDATE/DELETE are trigger-rejected; restricted runtime roles with only SELECT/INSERT are denied module-state and audit-event UPDATE/DELETE/TRUNCATE. Database-owner behavior remains privileged and must not be confused with runtime-role behavior.
- PostgreSQL `TransactionTestCase` with independent connections proves concurrent same-Company requests serialize; one accepted transition per version, stale opposing transition conflicts. Raw SQL UPDATE/DELETE/TRUNCATE on revision rows must be rejected. Do not infer concurrency safety from SQLite or `TestCase` alone.

### Admin and DRF API

- Only current Platform Back Office actor can configure; ordinary Company roles, non-platform staff/superuser, inactive actor, expired membership, and unauthorized Company fail.
- Admin company selector/history cannot enumerate Companies outside `managed_companies`; suspended Company mutation remains denied by current policy.
- Authorized Company read returns the complete bounded catalog and current/unconfigured projection; another/non-visible Company returns 404; unauthenticated returns 401; Company B data never appears in Company A response.
- No Branch selector/query can widen scope. Read is metadata-only and no write API exists.
- Safe conflict/error output preserves request ID and does not leak internal exception text.

### React data boundary and regression

- Response parser rejects malformed IDs, state, code, version and timestamps.
- Query is disabled without authenticated Company context or an `owner`/`accountant`/`media` Company read role, keyed by user+Company, cleared on identity/Company scope changes, and refetched on focus once stale. An Investor-only Company context issues no module-state request.
- Query failure/unconfigured state is fail-closed for future backend operations but leaves existing DEMO surfaces available.
- Snapshot tests are not a substitute for checking existing route keys, role navigation, query parameters and DEMO labels remain unchanged.

### Existing workflows

- Re-run focused Phase 1 account/tenant authorization and audit regressions plus relevant Phase 2 React API/auth/navigation tests after implementation. Do not weaken any existing test.
- No Phase 3 business E2E is claimed: there is no operational module API in this slice. A later module must add its own create/read/update/reload and module-OFF scenarios before claiming backend persistence.

## 13. Acceptance criteria and explicit limits

Phase 3 module-state foundation is accepted only when:

1. The approved stable 14-code module catalog is explicit, includes `audit_corrections`, preserves mandatory cross-cutting audit capture/retention independently of that code, and rejects unknown values.
2. A Platform Back Office operator can create a version or change the current state through scoped Django Admin; Company state cannot be directly edited or deleted.
3. Each effective transition has an immutable audit event in the same transaction, with actor, Company, resource revision, reason, old/new state, version and request correlation.
4. Duplicate same-target submissions do not create duplicate versions/events; stale conflicting submissions fail without partial state.
5. No configuration rows are seeded. An absent row reads as `UNCONFIGURED` and never as enabled.
6. Company module-state API enforces existing Company visibility, has no Branch authorization shortcut, and returns only the current bounded projection.
7. React consumes the contract through the shared API/query boundary without changing approved UI, DEMO truth, route identities or `mockData.ts`.
8. The implementation does not claim module-operation enforcement until a later protected business endpoint has an actual tested policy call-site.
9. Migration is additive and reversible by code disablement while preserving populated state/audit history.

## 14. Decisions and implementation readiness

1. **14 module codes — approved:** user approved the initial 13 codes and explicitly added `audit_corrections` on 2026-11-02.
2. **Audit retention — locked:** audit capture and append-only retention remain cross-cutting and are never disabled by the `audit_corrections` state. Capability-specific OFF behavior must be defined by the owning future workflow before correction operations are exposed.
3. **Effective timing — fixed for this slice:** changes take effect at server time immediately; caller-supplied future/backdated timestamps are not supported. Scheduling would require a new product requirement and migration/API review.
4. **Suspended Companies — existing behavior preserved:** `require_action` currently denies mutation for inactive Companies. Phase 3 preserves that behavior and adds no preconfiguration exception.
5. **Module OFF operation exceptions — deferred to the owning business phase:** Phase 3 adds no business-operation endpoint. The approved V2 default deny applies; a later module must define and test only its own authorized history/open-obligation behavior before its endpoint ships. The `audit_corrections` state never disables audit capture or retention.
6. **React read-role gate — verified and locked:** `currentCompany` may exist for an Investor-only context, while `visible_companies` permits Company reads only to Owner, Accountant, and Media grants. The React query must use the existing matching role predicate and make no request for Investor-only context; no permission expansion is proposed.

The catalog decision and architecture consistency review are complete. The code-level design reached `PHASE_3_CODE_ARCHITECTURE_READY_FOR_IMPLEMENTATION`; the user then authorized the bounded implementation. The implementation and verification status are recorded below.

## 15. Implementation checkpoint — 2026-11-03

### Implemented in the local worktree

- Django: versioned Company module-state model and additive PostgreSQL migration; UUID identity; protected Company/actor foreign keys; catalog/state/version constraints; immutable revision model and database UPDATE/DELETE trigger; Platform-only `module.configure` policy action; bounded audit metadata; locked command and primitive with expected-version conflict, same-state no-op, and atomic audit write; scoped Django Admin read-only history and audited configuration form; Company-scoped, read-only 14-row DRF projection with fail-closed `unconfigured` values and private no-store headers.
- React: strict 14-code response parser tied to the requested Company identity; authenticated request service; user+Company React Query key; Company-reader role gate; zero-render query bootstrap in `auth/AppRoutes.tsx`. No visible UI, `App.tsx`, `mockData.ts`, navigation registry, route identity, or business workflow was changed.
- Tests: backend command/API/Admin/database-constraint/runtime-role/concurrency/migration-rollback tests and React API/query/workspace-bootstrap tests are present. The migration was applied to a fresh disposable PostgreSQL database; reversing it is refused when module-state history exists.

### Verification performed

- `python manage.py check` — passed against the disposable PostgreSQL configuration.
- `python manage.py test apps.accounts apps.tenants --noinput --verbosity 1` — **232 tests passed** on disposable PostgreSQL 15; this includes Phase 1 scope/auth regressions and Phase 3 command, API, Admin, concurrency, database-constraint/runtime-role and migration-protection tests.
- `python manage.py makemigrations --check --dry-run --noinput` — `No changes detected`.
- Fresh `python manage.py migrate --noinput` — all migrations applied from an empty disposable database. `python manage.py migrate tenants 0002 --noinput` succeeded while Phase 3 history was empty; migration `0003` then reapplied successfully. A backend test verifies reversal is refused and history retained when a module-state row exists.
- The full regression run exposed that a Phase 1 migration rehearsal left `tenants` at migration `0002`; its teardown now restores the latest schema so later Phase 3 tests use the complete schema.
- `npm test` — 16 files, **89 tests passed**. `npm run lint` — passed. `npm run build` — TypeScript and Vite build passed; Vite reports the main chunk exceeds 500 kB.

### Completion gate — passed locally

The approved Phase 3 foundation is implemented and verified locally against an explicitly isolated PostgreSQL database. The runtime database role used in deployment must remain non-owner with only the required runtime grants; migration-owner privileges are not runtime-role evidence. Staging/production data, deployment behavior and live browser/server integration remain unverified. No visible UI or route change occurred; push and deployment are outside this approved scope. Do not reverse migration `0003` after module-state rows exist; roll application code back while retaining the additive schema/history.
