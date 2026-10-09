04 — DATA MODEL & RELATIONSHIPS
Vehicle Investment, Modification & Resale Management System
Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH
A. Purpose & Authority
This document defines the authoritative conceptual data model for the platform.
It defines:
Persistent business entities
Immutable identities
Global vs Tenant ownership
Entity relationships and cardinalities
Financial source-of-truth structures
Historical snapshots
Transaction history
Derived vs stored values
Data-retention rules
Integrity boundaries
Tenant-isolation requirements
01 — Business Rules remains authoritative for business and financial rules.
02 — User Roles & Permissions remains authoritative for authorization, operational authority, and Tenant access.
03 — System Modules remains authoritative for module boundaries.
This document translates those locked requirements into a relational data architecture without redefining them.

B. GLOBAL DATA PRINCIPLES
DM-CORE-001 — Immutable UUID Identity
Every persistent business/system entity must use a backend-generated immutable UUID as its primary system identity.
Human-readable values are attributes only.
Therefore:
Investor Name ≠ Investor ID
Buyer Name ≠ Buyer ID
Buyer Phone Number ≠ Buyer ID
Labour Name ≠ Labour ID
Vehicle Registration Number ≠ Vehicle ID
Garage Name ≠ Tenant ID
Username ≠ User ID
Relationships must use immutable entity identities rather than names, numbers, labels, or other editable values.

DM-CORE-002 — Financial Precision
Authoritative money values must use fixed-precision decimal/numeric storage.
Floating-point types must not be used for financial truth.
Percentages must also use controlled fixed-precision values.
Phone numbers and identifier-like values must be stored as strings.

DM-CORE-003 — Single Source of Truth
An important business value must not have multiple independently editable sources of truth.
Examples:
Total Vehicle Expense derives from Vehicle Expense records.
Amount Received derives from Sale Payment records.
Pending Amount derives from Sale and Payment data.
Investor Fund balances derive from authoritative fund activity.
Vehicle Profit/Loss derives from authoritative financial data.
Historical completed-deal calculations use immutable snapshots.
Cached or materialized totals may later exist for performance, but they must remain rebuildable and must never become independent financial truth.

DM-CORE-004 — Historical Integrity
Important history must survive:
Rename
Deactivation
Investor closure
Vehicle sale
Tenant transfer
User deactivation
Configuration changes
Percentage changes
Financial corrections
Historical financial data must not be silently deleted or rewritten.

DM-CORE-005 — Time
Important records must use timezone-aware timestamps.
Relevant records should support:
Created At
Updated At where legitimate
Effective Date/Time
Created By / Changed By where required

C. ENTITY SCOPE CLASSIFICATION
Entity
Scope
Tenant / Garage
Global system entity defining an operational Tenant
User
Global system identity
Role / Permission
System-level
Tenant Membership
Relationship / Tenant-scoped authorization
Business Owner / Profit Recipient
Global business entity
Investor
Global business entity
Investor Fund Ledger
Global Investor ledger with Tenant/Vehicle context
Investor Profit Ledger
Global Investor financial activity with contextual references
Vehicle
Tenant-scoped operational entity linked to a global Investor
Vehicle Tenant History
Historical relationship
Expense Category
Tenant-scoped configuration entity
Vehicle Expense
Tenant-scoped transaction through Vehicle
Buyer
Tenant-scoped business entity
Sale
Tenant-scoped transaction
Sale Payment
Tenant-scoped transaction through Sale
Profit Agreement
Global Investor agreement/history
Owner Split Configuration
System/Tenant configuration
Profit Distribution Snapshot
Immutable financial snapshot
Investor Exit Request
Global Investor lifecycle record
Settlement
Global Investor settlement with contextual records
Labour
Tenant-scoped entity
Labour Payment
Tenant-scoped transaction
Media Asset
Tenant-scoped through Vehicle
Vehicle Publication
Tenant-scoped through Vehicle
Audit Record
System record with optional Tenant context
Business Configuration
System or Tenant scoped

Investor and its principal Fund must never be duplicated per Tenant.

