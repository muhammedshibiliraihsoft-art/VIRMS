# 01 — Business Rules

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — BUSINESS SOURCE OF TRUTH

## Authority

This document defines business behavior. Document 02 governs permissions, 04 governs persistent data truth, and 05 governs financial state transitions. The latest explicitly locked user decisions incorporated here supersede older wording in /docs. A change to these rules requires an explicit business decision.

## Business and identity

- External Investors provide capital for Vehicle purchase and approved Vehicle work. Owners are profit recipients, not ordinary funding Investors in the current model.
- The cycle is Investor Fund → Vehicle purchase → approved Vehicle Expenses → Sale → actual Buyer collection → Principal Recovery → Profit distribution → Investor settlement where applicable.
- Each Vehicle has exactly one funding Investor. One Investor may fund many Vehicles. Investor and Investor Fund identities are global across Garages.
- Garage = Tenant. The business currently has two Garages, but their count is not a coded limit. All Garages use one system; operational records retain Tenant context.
- Persistent records use immutable backend-generated UUIDs. Names, phone numbers, registration numbers, and Garage names are editable attributes, never system identity.

## Investor principal

- Each Investor has one global, auditable principal Fund. Initial and additional capital are recorded as distinct transactions; a balance is not manually overwritten.
- Vehicle purchase and every approved Vehicle Expense use the assigned Investor's available principal. Normal operations must reject a purchase or expense that exceeds Available Fund.
- Gross Fund Ledger Balance is the net valid principal credits and debits before reserving outstanding return/refund obligations. Available Fund = greater of zero or (Gross Fund Ledger Balance − outstanding Owner Contribution Return Payables − Buyer Principal Refund Reserves). A Buyer Principal Refund Reserve is the Fund-backed portion of an unpaid Buyer Refund Payable that was previously credited as Principal Recovery but is no longer applied to the corrected Sale. Only money actually present can be reserved; any uncovered amount remains payable, creates no negative Available Fund, and blocks final Settlement. Purchase/expense debits reduce the Fund; actual Principal Recovery and Owner Loss Contribution credits increase it. An actual contribution return or principal-backed Buyer refund records a Fund debit and reduces the corresponding payable/reserve by the same amount. Do not add cumulative Recovered Principal again in an Available Fund formula.
- Currently Used / Locked Principal is the sum of each of the Investor's nonnegative Outstanding Vehicle Principal positions, including Vehicle principal still deployed or financially unresolved. Recovered Principal is a cumulative historical metric; redeployment never reduces it. A linked correction or actual principal-backed Buyer refund changes the corrected valid cumulative amount while preserving every original movement and adjustment in history.
- Vehicle Principal Used = Purchase Cost + valid approved Vehicle Expenses. After a Sale, Outstanding Vehicle Principal = original Vehicle Principal Used − net confirmed Buyer Principal Recoveries after linked allocation corrections − confirmed Investor Loss Recognition − retained Owner Loss Contributions + principal correction increases − principal correction decreases. Retained Owner Loss Contributions = actual contributions − actual contribution returns paid − amounts designated as Owner Contribution Return Payables. Outstanding Vehicle Principal must never be negative. Before Sale, the full deployed Vehicle Principal remains outstanding.
- Each actual Buyer receipt recovers `min(receipt amount, Outstanding Vehicle Principal)` as principal. Only the remainder of that actual receipt is collected profit. A receipt, loss allocation, or contribution may affect principal only once and through its separately recorded source event.
- Unused principal may remain Available. Recovered principal returns to the same Investor Fund and is not an automatic cash payout.
- Principal and Profit are separate. Profit never becomes new principal automatically.
- Investor Fund movements must retain Investor, amount, movement type, time, and Vehicle/Tenant context where applicable.
- A future protected negative-fund exception is outside current operations; current UI and normal backend flow must not permit negative Available Fund.

## Vehicle and expenses

