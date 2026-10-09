02 — USER ROLES & PERMISSIONS
Vehicle Investment, Modification & Resale Management System
Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH
Purpose: Roles, Permissions, Tenant Access, Operational Authority, User Management Authority, Public Access, Back Office Scope, AI Access എന്നിവയ്ക്ക് authoritative reference.
LOCKED rules implementation സമയത്ത് silently broaden, reduce, bypass, reinterpret, അല്ലെങ്കിൽ omit ചെയ്യരുത്.
01 — Business Rules business/financial truth define ചെയ്യുന്നു.
02 — User Roles & Permissions ആര്ക്ക് എന്ത് കാണാം / ചെയ്യാം എന്നത് define ചെയ്യുന്നു.
Authentication, password, login recovery, session-security mechanics separate Authentication document-ൽ define ചെയ്യും.

A. AUTHORIZATION PRINCIPLES
RP-CORE-001 — Least Privilege
Status: LOCKED
ഓരോ user-നും അവരുടെ role ചെയ്യാൻ ആവശ്യമായ permissions മാത്രം ലഭിക്കണം.
Sensitive operation explicit permission ഇല്ലെങ്കിൽ deny ചെയ്യണം.

RP-CORE-002 — Backend-Enforced Authorization
Status: LOCKED — CRITICAL
Frontend button hide/show permission security അല്ല.
Permissions enforce ചെയ്യേണ്ടത്:
Backend
API
Business Logic
Tenant Scope
Object-Level Access
Frontend permission state-ന്റെ representation മാത്രമാണ്.

RP-CORE-003 — Central Permission Architecture
Status: LOCKED
Application മുഴുവൻ scattered:
if role == ...
checks കൊണ്ട് architecture build ചെയ്യരുത്.
Concept:
User → Role → Permission → Scope → Resource
Centralized, reusable permission model വേണം.

RP-CORE-004 — Extensible Roles
Status: LOCKED ARCHITECTURAL REQUIREMENT
Future role add ചെയ്യാൻ authorization system rewrite ചെയ്യേണ്ടതില്ല.
New role controlled ആയി:
Role + Permission Set + Scope
വഴി add ചെയ്യാൻ കഴിയണം.

B. MULTI-TENANT MODEL
RP-TENANT-001 — Multi-Tenant From Day One
Status: LOCKED — CRITICAL
System architecture initial implementation മുതൽ തന്നെ:
Multi-Tenant
ആയിരിക്കണം.
ഇത് future feature അല്ല.

RP-TENANT-002 — Garage = Tenant
Status: LOCKED
ഓരോ operational Garage:
One Tenant
ആയി represent ചെയ്യണം.

RP-TENANT-003 — Current Operational Situation
Status: LOCKED
Architecture multi-tenant ആണ്.
Current operational phase-ൽ ഒരു tenant മാത്രം actively use ചെയ്താലും:
Tenant model
Tenant assignments
Tenant resolver
Tenant isolation
ഇപ്പോൾ തന്നെ ഉണ്ടായിരിക്കണം.

RP-TENANT-004 — Tenant Resolver Required
Status: LOCKED — CRITICAL
ഓരോ tenant-scoped request-ലും backend current tenant context reliably determine ചെയ്യണം.
Concept:
Authenticated User
→ Tenant Assignment
→ Tenant Context
→ Permission Check
→ Resource Access

RP-TENANT-005 — Tenant Isolation
Status: LOCKED — CRITICAL
Tenant A scoped operational user unauthorized ആയി Tenant B-യുടെ:
Vehicles
Expenses
Labour
Media
Operational Records
Financial Data
Reports
access ചെയ്യരുത്.
Tenant ID manually change ചെയ്തതുകൊണ്ട് permission ലഭിക്കരുത്.

RP-TENANT-006 — Tenant Awareness
Status: LOCKED
Relevant scope maintain ചെയ്യണം:
API queries
Database access
Permissions
Search
Reports
Exports
Media
Cache
Background jobs
Audit logs

RP-TENANT-007 — Same User Across Multiple Tenants
Status: LOCKED
Same real user future-ൽ multiple tenants manage ചെയ്യേണ്ട സാഹചര്യം വന്നാൽ duplicate identity ആവശ്യമില്ല.
One account explicitly multiple tenants-ലേക്ക് assign ചെയ്യാൻ architecture support വേണം.

RP-TENANT-008 — Operational User Tenant Assignment
Status: LOCKED — CRITICAL
Accountant പോലുള്ള operational users എല്ലാ tenants-നും automatic access നേടരുത്.
Access explicit assignment അടിസ്ഥാനത്തിലായിരിക്കണം.
Support:
One User → One Tenant
or
One User → Multiple Explicitly Assigned Tenants
Backend verify ചെയ്യണം:
User
→ Is user assigned to requested tenant?
→ Does role have required permission?
→ Does requested resource belong to allowed scope?
→ Allow / Deny
Cross-tenant operational access deliberate assignment ആയിരിക്കണം.

C. TENANT MERGE / RESTRUCTURING SUPPORT
RP-TENANT-009 — Merge Is Not a Current Core Workflow
Status: LOCKED
Tenant merge സാധാരണ day-to-day business operation അല്ല.
Current primary UI-ൽ Tenant Merge option expose ചെയ്യേണ്ടതില്ല.

RP-TENANT-010 — Architecture Must Not Unnecessarily Block Future Merge
Status: LOCKED PRINCIPLE
Future-ൽ രണ്ട് garages/tenants operationally ഒന്നാക്കേണ്ട rare scenario വന്നാൽ safe migration/merge technically സാധ്യമാകുന്ന രീതിയിൽ architecture reasonably designed ആയിരിക്കണം.
പക്ഷേ merge support implementation disproportionate complexity ഉണ്ടാക്കുന്നുവെങ്കിൽ current core system unnecessarily complicate ചെയ്യരുത്.

RP-TENANT-011 — Merge Is Back Office / System-Level Only
Status: LOCKED
Future Tenant Merge implement ചെയ്താൽ അത്:
Back Office / Controlled System Administration
operation മാത്രമായിരിക്കണം.
Accountant normal operational action അല്ല.

RP-TENANT-012 — Detailed Merge Logic Separate Document
Status: LOCKED
Tenant Merge:
historical identity
target tenant
old tenant state
user reassignment
vehicle origin
audit
conflict handling
rollback/recovery
എന്നിവയുടെ detailed architecture separate supporting document-ൽ define ചെയ്യണം.
Supporting Document
Tenant Merge & Organizational Restructuring Architecture
ഈ 02 document merge workflow define ചെയ്യില്ല.

