
TASK: FINALIZE “03 — SYSTEM MODULES”

Project: Vehicle Investment, Modification & Resale Management System

Create the final authoritative English document:

docs/03-system-modules.md

This task is DOCUMENTATION ONLY.
Do not implement application code, migrations, models, APIs, UI, or database changes.

SOURCE OF TRUTH

Before writing anything, read and reconcile:

1. 01 — Business Rules
2. 02 — User Roles & Permissions
3. Authentication & Account Security document, only to understand what must NOT be duplicated in 03
4. Existing draft/current version of 03 — System Modules, if present

01 defines business and financial truth.
02 defines permissions, tenant scope, operational authority, latest role decisions, and later approved scope changes.
03 must define module boundaries only.

Do not invent business rules.
Do not silently change locked decisions.
Do not restore superseded old requirements.
If a genuine unresolved contradiction remains, report it instead of guessing.

KNOWN LATEST DECISIONS THAT MUST BE PRESERVED

- Multi-Tenant from Day One.
- Garage = Tenant.
- Investor is a GLOBAL business entity, not tenant-owned.
- Investor fund position is global, not duplicated per tenant.
- One Vehicle → One Investor.
- One Investor → Multiple Vehicles.
- Owner is full-business read-only.
- Accountant is the main operational write role.
- Labour is a simple current-scope module.
- No dedicated Cash/Bank Account module in the current scope.
- No General Garage Expense module in the current scope.
- No separate Loss Allocation module/workflow.
- Public Vehicle API exposes only explicitly approved public-safe fields.
- Tenant Merge is NOT a normal operational module. It belongs to a separate supporting Tenant Merge & Consolidation architecture and may later be Back Office/system-level only.
- Authentication/password/recovery/session rules must not be duplicated in 03.
- Historical financial truth must be preserved.
- Unreceived sale money must never be treated as received or available funds.

GLOBAL IDENTITY / UUID RULE

Add and lock a system-module-level identity principle:

Every persistent business/system entity must use a backend-generated immutable UUID (or equivalent opaque globally unique system identifier) as its real system identity.

This applies wherever appropriate, including:
- Tenant/Garage
- User/Account
- Investor
- Buyer/Customer
- Labour
- Vehicle
- Expense Entry
- Expense Category
- Sale
- Buyer Payment / Receivable Payment
- Investor Fund/Ledger Entry
- Settlement
- Profit/Distribution Snapshot
- Audit/Correction Record
- Media/File record
- Important configuration records
- Other persistent business records introduced later

Human-readable/business values are attributes only and must not be treated as immutable identifiers.

Examples:
- Investor Name ≠ Investor ID
- Buyer Name ≠ Buyer ID
- Buyer Phone Number ≠ Buyer ID
- Labour Name ≠ Labour ID
- Vehicle Registration Number ≠ Vehicle ID
- Garage Name ≠ Tenant ID

Names, phone numbers, registration numbers, labels, codes, or other editable business values may change and must not break relationships or history.

Do not expose database auto-increment IDs as the architectural identity requirement.

OFFICIAL SYSTEM MODULES

Define the following modules concisely.

For each module include only:
- Purpose
- Core Responsibilities
- Main Data / Views
- Role Ownership
- Tenant Scope
- Explicit Non-Scope

Avoid repeating detailed formulas or complete permission matrices already defined in Documents 01 and 02.

1. DASHBOARD

Role-based dashboards for Owner, Accountant, and Investor.

Owner Dashboard must explicitly provide authorized read-only visibility across:
- Investors
- Investor Fund positions
- Vehicles
- Vehicle Costs
- Vehicle Expenses
- Buyers
- Sales
- Receivables
- Profit / Loss
- Investor Shares
- Owners Pool
- Owner Shares
- Labour
- Settlements
- Percentage Changes
- Financial Corrections
- Reports
- Audit History
- Operational Status
- Tenant-wise information
- Combined authorized multi-tenant information

Dashboard values must come from authoritative backend data.
Dashboard must never become a separate financial source of truth.

