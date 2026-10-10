> ⚠️ LEGACY — NON-AUTHORITATIVE — DO NOT IMPLEMENT

> This document is retained only for historical reference.
> `/docs-final/` is the sole VIRMS implementation source of truth.
> Any older `LOCKED`, `FINAL`, or `AUTHORITATIVE` wording below is historical
> and is superseded by the current `/docs-final/` documentation.

AUTHENTICATION, PASSWORD & ACCOUNT RECOVERY STANDARDS
AUTH-001 — System-Managed Authentication
Status: LOCKED DEFAULT
Current default authentication model:
Username / Login ID + Password
Google authentication, social login, email verification എന്നിവ current default requirement അല്ല.
Future business requirement വന്നാൽ architecture extend ചെയ്യാൻ കഴിയണം.

AUTH-002 — System Creates Initial Account
Status: LOCKED
Authorized system administrator / Back Office user account create ചെയ്യാം.
Account creation സമയത്ത്:
Username / Login ID
Initial temporary password
generate/set ചെയ്യാം.
Initial password permanent password ആയി തുടരേണ്ടതില്ല.

AUTH-003 — Force Password Change on First Login
Status: LOCKED — SECURITY CRITICAL
Temporary/default password ഉപയോഗിച്ച് ആദ്യമായി login ചെയ്താൽ user സ്വന്തം പുതിയ password create ചെയ്യണം.
Until changed:
normal application access limit ചെയ്യാം
password-change flow complete ചെയ്യണം

AUTH-004 — User Can Change Own Password
Status: LOCKED
Logged-in user-ന് സ്വന്തം password change ചെയ്യാനുള്ള option വേണം.
Normal change flow:
Current Password
→ New Password
→ Confirm New Password
Current password validate ചെയ്തശേഷം മാത്രം change apply ചെയ്യണം.

AUTH-005 — Passwords Must Never Be Stored as Plain Text
Status: LOCKED — CRITICAL
System ഒരിക്കലും actual password readable/plain-text form-ൽ database, logs, analytics, backups, frontend state എന്നിവയിൽ store ചെയ്യരുത്.
Passwords secure password hashing mechanism ഉപയോഗിച്ച് മാത്രം store ചെയ്യണം.
Admin/Developer/Back Office user-ന് existing user's actual password കാണാൻ കഴിയരുത്.
Password can be reset, but never retrieved.

AUTH-006 — Forgotten Password Without Email/OTP
Status: LOCKED
Email/phone identity verification ഇല്ലാത്ത current model-ൽ public self-service Forgot Password → Set New Password അനുവദിക്കരുത്.
User password മറന്നാൽ authorized administrator വഴി recovery initiate ചെയ്യണം.

AUTH-007 — Administrator Password Reset
Status: LOCKED
Authorized administrator-ന് permitted user account-ന്റെ password reset ചെയ്യാൻ കഴിയണം.
Admin പഴയ password കാണുകയോ recover ചെയ്യുകയോ ചെയ്യരുത്.
Reset flow:
User reports forgotten password
→ Identity/business verification
→ Authorized admin initiates reset
→ Temporary/reset credential generated
→ Existing sessions revoked where appropriate
→ User logs in
→ User must create new private password

AUTH-008 — Forced Change After Administrative Reset
Status: LOCKED — CRITICAL
Admin reset ചെയ്ത temporary password final password ആയി തുടരാൻ പാടില്ല.
Next successful login-ൽ:
New Password + Confirm Password
mandatory ആക്കണം.

AUTH-009 — Admin Must Not Choose and Keep User's Permanent Password
Status: LOCKED
Administrator temporary/reset credential നൽകാം.
User-ന്റെ final permanent password user തന്നെയാണ് privately set ചെയ്യേണ്ടത്.

AUTH-010 — No Security Questions
Status: LOCKED DEFAULT
“What is your mother's name?” പോലുള്ള security-question based password recovery ഉപയോഗിക്കരുത്.
അവ guessable/leakable ആയതിനാൽ recovery security ആയി rely ചെയ്യരുത്.