D. CURRENT SYSTEM ROLES
RP-ROLE-001 — Current Authenticated Roles
Status: LOCKED
Current system roles:
Owner
Accountant / Operations Admin
Investor
Media User
Back Office Admin
Labour
Managed Entity — No Login
Public Vehicle Access
Public vehicle viewing ഒരു user role അല്ല.
അതിന് dedicated:
Public / External Vehicle View API
ഉണ്ടായിരിക്കണം.

E. OWNER ROLE
RP-OWNER-001 — Owner Purpose
Status: LOCKED
Owner role:
View + Monitor + Analyse
ആണ്.
Owner normal operational write user അല്ല.

RP-OWNER-002 — Full Business Read Visibility
Status: LOCKED — CRITICAL
Owner authorized business scope-ൽ full read visibility ലഭിക്കണം.
Includes:
Investors
Investor Funds
Vehicles
Vehicle Costs
Vehicle Expenses
Sales
Buyers
Receivables
Labour
Profit / Loss
Investor Shares
Owners Pool
Owner Shares
Settlements
Reports
Financial Corrections
Percentage Changes
Audit History
Operational Status

RP-OWNER-003 — Strict Operational Read-Only
Status: LOCKED — CRITICAL
Owner normal operational system-ൽ:
Create ❌
Edit ❌
Delete ❌
Expense Entry ❌
Vehicle Write ❌
Sale Entry ❌
Financial Correction ❌
Investor Fund Modification ❌
Owner = Read Only

RP-OWNER-004 — Flexible Filtering
Status: LOCKED
Owner data filter/search ചെയ്യാൻ കഴിയണം.
Examples:
Tenant
Investor
Vehicle
Date
Status
Sale Status
Payment Status
Settlement Status

RP-OWNER-005 — Multi-Tenant Owner Visibility
Status: LOCKED
Owner authorized multiple tenants ഉള്ളപ്പോൾ:
Tenant-wise View
Combined Business View
support ചെയ്യണം.
Combined access tenant-isolation bypass അല്ല.
Explicit authorized Owner scope ആണ്.

F. OWNER AI
RP-AI-001 — Owner Only in Current Scope
Status: LOCKED
Current phase-ൽ AI permission:
Owner മാത്രം

RP-AI-002 — Read-Only AI
Status: LOCKED — CRITICAL
AI:
Query
Read
Analyse
Explain
Summarize
ചെയ്യാം.
AI write operations:
Create ❌
Update ❌
Delete ❌
Financial Transaction ❌
Percentage Change ❌

RP-AI-003 — Verified Data First
Status: LOCKED
Preferred architecture:
Verified Data / Deterministic Query
→ Verified Result
→ AI Explanation
AI model financial truth invent ചെയ്യരുത്.

G. ACCOUNTANT / OPERATIONS ADMIN
RP-ACC-001 — Main Operational Role
Status: LOCKED — CRITICAL
Accountant ആണ് day-to-day system operations-ന്റെ primary write authority.
Normal non-protected operations:
View + Create + Edit + Manage + Controlled Correction

H. ACCOUNTANT — INVESTOR MANAGEMENT
RP-ACC-INV-001
Status: LOCKED
Accountant manage ചെയ്യാം:
Investor Create
Investor Basic Details
Investor Account Provisioning
Investor Status
Initial Fund
Additional Fund
Investor Financial Position
Investor History
Exit Workflow
Settlement Operations

I. INVESTOR IS GLOBAL — NOT TENANT-OWNED
RP-INV-GLOBAL-001 — Global Investor Identity
Status: LOCKED — CRITICAL
Investor ഒരു particular tenant/garage-ന്റെ owned entity അല്ല.
Investor:
Business / Organization Global Entity
ആണ്.

RP-INV-GLOBAL-002 — No Mandatory Direct Investor → Garage Ownership
Status: LOCKED
Investor profile-ൽ mandatory:
Investor belongs to Garage X
relationship വേണ്ട.

RP-INV-GLOBAL-003 — Investor Can Participate Across Tenants
Status: LOCKED
Same investor:
One tenant-ൽ മാത്രം vehicles fund ചെയ്യാം
Multiple tenants-ൽ vehicles fund ചെയ്യാം
Duplicate Investor identity create ചെയ്യരുത്.

RP-INV-GLOBAL-004 — Global Investor Fund
Status: LOCKED
Investor fund source-of-truth global ആയിരിക്കണം.
Tenant-wise duplicate investor fund balance create ചെയ്യരുത്.

RP-INV-GLOBAL-005 — Transaction Traceability
Status: LOCKED
Investor global ആയാലും ഓരോ fund usage / vehicle financial movement-നും relevant:
Investor
Vehicle
Tenant / Context where applicable
trace ചെയ്യാൻ കഴിയണം.
Concept:
Global Investor Fund + Vehicle/Tenant-Tagged Financial History
Detailed ledger implementation Data Model & Financial Ledger Architecture document-ൽ define ചെയ്യണം.

J. ONE VEHICLE / ONE INVESTOR
RP-ACC-VEH-001 — Relationship Rule
Status: LOCKED — CRITICAL
One Vehicle → One Investor
ഒരു vehicle രണ്ട് investors fund ചെയ്യരുത്.
ഇത് 01 — Business Rules-ലും locked business constraint ആണ്. Pasted markdown

RP-ACC-VEH-002 — One Investor Can Fund Multiple Vehicles
Status: LOCKED — CRITICAL
One Investor → Multiple Vehicles ✅
One Investor = One Vehicle എന്ന restriction ഇല്ല.
ഇത് 01 Business Rules-ലും explicitly supported ആണ്. Pasted markdown

K. ACCOUNTANT — VEHICLE MANAGEMENT
RP-ACC-VEH-003
Status: LOCKED
Accountant manage ചെയ്യാം:
Vehicle Create
Purchase Details
Investor Assignment
Tenant/Garage Assignment
Vehicle Details
Vehicle Status
Vehicle Work/Modification
Vehicle Expenses
Sale
Buyer
Receivable
Buyer Payment

L. VEHICLE STATUS
RP-VEH-STATUS-001
Status: LOCKED CURRENT MODEL
Current simple vehicle lifecycle:
Purchased
→ In Work
→ Ready
→ Listed
→ Sold
Unnecessary additional statuses current phase-ൽ add ചെയ്യരുത്.

M. ACCOUNTANT — EXPENSE MANAGEMENT
RP-ACC-EXP-001
Status: LOCKED
Accountant:
Vehicle Expense Add
Vehicle Expense Edit
Controlled Correction
Expense History
Total Vehicle Expense
Category Totals
manage ചെയ്യാം.