D. TENANT / USER / MEMBERSHIP MODEL
1. Tenant
Identity: UUID
Scope: System-level operational boundary
Core conceptual fields:
ID
Name
Status
Basic business details
Created At
Updated At
Archived/Inactive state where applicable
Relationships:
Tenant 1 → many Vehicles
Tenant 1 → many Labour records
Tenant 1 → many Tenant Memberships
Tenant 1 → many Tenant configuration versions
Tenant 1 → many Buyer records
Current Garage count must not be hard-coded.

2. User
Identity: UUID
Scope: Global system identity
A User must not be duplicated simply because access spans multiple Tenants.
Authentication credentials remain part of the separate Authentication architecture.

3. Role and Permission
Roles and permissions are system-level authorization definitions.
Conceptually:
User → Role/Permission → Tenant Scope → Resource
Detailed permission behavior remains controlled by Document 02.

4. Tenant Membership
Tenant Membership links a User to an authorized Tenant context.
Relationships:
User 1 → many Tenant Memberships
Tenant 1 → many Tenant Memberships
The architecture must support:
One User → One Tenant
One User → Multiple explicitly assigned Tenants
A supplied Tenant UUID must never independently grant access.

E. BUSINESS OWNER / PROFIT RECIPIENT MODEL
Business Owner
Business Owners must not be represented only as fixed owner_1 and owner_2 database columns.
Use a persistent BusinessOwner / ProfitRecipient entity.
Core conceptual fields:
UUID
Display Name
Status
Optional linked Owner User
Created At
A Business Owner and an authenticated User are related concepts but not necessarily the same record.
This permits additional future Owners without redesigning the schema.

F. INVESTOR & INVESTOR FUND MODEL
1. Investor
Identity: UUID
Scope: Global
Core conceptual fields:
UUID
Name
Basic contact/details
Lifecycle Status
Current applicable Profit Agreement reference
Created At
Updated At
Relationships:
Investor 1 → many Vehicles
Investor 1 → many Investor Fund Ledger Entries
Investor 1 → many Investor Profit Ledger Entries
Investor 1 → many Profit Agreements
Investor 1 → many Exit Requests over lifetime
Investor 1 → many Settlements
Investor 0..1 → User account where applicable
No mandatory Investor → Tenant ownership relationship is permitted.
Closing or deactivating an Investor must not delete historical data.

2. Investor Fund Ledger
Identity: UUID
Scope: Global Investor financial ledger
Investor principal must use an auditable transaction model rather than a single manually editable balance.
Supported conceptual transaction types include:
Initial Fund
Additional Fund
Vehicle Purchase Use
Vehicle Expense Use
Principal Recovery
Correction / Reversal
Each entry should contain:
UUID
Investor
Amount
Transaction Type
Financial Effect
Vehicle where applicable
Tenant context where applicable
Source Record reference
Effective Date/Time
Actor
Reversal/Correction reference where applicable
Derived Fund Position
The following are derived/reconciled values:
Total Fund
Available Fund
Fund Used
Recovered Principal
Investor Fund is global, but every applicable movement remains traceable to the Vehicle and Tenant where the business event occurred.

3. Investor Profit Ledger / Entitlement
Principal and Profit must remain separate.
Use a separate Investor profit structure capable of representing:
Profit Earned
Profit Paid
Profit Pending
Legitimate correction/reversal
Investor profit must not automatically become principal.
Relationships should allow a Profit Entitlement to reference:
Investor
Vehicle
Sale
Profit Distribution Snapshot
Tenant context
Settlement where applicable
Calculated entitlement and actual payment are separate states.

G. VEHICLE & TENANT HISTORY MODEL
1. Vehicle
Identity: UUID
Scope: Tenant-scoped operational entity
Core conceptual fields:
UUID
Current Tenant
Investor
Make / Model / Variant and other business attributes
Registration Number where available
Purchase Cost
Purchase Date/details
Current Status
Work/Modification information
Created At
Updated At
Relationships:
Investor 1 → many Vehicles
Vehicle many → 1 Investor
Tenant 1 → many Vehicles
Vehicle many → 1 Current Tenant
A Vehicle must have exactly one funding Investor.
Registration Number is not system identity.
Current lifecycle:
Purchased → In Work → Ready → Listed → Sold

