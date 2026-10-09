> ⚠️ LEGACY — NON-AUTHORITATIVE — DO NOT IMPLEMENT

> This document is retained only for historical reference.
> `/docs-final/` is the sole VIRMS implementation source of truth.
> Any older `LOCKED`, `FINAL`, or `AUTHORITATIVE` wording below is historical
> and is superseded by the current `/docs-final/` documentation.

# 06 — TECHNICAL ARCHITECTURE, ENGINEERING & OPERATIONS

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — AUTHORITATIVE TECHNICAL ARCHITECTURE & ENGINEERING SOURCE OF TRUTH

Consolidates:

- Former 06 — Branch / Tenant & Labour Architecture
- Former 09 — Performance Architecture
- Former 10 — Security Architecture
- Former 11 — AI / Automation Architecture
- Former 12 — API & Backend Architecture
- Former 13 — Deployment / Staging / Production
- Former 14 — Testing & Audit Strategy


# 1. PURPOSE

This document defines the technical boundaries and engineering rules required to implement the system safely.

It intentionally does NOT duplicate detailed business logic already defined elsewhere.

The implementation agent must use:

- 01 — Business Rules
- 02 — User Roles & Permissions
- 03 — System Modules
- 04 — Data Model & Relationships
- 05 — Vehicle / Investor / Finance Workflow
- 07 — UI / Navigation Structure
- 08 — Image & File Architecture
- Authentication / Account Security rules
- this document

together as the project source of truth.


# 2. AUTHORITY & CONFLICT RULE

Authority by subject:

| Subject | Primary Authority |
|---|---|
| Business behavior | 01 |
| Roles / permissions / tenant access | 02 |
| Module boundaries | 03 |
| Entities / relationships / data truth | 04 |
| Vehicle / investor / finance workflow | 05 |
| Technical architecture / engineering / operations | 06 |
| UI / navigation | 07 |
| Images / files | 08 |
| Login / passwords / sessions | Authentication document |

Latest explicitly locked user decision overrides older conflicting wording.

If authoritative documents genuinely conflict:

`STOP → identify conflict → request resolution`

Do not guess.


# 3. CODEX DECISION BOUNDARY

Codex may decide technical implementation details when they do not change locked business behavior.

Examples Codex MAY decide:

- internal package/folder structure
- service boundaries
- repository patterns
- serializers/controllers/views
- indexing strategy
- caching implementation
- background-job implementation
- query optimization
- retry implementation
- storage adapters
- deployment configuration
- test organization
- observability implementation
- exact technical libraries where justified

Codex MUST NOT independently decide:

- new business roles
- new financial rules
- new profit rules
- new Investor ownership rules
- new Vehicle statuses
- new loss allocation rules
- new tenant access rights
- new Owner write permissions
- new Media financial permissions
- new Labour workflows
- changes to principal/profit logic
- new business modules merely for technical convenience

If a missing decision would change business behavior, finance, authorization or ownership:

`BUSINESS DECISION REQUIRED`

Do not silently fill the gap.


# 4. REPOSITORY-FIRST IMPLEMENTATION

Before making technical architecture changes, Codex must inspect:

- actual repository structure
- existing framework
- dependencies
- existing models
- migrations
- API conventions
- authentication implementation
- tests
- environment configuration
- deployment configuration
- documentation

Prefer extending a sound existing architecture over rewriting it.

Do not introduce:

- new frameworks
- microservices
- message queues
- distributed infrastructure
- large dependencies
- new storage systems

unless actual requirements justify them.

Architecture must be:

`Simple enough now + safely extensible later`


# 5. TENANT / GARAGE ARCHITECTURE

## 5.1 Core Model

`Garage = Tenant`

Each operational Garage is represented as one Tenant.

Do not create a separate parallel `Branch` entity for the same concept.

Current operation may initially use only one active Tenant.

The architecture must nevertheless be multi-tenant from day one.


## 5.2 Tenant Identity

Tenant uses immutable backend-generated UUID identity.

Garage/Tenant name is an editable attribute, not identity.


## 5.3 Tenant Resolver

Every tenant-scoped backend operation must reliably establish:

Authenticated User
→ Explicit Tenant Assignment
→ Active Tenant Context
→ Permission
→ Resource Scope
→ Allow / Deny

A supplied Tenant UUID must never grant access by itself.


