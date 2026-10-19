# VIRMS — Architecture Authority and Delivery Model

> **Reconciliation status: PARTIALLY RECONCILED. CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. Missing target behavior is an **IMPLEMENTATION GAP**; unresolved target meaning is **BUSINESS DECISION REQUIRED**. `/docs-final/`, `/docs-legacy/` and unreconciled V1-derived design are **HISTORICAL / SUPERSEDED**. This document's earlier delivery sequence is **PROPOSED / UNVERIFIED**, not a locked V2 sequence.

## Purpose

This document records the authority distinctions and a prior technical delivery proposal. It does not lock V2 implementation sequencing, create business behavior or grant permissions.

## Source Basis

### Current V2 target sources

- `docs-final-v2/01-business-rules.md` through `10-garage-jobs-workflow.md`
- `docs-final-v2/supporting/authentication-account-security.md`
- `docs-final-v2/supporting/production-engineering-standards.md`
- `docs-final-v2/supporting/tenant-merge-consolidation.md`

### Historical System Design references

- `system-design/00-authority-and-design-contract.md`
- `system-design/01-system-context-and-boundaries.md`
- `system-design/02-domain-and-module-architecture.md`
- `system-design/07-backend-application-and-api-design.md`
- `system-design/08-frontend-and-ui-shell-design.md`
- `system-design/11-concurrency-idempotency-and-failure-design.md`
- `system-design/13-testing-verification-and-quality-strategy.md`
- `system-design/14-deployment-environments-and-release-design.md`

### Historical derived architecture proposal

- Earlier design proposed a backend foundation, then a real-backend-integrated frontend foundation, followed by full-stack module slices.
- These sequence choices are PROPOSED / UNVERIFIED for V2; current implementation status is recorded in the repository and living maps.

### Business decisions

This document resolves none. V2 decisions remain open as recorded in `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.

## Authority and evidence model

```text
CURRENT APPROVED/TARGET: /docs-final-v2/
CURRENT IMPLEMENTED:    repository source, schema and verified runtime evidence
HISTORICAL/SUPERSEDED:  /docs-final/, /docs-legacy/, unreconciled V1-derived design
LIVING MAPS:             /architecture/01-DATA-FLOW.md through 04-CHANGE-IMPACT-COMPATIBILITY.md
```

Do not infer authority from folder names, labels or Git recency alone. Explicit project intent selects V2 as the current target; V2's unresolved items remain `BUSINESS DECISION REQUIRED`. Current code does not override target rules. Unreconciled System Design and older architecture material are historical proposals, not a V2 contract. If an actual authority ambiguity remains, record `AUTHORITY CONFLICT — USER / BUSINESS CONFIRMATION REQUIRED`. Technical documents cannot invent business, financial, permission, identity, Tenant or privacy outcomes.

## Previously proposed delivery model — not locked for V2

The sequence below was derived from V1-era design work. Treat it as a technical proposal only; it is not a V2 implementation order. V2-specific phase sequencing requires separate review, especially where a slice depends on the unresolved decisions listed in the four living maps.

### Stage 1 — Backend Foundation first

Build and verify the Django/DRF and PostgreSQL platform, identity/authentication, role and permission enforcement, Tenant/resource scope, application operation boundary, API foundation, audit, transaction conventions, idempotency/concurrency approach, financial event foundation, tests and environment configuration. Backend correctness must not depend on frontend code.

### Stage 2 — Frontend Foundation with real integration

After the Backend Foundation exit gate passes, build the React/Vite shell, routing, API client, Django authentication integration, role-aware presentation, Tenant-aware context and shared screen states. Integrate against the real DRF API. A mock or independently invented contract cannot become the integration source of truth.

### Stage 3+ — Integrated business-module vertical slices

After both foundations pass their gates, build each business module end to end: approved rule and design → backend domain/persistence → application operation → API → frontend → real integration → permission/Tenant verification → audit/history → tests and regression. Do not return to a backend-for-all-modules phase followed much later by a frontend phase.

The former business-module order in `architecture/00-master-roadmap.md` is historical V1 sequencing. No V2 module order is established by this document.

## Technology and infrastructure boundary

Use the locked React 19, Vite, TypeScript, Tailwind CSS v4, React Router, TanStack Query, Python, Django, DRF and PostgreSQL stack. Authentication and authorization remain backend-controlled. Use Cloudflare R2 through the replaceable S3-compatible adapter. Local precedes Render staging; the production application host is undecided. Do not introduce the excluded frameworks or infrastructure listed in canonical engineering guidance without verified need and an approved Architecture Decision.

## Change and traceability rule

Every architecture decision must cite its canonical and System Design basis. If a proposal would change a business or permission outcome, pause architecture work for that item and have the source-of-truth process resolve it first. Future implementation plans are written one phase at a time from the current repository state.