RP-ACC-EXP-002 — Dynamic Categories
Status: LOCKED
Accountant new vehicle expense category UI വഴി add ചെയ്യാം.
Code deployment ആവശ്യമില്ല.
01 Business Rules dynamic categories require ചെയ്യുന്നു. Pasted markdown

RP-ACC-EXP-003 — Expense Scope
Status: LOCKED CURRENT SCOPE
Current expense model primarily:
Vehicle-Based Expenses
ആണ്.
General garage expense/accounting module current core scope-ൽ വേണ്ട.

N. INVESTOR PROFIT PERCENTAGE AUTHORITY
RP-PROFIT-001 — Initial Percentage
Status: LOCKED
New investor agreement/setup സമയത്ത് investor-specific profit percentage:
Accountant set ചെയ്യാം.

RP-PROFIT-002 — Later Percentage Change
Status: LOCKED — FINANCIAL CONTROL
Legitimate requirement വന്നാൽ Accountant investor-specific percentage change ചെയ്യാം.
Mandatory audit:
Old Value
New Value
Investor
Changed By
Date / Time
Scope

RP-PROFIT-003 — Owner Visibility
Status: LOCKED
Percentage change ഉണ്ടായാൽ Owner-ന്:
Notification
Old Value
New Value
Changed By
Date/Time
കാണണം.
Owner approval mandatory അല്ല.

RP-PROFIT-004 — Historical Protection
Status: LOCKED — CRITICAL
Later percentage change completed historical deals-നെ recalculate ചെയ്യരുത്.
01 Business Rules historical percentage snapshots preserve ചെയ്യണമെന്ന് explicitly require ചെയ്യുന്നു. Pasted markdown

RP-PROFIT-005 — System / Tenant Defaults
Status: LOCKED
System-level / tenant-level default profit configuration:
Back Office
manage ചെയ്യണം.

O. ACCOUNTANT — SALES & RECEIVABLES
RP-ACC-SALE-001
Status: LOCKED
Accountant manage ചെയ്യാം:
Full Payment Sale
Partial Payment Sale
Credit Sale
Buyer
Agreed Sale Price
Amount Received
Pending Amount
Receivable
Payment Completion

RP-ACC-SALE-002 — Payment States
Status: LOCKED
Simple primary states:
Pending / Partially Received
Fully Received
അതോടൊപ്പം exact:
Total Amount
Received Amount
Pending Amount
show ചെയ്യണം.

RP-ACC-SALE-003 — Actual Received Money Only
Status: LOCKED — CRITICAL
Unreceived money actual available/recovered fund ആയി treat ചെയ്യരുത്.
Payment വന്നുകൊണ്ടിരിക്കുന്നതിനനുസരിച്ച് received/pending position update ചെയ്യണം.

P. FINANCIAL CORRECTIONS
RP-CORR-001 — Accountant Authority
Status: LOCKED
Legitimate sold-vehicle / relevant financial correction:
Accountant
നടത്താം.

RP-CORR-002 — Audit Required
Status: LOCKED — CRITICAL
Correction preserve ചെയ്യണം:
Previous Value
Corrected Value
Changed By
Date / Time
Reason where applicable
Old financial truth silently delete ചെയ്യരുത്.
01 Business Rules correction audit already requires this. Pasted markdown

Q. LOSS HANDLING
RP-LOSS-001 — No Separate Loss Workflow
Status: LOCKED CURRENT SCOPE
Vehicle result negative ആണെങ്കിൽ normal calculation വഴി:
Sale Price − Total Vehicle Cost
negative value = Loss.
Current system-ൽ separate:
Loss Allocation Selector
Investor Loss Option
Owner Loss Option
Shared Loss Configuration
വേണ്ട.
Rare exceptional business adjustments existing legitimate financial/correction mechanisms വഴി handle ചെയ്യാം.

R. LABOUR MODULE
RP-LAB-001 — Separate Simple Module
Status: LOCKED
Labour separate module ആയിരിക്കണം.
Current phase intentionally simple ആയിരിക്കണം.

RP-LAB-002 — Accountant Labour Permissions
Status: LOCKED
Accountant can:
Labour Create
Basic Details Edit
Labour List/View
Active/Inactive if required
Labour Payment Entry
Payment History
സത്യമാണൊരു കാരണം, ഓൾസോ ഫുള്ള് ഇംഗ്ലീഷായിരിക്കണം.
Understood. The final document should be fully in English.
Below is the clean, locked 02 — User Roles & Permissions document. I have removed authentication/password mechanics from this document, simplified Labour, removed the current Cash/Bank account module permissions, incorporated the global Investor model, clarified tenant assignment, added the flexible public Vehicle API, and kept Tenant Merge only as a reference to a separate supporting architecture document.

02 — USER ROLES & PERMISSIONS
Vehicle Investment, Modification & Resale Management System
Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH
Purpose: Defines roles, permissions, tenant scope, operational authority, administrative authority, public access, user provisioning ownership, and access-control boundaries.
Any rule marked LOCKED must not be silently changed, broadened, bypassed, or reinterpreted during implementation.
Authentication, password management, password recovery, login security, and session security are defined in a separate Authentication & Account Security document and are intentionally excluded from this document.

A. AUTHORIZATION PRINCIPLES
RP-CORE-001 — Least Privilege
Status: LOCKED
Every user must receive only the permissions required for their role.
Sensitive access must never be granted merely because a user is authenticated.

RP-CORE-002 — Backend-Enforced Authorization
Status: LOCKED — CRITICAL
Hiding a button in the frontend is not security.
Authorization must be enforced by:
Backend APIs
Business logic
Tenant scope
Object-level authorization
Data access rules
The frontend only represents permissions already enforced by the backend.

RP-CORE-003 — Centralized Permission Architecture
Status: LOCKED
Permission logic must not be scattered throughout the application as ad-hoc role checks.
The conceptual authorization model is:
User
→ Role
→ Permission
→ Tenant / Scope
→ Resource
→ Allow / Deny
The permission layer must remain reusable and extensible.

RP-CORE-004 — Future Role Extensibility
Status: LOCKED
Adding a future role must not require rewriting the authorization system.
New roles should be introduced through controlled:
Role definitions
Permission sets
Scope assignments

B. TENANT ARCHITECTURE
RP-TENANT-001 — Multi-Tenant From Day One
Status: LOCKED — CRITICAL
The platform is a multi-tenant system from the initial implementation.
It is not a single-tenant application that may later be converted.