2. Vehicle Tenant History
Vehicle movement between Garages/Tenants must be preserved.
Core conceptual fields:
UUID
Vehicle
From Tenant
To Tenant
Effective Date/Time
Actor
Optional Reason/Note
Relationships:
Vehicle 1 → many Tenant History records
Changing the current Tenant must never overwrite historical Tenant context.

H. VEHICLE EXPENSE & CAPITAL MODEL
1. Expense Category
Identity: UUID
Scope: Tenant-scoped configuration
Core fields:
UUID
Tenant
Name
Active/Inactive
Created By
Created At
Expense categories are dynamic.
Their names must not be hard-coded as permanent application constraints.
Initial categories may be seeded, while Accountants may add Tenant-specific categories through the application.

2. Vehicle Expense
Identity: UUID
Scope: Tenant-scoped through Vehicle
Core fields:
UUID
Vehicle
Expense Category
Amount
Expense Date
Optional Description/Note
Created By
Created At
Correction/Reversal reference where applicable
Relationships:
Vehicle 1 → many Vehicle Expenses
Expense Category 1 → many Vehicle Expenses
Vehicle Expense → relevant Investor Fund Ledger entry
Every expense must use the Investor belonging to that Vehicle.
An expense must never debit another Investor.

3. Vehicle Capital Source of Truth
Total Vehicle Cost is reconstructed from authoritative source data:
Purchase Cost + Valid Vehicle Expenses
A separate independently editable Vehicle Capital total must not exist.
Vehicle Purchase and Vehicle Expense fund effects must be linked to the corresponding Investor Fund Ledger movements.
A separate persistent Vehicle Capital Ledger is not required as a competing source of truth; if a later reporting projection is introduced, it must remain fully derived/rebuildable.

I. BUYER / SALE / PAYMENT / RECEIVABLE MODEL
1. Buyer
Identity: UUID
Scope: Tenant-scoped in the current architecture
Core fields:
UUID
Tenant
Buyer Name
Phone Number — Required
Secondary Phone — Optional
Address — Optional
Notes — Optional
Status where required
Created At
Updated At
Phone numbers must be stored as strings.
Buyer Phone Number is not system identity and must not automatically be globally unique.
Relationships:
Tenant 1 → many Buyers
Buyer 1 → many Sales
A returning Buyer within the same Tenant should reuse the existing Buyer record rather than creating a new Buyer for every Sale.
Cross-Tenant customer identity unification is not required in the current scope.

2. Sale
Identity: UUID
Scope: Tenant-scoped through Vehicle
Core fields:
UUID
Vehicle
Buyer
Tenant Context
Agreed Total Sale Price
Sale Date
Sale Type where applicable
Payment State
Profit Distribution Snapshot reference
Created By
Timestamps
Relationships:
Vehicle 1 → 0..1 authoritative Sale in the current normal lifecycle
Buyer 1 → many Sales
Sale 1 → many Sale Payments
Sale 1 → 0..1 finalized Profit Distribution Snapshot
Cancellation/resale workflows are not introduced by this document.

3. Sale Payment
Identity: UUID
Scope: Tenant-scoped transaction
Each actual receipt must be preserved individually.
Core fields:
UUID
Sale
Amount
Received At
Optional Reference/Note
Recorded By
Correction/Reversal reference
Created At
Relationships:
Sale 1 → many Sale Payments
Amount Received derives from valid payment transactions.
Payment history must not be replaced by repeatedly overwriting one balance field.

4. Receivable
A separate independently editable Receivable balance is not required as financial truth.
Receivable position derives from:
Agreed Sale Price
Valid Sale Payments
The system may maintain a derived/query-optimized receivable projection later, but it must remain completely reconcilable and rebuildable from Sale and Sale Payment records.
Two primary states are:
Pending / Partially Received
Fully Received
Unreceived money must never become available/recovered Investor Fund.

