# VIRMS — Architecture Phase Roadmap

> **Status: HISTORICAL / SUPERSEDED PROPOSAL. CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. Missing target behavior is an **IMPLEMENTATION GAP**; unresolved meaning remains **BUSINESS DECISION REQUIRED**. This V1-derived phase snapshot identifies no V2 next step and authorizes no implementation.

## Source Basis

### Historical V1 source basis

- `docs-final/03-system-modules.md`
- `docs-final/06-technical-architecture-engineering-operations.md`
- `docs-final/supporting/production-engineering-standards.md`

### Historical System Design references

- `system-design/00-authority-and-design-contract.md`
- `system-design/02-domain-and-module-architecture.md`
- `system-design/13-testing-verification-and-quality-strategy.md`
- `system-design/14-deployment-environments-and-release-design.md`

### Historical derived architecture

- The earlier proposal described Backend Foundation, integrated Frontend Foundation, then business modules and a final audit.
- That sequence and phase status are historical/proposed, not a verified V2 delivery decision.

### Business decisions

This historical roadmap resolves none. See the current open decisions in `architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.

## Where we are

The phase table below is a historical V1-derived status snapshot. It does not state the current V2 phase status or next stage. Verify current implementation from source and maps before creating any V2 phase plan.

| Stage | What it delivers | Status |
|---|---|---|
| Architecture Foundation | Earlier authority, Backend Foundation, Frontend integration and vertical-slice proposal | HISTORICAL SNAPSHOT: marked complete at the time; not V2 verification |
| Phase 1 — Backend Foundation | Earlier Django/DRF and PostgreSQL foundation proposal | HISTORICAL SNAPSHOT: listed next; current state must be read from code/maps |
| Phase 2 — Frontend Foundation + Real Backend Integration | Earlier React shell and API integration proposal | HISTORICAL SNAPSHOT: dependency proposal only |
| Phase 3+ — Integrated Business Modules | Earlier backend/API/frontend vertical-slice proposal | HISTORICAL SNAPSHOT: no V2 module order implied |
| Final — Architecture / Release Audit | Earlier security, tenancy, finance and release audit proposal | HISTORICAL SNAPSHOT: not current release status |

The business-module sequence in `00-master-roadmap.md` is historical V1 material. A V2 phase plan requires separate review against current implementation, target documents, maps and relevant BDR gates.
