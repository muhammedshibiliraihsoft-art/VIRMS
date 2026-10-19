# 19 — Requirement traceability matrix

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


This matrix maps major canonical requirements to design enforcement, future implementation ownership and verification category. It is an index, not a replacement for the cited source text. Source aliases: 01–08 mean the matching numbered file under /docs-final/; AUTH = supporting/authentication-account-security.md; PROD = supporting/production-engineering-standards.md; MERGE = supporting/tenant-merge-consolidation.md. Section names identify the controlling rule. "Future module" is an implementation boundary, not a prewritten phase plan.

## Authority, business, identity and Tenant scope

| Class | Canonical source → requirement | System-design location | Future module | Verification category |
|---|---|---|---|---|
| Authority | 01 Authority; 06 Authority → canonical rules govern behavior | 00, 17 | All modules | Traceability/design review |
| Data | 03 Boundary rules → module responsibility and one financial fact source | 02, 05 | All modules | Dependency/authority review |
| Business | 01 Business and identity → external Investor capital, Owner recipients, one cycle | 01, 02 | Investor/Fund/Vehicle/Sale | End-to-end business flow |
| Identity | 01 Business; 04 Identity → immutable UUIDs; labels/phone/registration not identity | 03, 04 | Identity, Vehicle, Buyer | Model/API identity tests |
| Identity | 01 Business; 04 Identity → one funding Investor per Vehicle | 02, 04 | Investor/Vehicle | FK/constraint tests |
| Tenant | 01 Business; 06 Tenant → Garage is Tenant, count not coded limit | 01, 03, 04 | Tenant | Multi-Tenant tests |
| Tenant | 02 Authorization; 04 Identity → global Investor/Fund/User/Owner, scoped operational records | 03, 04 | Identity, Investor, Tenant | Scope/query tests |
| Tenant | 02 Authorization; 06 Tenant → explicit historical membership and authorized Owner union | 03, 04 | Identity/Tenant | Cross-Tenant read tests |
| Authorization | 02 Future modules → new resource/operation default-deny | 00, 03, 07 | Authorization | Negative permission matrix |
| Authorization | 02 Current roles/Operations → Accountant daily operational confirmation | 02, 03, 05 | Application commands | Allowed/denied command tests |
| Authorization | 02 Current roles → Owner relevant read, no normal writes | 03, 08 | Authorization/UI | Owner write denial |
| Authorization | 02 Current roles → Investor self-finance and own normal Exit request | 03, 06, 08 | Investor/Settlement | Self-scope tests |
| Authorization | 02 Operations → Media public-facing capability only, no finance/core lifecycle | 03, 08, 09 | Media/Vehicle | Field/action denial |
| Authorization | 02 Operations; 07 Role navigation → Back Office full authorized finance read, no ordinary finance write | 03, 07, 08 | Back Office | Read path/API write denial |
| Authorization | 02 Account administration → Back Office provisions Owner/Accountant; Accountant provisions Investor/Media | 03, 07 | Accounts/Admin | Provisioning scope tests |
| Authorization | 02 Account administration → Labour has no authenticated role | 03, 08 | Labour/Accounts | Login/navigation denial |
| Authorization | 02 Public and AI → public-only safe published fields | 01, 07, 09 | Public Vehicle Access | Serializer/privacy tests |
| Authorization | 02 Public and AI → Owner AI read-only in authorized scope | 15 | Owner AI | Scope/no-write tests |

## Fund, Sale, distribution and settlement