- Vehicle identity is its UUID, not its registration. Record its funding Investor and current Tenant at creation; preserve Tenant transfer history.
- Current core lifecycle: Purchased → In Work → Ready → Listed → Sold. Sale state and Buyer collection state are separate; a sold Vehicle may still have Pending or Partially Received collection.
- Total Vehicle Cost = Purchase Cost + valid approved Vehicle Expenses. Each expense belongs to one Vehicle, is individually traceable, and uses that Vehicle's Investor Fund.
- Expense Categories are Tenant-scoped, manageable by authorized operational users, and extendable without a code deployment.
- Vehicle-level Labour Expense is a total work cost. It is distinct from a worker's manual Labour Payment; no worker-level Vehicle cost allocation is required.
- Sold Vehicles and their financial history must not be hard-deleted. Financial corrections use traceable correction/reversal history.

## Sale, collection, and recovery

- Full-payment, partial-payment, and credit Sales are allowed. Each Sale records the agreed total price and a Tenant-scoped Buyer; Buyer phone is required but is not globally unique identity.
- Vehicle Profit/Loss = Agreed Sale Price − Total Vehicle Cost. The agreed price, not money received so far, is the calculation basis.
- For an ordinary Sale, Amount Received is valid confirmed Buyer Payments and Remaining Receivable = Agreed Sale Price − Amount Received. A later corrected Sale Price below cash already received creates a separate Buyer Refund Payable: the greater of zero or (gross confirmed Buyer Payments − actual Buyer refunds − corrected Agreed Sale Price). The amount applied to the corrected Sale is gross confirmed Buyer Payments − actual Buyer refunds − outstanding Buyer Refund Payable; Remaining Receivable = corrected Agreed Sale Price − that applied amount and must remain nonnegative. Preserve original receipts and linked refund obligations/payments; cash still held for a pending refund is not applied Sale revenue or recovered principal.
- Each new Buyer Payment must be greater than zero and no greater than the current Remaining Receivable. The backend must reject any excess new payment without override, automatic Buyer credit, automatic refund-ledger posting, Profit, Principal, or Fund conversion; concurrent posting must never make Receivable negative. A separately authorized Sale correction may create the explicit Buyer Refund Payable above; only an actual recorded refund settles it.
- An actual Buyer refund must be greater than zero and cannot exceed the current Buyer Refund Payable. A pending Buyer Refund Payable prevents new Profit payout eligibility and final financial resolution; it is not a second Buyer Payment or an automatic deduction from prior Profit Payments.
- Every actual Buyer receipt is allocated to outstanding Vehicle Principal first. Principal Recovery is recorded in the Fund Ledger and increases Available Fund only through that actual recovery movement.
- A sale confirmation marks the Vehicle Sold even if Buyer collection is pending. Buyer payment state remains separate: Pending, Partially Received, or Fully Received.

## Profit, loss, and payout

- For a positive deal, Investor Profit Share = Profit × the applicable Investor-specific percentage. Owners Pool = remaining Profit. Owner allocations divide that Pool using the applicable configuration.
- Investor percentages are agreement-specific. The present standard Owner split is 48.5% and 51.5% of the Owners Pool, not of total Vehicle Profit. Owner allocations must be configurable and represented as recipient allocations rather than permanent fixed Owner columns. Tenant-specific Owner split configuration is supported.
- Investor-specific percentages may be set and later changed by the Accountant with mandatory old/new value, actor, time, scope, and Investor audit; Owner receives change visibility/notification. System and Tenant default profit configuration belongs to Back Office.
- Investor percentage must be between 0% and 100%, inclusive. Each applicable Owner allocation percentage must be nonnegative and the configured recipient percentages must total exactly 100% of the Owners Pool. A 0% Investor share and a 100% Investor share are permitted; a zero Owner Pool produces no Owner allocation for that deal, while a positive Owner Pool requires at least one configured recipient.
- For a loss, the same applicable percentages share the loss: Investor bears the Investor share; the Owners Pool bears the remainder; individual Owners bear their applicable allocations of that remainder. Use the deal's historical percentage snapshot. There is no manual loss-bearer selector. A Loss Note explains a loss but has no financial effect.
- At Sale confirmation, preserve the applicable Investor and Owner percentages/configuration and calculated result. Future changes never recalculate completed historical deals.
- Calculated, Eligible, and Paid are distinct. Profit payment is universally held until full agreed Sale Price collection and Principal Recovery. No early-payout modes exist.
- After full collection and principal recovery, the Investor Profit Share must be paid before Owner Profit Shares. Actual payouts require explicit Accountant confirmation; calculation or eligibility never marks an amount Paid.
- Outstanding Eligible Entitlement = Eligible Entitlement − confirmed valid Profit Payments for that recipient. Each new Profit Payment must be greater than zero and no greater than that current outstanding amount; the backend must reject excess or concurrent overpayment. Owner payout eligibility begins only after the Investor Profit Share for the deal is fully paid.
- The Investor-borne loss share reduces the Investor's principal claim through an audited loss-allocation movement; it is not received money. Each Owner-borne loss share requires an actual Owner contribution into the same Investor Fund, recorded with Owner, Vehicle, Sale, Tenant, amount, time and source. Only an actual contribution may restore Available Fund or resolve that share of outstanding principal. Buyer recovery and Owner loss coverage remain separately traceable.