J. PROFIT AGREEMENT & DISTRIBUTION SNAPSHOT MODEL
1. Investor Profit Agreement
Investor-specific percentages require effective history.
Core fields:
UUID
Investor
Percentage
Effective From
Effective To where applicable
Status
Set/Changed By
Changed At
Optional Reason
Relationships:
Investor 1 → many Profit Agreements
Only one applicable active agreement should apply at a given effective point under the final workflow rules.
33% must never be hard-coded as universal.

2. Owner Split Configuration
Use normalized configuration rather than fixed Owner columns.
OwnerSplitConfiguration
Core fields:
UUID
Scope Type
Tenant where applicable
Effective From/To
Status
Created By
Created At
OwnerSplitAllocation
Core fields:
UUID
OwnerSplitConfiguration
Business Owner / Profit Recipient
Percentage
Relationships:
OwnerSplitConfiguration 1 → many OwnerSplitAllocations
BusinessOwner 1 → many OwnerSplitAllocations
The allocation rows for one configuration must form a complete valid split.
Current values may include the present 48.5% / 51.5% Owners Pool split, but the schema must not assume exactly two Owners forever. Existing business documents require the split and percentage configuration to remain configurable and historically reproducible. Pasted text(20261007-144644)

3. Profit Distribution Snapshot
Identity: UUID
Scope: Immutable historical financial snapshot
The snapshot is created/finalized at the authoritative financial point defined by Document 05.
Once finalized, it must not be silently recalculated.
Core fields include:
UUID
Vehicle
Sale
Investor
Tenant Context
Total Vehicle Cost
Agreed Sale Price
Profit / Loss
Investor Percentage
Investor Entitlement
Owners Pool Amount
Owner Split Configuration/version reference
Calculation Version
Calculated At
Finalized At
Profit Allocation Snapshot
Use child records for Owner allocations:
UUID
Profit Distribution Snapshot
Business Owner
Percentage
Amount
Relationships:
Sale 1 → 0..1 finalized Profit Distribution Snapshot
Profit Distribution Snapshot 1 → many Profit Allocation Snapshots
Historical deals must preserve the percentages/configuration that applied when the deal was finalized rather than using later settings. Pasted text(20261007-144644)

K. INVESTOR EXIT & SETTLEMENT MODEL
1. Investor Exit Request
Identity: UUID
Scope: Global Investor lifecycle record
Core fields:
UUID
Investor
Requested At
Notice Start
Notice End
Terms Acceptance
Terms Accepted At
Status
Requested By
Audit metadata
Relationships:
Investor 1 → many historical Exit Requests
Exit does not replace or delete Investor identity.

2. Settlement
Identity: UUID
Scope: Global Investor financial settlement
Core fields:
UUID
Investor
Exit Request where applicable
Settlement Status
Principal Position
Profit Position
Pending Receivable Position
Final Settlement Position
Created/Completed Dates
Managed By
Audit metadata
Relationships:
Investor 1 → many Settlements
Exit Request 1 → 0..1 settlement for that exit cycle
Settlement Item
Where detailed traceability is required:
UUID
Settlement
Related Vehicle / Sale / financial source
Component Type
Amount
Tenant Context
A global Investor settlement must be capable of representing relevant activity from more than one Tenant.

L. LABOUR & LABOUR PAYMENT MODEL
1. Labour
Identity: UUID
Scope: Tenant-scoped
Core fields:
UUID
Tenant
Name
Basic Contact Details where required
Status
Created At
Updated At
Labour Name is not identity.
Current Labour model intentionally does not contain:
Fixed Salary
Attendance
Payroll Schedule
Vehicle Assignment
Work-Type Assignment
Worker-level Vehicle Costing

2. Labour Payment
Identity: UUID
Scope: Tenant-scoped transaction
Core fields:
UUID
Labour
Tenant
Amount
Payment Date
Optional Note
Created By
Created At
Relationships:
Labour 1 → many Labour Payments
Each payment may have a different amount.
A Labour Payment is independent from a Vehicle-level Labour Expense category; the system does not require worker-level Vehicle cost allocation in the current scope.