RP-TENANT-002 — Garage = Tenant
Status: LOCKED
A Garage is treated as a Tenant.
Each tenant represents an operational boundary.

RP-TENANT-003 — Current Operational State
Status: LOCKED
The architecture is multi-tenant.
However, only one tenant may currently be actively operated during the initial implementation.
This must not weaken the underlying multi-tenant architecture.

RP-TENANT-004 — Tenant Resolver
Status: LOCKED — CRITICAL
The backend must establish the active tenant context for tenant-scoped operations.
Conceptually:
Authenticated User
→ Tenant Membership
→ Tenant Resolver
→ Current Tenant Context
→ Permission Check
→ Resource Access
Tenant resolution must exist from the initial implementation.

RP-TENANT-005 — Tenant Isolation
Status: LOCKED — CRITICAL
A user assigned only to Tenant A must not access Tenant B private data.
This includes:
Vehicles
Expenses
Labour
Users
Media
Operational records
Reports
Tenant-specific configuration
Tenant isolation must be enforced by the backend.
Changing a tenant ID in a request must never be sufficient to gain access.

RP-TENANT-006 — Tenant Awareness Across the System
Status: LOCKED
Tenant awareness must be preserved where relevant across:
API queries
Database access
Permissions
Search
Reports
Exports
Media
Background jobs
Audit records
Notifications
Cache keys

RP-TENANT-007 — Global Owner Identity
Status: LOCKED
An Owner is not duplicated simply because the business operates multiple tenants.
A single Owner identity may be assigned to multiple authorized tenants.

RP-TENANT-008 — Operational User Tenant Assignment
Status: LOCKED — CRITICAL
Operational users, especially Accountants, must not automatically receive access to every tenant.
Tenant access must be explicitly assigned.
The system must support:
One User → One Tenant
and, when intentionally required:
One User → Multiple Explicitly Assigned Tenants
Every request must validate:
User
→ Tenant Assignment
→ Role Permission
→ Requested Resource Tenant
→ Allow / Deny
Selecting or submitting another tenant identifier must never grant access by itself.
Practical Example
Tenant A has Accountant A.
Tenant B has Accountant B.
By default:
Accountant A → Tenant A only
Accountant B → Tenant B only
If Accountant A later needs to operate both tenants, Tenant B must be explicitly assigned.

C. TENANT MERGE READINESS
RP-TENANT-009 — Tenant Merge Must Not Be Blocked
Status: LOCKED ARCHITECTURAL PRINCIPLE
The core architecture should avoid making a future tenant consolidation unnecessarily difficult.
A rare future situation may require two tenants/garages to be consolidated into one operational tenant.
This is not a normal business operation.
The regular application must not expose a Tenant Merge action.
If a safe and reasonably simple merge mechanism is implemented, it belongs to:
Back Office only
Detailed merge behavior, migration rules, historical preservation, conflict handling, and audit requirements must be defined in a separate supporting document:
Supporting Architecture — Tenant Merge & Consolidation
The core system must not be over-engineered purely for tenant merging.
If implementing automatic tenant merging would create disproportionate architectural risk or complexity, the merge process may remain a controlled administrative/migration procedure instead.

D. CURRENT SYSTEM ROLES
RP-ROLE-001 — Current Roles
Status: LOCKED
Authenticated roles are:
Owner
Accountant / Operations Admin
Investor
Media User
Back Office Admin
Labour is not an authenticated user role.
Labour is a managed business entity.

E. OWNER ROLE
RP-OWNER-001 — Role Purpose
Status: LOCKED
Owner is primarily a:
View + Monitor + Analyse
role.
Owner is not the normal operational data-entry user.

RP-OWNER-002 — Full Business Visibility
Status: LOCKED
Owner must have read access to the full authorized business view, including relevant:
Investors
Investor fund positions
Vehicles
Vehicle expenses
Sales
Receivables
Labour
Profit / Loss
Investor shares
Owners Pool
Owner shares
Settlements
Percentage-change history
Corrections
Reports
Audit information
Operational statuses

RP-OWNER-003 — Operational Read-Only
Status: LOCKED — CRITICAL
Owner must not perform normal operational writes.
Owner must not normally:
Create vehicles
Edit vehicle operations
Add expenses
Enter sales
Perform financial corrections
Modify investor funds
Modify operational records
Owner remains read-only unless a future rule explicitly grants a specific exception.

RP-OWNER-004 — Flexible Filtering
Status: LOCKED
Owner must be able to filter and inspect business information using relevant criteria such as:
Tenant
Investor
Vehicle
Date range
Vehicle status
Sale status
Payment status
Settlement status

RP-OWNER-005 — Multi-Tenant Owner View
Status: LOCKED
When multiple tenants are active, Owner must support:
Individual tenant view
Combined authorized business view

F. OWNER AI
RP-AI-001 — Owner-Only AI Access
Status: LOCKED
Current AI access is for Owner only.
Accountant, Investor, Media, and Labour do not receive AI access in the current scope.

RP-AI-002 — Read-Only AI
Status: LOCKED
AI may:
Query
Explain
Summarize
Analyse
verified system information.
AI must not:
Create data
Modify data
Delete data
Perform financial transactions
Change permissions
Change percentages

RP-AI-003 — AI Is Not the Financial Source of Truth
Status: LOCKED — CRITICAL
Preferred model:
Verified database/query logic
→ Deterministic result
→ AI explanation
The AI model must not invent authoritative financial values.

G. ACCOUNTANT / OPERATIONS ADMIN
RP-ACC-001 — Main Operational Role
Status: LOCKED
Accountant is the primary day-to-day operational user.
For normal non-protected business operations, Accountant receives:
View
Create
Edit
Manage
Controlled Correction
permissions where applicable.

H. INVESTOR MANAGEMENT
RP-ACC-INV-001 — Investor Operations
Status: LOCKED
Accountant may manage:
Investor creation
Investor basic information
Investor account creation
Investor status
Initial fund
Additional fund
Investor financial position
Investor history
Exit workflow
Settlement operations

I. INVESTOR ENTITY MODEL
RP-INV-MODEL-001 — Investor Is Global
Status: LOCKED — CRITICAL
Investor is a global business-level entity.
Investor is not owned by a Tenant.
Do not create separate duplicate Investor identities such as:
Investor X — Tenant A
Investor X — Tenant B
for the same real investor.

RP-INV-MODEL-002 — No Mandatory Direct Investor–Tenant Ownership
Status: LOCKED
Investor does not require a permanent direct Tenant/Garage ownership relationship.
An Investor may:
Invest only in one tenant
Invest in multiple tenants
Have future relationships with other business areas
without duplicating the investor identity.