## 5.4 Tenant Isolation

Tenant isolation applies wherever relevant to:

- database access
- API queries
- Vehicles
- Expenses
- Buyers
- Labour
- Media
- Users / memberships
- reports
- search
- exports
- configuration
- cache keys
- background jobs
- notifications
- audit records

Frontend filtering is not tenant security.

Backend enforcement is mandatory.


# 6. ENTITY SCOPE SUMMARY

| Entity / Area | Scope |
|---|---|
| Tenant / Garage | System operational boundary |
| User identity | Global |
| Owner identity | Global |
| Investor | Global |
| Investor Fund | Global |
| Investor Fund movements | Global with Vehicle/Tenant context |
| Business Owner / Profit Recipient | Global |
| Vehicle | Tenant-scoped |
| Vehicle Tenant History | Historical |
| Vehicle Expense | Through Tenant-scoped Vehicle |
| Expense Category | Tenant-scoped |
| Buyer | Tenant-scoped current model |
| Sale / Buyer Payments | Tenant-scoped through Vehicle/Sale |
| Labour | Tenant-scoped |
| Labour Payment | Tenant-scoped |
| Vehicle Media | Through Vehicle |
| Tenant-specific Configuration | Tenant-scoped |

Do not duplicate a global Investor merely because the Investor operates across multiple Tenants.


# 7. USER / TENANT ASSIGNMENT

A single User identity may be explicitly assigned to one or multiple authorized Tenants where required.

Operational users must not automatically receive access to every Tenant.

Typical default:

Tenant A Accountant
→ Tenant A

Tenant B Accountant
→ Tenant B

Cross-Tenant operational access requires explicit assignment.

Tenant selection changes context only.

It does not grant permission.


# 8. OWNER ARCHITECTURE — CRITICAL

Owner is:

`VIEW + MONITOR + ANALYSE`

Owner is NOT the normal operational write user.

Owner must have complete authorized read visibility over relevant:

- Tenants / Garages
- Investors
- Investor Funds
- fund history
- Vehicles
- Vehicle capital/cost
- Vehicle Expenses
- Sales
- Buyers
- Receivables
- Buyer Payments
- Principal Recovery
- Profit / Loss
- Investor Shares
- Owners Pool
- Owner Shares
- Labour
- Labour Payments
- Investor Exit
- Settlements
- Percentage history
- financial corrections
- reports
- audit history
- operational statuses
- Media / publication information

Owner must support:

### Tenant View

View one authorized Tenant.

### Combined Business View

Aggregate/query data across all Tenants explicitly authorized for that Owner.

Combined Owner view is NOT a tenant-isolation bypass.

Every result must originate from authorized scope.


## 8.1 Owner Write Restrictions

Normal Owner account must not:

- create Vehicles
- edit operational Vehicles
- enter Expenses
- enter Sales
- record Buyer Payments
- modify Investor Funds
- perform financial corrections
- record Labour Payments
- modify normal operational records
- change protected business data unless a future explicit rule grants it

Owner read access does not imply mutation permission.


# 9. ACCOUNTANT ARCHITECTURE

Accountant / Operations Admin is the primary day-to-day operational role.

Within explicitly authorized Tenant/business scope, Accountant performs applicable:

- Investor operations
- Investor Fund operations
- Vehicle operations
- Vehicle Expenses
- Sales
- Receivables
- Buyer Payments
- Profit payout confirmation
- Investor-specific percentage management
- corrections
- Labour management
- Labour Payments
- Investor Exit
- Settlement
- Vehicle Media / publication operations

Protected Back Office configuration remains outside normal Accountant authority where already defined.


# 10. INVESTOR ARCHITECTURE

Investor identity and fund position are global.

Investor access remains self-scoped.

Investor may view approved own:

- Fund
- Available Fund
- Currently Used Fund
- Recovered Principal
- Profit Earned
- Profit Paid
- Profit Pending
- Vehicles
- Sale information
- Settlement information

Investor financial information is read-only.

Investor must never gain access to another Investor's private finance.


# 11. MEDIA USER ARCHITECTURE

Media User is limited to approved public-facing Vehicle/media functions.

Permitted areas may include:

- Vehicle images
- permitted public Vehicle details
- display information
- publication status
- permitted operational/public Vehicle status

Media must never receive internal access to:

- Investor Fund
- purchase cost
- internal Expenses
- internal Profit/Loss
- Investor Share
- Owner Shares
- settlement finance
- financial corrections
- protected configuration

Media architecture must follow 08 for images/files.


# 12. BACK OFFICE

Back Office is the system administration surface.

Responsibilities include applicable:

- Tenant creation/configuration/status
- Owner account provisioning
- Accountant account provisioning
- Tenant assignments
- protected system defaults
- protected Tenant defaults
- administrative configuration

Back Office is not the daily operational accounting interface.

Django Admin may temporarily perform system-level provisioning until Back Office exists.

Do not design daily business workflow around Django Admin.


# 13. TENANT MERGE READINESS

Tenant Merge is NOT a normal operational feature.

The normal UI must not expose a routine Merge Tenant action.

Core architecture must merely avoid making future consolidation unnecessarily impossible.

If consolidation is later required:

- define it in a separate supporting architecture
- preserve source Tenant identity/history
- preserve Vehicle origin/history
- preserve financial history
- preserve global Investor identity
- audit the operation
- plan rollback/recovery

A controlled administrative migration is acceptable if building a generic automated merge system would add disproportionate complexity.


# 14. LABOUR ARCHITECTURE

Labour is a Tenant-scoped managed entity.

Labour has:

- no login
- no dashboard
- no portal

Current Labour model stays intentionally simple.


## 14.1 Labour Operations

Accountant may:

- create Labour
- edit basic Labour details
- view Labour
- activate/deactivate Labour
- record manual Labour Payment
- enter payment amount
- enter payment date
- add optional note
- view payment history

Owner:

`full authorized read-only visibility`

Investor:

`no Labour management access`

Media:

`no Labour management access`


## 14.2 Labour Payment

Each Labour Payment is an independent historical transaction.

Typical fields derive from 04:

- Labour
- Tenant
- Amount
- Payment Date
- Optional Note
- Recorded By
- Timestamp

Payment history must remain preserved.

Deactivating Labour must not erase old payments.


## 14.3 Explicit Labour Non-Scope

Current Labour architecture does NOT include:

- fixed monthly salary
- payroll engine
- automatic salary generation
- attendance
- shift management
- Vehicle assignment
- work-type assignment
- worker-level Vehicle costing
- detailed workforce scheduling

Labour Payment must not automatically become Vehicle Expense unless an explicit separate Vehicle Expense transaction/business rule requires it.


# 15. BACKEND ARCHITECTURE PRINCIPLES

Use the repository's existing backend framework and conventions unless evidence shows they are unsuitable.

Prefer a modular monolith for the current product unless the actual repository already establishes another justified architecture.

Do not split into microservices merely for theoretical scalability.


## 15.1 Business Logic

Core domain logic must not be duplicated across:

- controllers/views
- serializers
- frontend
- reports
- AI

Centralize important business/domain operations.

Finance calculations must use authoritative records defined by 04/05.


## 15.2 Layer Responsibility

Conceptually separate:

Request/API Layer
→ Authorization / Scope
→ Validation
→ Domain / Service Logic
→ Persistence
→ Audit / Events where required

Exact classes/folders are implementation decisions for Codex.


# 16. DATABASE SAFETY

Critical financial/business writes must use appropriate transaction boundaries.

Prevent:

- partial commits
- duplicate records
- lost updates
- race conditions
- incorrect fund balance
- double Buyer Payment
- double Principal Recovery
- double Profit Payment
- duplicate Settlement

Use where appropriate:

- database constraints
- unique constraints
- transactions
- locking
- optimistic/version checks
- idempotency keys
- immutable/reversal records

Do not rely only on frontend button disabling.


# 17. FINANCIAL DATA TRUTH

Performance optimizations must never create a second editable financial truth.

Authoritative financial truth remains transaction/ledger/source-record based.

Derived values may be:

- calculated
- cached
- materialized
- summarized

only when they remain rebuildable/reconcilable from authoritative data.

Financial cache must not become dangerously stale merely for speed.


# 18. API ARCHITECTURE

APIs must use consistent conventions for:

- authentication
- authorization
- validation
- error responses
- pagination
- filtering
- sorting
- search
- UUID references
- version evolution

Do not expose database implementation details as API contracts.


## 18.1 Authorization

Every protected endpoint must perform backend authorization.

Requirements:

Authenticated
≠ Authorized