M. MEDIA & PUBLIC VEHICLE MODEL
1. Media Asset
Identity: UUID
Scope: Tenant-scoped through Vehicle
Core fields:
UUID
Vehicle
File/Storage Reference
Media Type
Sort Order
Primary Flag where applicable
Status
Uploaded By
Created At
Relationships:
Vehicle 1 → many Media Assets
Storage, CDN, compression, variants, and delivery behavior belong to 08 — Image & File Architecture.

2. Vehicle Publication
Identity: UUID
Scope: Tenant-scoped through Vehicle
Core fields:
UUID
Vehicle
Public Identifier if separate from internal Vehicle ID
Public Title
Display Price
Short Description
Public Availability/Status
Publication Status
Published At
Updated At
Relationships:
Vehicle 1 → 0..1 active Publication Profile
Public-facing access must use an explicitly approved public-safe projection/schema rather than unrestricted exposure of the internal Vehicle entity. The current module rules explicitly prohibit internal financial data from being exposed through the Public Vehicle API. Pasted text(20261007-144644)

N. SYSTEM / BUSINESS CONFIGURATION
Configuration must distinguish between:
System defaults
Tenant defaults
Investor-specific agreements
Owner Split configurations
Protected business configuration
Historical versions
High-risk financial configuration should use typed, validated structures rather than unrestricted arbitrary key/value records.
Configuration changes must preserve:
Previous value/version
New value/version
Applicable scope
Changed By
Changed At
Completed historical transactions must not depend on mutable current configuration.

O. GST / TAX / INVOICE EXTENSION
GST, tax, and invoice data is optional in the current phase.
Where required, it should be represented through a dedicated optional Sale-linked extension rather than making tax fields mandatory on every Sale.
Exact statutory invoice-document multiplicity is not locked in the current business requirements and is therefore deferred to the relevant tax/invoice design if that capability becomes active.
No full tax/accounting subsystem is introduced here.

P. AUDIT & FINANCIAL CORRECTION MODEL
Audit Record
Identity: UUID
Important audit events may include:
Actor
Timestamp
Action
Entity Type
Entity UUID
Tenant Context
Previous State where appropriate
New State where appropriate
Reason
Request/Correlation Reference where applicable
Audit data must never contain:
Passwords
Authentication tokens
Secrets

Financial Corrections
Important financial records must not be silently overwritten.
For transaction-style records, correction should normally use:
Reversal
Compensating entry
Correction entry
and preserve links to the original record.
Correction history must retain:
Original Record
Correcting Record
Previous Value
Corrected Value
Actor
Date/Time
Reason where applicable
The locked business model requires financial corrections and percentage/configuration history to remain traceable. Pasted text(20261007-144644)

Q. DERIVED VS STORED VALUES
Business Value
Authoritative Source
Initial / Additional Investor Fund
Investor Fund Ledger transactions
Total Investor Fund
Ledger-derived
Available Investor Fund
Ledger-derived
Fund Used
Ledger-derived
Recovered Principal
Ledger-derived
Profit Earned
Investor Profit Entitlement/Ledger
Profit Paid
Investor Profit payment/settlement transactions
Profit Pending
Derived from entitlement minus valid payments
Purchase Cost
Vehicle purchase source data
Total Vehicle Expense
Vehicle Expense transactions
Total Vehicle Cost
Purchase Cost + valid Vehicle Expenses
Agreed Sale Price
Sale
Amount Received
Valid Sale Payments
Pending Amount
Sale Price minus valid Sale Payments
Vehicle Profit/Loss
Derived calculation; historical finalized value captured in snapshot
Investor Share
Profit Distribution Snapshot
Owners Pool
Profit Distribution Snapshot
Owner Allocations
Profit Allocation Snapshot rows
Settlement Position
Settlement + linked authoritative financial records

The locked calculation model already defines Vehicle Cost, Investor Fund, Profit/Loss, and pending-sale relationships; 04 defines where those facts originate rather than replacing their business formulas. Pasted text(20261007-144644)