RP-INV-MODEL-003 — Global Investor Fund
Status: LOCKED
Investor has one global fund position.
Example:
Total Fund: ₹10,00,000
Vehicle in Tenant A uses:
₹4,00,000
Vehicle in Tenant B uses:
₹3,00,000
Then:
Total Fund = ₹10,00,000
Fund Used = ₹7,00,000
Available Fund = ₹3,00,000
Tenant-wise duplicate fund balances must not be created for the same investor.

RP-INV-MODEL-004 — Fund Movement Must Remain Traceable
Status: LOCKED
Even though the Investor fund is global, each relevant fund movement must remain traceable to its business context.
Where applicable, history should identify:
Investor
Vehicle
Tenant/Garage context
Amount
Date
Transaction type
This provides traceability without turning the Investor into a tenant-owned entity.

J. VEHICLE ↔ INVESTOR RELATIONSHIP
RP-ACC-VEH-001 — Vehicle Management
Status: LOCKED
Accountant may manage:
Vehicle creation
Purchase details
Investor assignment
Tenant/Garage assignment
Vehicle details
Vehicle status
Vehicle expenses
Sale
Buyer
Receivables
Payments

RP-ACC-VEH-002 — One Vehicle, One Investor
Status: LOCKED — CRITICAL
The rule is:
One Vehicle → One Investor
Two Investors must not jointly fund the same vehicle.
However:
One Investor → Multiple Vehicles
is fully allowed.
There must never be a rule stating:
One Investor → One Vehicle

K. VEHICLE ↔ TENANT RELATIONSHIP
RP-VEH-TENANT-001 — Current Tenant
Status: LOCKED
A vehicle must have a current operational Tenant/Garage context.

RP-VEH-TENANT-002 — Historical Tenant Context
Status: LOCKED
If a vehicle moves between garages/tenants, its historical location/tenant information must not be silently lost.

L. VEHICLE EXPENSES
RP-ACC-EXP-001 — Vehicle-Based Expenses
Status: LOCKED
Vehicle expenses are primarily vehicle-based.
Each relevant expense must belong to the vehicle that caused the expense.

RP-ACC-EXP-002 — Expense Management
Status: LOCKED
Accountant may:
Add vehicle expenses
Edit legitimate entries
Perform controlled corrections
View expense history
View total vehicle expense

RP-ACC-EXP-003 — Dynamic Expense Categories
Status: LOCKED
Expense categories must not be permanently hard-coded.
Accountant may add new operational expense categories through the application.

RP-ACC-EXP-004 — No Separate Garage Expense Module in Current Core Scope
Status: LOCKED CURRENT SCOPE
The current core expense model does not require a separate general Garage Expense module.
Vehicle-related costs should remain attached to vehicles.
Future non-vehicle operational expense requirements may be added later if the business requires them.

M. INVESTOR PROFIT PERCENTAGE
RP-PROFIT-001 — Initial Investor Percentage
Status: LOCKED
Accountant may set the agreed investor-specific profit percentage during Investor setup.

RP-PROFIT-002 — Investor Percentage Changes
Status: LOCKED
Accountant may make a legitimate change to an existing Investor-specific percentage.
Mandatory audit information:
Previous value
New value
Changed by
Date/time
Investor
Applicable scope

RP-PROFIT-003 — Owner Notification
Status: LOCKED
Owner must be able to see relevant percentage-change notifications/history.
Owner approval is not required for the normal Accountant-controlled change.

RP-PROFIT-004 — Historical Deals Cannot Change
Status: LOCKED — CRITICAL
Changing the current percentage must not recalculate completed historical deals.

RP-PROFIT-005 — System/Tenant Defaults
Status: LOCKED
System-level or Tenant-level default profit configuration belongs to:
Back Office
not the normal Accountant workflow.

N. SALES & RECEIVABLES
RP-ACC-SALE-001 — Sale Management
Status: LOCKED
Accountant may manage:
Full-payment sale
Partial-payment sale
Credit sale
Buyer information
Amount received
Pending amount
Receivables
Payment completion

RP-ACC-SALE-002 — Two Payment States
Status: LOCKED
The current simple payment-state model is:
Pending / Partially Received
The full amount has not yet been received.
Fully Received
The full agreed amount has been received.
The UI must also show the actual values:
Total Amount
Amount Received
Amount Pending

RP-ACC-SALE-003 — Actual Payment Drives Recovery
Status: LOCKED — CRITICAL
Only money actually received may be treated as received/recovered funds.
Unreceived receivables must never be treated as available money.

O. LOSS HANDLING
RP-LOSS-001 — No Separate Loss Workflow
Status: LOCKED CURRENT SCOPE
A separate:
Loss allocation module
Loss responsibility selector
Owner-vs-Investor loss configuration
Special loss transaction workflow
is not required.
If:
Sale Price − Total Vehicle Cost
is negative, the result may simply be shown as a loss.
Rare business exceptions should be handled through legitimate existing operational/correction mechanisms instead of introducing unnecessary loss-specific complexity.

P. FINANCIAL CORRECTIONS
RP-CORR-001 — Accountant Correction Authority
Status: LOCKED
Accountant may perform legitimate controlled corrections to applicable financial records.

RP-CORR-002 — Correction Audit
Status: LOCKED — CRITICAL
Corrections must preserve:
Previous value
Corrected value
Changed by
Date/time
Reason where applicable
Old financial truth must not be silently erased.

Q. LABOUR MODULE
RP-ACC-LAB-001 — Separate Simple Labour Module
Status: LOCKED
Labour must exist as a separate module.
The current module must remain deliberately simple.

RP-ACC-LAB-002 — Current Labour Operations
Status: LOCKED
Accountant may:
Create Labour
Edit basic Labour information
View Labour list
Activate/Deactivate Labour when required
Record a salary/payment
Enter payment amount
Enter payment date
Add an optional note
View payment history

RP-ACC-LAB-003 — No Fixed Salary Requirement
Status: LOCKED
A Labour record does not require a permanent fixed salary value.
The Accountant enters the amount each time a salary/payment is made.
Example:
Labour: Worker A
Date: 07-10-2026
Amount: ₹8,000
A later payment may have a different amount.

RP-ACC-LAB-004 — Labour Features Not Required Now
Status: LOCKED CURRENT SCOPE
Current Labour module does not require:
Attendance
Automatic payroll
Fixed monthly salary engine
Vehicle assignment
Work-type assignment
Individual vehicle labour costing
Detailed workforce scheduling
The architecture should not unnecessarily block future expansion.

