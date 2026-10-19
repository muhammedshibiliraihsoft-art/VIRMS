# 00 — Authority and design contract

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Status: Historical V1-derived technical design; baseline commit is historical provenance only, not a V2 approval.

## Current target and evidence distinctions

1. `/docs-final-v2/` defines the current intended business and architecture direction; explicitly open items remain `BUSINESS DECISION REQUIRED`.
2. Current repository source, schema, tests and runtime evidence define what is actually implemented; they do not override the V2 target.
3. `/architecture/01-DATA-FLOW.md` through `04-CHANGE-IMPACT-COMPATIBILITY.md` distinguish target, implementation, history and unresolved items.
4. This `system-design/` set and older phase documents are historical V1-derived proposals until each affected section is reconciled and technically verified.
5. `/docs-final/` and `/docs-legacy/` are historical/superseded, not current product authority.

Do not infer authority from filenames, labels or Git recency alone. Where a technical proposal differs from V2, treat the proposal as historical and follow V2 for defined behavior. Do not invent schema, API, economic, permission, identity, Tenant or privacy details to complete a design; missing business meaning remains `BUSINESS DECISION REQUIRED`.

## Design boundary

This set specifies a provider-neutral Django/DRF and React/Vite modular monolith using PostgreSQL, backend-controlled authentication and Cloudflare R2 behind an S3-compatible adapter. It defines conceptual entities, command boundaries, projections, APIs, UI shell and operations. It contains no executable application, migrations, deployed resources or phase-specific implementation plans.

Financial formulas and reconciliation are explained once in 05-financial-engine-design.md; other design documents reference that file and the controlling sections of canonical 01, 04 and 05. Canonical documents remain the final authority for the exact financial rule. Names of tables, routes and packages here are technical design names, not new business entities or permissions.

## Change and traceability contract

- Each material design choice links to at least one canonical source in 19-requirement-traceability-matrix.md. 18-decision-register-and-adrs.md records technical choices and trade-offs.
- A change to business outcome, eligible actor, Company/Branch scope or sensitive disclosure must be recorded in the applicable V2 source document before implementation, followed by reconciliation of affected technical material and its traceability.
- Derived projections and caches are rebuildable from authoritative source events. A design decision never turns a computed balance into an independent editable value.
- Future phase plans inspect the current main/staging state, completed phases, this design, all relevant canonical documents and production engineering standards. They plan one phase, pass audit, implement and verify it, record evidence, then plan the next phase.
- Technical design revisions preserve backward traceability to the canonical source and to any implemented migration/API contract they affect.

## Requirement classes

The traceability matrix classifies business, financial, identity, Tenant, authorization, lifecycle, data, API, UI, media/storage, security, audit/history, concurrency/idempotency, performance/reliability, deployment/operations and explicit non-scope requirements. Technical sections may refine how a rule is enforced; they may not create a new rule.