| Class | Canonical source → requirement | System-design location | Future module | Verification category |
|---|---|---|---|---|
| Financial | 01 Investor principal; 04 Financial truth; 05 §1 → one global auditable Investor Fund, no manual balance | 04, 05 | Investor Fund | Ledger reconciliation |
| Financial | 01/05 §1 → Available Fund from Gross Ledger less return/refund reserves, nonnegative even with uncovered payable | 05, 11 | Fund/Adjustment | Property/concurrency |
| Financial | 01/05 §1–4 → Used/Locked Principal and cumulative Recovered Principal distinct; redeployment not a recovery reversal | 05 | Fund/Vehicle | Fund-cycle tests |
| Financial | 01/05 §2 → purchase/approved Expense use same available Investor Fund atomically | 02, 05, 11 | Vehicle/Expense/Fund | Insufficient-fund/atomicity |
| Lifecycle | 01 Vehicle; 05 §2 → Purchased → In Work → Ready → Listed → Sold | 06, 08 | Vehicle | State transition tests |
| Data | 01 Vehicle; 04 Identity → dynamic Tenant Expense Categories and individually traceable Vehicle Expense | 02, 04, 08 | Expenses | Tenant/category tests |
| Business | 01 Vehicle → Labour Payment separate from Vehicle Labour Expense | 02, 08 | Labour/Expenses | Non-coupling tests |
| Data | 03 Dashboard/Reports → derived role-scoped views, no editable financial truth | 02, 08, 12 | Dashboard/Reports | Projection/scope tests |
| Audit/history | 03 Audit & Correction History → source-linked trace rather than silent edits | 02, 04, 10 | Audit/Correction | Event-history tests |
| Authorization | 03 Back Office/Configuration → restricted defaults and administration, separate from daily writes | 02, 03, 08 | Configuration/Back Office | Admin/write-denial tests |
| Business | 01 Sale; 04 Identity; 05 §3 → one normal Sale, Tenant Buyer, phone required/nonunique | 04, 06, 07 | Buyer/Sale | Uniqueness/scope tests |
| Financial | 01 Sale; 05 §3 → agreed price versus received cash; Sold independent of collection | 05, 06, 08 | Sale/Receivable | Partial-payment E2E |
| Financial | 01 Sale; 05 §3 → new Buyer payment positive and capped by receivable | 05, 11 | Buyer Payment | Boundary/race tests |
| Financial | 01 Sale; 04 Financial truth; 05 §3 → correction-created Refund Payable from payments, actual refunds and current price | 05, 06 | Buyer Refund | Repeated-correction tests |
| Financial | 01 Corrections; 05 §3–4 → reserve principal-backed unpaid refund, no cash creation on release | 05, 11 | Fund/Buyer Refund | Reserve/liquidity tests |
| Financial | 05 §3 → actual refund capped by current payable; latest applied receipt portions reversed first | 05, 11 | Buyer Refund | Partial/refund-order tests |
| Financial | 01 Sale; 05 §4 → actual Buyer receipt recovers OVP principal first, remainder collected Profit | 05 | Principal Recovery | Allocation tests |
| Financial | 01 Corrections; 05 §4 → reclassify original receipt without second Buyer receipt or duplicate Fund effect | 05, 06 | Principal Recovery/Correction | Correction-chain tests |
| Financial | 01 Profit; 04 Snapshots; 05 §5 → applicable Investor/Owner percentages, ranges and historical deal snapshot | 04, 05 | Configuration/Distribution | Snapshot/validation tests |
| Audit/history | 01 Profit; 02 Operational → Investor percentage change records old/new/actor/time/scope and reaches Owner notification/history | 04, 08, 10 | Investor Agreement/Notification | Change visibility/audit tests |
| Financial | 01 Profit; 04 Snapshots → current standard Owner split 48.5%/51.5% of Owners Pool, configurable by Tenant/version | 04, 05 | Configuration/Distribution | Configuration/snapshot tests |
| Financial | 01 Monetary; 05 §5–6 → INR Decimal, ROUND_HALF_UP, balanced paise and exact Profit/Loss conservation | 05, 13 | Financial engine | Exhaustive/property math |
| Financial | 01 Profit; 05 §5 → calculated, eligible, paid separate; full collection/recovery gate | 05, 06, 08 | Profit Distribution | Eligibility tests |
| Financial | 01 Profit; 05 §5 → same-deal Investor payout and adjustment resolution before Owner payout | 05, 08 | Profit Distribution | Ordering tests |
| Financial | 01 Profit; 05 §5 → actual Profit Payment positive and capped by outstanding eligible entitlement | 05, 11 | Profit Payment | Boundary/race tests |
| Financial | 01 Loss; 05 §6 → same historical split, no manual Loss bearer or positive entitlement | 05, 06 | Loss Allocation | Loss allocation tests |
| Financial | 01 Loss; 05 §6 → Investor loss recognition non-cash; actual Owner contribution into same Fund | 05 | Loss/Owner Contribution | Fund/claim tests |
| Financial | 01 Loss; 05 §6 → Owner actual contribution positive and capped by obligation | 05, 11 | Owner Contribution | Partial/excess/race |
| Financial | 01 Exit; 05 §7 → Investor Principal Claim reconciles Fund + OVP − reserves | 05, 13 | Settlement/Fund | Reconciliation tests |
| Financial | 01 Exit; 05 §7 → Principal Settlement actual payment bounded by payable and Available Fund | 05, 11 | Principal Settlement | Partial/excess/race |
| Financial | 01 Exit; 05 §7 → eligible Investor Profit may be paid before Exit and is not duplicated later | 05, 06, 08 | Profit/Settlement | Pre-Exit/retained tests |
| Financial | 01 Exit; 05 §7 → final remaining Principal first, then remaining eligible Profit, actual payments and blockers | 05, 06, 08 | Settlement | Closure/order E2E |

## Corrections, history and operational scope

