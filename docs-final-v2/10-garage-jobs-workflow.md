# 10 — Garage Jobs & Work Workflow

Status: DRAFT V2 — Garage operations source after approval

## Scope and separation

The Garage Module operates within a Company and its Branches. A Branch/Garage is not a Tenant. It supports Company/Investor-funded Stock Vehicle work and external customer Vehicle work as financially distinct flows. Garage owns Job work/status/history and Branch attribution; Investment owns Investor Fund, agreement and settlement; Accounting owns Company income/Expense, receipts/payments and Garage Revenue. The Garage Module must function when Investment is OFF.

The BILLTECH legacy system is a process reference only. It does not define VIRMS architecture, UI, authentication, accounting rules, tyre-retail features or database schema. Use only real work concepts needed by this business.

## Company/Investor Stock Vehicle work

A Stock Vehicle has stable Company identity and exactly one funding Investor. The Job records the Company, working Branch, Vehicle, work details, Labour work/cost where applicable without requiring a worker assignment, materials/parts, approved Expenses, source references, charge/cost where relevant, status and history. Work in another Branch links to the same Vehicle after a recorded movement; it never duplicates the Vehicle or changes its Investor. Relevant approved cost joins consolidated Vehicle costing **once** and retains the Branch where it arose. The approved funding source may be Investor Available Fund or actual Company Running Capital; Job data alone does not debit either source. Investment and Accounting confirm their respective financial events under 05 and 09.

Vehicle-level Labour Expense can be the total approved work cost. A manual Labour Payment to a worker is a separate Company/Branch transaction and is not automatically allocated to the Vehicle. Labour remains a managed record with basic details, Active/Inactive state, manual amount/date, optional note and payment history. Login, fixed salary, payroll, attendance, worker-to-Vehicle assignment, Work-Type scheduling and worker-level costing are not initial requirements unless separately approved.

## External customer Vehicle work

An external customer Vehicle has stable Company-wide identity and Branch movement/history for Garage purposes, but it needs no Investor. The Job records customer/Vehicle, Branch, work, Labour/materials, cost, customer charge, actual receipt, outstanding balance, status and audit history. Conceptual flow: `External Customer Vehicle → Garage Job → work and approved costs → customer charge → actual receipt/remaining balance → Garage/Company Revenue`.

An agreed charge is not an actual receipt. Partial customer collection and remaining balance are recorded and visible. Investment Fund, Investor percentage, Investor principal recovery and Stock Vehicle positive-share allocation do not arise solely from the external customer Job. Any explicit investment relationship would require its own approved business rule rather than silent reuse of a funded Stock Vehicle workflow.

## Branch activity and correction

Every Job, work entry and Expense retains its Company, creating Branch, Vehicle and actor context. Authorized same-Company users may see previous-Branch history of a moved Vehicle. Another Branch cannot ordinarily edit the earlier Branch's record; explicit Company-level correction authority can permit an audited linked correction. Transfer changes current Branch/location and preserves all prior Jobs, costs and source attribution. Company reports can consolidate a Vehicle and filter Branch activity without creating Branch financial silos.

Amounts, customer balance and Job status may be calculated or suggested; actual Company receipt/payment and sensitive correction require human confirmation. A confirmed financial Job event is never silently deleted or rewritten. Corrections preserve original record, old/new values, reason, actor and timezone-aware time and reconcile with Accounting rather than posting a second revenue or Expense.

Under 01's automation levels, backend-calculated approved Job totals and customer outstanding balances are Level 1. Editable expected work/charge suggestions where allowed are Level 2. Pending/ready Job status and unpaid customer charge are Level 3 reminders/statuses, never receipts. Actual customer receipt, Expense payment and consequential correction are Level 4 authorized human-confirmed events. Unusual Job/funding corrections are Level 5 manual exceptional handling with reason and audit; any resulting financial event still requires its own authorized confirmation. Garage automation does not grant Investment access, post Investor Fund money or settle a Stock Vehicle automatically.

## Materials, media and current exclusions

Initial parts/materials may be recorded as approved Vehicle or Job costs. Full stock-level Parts Inventory, barcodes, tyre-retail schemes, manufacturing and generic ERP processes are not required. The design may later integrate an approved Inventory module without changing the ownership of existing Job and financial history. Current approved Vehicle media/publication rules in 08 are not automatically expanded into a public gallery of external customer work; private customer records remain protected.