Permission checks must include relevant:

- role
- Tenant assignment
- resource scope
- object-level permission


## 18.2 Public vs Private APIs

Public Vehicle API must use a dedicated safe response schema.

Never serialize the full internal Vehicle model and depend on frontend hiding.

Public API may expose only approved public fields.

Never expose:

- Investor private data
- Investor Fund
- Purchase Cost
- Internal Expenses
- internal Profit/Loss
- Investor Share
- Owner Shares
- corrections
- internal audit
- protected configuration


## 18.3 Lists

Large datasets require server-side:

- pagination
- filtering
- sorting
- search

Do not fetch an entire growing dataset merely to filter it in the browser.


## 18.4 Dashboard / Reports

Dashboard should use purpose-built summary/query APIs where appropriate.

Do not make dashboard loading depend on downloading entire operational tables.


## 18.5 Error Model

Errors should be consistent and safe.

User-facing errors must:

- explain what failed where practical
- not expose stack traces
- not expose SQL/internal paths
- not expose credentials/secrets

Client must distinguish relevant:

- validation
- unauthorized
- forbidden
- not found
- conflict
- timeout
- server error


# 19. IDEMPOTENCY

Critical writes must remain safe when:

- user double-clicks
- browser retries
- connection drops
- proxy retries
- request result is unknown

High-risk examples:

- Investor Fund additions
- Vehicle purchase
- Vehicle Expense
- Sale confirmation
- Buyer Payment
- Principal Recovery
- Profit Payment
- financial correction
- Settlement

A repeated request must not silently create duplicate money movement.


# 20. BACKGROUND JOBS

Use background jobs only when useful.

Suitable examples:

- image processing
- large PDF/report generation
- heavy export
- notifications
- AI processing
- large maintenance tasks

Jobs should be:

- bounded
- observable
- safely retryable
- idempotent where required
- concurrency-safe
- resumable where long-running

Do not introduce a queue infrastructure when no actual asynchronous workload justifies it.


# 21. PERFORMANCE ARCHITECTURE

Primary rule:

`Fast network → fast application`
`Slow network → smart application`

Optimization must never reduce:

- business correctness
- security
- financial accuracy
- image clarity beyond practical tolerance
- tenant isolation


## 21.1 Initial Load

Display quickly:

- application shell
- route structure
- essential data/loading state

Do not wait for:

- all images
- analytics
- AI
- optional widgets
- unrelated routes

No blank white screen.


## 21.2 Frontend Code

Use where appropriate:

- route splitting
- lazy loading
- dynamic imports
- tree shaking

Users should not download/parse heavy code for functionality they are not currently using without a justified preload reason.


## 21.3 Backend Queries

For growing data:

- query server-side
- paginate
- filter in database
- sort in database
- avoid N+1 queries
- use indexes based on actual query patterns
- inspect expensive queries

Do not optimize by guess alone.


## 21.4 Caching

Cache only when it gives measurable value.

Every cache must have:

- scope
- key design
- invalidation/freshness rule

Tenant/user-specific data must never leak through shared cache keys.

Financial truth must not be hidden behind uncontrolled stale caching.


## 21.5 Media

All detailed image behavior follows 08.

Critical rule:

`Media failure is local, never global.`


# 22. PERFORMANCE MEASUREMENT

Performance must eventually be measured, not described as "feels fast."

Relevant measurements may include:

- LCP
- INP
- CLS
- frontend bundle size
- route bundle size
- API p95
- DB/query latency
- query count
- image payload
- error rate

Exact performance budgets must be established from the actual application/environment rather than invented prematurely.


# 23. LOW-END / SLOW-NETWORK STANDARD

Important flows must be validated using realistic conditions including:

- approximately 360px width
- slower CPU
- slow/3G-like network
- cold cache
- keyboard-open mobile viewport
- request interruption
- unstable network

Important UI releases should also be tested on relevant real:

- Android browser
- iPhone/iOS Safari

where practical.


# 24. FAILURE HANDLING

No normal failure may become:

- blank screen
- silent error
- infinite spinner
- lost form input
- false success
- duplicate transaction
- whole-page crash because one image failed
- unnecessary full reload

Every loading state must eventually resolve to:

- success
- empty
- validation error
- authorization error
- network error
- timeout
- server error
- controlled retry


# 25. NETWORK RESILIENCE