R. NO CASH/BANK ACCOUNT MODULE IN CURRENT SCOPE
RP-FIN-001 — Dedicated Cash/Bank Account Management Not Required
Status: LOCKED CURRENT SCOPE
The current system does not require a dedicated:
Cash Account creation module
Bank Account creation module
Bank-wise balance module
Cash-vs-Bank operational ledger
The system must track required business fund and transaction amounts without forcing a Cash/Bank account architecture that the current business does not need.
A future financial account module may be introduced if later required.

S. INVESTOR ROLE
RP-INV-001 — Own Financial Information
Status: LOCKED
Investor may view their own relevant financial information.
Investor must not access another Investor's private financial data.

RP-INV-002 — Investor Dashboard
Status: LOCKED
Investor may view relevant own information including:
Total Fund
Available Fund
Fund Used
Recovered Principal
Profit Earned
Profit Paid
Profit Pending
Vehicles
Settlement Status

RP-INV-003 — Own Vehicles First
Status: LOCKED
Investor vehicle experience should prioritize:
My Vehicles
Relevant own vehicle information may include:
Capital used
Expenses
Status
Sale information
Investor share
Settlement information

RP-INV-004 — Financial Information Is Read-Only
Status: LOCKED
Investor must not manually modify authoritative financial values.

T. OTHER / PUBLIC VEHICLES FOR INVESTORS
RP-INV-PUBLIC-001
Status: LOCKED
Investor may view permitted public-level information for other vehicles.

RP-INV-PUBLIC-002 — Internal Information Forbidden
Status: LOCKED
Investor must not see another vehicle's:
Investor identity
Investor fund
Purchase cost
Internal expenses
Internal profit
Owner shares
Private financial information

U. INVESTOR EXIT
RP-EXIT-001 — Exit Request
Status: LOCKED
Investor may submit a normal exit request.
Submitting an exit request does not immediately close the Investor.

RP-EXIT-002 — Exceptional Early Closure
Status: LOCKED
Exceptional early closure may be operationally initiated/managed by Accountant.
It must be audited.
It does not override actual recovery, locked funds, receivables, or settlement rules.

V. MEDIA USER
RP-MEDIA-001 — Role Purpose
Status: LOCKED
Media User handles limited public-facing vehicle/media operations.

RP-MEDIA-002 — Allowed Access
Status: LOCKED
Media User may:
Upload vehicle photos
View permitted vehicle public details
Edit permitted public-facing fields
Manage publication status
Update permitted public/operational vehicle status

RP-MEDIA-003 — Financial Restrictions
Status: LOCKED — CRITICAL
Media User must not access:
Investor fund
Investor private data
Purchase cost
Internal expenses
Internal profit/loss
Investor share
Owner shares
Settlement finance
Financial corrections
Protected configuration

W. LABOUR ACCESS
RP-LAB-001 — No Labour Login
Status: LOCKED
Labour has:
No login
No dashboard
No portal
in the current scope.
Labour is managed by Accountant.

X. PUBLIC / EXTERNAL VEHICLE VIEW API
RP-PUBLIC-API-001 — Public Vehicle API
Status: LOCKED
The system must provide a flexible read-only API for public vehicle viewing.
Possible consumers include:
Public website
Mobile application
Vehicle catalog
Approved external frontend
Future marketing website
This API is not a user role.

RP-PUBLIC-API-002 — Minimum Default Data
Status: LOCKED
The default public response should expose only minimum safe public information.
Initial public fields may include:
Public Vehicle ID
Vehicle Name / Make / Model
Main/Public Image
Public Display Price
Public Availability / Status
Short Description when available

RP-PUBLIC-API-003 — Flexible Public Fields
Status: LOCKED
The API must be extensible.
Future approved public fields may include:
Year
Colour
Mileage
Fuel
Transmission
Variant
Features
Location
Promotional Price
Video
Featured status
Adding future public fields must not require redesigning the API.

RP-PUBLIC-API-004 — Minimum Data by Default
Status: LOCKED — PRIVACY PRINCIPLE
The backend must not serialize the entire internal vehicle model and rely on the frontend to hide sensitive fields.
Use a dedicated public response schema/serializer.

RP-PUBLIC-API-005 — Internal Information Must Never Be Public
Status: LOCKED — CRITICAL
Public API must not expose:
Investor identity/private data
Investor fund
Purchase cost
Internal expenses
Internal profit/loss
Investor share
Owner shares
Internal financial corrections
Internal audit data
Protected settings

RP-PUBLIC-API-006 — Published Vehicles Only
Status: LOCKED
Only vehicles explicitly eligible for public display should appear in the public API.

RP-PUBLIC-API-007 — Pagination and Media Efficiency
Status: LOCKED
Public vehicle lists must:
Use pagination/incremental loading
Avoid unbounded results
Use optimized image variants
Avoid returning full-resolution originals for cards/lists

Y. BACK OFFICE
RP-BO-001 — Back Office Purpose
Status: LOCKED
Back Office is the system-level administration layer.
It is not the normal day-to-day business operations interface.

RP-BO-002 — Back Office Responsibilities
Status: LOCKED
Back Office may manage:
Tenant creation
Tenant configuration
Tenant status
Owner accounts
Accountant accounts
Tenant assignments
System defaults
Tenant-level protected defaults
Protected configuration
Future controlled tenant consolidation if implemented

RP-BO-003 — Sensitive Changes
Status: LOCKED
Sensitive changes must require:
Strong warning
Current/old value
New value
Affected scope
Explicit confirmation
Audit record

Z. DJANGO ADMIN — INTERIM SYSTEM ADMINISTRATION
RP-DJANGO-001 — Temporary Administration Interface
Status: LOCKED
Until the Back Office UI is built, Django Admin may temporarily perform system-level provisioning.

RP-DJANGO-002 — Current Django Admin Responsibilities
Status: LOCKED
Django Admin may currently be used for:
Tenant creation
Tenant configuration
Owner creation
Accountant creation
Tenant assignments
Initial system configuration

RP-DJANGO-003 — Not the Daily Operations UI
Status: LOCKED — CRITICAL
Normal business operations must not be designed around Django Admin.
Operations such as:
Investors
Vehicles
Expenses
Sales
Receivables
Labour
belong to the normal application UI/API.

AA. ACCOUNT PROVISIONING OWNERSHIP
RP-ACCOUNT-001 — Owner Accounts
Status: LOCKED
Owner accounts:
Django Admin now
→ Back Office later

RP-ACCOUNT-002 — Accountant Accounts
Status: LOCKED
Accountant accounts:
Django Admin now
→ Back Office later

