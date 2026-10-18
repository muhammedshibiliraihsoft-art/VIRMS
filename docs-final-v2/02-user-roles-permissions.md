# 02 — User Roles & Permissions

Status: DRAFT V2 — authorization source after approval

## Authorization boundary

Every protected request requires backend authentication, Company/Tenant membership, enabled-module permission, role/action permission, Branch scope where relevant, and object/field ownership checks. A Company, Branch, Investor, Vehicle, Job or image UUID grants no access by itself. Default deny applies to every new module and operation; frontend visibility is only presentation. A Platform operator's access to one Company never implies access to another Company's business data.

Company-wide views aggregate only the user's explicitly authorized Company scope and permitted Branch records. Same-Company previous-Branch history may be read by authorized users; another Branch's original operational record is normally read-only unless Company-level correction authority is explicitly granted. Company and Branch access checks apply to reports, exports, search, files, jobs, notifications and audit as well as ordinary APIs.

## Existing business roles

| Role | Current authority | Boundary |
|---|---|---|
| Owner | Read, monitor, filter, analyse and audit authorized Company-wide business information, including authorized Branch views and Owner AI | No ordinary operational, finance, percentage, payout, correction or closure mutation |
| Accountant / Operations Admin | Primary authorized business-operation writer: Investors/Fund, Stock Vehicles, approved Expenses, Sales, actual Buyer receipts/refunds, Profit and interim payment confirmations, reconciliations, corrections, Labour, Garage/Accounting entries, media and settlement where a rule grants the action | Company, Branch, module, object and current-position checks; no automatic Platform control authority |
| Investor | View own permitted Fund, Stock Vehicles, Profit, interim/reconciliation, recoverable and exit/settlement positions; submit normal Exit request | No authoritative finance write or access to another Investor's private data; other Vehicles only via approved public view |
| Media User | Manage authorized Vehicle images, approved public fields, display price/information, publication and public availability | No internal finance, Investor private data, core Vehicle lifecycle or Garage accounting mutation |
| Platform Back Office Admin | Manage Companies, Branch administration, Tenant activation/suspension, accounts/membership, module enablement/configuration, protected Investor agreements and business rates, Owner distribution percentages, sensitive Company defaults, future plan/subscription settings and platform audit/support; controlled Company/Tenant consolidation | Platform administration alone grants no routine Tenant financial posting or confirmation authority; financial read requires authorized scope |
| Labour | No login in current scope | Managed operational record only |

Public consumers have only the dedicated published/eligible public-safe Vehicle projection. Tenant administrator/account management is a Platform Back Office capability in the baseline; any separately empowered Company administrator requires an explicit grant, not an implied new role.

## Operational confirmation and protected configuration

- Accountant/Operations is the ordinary confirmer of actual Buyer Payments/refunds, eligible Profit Payments, Monthly Interim Payouts, recoveries, Running Capital and Company accounting transactions, Owner distributions and settlement actions only within explicitly granted Company/Branch/module/resource scope. A suggested amount, reminder or UI control never constitutes confirmation.
- Platform Back Office is the sole administrator of protected financial configuration: Investor-specific positive-share agreements, protected monthly interim rates, Owner distribution percentages, sensitive Company financial defaults and other explicitly protected business rates. A change requires specific backend protected-action permission, effective/versioned configuration and audit of old/new value, effective cycle or time, Investor/Company scope, actor and reason. Accountant/Operations uses approved effective values for ordinary authorized operations but cannot independently change protected percentages or rates. Owner has authorized visibility/notification but no mutation authority. Configuration authority is separate from ordinary transaction confirmation authority.
- Manual Loss impact, Company-level correction of another Branch record, sensitive override, and Company distributable-Profit confirmation require explicit action-level authority and reason/history. Owner read visibility does not itself grant approval or posting permission.
- Media and Investor cannot confirm internal financial movements. Platform Back Office financial review does not turn that role into the ordinary daily Accountant. No separate secondary/protected password is required.

## Module availability

An enabled module still requires the user's normal Company, Branch, role and object permissions. When a module is OFF, ordinary new module activity is denied by the backend; authorized history/read access and minimum actions needed to resolve already-open obligations remain available under explicit permission. Data is retained, and re-enabling restores ordinary supported access without recreating historical records. Module OFF cannot be used to evade an open receivable, refund, recovery, interim or settlement position.

## Accounts, Portal, public access and audit

Platform Back Office provisions and manages privileged Company/Tenant assignments; Accountant may provision Investor and Media accounts within authorized operational scope as in the approved baseline. Account and membership changes retain history. Investor can request normal Exit after Terms & Conditions acceptance but cannot self-confirm financial settlement. Public APIs expose only approved public identity, name/make/model, optimized Primary image, display price, public availability and approved description where present. Never serialize private internal entities for public, Media or Investor views.

Owner AI is read-only over the Owner's verified authorized Company/Branch scope and cannot create financial truth or mutate records. Corrections, configuration, module changes, account actions and sensitive financial confirmations retain actor, time, scope, old/new information and reason where relevant.

## Authorization decisions pending

- **BUSINESS DECISION REQUIRED:** Define exact Company-level correction and manual Loss confirmation authority, including whether the existing Accountant role may exercise it in all Branches or only through a separate explicit grant.
- **BUSINESS DECISION REQUIRED:** Define whether and when Platform Back Office support may read a Company's private financial records beyond explicit Company assignment, and the exact minimum settlement actions permitted while each module is OFF.
