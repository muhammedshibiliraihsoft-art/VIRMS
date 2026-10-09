# 05 — Vehicle / Investor / Finance Workflow

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — FINANCE WORKFLOW SOURCE OF TRUTH

Authorization follows 02. Persistent financial sources and relationships follow 04. This document defines ordering and state transitions.

## 1. Investor and principal Fund

Investor and Fund are global. Each relevant Fund Ledger movement retains Investor, amount, type, time, and Vehicle/Tenant context. Principal and Profit are distinct.

| Position | Meaning |
|---|---|
| Total Principal Fund | Principal supplied through valid initial/additional funding transactions, subject to legitimate historical corrections |
| Available Fund | Greater of zero or (Gross Fund Ledger Balance − outstanding Owner Contribution Return Payables − Buyer Principal Refund Reserves); Gross Fund Ledger Balance is net valid principal credits/debits before these reserves |
| Currently Used / Locked Principal | Sum of the Investor's nonnegative Outstanding Vehicle Principal positions, including deployed or financially unresolved Vehicle principal |
| Recovered Principal | Cumulative historical principal restored by actual Buyer recovery and actual Owner loss coverage, with each source identifiable |
| Profit Earned / Eligible / Paid / Pending | Separate profit positions, never principal |

Available Fund is derived from the Fund Ledger balance after reserving only money actually held for outstanding Owner Contribution Return Payables and Buyer Principal Refund Reserves. An uncovered return/refund amount remains payable and cannot make Available Fund negative. Purchase/Expense debits reduce the Fund; actual Principal Recovery and Owner Loss Contribution credits increase it. An actual contribution return or principal-backed Buyer refund records a separate debit to the same Investor Fund and reduces the linked payable/reserve. Cumulative Recovered Principal is a reporting metric and is not added again to Available Fund. Redeploying recovered money debits Available Fund but does not decrease historical Recovered Principal.

## 2. Purchase and expense

Before purchase validate one Investor, current Tenant, eligible Investor lifecycle, and sufficient Available Fund. Commit Vehicle/Purchase, Fund use, and ledger movement atomically; Vehicle begins Purchased. Each approved Vehicle Expense belongs to that Vehicle, uses the same Investor Fund, and atomically increases Vehicle cost while reducing Available Fund. Total Vehicle Cost = Purchase Cost + valid approved Vehicle Expenses. Dynamic Expense Categories are supported.

Current Vehicle lifecycle: Purchased → In Work → Ready → Listed → Sold. Tenant transfers preserve Vehicle Tenant History. Labour Payment is not automatically a Vehicle Expense; an approved Vehicle-level Labour Expense is a separate cost record.

## 3. Sale and collection

Record a Tenant-consistent Buyer, Agreed Total Sale Price, and the applicable Investor agreement and Owner allocation configuration. On Sale confirmation:

1. Create the authoritative Sale and mark Vehicle Sold.
2. Calculate Vehicle Profit/Loss = Agreed Sale Price − Total Vehicle Cost.
3. Preserve the applicable percentage/configuration snapshot and calculated recipient allocations.
4. Begin the separate Buyer collection state: Pending, Partially Received, or Fully Received.

Each actual receipt is an individual Sale Payment. For an ordinary Sale, Amount Received is the sum of valid confirmed payments and Receivable is Agreed Sale Price minus those payments. A repeat/retry must not duplicate a receipt. Unreceived amounts create no Fund credit or payout eligibility.

For an ordinary uncorrected Sale, Remaining Receivable = Agreed Sale Price − confirmed valid Sale Payments; the correction-specific applied-amount formula below governs a corrected Sale. A new Sale Payment must satisfy `0 < Payment Amount <= Remaining Receivable`. The backend rejects an excess payment with a clear validation error; no role may override it, and no excess becomes Buyer credit, automatic refund-ledger activity, Profit, Principal, or Investor Fund credit. Validate and post atomically with appropriate locking/version protection so concurrent requests cannot produce aggregate payments above the current Agreed Sale Price. Remaining Receivable may become zero but never negative.

If a later authorized Sale correction lowers Agreed Sale Price below cash already received, preserve all original receipts and create `Buyer Refund Payable = max(0, Gross Confirmed Buyer Payments − Actual Buyer Refund Payments − Corrected Agreed Sale Price)`. `Sale Applied Buyer Amount = Gross Confirmed Buyer Payments − Actual Buyer Refund Payments − Outstanding Buyer Refund Payable`; corrected Remaining Receivable = Corrected Agreed Sale Price − Sale Applied Buyer Amount and cannot be negative. The pending refund remains actual cash held but is not applied to the corrected Sale, recovered principal, or collected Profit. Record each actual refund separately, reducing cash held and the payable by the same amount. A refund obligation arises only from the correction; it does not permit an excess new Buyer Payment.