R. DELETE / ARCHIVE / HISTORICAL INTEGRITY
Unsafe cascade deletion must not destroy business history.
Required principles:
Closed Investor ≠ Delete Investor
Sold Vehicle ≠ Delete Vehicle
Inactive Labour ≠ Delete Labour Payments
Deactivated User ≠ Delete historical actions
Inactive Tenant ≠ Delete Tenant history
Buyer edit/deactivation ≠ Delete Sale history
Configuration update ≠ Rewrite completed deals
Appropriate lifecycle mechanisms include:
Active/Inactive
Archived
Closed
Protected/Restricted foreign keys
Immutable historical records
Hard deletion is acceptable only for data with no required business/history consequences and only when permitted by later implementation rules.

S. RELATIONSHIP & CARDINALITY MAP
User
  └──< TenantMembership >── Tenant

User
  ├── may link to BusinessOwner
  └── may link to Investor

Tenant
  ├──< Vehicle
  ├──< Buyer
  ├──< Labour
  ├──< ExpenseCategory
  └──< TenantConfiguration

Investor
  ├──< Vehicle
  ├──< InvestorFundLedgerEntry
  ├──< InvestorProfitLedgerEntry
  ├──< InvestorProfitAgreement
  ├──< InvestorExitRequest
  └──< Settlement

Vehicle
  ├── belongs to one Investor
  ├── belongs to one Current Tenant
  ├──< VehicleTenantHistory
  ├──< VehicleExpense
  ├──< MediaAsset
  ├──0..1 Sale
  └──0..1 VehiclePublication

ExpenseCategory
  └──< VehicleExpense

Buyer
  └──< Sale

Sale
  ├──< SalePayment
  └──0..1 ProfitDistributionSnapshot

ProfitDistributionSnapshot
  └──< ProfitAllocationSnapshot

BusinessOwner
  ├──< OwnerSplitAllocation
  └──< ProfitAllocationSnapshot

OwnerSplitConfiguration
  └──< OwnerSplitAllocation

InvestorExitRequest
  └──0..1 Settlement

Settlement
  └──< SettlementItem

Labour
  └──< LabourPayment

User
  └──< AuditRecord as Actor
There is no mandatory Investor → Tenant ownership relationship.

T. DATA-INTEGRITY CONSTRAINTS
The implementation must ultimately enforce applicable constraints at backend/database level.
Core constraints include:
Every persistent entity uses UUID identity.
Every Vehicle has exactly one Investor.
A Vehicle Expense belongs to exactly one Vehicle.
Vehicle financial activity must use that Vehicle's Investor context.
Tenant-scoped records must remain Tenant-consistent.
Money and percentages use fixed precision.
Normal operations must not create a negative Investor available principal balance.
Valid Sale Payments must not silently produce an invalid negative pending balance.
Profit percentages must remain within valid controlled ranges.
Owner Split allocations for one effective configuration must form the required complete allocation.
Historical finalized financial snapshots are immutable.
Important financial writes must support atomic transactions.
Duplicate processing of critical financial writes must be preventable through appropriate constraints/idempotency mechanisms.
The following values must not automatically be unique:
Person Name
Investor Name
Buyer Name
Buyer Phone Number
Labour Name
Vehicle Registration Number
unless a future explicit business rule requires uniqueness.

U. TENANT ISOLATION
Every Tenant-scoped entity must have an unambiguous Tenant context either directly or through an authoritative parent relationship.
Examples:
Vehicle → Current Tenant
Vehicle Expense → Vehicle → Tenant
Sale → Vehicle → Tenant
Sale Payment → Sale → Vehicle → Tenant
Media Asset → Vehicle → Tenant
Labour Payment → Labour → Tenant
Where security, querying, or historical integrity requires explicit Tenant storage in addition to inherited scope, such duplication must be validated against the parent relationship and must not become a conflicting source of truth.
Investor and Investor Fund remain global.
Tenant context on Investor financial activity exists for traceability, not ownership.
The locked permission model requires backend Tenant isolation and explicitly assigned cross-Tenant access. Pasted text(20261007-144644)

