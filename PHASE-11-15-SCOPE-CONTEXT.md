# VIRMS: Phase 11–15 scope-setting context

This document gives a new agent enough context to **define and verify the scope** of Phases 11–15. It is not an implementation authorization or a claim that earlier phases are complete. First verify the current repository, Git state, code, and canonical documents; this snapshot was prepared on 2026-11-19 in `D:/VIRMS/tmp/phase5-investment-foundation-20261107` (`codex/phase5-investment-foundation`, HEAD `d57a9208`) with substantial local uncommitted work.

## Product and authority

VIRMS manages a vehicle investment, modification, garage, resale, and Company accounting business. It has a Main Operations system with Company/Branch roles, a Platform Back Office, an Investor Portal, and planned Owner and public/media surfaces. PostgreSQL/Django owns authenticated, tenant-scoped records and financial truth; React consumes APIs. Actual cash movements belong to Accounting. Investor Fund principal, Company Running Capital, Vehicle cost, Income/Expense, Profit, and payments are distinct concepts. Company and Branch permissions, immutable history, explicit approvals, idempotency, and corrections matter throughout.

Read `AGENTS.md`, `README.md`, relevant `docs-final-v2/` files, and the four `architecture/01`–`04` maps. `docs-final-v2/` is the approved *target*; code/migrations/tests and observed runtime establish what exists. `docs-final/`, `docs-legacy/`, and older V1 proposals are historical. The [V2 roadmap](planning/V2-DEVELOPMENT-ROADMAP.md) sets order, not detailed business rules. Mark absent or conflicting business meaning **BUSINESS DECISION REQUIRED**; do not invent it.

## What precedes Phase 11

Phases 1–3 establish identity, Company/Branch scope, roles, modules, and frontend/auth foundations. Phase 4 establishes Accounting and Cash/Bank records. Phase 5 adds Investor Fund, Vehicle identity, purchase/funding, expenses, Sale/Buyer receipt and correction links. Phase 6 adds Garage jobs and related costs/payments. Phase 7 covers Sales workflow and connected Vehicle history. Verify their actual acceptance state before using them as dependencies.

Phase 8 integrates Investor/Company finance, principal and Running Capital recovery, Profit/Loss, Interim payments, period reconciliation, Exit settlement, Company result, and Owner Distribution. Phase 9 accepts the integrated Main System across real backend workflows. Phase 10 delivers the Investor's own authorized Portal. **At this snapshot Phases 8–10 are incomplete**: capital recovery and safe refund/correction handling, final settlement, Company period confirmation/carryforward, Owner distribution records and payout, fully authoritative dashboard/detail pages, private final payable/recoverable positions, and integrated browser acceptance remain. Some local code and focused checks exist; see [Phase 8 architecture](architecture/phase-08-integrated-finance/PHASE-08-INTEGRATED-FINANCE-ARCHITECTURE.md), [Phase 9 acceptance matrix](architecture/phase-09-main-system-core/PHASE-09-CORE-ACCEPTANCE-MATRIX.md), [Phase 10 architecture](architecture/phase-10-investor-portal/PHASE-10-INVESTOR-PORTAL-ARCHITECTURE-PLAN.md), and [current handoff](CODEX_HANDOFF.md). Their dated checkpoints may be stale; inspect current code. Do not count a calculated amount as a confirmed payable or an actual payment.

## Roadmap's intended Phase 11–15 boundaries

| Phase | Intended scope | Dependency and boundary |
| --- | --- | --- |
| **11 — Owner Platform** | Authorized Owner read-only oversight and analysis of available Company information. | Begins after Investor Portal and authorized Company report/audit sources are ready. No ordinary operational or financial mutation. Owner Distribution is Phase 8 finance, not an Owner Portal write action. |
| **12 — Media and Publication Surface** | Authorized Vehicle images, public-safe fields, publication, and availability workflows. | Requires reliable Vehicle identity and an approved media/privacy boundary. Public pages must not expose private Company or Investor finance. |
| **13 — Reporting, Dashboard, Audit Refinement** | Permission-scoped reports and dashboards, audit access, and correction visibility across approved surfaces. | Needs integrated Investor, Owner, Media and core module sources. Every projection must reconcile to authoritative records and honor Company, Branch, role, and privacy scope. Do not move basic Phase 9 integration defects here merely because they appear on a dashboard. |
| **14 — Optional AI and Automation** | Approved read-only assistance or explicitly confirmed automation. | Optional/deferred until required systems and data boundaries are stable. Company-wide Automation Approval setting and explanation UI were discussed earlier; verify canonical approval, scope, and current code before placing or implementing them here. Never infer automatic financial posting authority. |
| **15 — V2 Release Readiness** | Evidence for scope completion, integration, auth/security, migrations/data, operations, and a production-release decision. | A release gate, not proof that production deployment happened. Optional/deferred scope must be recorded; unknown business decisions cannot be silently implemented. |

## Task for the next agent

1. Verify the worktree, dirty files, current roadmap and V2 documents. Reconcile stale roadmap checkpoints against code. Preserve unrelated uncommitted work.
2. Build a **scope proposal for each of Phases 11–15**, listing user journeys, backend/data/API owners, frontend surfaces, authorization/privacy, dependencies, exclusions, acceptance evidence, and actual decision gaps. Distinguish required scope from optional work. Keep Phase 8–10 obligations in their original phases.
3. Identify only **critical business questions** that block a safe architecture; present them in clear Malayalam with small examples. Do not create rules from speculation or re-ask already approved decisions.
4. Produce a compact dependency order and acceptance map. Label each claim VERIFIED FROM REPOSITORY, DOCUMENTATION TARGET, INFERENCE, UNVERIFIED, or BUSINESS DECISION REQUIRED. Do not mark Phase 11–15 complete or start implementation from a scope document alone.

Local dirty work is not transferred by copying this Markdown to another machine. Recheck the actual Git branch, source, tests and database identity there.