Every external/network request must have sensible timeout behavior.

Read operations may retry when safe.

Retries must be:

- bounded
- selective
- backoff-based where appropriate

Financial/write operations must never be blindly retried.

Navigation away from a request must not create corrupted client state.


# 26. SECURITY ARCHITECTURE

Security must be enforced server-side.

Minimum areas:

- authentication
- authorization
- Tenant isolation
- object-level permission
- server-side validation
- SQL injection protection
- XSS protection
- CSRF protection where applicable
- SSRF prevention
- secure file upload
- secret management
- rate limiting
- dependency security
- secure error handling
- auditability


# 27. AUTHENTICATION BOUNDARY

Exact:

- login mechanics
- password rules
- password reset
- session/token lifecycle
- MFA if later required
- credential recovery

belong to the Authentication / Account Security source of truth.

This document does not invent another authentication model.

Whatever authentication mechanism is implemented must integrate with backend authorization and Tenant scope.


# 28. CENTRAL AUTHORIZATION

Permission logic must not become scattered ad-hoc checks.

Conceptual model:

User
→ Role
→ Permission
→ Tenant / Scope
→ Resource
→ Allow / Deny

Frontend route hiding is UX only.

Backend/API remains authoritative.


# 29. SERVER-SIDE VALIDATION

Never trust:

- frontend validation alone
- supplied Tenant ID
- supplied role
- supplied ownership
- supplied calculated money
- uploaded filename extension
- hidden UI state

All security/business-critical input must be validated server-side.


# 30. FILE / UPLOAD SECURITY

Follow 08.

At minimum validate:

- actual MIME/file signature
- allowed type
- file size
- dimensions where relevant
- corruption
- malicious payload

Never trust extension alone.

Storage credentials must never reach the frontend.


# 31. SECRETS

Secrets must not exist in:

- source code
- committed `.env`
- frontend bundles
- logs
- API responses
- AI prompts

Use environment/secret-management mechanisms appropriate to the actual deployment platform.


# 32. RATE LIMITING

Apply rate limiting where risk warrants it, especially:

- public APIs
- authentication endpoints
- abuse-prone endpoints
- expensive endpoints

Exact limits must be determined from real requirements and traffic.

Do not invent arbitrary business limits.


# 33. AUDIT SECURITY

Important sensitive actions must retain relevant audit context such as:

- actor
- action
- timestamp
- entity UUID
- Tenant
- old/new value where appropriate
- reason where applicable
- request/correlation context where useful

Never write:

- passwords
- access tokens
- secret keys

to audit logs.


# 34. OWNER AI ARCHITECTURE

Current AI access:

`OWNER ONLY`

AI is read-only.

AI may:

- query
- summarize
- explain
- analyse

verified data the Owner is already authorized to access.

AI must not:

- create records
- update records
- delete records
- perform financial transactions
- change percentages
- change permissions
- change configuration
- bypass Tenant access


# 35. VERIFIED-DATA-FIRST AI

Required architecture:

Authorized Request
→ Deterministic Backend Query/Calculation
→ Verified Result
→ AI Explanation

AI must NOT calculate authoritative finance from unverified natural-language context.

Examples of authoritative values that must originate from deterministic application logic:

- Investor Fund
- Available Fund
- Currently Used Fund
- Recovered Principal
- Vehicle Cost
- Amount Received
- Amount Pending
- Profit/Loss
- Investor Share
- Owner Shares
- Settlement position


# 36. AI TENANT SCOPE

Owner AI may access only data already authorized for that Owner.

If Owner has multiple authorized Tenants:

AI may analyse:

- selected Tenant
- authorized combined business view

but must never expand scope beyond explicit authorization.


# 37. AI PRIVACY / FAILURE

AI requests should send only data required for the query.

Do not send:

- passwords
- authentication secrets
- unrelated private records

AI/provider failure must not block core application functions.

AI timeout/error should degrade only the AI feature.


# 38. AUTOMATION BOUNDARY

Current system does not authorize autonomous AI business actions.

Automation may perform technical/supporting tasks such as:

- background image processing
- notifications
- report generation
- controlled maintenance

but business/financial actions still obey normal permissions and workflow.

Any future write-capable AI/automation requires a new explicit business/security decision.


# 39. OBSERVABILITY

Use structured logs.

Useful safe context may include:

- request ID
- endpoint
- Tenant UUID
- safe User reference
- status
- duration
- error category

Monitor where relevant:

- slow APIs
- slow DB queries
- failed jobs
- repeated failures
- authentication failures
- image-processing failures
- elevated error rates

Never log secrets.


# 40. REQUEST / CORRELATION IDS

Requests should support a correlation/request identifier where useful.

This enables:

User reports failure
→ Reference ID
→ Developer locates corresponding logs/request path

Reference IDs must not reveal sensitive internal information.


# 41. HEALTH / READINESS

Production services should expose appropriate health/readiness behavior.

Critical dependency failure should be detectable.

Optional dependency failure should degrade locally where possible rather than crashing the entire application.


# 42. DEPLOYMENT ENVIRONMENTS

Required environment progression:

`Local / Development`
→ `Staging`
→ `Production`

Do not test dangerous schema/business changes directly against Production.


## 42.1 Local

Used for:

- development
- unit/integration testing
- migrations during development
- local verification


## 42.2 Staging

Must approximate Production sufficiently to validate:

- frontend/backend integration
- authentication
- Tenant isolation
- migrations
- environment variables
- uploads/storage
- jobs
- public API
- mobile/browser behavior
- performance regressions
- deployment behavior

Use isolated non-production data/configuration.


## 42.3 Production

Production contains live business data.

Production changes require higher verification.

Do not treat Production as a debugging sandbox.


# 43. ENVIRONMENT IDENTIFICATION

Before applying:

- migration
- destructive command
- reset
- data correction
- infrastructure change

Codex/implementation agent must establish which environment is being targeted.

Never assume a connected database/service is development.

If environment identity is ambiguous:

`STOP`


# 44. CONFIGURATION

Environment-specific values belong in controlled configuration.

Examples:

- database URL
- storage credentials
- API host
- allowed origins
- secret keys
- provider credentials
- environment flags

Do not hard-code environment secrets.

Required configuration should be documented.


# 45. DATABASE MIGRATIONS

Migrations must consider:

- forward compatibility
- existing data
- deployment order
- rollback/recovery
- locks/downtime
- destructive-change protection

Prefer safe expand/migrate/contract patterns for risky schema changes.

Do not combine unsafe destructive removal with code that still depends on the removed structure.


# 46. BACKFILL

Large data migrations/backfills should be:

- bounded
- batched
- resumable
- observable
- safe to retry where appropriate

Do not run uncontrolled full-table application loops on Production.


# 47. BACKUP & RESTORE

Production data requires backups.

A restore procedure must be known.

Important backups must be periodically verified by actual restore/testing.

A backup that has never been tested must not be blindly assumed valid.


# 48. RELEASE / ROLLBACK

A Production release must have a practical recovery path.

Where relevant:

- rollback application version
- rollback/forward-fix configuration
- migration recovery plan
- disable risky feature
- restore data only when necessary and understood

Feature flags/killswitches are useful for risky modules or difficult rollback scenarios.

Do not add flags to every trivial feature.


# 49. DEPLOYMENT PROVIDER

This document is provider-neutral.

Codex must inspect the actual connected repository/environment before choosing provider-specific configuration.

Do not invent:

- DigitalOcean
- Render
- AWS
- Cloudflare
- Supabase
- another provider

unless the real project configuration/approved decision supports it.


# 50. SOURCE CONTROL / RELEASE SAFETY

Implementation should use clean, reviewable commits/checkpoints.

Do not:

- mix unrelated changes
- commit secrets
- deploy unfinished work
- push/deploy without required project authorization

Architecture/document changes should correspond to actual accepted decisions.


# 51. TESTING STRATEGY

Testing must match risk.

Use appropriate combinations of:

- unit tests
- model/domain tests
- service tests
- API tests
- permission tests
- Tenant-isolation tests
- integration tests
- concurrency tests
- UI/component tests
- browser/end-to-end tests
- deployment smoke tests


# 52. REQUIRED HIGH-RISK TEST AREAS

High-risk areas require deeper testing:

- authentication
- authorization
- Tenant isolation
- Investor Funds
- Vehicle purchase
- Expenses
- Sales
- Buyer Payments
- Principal Recovery
- Profit calculation
- Profit payment
- financial corrections
- Investor Settlement
- migrations


# 53. TENANT SECURITY TEST MATRIX

Tests must prove examples such as:

Tenant A User
→ Tenant A resource ✅

Tenant A User
→ Tenant B resource ❌

Changing Tenant UUID manually
→ must NOT grant access

Owner authorized A+B
→ A ✅
→ B ✅
→ combined A+B ✅

Owner unauthorized C
→ C ❌

Media
→ public/media data ✅
→ finance ❌

Investor A
→ own finance ✅
→ Investor B private finance ❌


# 54. OWNER TESTS

Owner tests must explicitly confirm:

- full relevant authorized read visibility
- tenant-wise view
- combined authorized view
- filters
- report visibility
- audit/history visibility
- no normal operational create
- no edit
- no delete
- no fund mutation
- no expense entry
- no sale entry
- no financial correction

A UI-hidden write control is not enough.

Backend write attempt must also fail.


# 55. LABOUR TESTS

Test:

- create Labour by Accountant
- basic edit
- activate/deactivate
- manual payment
- different payment amounts on different dates
- optional note
- payment history preservation
- Owner read-only visibility
- no Labour login
- no attendance/payroll assumptions
- no automatic Vehicle linkage


# 56. FINANCE TESTS

Finance tests must include:

- happy path
- invalid state
- duplicate request
- concurrent request
- partial failure
- rollback
- permission denial
- Tenant denial
- history preservation

Financial tests must verify amounts, not only HTTP status.


# 57. API TESTS

For new/changed endpoints verify as applicable:

- validation
- authentication
- authorization
- object permission
- Tenant scope
- public/private schema
- pagination
- filtering
- sorting
- error shape
- rate limiting
- backward compatibility
- duplicate safety


# 58. FAILURE-PATH TESTING

Tests must cover failure paths, not only success.

Examples:

- timeout
- storage failure
- database conflict
- invalid transition
- unauthorized access
- stale state
- duplicate submit
- job failure
- image failure
- partial network interruption


# 59. PERFORMANCE TESTING

Important releases should measure relevant:

- query count
- slow queries
- API latency
- frontend bundle impact
- image payload
- core web performance
- slow-network behavior

Do not approve performance based only on a developer machine.


# 60. REGRESSION

Every meaningful change must verify that existing locked behavior still works.

No implementation is complete merely because the new feature works in isolation.


# 61. TASK-LEVEL CODEX GATE

After each meaningful implementation task, Codex should check only relevant categories.

Always consider:

- correctness
- permissions
- data integrity
- error handling
- regression
- performance impact

When API/data touched:

- validation
- authorization
- Tenant isolation
- pagination where relevant
- transactions
- indexes
- N+1
- concurrency

When finance touched:

- atomicity
- idempotency
- duplicate prevention
- audit
- history
- exact calculations

When UI touched:

- responsive behavior
- loading/error/empty states
- keyboard/mobile
- no layout break

When images touched:

Follow 08.


# 62. MILESTONE AUDIT

Do NOT run the largest audit after every tiny task.

Run broader audit at logical:

- feature milestone
- phase completion
- architecture milestone
- pre-production release
- major infrastructure/schema change

Audit relevant:

- architecture
- business-rule consistency
- permissions
- Tenant isolation
- finance
- security
- performance
- data integrity
- failure handling
- scaling
- observability
- deployment
- backup/recovery
- regression


# 63. CODEX / DEEPSEEK RESPONSIBILITY

## Codex

Primary role:

- inspect actual repository
- implement
- write/update tests
- run targeted validation
- provide evidence
- fix verified defects

## DeepSeek / Independent Auditor

Primary role:

- read-only milestone audit
- architecture review
- security review
- finance review
- performance review
- cross-module review

DeepSeek finding is NOT automatically accepted as truth.


# 64. AUDIT FINDING CLASSIFICATION

Every external audit finding must be verified against the actual repository/environment.

Classify as:

- VERIFIED — FIX
- VALID / LOW PRIORITY
- NOT REPRODUCIBLE
- AUDITOR ASSUMPTION
- BUSINESS DECISION REQUIRED

Only verified implementation defects become automatic Codex fix tasks.


# 65. EVIDENCE STANDARD

Completion should rely on evidence such as:

- tests
- command output
- query evidence
- browser verification
- logs
- migration result
- measured performance
- diff/review
- reproducible steps

Avoid unsupported statements such as:

`Looks good`
`Should work`
`Probably safe`
`Works on my machine`