Each actual Buyer refund must satisfy `0 < Refund Amount <= Outstanding Buyer Refund Payable`, with atomic, duplicate-safe and concurrency-safe posting. Reconcile its linked principal-backed and collected-Profit portions to the exact amount actually refunded; reverse the latest applied receipt portions first, so collected Profit is reversed before earlier principal when both were present. An unpaid Buyer Refund Payable blocks new Profit payout eligibility and final Settlement, even if the corrected Sale Applied Buyer Amount equals the corrected Agreed Sale Price.

## 4. Principal Recovery

Allocate each actual Buyer receipt to outstanding Vehicle Principal first. Record each recovery as an auditable Fund Ledger credit to the same Investor; this increases Available Fund. Only the portion of actual receipt after principal recovery is collected profit. Unreceived Sale Price never becomes recovered or available.

Recovered Principal remains cumulative even if reused. A linked correction or actual principal-backed Buyer refund changes the corrected net valid cumulative amount while keeping every historical movement visible; redeployment alone never reduces it. If Investor is Exit Requested or Settlement Pending, recovered principal is not used for a new Vehicle purchase. A fully collected Sale may still have financially unresolved principal when the deal is a loss; resolution follows section 6.

Vehicle Principal Used = Purchase Cost + valid approved Vehicle Expenses. Before Sale, that full deployed amount is Outstanding Vehicle Principal. After Sale:

`Retained Owner Loss Contributions = Actual Owner Loss Contributions − Actual Contribution Returns Paid − amounts designated as Owner Contribution Return Payables`

`Outstanding Vehicle Principal = Original Vehicle Principal Used − Net Confirmed Buyer Principal Recoveries After Linked Allocation Corrections − Confirmed Investor Loss Recognition − Retained Owner Loss Contributions + Principal Correction Increases − Principal Correction Decreases`

This position cannot be negative. For each actual Buyer receipt, Principal Recovery = the lesser of the receipt and current Outstanding Vehicle Principal. Only the remainder of that actual receipt is collected Profit. Each component is recorded once from its distinct source; calculated Loss or an unrecorded Owner contribution never counts as money recovered.

If a later authorized cost or Sale correction changes how a previously confirmed Buyer receipt should have been divided, preserve that receipt and its original allocation and record a linked reclassification. Reallocate only the Sale Applied Buyer Amount to corrected outstanding principal before collected Profit. Credit the Investor Fund only for an additional valid principal portion. If a principal allocation decreases without a pending Buyer refund, reverse its Fund effect through a linked adjustment. If the reduction corresponds to a pending Buyer refund, retain the original Fund credit and create a Buyer Principal Refund Reserve for that portion until actual refund records the Fund debit and clears the reserve. The corrected net Buyer Principal Recovery is the amount used in Outstanding Vehicle Principal and Fund reconciliation. A reclassification is not another Buyer Payment, cannot duplicate Recovered Principal, and must update Profit eligibility and any resulting payout adjustment.

Example: Vehicle cost 1,000, original Sale Price and fully received Buyer Payment 1,100, and original Buyer Principal Recovery 1,000. A legitimate correction lowers the Sale Price to 900. The original 1,100 receipt remains historical; 200 becomes Buyer Refund Payable, only 900 remains applied to the corrected Sale, corrected Buyer Principal Recovery is 900, and 100 of the unpaid Buyer refund is a Buyer Principal Refund Reserve against the earlier Fund credit. The other 100 was previously classified as collected Profit. When the 200 is actually refunded, only its 100 principal-backed portion debits the Investor Fund and clears that reserve. Any prior Profit payout recovery and corrected Loss allocation remain separate.

## 5. Positive profit allocation and universal payout

For positive Vehicle Profit:

1. Use fixed-precision decimal arithmetic; authoritative money is INR and final posted amounts have two decimal places using `ROUND_HALF_UP`. Retain higher precision for intermediate percentage calculations and never use binary floating point.
2. Calculate Investor Profit Share from Profit and the snapshotted Investor percentage, then round that monetary share.
3. Derive Owners Pool = authoritative Profit − final Investor Profit Share.
4. For Owner recipients in configured allocation order, calculate at high precision and round normal allocations; set the final recipient amount to Owners Pool minus all previous finalized allocations. The complete allocation must exactly equal authoritative Profit.