| Class | Canonical source → requirement | System-design location | Future module | Verification category |
|---|---|---|---|---|
| Audit/history | 01 Corrections; 04 Retention → finalized sources immutable, linked actor/time/reason/old/new history | 04, 06, 10 | Audit/Correction | Reconstruction tests |
| Financial | 01 Corrections; 05 §7 → Net Retained Profit uses actual recovery receipts, not open obligation | 05 | Profit Recovery | Partial chain tests |
| Financial | 01 Corrections; 05 §7 → reconcile one Additional Payable or Recovery Obligation target | 05, 06 | Profit Correction | Chained-correction tests |
| Financial | 01 Corrections; 05 §7 → actual Profit Recovery positive and capped by current obligation | 05, 11 | Profit Recovery | Partial/excess/race |
| Financial | 01 Corrections; 05 §7 → same-side Loss uses original percentages, net recognition and retained Owner contribution | 05, 06 | Loss Correction | Increase/decrease tests |
| Financial | 01 Corrections; 05 §7 → Profit-to-Loss keeps payout recovery separate from new Loss obligations | 05, 06 | Correction | Crossover tests |
| Financial | 01 Corrections; 05 §7 → Loss-to-Profit reverses net recognition and returns only net retained Owner contribution | 05, 06 | Correction/Owner Return | Repeated-crossover tests |
| Financial | 01 Corrections; 05 §7 → actual Owner return positive, capped and same-Fund debit; uncovered part stays open | 05, 11 | Owner Return/Fund | Illiquidity/race tests |
| Financial | 01 Corrections; 04 Retention → post-closure correction preserves historical closure and new unresolved position | 04, 06 | Correction/Settlement | History/current-state tests |
| Audit/history | 04 Time integrity → timezone-aware meaningful timestamps | 04, 10 | Persistence/Audit | Timestamp tests |
| Lifecycle | 01 Exit; 05 §7 → normal Terms acceptance/three-month notice; Exit Requested blocks new purchase only | 06, 08 | Investor/Settlement | Exit lifecycle tests |
| Lifecycle | 02 Operations → Accountant exceptional early closure with audit; Owner read-only | 03, 06 | Settlement | Authorization/audit tests |
| Business | 01 Other scope; 03 Labour → simple Tenant Labour/manual payments, no login/payroll/assignment | 02, 04, 08 | Labour | Scope/non-coupling tests |
| Business | 01 Other scope; 03 GST/Tax → optional applicable tax/invoice data, no full tax suite | 02, 04 | Optional tax fields | Optionality tests |
| UI | 07 Shell/role navigation → approved responsive shell, role routes, Tenant context, read-only modes | 08 | Frontend shell | Responsive/role tests |
| UI | 07 UI reference baseline → pinned SGTP layout only; no copied branding/domain/rules | 08 | Frontend shell | Visual/scope review |
| UI | 07 Record details → distinguish calculated/eligible/paid, refund, contribution, corrections and settlement | 08 | Finance views | Component/E2E tests |
| Media/storage | 08 Scope → up to four active images and exactly one Primary when active | 09, 11 | Media | Concurrent upload/primary tests |
| Media/storage | 08 Upload/Storage → validate real content, preserve original, optimized variants, R2 adapter | 09 | Media/Storage | Upload/security/storage tests |
| Media/storage | 08 Publication → public only eligible published safe media; private originals inaccessible | 09, 10 | Publication/Public API | Privacy/cache tests |
| Security | AUTH Login → username/password, temporary first-login replacement, no plaintext | 03, 10 | Auth/Accounts | Login/password tests |
| Security | AUTH Recovery → admin-assisted reset, no public reset/questions, session revocation | 03, 10 | Auth/Accounts | Reset/revocation tests |
| Security | AUTH Abuse → generic login failure, rate limiting, audit without secrets | 03, 10 | Auth/Security | Brute-force/audit tests |
| Concurrency | 05 critical writes; PROD Network → atomic caps, idempotency, retries and no false success | 05, 11 | Financial commands | Parallel/retry tests |
| Performance | 06 Performance; PROD Mobile/Network → bounded API/UI, no N+1, slow-network behavior | 08, 12 | Read models/Frontend | Query/mobile measurements |
| Reliability | 06 Health/Environment; PROD Availability → readiness, backup/restore, migration/release safety | 12, 14 | Operations/CI | Readiness/restore smoke |
| Deployment | 06 Stack/Hosting; PROD Stack → locked React/Django/PostgreSQL/R2, Render staging, production undecided | 00, 14, 18 | Platform/Infrastructure | Config/deployment review |
| Deployment | 06 Delivery; PROD Stack → GitHub Actions preferred, pinned supported versions, branch governance | 14, 18 | CI/Release | Build/governance checks |
| Security | 06 Security → backend auth, CSRF/XSS/SQLi/SSRF, secrets and data minimization | 03, 10 | Security/API | Threat/penetration tests |
| Security | 06 Security; 02 AI → Owner AI minimum authorized data and no mutation | 15 | Owner AI | Disclosure/no-write tests |
| Tenant | MERGE Identity/Stages → Source/Target UUID and history retained, reviewed manifest and controlled cutover | 16 | Tenant Merge | Preflight/history tests |
| Tenant | MERGE Financial/User safety → no ledger repost, no privilege union, Source legacy access explicit | 16 | Tenant Merge | Finance/scope/retry tests |
| Explicit non-scope | 01 Other scope; 03 Exclusions; 06 Non-scope; 08 Out of scope → excluded business/media/infrastructure capabilities | 00, 17, 18 | All modules | Scope/design review |

## Coverage and change rule

All 11 canonical documents are represented above: 01–08, AUTH, PROD and MERGE. Every future phase plan must cite the subset it implements and expand test evidence against the actual repository. If a new canonical rule is approved, update its source document first, then this matrix, affected design sections and corresponding verification categories before implementation. A missing mapping is a design defect, never permission to infer behavior.
