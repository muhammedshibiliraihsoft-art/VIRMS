# 03 — System Modules

Status: DRAFT V2 — module-boundary source after approval

## Boundary rules

VIRMS is a provider-neutral modular monolith. Platform Core, Accounting, Investment, Garage, Investor Portal and approved supporting modules have separate logical ownership. Shared authentication, Company/Branch resolution, permissions, search, pagination, notifications, audit, error handling and image processing are cross-cutting capabilities. A frontend page or shared database does not transfer financial authority between modules. Integrate through stable internal contracts, services, events or APIs where appropriate; no microservice separation is required.

Accounting is the Company financial backbone. Investment owns Investor Fund and Investor financial relationships; Garage owns Jobs and work. Garage must function for a Company with Investment OFF. Investment must not own Garage workflow. Each fact has one authoritative source and can be referenced by other modules without duplicating money.

Investor Portal is an early development priority, not the whole product; the approved Owner, Accountant, Media, Back Office, reporting, audit and public-safe surfaces remain in scope.

## Official module responsibilities

| Module | Owns or presents | Does not own |
|---|---|---|
| Platform Core | Companies/Tenants, Tenant activation/suspension, Branches, Users, memberships, enabled-module state, protected configuration with effective/versioned history and Platform Back Office action authorization, platform audit, shared Vehicle identity and movement boundary | Company business postings merely because it manages Tenants |
| Accounting | Company Ledger, classified income/expense, actual receipts/payments, Cash/Bank basics, Company Share, Garage Revenue, Running Capital source/return, Company result and Owner Distribution | Investor agreement or Garage Job work detail |
| Investment | Company-scoped Investor identity, Fund/ledger, Stock Vehicle funding, effective Investor positive-share agreement (protected changes administered by Platform Back Office), Monthly Business Cycle and Interim Payout, period reconciliation, recoverable, Exit and Settlement | Garage Job lifecycle or direct Owner distribution |
| Garage | Branch Jobs, stock-Vehicle work and external-customer Vehicle work, Labour/material/work history, customer charge and collection source | Investor Fund, Investor Profit or an Investor requirement for customer Vehicles |
| Investor Portal | Permitted Investor self-view, own financial history and normal Exit request | Independent editable financial truth |
| Vehicle Management | Company-wide Vehicle identity, one funding Investor for funded Stock Vehicle, lifecycle, current Branch and transfer history | Duplicate Vehicle identity after transfer |
| Vehicle Expense Management | Approved, individually traceable Vehicle costs and Company/Branch attribution | General Company overhead without classification |
| Sales and Receivables | Authoritative Stock Vehicle Sale, Tenant-scoped Buyer, actual Buyer receipts, corrected receivable and explicit refund obligations/payments | Profit from unreceived Sale money or automatic excess Buyer credit |
| Media / Vehicle Publication | Approved images, public fields, publication and public availability shared by Accountant and Media with different permissions | Core Vehicle lifecycle or private finance |
| Public Vehicle Access | Dedicated published/eligible public-safe read projection | Internal Vehicle serialization |
| Labour | Company/Branch managed basic person record and manual payment history | Payroll, attendance or worker-level Vehicle cost attribution |
| Reports and Dashboard | Bounded, permission-scoped Company/Branch, Investor, Vehicle, Garage, Accounting, media and audit views | Independent editable balances |
| Audit and Corrections | Immutable event linkage, actor, time, old/new and reason context; current-position reconciliation | Silent history replacement |
| Platform Back Office | Tenant/Branch/module/account control, Tenant activation/suspension, protected Investor positive-share agreements and business rates, Owner distribution percentages, sensitive Company defaults, support/audit, future plan/subscription configuration and controlled Tenant consolidation | Routine Tenant accounting and payment confirmation |
| GST / Tax / Invoice capability | Optional applicable transaction metadata | Full tax suite |
| Owner AI Assistant | Read-only explanation of verified authorized data | Financial posting or authoritative calculation |

The named capabilities may be packaged together within the modular monolith. These boundaries identify responsibility; they do not require one deployable service or database per row.

## Automation boundary

Each module follows the five levels in 01: deterministic backend calculation, editable suggestion where allowed, due/reminder, specifically authorized human confirmation of consequential events, and manual exceptional handling. Investment, Garage and Accounting may show the same source amount in their own views without creating another transaction. A calculated balance or share, suggested recovery, due status or ended period cannot post a payment, approve Loss or close settlement. Protected configuration confirmation belongs to Platform Back Office; ordinary Company financial-event confirmation follows 02 and the owning module. AI is optional read-only assistance, never a calculation or posting authority.

## Module enablement

Supported modules are enabled or disabled per Company through versioned configuration, without editing code. Backend permissions enforce module availability. OFF denies ordinary new activity, preserves data and authorized history, and retains narrowly scoped actions needed to settle existing open positions. Re-enable restores access to retained records. Any future optional module receives no role permissions or financial authority by default.

## Current scope limits

The initial Garage materials model does not require stock-level Parts Inventory. No manufacturing, barcode-heavy retail, schemes, broad CRM or generic ERP module is implied. A future Inventory or subscription feature may use the module boundary when separately approved. BILLTECH is only a process reference, never an implementation, UI, security or permission source.
