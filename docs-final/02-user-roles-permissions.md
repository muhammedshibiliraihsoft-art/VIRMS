# 02 — User Roles & Permissions

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — AUTHORIZATION SOURCE OF TRUTH

## Authorization boundary

Every protected read or write requires backend checks for authenticated User, role/permission, Tenant assignment, and resource/object scope. Hiding a UI control is not authorization. A supplied Tenant UUID, Vehicle UUID, or Investor UUID grants no access by itself. Default to deny where permission is not explicit.

User identity is global. Tenant memberships are explicit and may authorize one or multiple Tenants. Owner combined views aggregate only authorized Tenants. Investor identity and Fund remain global business records; Tenant context on activity is traceability, not Investor ownership.

## Future modules and features

A new module, feature, resource, or operation receives no role access merely because it is considered normal or operational. Before implementation, its authorization contract must explicitly define allowed and denied roles; read, create, update, and delete/archive permissions where relevant; approval or confirmation authority where relevant; Tenant, global, and object/resource scope; and sensitive-field restrictions where relevant. Permission that is not explicitly granted is denied.

There is no automatic Owner or Accountant permission inheritance for an undefined future capability. Owner read-only visibility and Accountant operational-writer responsibility continue for the existing capabilities explicitly defined below, but those role philosophies do not grant access to a future capability by themselves. Authorization remains backend-enforced, and frontend visibility is never authorization.

## Current roles

| Role | Authorized capability | Boundary |
|---|---|---|
| Owner | View, monitor, filter, analyse, and audit all business information within explicitly authorized Tenant scope, including combined authorized views and Owner AI | Operationally read-only; no Vehicle, Expense, Sale, Fund, correction, percentage, payout, or closure mutation |
| Accountant / Operations Admin | Primary daily operations within authorized scope: Investors/Fund, Vehicles, Expenses, Sales, Buyer receipts, payouts, corrections, Labour, media/publication, exit and settlement | No system/Tenant default configuration or Tenant Merge authority by normal role |
| Investor | View own Fund, Vehicles, finance, exit and settlement; submit normal exit request; view other Vehicles only at approved public level | Authoritative finance is read-only; never another Investor's private data |
| Media User | Manage authorized Vehicle images, public-facing fields, display information, publication and public availability | No internal finance or core Vehicle lifecycle mutation |
| Back Office Admin | Tenant and system administration, Owner/Accountant provisioning, membership, defaults and protected configuration; controlled Tenant consolidation if implemented | Not the daily operational finance interface |
| Labour | No authenticated role in current scope | Managed Tenant-scoped record only |

## Operational permissions

- Accountant can create Investors, record initial/additional principal, assign one Investor to each Vehicle, purchase Vehicles, add valid Vehicle Expenses, manage Buyers/Sales/actual payments, record actual refunds against correction-created Buyer Refund Payables, confirm Profit Payments, and perform audited corrections.
- Accountant records each actual Owner loss contribution into the affected Investor Fund with Owner, Vehicle, Sale and Tenant context. The Owner role remains read-only in the application even when the person contributes money.
- Accountant sets the initial Investor-specific profit percentage and may later change it for a legitimate reason. A later change records previous/new values, Investor, applicable scope, actor, and time; Owner can see the notification/history. Owner approval and a separate secondary password are not required.
- Back Office manages system/Tenant default profit configuration and Owner split configuration. Sensitive changes require restricted permission, explicit review/confirmation, and audit.
- Accountant may initiate/manage exceptional early Investor closure with audit. Owner can inspect it but cannot initiate or manage it.
- The core Vehicle lifecycle Purchased → In Work → Ready → Listed → Sold is controlled by authorized operational/Accountant actions. Media may change only public-facing availability/status and publication state, never those core states.
- Accountant and Media User use the same Media / Vehicle Publication capability with different field permissions. Media must never receive Investor identity/private data, Fund, purchase cost, internal Expenses, Profit/Loss, shares, settlement finance, corrections, or protected configuration.
- Investor can submit a normal exit request after Terms & Conditions acceptance. That request does not close the account or mutate authoritative finance.

## Account and Tenant administration

- Back Office provisions Owner and Accountant accounts and controls Tenant assignment. Django Admin may temporarily supply those system administration functions until a dedicated Back Office exists; it is not the normal operations UI.
- Accountant may provision Investor and Media accounts within authorized operational scope. Labour has no login.
- Tenant-scoped writes and reads must enforce the current authorized Tenant and validate linked objects belong to the permitted scope. Vehicle transfer preserves historical Tenant context.
- Tenant Merge is controlled Back Office/system administration only; Accountant, Owner, Investor, Media, and public users do not receive a normal Merge action.

## Public and AI access

- Public Vehicle API is read-only and returns only explicitly published/eligible Vehicles through a dedicated public-safe schema. Default fields are limited to public identity, make/model/name, public image, display price, public availability, and approved description where present.
- Public responses must not serialize internal Vehicle objects or expose Investor identity, finance, internal costs, shares, audit, protected configuration, or private storage paths.
- Owner AI is Owner-only, read-only, self-limited to the Owner's authorized Tenant scope, and uses verified system data. It cannot create financial truth or perform mutations.

## Historical controls

Financial corrections and percentage changes are audited; past finalized percentage snapshots and transaction history remain intact. Account deactivation and Investor closure never delete historical business records. Authentication, password reset, sessions, and login protection follow the supporting Authentication document.
