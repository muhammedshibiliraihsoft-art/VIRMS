# Phase 6 source contracts — working design

**Status:** WORKING DESIGN, not implementation ready. Baseline `26e509a1`, 2026-11-17. This note records source-level findings and a design to validate before coding; it does not change V2 business rules.

## Customer Job cost payment decision — 2026-11-18

The user approved recording actual workshop payments in instalments linked to the Customer Job cost, with remaining amount visible and one Accounting cash effect per actual payment; see V2 `10`. The existing `GarageCustomerCost` is not an Accounting Expense and has no payment source link. Generic Accounting `PAYMENT` requires an Accounting Expense target, which would introduce an independently recognized Expense and is therefore not an equivalent source contract. Design an additive typed link to an Accounting-owned payment event, same-Company/Branch checks, one exact outflow, transaction/idempotency and a shared Job lock for payments and cost corrections. Partial payments and cost reductions must not produce an unexplained negative payable. Payment/refund corrections, references, module-OFF behavior and applicable authorization must be reconciled with approved rules and existing patterns before enabling the workflow. This is a design note, not a claim that the payment flow is implemented.

## Customer Job cost vendor refund decision — 2026-11-18

The user approved a real workshop refund as one Accounting cash receipt, linked to the Customer Job cost for the applicable amount; the Accountant chooses an appropriate destination for any excess. See V2 `10` and the existing Vehicle Expense rules in V2 `01` (Q118/Q123/Q124/Q132). The existing Vehicle implementation supports explicit new Income classification but its narrow option must not be assumed to cover every appropriate destination. A refund is not a reversal of a real payment: paid net of applied refunds, cost-correction floors and payment-correction limits must agree under the same Job lock. The complete contract must preserve the full receipt, typed allocation, cross-Company/Branch authorization, audit, idempotency, source/target limits, correction history and rollback. Do not silently classify excess as Income or expose a partial implementation as the finished workflow.

**Incomplete local schema draft:** Accounting migration `0016` and Garage migration `0025` add the refund type/model only. They do not implement allocation, posting, audit or integrity triggers and must not be applied to a persistent database or treated as a working refund flow. Docker access was denied in the current sandbox, so these migrations have not been tested. The draft must gain deferred source/cash-shape guards and correction-aware net calculations before integration and disposable PostgreSQL verification.

**Follow-up:** Disposable PostgreSQL became accessible via approved sandbox escalation. Migration `0026` temporarily rejects all draft refund events and links at the database boundary; a fresh disposable test database replayed migrations and one focused test verified that an unimplemented refund event is rejected. This fail-closed guard is temporary and must be replaced by the complete refund source and allocation integrity contract; it does not implement refunds or authorize applying these migrations to a persistent database.

A separate disposable PostgreSQL test also verified that an existing Accounting Income event cannot be linked through the unimplemented refund model. This is a guard check only, not refund allocation or end-to-end verification.

`apps/garage/refund_allocation.py` now contains independently tested Decimal arithmetic to split an actual refund into the portion covered by net payments and excess, without choosing or posting a destination. Two unit tests cover partial, excess, zero prior payment, invalid inputs and 38-digit values. This helper is not yet connected to an API or database operation; callers must provide transaction-locked authoritative values. The fail-closed guard remains.

An internal, read-only `preview_customer_cost_refund` now obtains the Job through the existing Company/Branch read scope and derives a proposed split from current payments and linked refunds. A focused disposable PostgreSQL test verified the split, inaccessible cost rejection and absence of a new cash movement. It is not an API, reservation, permission to post, or a consistent locked snapshot; a future posting must re-read and recompute under the Job lock and independently authorize the financial action.

The preview now takes the Job row lock in a short transaction while reading payment and refund totals, superseding the earlier unlocked-snapshot statement. A disposable PostgreSQL concurrency test held this lock while a payment attempted to commit and verified that the preview returned its pre-payment snapshot and the payment completed afterward. This snapshot does not reserve money; future posting must still reauthorize and recalculate under its own lock.

The preview is now also exposed through a Company/Job/cost-scoped GET endpoint with one positive, two-decimal amount. A disposable PostgreSQL API test verified the result, invalid and repeated parameters, cross-Company denial and no additional cash movement. It is a nonbinding preview, not a transaction or refund posting, and the earlier statement that it is not an API is superseded. No UI consumes this endpoint yet.

The customer cost payment panel now offers an explicitly requested refund preview with the cost-applied and other-destination amounts. It states that no refund is recorded and values may change. Twelve focused React tests and the production build passed; this supersedes the previous UI absence statement. Live browser verification and actual refund posting remain outstanding.

Repeating Calculate for the same refund amount now requests a fresh preview and hides the prior result while loading. Five focused payment-panel tests and lint passed. This does not reserve a refund amount or implement posting.

A disposable PostgreSQL concurrency test races a customer cost reduction against a payment exceeding the reduced cost. One succeeds and one conflicts; the saved cost remains at least the paid total and the Accounting cash outflow equals that total. This tests the pre-refund payment/cost contract and does not prove refund behavior.

