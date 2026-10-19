# 17 — Cross-cutting invariants

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


This is a consolidated verification index, not a new business authority. Canonical source locations below control exact behavior; financial equations remain in canonical 01/04/05 and technical 05.

| Invariant | Canonical source | Design enforcement / verification |
|---|---|---|
| Persistent identity is immutable opaque UUID; names, phone, registration and URLs are not identity | 01 Business and identity; 04 Identity | 04 keys/FKs; identity tests |
| One global Investor and Fund may span Tenants; each Vehicle has exactly one funding Investor | 01 Business; 04 Identity | 03 scope and 04 FK/unique constraints |
| Garage is Tenant; Tenant-scoped links and object reads never cross unauthorized scope | 02 Authorization; 04 Identity; 06 Tenancy | 03 scope pipeline; cross-Tenant API/query tests |
| A User may hold explicit historical Tenant memberships; Owner combined view is only authorized union | 02 Authorization; 04 Identity | 03 backend evaluation and membership history |
| New operations are default-deny until their contract grants role/object/field scope | 02 Future modules | 03 operation registry/policy; permission matrix tests |
| Investor self-read cannot expose other Investor private data; Media/public cannot see internal finance | 02 Current roles/Public; 07 Security | 03 field scope; 07 dedicated serializers |
| Back Office can discover and read authorized finance but cannot confirm ordinary finance writes | 02 Operational; 07 Role navigation | 03/08 read routes and backend denial tests |
| Fund balances derive from source ledger, never manually entered; Profit is separate from principal | 01 Investor principal; 04 Financial truth | 04 events; 05 engine; ledger reconciliation tests |
| Available Fund, OVP, receivable and capped payables remain nonnegative under concurrency | 01 Finance; 04 Financial truth; 05 sections 1–7 | 05/11 atomic locks and constraints; race tests |
| Calculations/obligations/reserves do not create cash; one payment has one effect | 01 Sale/Loss/Corrections; 05 sections 3–7 | 05 source/event separation; invariant and chain tests |
| Actual Buyer receipts recover principal first; cumulative recovery is not reused as new cash | 01 Sale; 05 Principal Recovery | 05 allocation and source-linked Fund movement |
| Buyer excess new payment is rejected; a later correction may create an explicit refund payable | 01 Sale; 05 Sale and collection | 05 command caps; 11 Sale lock/idempotency |
| Unpaid Buyer refund excludes money from applied Sale/profit and blocks final resolution | 01 Corrections; 04 relationships; 05 sections 3–4 | 05 refund/reserve reconciliation; UI and correction tests |
| Investor share rounds first; Owner paise are nonnegative, deterministic and exactly conserved | 01 Monetary precision; 04 Financial truth; 05 section 5 | 05 single algorithm; exhaustive/property tests |
| Original percentage/configuration snapshots and historical payouts survive later changes | 01 Profit and Corrections; 04 snapshots | 04 append-only versions; 06 transitions |
| Positive Profit is eligible only after required collection/recovery; same-deal Investor payout/adjustments precede Owner payout | 01 Profit; 05 section 5 | 05 eligibility and command gates; scenario tests |
| Normal eligible Investor Profit can be paid before Exit; final remaining Principal is paid before final remaining Profit | 01 Exit; 05 section 7 | 05 settlement; 08 separate labels; E2E tests |
| Loss recognition is non-cash; Owner share requires actual same-Fund contribution | 01 Loss; 05 section 6 | 05 separate events and OVP/claim reconciliation |
| Same-side and crossover corrections reconcile net actual events to one current position without destructive rewrite or silent netting | 01 Corrections; 04 Retention; 05 section 7 | 04 chain; 05 targets; 06 protocol; property tests |
| Actual recovery, contribution, return, refund, payout and settlement cannot exceed their current authoritative cap | 01 Finance; 05 sections 3, 5–7 | 05 command contracts; 11 lock/idempotency |
| Closure waits for every unresolved principal, receivable, refund, Profit, coverage, return and correction position plus actual payments | 01 Exit; 04 Settlement; 05 section 7 | 05 global closure gate; settlement tests |
| Core Vehicle Sold and Buyer collection/publication states are distinct | 01 Vehicle/Sale; 07 UI; 08 media | 06 state machines; UI/API tests |
| Four active images maximum and exactly one Primary when active; public media requires explicit publication | 08 Scope/Publication | 09 Vehicle lock and safe projection; concurrency tests |
| Original media and R2 credentials stay private; adapter retains provider portability | 06 Storage; 08 Storage | 09 adapter/access; security/storage tests |
| Account reset never reveals password and invalidates old sessions; no public self-service reset | supporting Authentication | 03/10 session controls; auth tests |
| Tenant Merge retains original Tenant/financial history and never reposts money | supporting Tenant Merge | 16 manifest/cutover; merge validation tests |
| Local/staging/production share business behavior; readiness, backups and restore protect releases | 06 Environments/Health; supporting Production | 12/14 operations and smoke/restore gates |
| Owner AI receives minimum authorized data and cannot mutate financial truth | 02 Public and AI; 06 Security | 15 scoped adapter; disclosure/denial tests |

Explicit non-scope remains effective: no Cash/Bank operational ledger, General Garage Expense, Labour payroll/attendance/assignment, manual loss-bearer selector, early Profit payout mode, normal Tenant Merge UI, AI financial mutation, unsupported media editing/video/social features or speculative distributed infrastructure. Sources: docs-final/01 Other scope, 03 Exclusions, 06 Non-scope, 08 Out of scope.
