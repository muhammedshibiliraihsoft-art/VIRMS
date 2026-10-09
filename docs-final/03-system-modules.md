# 03 — System Modules

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — MODULE BOUNDARY SOURCE OF TRUTH

## Boundary rules

Modules separate business responsibilities; shared permission enforcement, authentication, Tenant resolution, search, pagination, notifications, audit infrastructure, error handling, and image processing are cross-cutting capabilities. One authoritative source exists for each financial fact (04 and 05). UI grouping does not change module authority (07). Every persistent entity uses an immutable backend-generated UUID.

## Official modules

| Module | Purpose and responsibilities | Key data / views | Primary roles and scope | Explicit non-scope |
|---|---|---|---|---|
| Dashboard | Summarize verified business positions and alerts | Role-specific overview, Tenant/combined Owner view | Owner read, Accountant operations, Investor own; scope per 02 | Editable financial truth |
| Investor Management | Manage global Investor identity, agreement, lifecycle, portfolio | Profile, status, history, Vehicles | Accountant write; Owner/Investor permitted read; global Investor | Tenant-owned Investor duplicates |
| Investor Fund & Ledger | Record principal additions, use, recovery, corrections and derived balances | Ledger, Available/Used/Recovered positions | Accountant write; Investor own read; global Fund with event Tenant context | Tenant-specific Fund, automatic Profit reinvestment |
| Vehicle Management | Record purchase, one Investor, current Tenant, lifecycle and transfers | Vehicle details, statuses, Tenant history | Accountant write; authorized read; Tenant-scoped Vehicle | Multiple funding Investors |
| Vehicle Expense Management | Record approved Vehicle costs and dynamic categories | Expense entries, category totals, Vehicle cost | Accountant write; Tenant-scoped through Vehicle | General Garage Expense, worker-level allocation |
| Sales | Confirm one normal authoritative Sale for a Vehicle at agreed price | Sale, Buyer link, Sold state, price/history | Accountant write; Tenant-scoped through Vehicle | Profit based on receipts alone |
| Receivables & Payment Tracking | Preserve each actual Buyer receipt, correction-created Buyer Refund Payable, actual refund and derived pending balance | Payments, refunds, Pending/Partial/Fully Received | Accountant write; Tenant-scoped through Sale | Treating unreceived or refund-owed money as Fund |
| Profit, Loss & Distribution | Calculate deal result, percentage snapshots, recipient shares, Owner loss coverage and payment state | Profit/loss, loss shares, actual coverage, entitlements, payout history | Accountant operational write; Owner read; Vehicle/Tenant context | Manual loss selector, separate loss engine, early payout mode |
| Investor Exit & Settlement | Handle notice, exceptional closure and global financial settlement | Exit acceptance/status, locked positions, refund and settlement items | Investor normal request; Accountant manage; Owner read; global Investor with context | Closure before required positions resolve |
| Labour | Maintain simple Tenant-scoped Labour and manual payment history | Basic details, Active/Inactive, payments | Accountant write; Owner read | Login, assignment, attendance, payroll |
| Buyer / Customer | Reuse Tenant Buyer identity for Sales | Contact details, purchases, receivables | Accountant write; Tenant-scoped | Full CRM or global phone-based identity |
| Media / Vehicle Publication | Manage Vehicle images and approved public fields in one shared capability | Gallery, primary image, display price, publication, public availability | Accountant/Media limited write; Owner read; through Vehicle/Tenant | Core lifecycle changes by Media; internal finance |
| Public Vehicle Access | Serve explicitly published safe Vehicle information | Public catalog and read-only API | Public consumers; approved publication scope | Internal Vehicle schema or finance |
| Reports | Derive authorized business/financial and Tenant summaries | Investor, Fund, Vehicle, Sale, payment, profit, Labour, audit reports | Owner broad authorized read; Accountant operational; Investor own where permitted | Independent editable balances |
| Audit & Correction History | Preserve actor, old/new, reason, time and event context | Finance/config/permission/correction history | Authorized operational or Back Office writes; read per 02 | Silent destructive edits |
| Tenant / Garage Management | Maintain Tenants, memberships and Vehicle Tenant history | Tenant information, assignments, context | Back Office administration; Owner authorized read; system boundary | Normal user Tenant Merge |
| User & Permission Management | Provision identities, roles, Tenant assignments and account states | Users, memberships, access history | Back Office Owner/Accountant provisioning; Accountant Investor/Media provisioning | Authentication mechanics |
| Back Office | Control system/Tenant administration and sensitive defaults | Administrative configuration, audit | Back Office Admin; system/global and Tenant scopes | Daily accounting operations |
| System & Business Configuration | Version applicable defaults and Owner recipient allocations | Investor/Owner defaults, Tenant overrides, history | Back Office for defaults; global/Tenant | Hard-coded percentages |
| GST / Tax / Invoice Capability | Retain applicable tax/invoice information | Optional tax/invoice data | Accountant within authorized operations; relevant Tenant | Full accounting/tax suite |
| Owner AI Assistant | Explain verified authorized data | Read-only analysis | Owner only, within authorized Tenant scope | Writes or AI-generated financial truth |

## Controlled supporting operation

Tenant Merge is not a normal module or navigation action. If needed, Back Office/controlled system administration follows supporting/tenant-merge-consolidation.md and preserves both historical and financial truth.

## Current exclusions

No dedicated Cash/Bank account module, cash-versus-bank operational ledger, General Garage Expense module, payroll/attendance, Labour Vehicle or Work-Type assignment, full CRM, separate loss-allocation engine, duplicate media module, or normal Tenant Merge workflow. Detailed financial behavior belongs to 05; role permissions belong to 02.