## Current implementation evidence

- `apps/vehicles/services.py:create_vehicle_expense` enters `execute_domain_mutation`, uses the Vehicle's current Branch, locks Vehicle and Fund credits, enforces Vehicle and funding actions, and creates one `VehicleExpense` plus Fund-use allocations. Its API is not a safe cross-request transaction for creating a Garage Job cost.
- `apps/accounting/services.py:create_receipt_or_payment` requires a current `INCOME` target, then posts an Accounting `RECEIPT`, movement and application. `INCOME` participates in the current bounded accounting result. Creating generic Income for the full Job charge could therefore decide Garage Revenue recognition before V2 permits it.
- `apps/vehicles/services.py:create_sale_receipt` illustrates a domain-specific cash event, typed `AccountingSourceLink`, parent row lock, action and module checks, and idempotent transaction. `AccountingSourceLink` is protected by exactly-one-source and same-Company database rules; adding a source requires migration and trigger review.

## Proposed Stock Job cost contract

One source of Stock cost: an existing Vehicle-owned `VehicleExpense` linked to one Garage Job by a typed, same-Company, same-Vehicle relationship. Use a uniqueness constraint to prevent a Vehicle Expense being assigned to two Jobs. The Vehicle total continues deriving cost from Vehicle Expense alone; the Garage view reads the linked source and its audited corrections. A Job cost link does not itself add a cost or create a Fund-use record.

Extract or share the existing domain operation inside one outer transaction rather than invoking two independent public commands. Lock/revalidate Company and module revisions, actor scope, Vehicle, Job, and Fund credits under a single documented lock order, including Vehicle movement writers. Recheck Job OPEN, original Job Branch and Vehicle's current Branch under lock. If current Branch differs, do not silently attribute the old Job cost to the new Branch: retain the history and require a reviewed compatible source operation; the precise historical-Branch rule must be reconciled with existing policy before enabling this path.

## Proposed external Job cash contract

Garage owns the agreed charge and its revision history. Actual receipts are Accounting-owned domain-specific receipt events, each with one movement and an explicit typed, same-Company relationship to the Job receipt source. An unapplied or generic Income event is not used to fabricate a charge. Garage receivable equals current charge less valid linked receipts/corrections, not a separately editable balance. Do not present the Garage source as recognized Company Profit until the separate V2 recognition rule is decided.

Use the existing Company row/module locking and scoped mutation framework, with a single idempotency key and result committed with the Job receipt, Accounting event, movement, source link and audit. Lock the Job/charge parent for both receipt and charge correction. Recheck current outstanding and reject overcollection or reduction below collected amount. Add database-backed uniqueness for the required Company-wide Garage receipt reference; exact normalization is not specified by the approved Garage rule and must not be borrowed silently from Sale. Keep rollback complete on errors and handle retries without duplicate movements.

## Unresolved engineering checks

1. Trace `AccountingEvent` event-type checks, movement triggers, append-only triggers, report filters and OFF-state authorization to define the new event and correction path without disturbing existing events.
2. Trace Vehicle movement, Company lock and `execute_domain_mutation` lock ordering across all affected writers; confirm no deadlock and preserve original Job Branch.
3. Confirm exact supported Garage action policy with Company/Branch grants, including the authorized Labour payment actor; no permission may be inferred from existing Vehicle roles alone.
4. Design additive migrations and disposable PostgreSQL tests for constraints, source tenancy, concurrency, duplicate reference, retries, rollback, accounting result exclusion and Phase 5 regressions. Complete these before claiming the source contract is ready.

## Correction implementation constraints observed on 2026-11-18

- `AccountingEvent` already models a reversal and an optional replacement as immutable events with one reversal and one replacement per original. The generic correction endpoints deliberately admit only their own Income/Expense/Receipt/Payment types, not `GARAGE_RECEIPT` or `LABOUR_PAYMENT`.
- Garage migration `0010` and Labour migration `0016` currently require each of those typed events to have one original source link, one exact movement, a positive effect and no reversal or replacement. They reject the generic Accounting reversal and replacement shape. Editing those guards without a new typed correction link would either leave events unattributed or break existing source invariants.
- Garage's existing outstanding calculation and the charge-floor/receipt-cap database triggers sum the original receipt event amounts. A correction-aware implementation must change all three consistently; merely adding reversal movements would leave the Job showing the wrong amount. Job locking must cover correction, receipt and charge updates together.
- The original Company-wide unique receipt reference is attached to the immutable receipt. Any correction representation must preserve that uniqueness, history and cross-Company isolation; it cannot insert a second original receipt with the same reference. The source link, reversal/replacement shape, account movement and audit evidence must commit atomically.
- A future additive schema must keep existing original records valid, reject orphan or cross-Company correction links, verify reversal and replacement movement amounts and actor/Branch scope, and reject duplicate or stale correction attempts. It needs fresh and populated upgrade/replay tests, failure rollback, multi-user receipt/charge/correction races, OFF-state authorization tests and existing Accounting/Vehicle regression tests. Those changes are not yet implemented or verified.