Configuration validation requires an Investor percentage from 0% through 100%, inclusive, and nonnegative Owner allocation percentages totaling exactly 100% of the Owners Pool. A 0% or 100% Investor percentage is valid. A positive Owners Pool requires at least one configured recipient; a zero Owners Pool produces no Owner allocation for that deal. Reject invalid configurations before they can apply to a Sale.

Amounts may be Calculated when the Sale is confirmed, but no Profit Payment is eligible during partial Buyer collection. The universal sequence is:

Buyer actual payments → Principal Recovery → full agreed Sale Price collection → Investor Profit Share payout → Owner Profit Share payouts.

Full collection and recovery make applicable profit Eligible; Eligible is not Paid. Before that gate, eligible Profit Payment is zero even when a calculated entitlement exists. Accountant must explicitly confirm each actual payout and record it separately from the calculation. Complete the Investor Profit Share payout before any Owner Profit Share payout; Owner eligibility begins only after the deal's Investor Profit Share is fully satisfied. No system, Tenant, Investor, or Vehicle payout mode changes this sequence.

For each recipient, Outstanding Eligible Entitlement = Eligible Entitlement − confirmed valid Profit Payments. A new Profit Payment must satisfy `0 < Payment Amount <= Outstanding Eligible Entitlement`. The backend rejects excess payment without warning-only or manual override and without expanding entitlement. Validate and post atomically with appropriate locking/version protection so concurrent requests cannot collectively overpay.

## 6. Loss

For a negative result, Loss = Total Vehicle Cost − Agreed Sale Price. The snapshotted Investor profit-share percentage is also the Investor loss-share percentage. Apply the same fixed-precision, `ROUND_HALF_UP`, derived Owners Pool and final-recipient residual rules used for Profit so Investor loss plus Owner losses exactly equal authoritative Loss. A Loss Note is explanatory only; no manual loss-bearer selector or separate loss-allocation engine exists. Do not create positive-profit entitlements for a loss deal.

Loss allocation alone does not create cash, principal recovery, or an Available Fund credit. Record the Investor-borne share as an audited principal-loss recognition that reduces the Investor's remaining principal claim, never as money received. Each Owner-borne share must be actually contributed into the same Investor Fund; Accountant records the source-tagged principal coverage movement with the contributing Owner, Vehicle, Sale and Tenant before it increases Available Fund or resolves that share of outstanding principal. Preserve the distinction between Buyer-recovered principal and Owner-provided loss coverage. Only after full Buyer collection, Investor loss recognition, and every required actual Owner contribution may the Vehicle's loss-related principal position be treated as resolved for Investor Settlement.

Investor Loss Recognition reduces the Investor's principal claim but does not create or credit cash. An actual Owner Loss Contribution credits Available Fund and covers the corresponding unresolved principal shortfall; it does not increase the Investor Principal Claim. After all required events, the Vehicle's Outstanding Vehicle Principal must be zero.

Example: Cost 1,000 and fully collected Sale 900 create Loss 100. If the applicable Investor loss share is 30 and Owners' combined share is 70, record Buyer recovery 900, Investor principal-loss recognition 30, and actual Owner contributions totaling 70 before the Vehicle principal position is resolved. Available principal grows only through the 900 and the actual 70, never through the calculated loss allocation alone.

## 7. Exit, settlement, and correction

Normal Investor exit requires Terms & Conditions acceptance and a three-month notice. Exit Requested blocks new Vehicle purchases but permits previously funded approved work, Sales, collections, and recovery. Notice expiry and exceptional early closure do not unlock Vehicle capital. Accountant may manage exceptional early closure with audit; Owner is read-only.

Current Investor Principal Claim = valid initial/additional Investor principal − confirmed principal settlements paid to the Investor − confirmed Investor Loss Recognition + principal claim increases from linked corrections − principal claim decreases from linked corrections. Owner Loss Contributions are coverage of a shortfall: they credit the Fund but do not increase this claim. Reconcile the claim to Gross Fund Ledger Balance + Currently Used / Locked Principal − outstanding Owner Contribution Return Payables − Buyer Principal Refund Reserves. Available Fund = greater of zero or (Gross Fund Ledger Balance − those two outstanding reserve amounts); if combined reserves exceed the gross balance, the uncovered amount remains unresolved and the equivalent reconciliation is Available Fund + Currently Used / Locked Principal − that uncovered amount. No negative Available Fund or fictitious liquidity is permitted.