V. TENANT MERGE READINESS
04 does not define a Tenant Merge workflow.
The relational architecture must only avoid unnecessarily blocking future controlled consolidation.
Required readiness principles:
Stable UUID identities
No records identified by Tenant name
Investor remains global
Vehicle Tenant history is preserved
Financial history remains immutable
User access uses membership/assignment
Source Tenant records need not be destructively deleted
Historical Tenant context remains traceable
Detailed consolidation rules belong to the separate:
Tenant Merge & Consolidation Architecture
Tenant Merge remains outside normal operations. Pasted text(20261007-144644)

W. EXPLICIT NON-SCOPE
The current data model must not introduce unnecessary entities for:
Dedicated Cash Accounts
Dedicated Bank Accounts
Cash-vs-Bank Operational Ledger
General Garage Expense
Attendance
Automated Payroll
Fixed Labour Salary Engine
Labour Vehicle Assignment
Labour Work-Type Assignment
Detailed Worker-Level Vehicle Costing
Full CRM
Separate Loss Allocation Workflow
Normal user-facing Tenant Merge
AI-generated financial truth
Older references to Cash/Bank and detailed Labour assignment are superseded by the latest locked scope. The current authoritative module definition explicitly removes dedicated Cash/Bank and keeps Labour simple. Pasted text(20261007-144644)

X. AUTHORITATIVE ENTITY INVENTORY
The current architecture contains the following principal persistent entities or relationship records:
Tenant
User
Role
Permission
TenantMembership
BusinessOwner
Investor
Investor/User Link where required
InvestorFundLedgerEntry
InvestorProfitLedgerEntry
InvestorProfitAgreement
Vehicle
VehicleTenantHistory
ExpenseCategory
VehicleExpense
Buyer
Sale
SalePayment
OwnerSplitConfiguration
OwnerSplitAllocation
ProfitDistributionSnapshot
ProfitAllocationSnapshot
InvestorExitRequest
Settlement
SettlementItem
Labour
LabourPayment
MediaAsset
VehiclePublication
System/Tenant Configuration records
Optional GST/Tax/Invoice extension record
AuditRecord
Correction/Reversal relationships
Intentionally Derived Rather Than Independent Truth
The following do not require separate independently editable business entities in the current model:
Total Investor Fund
Available Investor Fund
Fund Used
Total Vehicle Cost
Total Vehicle Expense
Amount Received
Pending Receivable
Vehicle Capital Total
Dashboard Totals
Report Totals
These are derived from authoritative records or preserved in immutable historical snapshots where required.

Y. DOCUMENT DEPENDENCIES
01 — Business Rules
Defines business and financial rules.
02 — User Roles & Permissions
Defines access, authority, and Tenant scope.
03 — System Modules
Defines official modules and boundaries.
04 — Data Model & Relationships
Defines entity identities, relationships, ownership, financial data sources, and historical integrity.
The following later documents may refine workflow or implementation without contradicting 01–04:
05 — Vehicle / Investor / Finance Workflow
06 — Tenant / Labour Architecture
07 — UI / Navigation Structure
08 — Image & File Architecture
09 — Performance Architecture
10 — Security Architecture
11 — AI / Automation Architecture
12 — API & Backend Architecture
13 — Deployment / Staging / Production
14 — Testing & Audit Strategy

Z. DOCUMENT STATUS
04 — DATA MODEL & RELATIONSHIPS
Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH
This document is authoritative for:
Entity identity
UUID requirements
Global vs Tenant ownership
Core relationships
Cardinalities
Investor Fund source-of-truth architecture
Buyer/Sale/Payment relationships
Historical profit snapshots
Owner allocation structure
Settlement relationships
Labour data structure
Audit/correction structure
Derived vs stored values
Historical-retention principles
Tenant-isolation relationships
Current data-model non-scope
Later implementation documents may refine physical schemas, indexes, ORM details, APIs, migrations, and workflow sequencing, but they must not silently contradict the entity ownership, relationships, historical-integrity requirements, or financial sources of truth defined here.
