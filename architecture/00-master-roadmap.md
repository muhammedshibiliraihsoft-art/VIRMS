# VIRMS — Master Implementation Roadmap

**Status: HISTORICAL / SUPERSEDED V1-derived sequence. CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. Missing target behavior is an **IMPLEMENTATION GAP**; unresolved behavior is **BUSINESS DECISION REQUIRED**. The phase table below is retained for traceability, not V2 planning or authorization.

## Source Basis

### Historical V1 source basis

- `docs-final/03-system-modules.md`
- `docs-final/05-vehicle-investor-finance-workflow.md`
- `docs-final/06-technical-architecture-engineering-operations.md`
- `docs-final/supporting/production-engineering-standards.md`

### Historical System Design references

- `system-design/00-authority-and-design-contract.md`
- `system-design/02-domain-and-module-architecture.md`
- `system-design/05-financial-engine-design.md`
- `system-design/13-testing-verification-and-quality-strategy.md`
- `system-design/14-deployment-environments-and-release-design.md`

### Historical derived architecture

- The former proposal added backend/frontend foundation gates and integrated vertical slices to the V1 module progression.
- It is retained only as historical planning context; no V2 sequence is approved here.

### Business decisions

This historical roadmap resolves none. V2 open decisions are tracked in `architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.

The following phase table records a prior V1-derived proposal only. Its module ordering and any business wording are historical, not V2 target requirements.

| Phase | Purpose and major modules | Prerequisites | Major deliverable | Risk | Exit gate |
|---|---|---|---|---|---|
| 1 — Backend Foundation | Django/DRF and PostgreSQL platform, identity/authentication, roles/permissions, Tenant/object scope, application/API boundary, audit, transaction/idempotency/concurrency foundation, financial event foundation, tests and environment configuration | Frozen docs and audited System Design | Independently coherent backend foundation | High | Backend Foundation gate in `02-backend-foundation-architecture.md` passes without a frontend dependency |
| 2 — Frontend Foundation + Real Backend Integration | React shell, routing, API client, Django session integration, role-aware navigation, authorized Tenant context, shared UI states | Phase 1 gate passes | Frontend foundation verified against actual DRF authentication, authorization and Tenant-scoped response | High | Real auth → API → authorization → scoped response → loading/error/success path verified; no mock contract is authoritative |
| 3 — Investor, Fund, Vehicle and Cost | Investor Management; Investor Fund & Ledger; Vehicle Management; Vehicle Expense Management | Both foundations | Traceable principal use and one-Investor Vehicle records, delivered as integrated slices | High | Fund/OVP conservation, authorization, audit, API/UI integration and scoped command checks pass |
| 4 — Buyer, Sale and Collection | Buyer / Customer; Sales; Receivables & Payment Tracking; Principal Recovery | Phase 3 | Sold/collection separation and bounded actual receipts, integrated end to end | High | Partial/full collection, overpayment rejection, retry, concurrency, privacy and regression gates pass |
| 5 — Profit, Loss and Distribution | Profit, Loss & Distribution; allocation snapshots; Owner loss coverage and payout ordering | Phase 4 | Exact allocation and actual payout/coverage flows, integrated end to end | High | Conservation, tiny-paise, eligibility, payout order, actual contribution, audit and regression gates pass |
| 6 — Corrections, Refunds and Returns | Audit & Correction History; Buyer Refunds; Profit recovery; Owner contribution returns; linked reconciliation | Phase 5 | Correction chains and one current open position per canonical target | High | Repeated same-side/crossover corrections, no duplicate effect, liquidity and concurrency audit passes |
| 7 — Investor Exit and Settlement | Investor Exit & Settlement; global blockers; principal-first final settlement | Phase 6 | Audited Investor lifecycle and actual settlement flow | High | Global reconciliation, partial payment, closure-denial, prior-profit history and principal-first gates pass |
| 8 — Ancillary and Media | Labour; Media / Vehicle Publication; Public Vehicle Access; applicable optional tax/invoice fields | Foundations and relevant core scopes | Controlled media/publication and simple ancillary records | Standard | Upload/public privacy, four-image race, authorization, Labour boundary and real integration checks pass |
| 9 — Read Models and Administration | Dashboard; Reports; Tenant / Garage Management; User & Permission Management; Back Office; System & Business Configuration; Owner AI Assistant | Relevant source modules complete | Bounded authorized reports, administration and read-only Owner AI | High | Field-scope, read-only, AI minimization, report reconciliation, audit and regression checks pass |
| 10 — Consolidation and Release Readiness | Controlled Tenant Merge; readiness, backup/restore, migration/release hardening | Phases 1–9 and operational evidence | Reviewed consolidation procedure and release evidence | High | Merge preflight/recovery, isolation, reconciliation, restore and release smoke/audit gates pass |

Under this historical V1-derived proposal, each Phase 3+ module was expected to combine backend domain/persistence, application operation, API, frontend, real integration, authorization/Tenant scope, audit/history and relevant tests/regression. A backend-only or frontend-only module was considered incomplete under that proposal. This is not a V2 delivery requirement or implementation order.

## Future phase planning rule

For any separately authorized V2 planning task, inspect the current branch/worktree and implementation evidence, relevant `/docs-final-v2/` sources, the four living architecture maps, and only technical sections already reconciled with V2. Check the applicable BDR gates before planning affected behavior. This historical roadmap does not authorize implementation or define a V2 phase order.
