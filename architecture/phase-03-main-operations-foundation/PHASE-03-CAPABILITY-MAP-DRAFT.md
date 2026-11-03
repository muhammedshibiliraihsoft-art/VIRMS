# Phase 3 — Main Operations Foundation: Capability Map and Impact Report

**Status (2026-11-03):** SCOPE AND 14-CODE CATALOG APPROVED; MODULE-STATE FOUNDATION IMPLEMENTED AND VERIFIED LOCALLY ON DISPOSABLE POSTGRESQL; DEPLOYED RUNTIME NOT VERIFIED

**Architecture baseline:** branch `codex/audit`, HEAD `223e8191d5821e8eb6114a2c78ed710a6a33efc8`, clean when the architecture draft was prepared. The approved implementation is present on the local `codex/audit` branch; no push has occurred.

## 1. Purpose and gate

This draft turns the V2 roadmap's Phase 3 goal into a reviewable implementation boundary. It does not claim that the roadmap already defines the detailed deliverable. The approved boundary prepares the existing authenticated Company workspace to host later authorized business capabilities while preserving the approved React UI and existing route identities.

The user approved the scope in Section 10 on 2026-11-02 and authorized its implementation on 2026-11-03: versioned Company module state, authorized Platform Back Office updates through the existing Django Admin control path, a Company-scoped read contract consumed by the React workspace, later business modules, and fail-closed unconfigured state. The user approved all 13 entries in the initial catalog proposal, then explicitly approved the omitted V2 “Audit and Corrections” row as the 14th code while requiring audit history to remain retained. Audit capture and retention stay cross-cutting regardless of `audit_corrections` state. The scoped implementation and regression checks are complete locally; deployed runtime remains unverified.

## 2. Verified current baseline

- planning/V2-DEVELOPMENT-ROADMAP.md identifies Phase 3 as Main Operations Foundation after Phase 2; Accounting is Phase 4, Investment/Vehicle is Phase 5, and Garage is Phase 6. The roadmap's original NOT STARTED status was updated to IN PROGRESS on 2026-11-03 after implementation approval.
- Phase 2 provides the authenticated React shell and real Company/Branch/account context. `auth/AppRoutes.tsx` now mounts a zero-render module-state query bootstrap in the default protected workspace; the approved `App.tsx` page content remains unchanged.
- The Django URL tree now includes the read-only Company module-state route; the new versioned model, migration, scoped Admin action, command, audit/policy integration and tests are present. No Phase 3 business-domain endpoint was added.
- Phase 1 intentionally deferred persisted business-module configuration; its plan describes unknown/unsupported modules as deny-by-default. core/permissions.py currently contains only DenyByDefault.
- demo/react/src/App.tsx initializes business state from data/mockData.ts and local React state. navigationRegistry.ts already carries DataSourceStatus, defaults unbacked surfaces to demo, and the shell renders DEMO badges. This status is presentation metadata, not authorization or module availability.
- Navigation items have separate id, label, and routeKey fields. The current registry has 39 unique id values in this snapshot. routeKey is the existing runtime selection value and must remain unchanged for compatibility.
- The platform-user React path redirects to Django Admin. Existing Tenant and Branch Admin adapters are Company-scoped and use tenant command/persistence patterns; this is a current extension point, not proof that module administration already exists.
- V2 assigns Company module-state ownership to Platform Core and module administration to Platform Back Office. Module state is versioned per Company and backend-enforced. Module OFF behavior preserves authorized history and leaves non-Garage open-obligation exceptions unresolved for their owning modules.

## 3. Review reconciliation