Settlement evaluates the Investor's global position across Tenants: Available and Locked Principal, recovered history, earned/eligible/paid/pending Profit, Buyer receivables, unsold Vehicles, corrections, and unresolved loss positions. After all Vehicles and required positions resolve, Principal Settlement Payable = Available Fund and must equal Current Investor Principal Claim. Any mismatch remains unresolved and blocks closure.

Each actual Principal Settlement payment to the Investor records a linked Fund Ledger debit and reduces Available Fund and Current Investor Principal Claim by the paid amount. The current unpaid Principal Settlement Payable is recalculated from the remaining Available Fund after that debit; a payable calculation or Settlement status change does not itself transfer money.

Outstanding Eligible Investor Profit = sum across the Investor's deals of the greater of zero or (corrected current Eligible Investor Profit Entitlement − confirmed valid Investor Profit Payments). Any Additional Payable representing that same positive difference labels the amount and is not added again.

Investor Settlement Payable = Principal Settlement Payable + Outstanding Eligible Investor Profit. Recovery Obligations owed by the Investor, Owner Contribution Return Payables, Buyer Refund Payables, Buyer receivables, Locked Principal, and other correction positions are resolved and recorded separately before final closure. Each actual Owner contribution return or principal-backed Buyer refund debits the same Investor Fund and reduces its linked payable/reserve; the portion previously reserved is released by the same amount. If a return/refund obligation exceeds current Fund liquidity, record the full obligation but leave the uncovered portion pending until money is actually available. A Buyer refund amount previously treated as collected Profit has no Investor Fund debit; any recovery of already paid Profit is a separate recorded obligation. Do not silently net an obligation against a payable. Settlement is Closed only when all required principal, receivable, refund, Profit, Owner contribution, correction and recovery positions are resolved, the principal reconciliation matches, and all settlement amounts owed have actual recorded payments. Settlement must not manufacture liquidity.

Corrections preserve the original authoritative posting, timestamp, actor, financial values and historical percentage/configuration snapshot, plus the linked correction/reversal/adjustment, correction actor, timezone-aware timestamp, reason and resulting current position. Never silently overwrite or delete the original.

If correction occurs after calculation/finalization but before payout, preserve the original calculation and snapshot, record the linked adjustment, and use the corrected current outstanding entitlement for future payout. If confirmed payment already exists, preserve it and calculate `Adjustment Position = Corrected Entitlement − Confirmed Valid Payments`: positive creates Additional Payable, negative creates an explicit Recovery / Adjustment Obligation, and zero creates no further adjustment. A negative adjustment never silently changes Investor Fund or Principal, deletes a payment, rewrites paid entitlement, or records recovery without actual settlement.

A legitimate correction may change Profit amount, Profit to Loss, Loss amount, or Loss to Profit. Apply the original deal's historical percentages, canonical rounding and loss/contribution rules, then record resulting adjustment obligations. Any Additional Payable, Recovery / Adjustment Obligation, Owner contribution obligation or other required adjustment remains unresolved until its actual settlement is recorded. If an earlier Settlement was Closed, preserve that closure event and track the correction-related unresolved position separately.

For a Profit-to-Loss correction, corrected positive-Profit Entitlement is zero. The adjustment for each recipient is therefore zero minus that recipient's confirmed prior Profit Payments; any negative result is a Recovery / Adjustment Obligation. Calculate and record the corrected Loss allocations separately using the original snapshot. Prior Profit payout recovery and new Loss allocation/contribution are distinct obligations and must not be silently netted.

For a Loss-to-Profit correction, reverse the prior Investor Loss Recognition through a linked principal adjustment. Record return of every actual prior Owner Loss Contribution as a separate Owner Contribution Return Payable. Reserve only money currently held in the same Investor Fund; any uncovered amount stays payable and blocks final Settlement without making Available Fund negative. An actual return debits that Fund and reduces the payable. Calculate corrected Profit allocations using the original snapshot. Do not delete prior loss/contribution history, and do not automatically net contribution returns against Profit Payments.

For either crossover, the corrected positive-Profit Entitlement is the corrected positive allocation only; Loss allocations are separate principal/coverage positions, never negative Profit Entitlements. All correction obligations remain unresolved until each actual settlement is recorded.

Critical purchase, expense, Sale, receipt, recovery, payout, correction, obligation-settlement, and Investor-settlement writes must be atomic, concurrency-safe, and duplicate-safe.