## Monetary precision and allocation

- INR is the current operating currency. Authoritative money and percentage calculations use fixed-precision decimal arithmetic; binary floating point is prohibited. Final posted money has two decimal places and uses `ROUND_HALF_UP`; intermediate percentage calculations retain sufficient precision and are not rounded prematurely.
- Round the Investor share first, then derive Owners Pool as authoritative Profit/Loss minus that final Investor share. For the ordered applicable Owner recipient allocations, finalize preceding recipients with the canonical rounding rule and assign the smallest-unit residual to the final configured recipient. Investor Share plus all Owner allocations must exactly equal the authoritative Profit/Loss. Apply the same rule to positive Profit and Loss using the historical deal snapshot.

## Post-finalization financial corrections

- A finalized or paid posting is never silently overwritten or deleted. Preserve the original record, actor, timestamp, values and percentage/configuration snapshot; record a linked correction, reversal or adjustment with actor, timezone-aware timestamp, reason and resulting current position.
- Before payout, a correction updates current outstanding entitlement through a linked adjustment while retaining the original calculation. After payout, Adjustment Position = Corrected Entitlement − confirmed valid payments: positive is Additional Payable, negative is an explicit Recovery / Adjustment Obligation, and zero requires no further adjustment. Never silently deduct a negative adjustment from Investor Fund or Principal, delete payment history, or mark recovery without an actual recorded settlement.
- A correction may move a deal between Profit and Loss. Use the original deal's historical percentage/configuration snapshot and canonical loss rules. Any Additional Payable, Recovery / Adjustment Obligation, Owner contribution obligation or other required adjustment keeps the relevant current financial position unresolved. Preserve any earlier historical Settlement closure and track the new correction-related position separately until settled.
- For a correction from Profit to Loss, corrected positive-Profit Entitlement is zero. Confirmed Profit Payments therefore create Recovery / Adjustment Obligations equal to the payments already made; calculate the corrected Loss allocation separately. The payout recovery and Loss allocation are distinct obligations and must not be silently netted.
- For a correction from Loss to Profit, reverse the prior Investor Loss Recognition through a linked principal adjustment and record return of actual Owner Loss Contributions as separate Owner Contribution Return Payables. Calculate the corrected Profit allocation separately using the original snapshot. Do not delete past contributions or automatically net returns against Profit Payments.
- After a corrected Vehicle cost or Sale position changes the principal-first allocation of Buyer money already received, reclassify the affected portion of that same confirmed receipt between collected Profit and Buyer Principal Recovery through a linked adjustment. A shift into Principal Recovery credits the Investor Fund only for the newly allocated principal portion. A reverse shift records a linked Fund adjustment, or, when tied to a pending Buyer refund, reserves that principal-backed amount until actual refund debits the Fund. Preserve the original receipt and allocation history, and never record a second Buyer receipt or count the same principal recovery twice. Reassess Profit eligibility and any payout adjustments against the corrected position.
- A Buyer Refund Payable identifies the excess actual Buyer money owed back after a Sale correction; its principal-backed portion is reserved against the Investor Fund until the actual refund debits that Fund, and its collected-Profit portion remains separate from principal. The refund payment reduces both cash held and the outstanding payable by the same amount without erasing the original Buyer Payment. A pending refund, including any uncovered Fund-backed amount, blocks final financial resolution. Prior Profit Payments and their correction-related recovery obligations remain separate; never silently net them against the Buyer refund.

## Investor exit and settlement