2. INVESTOR MANAGEMENT

Global Investor profile and business relationship.

Include:
- Basic details
- Status/lifecycle
- Vehicle portfolio
- Profit position
- Exit state
- Settlement state
- Historical activity

Investor is global and must never be duplicated simply because activity exists in multiple tenants.

3. INVESTOR FUND & LEDGER

Authoritative Investor fund position and fund movement history.

Include:
- Initial Fund
- Additional Fund
- Total Fund
- Available Fund
- Fund Used
- Recovered Principal
- Profit Earned
- Profit Paid
- Profit Pending
- Fund/Ledger History

Investor fund is GLOBAL.

Individual fund movements must remain traceable to:
- Investor
- Related Vehicle where applicable
- Tenant/context where the activity occurred
- Amount
- Date
- Transaction type/context

Do not create separate Investor balances per tenant.

4. VEHICLE MANAGEMENT

Include:
- Vehicle creation
- Purchase information
- Investor assignment
- Tenant/Garage assignment
- Vehicle details
- Vehicle status
- Vehicle work/modification information
- Operational work/progress context where required
- Vehicle history
- Tenant/Garage movement history
- Sold Vehicle history

Enforce conceptually:
One Vehicle → One Investor
One Investor → Multiple Vehicles

Vehicle must have an immutable UUID/system identity.
Registration Number is only a business attribute.

Current simple lifecycle:
Purchased → In Work → Ready → Listed → Sold

Do not add unnecessary statuses in this document.

5. VEHICLE EXPENSE MANAGEMENT

Vehicle-specific approved expenses.

Include:
- Individual expense entries
- Dynamic expense categories
- Amount/date/details
- Expense history
- Total Vehicle Expense
- Category totals where useful
- Controlled correction history

Expense records inherit Vehicle/Tenant context.

General Garage Expense management is outside current scope.

6. SALES

Include:
- Vehicle Sale
- Buyer
- Agreed Sale Price
- Full Payment
- Partial Payment
- Credit Sale
- Sale history

Sale must reference the existing Vehicle and Buyer using immutable system identities.

7. RECEIVABLES & PAYMENT TRACKING

Include:
- Total Sale Price
- Amount Received
- Pending Amount
- Payment entries/history
- Pending / Partially Received
- Fully Received

Only actually received money can be considered received/recovered.

Unreceived amounts remain receivables.

8. PROFIT & DISTRIBUTION

Include:
- Vehicle-level Profit/Loss
- Investor-specific profit share
- Owners Pool
- Owner shares
- Applicable percentage snapshots
- Percentage-change history

Calculated financial outputs must come from authoritative source data.
Do not create a normal manual “final profit” input.

No separate Loss Allocation workflow exists in current scope.

9. INVESTOR EXIT & SETTLEMENT

Include:
- Exit Request
- Terms & Conditions acceptance
- 3-month notice
- Settlement Pending
- Recovery position
- Final Settlement
- Exceptional Early Closure
- Exit/Settlement history

Investor is global, so settlement logic must not incorrectly assume the Investor belongs to one Tenant.

10. LABOUR

Keep deliberately simple.

Include:
- Labour creation
- Labour UUID
- Name/basic details
- Active/Inactive where needed
- Manual salary/payment entry
- Payment amount
- Payment date
- Optional note
- Payment history

Current non-scope:
- Fixed salary
- Attendance
- Automated payroll
- Vehicle assignment
- Work-type assignment
- Detailed worker-level Vehicle costing
- Workforce scheduling

Labour Name is a display/business value, not identity.

11. BUYER / CUSTOMER

This is a lightweight Buyer module, NOT a full CRM.

Required core data:
- Buyer UUID
- Buyer Name
- Phone Number — REQUIRED
- Optional secondary phone/contact
- Optional address
- Optional notes
- Purchased Vehicle history
- Related Sales
- Related Receivables/Payments
- Purchase History

Buyer Phone Number must NOT be treated as the immutable Buyer identity.