AUTH-011 — Login Failure Protection
Status: LOCKED
Repeated wrong login attempts unlimited speed-ൽ അനുവദിക്കരുത്.
System support ചെയ്യണം:
Rate limiting
Progressive delay / backoff
Suspicious repeated-attempt protection
Audit/security logging
Hard permanent lockout മാത്രം default approach ആകരുത്; legitimate user-നെ unnecessarily block ചെയ്യാൻ പാടില്ല.

AUTH-012 — Password Reset Protection
Status: LOCKED
Password reset high-impact security action ആണ്.
Reset attempt/action audit ചെയ്യണം:
Account
Initiated By
Date / Time
Tenant / Scope where relevant
Result
Password itself audit log-ൽ ഒരിക്കലും record ചെയ്യരുത്.

AUTH-013 — Session Revocation After Reset
Status: LOCKED
Password reset അല്ലെങ്കിൽ suspected credential compromise ഉണ്ടായാൽ existing authenticated sessions revoke ചെയ്യാൻ system support വേണം.
Old stolen session password change കഴിഞ്ഞിട്ടും indefinitely usable ആകരുത്.

AUTH-014 — Password Quality
Status: LOCKED
Passwords reasonable strength meet ചെയ്യണം.
System:
extremely weak/common passwords discourage/reject ചെയ്യണം
sufficiently long passwords/passphrases allow ചെയ്യണം
unnecessary restrictive rules കൊണ്ട് users-നെ predictable passwords create ചെയ്യാൻ force ചെയ്യരുത്
password manager generated passwords support ചെയ്യണം

AUTH-015 — Login Error Privacy
Status: LOCKED
Login errors unnecessary account information leak ചെയ്യരുത്.
Public login response:
“Invalid username or password.”
പോലുള്ള safe response ഉപയോഗിക്കാം.
Attacker-ന് username exists/does not exist എന്ന വിവരം unnecessarily reveal ചെയ്യരുത്.

AUTH-016 — Password Fields
Status: LOCKED
Password UI:
masked by default
intentional Show/Hide control
correct autocomplete semantics
paste/password-manager support
mobile friendly
ഉണ്ടായിരിക്കണം.
Password paste disable ചെയ്യരുത്.

AUTH-017 — Account Disable / Reactivation
Status: LOCKED
Authorized administration layer user account:
Activate
Deactivate
Reactivate
ചെയ്യാൻ support ചെയ്യണം.
Deactivated account login ചെയ്യാൻ പാടില്ല.
Historical business records delete ചെയ്യരുത്.

AUTH-018 — Authentication Architecture Must Be Extendable
Status: LOCKED ARCHITECTURAL REQUIREMENT
Current system-managed password model future authentication improvements block ചെയ്യരുത്.
Later ആവശ്യമായാൽ support ചെയ്യാൻ കഴിയണം:
Email verification
Email/OTP password recovery
MFA / TOTP
Passkeys
Google / Microsoft authentication
SSO
ഇവ current implementation requirement അല്ല.

DEFAULT RECOVERY FLOW
Normal Login
**Username
Password
→ Authenticated Session**
First Login
Temporary Password
→ Authentication
→ Mandatory New Password
→ Normal Access
Normal Password Change
Current Password
→ New Password
→ Confirm
→ Password Updated
Forgotten Password
User contacts authorized administrator
→ Identity verified through business process
→ Admin initiates reset
→ Temporary credential/reset mechanism
→ Existing sessions revoked where appropriate
→ User logs in
→ Mandatory New Password
Important Rule
Admins reset passwords; they never retrieve passwords.

CURRENT AUTHENTICATION DECISION
Current Phase
✅ Username/Login ID + Password
✅ System-created accounts
✅ User password change
✅ Admin password reset
✅ Mandatory change after reset
✅ Audit trail
✅ Login rate limiting
✅ Session revocation support
Not required currently
❌ Google Sign-In
❌ Mandatory email verification
❌ Email-based password recovery
❌ Social login
❌ Labour login unless later required
❌ MFA unless later required
Future architecture must allow these features without authentication redesign.

----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