| Review finding | Reconciled architecture rule |
|---|---|
| Phase 3 had no concrete deliverable or exit condition. | This map and the code architecture define the Phase 3 module-state deliverable and acceptance gate. The user approved scope and all 14 catalog entries on 2026-11-02 and authorized this scoped implementation on 2026-11-03. |
| Platform Core / Platform Back Office ownership was left open. | Ownership is fixed by V2: Platform Core owns Company module state; Platform Back Office administers it. The user approved the Phase 3 persistence/read/Admin foundation on 2026-11-02. |
| A generic module-OFF gate could mishandle history and open obligations. | Phase 3 will not implement business-operation exceptions for modules with no business APIs. The shared boundary must distinguish unknown/unconfigured, enabled, and disabled state; future module endpoints enforce their own approved history/open-obligation policy. |
| A single owning module per screen is invalid for overview and aggregate reports. | Module ownership attaches to a domain capability or operation, not automatically to a page or navigation group. Aggregate screens may depend on multiple modules and are outside Phase 3 live-data scope. |
| Route identity was ambiguous. | Preserve every existing routeKey string and route behavior. Use existing navigation item id only as a registry metadata key; keep label display-only. Do not rename routes or infer domain ownership from visual grouping. Detail routes continue to use their existing parent/record flow. |
| Source-status and DEMO badges already exist. | Reuse DataSourceStatus; keep DEMO separate from module enablement and authorization. Do not rebuild badges or remove them while records/mutations remain mock-backed. |
| A Company read contract without a write/initialization path is unusable. | If module state is included, use the existing Platform Back Office Django Admin control path and existing scoped admin/service conventions. Do not seed or auto-enable modules. Missing configuration is UNCONFIGURED and fails closed; product defaults are not inferred. |
| The capability map proposed a generic module gate with no Phase 3 business endpoint call-site. | Phase 3 documents the module-policy contract but does not add an unused generic enforcement helper. Each later protected business endpoint must enforce Company, module, role/action, Branch/resource/object/field scope using its approved module policy. |

## 4. Approved capability map

| Capability ID | Responsibility | Depends on | Phase 3 boundary |
|---|---|---|---|
| operations-workspace-context | Reuse the authenticated workspace, Company/Branch/account context, current role presentation, and React API/cache foundation. | Accepted Phase 2 | No new shell, layout/theme/spacing changes, or route/query-parameter renames. |
| company-module-availability | Platform Core-owned, versioned module configuration per Company, with an authorized Platform Back Office write path and a Company-scoped read contract for Main Operations. | Existing Tenant/Company scope, Platform Back Office identity, append-only audit path | Approved Phase 3 scope. All 14 catalog codes, including `audit_corrections`, are approved. Audit capture and retention remain mandatory cross-cutting behavior regardless of that code's state. No auto-seed/default-enabled business modules. A missing/unsupported state denies module operations. |
| module-policy-contract | Document the required check ordering and fail-closed semantics for future protected operations. | company-module-availability | Policy contract only in Phase 3; no unused helper or business endpoint. Each later endpoint adds the check at its real call-site and applies only its approved history/open-obligation rules. |
| capability-presentation-metadata | Keep source status and module/capability presentation metadata distinct from route identity and visual navigation groups. | Existing navigationRegistry.ts | Reuse existing item id for metadata where appropriate; preserve routeKey. Do not assign one module owner to Overview, aggregate reports, or other cross-module views. |
| shared-data-access-boundary | Reuse Django/DRF, the existing React API client and TanStack Query; scope cache entries to authenticated identity and Company, adding Branch only for Branch-scoped resources. | Existing Phase 1/2 contracts | No new global mutable business store, duplicate mock store, or generic framework. |

**Build order:** scope approved → review/lock module-state/API/Admin contracts → implement Platform Core persistence and authorized update/read path → connect the existing workspace query/cache boundary without visual or route changes → verify scope, history, cache and regression behavior. Later business modules proceed as vertical full-stack slices in their roadmap phases.

## 5. Approved Phase 3 included scope

The approved Phase 3 scope includes:

1. A Company-level versioned module-availability record owned by the existing Platform Core area (apps.tenants in the current codebase), rather than a parallel platform app/service.
2. A mutation path restricted to existing Platform Back Office control-plane authority, extending current Django Admin/tenant-command conventions. Each effective change is atomic and records actor, reason, old/new state and version/effective time using the existing append-only platform/account event path where its contract fits.
3. A read-only Company-scoped API contract consumed by the authenticated React workspace. Caller-supplied Company IDs remain selectors only; the backend resolves authorization. Module availability is Company-wide, not Branch authorization.
4. A documented backend module-policy contract: future protected operations must deny unknown or unconfigured modules and enforce module availability together with normal Company, Branch, action, object and field scope. Phase 3 has no business-operation call-site, so it adds no unused generic enforcement helper and no financial/workflow exception engine.
5. React query/cache integration for module availability and capability metadata, with no visible redesign. Existing routeKey values, navigation composition, query parameters and DEMO states remain intact.
6. Regression coverage for state versioning, Platform Back Office authorization, Company isolation, default deny, cache scope, and unchanged current role navigation/routes.

## 6. Explicit exclusions

- No Accounting, Investor/Fund, Vehicle, Garage/Job/Labour, Sales/Collections, Inventory, Company Ledger, settlement, payroll, CRM, or other business-domain workflow/model/API.
- No real dashboard/report metrics, formula changes, or dashboard-specific mock data.
- No new role, permission grant, Company/Branch authorization rule, module-OFF exception, financial formula, or initial module package/default.
- No authentication/session redesign.
- No React layout, visual, route, label, or interaction redesign. Existing surfaces stay DEMO until their records and mutations are backed by the owning backend slice.
- No migration against staging/production, deployment, commit, or push in this planning task.

## 7. Impact report for the approved scope

### Frontend and current flows

Expected React files are `demo/react/src/api/types.ts`, a new `moduleApi.ts`, `queries.ts`, `queryKeys.ts`, and `demo/react/src/auth/AppRoutes.tsx` to start the shared query in the protected workspace. `App.tsx`, `navigationRegistry.ts`, AppShell layout, page components and `mockData.ts` remain untouched. The contract is Company-scoped and cache-keyed by user and Company; Branch selection never grants access. DEMO is independent from module availability. All route keys, query parameters and visual composition are protected.

### Backend/API and ownership

Expected backend files are `apps/tenants/models/module_state.py`, its package export and additive migration, `apps/tenants/commands.py`, `primitives.py`, scoped `admin.py`/form/template files, `apps/accounts/policy.py`, `apps/accounts/audit.py`, and a read-only serializer/view/URL under `apps/tenants`. Reuse `visible_companies`; do not modify `selectors.py` or `core/permissions.py`. The read route and response contract are locked in the code architecture document. No business operation endpoint is included.

### Schema, history, migration, transaction

Persistent module state requires an additive migration. No business-record backfill is identified. Configuration history must be versioned and retained; do not overwrite/delete prior effective values. A state change and its audit event must commit atomically. The implementation design must prevent concurrent stale updates from silently replacing a newer version and make repeat/no-op submissions safe. After configuration records exist, rollback should disable the consuming code path and retain history; it must not drop populated configuration history.

### Authorization and tenant boundary

Platform Back Office write authority is established by V2 and existing scoped admin patterns. The read API must resolve the requested Company through existing backend visibility/scope selectors; a UUID is never proof of access. No new user role is proposed. Backend module state is an additional gate and never replaces role/action/object checks. Module OFF history and open-obligation actions remain governed by the owning module's approved rules.

### Old-flow and regression risks

The main risks are accidental route-key changes, treating display groups as module ownership, hiding DEMO routes because no config row exists, leaking module state across Company cache keys, using Branch selection as authorization, and treating stale client state as backend permission. Backend authorization must remain authoritative even when the frontend has stale or absent module state.

## 8. Phase 3 exit criteria

Phase 3 can be considered complete only when:

- Platform Back Office can create and version a Company module state through the approved existing control path; every change is scoped, atomic, audited and retained.
- An authorized Company workspace can read its Company module state; an unauthorized Company UUID cannot expose or mutate that state.
- The module-state read/configuration foundation returns UNCONFIGURED for absent state. Phase 3 has no business-operation API to exercise runtime module enforcement; each later protected endpoint must deny unknown/unconfigured state at its call-site and add only approved module-specific history/open-obligation rules.
- The React workspace consumes the contract without changing existing layout, route identities, query parameters, or DEMO truth labels; cache state cannot cross users or Companies.
- Existing auth, Company/Branch, role-navigation, DEMO badge and route regression remains intact.
- No Phase 4–6 business module has been pulled into Phase 3.

These criteria fill the deliverable gap in the roadmap. They do not claim that Phase 3 business workflows or runtime module enforcement exist.

## 9. Implemented files and current verification status

Backend changes in the local worktree: `apps/tenants/models/module_state.py`, `apps/tenants/migrations/0003_company_module_state.py`, module-state form/exception, scoped Django Admin history/configuration action, command/primitive, serializer/read view/URL; `apps/accounts/policy.py` and `apps/accounts/audit.py` allow only the new audited Platform action. Migration apply and empty-state reverse/reapply passed on disposable PostgreSQL; reversal is blocked when state rows exist. No business-operation module check/helper was added because no Phase 3 business endpoint exists; later modules add checks at real call-sites.

Frontend changes: typed Company-bound module-state API, strict response validation, user+Company query key and role-gated shared query; the default protected workspace mounts a zero-render bootstrap. `App.tsx`, `mockData.ts`, navigation, visible components/layout structure, and route keys remain unchanged.

Tests: `apps/tenants/tests/test_module_state.py` covers commands, audit atomicity, policy, history, DB constraints/permissions, concurrency, populated-history migration rollback protection, API scoping and Admin behavior. The combined `apps.accounts apps.tenants` suite passed **232/232** on disposable PostgreSQL 15. React passed **89/89** across 16 files; configured ESLint, TypeScript/Vite build, Django system check and migration drift check passed. Fresh migration apply and empty-state reverse/reapply passed. Vite reports the main chunk exceeds 500 kB. No shared database or deployed runtime was used.

## 10. User scope decision — approved

**Recommended:** include the Platform Core module-availability foundation in Phase 3: versioned Company state, existing Platform Back Office administration path, Company-scoped read contract, and Main Operations consumption. Keep all business modules and their operation-specific OFF/history rules for later phases. Do not pre-enable modules; an unconfigured module fails closed.

**User decisions:** on 2026-11-02, “ഉൾപ്പെടുത്താം (Recommended)” approved the recommended scope and all 13 proposed catalog entries; the user then approved “Audit and Corrections” as the 14th code and required audit history to remain retained. On 2026-11-03, the user authorized the module-state foundation implementation. `audit_corrections` controls capability availability when its owning workflow exists; it never disables mandatory platform audit capture/retention. The implementation and disposable-PostgreSQL verification are complete locally; deployed runtime remains unverified.

## 11. Evidence pointers

- Phase sequencing: planning/V2-DEVELOPMENT-ROADMAP.md, Phase 3–6.
- Platform module ownership/enablement: docs-final-v2/03-system-modules.md, Platform Core and Module enablement.
- Backend authorization and OFF behavior: docs-final-v2/02-user-roles-permissions.md, Authorization boundary and Module availability.
- Current React routes/context: demo/react/src/auth/AppRoutes.tsx, demo/react/src/auth/AuthContext.tsx, demo/react/src/App.tsx.
- Existing navigation/source status: demo/react/src/data/navigationRegistry.ts, demo/react/src/components/AppShell.tsx, demo/react/src/components/SidebarFlyout.tsx.
- Current API tree: core/urls.py, apps/accounts/urls.py, apps/tenants/urls.py.
- Current Platform Core persistence/admin/audit conventions: apps/tenants/models, apps/tenants/admin.py, apps/tenants/commands.py, apps/tenants/primitives.py, apps/accounts/audit.py, apps/accounts/models/users.py.
- Phase 1 module-state deferral: architecture/phase-01-platform-core-auth/phase-01-platform-core-auth-implementation-plan.md.