- Normal Investor exit requires recorded Terms & Conditions acceptance and three months' notice. The lifecycle is Active → Exit Requested → Settlement Pending → Closed; historical identity and records remain.
- After Exit Requested, no new Vehicle purchase may use that Investor Fund. Already-funded approved Vehicle work, Sale collection, and Principal Recovery may continue.
- Notice expiry or exceptional closure never creates liquidity from unrecovered Vehicle capital. Settlement considers the Investor's global position across relevant Tenants, including Available and Locked Principal, profit, receivables, and corrections.
- Accountant may initiate/manage exceptional early closure with mandatory audit. Owner has read/view/audit access only. Investor cannot self-initiate exceptional closure.
- A financial closure must wait until required unresolved positions are resolved. A previously closed Investor may return without overwriting old history.
- Current Investor Principal Claim = valid initial/additional Investor principal − confirmed principal settlements paid to the Investor − confirmed Investor Loss Recognition + principal claim increases from linked corrections − principal claim decreases from linked corrections. Owner Loss Contributions are coverage of a principal shortfall; they credit Available Fund but do not increase this Investor Principal Claim.
- Current Investor Principal Claim must reconcile to Gross Fund Ledger Balance + Currently Used / Locked Principal − outstanding Owner Contribution Return Payables − Buyer Principal Refund Reserves. Equivalently, it equals Available Fund + Currently Used / Locked Principal − any combined reserve amount not covered by the Gross Fund Ledger Balance. Once all Vehicle principal and other required positions are resolved and Owner Contribution Return Payables and Buyer Refund Payables are actually paid, Principal Settlement Payable equals Available Fund and must also equal the reconciled Current Investor Principal Claim. A mismatch is unresolved and blocks closure.
- Each actual Principal Settlement payment to the Investor is recorded as a Fund Ledger debit and reduces Available Fund and Current Investor Principal Claim by that same amount. Recording a payable or changing Settlement status alone does not count as payment.
- Outstanding Eligible Investor Profit = sum across the Investor's deals of the greater of zero or (corrected current Eligible Investor Profit Entitlement − confirmed valid Investor Profit Payments). Any Additional Payable representing this same positive difference is a label for that amount, not an extra amount.
- Investor Settlement Payable = Principal Settlement Payable + Outstanding Eligible Investor Profit. Recovery Obligations owed by the Investor, Owner Contribution Return Payables, Buyer Refund Payables, receivables, Locked Principal, or any other unresolved correction position must be settled and recorded separately before final closure; no automatic netting is permitted.
- Settlement may be Closed only when Locked Principal, unresolved Vehicle principal, Buyer receivables and Buyer Refund Payables, unpaid required Profit positions, pending Owner Loss Contributions, Additional Payables, Recovery / Adjustment Obligations, Owner Contribution Return Payables, and other correction positions are resolved, the principal reconciliation matches, and all payable settlement amounts have actually been recorded as paid.

## Other current scope

- Labour is a Tenant-scoped managed entity with basic details, Active/Inactive state, manual payment amount/date, optional note, and payment history. Labour has no login. Fixed salary, payroll, attendance, Vehicle or Work-Type assignment, scheduling, and worker-level Vehicle costing are outside current scope.
- Media User manages only approved public Vehicle information, images, publication status, and public-facing availability. Media cannot change the core Vehicle lifecycle or access internal finance.
- The current expense model is Vehicle-based. Dedicated Cash Account, Bank Account, cash-versus-bank ledger, and General Garage Expense modules are outside current scope.
- GST/Tax/Invoice information is supported where applicable but is not mandatory for every current transaction; a full tax/accounting suite is outside current scope.
- Investor, Fund, Vehicle, Tenant, Sale, Buyer Payment, Profit, Settlement, Labour Payment, user assignment, configuration, correction, and audit history must remain traceable. No silent financial deletion or historical rewrite.
- Tenant consolidation is rare Back Office/controlled administration work, not a normal operational action. Preserve old Tenant identity and historical financial truth.

## Loss-settlement closure

For a fully collected loss Sale, the Investor's allocated loss and every Owner's actual contribution must be recorded before the Vehicle's principal position is considered resolved for Investor Settlement. Final Investor closure still requires all other relevant positions to be resolved.