Do not require phone number uniqueness unless a later business/data-model decision explicitly requires it.

If the same Buyer returns later, architecture should allow future Sales to reference the same Buyer record instead of forcing duplicate Buyer creation.

Buyer details must remain extendable for future business needs.

12. MEDIA & VEHICLE PUBLICATION

Include:
- Vehicle image/media upload
- Public-facing Vehicle details
- Display Price
- Publication Status
- Permitted public Vehicle status
- Media management

Media User must never gain internal financial access through this module.

13. PUBLIC VEHICLE ACCESS

Include:
- Published Vehicle catalog
- Vehicle list/detail
- Read-only Public Vehicle API
- Search/filter where appropriate
- Pagination
- Optimized media variants

Default minimum safe public fields:
- Public Vehicle ID
- Vehicle Name / Make / Model
- Main/Public Image
- Display Price
- Public Availability/Status
- Optional Short Description

Future explicitly approved public fields may be added without redesigning the API.

Never expose:
- Investor identity/private data
- Investor Fund
- Purchase Cost
- Internal Expenses
- Internal Profit/Loss
- Investor Share
- Owner Shares
- Financial Corrections
- Internal Audit
- Protected Configuration

Use a dedicated public response schema.
Never serialize the entire internal Vehicle object and rely on the frontend to hide fields.

14. REPORTS

Include relevant:
- Investor Reports
- Fund Reports
- Vehicle Reports
- Expense Reports
- Sales Reports
- Receivables Reports
- Profit/Distribution Reports
- Labour Payment Reports
- Tenant Reports
- Owner Consolidated Reports

Owner must have complete authorized read-only business reporting visibility.

15. AUDIT & CORRECTION HISTORY

Track important changes including:
- Investor fund changes
- Additional funds
- Vehicle financial changes
- Expenses
- Sales
- Buyer Payments
- Receivables
- Percentage changes
- Settlements
- Financial Corrections
- Important protected configuration changes
- Exceptional closure actions

Historical business/financial truth must not be silently overwritten or deleted.

16. TENANT / GARAGE MANAGEMENT

Garage = Tenant.

Include:
- Tenant UUID
- Tenant/Garage information
- Status/configuration
- User/Tenant assignments
- Tenant context
- Tenant isolation
- Relevant Vehicle tenant history

Multi-Tenant architecture exists from Day One.

Tenant Merge must NOT be presented as a normal operational module/action.

17. USER & PERMISSION MANAGEMENT

Include:
- Owner account provisioning
- Accountant account provisioning
- Investor account provisioning
- Media account provisioning
- Role assignment
- Tenant assignment
- Activate/Deactivate

User identities must use immutable backend identifiers.

Do not duplicate:
- Password rules
- Password recovery
- Login protection
- Session security
- Authentication mechanics

Those belong to the Authentication document.

18. BACK OFFICE

System-level administration.

Include:
- Tenant creation/configuration
- Owner provisioning
- Accountant provisioning
- Tenant assignments
- System defaults
- Tenant defaults
- Protected configuration
- Administrative controls

Django Admin may temporarily provide these provisioning functions until Back Office exists.

Back Office/Django Admin must not become the normal daily business operations UI.

19. SYSTEM & BUSINESS CONFIGURATION

Include configurable values such as:
- Investor profit defaults
- Owner split configuration
- Applicable Tenant/Garage-specific percentage/default configuration
- Protected business configuration
- Other approved system/business defaults

Configurable business percentages must never be hard-coded into application logic.

Historical completed deals must preserve the configuration/percentage snapshot that applied at that time.

20. GST / TAX / INVOICE CAPABILITY

Architecture must support applicable:
- GST
- Tax
- Invoice information

These fields are not mandatory for every transaction in the current phase.

Do not turn this into a full tax/accounting suite unless separately approved later.

21. OWNER AI ASSISTANT

Owner only in current scope.

Read-only.

May:
- Query
- Summarize
- Explain
- Analyse
- Assist with reports

