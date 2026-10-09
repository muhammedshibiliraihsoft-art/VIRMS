TENANT MERGE & CONSOLIDATION ARCHITECTURE
Vehicle Investment, Modification & Resale Management System (VIRMS)
Version: Final v1.0  
Status: LOCKED — SUPPORTING ARCHITECTURE SOURCE OF TRUTH
---
1. PURPOSE
This document defines the controlled architecture for the rare case where two existing operational Garages/Tenants must be consolidated into one continuing operational Tenant.
This is a supporting architecture document.
Tenant Merge is not a normal day-to-day business workflow and must not become a routine operational feature.
The purpose of this document is to make a future consolidation possible without:
deleting the old Tenant,
rewriting historical identity,
changing historical financial truth,
duplicating global Investors,
corrupting Investor Fund history,
losing Vehicle origin/history,
silently escalating user permissions,
breaking Tenant isolation,
or forcing the core application to become unnecessarily complex.
---
2. AUTHORITATIVE SOURCES
This document must be read together with:
01 — Business Rules
02 — User Roles & Permissions
03 — System Modules
04 — Data Model & Relationships
05 — Vehicle / Investor / Finance Workflow
06 — Technical Architecture, Engineering & Operations
07 — UI / Navigation Structure
08 — Image & File Architecture
Authentication / Account Security
Production Engineering / Reliability standards
If this document conflicts with a newer explicitly locked business rule, the newer locked rule wins.
This document may define the technical consolidation process, but it must not create new financial or permission rules.
---
3. CORE PRINCIPLE
A Tenant consolidation means:
`Source Tenant + Target Tenant → one continuing operational Tenant`
It does not mean:
`delete Source Tenant and rewrite all old records as Target Tenant`
The Target Tenant continues as the active operational destination.
The Source Tenant remains preserved as a historical Tenant identity.
---
4. TERMINOLOGY
Source Tenant
The Garage/Tenant whose normal future operations are being consolidated into another Tenant.
Target Tenant
The Garage/Tenant that continues as the operational destination after consolidation.
Consolidation
A controlled system-level process that transfers only the operational scope that must continue under the Target while preserving historical source context.
Historical Source Context
The original Tenant/Garage context that existed when a historical business or financial event occurred.
Historical Source Context must never be silently rewritten.
---
5. AUTHORITY
Tenant Merge / Consolidation is:
`Back Office / Controlled System Administration ONLY`
It is not an Accountant normal operational action.
It is not:
Owner self-service,
Accountant self-service,
Investor functionality,
Media functionality,
Public API functionality.
If a dedicated Back Office UI does not exist, the consolidation may be executed as a controlled administrative/migration procedure.
A generic public-facing or daily operational `Merge Tenant` button is not required.
---
6. DO NOT OVER-ENGINEER THE CORE SYSTEM
The core system must be merge-ready, not merge-centric.
Normal application architecture should preserve:
stable UUID identities,
Tenant history,
explicit memberships,
Vehicle Tenant history,
financial history,
global Investor identity,
auditability.
Do not introduce complex infrastructure, distributed workflows, or permanent runtime overhead solely to support a rare merge operation.
If a safe one-off controlled migration is simpler than a generic automated merge engine, the controlled migration is acceptable.
---
7. NON-NEGOTIABLE IDENTITY RULES
Source Tenant
keeps its original UUID,
must not be hard-deleted,
must not be silently renamed into the Target,
remains queryable for historical/audit purposes.
Target Tenant
keeps its original UUID,
does not inherit the Source UUID,
remains the continuing operational Tenant.
Business Records
Existing persistent UUID identities must remain stable.
A merge must not create replacement records merely to make historical data appear as if it always belonged to the Target.
Human-readable values such as:
Tenant name,
Vehicle registration,
person name,
phone number,
category label
must never be used as merge identity.
---
8. GLOBAL ENTITIES — DO NOT MERGE OR DUPLICATE
The following are global/business-level identities and must not be duplicated because of Tenant consolidation:
User identity
Owner identity
Business Owner / Profit Recipient identity
Investor identity
Investor Fund position
Investor Fund Ledger identity/history
Investor Profit Agreement/history
Investor lifecycle identity
Most importantly:
`Investor is GLOBAL`
and
`Investor Fund is GLOBAL`
A merge must never create:
Investor A — Source Tenant
Investor A — Target Tenant
as separate Investors for the same real Investor.
Tenant-tagged financial activity remains historical context only.
---
9. INVESTOR FUND & FINANCIAL HISTORY
Tenant consolidation must never recalculate or rewrite:
Initial Fund
Additional Fund
Vehicle Purchase Use
Vehicle Expense Use
Principal Recovery
Recovered Principal history
Profit Earned
Profit Paid
Profit Pending
Sale amounts
Buyer Payments
Profit snapshots
Owner allocation snapshots
Settlements
Corrections
Existing ledger/transaction entries retain their original:
Investor,
Vehicle,
Tenant/context,
amount,
date/time,
source record,
actor,
audit history.
A Tenant merge is an organizational/operational consolidation.
It is not a financial re-posting operation.
---
10. VEHICLE HANDLING
Vehicle UUID remains unchanged.
Vehicle → Investor relationship remains unchanged.
One Vehicle → One Investor remains unchanged.
10.1 Vehicles Requiring Continued Operation
An unsold/currently operational Vehicle that must continue under the Target may have its current Tenant changed from Source to Target through the existing controlled Vehicle Tenant movement architecture.
The transfer must create/preserve Vehicle Tenant History containing the equivalent of:
Vehicle
From Tenant
To Tenant
transfer date/time
actor
merge/consolidation reference
optional reason/note
The merge must never simply overwrite the Vehicle Tenant without history.
10.2 Historical / Completed Vehicles
Completed historical Vehicles must not be rewritten merely to make old business appear as though it originally occurred in the Target.
Historical Source Tenant context remains preserved.
10.3 Vehicle Financial Data
Moving the current operational Tenant of a Vehicle must not:
change its Investor,
recalculate Purchase Cost,
recreate Expenses,
recreate Fund usage,
reset Recovered Principal,
recreate Sale,
recalculate historical Profit,
alter historical snapshots.
The Vehicle keeps one continuous financial identity.
---
11. TWO-STAGE CONSOLIDATION MODEL
The preferred safe model is staged consolidation.
Stage A — Operational Cutover
The Source stops accepting new normal business operations.
Transfer only the operational scope that must continue in the Target.
Examples include eligible:
active/unsold Vehicles,
required user access,
current operational media/publication context,
other explicitly approved continuing records.
Existing Source historical records remain intact.
Stage B — Source Finalization
The Source may remain temporarily available only for controlled completion/review of unresolved legacy positions.
Examples may include:
open Receivables,
pending Buyer Payments,
unresolved corrections,
required historical reporting,
other legitimate open Source obligations.
When required legacy positions are resolved and validation passes:
Source becomes Inactive/Archived/Consolidated,
Target remains operational,
Source history remains preserved.
This staged approach avoids rewriting live financial history merely to finish a merge.
---
12. SOURCE OPERATIONAL LOCK
Before execution begins, the Source must enter a controlled consolidation/cutover state or equivalent system-level lock.
After cutover, the Source must not accept ordinary new operations such as:
new Vehicle purchase,
new unrelated Vehicle creation,
new normal Investor-funded business assigned to Source,
new routine Source business merely because the old Tenant still exists historically.
Necessary legacy completion actions may remain available only under controlled authorization until finalization.
The exact technical mechanism may be:
status,
maintenance lock,
consolidation flag,
backend policy,
depending on the actual repository architecture.
---
13. USER & TENANT MEMBERSHIP HANDLING
User identity is global.
Do not duplicate a User because the same person existed in both Tenants.
Merge processing must treat:
`User identity`
and
`Tenant Membership / Assignment`
as separate concerns.
13.1 Source-Only User
If a Source operational user must continue in Target:
create/enable an explicit Target assignment,
preserve Source membership history,
validate the role/permission allowed in Target.
13.2 User Already Assigned to Both
Do not create another User.
Do not create duplicate active membership unnecessarily.
Reconcile memberships explicitly.
13.3 No Automatic Privilege Union
If Source and Target memberships differ, the merge must not automatically combine privileges.
Example:
Source role = higher privilege  
Target role = lower privilege
must not become:
Target role = higher privilege
merely because a merge occurred.
Permission changes require explicit authorized mapping.
13.4 Source Membership History
Old Source assignments must remain auditable.
After Source finalization they may become inactive/historical where appropriate.
---
14. OWNER ACCESS
Owner identity is global.
Owner normal role remains:
`View + Monitor + Analyse`
and remains operationally read-only.
Consolidation must preserve Owner visibility into:
Source historical data,
Target operational data,
authorized combined business reporting.
A merge must not require duplicating Owner identity.
A merge also must not grant Owner normal operational write permissions.
---
15. ACCOUNTANT ACCESS DURING TRANSITION
Accountant remains the operational role for normal business activity.
During staged consolidation, an explicitly authorized Accountant may temporarily require access to:
Target current operations,
Source legacy/open positions.
This must use explicit Tenant assignment/scope.
Target membership alone must not magically bypass Source Tenant isolation.
Once Source legacy work is complete, obsolete Source operational access should be deactivated according to the approved access plan.
---
16. BUYER / CUSTOMER HANDLING
Buyer is Tenant-scoped in the current architecture.
Therefore Tenant consolidation must NOT automatically unify Buyers based on:
name,
phone number,
secondary phone,
address,
textual similarity.
Historical Source Buyer records remain attached to Source historical Sales.
For future Target business:
reuse an existing Target Buyer when legitimately matched through normal application rules,
otherwise create/use a Target Buyer record as required.
Do not rewrite historical Source Sales merely to create a single cross-Tenant Buyer identity.
A future global customer identity model would require a separate explicit business decision.
---
17. LABOUR HANDLING
Labour is Tenant-scoped and intentionally simple.
Historical Source Labour and Labour Payment history must remain preserved.
Do not automatically merge Labour records by:
name,
phone,
similarity.
If the same worker continues operationally in the Target, implementation may create or use the appropriate Target Labour record while retaining Source historical Labour/Payment history.
Do not rewrite old Labour Payments as Target payments.
No merge process may introduce:
payroll engine,
attendance,
Vehicle assignment,
work-type tracking
as a side effect.
---
18. EXPENSE CATEGORY HANDLING
ExpenseCategory is Tenant-scoped.
Source and Target may contain categories with the same human-readable name.
Same label does not mean same identity.
Do not automatically merge ExpenseCategory records by name.
Historical Source Vehicle Expenses keep their existing category references.
Future Target Expenses use valid Target categories.
If explicit category mapping is useful during consolidation, it must be a controlled mapping for future use and must not rewrite historical Expense records.
---
19. TENANT CONFIGURATION
Target configuration governs future Target operations after cutover.
Source historical configurations/snapshots remain historical truth.
Do not:
copy Source settings over Target automatically,
recalculate completed deals using Target defaults,
replace historical percentage snapshots,
rewrite completed financial configuration history.
Before cutover, any Source configuration that legitimately must continue in Target must be reviewed explicitly.
Configuration conflicts require an explicit decision in the merge plan.
No silent `Source wins` / `Target wins` behavior is permitted except that Target's already-approved configuration remains the default for future Target operations unless an authorized merge decision changes it.
---
20. MEDIA / PUBLICATION
Vehicle media follows the Vehicle relationship defined in the Image & File Architecture.
For a Vehicle moved operationally to Target:
image UUIDs remain unchanged,
media records remain attached to the same Vehicle,
optimized/original files do not need to be duplicated merely because Tenant context changed.
Historical/publication information must remain auditable.
Storage keys/URLs are not business identity.
Public APIs must still expose only approved public-safe information.
---
21. SOLD VEHICLES / OPEN RECEIVABLES
A sold Vehicle may still have:
Pending/Partial Buyer collection,
Buyer Payment history,
Principal recovery activity,
Profit eligibility/payment state,
correction requirements.
These are financial history and must not be rewritten merely for Tenant consolidation.
Preferred safe behavior:
keep the historical Sale and financial context under the Source,
allow explicitly authorized legacy completion while Source is in staged consolidation,
finalize Source only after required unresolved positions are handled.
If the actual implementation proposes moving an unresolved financial position to Target, it must prove that historical Tenant context, financial source-of-truth, idempotency, audit and reconciliation remain intact.
Do not invent such migration merely for convenience.
---
22. SETTLEMENT / INVESTOR LIFECYCLE
Investor Exit and Settlement are global Investor lifecycle concerns with relevant Tenant/Vehicle context.
Tenant consolidation must not:
close an Investor,
reopen an Investor,
manufacture recovered money,
unlock capital,
change Settlement amounts,
change Investor lifecycle state
unless the normal authoritative workflow independently requires it.
Existing Settlement/history records retain original context.
---
23. CONFLICT DETECTION — REQUIRED
Before any write, the merge must perform a preflight/dry-run.
At minimum inspect for conflicts involving:
Source and Target validity
Tenant status
user memberships/roles
active Vehicles
sold Vehicles with unresolved Receivables
pending Buyer Payments
pending Settlements
pending financial corrections
duplicated or conflicting tenant-scoped configuration
ExpenseCategory naming/constraint conflicts
Buyer similarities
Labour similarities
Vehicle registration/display conflicts
public/media status
background jobs or pending processing
database uniqueness/foreign-key constraints
application assumptions that depend on Tenant scope
Preflight findings must be classified as:
safe automatically,
explicit mapping required,
manual review required,
blocking conflict.
Blocking conflicts stop execution.
---
24. NO NAME-BASED AUTO-MERGE
The system must never automatically decide that two records are identical solely because they share:
name,
phone,
Vehicle registration,
category name,
label,
public title,
filename.
UUID/entity identity remains authoritative.
Human-readable duplicates are conflict/review signals only.
---
25. MERGE PLAN / MANIFEST
Before execution, produce a deterministic merge plan or equivalent manifest.
It should identify:
Source Tenant UUID
Target Tenant UUID
operation identifier
actor
planned cutover time
Source records to remain historical
records to transfer operationally
Vehicle transfer list
membership mapping
configuration decisions
known conflicts
unresolved legacy positions
blocking issues
expected record counts
validation checks
Execution must use the reviewed plan rather than rediscovering business decisions mid-operation.
---
26. AUDIT RECORD
If Tenant consolidation is implemented, persist a durable merge/consolidation audit record or equivalent.
Audit should preserve:
operation UUID/reference
Source Tenant
Target Tenant
initiated/executed by
timestamps
preflight result
approved mappings
affected record counts
Vehicle transfers
membership changes
configuration decisions
warnings/conflicts
completion state
failure state if any
rollback/recovery reference where applicable
Passwords, tokens and secrets must never appear in merge audit data.
---
27. EXECUTION SAFETY
Merge execution must be:
controlled,
repeat-safe/idempotent where practical,
resumable when work is chunked,
transaction-safe,
observable,
validated before and after.
Do not perform one enormous unsafe transaction if it creates unacceptable production locks.
Do not perform uncontrolled row-by-row mutation without checkpointing.
Codex may choose the exact migration/service/command structure based on the actual repository and database.
---
28. CONCURRENCY
During critical consolidation windows, prevent conflicting writes that could make the merge plan stale.
Examples:
Vehicle transferred while merge is processing,
user membership changed mid-merge,
Source config changed after preflight,
new Source Vehicle created during cutover.
Use appropriate:
operational lock,
version/checkpoint validation,
transaction boundaries,
revalidation immediately before mutation.
Do not assume preflight state remains valid indefinitely.
---
29. BACKUP / CHECKPOINT
Before destructive or large-scale consolidation mutation:
identify the actual environment,
confirm Production vs Staging,
create/verify an appropriate backup/checkpoint,
ensure a restore/recovery path is known,
record the accepted merge plan.
Do not execute an unverified merge directly against Production data.
Prefer rehearsal in a production-like staging/copy where feasible.
---
30. ROLLBACK / RECOVERY
Rollback must be designed before execution.
Before Final Cutover
Where possible, changes should be reversible using:
merge manifest,
previous Tenant assignments,
VehicleTenantHistory,
membership history,
transactional checkpoints.
After New Target Activity Exists
Do not blindly "undo" the merge by deleting history or rewriting rows backward.
Once new Target operations have occurred, rollback may itself require a controlled reverse migration/recovery plan.
Historical merge audit must remain even if the operation is reversed.
No rollback may erase financial history.
---
31. SOURCE TENANT FINAL STATE
After successful finalization:
Source Tenant:
remains a persistent historical Tenant,
is not hard-deleted,
is not a normal selectable operational destination,
is marked Inactive/Archived/Consolidated or equivalent,
retains historical references,
retains merge audit/reference to Target where implemented.
Target Tenant:
remains the active continuing operational Tenant,
keeps its own UUID,
receives only the operational scope explicitly migrated.
---
32. REPORTING AFTER CONSOLIDATION
Historical reporting must still be able to distinguish:
activity originally belonging to Source,
activity originally belonging to Target,
post-cutover Target operations.
Owner must retain authorized read visibility across consolidated history.
Combined reporting must not flatten history so aggressively that original Tenant context becomes unknowable.
Where a "consolidated business" report is provided:
aggregate totals may be shown,
original Tenant context must remain drillable/traceable.
---
33. TENANT ISOLATION AFTER MERGE
Consolidation must not disable Tenant isolation.
Normal requests must still follow:
Authenticated User
→ Tenant Assignment / approved historical scope
→ Permission
→ Resource
→ Allow / Deny
Knowing Source or Target UUID must never be sufficient to access data.
Historical Source access after consolidation must be explicit/system-authorized, not an accidental side effect of Target access.
---
34. CACHE / SEARCH / EXPORT / JOB SAFETY
Consolidation must account for Tenant-aware infrastructure including:
cache keys,
search indexes,
report scopes,
exports,
background jobs,
notifications,
media authorization.
After cutover:
stale Source operational caches must not continue enabling writes,
Target views must not omit transferred active records,
search/report indexes must preserve original history,
pending jobs must not process records under the wrong Tenant context.
Exact invalidation/reindex mechanism is an implementation decision.
---
35. PUBLIC API
Tenant Merge does not expose a new public API operation.
Public vehicle consumers should continue receiving only approved public Vehicle data.
Public output must not reveal:
merge internals,
Source/Target administrative details,
financial data,
Investor private data,
internal audit data.
A Vehicle that remains public after transfer should continue through normal publication rules.
---
36. IMPLEMENTATION FORM
Tenant consolidation may be implemented as one of:
protected Back Office workflow,
protected internal admin tool,
Django management command,
controlled migration script/service,
depending on the actual repository maturity.
The implementation form is secondary.
The safety rules in this document are mandatory.
---
37. PRE-MERGE CHECKLIST
Before execution confirm:
[ ] Source Tenant identified by UUID
[ ] Target Tenant identified by UUID
[ ] Source ≠ Target
[ ] Target is valid operational destination
[ ] Environment identified
[ ] Backup/recovery path confirmed
[ ] New Source operations controlled/frozen
[ ] Active Vehicles inventoried
[ ] Open Receivables inventoried
[ ] Pending Settlements/corrections inventoried
[ ] User memberships mapped
[ ] No automatic privilege escalation
[ ] Tenant configuration conflicts reviewed
[ ] Buyer/Labour/category duplicate signals reviewed
[ ] Financial ledger reconciliation passes
[ ] Merge manifest created
[ ] Blocking conflicts = 0
---
38. POST-MERGE VALIDATION
After operational cutover/finalization verify:
Tenant
Source UUID still exists
Target UUID unchanged
Source historical state preserved
Source cannot accept unauthorized new operations
Vehicles
transferred Vehicle UUIDs unchanged
Investor relationship unchanged
current Tenant correct
VehicleTenantHistory exists
historical Vehicle records preserved
Finance
Investor Fund totals unchanged except legitimate normal transactions
no duplicate ledger entries
no recalculated historical profit
no lost Buyer Payments
no changed Recovered Principal history
no broken Settlement history
Permissions
target users have only approved access
no role escalation
source legacy access works only where explicitly authorized
Media still cannot see finance
Investor still sees only permitted own/private scope
Owner remains read-only
History
Source historical reports remain traceable
audit record exists
configuration history remains intact
user membership history remains intact
Technical
caches/invalidation correct
jobs use correct Tenant context
search/report results correct
API authorization tests pass
---
39. TEST REQUIREMENTS
If Tenant Merge is implemented, tests must cover at minimum:
Source and Target cannot be the same Tenant.
Unauthorized role cannot start merge.
Accountant cannot perform normal merge action.
Owner cannot perform merge action.
Global Investor is not duplicated.
Global Investor Fund is not duplicated.
Vehicle UUID remains unchanged.
Vehicle Investor remains unchanged.
Vehicle transfer creates history.
Historical Sale/Expense/Payment truth is preserved.
Source Tenant is not hard-deleted.
Existing user identity is not duplicated.
Membership conflict does not escalate permission.
Source/Target configuration conflict does not silently overwrite history.
Duplicate Buyer phone does not trigger automatic Buyer merge.
Duplicate Labour name does not trigger automatic Labour merge.
Failed mid-process execution can resume/recover safely.
Re-running an accepted merge step does not create duplicate financial/transfer records.
Target user cannot access Source history without approved scope.
Post-merge Owner visibility and read-only restrictions remain correct.
---
40. EXPLICIT NON-SCOPE
This document does NOT create:
routine Tenant Merge UI for normal users,
Accountant-controlled merge,
Owner-controlled merge,
automatic company acquisition workflow,
generic organization tree,
automatic Buyer globalization,
automatic Labour globalization,
automatic cross-Tenant deduplication,
financial ledger consolidation/re-posting,
Investor duplication,
automatic Tenant configuration blending,
historical financial rewriting,
cross-Tenant access bypass,
payroll/attendance features.
---
41. CODEX IMPLEMENTATION RULE
When Tenant consolidation is actually requested, Codex must:
Read the authoritative project docs.
Inspect the actual repository and current schema.
Inspect existing Tenant, Membership, VehicleTenantHistory, finance and audit implementation.
Identify the exact environment.
Run a read-only preflight first.
Produce the merge plan/conflicts before destructive mutation.
Reuse existing architecture where safe.
Do not invent new business/financial rules.
Preserve all identities/history required by this document.
Implement the smallest safe approach.
Add targeted tests.
Validate finance, permissions and Tenant isolation.
Provide evidence.
Stop if a real unresolved business decision is encountered.
Codex may decide low-level implementation mechanics.
Codex may not weaken the invariants below.
---
42. NON-NEGOTIABLE INVARIANTS
Tenant Merge is rare, not normal operations.
Merge is Back Office / controlled system administration only.
Source Tenant is never silently deleted.
Source Tenant UUID remains preserved.
Target Tenant UUID remains preserved.
Historical Tenant identity remains traceable.
Historical financial truth is never rewritten merely because of merge.
Global Investor is never duplicated per Tenant.
Global Investor Fund is never duplicated per Tenant.
Existing ledger entries retain historical Tenant/Vehicle context.
Vehicle UUID remains unchanged.
Vehicle Investor relationship remains unchanged.
Vehicle Tenant change must preserve VehicleTenantHistory.
Users are not duplicated merely because memberships span Tenants.
Merge must not silently escalate permissions.
Buyer records are not auto-merged by phone/name.
Labour records are not auto-merged by name/similarity.
Tenant-specific configuration does not silently overwrite completed historical configuration.
Owner remains read-only.
Accountant does not receive Tenant Merge authority.
Tenant isolation remains backend-enforced.
Merge must be audited.
Merge requires preflight/conflict detection.
Production merge requires backup/recovery planning.
Merge implementation must remain as simple as safely possible.
---
43. DOCUMENT STATUS
Document:
`Tenant Merge & Consolidation Architecture`
Project:
`VIRMS — Vehicle Investment, Modification & Resale Management System`
Version:
`Final v1.0`
Status:
`LOCKED — SUPPORTING ARCHITECTURE SOURCE OF TRUTH`
This document exists only to govern rare future Tenant/Garage consolidation.
It must not add normal operational complexity to the core system.