RP-ACCOUNT-003 — Investor Accounts
Status: LOCKED
Investor accounts are created/managed operationally by Accountant.

RP-ACCOUNT-004 — Media Accounts
Status: LOCKED
Media accounts are created/managed operationally by Accountant.

RP-ACCOUNT-005 — Labour
Status: LOCKED
Labour has no authenticated account in the current scope.

AB. LARGE / FINANCIAL FORM SAFEGUARD
RP-FORM-001 — Review Before Final Commit
Status: LOCKED
Large, multi-section, or financially important forms should use a review step where appropriate:
Fill
→ Review
→ Confirm
→ Save
This is especially important on mobile/tablet.

AC. DEFAULT FUTURE PERMISSION INHERITANCE
RP-DEFAULT-001 — Owner
Status: LOCKED
For new normal operational modules:
Owner → View by default
unless explicitly restricted.

RP-DEFAULT-002 — Accountant
Status: LOCKED
For new normal operational modules:
Accountant → Operational access by default
unless the feature is explicitly protected.

RP-DEFAULT-003 — Investor
Status: LOCKED
Investor receives no automatic access to future modules.
Explicit permission is required.

RP-DEFAULT-004 — Media
Status: LOCKED
Media receives no automatic access to future modules.
Explicit permission is required.

AD. PERMISSION MATRIX
Capability
Owner
Accountant
Investor
Media
Back Office / Django Admin
Full business view
Read-only
Operational scope
No
No
Administrative scope
Tenant data
Authorized tenants
Assigned tenants
Own permitted data
Permitted public scope
Yes
Create Owner
No
No
No
No
Yes
Create Accountant
No
No
No
No
Yes
Create Investor
No
Yes
No
No
No
Create Media User
No
Yes
No
No
No
Create Labour
No
Yes
No
No
No
Record Labour Payment
Read
Yes
No
No
No
Create Vehicle
No
Yes
No
No
No
Edit Vehicle Operations
No
Yes
No
Limited
No
Vehicle Expenses
Read
Manage
Own applicable view
No
No
Investor Fund
Read
Manage
Own read-only
No
No
Investor % Initial Set
Read
Yes
Own view where applicable
No
Default config only
Investor % Change
Read + notification
Yes, audited
Own view
No
Default config only
System/Tenant Default Profit Config
Read
No
No
No
Yes
Sale / Receivables
Read
Manage
Own view
No
No
Financial Correction
Read
Yes, audited
No
No
No
Public Vehicle Media
Read
Yes
Read
Yes
No
Public Vehicle Details
Read
Yes
Read
Permitted edit
No
Reports
Full read
Operational
Own applicable
No
Administrative if required
AI
Read-only
No
No
No
No
Investor Exit Request
View
Manage
Submit
No
No
Exceptional Early Closure
View
Manage, audited
No
No
No
Tenant Creation
No
No
No
No
Yes
Tenant Assignment
No
No
No
No
Yes
Tenant Merge/Consolidation
No
No
No
No
Only if separately implemented


AE. NON-OVERRIDABLE RULES
Status: LOCKED — CRITICAL
The following rules must not be bypassed:
Owner remains operationally read-only.
Accountant cannot create Owner accounts.
Accountant cannot create Accountant accounts.
Investor cannot edit authoritative financial values.
Investor cannot access another Investor's private financial information.
Media cannot access internal finance.
Public API cannot expose internal financial information.
Tenant isolation is backend-enforced.
Cross-tenant access must be explicitly assigned.
Labour has no login in the current scope.
One Vehicle can have only one Investor.
One Investor may fund multiple Vehicles.
Investor identity is global, not tenant-owned.
Investor fund position is global, not duplicated per tenant.
Historical financial truth must not be rewritten by permission changes.
Tenant consolidation must never silently rewrite historical financial truth.
Unreceived sale money must never be treated as received/available funds.

AF. SUPPORTING DOCUMENTS
The following topics are intentionally separated from this document.
01 — Business Rules
Authoritative source for:
Investor fund logic
Vehicle costing
Profit calculation
Sale logic
Exit rules
Historical financial rules
Authentication & Account Security
Defines:
Login
Password rules
Password reset
Forgot-password flow
Session security
Login protection
Authentication mechanisms
Tenant Merge & Consolidation Architecture
Supporting architecture document defining, only if needed:
Source/target tenant behavior
Historical preservation
User reassignment
Vehicle reassignment
Conflict handling
Merge audit
Rollback/recovery
Global Investor preservation
Tenant Merge is deliberately not implemented as a core operational workflow unless it can be supported safely and without disproportionate complexity.

AG. LOCKED PRINCIPLES SUMMARY
Tenant
Multi-Tenant From Day One
Garage = Tenant
Explicit Tenant Assignment
Tenant Resolver From Initial Implementation
Backend-Enforced Tenant Isolation

Investor
Investor = Global Business Entity
Investor Is Not Tenant-Owned
Global Investor Fund
One Investor → Many Vehicles
One Vehicle → One Investor

Owner
Full Read Visibility
No Normal Operational Writes
Cross-Tenant Authorized View Supported
Read-Only AI

Accountant
Primary Operational Role
Manages Investors, Vehicles, Expenses, Sales, Receivables, Labour and Corrections
Creates Investor and Media Accounts
Manages Investor-Specific Profit Percentages

Labour
Separate Simple Module
Create Labour
Record Manual Payment
No Fixed Salary Requirement
No Payroll Complexity in Current Scope

Media
Public Vehicle / Media Operations
No Internal Finance

Public API
Read-Only Vehicle API
Minimum Public Data by Default
Flexible Future Fields
Dedicated Public Schema
No Internal Finance Exposure

Financial Accounts
No Dedicated Cash/Bank Account Module in Current Scope

Back Office
System/Tenant Administration
Owner + Accountant Account Provisioning
Tenant Management
Protected Defaults
Possible Future Tenant Consolidation

Current Administration
Django Admin Temporarily Performs Back Office Provisioning
Django Admin Is Not the Daily Business Interface

DOCUMENT STATUS
02 — USER ROLES & PERMISSIONS
Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH
This document is authoritative for:
Roles
Permissions
Tenant access
Tenant isolation
Operational authority
Administrative authority
Account provisioning ownership
Investor scope
Labour access
Media access
Public Vehicle API access
AI access
Authentication and password mechanics are intentionally maintained in a separate security document.
Tenant Merge/Consolidation is intentionally maintained as a separate supporting architecture topic and must not add unnecessary complexity to the core application.
—--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Create “03 — System Modules” for the Vehicle Investment, Modification & Resale Management System. Use 01 — Business Rules and 02 — User Roles & Permissions as authoritative sources. Do not invent new business logic, change locked rules, or duplicate Authentication/Password rules. Keep the document concise, implementation-ready, and fully in English.