Preferred flow:
Verified backend/database/query result
→ deterministic result
→ AI explanation

AI must never:
- Create records
- Edit records
- Delete records
- Perform transactions
- Modify funds
- Change percentages/configuration
- Become the source of financial truth

CROSS-CUTTING CAPABILITIES — NOT SEPARATE BUSINESS MODULES

Treat the following as shared technical/system capabilities rather than standalone business modules:
- Search & Filtering
- Notifications
- Authentication
- Tenant Resolver
- Backend Permission Enforcement
- Pagination
- Media Optimization
- Error Handling
- Audit Logging Infrastructure
- Background Jobs where justified
- Shared Reporting Infrastructure

INTENTIONALLY OUT OF CURRENT SCOPE

Do not introduce the following as current modules:
- Dedicated Cash Account Module
- Dedicated Bank Account Module
- Cash-vs-Bank Operational Ledger
- General Garage Expense Module
- Full Payroll
- Attendance
- Full CRM
- Separate Loss Allocation Module
- Labour Vehicle Assignment
- Labour Work-Type Tracking
- Detailed Worker-Level Vehicle Costing
- Tenant Merge as a normal user-facing action

TENANT MERGE / CONSOLIDATION

Do not fully design Tenant Merge inside 03.

03 should only state:

- Tenant consolidation is a rare administrative scenario.
- Core architecture should avoid unnecessarily blocking a future safe consolidation.
- It must not complicate normal business workflows.
- If implemented, it belongs to Back Office/system administration.
- Detailed rules belong to a separate supporting document:
  “Tenant Merge & Consolidation Architecture”.
- Historical identity, financial truth, global Investor identity, auditability, and data integrity must be preserved.
- If automated merging creates disproportionate risk/complexity, a controlled administrative migration procedure is acceptable.

CORE BUSINESS MODULE FLOW

Investor
→ Investor Fund
→ Vehicle
→ Vehicle Expense
→ Sale
→ Receivable / Payment
→ Profit Distribution
→ Settlement

Supporting domains:
Labour
Buyer
Media/Public Vehicle
Reports
Audit
Tenant
Users/Permissions
Configuration
Tax/Invoice
Back Office
Owner AI

DOCUMENT STRUCTURE

Write:

# 03 — SYSTEM MODULES

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH

Then include:

A. Core Module Principles
B. Official System Modules
C. Cross-Cutting Capabilities
D. Intentionally Out of Current Scope
E. Tenant Merge / Consolidation Reference
F. Core Business Module Flow
G. Document Dependencies
H. Document Status

Keep it concise.
Do not expand every module into implementation-level database/API/UI design.

FINAL VERIFICATION BEFORE MARKING LOCKED

Before finalizing the document, perform a strict consistency check against Documents 01 and 02.

Verify at minimum:

- No business rule was silently dropped.
- No superseded Cash/Bank module was reintroduced.
- Labour remains simplified.
- Investor remains global.
- Investor fund remains global.
- Tenant isolation remains intact.
- Owner retains full authorized business read visibility.
- Buyer Phone Number is explicitly required.
- Buyer/Investor/Labour/Vehicle and all persistent records use immutable UUID/system identities rather than human names/labels as identity.
- Vehicle Work/Modification responsibility is represented.
- Tenant-specific configurable percentages/defaults are represented.
- Public API cannot leak internal finance.
- Historical percentage/financial snapshots are preserved.
- Tenant Merge remains a separate supporting architecture topic.
- Authentication mechanics are not duplicated.
- No Full CRM, Payroll, Attendance, Loss Allocation, General Garage Expense, or Cash/Bank module has been accidentally introduced.

If all checks pass, mark 03 as FINAL / LOCKED.

If a genuine contradiction cannot be resolved from the authoritative documents and explicit latest decisions, do NOT guess. Report:

CONFLICT FOUND
- Source A:
- Source B:
- Why they conflict:
- Business decision required:

Do not mark the document LOCKED until such a genuine unresolved conflict is resolved.
