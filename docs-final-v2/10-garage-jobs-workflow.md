# 10 — Garage Jobs & Work Workflow

Status: DRAFT V2 — Garage operations source after approval

## Scope and separation

The Garage Module operates within a Company and its Branches. A Branch/Garage is not a Tenant. Vehicle Management owns the single Company-wide Vehicle aggregate, stable identity, lifecycle, current Branch/location and movement history. Garage supports Stock Vehicle work and external-customer work as distinct per-Job contexts. Garage owns Job work/status/history, approved Job cost source, customer charge and Branch attribution; Investment owns Investor/Fund and financial events; Accounting owns actual Company receipts/payments and Garage Revenue. The Garage Module must function when Investment is OFF.

Every protected Garage action also requires authenticated Company membership, effective Branch assignment, enabled Garage module, role/action permission and object scope under 02. The frontend is presentation only. The Garage workflow does not add cross-Branch correction authority.

The BILLTECH legacy system is a process reference only. It does not define VIRMS architecture, UI, authentication, accounting rules, tyre-retail features or database schema. Use only real work concepts needed by this business.

## Company/Investor Stock Vehicle work

A funded Stock Vehicle has one active Investor responsibility. A Garage Job records the Company, working Branch, stable Vehicle UUID, explicit per-Job responsibility context, work, status and source references. A Job on an active Investor-funded Vehicle does not by itself debit Investor Fund. The approved financial source is recorded only by its owning module and authorized operation; actual Company Running Capital is separate. Relevant approved Job cost joins consolidated Vehicle costing once and keeps its original Branch attribution. Work in another Branch references the same Vehicle after a recorded movement; it never duplicates Vehicle identity or silently changes Investor responsibility.

Vehicle-level Labour Expense can be the total approved work cost. A manual Labour Payment to a worker is a separate Company/Branch transaction and is not automatically allocated to the Vehicle. Labour remains a managed record with basic details, Active/Inactive state, manual amount/date, optional note and payment history. Login, fixed salary, payroll, attendance, worker-to-Vehicle assignment, Work-Type scheduling and worker-level costing are not initial requirements unless separately approved.

## External customer Vehicle work

The same Vehicle UUID may later be used for external-customer Garage work after Investor responsibility ends. A new Job in that context does not affect the former Investor's Fund, principal, Profit, reconciliation or settlement. Job service-contact context is limited to Name and Phone; it does not prove legal Vehicle ownership or payer identity, and phone is not a unique identity key. The Garage workflow does not create a reusable Customer/CRM, merge, deduplication or marketing workflow. The approved field set is Name and Phone; whether each field is mandatory remains unresolved because no current Garage form or V2 rule establishes requiredness. Resolve that input before schema/API implementation or treat it as an explicit business-decision gate.

The Job records Vehicle, Company, Branch, context, work, approved cost source, agreed customer charge, OPEN/COMPLETED status and audit history. Accounting records the single actual Company receipt and Garage Revenue event; the Job references the Accounting receipt identifier rather than maintaining a second receipt amount. Outstanding balance is derived from charge and linked valid receipt/correction events. Each receipt requires an operator-supplied external reference unique Company-wide across Branches; another Company may use the same reference. Total valid receipts must not exceed the applicable Job charge, and a charge cannot be reduced below valid receipts. Do not add automatic refund or customer-credit behavior. The backend must enforce the cap atomically so concurrent receipts cannot over-collect. Conceptual flow: external-customer Job → work and approved costs → Garage charge/receivable → one Accounting receipt/revenue source → derived outstanding balance.

An agreed charge is not an actual receipt. Partial customer collection and remaining balance are recorded and visible. Investment Fund, Investor percentage, Investor principal recovery and Stock Vehicle positive-share allocation do not arise solely from the external customer Job. Any explicit investment relationship would require its own approved business rule rather than silent reuse of a funded Stock Vehicle workflow.

## Branch activity and correction

Every Job, work entry, movement and cost retains its Company, creating Branch, Vehicle and actor context. Authorized same-Company users may read previous-Branch history of a moved Vehicle. Phase 6 denies cross-Branch mutation by default and introduces no Company-level correction grant; a broader grant remains outside ordinary Phase 6 behavior. Transfer changes current Branch/location and preserves all prior Jobs, costs and source attribution. Company reports can consolidate a Vehicle and filter Branch activity without creating Branch financial silos.

The only current Garage Job status values are OPEN and COMPLETED. A new Job is OPEN. OPEN may transition to COMPLETED, and COMPLETED may be reopened to OPEN. While COMPLETED, work, cost and charge entries cannot be added or changed; reopen the Job first. Keep status values centralized and preserve status history with actor and time. Future status values may be added without changing Vehicle identity or rewriting Job history.

Amounts and outstanding balance are derived from their authoritative sources; an agreed charge is not a receipt. Actual Company receipt/payment and sensitive correction require human confirmation. A confirmed financial fact is never silently deleted or rewritten. Corrections preserve original record, old/new values, reason, actor and timezone-aware time and reconcile through the authoritative module without a second revenue or cost event.

When Garage is OFF, deny new Jobs, optional expansion of existing Jobs and unrelated new Garage charges. Authorized history/read access remains available. Actions strictly required to resolve already-open financial obligations may remain available only through their authoritative module (for example Accounting) and its normal role/object permissions. Do not create a generic Garage shutdown or settlement engine.

Under 01's automation levels, backend-calculated approved Job totals and customer outstanding balances are Level 1. Editable expected work/charge suggestions where allowed are Level 2. OPEN/COMPLETED Job status and unpaid customer charge are not receipts. Actual customer receipt is a Level 4 Accounting event; cost/payment and consequential correction use their owning module and authorized operation. Unusual Job/funding corrections are Level 5 manual exceptional handling with reason and audit; any resulting financial event still requires its own authorized confirmation. Garage automation does not grant Investment access, post Investor Fund money or settle a Stock Vehicle automatically.

## Materials, media and current exclusions

Initial parts/materials may be recorded as approved Vehicle or Job costs. Full stock-level Parts Inventory, barcodes, tyre-retail schemes, manufacturing and generic ERP processes are not required. The design may later integrate an approved Inventory module without changing the ownership of existing Job and financial history. Current approved Vehicle media/publication rules in 08 are not automatically expanded into a public gallery of external customer work; private customer records remain protected.