SYSTEM MODULES TO DEFINE:

1. Dashboard — Role-based dashboards for Owner, Accountant, and Investor. Owner must have full read-only business visibility across Investors, Investor Funds, Vehicles, Expenses, Sales, Receivables, Profit/Loss, Labour, Settlements, Audit, Reports, tenant-wise data, and combined authorized tenant data. Sensitive credentials/secrets are never included.

2. Investor Management — Global Investor profile, basic details, status, vehicle portfolio, exit state, settlement state, and complete history. Investor is a global business entity, not tenant-owned.

3. Investor Fund / Ledger — Initial Fund, Additional Fund, Total Fund, Available Fund, Fund Used, Recovered Principal, Profit Earned, Profit Paid, Profit Pending, and fund history. Investor fund is global; individual fund movements must remain traceable to the related vehicle and tenant context where applicable.

4. Vehicle Management — Vehicle creation, purchase information, Investor assignment, Tenant/Garage assignment, vehicle details, status, history, transfer history, and sold-vehicle history. Enforce One Vehicle → One Investor and allow One Investor → Multiple Vehicles. Current lifecycle: Purchased → In Work → Ready → Listed → Sold.

5. Vehicle Expense Management — Vehicle-based expenses, dynamic expense categories, individual entries, total vehicle expense, category totals, and controlled correction history. General Garage Expense management is not part of the current scope.

6. Sales — Vehicle sale, Buyer details, Agreed Sale Price, Full Payment, Partial Payment, Credit Sale, and sale history.

7. Receivables & Payment Tracking — Total Sale Price, Amount Received, Pending Amount, payment history, and two primary states: Pending/Partially Received and Fully Received. Only actually received money may be treated as received/recovered funds.

8. Profit & Distribution — Vehicle Profit/Loss, Investor-specific profit share, Owners Pool, Owner 1 share, Owner 2 share, historical percentage snapshots, and percentage-change history. Profit must be derived from authoritative vehicle/sale/expense data, not manually entered as the normal workflow.

9. Investor Exit & Settlement — Exit request, Terms & Conditions, 3-month notice, Settlement Pending, final settlement, exceptional early closure, and exit history.

10. Labour — Separate but intentionally simple module: create Labour, edit basic details, list/view, Active/Inactive when required, manual salary/payment entry, payment amount, date, optional note, and payment history. No fixed salary, attendance, payroll automation, vehicle assignment, work-type tracking, or detailed labour costing in the current scope.

11. Buyer / Customer — Lightweight sales-related entity/module for buyer details, purchased vehicle history, sale association, and receivable association. Do not build a full CRM.

12. Media / Vehicle Publication — Vehicle image upload, public-facing vehicle details, display price, publication status, permitted public vehicle status, and media management. Internal financial data must remain inaccessible.

13. Public Vehicle Access — Published vehicle catalog plus a flexible read-only Public Vehicle API for websites, mobile apps, and approved external frontends. Default response must contain minimum safe public data such as Public Vehicle ID, Vehicle Name/Make/Model, Main/Public Image, Display Price, Public Availability/Status, and optional Short Description. Future public fields may be added without redesigning the API. Never expose Investor data, Investor Fund, Purchase Cost, Internal Expenses, Profit, Owner Shares, Financial Corrections, or Audit data. Use pagination and optimized image variants.

14. Reports — Investor, Fund, Vehicle, Expense, Sales, Receivables, Profit, Labour Payment, Tenant, and Owner consolidated reports. Owner must be able to access all authorized business reporting data in read-only form.

15. Audit & Correction History — Track Investor fund changes, expenses, sales, buyer payments, percentage changes, settlements, financial corrections, important configuration changes, and exceptional closure actions. Historical financial truth must never be silently overwritten.

16. Tenant / Garage Management — Tenant/Garage information, tenant configuration, user assignments, current tenant context, tenant isolation, and vehicle tenant history. The system is multi-tenant from day one, with Garage = Tenant. Tenant Merge is not a normal operational module.

17. User & Permission Management — Owner provisioning, Accountant provisioning, Investor account provisioning, Media account provisioning, role assignment, tenant assignment, and account activation/deactivation. Authentication, passwords, password recovery, login security, and sessions belong to a separate Authentication document.

18. Back Office — Tenant creation/configuration, Owner and Accountant provisioning, tenant assignments, system defaults, tenant defaults, and protected configuration. Django Admin temporarily performs these system-level provisioning functions until Back Office is built.

19. System / Business Configuration — Investor profit defaults, Owner split configuration, tenant-specific defaults, protected business configuration, and other configurable business values. Do not hard-code configurable business percentages.

20. GST / Tax / Invoice Capability — Support applicable GST/Tax/Invoice information without making tax fields mandatory for every transaction in the current phase. Do not build a full accounting/tax suite unless later required.

21. Owner AI Assistant — Owner-only, read-only AI over verified system data. It may query, summarize, explain, and analyse but must never create, modify, delete, or become the source of financial truth.

CROSS-CUTTING CAPABILITIES, NOT SEPARATE BUSINESS MODULES: Search & Filtering, Notifications, Tenant Resolver, Pagination, Authentication, Audit Logging Infrastructure, shared media optimization, shared error handling, and shared permission enforcement.

INTENTIONALLY OUT OF CURRENT SCOPE: Dedicated Cash/Bank Account Module, General Garage Expense Module, Full Payroll Module, Attendance Module, Full CRM, Separate Loss Allocation Module, Labour work/vehicle-assignment workflow, and Tenant Merge as a normal user-facing operation.

TENANT MERGE NOTE: The architecture should not unnecessarily block future tenant consolidation. If two tenants/garages ever need to be merged, the detailed process must be defined in a separate supporting document called “Tenant Merge & Consolidation Architecture.” It should be a Back Office/system-level controlled operation only if it can be implemented safely without disproportionate complexity. Historical identities and financial truth must not be silently rewritten.

CORE BUSINESS FLOW: Investor → Investor Fund → Vehicle → Vehicle Expense → Sale → Receivable/Payment → Profit Distribution → Settlement.

Create the final “03 — System Modules” document from this structure. For each module, define only its Purpose, Core Responsibilities, Main Data/Views, Role Ownership, Tenant Scope, and Explicit Non-Scope. Keep the document concise and avoid repeating business formulas or permission rules already defined in Documents 01 and 02.