# 66. PRODUCTION RELEASE GATE

Before important Production release confirm relevant:

- locked business rules preserved
- permissions correct
- Tenant isolation tested
- financial transactions safe
- migrations safe
- tests passing
- no critical known regression
- staging validation complete
- environment configuration correct
- backup/recovery available
- observability available
- rollback path understood
- security issues addressed
- important performance regression absent


# 67. GLOBAL FAILURE RULE

The following are production defects:

- blank application screen
- silent failure
- endless loading
- false success
- lost critical form input
- duplicate financial transaction
- Tenant data leakage
- permission bypass
- stale financial truth presented as authoritative
- entire page failing because an image failed
- uncontrolled destructive migration


# 68. GLOBAL ARCHITECTURE RULE

Prefer:

`clear`
`testable`
`secure`
`auditable`
`maintainable`
`appropriately scalable`

over:

`clever`
`over-abstracted`
`over-engineered`

Do not optimize for hypothetical millions of users at the cost of current system reliability.

Do not hard-code current counts of:

- Tenants
- Users
- Investors
- Vehicles
- Buyers
- Labour
- Images

except explicit business limits such as the current Vehicle image limit defined by 08.


# 69. CURRENT NON-SCOPE

Do not introduce through technical architecture:

- Dedicated Cash/Bank module
- General Garage Expense module
- Payroll engine
- Attendance
- Labour Vehicle assignment
- Labour work-type tracking
- worker-level Vehicle costing
- Full CRM
- separate Loss Allocation system
- routine Tenant Merge
- write-capable AI
- autonomous financial AI
- unnecessary microservices
- unnecessary distributed infrastructure


# 70. IMPLEMENTATION AGENT OPERATING RULE

When Codex begins implementation:

1. Read relevant authoritative docs.
2. Inspect actual repository.
3. Inspect actual environment before mutations.
4. Identify existing implementation.
5. Reconcile code with locked rules.
6. Choose the smallest sound technical design.
7. Do not redesign working architecture without evidence.
8. Implement only supported behavior.
9. Add/update appropriate tests.
10. Validate relevant permissions/Tenant/finance/failure cases.
11. Report evidence and remaining issues.
12. If a genuine business decision is missing, STOP and report it instead of guessing.


# 71. NON-NEGOTIABLE INVARIANTS

1. Garage = Tenant.
2. Multi-Tenant architecture exists from day one.
3. Tenant isolation is backend-enforced.
4. Tenant assignment is explicit.
5. Owner has full authorized business read visibility.
6. Owner is operationally read-only.
7. Owner supports tenant-wise and combined authorized views.
8. Investor identity is global.
9. Investor Fund is global.
10. Vehicle remains Tenant-scoped.
11. Accountant is the main operational write role.
12. Media has no internal financial access.
13. Labour has no login.
14. Labour remains simple in current scope.
15. Frontend permissions never replace backend authorization.
16. Financial truth is deterministic and auditable.
17. Critical financial writes are atomic and duplicate-safe.
18. Unreceived money never becomes received/recovered/available.
19. Public API never exposes internal finance.
20. AI is Owner-only and read-only.
21. AI never becomes financial source of truth.
22. Image/media behavior follows 08 and must degrade locally.
23. Core application must remain usable on slow networks.
24. Production changes progress through controlled environments.
25. Backups require a real restore path.
26. Tests must include permission/failure paths where relevant.
27. Independent audit findings require repository verification.
28. Codex may decide technical implementation but may not invent business rules.


# 72. DOCUMENT STATUS

Document:
06 — TECHNICAL ARCHITECTURE, ENGINEERING & OPERATIONS

Version:
Final v1.0

Status:
LOCKED — AUTHORITATIVE TECHNICAL ARCHITECTURE & ENGINEERING SOURCE OF TRUTH

This document replaces the need for separate:

- 06 — Branch & Labour Architecture
- 09 — Performance Architecture
- 10 — Security Architecture
- 11 — AI / Automation Architecture
- 12 — API & Backend Architecture
- 13 — Deployment / Staging / Production
- 14 — Testing & Audit Strategy

07 — UI / Navigation Structure
and
08 — Image & File Architecture

remain separate specialized source-of-truth documents.

Codex must derive implementation architecture from the complete approved documentation and actual repository state.

Codex must not invent missing business behavior.