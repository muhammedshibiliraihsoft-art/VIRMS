# 05 — Vehicle / Investor / Finance Workflow

Status: DRAFT V2 — Investment and Stock Vehicle finance source after approval

Authorization follows 02, source relationships follow 04, Company accounting follows 09, and Garage work follows 10. Every financial state is scoped to one Company; Branch is attribution, never Investor ownership.

## Vehicle responsibility boundary for Garage work

Vehicle Management owns one stable Company-wide Vehicle identity. The same Vehicle UUID may move from funded Stock activity to external-customer Garage service without a second Vehicle record. The Vehicle-side Investor responsibility has only ACTIVE and ENDED states. An authorized end operation records effective time, actor and reason; it preserves the relationship and all historical Fund, cost, Sale, receipt, Profit, reconciliation and settlement records. Ending the responsibility creates no payment, Fund event or settlement, and existing unresolved obligations remain with Investment/Accounting until their normal authorized resolution.

Garage work is financially scoped per Job/event, not inferred solely from the Vehicle's historical type or Investor. A Job on an active Investor-funded Stock Vehicle does not itself debit Investor Fund. After Investor responsibility is ENDED, a later external-customer Job on that same Vehicle UUID has no automatic former-Investor Fund, principal, Profit, reconciliation or settlement impact. The Garage workflow does not implement Investor Fund, Profit, reconciliation, reassignment or Exit/Settlement.

### Vehicle create field mapping for the Garage workflow

Vehicle registration, model and Branch are operator-entered attributes on the existing Vehicle aggregate. The existing `person` value maps only to Job service-contact Name/Phone context; it does not assert Vehicle ownership or payer identity. Investor responsibility is a separate authorized operation, not part of Vehicle creation. Purchase is outside the Garage workflow. Vehicle status and total cost are derived from their owning business sources and are not manually editable. Any React field placement must preserve the approved page composition and use the existing form contract.

## 1. Funding and approved Vehicle costs

An Investor has one auditable principal Fund relationship within a Company and may fund multiple Stock Vehicles in that Company. Each funded Stock Vehicle has exactly one Investor. Initial and additional capital are separate confirmed Fund credits. Approved Investor-funded purchase/Vehicle Expense records have a corresponding Fund use and cannot silently exceed Available Investor Fund. A Company may supply actual Running Capital for an approved shortfall; record its exact Vehicle-linked amount in Company finances, separate from Investor principal and Profit. The entire valid approved purchase/work cost contributes once to consolidated Vehicle cost even when funding sources differ. Before spending, validate Company, Branch, Investor lifecycle, Vehicle, approval and funding source; commit related financial events atomically.

The Fund balance, Available position, committed/locked position and cumulative recovered history are derived from authoritative valid movements, not manually editable totals. Gross Investor Fund Ledger Balance is the net valid Investor principal credits and debits before outstanding Buyer principal-refund reserves. For an Investor-only-funded position, `Available Investor Fund = max(0, Gross Investor Fund Ledger Balance − outstanding Investor-backed Buyer Principal Refund Reserve)`; reserve only actual Fund money held, and keep an uncovered refund payable open without inventing liquidity. Currently Used/Locked Investor Principal sums nonnegative outstanding Investor-funded Vehicle principal. Redeployment of actual recovered Investor money reduces what is Available but does not erase historical recovery; cumulative Recovered Principal is never added again to Available Fund. A calculated or pending recovery, suggested Company contribution or unreceived Buyer amount is not cash. No negative Investor Available Fund is permitted in normal operations. For a mixed-funded normal positive Vehicle, use the confirmed full-collection reconciliation in section 3; the Investor-only formula is not itself a complete mixed-funding rule.

## 2. Stock Vehicle, Sale and actual Buyer collection

The Stock Vehicle follows Purchased → In Work → Ready → Listed → Sold. Garage work in one or more Branches may contribute approved Vehicle costs through linked records without creating a second Vehicle. Labour Payment to a worker is not automatically Vehicle cost; an approved Vehicle/Job Labour Expense is a distinct cost event.

One normal authoritative Sale for a Stock Vehicle records a Company-consistent Buyer and agreed Sale Price. Buyer phone is required but is not a unique key. Sale confirmation marks Sold and retains applicable positive-share configuration, but collection remains Pending, Partially Received or Fully Received. `Total Vehicle Cost = Purchase Cost + valid approved Vehicle and Job Expenses`, counted once. Positive-result arithmetic may use `Agreed Sale Price − Total Vehicle Cost`; a negative calculation is a review signal, not an automatically approved Loss allocation.

Each Buyer Payment is an individual actual receipt. For an ordinary Sale, `Remaining Receivable = Agreed Sale Price − valid confirmed Buyer Payments`. Every new payment must satisfy `0 < Payment Amount <= current Remaining Receivable`. Reject excess or concurrent overcollection; do not convert it to Buyer credit, automatic refund, Profit or Investor Fund. A pending Buyer amount creates no Principal Recovery, settled Company Share or final Vehicle settlement.

If an authorized Sale correction reduces price below Buyer cash already received, preserve every original Buyer Payment. Define Net Valid Confirmed Buyer Payments before subtracting actual refunds. `Buyer Refund Payable = max(0, Net Valid Confirmed Buyer Payments − Actual Confirmed Buyer Refund Payments − Current Corrected Agreed Sale Price)`. `Sale Applied Buyer Amount = Net Valid Confirmed Buyer Payments − Actual Confirmed Buyer Refund Payments − outstanding Buyer Refund Payable`. `Remaining Receivable = corrected Agreed Sale Price − Sale Applied Buyer Amount`, nonnegative. Recompute one current payable after each valid price correction or actual refund; adjust its linked history rather than creating duplicates. Pending refundable money is not Sale revenue, collected Profit or freely available recovered principal.

An actual Buyer refund is separately confirmed, satisfies `0 < Refund Amount <= current Buyer Refund Payable`, and reduces that payable only when posted. Its principal-backed and other components reconcile to the exact returned amount. For an Investor-only-funded position, a Buyer Principal Refund Reserve is the unpaid refundable amount previously credited as Investor Principal Recovery but no longer applied to the corrected Sale; an actual refund of that part records an Investor Fund debit and reduces the reserve and payable. The original receipt and each correction, refund and reserve adjustment remain traceable. An unpaid refund blocks new affected positive-Profit payout eligibility and final Vehicle/Investor financial resolution. A later valid Sale correction may reduce or release an unused reserve but creates no new receipt or Fund credit. On a mixed-funded Vehicle, linked corrections reconcile actual Investor principal recovery, actual Company Running Capital recovery and positive result against the corrected Sale and actual refund; no refund may be assumed to belong wholly to Investor funds or counted as a second receipt.

## 3. Principal recovery, Running Capital and positive allocation

Actual Buyer collection and principal/Profit classification remain distinct. The existing principal-first rule applies to Investor-financed Stock Vehicle principal when Investor funding is the only principal source: recover no more than current outstanding valid Investor-funded principal from an actual receipt; only an actually collected excess is collected positive result. Record an Investor Fund credit once for actual Investor Principal Recovery. A later authorized cost or Sale correction can reclassify the *same* confirmed receipt through linked adjustments without a duplicate Buyer receipt or Fund effect. A principal-backed pending Buyer refund reserves only Fund money held; its actual refund records the linked Fund debit.

When Company Running Capital also funded a normal positive Vehicle, show Investor-funded cost, exact actual Company contribution, actual Buyer cash and the distinct capital recoveries. After full Buyer Sale collection, first reconcile actual Investor principal, then identify and recover/reconcile the exact actual Vehicle-linked Company Running Capital as capital, then determine the remaining actual positive economic result for Investor/Company allocation. Total approved Vehicle cost includes each cost once regardless of its funding source; do not subtract capital recovery as a second cost or count it again as Profit, Company Income, Company Share or Garage Revenue. A provisional position during partial collection is not final Vehicle settlement. Suggestions may be edited where permitted, but only authorized confirmation records actual capital recovery and final settlement. There is no assumed interest, premium, guaranteed return or automatic Loss waterfall.

For a positive completed result, use the Investor's applicable effective agreement percentage, valid within 0%–100% inclusive, to calculate the suggested Investor Share with fixed-precision decimal and `ROUND_HALF_UP` monetary posting. Company Share is the positive result remainder under the approved allocation, so the two final posted shares exactly equal the approved positive result. The current business standard may be configured as 33% Investor Share; it is versioned, never hard-coded or forced on every Company or agreement. No Company 65% or 67% constant exists. Platform Back Office alone changes the protected agreement/rate configuration with specific backend permission and audit; Accountant uses its effective value for authorized operations. Snapshot agreement, result and confirmed adjustments. Company Share enters 09 and is never a direct Owner deal payout. Editing a suggested payment does not rewrite the agreement; any authorized difference is an explicit, audited adjustment.

## 4. Deal-level Profit, Monthly Interim Payout and period reconciliation

Ordinary deal-level Investor Profit has Calculated, Eligible and confirmed Paid positions. Full agreed Buyer Sale Price collection, Principal Recovery and resolution of affected refund obligations gate eligible deal-level payout. The Investor may receive that eligible payout while Active and before Exit. Only an actual authorized Accountant/Operations confirmation creates a payment. A new ordinary eligible Profit Payment is positive and cannot exceed current outstanding eligible entitlement; concurrent/retried postings cannot overpay. The current corrected entitlement and actual net retained prior payments determine the outstanding amount; a merely open recovery obligation is not a received recovery.

Monthly Interim Payout is a separate advance against eventual Investor Profit. Each Investor has a configurable monthly rate and cycle day; a protected rate change is administered by Platform Back Office, while Accountant uses the approved effective rate. If day 30 or 31 does not exist in a month, use the final calendar day; other unavailable configured days follow the same rule. No daily proration. Use the eligible principal position for that cycle; top-up, allowed withdrawal and rate change during an active cycle take effect in the next cycle. The system may calculate Due/Suggested and issue a reminder, but Paid requires an actual confirmed payment. Authorized delay, skip, changed actual payment date and correction are recorded without fabricating payments. An interim payment can precede deal-level earned Profit; therefore it is never posted as an ordinary eligible deal-level Profit Payment merely to reuse that transaction cap.

At each configured six-month or annual Investor reconciliation, derive relevant earned Investor Profit and identify actual confirmed interim payments and any other already retained confirmed Profit payment affecting the same entitlement. Present one remaining payable or Company-recoverable position for human review and confirmation. Do not count a payment twice or automatically finalize because a period ended. A recoverable can be reduced by a separately recorded direct Investor repayment or authorized partial/multiple adjustments against future Profit. Example: ₹20,000 recoverable less one confirmed ₹10,000 future adjustment leaves ₹10,000. An open suggestion or reminder does not reduce it.

**BUSINESS DECISION REQUIRED:** Define the precise eligible-principal base and permitted withdrawal limits; define which deals fall in a reconciliation period and how ordinary deal-level payouts coexist with periodic payout so the same earned Profit is never distributed twice.

**Superseded by approved additions dated 2026-11-19:** The fixed monthly Interim amount replaces a rate/eligible-principal formula; ordinary principal withdrawals are limited to Available Fund; Vehicle results belong to the Sale-date period; and confirmed deal-level payments are counted Paid once in that same period. The actual Interim-payment and persisted reconciliation workflows remain implementation gaps.

## 5. Manual Loss and corrections

A negative arithmetic result does not automatically allocate Loss to Investor, Company or Owners and does not create a Fund movement or settlement. Authorized users record the confirmed Loss, manual Investor impact, manual Company impact, reason, corrections and actual financial actions. No separate automatic Loss engine, percentage-based Loss split, mandatory Owner contribution formula or automatic Running-Capital Loss recovery applies to new V2 activity. **BUSINESS DECISION REQUIRED:** Define exact approval/confirmation authority and how a manually confirmed Loss affects the Investor principal claim, Company finances and closure; do not substitute the old formula.

**Superseded by approved additions dated 2026-11-19:** Same-Company Company-level Accountant confirms each Vehicle Loss with reason; approved future-Profit offsets and the special Exit rule are recorded in the later additions below. Their implementation remains incomplete.

An authorized correction preserves original Sale, cost, receipt, Fund, interim, Profit, Running Capital and distribution events. Record linked actor, time, reason, old/new values, applicable effective snapshots and current reconciled position. Before payout, adjust the current entitlement without erasing the earlier calculation. After payout, `Net Retained Profit Payment = confirmed valid Profit Payments − actual confirmed recoveries against those payment correction chains`; an open recovery obligation is not actual recovery. Reconcile a corrected entitlement against net retained payment to one current Additional Payable or Recovery/Adjustment Obligation, rather than stacking duplicates. An actual Profit Recovery Receipt is positive and no greater than its current outstanding Recovery/Adjustment Obligation; partial receipt is permitted and reduces the obligation only when confirmed. Interim and recoverable corrections likewise reconcile actual events, not merely suggestions. Cross-category netting is forbidden except an explicitly confirmed future-Profit adjustment against an Investor recoverable. A previously closed position remains in history if a later correction opens a new obligation.

Critical purchase, expense, Sale, Buyer payment/refund, Fund recovery, interim payment, Profit payment/recovery, correction and settlement writes are atomic, bounded by their current authoritative position, Company/Branch authorized, concurrency-safe and duplicate-safe. Reject invalid excess values without automatic clamping or a fictitious balancing item.

## Automation levels in Investor and Vehicle finance

Under 01's five-level model, backend-derived Fund/Vehicle cost, Buyer receivable, paid/open balances and configured positive-share arithmetic are Level 1 calculations. Investor/Company positive-share amounts, Running Capital recovery, interim amount and reconciliation payable/recoverable adjustments are Level 2 suggestions where editing is permitted. Buyer outstanding, monthly due, period reconciliation due and unresolved settlement are Level 3 reminders/statuses. Actual Buyer receipt/refund, Company contribution/recovery, Investor/interim/Profit payment, recoverable repayment or future-Profit adjustment, reconciliation and final settlement are Level 4 specifically authorized human-confirmed events. Loss, unusual funding correction and exceptional settlement are Level 5 manual decisions with reason and audit; they still require authorized confirmation for any actual event. None of Levels 1–3 creates a payment, approved Loss or final settlement.

## 6. Exit and final Investor settlement

Normal Exit requires Terms & Conditions acceptance and three months' notice. Active → Exit Requested → Settlement Pending → Closed preserves history. Exit Requested prevents a new Stock Vehicle purchase from that Investor Fund; approved already-funded work, Sales and collection may continue. Accountant may manage exceptional early closure with audit; Owner may inspect only. Notice expiry never releases committed capital.

Settlement reviews the Investor's Company-level position across Branches: Fund, available/locked principal, completed Vehicles, Buyer receivables/refunds, actual interim payments, earned/paid Profit, recoverable, Running Capital links and corrections. No status change itself pays money. Close only after the relevant Vehicles are fully collected and financially resolved, principal reconciles, open payable/recoverable/refund/correction positions are resolved, and actual required payments are recorded. A Principal Settlement payment is positive, no more than its current payable and actually available Fund, and debits the Fund once. Partial payment is allowed.

Eligible normal Investor Profit paid while Active remains valid history and cannot be paid again. At *final Investor closure*, resolve blocking positions, settle remaining returnable Investor principal to zero first, then pay any remaining eligible Investor Profit; both must be actual confirmed payments. The final-closure order does not delay ordinary eligible deal-level Profit Payment until Exit. Company Running Capital is a separate Company position and must not be included in the Investor principal payout.

## Approved Business Decision Additions

### ADDITION — Fixed Monthly Interim amount, configuration and reconciliation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Each Investor may have an individually configured fixed INR amount for Monthly Interim. It is not a percentage of principal; amounts such as ₹500, ₹1,000, ₹2,000, or ₹3,000 are examples only, not defaults.
- The amount is available in the Investor create/edit workflow. Only that Investor's same-Company Company-level Accountant may set or edit it; Branch Accountants and Platform Back Office may not.
- An edit made during an active cycle takes effect in the next cycle. The configured amount is not proof that money was paid: Paid continues to require an actual authorized, confirmed payment.
- Monthly Interim remains an advance against eventual Investor Profit. Confirmed payments are reconciled against the Investor's actual earned Profit under the existing reconciliation process. Any excess remains an explicit recoverable position; later adjustment must use the approved repayment or explicitly recorded future-Profit adjustment, never silent netting.

**Scope**
- Investment-owned per-Investor Monthly Interim configuration, authorized edits, cycle amount, confirmed payment, and Investor Profit reconciliation.

**Preserve unchanged**
- Monthly cycle-day and no-proration rules; separation of Interim advances from ordinary deal-level Profit Payments; actual payment confirmation; configurable Investor agreement/share rules; and existing recovery/correction history. This addition does not resolve active-cycle principal withdrawal limits or which deals and ordinary payouts are included in six-month/annual reconciliation.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Monthly Interim rate and eligible-principal formula/basis. Only the amount basis is resolved. Permitted active-cycle principal withdrawals and reconciliation-period deal inclusion/ordinary payout interaction remain BUSINESS DECISION REQUIRED.
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Platform Back Office-only administration of Monthly Interim rate, only for the fixed amount field. All other protected Investor agreement/rate configuration remains under its existing authority.

**Implementation impact**
- Keep effective Investor amount configuration separate from immutable confirmed payment events; authorize writes using the Company-level Accountant grant; retain cycle-effective history and reconcile actual payments without changing Company Accounting's cash/ledger ownership.

### ADDITION — Interim advances appear as Paid in final Investor Profit reconciliation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- At six-month or annual Investor Profit reconciliation, include every actual confirmed Monthly Interim advance as `Paid` against the Investor's Profit entitlement.
- Present earned Investor Profit separately from Paid amounts. An Interim advance does not reduce or rewrite the earned-Profit figure; it is shown as money already paid toward that Profit.
- Count only confirmed actual payments. The monthly configured amount, a Due/Suggested value, reminder, skipped cycle, or unpaid amount is not Paid.
- Example for presentation: if the relevant earned Profit is ₹10,000 and confirmed Interim advances are ₹6,000, show Profit ₹10,000, Interim Paid ₹6,000, and a provisional remaining ₹4,000 before any other applicable confirmed Profit payments or unresolved period-allocation rules.
- If confirmed advances exceed earned Profit, retain the excess as the existing explicit Company-recoverable position. Do not silently net it against principal or another category, and do not create a second payment when displaying the advance as Paid.

**Scope**
- Investor Profit account and six-month/annual reconciliation presentation of confirmed Monthly Interim payments.

**Preserve unchanged**
- Fixed per-Investor monthly amount, Company-level Accountant edit permission, actual-payment confirmation, immutable payment history, and separation of Investor principal, Investor Profit, and Company cash. Which deals belong to each period and how ordinary deal-level Profit payouts interact with periodic reconciliation remain unresolved.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether a confirmed Interim advance is counted and displayed as Paid against Investor Profit in the final reconciliation. This does not decide period deal inclusion or the interaction with ordinary deal-level Profit payments.

**Implementation impact**
- Reconciliation must reference the confirmed Interim payment as Paid while preserving the gross earned-Profit calculation. Keep payment posting, reconciliation display, and any later payable/recoverable confirmation as distinct actions; do not duplicate economic events.

## Phase 5 Approved Business Decision Additions — Fund, Vehicle, Investor periods and Exit

### ADDITION — Pooled Fund, Branch-attributed credits, FIFO use and Company-only pooled spending

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Investor Fund is pooled at Company level, while each credit requires a source Branch. Branch attribution is provenance and authority scope, not a Branch sub-Fund.
- Branch Accountant records/views their authorized Branch credits only and cannot see consolidated balance or other Branch credits. Company-level Accountant may view across same-Company Branches.
- Company-level Accountant alone may use pooled Fund for Vehicle purchase. Each Stock Vehicle is linked to one Investor's Fund responsibility; additional Company Running Capital may fund the approved shortfall.
- Spend Fund credits FIFO by effective credit time and UUID; retain per-credit use lineage. Do not split a later Vehicle result by credit lot.

**Scope**
- Investment Fund credits, use, Branch read scope and Vehicle purchase funding.

**Preserve unchanged**
- Fund balance is derived; Company Running Capital is separately linked; Vehicle purchase cost counts once. Sale, Profit and settlement are not part of this posting.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: any Phase 5 question whether Fund is Branch-specific, whether Branch accountants can view pooled amounts or spend cross-Branch Fund. It does not grant general cross-Branch access.

**Implementation impact**
- Persist credit source Branch and FIFO use allocations, lock credit lots, and enforce Company Accountant authority before posting a purchase.

### ADDITION — Profit belongs to Vehicle result and Sale period, not credit lot

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Investor Profit is derived from the actual result of the Vehicle(s) funded for that Investor under the applicable agreement percentage. Do not attribute profit by separate Fund-credit tranche.
- Attribute the Vehicle result to the Investor calendar period containing the Sale date. If final Buyer cash arrives later, keep the result in the Sale period and restate that period with audit history after collection completes.
- An eligible later Fund top-up does not reassign or split the result of a Vehicle already sold in the period.

**Scope**
- Future Investment-owned Vehicle result and Investor Profit period calculation; not Phase 5 posting or cash receipt.

**Preserve unchanged**
- Investor Profit remains separate from Company Profit, actual Buyer receipt, Investor Fund principal and Company Running Capital. A report or re-statement does not pay money.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: that a profit from a Vehicle bought with a later top-up must automatically move to the next Investor period. Vehicle Sale date controls period membership; no credit-lot split applies.

**Implementation impact**
- Future Profit service must use immutable Vehicle Sale/result links and append an audited restatement when a later actual collection completes.

### ADDITION — Each Investor has a configurable calendar and historical periods are preserved

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Each Investor has a separate Profit calendar. Same-Company Company-level Accountant may set its start date and duration in months/years; six months is the default only.
- Calendar changes apply at the start of the next incomplete period. Reject a change whose proposed boundary falls inside a completed calculation; do not overlap or rewrite completed periods.
- Preserve prior reconciliation and payment records unchanged; new settings apply prospectively.

**Scope**
- Future Investor period versioning and reconciliation boundaries.

**Preserve unchanged**
- Company Profit periods remain calendar H1/H2/year; they do not govern Investor Profit. Investor calendar reports do not close/reset periods or settle automatically.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: a fixed/rolling-only Investor period calendar, only for configurable start and period duration. Existing reconciliations/payments remain immutable.

**Implementation impact**
- Append period-setting versions and bind each completed reconciliation to the version used; reject retroactive overlap under transaction lock.

### ADDITION — Monthly Interim configuration and paid history

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Each Investor may have an individually configured fixed Monthly Interim amount, edited only by the same-Company Company-level Accountant. The effective date is recorded; when changed mid-month, the old amount applies for that month and the new amount starts the next month without daily proration.
- Interim configuration or calculated amount is only a suggestion/setting; actual payment is manually confirmed and recorded as a separate immutable payment.
- At Investor Profit reconciliation, display actual confirmed Interim amounts as Paid without reducing earned Profit or creating a duplicate payment.

**Scope**
- Investor settings, future Interim payments and Investor Profit reconciliation.

**Preserve unchanged**
- Branch Accountant and Platform Back Office cannot edit this amount. Investor Profit formula and settlement remain outside Phase 5.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: a rate-based Interim calculation or Platform Back Office-only edit for this fixed amount. It does not authorize a payment or resolve other Investor agreement configuration.

**Implementation impact**
- Store versioned amount configuration separately from payment; future reconciliation references the actual payment UUID.

### ADDITION — Exit extension, cancellation and new-funding gate

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Normal Exit notice is three months. Same-Company Company-level Accountant may extend its deadline by recording a new date and reason without a fixed maximum.
- Investor may request Exit cancellation at any time; same-Company Company-level Accountant must approve before reactivation.
- Once Exit is requested, reject new Investor Fund credits and new Vehicle purchase funding. The Exit may remain pending while unresolved positions exist; do not auto-close or auto-settle when a date passes.
- If Investment turns OFF after an Exit began, no new credits/purchases may be opened; authorized Company-level Accountant may continue only the already-started Exit steps approved by policy. Actual money movement also requires Accounting ON.

**Scope**
- Investment Exit lifecycle and module-OFF handling.

**Preserve unchanged**
- No status change itself creates payment, fund return, vehicle sale or release of allocated principal. Full Exit calculation and settlement is future Investment scope.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: a fixed non-extendable notice deadline, automatic cancellation/reactivation, or Fund credit allowed after Exit starts. Other module-OFF rules remain unchanged.

**Implementation impact**
- Record request, extension and approval as immutable audited actions; gate new root credits/purchases by Investor state and module revisions.

### ADDITION — Vehicle registration reuse and Branch movement

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Normalized registration must be unique among active Vehicles in the same Company. A Sold Vehicle stays active by default; reusing its registration requires an explicit manual deactivation.
- Deactivation is permitted only after the Vehicle is Sold and has no open Job, financial or settlement position. Preserve Vehicle UUID and all history.
- Branch Accountant may deactivate only an eligible Vehicle in their authorized Branch; Company-level Accountant may do so in any Branch in the same Company.
- Only Company-level Accountant may move a Vehicle between Branches. Append movement history and retain the same Vehicle identity and old Job/finance Branch attribution.

**Scope**
- Vehicle Management registration, deactivation and movement.

**Preserve unchanged**
- Branch selection is not authorization; Accounting cross-Branch permission does not grant Vehicle movement permission. Sale status and open-position proof must come from their authoritative modules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether Sold automatically frees a registration or Branch users can move a Vehicle across Branches. The actual Sold/Job/finance prerequisites remain dependent on those modules.

**Implementation impact**
- Use an active-only Company registration constraint and immutable movement records; keep deactivation unavailable until Garage/Sales/Finance providers can prove the guards.

### ADDITION — Vehicle loss offset and final Exit settlement

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Calculate an Investor's share of a Vehicle loss using that Vehicle's applicable agreement snapshot. Do not debit ordinary Fund credits for the loss.
- Maintain loss separately; offset from that Investor's current/future Vehicle Profit with a distinct audited record. Keep gross Profit intact and show the offset and net payable separately. Any unpaid loss remains open for future Profit.
- Loss offset confirmation may be performed by Branch Accountant only for their authorized Branch; Company-level Accountant may confirm across same-Company Branches.
- At Exit, only when no future profitable Vehicle position remains, reduce remaining loss from eligible Available Fund first. Do not make Fund negative. Collect any residual directly from Investor; Exit remains open until received. Record the actual receipt in Cash/Bank and link it to the loss obligation without creating Company Income/Profit.
- Exit spanning Branches is calculated/closed by Company-level Accountant only.

**Scope**
- Future Vehicle Profit/Loss and Investor Exit settlement; not Phase 5 Fund/Vehicle foundation.

**Preserve unchanged**
- Fund credit history is immutable; Loss offset is not a cash movement; direct repayment is. No Company Running Capital balancing item is invented.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: whether a Vehicle loss affects Investor share, whether it may be netted against other Vehicle Profit, how residual loss carries, and how Exit handles an uncovered residual. It supersedes earlier text forbidding an Investor Fund debit specifically at Exit after all future-profit positions end.

**Implementation impact**
- Later design must use agreement snapshots, append-only Loss/offset events, current-position concurrency checks, and Accounting receipt links.

### ADDITION — Active Investor principal return follows available source credit

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Before Exit, return only unallocated Available Fund; an amount committed to an unresolved Vehicle is locked and cannot be returned.
- Branch Accountant may return only available credits from their authorized source Branch. Company-level Accountant may return eligible credit from any same-Company Branch.
- Fund is still pooled Company-wide; Branch credit provenance and permission do not create isolated Branch Funds.

**Scope**
- Future active Investor principal return.

**Preserve unchanged**
- Vehicle Profit, Exit settlement and actual Cash/Bank return remain separate. No credit return is a Company Expense/Profit event.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: permitted active-cycle principal withdrawal and the owning Branch for its return. Return source must be linked; Fund committed to a Vehicle is excluded.

**Implementation impact**
- Return API accepts source credit lot(s), locks their remaining Available amount, and posts one linked Accounting cash outflow atomically.

### ADDITION — Funding and source modules are independently gated

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- Investor profile/settings require Investment ON; Vehicle create/move/deactivate requires Vehicle Management ON; actual Fund credit requires Investment + Accounting ON; a Fund/Running Capital Vehicle purchase requires Investment + Vehicle Management + Accounting ON.
- Before Exit, new Fund credit or Vehicle funding is denied after Exit is requested. A previously begun Exit may continue only its authorized settlement actions if Investment turns OFF; actual cash move requires Accounting ON.

**Scope**
- Investment/Vehicle/Accounting operation gates.

**Preserve unchanged**
- Every API still checks same-Company membership, role, Branch and immutable module-state revision. OFF never deletes history or authorizes new activity.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: which Phase 5 modules must be enabled for each listed action and how an already-started Exit is handled after Investment OFF. Other module OFF behavior is unchanged.

**Implementation impact**
- Serialize writes with Company module revisions and distinguish new root records from an approved pre-existing Exit obligation.

### ADDITION — Complete seller-payment timing is still unresolved

**Status:** BUSINESS DECISION REQUIRED<br>
**Effective documentation state:** Current V2 blocker

**Rule**
- No Vehicle Purchase may be implemented until the Company decides whether a Purchase can be recorded before full seller payment. The current Accounting schema has no Supplier Payable or partial-purchase payment application workflow.
- Preferred safe option for the first slice is to require the entire approved purchase price actually paid and record one linked Accounting outflow in the same atomic operation. If partial/deferred payment is required, design and approve a payable/application lifecycle before coding.

**Scope**
- Vehicle Purchase creation and linked Accounting capital outflow.

**Preserve unchanged**
- Purchase cost is counted once; funding-source allocations equal full purchase cost; actual payment is not Company Expense/Profit.

**Supersedes**
- None. This is an explicit unresolved implementation gate, not an approved business decision.

**Implementation impact**
- Q39 blocks purchase API/model behavior; continue only independent profile/Fund-credit/Vehicle-identity slices until resolved.


### ADDITION — Company Running Capital shortfall and Investor Loss offset are separate

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- If Investor Fund is insufficient for an approved Vehicle cost/loss shortfall, the Company may fund the exact shortfall as Vehicle-linked recoverable Running Capital. Do not debit new Investor Fund or allow negative Investor Fund.
- Recover that Company Running Capital first only from actual proceeds of the same Vehicle; a calculated amount or pending Sale is not received money.
- Separately record the Investor's loss share and offset it against that Investor's current/future Vehicle Profit, including Profit from another Vehicle. Keep gross Profit, loss offset, Company Running Capital recovery, and net payable separately visible.
- Do not count a single real cash movement twice or silently merge the Company recovery and Investor Profit-offset obligations.

**Scope**
- Future Vehicle cost/loss funding and Sale proceeds/reconciliation.

**Preserve unchanged**
- Company Running Capital is not Investor principal or Company Expense/Profit. Actual cash is recorded only when received/paid. Phase 5 does not implement this loss/Sale workflow.

**Supersedes**
- SUPERSEDES the immediately preceding Phase 5 addition phrase saying an Investor loss never creates a Company Running Capital shortfall record. The previously approved Vehicle-linked Company funding rule remains distinct from the Investor's Profit offset.

**Implementation impact**
- Future code requires separate immutable linked records and a verified no-double-recovery reconciliation across same-Vehicle Company capital and Investor loss offsets.

### ADDITION — Vehicle purchase may precede full seller payment

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle purchase may be recorded before the seller has received the full purchase price.
- The unpaid amount remains a payable linked to that Vehicle purchase. It may be settled through one or more actual partial payments; total valid payments cannot exceed the approved purchase price.
- Record the full approved purchase cost and its approved Investor Fund/Company Running Capital allocations once. Do not treat the unpaid amount as cash paid or create a Cash/Bank movement until an actual payment occurs.
- Seller payments and the payable do not create Company Income, Expense, or Profit.

**Scope**
- Phase 5 Vehicle Purchase creation, seller payable, funding allocation, and actual seller payments.

**Preserve unchanged**
- Company-level Accountant remains the only role that may use pooled Investor Fund for Vehicle funding. Purchase cost is counted once; Accounting remains the source of actual Cash/Bank movements. Existing correction, Company isolation, Branch, module-state, audit, and idempotency rules remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the immediately preceding Q39 addition that left full payment versus payable/partial payment undecided. Option B is approved. This does not approve a general supplier-payables module or change other purchase permissions.

**Implementation impact**
- Implement a purchase-linked outstanding payable and append-only partial-payment applications, with one Accounting outflow/movement per actual installment and no cash effect for the unpaid balance.

### ADDITION — Zero-advance Vehicle purchase is permitted

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Vehicle purchase may be recorded with ₹0 paid to the seller. The full approved purchase cost is then outstanding seller payable.
- Show a clear warning that no seller advance has been paid. The warning does not block a valid zero-advance purchase or count as a payment.

**Scope**
- Phase 5 Vehicle purchase entry, payable display, and its existing React purchase flow when integrated.

**Preserve unchanged**
- The full purchase cost and funding allocations remain separate from actual Cash/Bank payment; approved UI composition and routes remain protected.

**Supersedes**
- None; this clarifies the approved purchase-before-full-payment rule.

**Implementation impact**
- Permit zero initial payment and derive the warning from zero actual seller payments. Reuse the existing purchase UI pattern when integration becomes possible.

### ADDITION — Existing seller payable may be paid after Investment or Vehicle Management OFF

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- If a Vehicle purchase and its seller payable were created before Investment or Vehicle Management became OFF, authorized actual installments against that existing payable may continue while Accounting is ON.
- OFF still prevents a new Vehicle purchase or new Investor Fund-use allocation. This exception creates no new purchase, funding source, or payable.
- If Accounting is OFF, this addition grants no seller-payment exception.

**Scope**
- Settlement of a pre-existing Phase 5 Vehicle purchase payable only.

**Preserve unchanged**
- Same-Company and Branch authorization, immutable module-state history, actual cash ownership by Accounting, audit, idempotency, and transaction protection remain required. Other module-OFF rules are unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Phase 5 architecture's unresolved exception for pre-OFF obligations, only for seller-payable installments while Accounting is ON. It does not authorize new purchase/funding while OFF.

**Implementation impact**
- Distinguish an existing payable installment from a new purchase/funding command. Recheck the purchase's pre-OFF origin and Accounting ON revision under the Company lock before posting actual cash.

### ADDITION — Vehicle purchase requires seller name

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Require the seller's name on a Vehicle Purchase. Seller phone number may be recorded but is optional.
- Show the seller identity with the purchase payable and its partial payments.

**Scope**
- Phase 5 Vehicle Purchase, seller payable, and seller-payment history.

**Preserve unchanged**
- Seller details do not create Vehicle ownership, Investor responsibility, or Garage Job customer identity. No general vendor directory is included.

**Supersedes**
- None; this adds the seller fields needed to identify a Vehicle purchase payable.

**Implementation impact**
- Add required `seller_name` and optional `seller_phone` to the purchase contract and preserve them with its immutable financial history.

### ADDITION — Seller installment actor follows purchase Branch

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may record a seller-payable installment only for a purchase attributed to their authorized Branch.
- Company-level Accountant may record installments for any Branch within the same Company.

**Scope**
- Actual payments against existing Vehicle Purchase seller payables.

**Preserve unchanged**
- Purchase creation and pooled Fund-use remain Company-level Accountant actions. Company/Tenant boundaries, Accounting module requirement, audit, idempotency, and append-only payment history remain.

**Supersedes**
- None; no seller-installment actor rule was previously specified.

**Implementation impact**
- Validate the purchase's original Branch against server-side role assignments for each installment; never authorize from selected Branch context alone.

### ADDITION — Lender finance and EMI are outside Phase 5

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 5 supports the approved seller payable and actual partial seller payments only. It does not include third-party lender financing, loan-principal tracking, EMI schedules/payments, interest or finance-fee calculation, or finance-specific tags.
- Do not treat the seller payable as a lender loan or infer a loan/interest event from it or from a negative Cash/Bank balance.

**Scope**
- Phase 5 Vehicle Purchase and deferred seller payment.

**Preserve unchanged**
- The full Vehicle purchase cost is counted once; seller payable is derived from that cost and valid linked actual seller payments; Accounting records each real Cash/Bank movement once. Existing later Vehicle deactivation guards and other financial rules remain unchanged.

**Supersedes**
- None; lender finance and EMI were not an approved Phase 5 workflow. This addition records their explicit exclusion from this phase.

**Implementation impact**
- Do not add lender, loan, EMI, interest, or finance-tag models/APIs/UI to Phase 5. A future request requires separately approved scope and accounting treatment.

### ADDITION — Purchase funding allocations are recorded at acquisition

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- At Vehicle Purchase creation, record the complete approved Investor Fund and Company Running Capital source allocations, totaling the full purchase cost, even when the seller has received ₹0 or only a partial payment.
- The Investor Fund allocation is committed/locked against the purchase at that time. Seller payable records only the remaining amount actually owed to the seller; it is not an additional purchase funding source.
- Source allocation does not create an Accounting Cash/Bank movement or mean the seller has been paid. Record a Cash/Bank movement only when an actual seller installment is paid.

**Scope**
- Phase 5 Vehicle Purchase, Investor Fund use, Company Running Capital allocation, and seller payable.

**Preserve unchanged**
- Purchase cost is recorded once; source allocations sum to the full cost; seller payable is derived from purchase cost less valid actual installments; each actual payment has one Accounting cash effect. No Income, Expense, Profit, lender finance, or EMI event is created by allocation.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: when full Investor Fund and Company Running Capital allocations take effect if seller cash is unpaid. They are recorded at purchase creation; the separate cash movement remains tied to actual payment.

**Implementation impact**
- Serialize purchase creation with Fund availability, append full source allocations atomically, and calculate seller payable independently from the committed funding allocations and actual Cash/Bank movements.

### ADDITION — Purchase cost correction requires an actual seller refund

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If a corrected Vehicle purchase cost would be lower than cumulative actual seller installments, block the correction until the seller has actually returned the excess and that receipt is recorded in Accounting.
- A promise to refund or a seller credit is not an actual refund and does not satisfy this condition.
- Preserve the original purchase, installments, and Cash/Bank events; record any accepted correction as audited history.

**Scope**
- Phase 5 Vehicle purchase cost corrections and seller payable settlement.

**Preserve unchanged**
- Full Investor Fund and Company Running Capital allocations are recorded at purchase creation; seller payable and actual Cash/Bank movement remain separate. Lender finance and EMI remain outside Phase 5.

**Supersedes**
- None; this addition resolves the previously unspecified correction case where actual seller installments exceed the corrected purchase cost.

**Implementation impact**
- Recheck cumulative valid installments inside the correction transaction. Require a same-Company Accounting record of the actual refund before accepting the correction; preserve allocation and payment history.

### ADDITION — Purchase correction reduces funding sources proportionally

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an accepted purchase-cost correction reduces the purchase total, reduce Investor Fund and Company Running Capital allocations in the same proportion as the recorded funding-source split.
- Preserve the original allocations and append audited correction/reallocation history. Within the Investor Fund portion, retain the existing approved Fund-credit FIFO attribution rule.

**Scope**
- Purchase-cost corrections, Investor Fund use, and Company Running Capital allocations for a Vehicle Purchase.

**Preserve unchanged**
- Full sources equal purchase cost; a correction below actual seller installments still requires the actual excess refund to be recorded in Accounting first. No source allocation itself creates a cash movement.

**Supersedes**
- None; this resolves which funding sources are reduced after an approved cost correction.

**Implementation impact**
- Append compensating allocation records that preserve the recorded source proportions and exact corrected total. A sub-paisa rounding rule for proportional adjustments remains to be specified before implementation.

### ADDITION — Proportional purchase-source corrections balance to the exact paise

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Calculate proportional Investor Fund and Company Running Capital adjustments at high precision, then round each amount to two decimals with `ROUND_HALF_UP`.
- Reconcile any residual one paise at a time so source adjustments sum exactly to the total correction. Give the residual to the source most under-allocated (or subtract from the most over-allocated); recompute after each paise. Break equal priorities in the fixed order Investor Fund first, Company Running Capital second.

**Scope**
- Downward Vehicle Purchase cost corrections and the matching source-allocation adjustments.

**Preserve unchanged**
- Source reductions follow the recorded proportion; Fund-lot attribution remains FIFO; source histories remain append-only.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: paise rounding for proportional purchase-source adjustments.

**Implementation impact**
- Use fixed-precision decimal intermediates and deterministic balanced-paise reconciliation; final source adjustments must equal the accepted cost reduction exactly.

### ADDITION — Company-wide approval mode governs Investor and Vehicle automation

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The Company-wide Automation Approval setting in 01 governs consequential Investor/Vehicle automation. ON requires per-action approval by an authorized role; OFF allows only already-approved module automation to execute under existing domain permissions.
- Show calculation/source details in a compact responsive popup beside Approve for calculation-based or materially consequential automated actions.

**Scope**
- Investor and Vehicle workflow automation and its in-context approval/details controls.

**Preserve unchanged**
- Investor profit, Loss, Fund, Vehicle and settlement boundaries; calculation-only results do not create financial events. Existing role, Company/Branch and module-state checks still apply.

**Supersedes**
- None; this references the new Company-wide approval mode without changing existing Investor/Vehicle automation levels.

**Implementation impact**
- Route approval decisions through the owning domain service and preserve the approver, policy version, calculation inputs/result and execution outcome in audit history.

### ADDITION — Investor and Vehicle pending automation survives mode changes

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Turning Company-wide Automation Approval OFF changes only future Investor/Vehicle automation. Existing pending actions remain pending until separately approved or cancelled in their owning workflow.

**Scope**
- Pending Investor and Vehicle automation actions.

**Preserve unchanged**
- The appropriate Investor/Vehicle action permission and all Company/Branch, module, audit and financial safeguards still apply.

**Supersedes**
- None; this applies the global pending-action rule to these modules.

**Implementation impact**
- Do not batch-execute or discard pending purchase, allocation or other domain actions when the mode changes.

### ADDITION — Automation OFF does not approve new Investor/Vehicle workflows

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- With Company-wide Automation Approval OFF, only Investor/Vehicle automations explicitly approved for automatic execution may skip per-action confirmation. Manual Investor/Vehicle operations and unapproved automation still require authorized human confirmation.

**Scope**
- Consequential automated actions in Investor and Vehicle workflows.

**Preserve unchanged**
- No unsupported Profit, Loss, Fund, purchase, correction, or settlement behavior becomes automated. Real cash events still require actual source evidence and Accounting ownership.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: per-action Level 4 confirmation for Investor/Vehicle actions, only for an explicitly approved automation while the Company mode is OFF.

**Implementation impact**
- Add explicit per-workflow automation authorization and enforce it in the owning service; the Company toggle alone cannot authorize the action.

### ADDITION — Seller refund and purchase correction are manual linked entries

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An Accountant manually records an actual seller refund and manually records the related Vehicle Purchase cost correction; both records must link to the same Purchase.
- Do not automatically create a refund or silently change purchase cost. Preserve the actual refund, original payment, correction, and source-allocation history.

**Scope**
- Vehicle Purchase seller refund and cost correction after actual installments.

**Preserve unchanged**
- A cost correction below cumulative actual installments still requires the full excess to have actually been refunded and recorded in Accounting first. Fund and Running Capital sources reduce proportionally with the approved balanced-paise rule.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether a seller refund and the related Purchase correction are automated or manually entered and linked.

**Implementation impact**
- Provide separate manually initiated, typed records linked to one Purchase; derive the displayed outstanding payable from the valid linked purchase, installment, and refund history. Keep actual cash movement in Accounting only.

### ADDITION — Remember the selected seller-payment Cash/Bank account

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- On the first seller-payment entry, the Accountant selects the Cash/Bank account. On the next entry, show the previously selected account as the starting choice; the Accountant can change it for the current entry.
- Do not impose Cash or Bank as a fixed default. The selected account for each actual payment remains part of that payment's Accounting record.

**Scope**
- The Cash/Bank choice when entering actual seller payments for Vehicle Purchases.

**Preserve unchanged**
- Company/Branch authorization, active account validation, actual cash-movement ownership, immutable confirmed payment history, and the separately approved seller-payable rules. This choice does not authorize silently rewriting an earlier confirmed payment.

**Supersedes**
- None.

**Implementation impact**
- Prefill the next entry from the last chosen account and permit selection of another authorized account. Preference scope (per Accountant or Company), persistence and when a choice becomes the remembered value remain UNRESOLVED; do not infer them.

### ADDITION — Seller-payment account preference is per Accountant

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Remember the last selected seller-payment Cash/Bank account separately for each Accountant. Another Accountant's selection must not replace it.

**Scope**
- Seller-payment account prefill for each Accountant within the current Company.

**Preserve unchanged**
- The first selection, ability to change the account for a payment, Company/Branch permissions, account validation and immutable confirmed financial history remain as previously approved.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: the per-Accountant versus Company-wide scope of the preceding seller-payment account preference addition. Persistence mechanism and the point at which a choice is remembered remain open.

**Implementation impact**
- Scope any remembered preference by authenticated Accountant and Company; validate any prefilled account against current server-side authorization and availability.

### ADDITION — Remember account after a successful seller payment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Remember the account from the Accountant's last successfully saved seller payment. Selecting an account in a form that is closed without saving does not change the remembered account.

**Scope**
- Per-Accountant seller-payment account preference within the Company.

**Preserve unchanged**
- The Accountant may change the account for each payment; existing authorization, validation and confirmed financial history remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: when the preceding seller-payment account selection becomes the remembered value. The technical persistence mechanism remains open.

**Implementation impact**
- Update the preference only after an authoritative successful payment; an unsaved or failed form must not replace it. Define retry/recovery and preference persistence in the implementation architecture.

### ADDITION — No automatic import of demo Investor and Vehicle data

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Do not automatically import demo/mock Investor or Vehicle records into the real database. Use actual records for the real backend integration.

**Scope**
- Phase 5 Investor and Vehicle data integration and the transition from prototype data.

**Preserve unchanged**
- Existing real database records, Company/Branch isolation, stable identities, and historical financial records. This decision does not authorize deletion or alteration of existing records.

**Supersedes**
- None.

**Implementation impact**
- Do not run automatic mock import or treat demo records as real business data. Any separate historical import requires its own reviewed source and mapping.

### ADDITION — Seller refund and purchase correction authority

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record an actual seller refund only for a Purchase in their authorized Branch; a Company-level Accountant may do so within the same Company.
- Purchase cost correction is restricted to the same-Company Company-level Accountant.

**Scope**
- Authorized seller refund entry and Vehicle Purchase cost correction.

**Preserve unchanged**
- Refund and correction are separate manual linked actions; an actual refund must precede a correction below net actual seller payments. Company, Branch, module, accounting source, audit and immutable history safeguards continue.

**Supersedes**
- None; this resolves the previously unspecified actor scope for the two actions.

**Implementation impact**
- Enforce distinct server-side action permissions and Purchase Branch scope; do not derive authorization from a selected Branch or a frontend control.

### ADDITION — Fund Credit form captures the actual account and source reference

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The existing Fund Credit form must provide an explicit Cash/Bank account selection and a required operator-supplied source reference before a real Fund credit is submitted.
- The submitted account and reference must map to the existing typed Fund Credit and Accounting capital-inflow contract.

**Scope**
- Phase 5 Fund Credit entry in the existing React form and its backend request contract.

**Preserve unchanged**
- Accounting remains the owner of the actual Cash/Bank movement. A Fund credit is Company capital, not Company Income, Expense, or Profit; Investment and Accounting module, Company, Branch, role, audit, transaction, and idempotency checks remain in force.

**Supersedes**
- None; this approves the minimum existing-form inputs needed to submit a real Fund credit and does not change accounting or source-of-truth rules.

**Implementation impact**
- Add the two inputs to the existing form without redesigning its page or route, and send the selected account UUID and required reference through the existing typed API fields. Do not use demo defaults or silently omit either value.

### ADDITION — Sale records the actual Sale date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The existing Sale form must allow the Accountant to enter the date the Vehicle was actually sold, including a past date when the Sale is recorded later.
- Use that entered Sale date for business-period attribution. Preserve the separate server-recorded timestamp as audit history; do not replace the Sale date with the entry date.

**Scope**
- The minimal authoritative Stock Vehicle Sale record and the existing Sale form in Phase 5.

**Preserve unchanged**
- Confirmed Sale remains the authoritative Sold source. Buyer phone remains required. Sale confirmation remains separate from Buyer collection, Investor Profit calculation, and settlement.

**Supersedes**
- None; this clarifies which date the minimal Sale record must capture and does not define a broader Sales workflow.

**Implementation impact**
- Add one Sale-date field to the existing form and persist it as the Sale's effective business date alongside the immutable server `recorded_at` timestamp. Do not force the effective date to equal the save date.

### ADDITION — Stock Vehicle Buyer Receipt requires an external reference

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Each actual Stock Vehicle Buyer Receipt must include a required operator-supplied external reference, such as a bank transaction ID or Cash voucher number.
- Store the reference with the actual Buyer Receipt and its linked Accounting event. The reference is traceability data; the server-generated Buyer Receipt UUID and typed Sale relationship remain record identity.

**Scope**
- Actual Buyer Receipts for Stock Vehicle Sales, including the approved Phase 5 Collection form and typed backend command.

**Preserve unchanged**
- Accounting owns the one actual Cash/Bank movement. A Buyer Receipt remains separate from Company Income and Sale price; partial receipts and the existing over-receipt limit remain unchanged. The Garage-specific Company-wide reference uniqueness rule remains separate.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the existing Collection form needs an operator-supplied external reference for Stock Vehicle Buyer Receipts. This does not supersede the separate Buyer Receipt account-selection approval.

**Implementation impact**
- Add a required reference input to the approved existing Collection form and pass it to the typed Sale Receipt API and Accounting `source_reference`. Do not use it as entity identity. Whether duplicate references are rejected, and at what scope, remains BUSINESS DECISION REQUIRED.

### ADDITION — Buyer Receipt reference is unique per Company and Cash/Bank account

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Reject a Stock Vehicle Buyer Receipt when the same external reference has already been used for another Buyer Receipt in the same Company and the same named Cash/Bank account, regardless of Branch.
- The same reference text may be used in a different Cash/Bank account within the same Company.

**Scope**
- Duplicate detection for actual Stock Vehicle Buyer Receipts and their selected Cash/Bank account.

**Preserve unchanged**
- The external reference is required traceability data, not record identity. The server-generated receipt UUID, typed Sale relationship, and idempotency key retain their separate roles. Garage receipt reference uniqueness remains governed by its existing Company-wide rule.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether duplicate Stock Vehicle Buyer Receipt references are rejected and the scope of that check. Exact comparison normalization remains a technical contract to lock.

**Implementation impact**
- Enforce the Company + Cash/Bank account uniqueness rule across Branches for the typed Buyer Receipt source. Do not apply it to all Accounting event types or other receipt domains. Lock trimming/case comparison before schema migration.

### ADDITION — Buyer Receipt reference matching trims spaces and ignores case

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When checking duplicate Stock Vehicle Buyer Receipt references, ignore leading/trailing whitespace and letter case. For example, `BANK-37`, `bank-37`, and ` BANK-37 ` are the same reference for duplicate detection within the same Company and Cash/Bank account.

**Scope**
- Duplicate matching for Stock Vehicle Buyer Receipt references only.

**Preserve unchanged**
- The Company + Cash/Bank account uniqueness scope across Branches; the same normalized reference may still be used in a different account. The stored external reference remains traceability data, not receipt identity.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: case and surrounding-whitespace normalization for the Buyer Receipt reference uniqueness rule.

**Implementation impact**
- Validate and enforce uniqueness using a trimmed, case-insensitive comparison key within the typed Buyer Receipt source. Do not change matching rules for other Accounting references or Garage receipts.

### ADDITION — Fund Credit reference is unique per Company and Cash/Bank account

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Reject a new Investor Fund Credit when its operator-supplied external reference matches an existing Fund Credit in the same Company and same named Cash/Bank account, regardless of Branch. Ignore leading/trailing whitespace and letter case when comparing references.
- The same reference may be used for a Fund Credit received into a different Cash/Bank account in that Company.

**Scope**
- Duplicate detection for actual Investor Fund Credits and their selected Cash/Bank account.

**Preserve unchanged**
- Each Fund Credit remains an immutable Investor principal record with Branch provenance and one Accounting-owned actual Cash/Bank movement. The external reference is traceability, not record identity. Do not broaden this rule to Investor returns or all Accounting events.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the required Fund Credit external reference must be unique and the scope/comparison rule for that check.

**Implementation impact**
- Enforce trimmed, case-insensitive uniqueness by Company and actual Cash/Bank account across Branches. The current Fund Credit row has no account FK; the code-level schema must expose an enforceable account key that is constrained to match its one linked Accounting movement. Do not create an independent account source of truth. Whether one real transfer can fund multiple Investor credits remains BUSINESS DECISION REQUIRED.

### ADDITION — One actual transfer is for one Investor Fund Credit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Record one actual Cash/Bank transfer as a Fund Credit for one Investor only. Do not divide one transfer across multiple Investors. If multiple Investors are credited, record a separate actual transfer for each Investor.

**Scope**
- Investor Fund Credit creation and the corresponding Accounting capital-inflow event and Cash/Bank movement.

**Preserve unchanged**
- Each Fund Credit remains an immutable principal record with Branch provenance and one linked Accounting movement. Multiple distinct transfers may be recorded for the same Investor. The reference remains traceability data and the existing Company + Cash/Bank account duplicate rule remains in force.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether one actual transfer may fund multiple Investors' Fund Credits, as left open by Q65.

**Implementation impact**
- Require a separate typed Fund Credit and Accounting source event per actual transfer; do not model a single transfer split across several Investors. Preserve the existing atomic write and idempotency protections.

### ADDITION — Fund Credit uses the actual money-received date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Record the date money was actually received as the Fund Credit effective date. It may be a past date when the entry is made late; a future date is not allowed.

**Scope**
- Investor Fund Credit, linked Accounting capital-inflow event and its Cash/Bank movement.

**Preserve unchanged**
- Keep the actual system entry/creation timestamp for audit. The effective receipt date does not replace or backdate the creation timestamp.

**Supersedes**
- None; this resolves the previously unspecified Fund Credit late-entry and future-date policy.

**Implementation impact**
- Apply the same actual-receipt effective date to the Fund Credit and its linked Accounting movement. Backdating changes historical as-of views and the effective-date-based Investor calendar. Timezone and time-of-day representation remain technical API details to lock.

### ADDITION — Correcting Fund Credit Investor attribution

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If an actual Fund transfer was received but its Fund Credit was assigned to the wrong Investor, keep the original credit and its history, and append an audited correction moving its Fund amount to the correct Investor.
- The correction must not create a second Cash/Bank receipt or movement; the actual transfer remains recorded once.

**Scope**
- A confirmed Fund Credit with valid actual cash receipt but incorrect Investor attribution.

**Preserve unchanged**
- Fund Credit and Accounting events remain append-only. Keep the original Branch provenance, one actual movement, and the rule that one transfer funds one Investor credit.

**Supersedes**
- None; the correction treatment for a valid transfer attributed to the wrong Investor was not previously specified.

**Implementation impact**
- Represent the correction as a typed append-only attribution record linked to the original Fund Credit, not as an edit to the original credit or its Accounting source link. Correction authority, partial corrections and effective-date treatment remain BUSINESS DECISION REQUIRED.

### ADDITION — Authority for Fund Credit Investor-attribution correction

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may correct only a Fund Credit from their authorized source Branch. Company-level Accountant may correct a Fund Credit from any Branch in the same Company.

**Scope**
- The audited append-only correction of a valid actual transfer attributed to the wrong Investor.

**Preserve unchanged**
- The original Branch provenance and actual Cash/Bank movement remain unchanged. This is only an Investment correction permission and does not grant cross-Branch access to other modules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: the role allowed to authorize this Fund Credit attribution correction.

**Implementation impact**
- Authorize using the original Fund Credit's source Branch and same-Company role grants. Keep the correction actor, reason and old/new Investor attribution in append-only audit history. Partial correction and effective-date rules remain unresolved.

### ADDITION — Whole-credit rule for wrong-Investor correction

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When correcting a valid Fund Credit attributed to the wrong Investor, move the entire original credit amount to the correct Investor. Do not divide that credit between Investors.

**Scope**
- Amount moved by the audited, append-only wrong-Investor attribution correction.

**Preserve unchanged**
- Preserve the original Fund Credit, actual Cash/Bank movement, Branch provenance, correction-authority scope, and Company-wide Fund total.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the wrong-Investor attribution correction may be partial, as left open by Q68 and Q69. Q66's one-transfer/one-Investor rule remains the basis.

**Implementation impact**
- Enforce correction amount equal to the full original Fund Credit and reject partial reallocation. The correction effective date remains a separate unresolved decision.

### ADDITION — Wrong-Investor correction uses the actual receipt date

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Apply a wrong-Investor Fund Credit correction from the original money-received date and recalculate the affected historical Investor calculations with audit history.
- Keep the original actual receipt and Cash/Bank movement unchanged.

**Scope**
- Effective dating and historical Investor-period recalculation for an append-only full-credit attribution correction.

**Preserve unchanged**
- The original credit, actual cash movement, creation timestamps, and prior calculation versions remain traceable. Investor Profit remains independent from Company Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether the correction uses the original receipt date or its later entry date, as left open by Q68-Q70.

**Implementation impact**
- Recompute affected Investor calculations against the original effective date while preserving prior versions. No historical actual payment is silently changed; how already-paid/settled amounts are handled remains BUSINESS DECISION REQUIRED.

### ADDITION — Apply historical Investor Profit differences as separate adjustments

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- After an audited historical Investor Profit restatement, preserve the old calculation and actual payment and record the revised difference separately.
- Add an unpaid amount to a later Investor Profit amount. Deduct an overpaid amount from a later Investor Profit amount.

**Scope**
- Investor Profit calculation and future settlement amount after a Fund Credit attribution correction restates a completed period.

**Preserve unchanged**
- Past actual payment/Cash/Bank movement remains immutable. The adjustment is not itself a cash event, Company Income, Expense, or Company Profit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: how already-paid Investor Profit is adjusted when its historical calculation changes.

**Implementation impact**
- Show the restated amount and adjustment as separate audited lines, then apply the net adjustment to a later Profit amount. Actual payout still requires a distinct authorized payment. Handling an overpaid balance when no later Profit is available or Exit occurs remains BUSINESS DECISION REQUIRED.

### ADDITION — Flexible Exit for unoffset historical Profit overpayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an Investor exits with a historical Profit overpayment still unoffset, the Company may choose for that case either to collect it before closing Exit or to close Exit without collecting it.

**Scope**
- Overpayment adjustment remaining after historical Investor Profit restatement and after future Profit offsets.

**Preserve unchanged**
- Actual prior payments and Cash/Bank movements remain immutable. No Fund debit, automatic repayment, or Company Income is created. This does not change normal Vehicle Loss or principal settlement rules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Exit must stay open until a restatement overpayment is fully collected.

**Implementation impact**
- Record the selected case outcome and audit trail. The authorized role and whether a balance left unpaid is waived or remains recoverable after Exit remain BUSINESS DECISION REQUIRED.

### ADDITION — Case-by-case disposition after Exit without full recovery

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Exit is completed without collecting the full historical Profit overpayment, either keep the unpaid adjustment open for later collection or waive it with a reason. Select the outcome for the individual case.

**Scope**
- Post-Exit handling of an unoffset overpayment from an audited Investor Profit restatement.

**Preserve unchanged**
- Keep the original and revised calculation versions, prior actual payments and Exit decision auditable. Do not auto-debit Fund, create a cash movement, or treat waiver as Company Income/Expense.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an unpaid adjustment after Exit remains open or is waived, as left open by Q73.

**Implementation impact**
- Record the selected disposition; waiver requires a reason. The actor/approval authority remains BUSINESS DECISION REQUIRED.

### ADDITION — Authority to choose post-Exit overpayment disposition

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may choose open-balance or waiver only for an adjustment from their authorized Branch. Company-level Accountant may choose for any Branch in the same Company.

**Scope**
- Post-Exit disposition of an unoffset historical Investor Profit restatement overpayment.

**Preserve unchanged**
- A Branch Accountant's action does not finalize an Exit spanning Branches. Existing Company-level Accountant authority for cross-Branch Exit remains. Other modules' Branch permissions are unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which role may choose the open-balance or waiver disposition after Exit.

**Implementation impact**
- Enforce source-Branch and same-Company authorization on the server. Require a reason for waiver. Preserve Q74 history and the selected disposition.

### ADDITION — Role scope for collecting an open adjustment after Exit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may record actual repayment only for an open post-Exit adjustment from their authorized source Branch. Company-level Accountant may record repayment for any Branch in the same Company.

**Scope**
- Actual repayment against a restatement overpayment retained open after Investor Exit.

**Preserve unchanged**
- The actual original Profit payment and Exit history remain immutable. No repayment is recorded before receipt; the permission does not authorize a Branch Accountant to finalize cross-Branch Exit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which role may record actual repayment of an open post-Exit adjustment.

**Implementation impact**
- Link the actual received amount to the open adjustment and validate source Branch scope. Accounting event classification and typed link remain to be specified; no generic Income target may be assumed.

### ADDITION — actual repayment of post-Exit Profit overpayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When the Investor repays an open historical Profit overpayment after Exit, record the money actually received as a Cash/Bank Receipt linked to that open adjustment.
- Reduce the open overpayment by the amount actually received. Do not create Company Income or Company Profit from the repayment.

**Scope**
- Post-Exit repayment workflow for historical Investor Profit restatement overpayments.

**Preserve unchanged**
- Preserve the prior Profit calculation, actual previous payment, restatement adjustment, Exit and disposition history, and Q76's role/Branch limits. Actual receipt is recorded only after money arrives.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: the business classification of an actual post-Exit repayment, specifically whether it is Company Income/Profit. Q76's authority decision remains unchanged.

**Implementation impact**
- Keep the repayment as a typed actual Receipt linked to the adjustment; do not route it through an Income target. The exact typed source-link/API design remains open.

### ADDITION — partial and repeated post-Exit repayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An Investor may repay an open post-Exit historical Profit overpayment in partial amounts and in multiple actual repayments.
- After each receipt, reduce the open balance by the amount actually received; keep any remaining amount open for later repayment.

**Scope**
- Post-Exit repayment workflow for historical Investor Profit restatement overpayments.

**Preserve unchanged**
- Q76 actor and Branch scope, Q77 Receipt classification, original Profit/payment/adjustment history, and actual-receipt-only movement creation remain in force.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an open post-Exit adjustment requires one full repayment or may be repaid partially and repeatedly.

**Implementation impact**
- Support multiple typed actual Receipts against one open adjustment and derive its residual. Do not assume behavior for receipts above the remaining amount; that case remains unresolved.

### ADDITION — edit a saved repayment entry with audit retained

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- An authorized Accountant may edit a saved post-Exit overpayment repayment entry. The ordinary workflow shows the latest value only; earlier values do not need to appear in that view.
- Retain the original and all corrections in backend audit history. The Accountant may add a note.
- Editing the repayment entry does not alter the actual Cash/Bank Receipt or movement.

**Scope**
- Post-Exit Investor Profit overpayment repayment entry and its normal list/detail/edit presentation.

**Preserve unchanged**
- Q76 actor scope, Q77 actual Receipt/no-Company-Income rule, Q78 partial/multiple repayments, and actual receipt-only movement creation remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether previously saved repayment-entry values must remain visible in the normal workflow after editing.

**Implementation impact**
- Provide an edit action that appends an audited correction while rendering the current value. Keep actual cash-event details immutable; excess-receipt treatment remains unresolved.

### ADDITION — choose disposition for repayment above the open balance

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an Investor actually repays more than the remaining open historical Profit overpayment, the authorized Accountant chooses case by case to keep the excess open as an amount due back to the Investor or record a separate actual refund after paying it back.
- Keep the original Receipt at the full amount actually received. Do not mark a refund complete before the actual cash outflow; do not create Company Income/Profit from the excess.

**Scope**
- Investor-facing repayment correction/edit workflow and disposition of an excess repayment after Exit.

**Preserve unchanged**
- Q76 role scope, Q77 Receipt classification, Q78 partial/multiple receipts, and Q79 backend audit retention with current-value normal views remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: how to disposition an actual repayment above the open amount.

**Implementation impact**
- Present both case-specific dispositions in the authorized edit flow, preserve each decision in audit history, and link any actual refund as a separate cash outflow. Typed source/API details remain open.

### ADDITION — partial refund of an excess Investor repayment

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If the Accountant keeps excess repayment open as due back to the Investor, they may return it in partial and multiple actual refunds.
- Record every actual refund separately. Reduce the due-back amount by each amount actually paid; keep any remainder open.

**Scope**
- Post-Exit repayment correction flow for refunding excess Cash/Bank receipts to an Investor.

**Preserve unchanged**
- Q76-Q80 actor scope, original Receipt, case-specific due-back/refund choice, audit history, and actual-movement-only rules remain in force.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether an excess due-back amount may be returned through partial/multiple refunds.

**Implementation impact**
- Show the current due-back balance and each separately recorded actual refund; do not mark a partial refund as full settlement.

### ADDITION — full Purchase/Sale amounts with partial settlement and refunds

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Record the complete Purchase cost and agreed Sale price on the Vehicle's source transaction before settlement is complete; neither amount depends on cash paid or received.
- Allow zero, partial and multiple seller installments and Buyer Receipts against their respective existing payable/receivable. Every installment must be positive and at most the current outstanding amount. A smaller installment is valid and leaves the remaining amount open.
- Allow actual Buyer and seller refunds in partial/multiple installments against the source-specific refund obligation. Record each actual cash event separately. For a Purchase cost correction that needs a seller refund, the correction remains blocked until the full required excess refund has actually been received and recorded.
- Use the same pattern for another module only when its authoritative total, typed obligation and permissions have already been defined.

**Scope**
- Phase 5 Vehicle Purchase, Sale, seller payment/refund, Buyer receipt/refund and their compact balance/status UI.

**Preserve unchanged**
- Q43-Q81 purchase/funding/receipt/refund/edit decisions, Company/Branch authorization, the actual-cash-only rule, and one economic event per movement remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: partial/multiple refund installments and the validity of a below-outstanding installment for Vehicle Purchase/Sale.

**Implementation impact**
- Derive `outstanding = source obligation − valid linked settlement events` using each source's approved correction/refund rules. Reject excess installments; accept lower partial amounts and retain the open balance.

### ADDITION — successful Sale-form Save confirms the actual Sale

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When an authorized Accountant successfully saves the existing Sale form for an actual completed Vehicle sale, the Sale is confirmed and the Vehicle is considered Sold.
- Buyer collection remains independent and may be Pending, Partially Received, or Fully Received after the Sale is confirmed.

**Scope**
- Phase 5's minimal authoritative Stock Vehicle Sale flow and its existing Sale form.

**Preserve unchanged**
- Keep the confirmed Sale as the Sold source; preserve the required Buyer details, agreed price, actual Sale date, typed Buyer Receipt links, and the rule that open or unknown Garage, finance, or Investor settlement positions block Vehicle deactivation.

**Supersedes**
- None; this clarifies that successful Save of the existing Sale form is the confirmation action and does not change the separate collection workflow.

**Implementation impact**
- The successful Sale create command persists a confirmed Sale. Do not add a second Confirm button or treat full Buyer collection as the Sold transition.

### ADDITION — Branch permission for actual Buyer refunds

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record an actual Buyer refund only for a Sale in their authorized Branch.
- A Company-level Accountant may record an actual Buyer refund for any Branch within the same Company.

**Scope**
- Actual partial or full Cash/Bank refunds against a Stock Vehicle Sale's Buyer refund obligation.

**Preserve unchanged**
- Preserve the Sale's original Company and Branch, actual-cash-only recording, typed Sale/refund relationship, current outstanding cap, and Q82's partial/multiple refund rules. No generic cross-Branch permission is added.

**Supersedes**
- None; this defines the role boundary for Buyer refunds, which was not set by the separate seller-refund decision.

**Implementation impact**
- Validate the linked Sale's Company and Branch on the server for each refund; retain the Branch Accountant limit and the Company-level Accountant's same-Company cross-Branch scope.

### ADDITION — Branch scope for confirming a Sale and recording Buyer Receipts

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may create/confirm a Stock Vehicle Sale and record actual Buyer Receipts only for a Sale in their authorized Branch.
- A Company-level Accountant may create/confirm the Sale and record its Buyer Receipts for any Branch in the same Company.

**Scope**
- The minimal Phase 5 Sale form and actual Buyer Receipt command.

**Preserve unchanged**
- Successful Sale-form Save confirms the actual Sale; Buyer collection remains separate. Each Receipt is a separate actual Cash/Bank event within the current outstanding cap. Q84 Buyer refund scope and all non-Sales permissions remain unchanged.

**Supersedes**
- None; this defines the actor Branch scope for Sale confirmation and Buyer Receipts without changing the separately approved Buyer refund authority.

**Implementation impact**
- Check the authenticated actor's same-Company role and authorized Branch against the Sale's server-owned Company/Branch. Do not rely on a submitted Branch selector for authority.

### ADDITION — block Buyer Receipts while Vehicle Management is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Vehicle Management is OFF, do not record a Buyer Receipt against any existing Sale, even when Accounting remains ON.
- The existing Sale stays recorded and its unpaid balance remains open. Do not create an Accounting Receipt, Cash/Bank movement, or other financial event for the blocked collection.

**Scope**
- Buyer collection against a Sale that was confirmed before Vehicle Management was turned OFF.

**Preserve unchanged**
- Sale create/confirmation remains blocked while Vehicle Management is OFF. Buyer Receipt recording requires both Vehicle Management and Accounting ON. The separately approved pre-OFF Seller payable installment exception remains unchanged.

**Supersedes**
- None; this defines Buyer Receipt module-OFF behavior and does not change the Seller payable exception.

**Implementation impact**
- Recheck Vehicle Management and Accounting state at Receipt write time; reject the command without changing the Sale balance or posting an Accounting cash event if either required module is OFF.

### ADDITION — block Seller refunds while Vehicle Management is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Vehicle Management is OFF, do not record a Seller refund against a Purchase that already exists, even when Accounting is ON.
- Leave the Purchase and its refund/correction position unchanged until Vehicle Management is ON; no Accounting event or Cash/Bank movement is created by the blocked command.

**Scope**
- Actual Seller refunds linked to pre-OFF Vehicle Purchases.

**Preserve unchanged**
- The separately approved exception to pay a pre-OFF Seller payable remains valid when Accounting is ON. This decision does not allow a new Purchase or Purchase correction while Vehicle Management is OFF.

**Supersedes**
- None; this defines the module-OFF rule for Seller refunds without changing the Seller payable exception.

**Implementation impact**
- Require Vehicle Management and Accounting ON for the linked Seller refund command; reject without changing balances or posting a cash movement otherwise.

### ADDITION — block Buyer refunds while Vehicle Management is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Vehicle Management is OFF, do not record or pay a Buyer refund against an existing Sale even when Accounting is ON.
- Keep the Sale and its refund obligation unchanged until Vehicle Management is ON; create no Accounting event or Cash/Bank movement for the blocked refund.

**Scope**
- Actual partial or full Buyer refunds against Stock Vehicle Sales recorded before Vehicle Management was turned OFF.

**Preserve unchanged**
- Require both Vehicle Management and Accounting ON for an actual Buyer refund. Preserve the distinct Q86 Buyer Receipt and Q87 Seller refund rules, and the pre-OFF Seller payable installment exception.

**Supersedes**
- None; this defines the module-OFF rule for Buyer refunds.

**Implementation impact**
- Recheck both required module states at refund write time; reject without changing the Sale/refund balance or posting a cash movement if either is OFF.

### ADDITION — block Purchase cost corrections while Vehicle Management is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Do not correct the cost of an existing Vehicle Purchase while Vehicle Management is OFF, even if Accounting is ON. Wait until Vehicle Management is ON.

**Scope**
- The previously approved, audited Company-level Accountant correction to an existing Vehicle Purchase cost.

**Preserve unchanged**
- Preserve the original Purchase, funding allocations, seller installments, and audit history while blocked. The pre-OFF Seller payable installment exception remains unchanged; this does not allow a new Purchase or Purchase cost correction while Vehicle Management is OFF.

**Supersedes**
- None; this explicitly confirms that a correction to an existing Purchase also waits for Vehicle Management to be ON.

**Implementation impact**
- Recheck Vehicle Management state before applying the cost correction; reject without changing the Purchase or its source allocations while OFF.

### ADDITION — block wrong-Investor Fund Credit correction while Investment is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Do not apply a wrong-Investor attribution correction to an existing Fund Credit while Investment is OFF, even if Accounting is ON. Wait until Investment is ON.

**Scope**
- The previously approved full-credit, audited attribution correction from the wrong Investor to the correct Investor.

**Preserve unchanged**
- Preserve the original Fund Credit and its Branch provenance, audit history, and one actual Cash/Bank movement. The correction changes Investor attribution only; it does not add or change cash.

**Supersedes**
- None; this clarifies module-OFF handling for the existing wrong-Investor correction rule.

**Implementation impact**
- Recheck Investment state before applying the attribution correction; reject without changing the Fund Credit or its original Accounting link while OFF.

### ADDITION — block standalone unused-principal returns while Investment is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If Investment is OFF, do not return unused Available Fund principal for an Investor who has no Exit/settlement already started before the OFF transition. Wait until Investment is ON.

**Scope**
- Standalone principal return from Investor Fund that is not part of a preexisting Exit workflow.

**Preserve unchanged**
- Keep the original Fund credits and Available Fund amount unchanged while blocked. The approved completion of an Exit started before Investment OFF remains allowed under its existing rule; actual cash movement still requires Accounting ON.

**Supersedes**
- None; this sets the Investment module-OFF rule for unused-principal returns outside an existing Exit.

**Implementation impact**
- Reject the standalone return without changing Fund allocations or Cash/Bank movements while Investment is OFF; preserve the distinct pre-OFF Exit settlement path.

### ADDITION — cap actual Seller refunds at net paid amount

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- For each Vehicle Purchase, cumulative confirmed Seller refunds cannot exceed confirmed actual Seller installments minus actual Seller refunds already received.
- Reject any refund that exceeds the remaining amount actually paid to the Seller.

**Scope**
- Manually recorded actual Seller refunds linked to a Vehicle Purchase.

**Preserve unchanged**
- Refund and Purchase cost correction are separate manual actions linked to the same Purchase; a refund does not itself change Purchase cost.
- Keep each confirmed installment and Accounting movement immutable. The refund is actual money received, not Company Income or assumed supplier credit.

**Supersedes**
- None; this sets the approved refund cap without changing the existing Purchase-correction rules.

**Implementation impact**
- Recalculate the linked Purchase's net confirmed installments and prior confirmed refunds while holding the Purchase mutation lock; post only if the requested refund is within the remaining cap.

### ADDITION — block Purchase cost correction while Investment is OFF

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Do not apply an existing Vehicle Purchase cost correction while Investment is OFF when that correction changes Investor Fund use/allocation. Wait until Investment is ON.

**Scope**
- Manual audited Purchase cost corrections and corresponding Investor Fund-use/allocation adjustments.

**Preserve unchanged**
- Preserve the existing Q89 rule that Vehicle Management must be ON for a Purchase cost correction.
- Preserve the original Purchase, allocations, Seller payments, refunds, and Cash/Bank movements while blocked. An actual Seller refund is separate and remains subject to its own module gate and Q92 net-paid cap.

**Supersedes**
- None; this resolves only the Investment module-OFF condition for Purchase cost corrections.

**Implementation impact**
- Check Investment state/revision inside the atomic correction command and reject without changing Purchase cost, allocations, payable, or history while Investment is OFF.

### ADDITION — upward Purchase correction follows its original funding proportions

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- If a Vehicle Purchase cost correction increases cost, allocate the increase using the Investor Fund/Company Running Capital proportions recorded for that Purchase. These proportions may differ by Purchase; do not hard-code 70:30 or use the Investor Profit-share percentage.
- When the Investor Fund cannot provide its proportional increase, Company Running Capital supplies the exact shortfall, subject to the approved source-availability rules.

**Scope**
- Upward audited Vehicle Purchase cost corrections and linked source-allocation adjustments.

**Preserve unchanged**
- Preserve original Purchase and allocation history. Keep the separately approved proportional decrease, ROUND_HALF_UP, balanced-paise and Fund-first tie-break rules for downward correction.
- Require Investment ON and Vehicle Management ON for correction; actual Seller refund remains separate and requires its own approved module gates.

**Supersedes**
- None; this sets the approved funding-source treatment for an upward cost correction.

**Implementation impact**
- Recompute the correction from the Purchase's stored source proportions, apply fixed-precision rounding and verify corrected source allocations equal corrected cost before commit.

### ADDITION — Purchase cost correction requires Vehicle Management, Investment, and Accounting ON

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Require Vehicle Management, Investment, and Accounting ON for a Purchase cost correction, including a non-cash correction to Purchase cost and source allocations.
- If any required module is OFF, wait; preserve the Purchase, payable, allocations, installments, refunds, and correction history.

**Scope**
- Existing Purchase cost and related Investor Fund/Company Running Capital allocation corrections.

**Preserve unchanged**
- Q89's Vehicle Management gate, Q93's Investment gate, Q94's source proportions, and the actual Seller refund's separate gate and cap remain in force.

**Supersedes**
- None; this adds the Accounting gate to the separately approved Q89/Q93 gates.

**Implementation impact**
- Recheck all three module revisions inside one atomic Purchase correction; reject without partial changes.

### ADDITION — Investor-funded Sale Buyer Receipt requires Investment ON

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Block a Buyer Receipt against an existing Investor-funded Sale while Investment is OFF, even if Vehicle Management and Accounting are ON. Wait until Investment is ON.

**Scope**
- Actual Buyer Receipt against an already confirmed Sale of an Investor-funded Stock Vehicle.

**Preserve unchanged**
- Buyer Receipt still requires Vehicle Management and Accounting ON under Q86. This is separate from the Buyer refund gate in Q99.

**Supersedes**
- None; this adds the Investment-OFF condition for Investor-funded Sale receipts.

**Implementation impact**
- Reject without changing Sale receivable or posting a Buyer Receipt/Accounting movement while Investment is OFF.

### ADDITION — Phase 5 includes Sale price corrections

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Include audited Sale price correction in Phase 5. A Branch Accountant may correct only a Sale in their authorized Branch; a same-Company Company-level Accountant may correct a Sale in any Branch of that Company.
- Preserve the original Sale and actual Buyer Receipt/refund history and recompute its current outstanding position under the existing V2 calculation rules.

**Scope**
- Agreed price correction for a confirmed Phase 5 Stock Vehicle Sale.

**Preserve unchanged**
- Buyer Receipt/refund events remain separate actual cash events. The existing rule accepts valid partial installments and shows a compact warning with the remaining balance; over-outstanding amounts are rejected.

**Supersedes**
- SUPERSEDES EARLIER PHASE 5 SCOPE STATEMENT: Sale price correction was deferred. Later approvals include Sale price correction and Buyer refunds in Phase 5; other Sales/CRM deferrals remain unchanged.

**Implementation impact**
- Append a typed, audited Sale correction; enforce Q85 Branch scope and derive the current Sale position from valid linked events.

### ADDITION — Sale price correction module gate

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Sale price correction requires Vehicle Management and Accounting ON. Investment may be OFF.

**Scope**
- Audited price correction of a confirmed Sale for an Investor-funded Stock Vehicle.

**Preserve unchanged**
- This is the latest repeated Q98 answer. It supersedes the earlier same-turn answer that required Investment ON. Sale correction still uses Q97's role scope and does not create an actual cash event.

**Supersedes**
- SUPERSEDES EARLIER Q98 RESPONSE: requiring all three modules ON. The current answer requires Vehicle Management and Accounting ON only.

**Implementation impact**
- Check Vehicle Management and Accounting state/revision at write time. Keep Sale correction distinct from Buyer Receipt, Buyer refund, Fund posting, and Profit payment.

### ADDITION — Buyer refund can be recorded while Investment is OFF

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Buyer refund against an Investor-funded Sale may be recorded while Investment is OFF if Vehicle Management and Accounting are ON.

**Scope**
- Actual partial or full Buyer refunds against an existing Investor-funded Stock Vehicle Sale.

**Preserve unchanged**
- Q88's Vehicle Management OFF block remains. Q96's Investment-ON rule for Buyer Receipts is distinct and unchanged; an actual refund is not a Buyer Receipt.

**Supersedes**
- None; this sets the Investment-OFF condition for actual Buyer refunds.

**Implementation impact**
- Require Vehicle Management and Accounting for the actual refund cash event; use the Sale's current refund payable and reject excess.

### ADDITION — refresh derived Investor calculations while Investment is OFF

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- When a Q98 Sale price correction or Q99 actual Buyer refund is recorded while Investment is OFF, refresh affected Investor calculations from authoritative Sale, Buyer Receipt/refund, and Accounting source records.
- Do not create a separate cash event or Investor Profit payment as part of the recalculation.

**Scope**
- Derived Investor calculations affected by an approved Sale correction or Buyer refund during Investment-OFF.

**Preserve unchanged**
- Cash/Bank movement remains Accounting-owned. Q96 still blocks Buyer Receipts against Investor-funded Sales while Investment is OFF; derived recalculation alone creates no settlement or separate cash event.

**Supersedes**
- None; this defines the calculation-only effect while Investment is OFF for Q98/Q99.

**Implementation impact**
- Recompute derived values from linked source history; do not infer an Investor Profit payment from recalculation.

### ADDITION — Phase 5 direct Vehicle expense entry

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 5 may add an expense directly to a Stock Vehicle, including repair, service, transport, and similar vehicle-specific costs. Each approved expense is linked to that Vehicle and counted once in its total cost.
- An actual payment for that cost remains a separate Accounting movement linked to the expense; multiple partial Payments follow the existing Expense/Payment rules. The Vehicle expense record does not create another Cash/Bank movement.
- Expense entered through a Garage Job is deferred until the Garage phase.

**Scope**
- Direct Vehicle Expense record, its Vehicle relationship, cost aggregation, and linked actual Accounting payment in Phase 5.

**Preserve unchanged**
- Approved Investor-funded Vehicle costs still require traceable Fund use and cannot exceed Available Investor Fund; an approved Company Running Capital contribution remains a separate exact source. Existing category ownership, permissions, module gates, and Garage Job workflow remain in force.

**Supersedes**
- None; this adds direct Vehicle expense entry to Phase 5 without moving Garage Job functionality forward.

**Implementation impact**
- Add the smallest typed Vehicle Expense source and connect it to Accounting's existing actual-payment mechanism. Keep expense amount, source allocations, actual payments, and Vehicle total cost separately auditable.

### ADDITION — Investor Fund first for Stock Vehicle costs

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- For a direct cost of an Investor-funded Stock Vehicle, use available Investor Fund first. If it is insufficient, record the exact remaining amount as Company Running Capital for that Vehicle; do not overdraw the Investor Fund.
- A Stock Vehicle cost funded partly by Company Running Capital is still a Vehicle cost, not an additional Company Accounting Expense solely because the Company supplied the source.
- For a customer's Vehicle, the cost belongs on that customer's Garage Job bill. Garage Job billing remains deferred until the Garage phase.

**Scope**
- Direct Phase 5 Stock Vehicle costs and their Investor/Company funding-source allocation; customer-owned Vehicle costs are future Garage Job scope.

**Preserve unchanged**
- Q102 still includes direct Stock Vehicle expenses in Phase 5 and counts each once in Vehicle total cost. Actual cash moves through Accounting once. Purchase/Sale, Vehicle cost, Investor Fund, Running Capital, and Company Income/Expense remain distinct. Garage Job costs stay deferred.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION WORDING: automatically applying the generic Company Accounting Expense/Payment classification to a direct Stock Vehicle cost. This does not alter the separate actual Cash/Bank movement rule.

**Implementation impact**
- Allocate eligible cost against available Investor Fund and then the exact Company Running Capital shortfall; validate atomically. Keep the cost/source allocation separate from its actual Accounting cash movement.

### ADDITION — direct Vehicle Expense save and payment module gates

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- For a direct expense on an Investor-funded Stock Vehicle, Vehicle Management and Investment must be ON to save the expense and its Investor Fund/Company Running Capital allocation.
- Accounting is required only when an actual Cash/Bank payment is recorded. If Accounting is OFF, save the cost and source allocation without a cash movement; record the actual payment after Accounting is ON.

**Scope**
- Phase 5 direct Stock Vehicle Expense creation, source allocation, and actual payment.

**Preserve unchanged**
- Q103 source allocation remains available Investor Fund first, then exact Company Running Capital shortfall. Purchase funding and Purchase cost correction retain their own approved module gates; Q102 Garage Job expense deferral remains.

**Supersedes**
- SUPERSEDES EARLIER Q102 UNRESOLVED GATE: modules required for direct Vehicle Expense and source-allocation save. This does not change the actual-payment Accounting requirement.

**Implementation impact**
- Gate the non-cash Expense/allocation transaction on Vehicle Management + Investment. Gate the separate Accounting payment operation on Accounting; make each operation atomic and idempotent under its own contract.

### ADDITION — full Vehicle Expense amount with partial payable settlement

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Record the full direct Vehicle Expense when the bill/cost is incurred. Do not wait for full payment.
- Example: for a ₹5,000 Vehicle repair bill with ₹2,000 paid, show Vehicle Expense and Vehicle cost as ₹5,000 and remaining payable as ₹3,000.
- Allow zero, one, or multiple partial actual payments against that expense. Reject cumulative payments above the current outstanding payable. Each actual payment is separately linked to the expense and recorded through Accounting once.
- Settling an existing payable does not add its amount to Vehicle total cost again.

**Scope**
- Direct Phase 5 Stock Vehicle Expense capture and supplier-payable settlement.

**Preserve unchanged**
- Apply Q103 funding source: available Investor Fund first, then exact Vehicle-linked Company Running Capital shortfall. Do not classify this cost as Company Accounting Expense. Q104 save/payment module gates and later Garage Job customer billing remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER Q102 IMPLEMENTATION AMBIGUITY: whether the Vehicle Expense could be saved before full settlement and whether a partial-payment balance remains open.

**Implementation impact**
- Keep full cost and payments separate, derive outstanding payable from confirmed linked payments, and perform each payment as a separate idempotent Accounting-linked mutation.

### ADDITION — shared per-Accountant account preference for Phase 5 payments

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Share the same remembered Cash/Bank account preference between Seller installment payments and direct Vehicle Expense installment payments.
- Scope the preference to the authenticated Accountant within the current Company. Prefill the account used in that Accountant's last successfully saved payment, and allow changing the account before each payment.
- An unsaved, failed, or rejected payment must not replace the preference.

**Scope**
- Account prefill for Phase 5 Seller installments and direct Vehicle Expense installments only.

**Preserve unchanged**
- A payment stores the account actually selected for that payment; a remembered preference is not financial truth or authorization. Revalidate Company, account status, module state, and actor permissions at posting.

**Supersedes**
- None; this extends the previously approved Seller-payment preference to direct Vehicle Expense installments.

**Implementation impact**
- Reuse a Company-and-Accountant-scoped preference across these two forms; update it only after a successful authoritative payment. Other payment forms are not included by this decision.

### ADDITION — external reference required for Vehicle Expense installments

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Require an operator-supplied external reference for each actual direct Vehicle Expense installment, such as a bank transaction ID or Cash voucher number.
- A partial payment has its own reference and remains linked to the full Vehicle Expense. The external reference does not replace the server-generated payment identity.

**Scope**
- Phase 5 direct Stock Vehicle Expense payment form and its typed payment/Accounting record.

**Preserve unchanged**
- The full expense and derived payable remain separate from actual payments. Q105 partial-payment rules, Q106 shared editable Cash/Bank preference, Q103 funding allocation, and Q104 module gates remain.
- No duplicate-reference rejection or comparison rule is approved by this decision; other source-specific reference rules stay separate.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: whether Vehicle Expense installments need a user-entered external reference.

**Implementation impact**
- Add a required reference input to the existing Vehicle Expense installment form and carry its value to the typed payment source and Accounting event source_reference.

### ADDITION — normalized unique references for Vehicle Expense installments

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A direct Vehicle Expense installment external reference must be unique within the same Company and Cash/Bank account across all Branches.
- Trim leading/trailing spaces and compare case-insensitively; reject a duplicate before recording the payment.

**Scope**
- Actual partial/full payments against Phase 5 direct Stock Vehicle Expenses.

**Preserve unchanged**
- Q107 still requires a user-supplied reference on each installment. Q105 payment caps, Q106 shared account preference, and reference rules for Buyer Receipts/Fund Credits remain separately scoped.

**Supersedes**
- SUPERSEDES EARLIER Q107 WORDING: duplicate-reference uniqueness and normalization were undecided for Vehicle Expense payments.

**Implementation impact**
- Validate the normalized Company/account/reference combination under concurrency at payment posting; do not treat the reference as payment identity or idempotency key.

### ADDITION — require vendor refund before reducing a paid Vehicle Expense

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- If an Expense correction would reduce its amount below net actual payments, require the vendor's excess refund to be actually received and recorded in Accounting before applying the correction.
- Example: a ₹5,000 Vehicle Expense with ₹2,000 paid is later found to be ₹1,500. The ₹500 vendor refund must be received and recorded first; then correct the Expense to ₹1,500.
- Keep the old Expense and all actual payments/refunds; add an audited linked correction. Do not silently edit or delete those events.

**Scope**
- Downward correction of a paid or partially paid direct Stock Vehicle Expense.

**Preserve unchanged**
- Q105 keeps the Expense cost separate from its partial settlements. Q103 funding-source rule, Q104 module gates, Q107 required external references, and Q108 duplicate checks remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: how to handle a downward Vehicle Expense correction when actual payments exceed the corrected cost.

**Implementation impact**
- Block the correction until linked net actual payments no longer exceed corrected cost after the recorded refund; validate atomically and retain audit history.

### ADDITION — corrected Vehicle Expense uses Fund-first source allocation

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Once a Q109 vendor refund is actually received and recorded, recalculate the corrected Vehicle Expense source split using available Investor Fund first; assign only the exact remaining shortfall to Company Running Capital.
- Do not carry the original source ratio forward. Example: if a corrected ₹1,500 cost can be fully covered by available Investor Fund, allocate ₹1,500 to Fund and ₹0 to Running Capital. If only ₹1,000 is available, allocate ₹1,000 to Fund and ₹500 to Running Capital.

**Scope**
- Source allocation for a direct Stock Vehicle Expense after an approved downward cost correction.

**Preserve unchanged**
- Original allocation/payment/refund records remain immutable; append adjustments. Q94 proportional correction remains Purchase-specific. Q103 fund availability and Company Running Capital separation remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q109 IMPLEMENTATION ITEM: whether a corrected Vehicle Expense follows original source proportions or reapplies the Fund-first order.

**Implementation impact**
- Lock/check current available Fund in the correction transaction and write exact fixed-precision adjustment rows; do not hard-code a percentage.

### ADDITION — Vehicle Expense correction requires all three modules

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- After the required vendor refund is actually received and recorded, a downward Vehicle Expense correction and its Fund-first source reallocation require Vehicle Management, Investment, and Accounting ON.
- Apply the correction only after validating all three modules; if any is OFF, leave the current Expense, payable, and source allocations unchanged.

**Scope**
- Downward correction and source reallocation of a direct Investor-funded Stock Vehicle Expense after actual payment/refund.

**Preserve unchanged**
- Q104's lower gate for initial Expense/source-allocation save and separate Accounting gate for actual payment remain. Q109 refund ordering and Q110 current-Fund-first allocation remain. Purchase correction gates are not changed.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Q110 IMPLEMENTATION ITEM: module requirements for a corrected Vehicle Expense and its reallocation.

**Implementation impact**
- Recheck Vehicle Management, Investment, and Accounting revisions at commit; roll back all writes if any required module is OFF.

### ADDITION — Company-funded Stock Vehicle expense source

**Status:** APPROVED BUSINESS DECISION CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- When a direct Stock Vehicle expense has no Investor Fund source, assign its full amount to Company Running Capital linked to the Vehicle. Do not create an Investor Fund use.

**Scope**
- Direct Phase 5 costs for Company-funded Stock Vehicles without an Investor Fund allocation.

**Preserve unchanged**
- Investor-funded Stock Vehicle costs continue to use available Investor Fund first and Company Running Capital for the exact shortfall. Customer Vehicle costs remain deferred Garage Job costs.

**Supersedes**
- None; this clarifies the already approved Q103 no-Investor source case.

**Implementation impact**
- Permit the Vehicle cost source to represent 100% Company Running Capital without a placeholder Investor Fund allocation. The module gate for this case remains BUSINESS DECISION REQUIRED.

### ADDITION — Vehicle Expense permissions and Company-funded module gate (Q112–Q115)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Branch Accountant may add a direct Stock Vehicle expense and pay its installments only for a Vehicle in the Accountant's authorized Branch. A same-Company Company-level Accountant may do so in any Branch.
- The same Branch scope applies to actual Vendor refunds and Vehicle Expense/source-allocation corrections.
- If no Investor Fund is used, Vehicle Management is required to record the cost; Investment is not required. Accounting is required for an actual payment.

**Scope**
- Direct Stock Vehicle expense entry, actual installments, Vendor refunds, and corrections.

**Preserve unchanged**
- Investor-funded expenses retain Q104 gates. Vendor refunds require all three modules under Q116; corrections use Q111/Q121 gates. No generic cross-Branch access is granted.

**Supersedes**
- None; these specify action-level Branch permissions and the Company-only funding gate.

**Implementation impact**
- Enforce resource Branch scope for each operation and validate action-specific module gates atomically.

### ADDITION — Vehicle Expense Vendor refund and correction decisions (Q116–Q122)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- An actual Vendor refund against a direct Vehicle Expense requires Vehicle Management, Investment, and Accounting ON. No refund cap based on prior Vendor payments is approved.
- Allow an upward correction for a valid additional Vendor bill. Recalculate the corrected source split using available Investor Fund first and Company Running Capital for the exact shortfall; derive outstanding payable from corrected cost minus valid actual payments.
- One Vehicle may use only one Investor's Fund. A Company Running Capital-only Vehicle cost creates no Investor Fund use.
- A downward correction requires all three modules even if no refund is needed. Apply corrections to the original Expense effective date and affected Investor calculation; keep the actual correction timestamp separately.

**Scope**
- Direct Stock Vehicle Expense refunds, upward/downward corrections, source allocation, and derived historical Investor calculations.

**Preserve unchanged**
- Q109 refund-before-correction rule when net actual payments exceed corrected cost; Q110 Fund-first correction source order; original history and actual cash movements remain unchanged. Company Profit reporting windows are not applied to Investor Profit.

**Supersedes**
- None; this completes the approved business handling around Q109–Q111 for the newly answered cases.

**Implementation impact**
- Append corrections and allocation changes, revalidate all required modules and current Fund under transaction locks, and derive the payable. Excess-refund classification remains unresolved.

### ADDITION — latest Vehicle Expense Vendor refund rule (Q118/Q123)

**Status:** APPROVED BUSINESS DECISION — LATEST CLARIFICATION
**Effective documentation state:** Current V2 addition

**Rule**
- Do not require an external reference for an actual Vendor refund or reject it because its reference duplicates another refund.
- Record the actual refund amount in Cash/Bank once. Apply against the Vehicle Expense only up to the remaining net actual payments. Provide the Accountant an option to assign any excess to another appropriate record. Never auto-create Company Income for that excess.

**Scope**
- Actual partial/full Vendor refunds against direct Phase 5 Stock Vehicle Expenses.

**Preserve unchanged**
- Q107/Q108 references remain mandatory and unique for Vehicle Expense installments, not refunds. Q117 has no cap on receiving actual money; Q123 limits the expense application. Q109/Q116 refund ordering and module gates remain.

**Supersedes**
- SUPERSEDES EARLIER Q118 ANSWER: required external reference and duplicate rejection for Vendor refunds only.
- SUPERSEDES EARLIER Q123 DETAIL only as to requiring a fixed excess record type/reason; the Accountant selects the destination from the available appropriate records.

**Implementation impact**
- Preserve the actual Cash/Bank movement once and reconcile the selected destination allocations. No duplicated movement or automatic Income classification.

### ADDITION — Phase 5 approved pooled-Fund and cost rules (Q124–Q131)

- An actual Vehicle Expense refund is entered for the full money received, once. Apply only the remaining net paid amount to that Expense. Explicitly allocate any excess to an eligible existing record; if no eligible record exists, do not post until it is created. Do not auto-create Company Income.
- Q130/Q132: Company Income is an explicit manual classification only. Create a separate Income record with Accountant-selected category and note, then apply the actual Receipt to it; do not edit the old Income record, auto-classify the excess, or create a second cash movement.
- Only a Company-level Accountant may allocate pooled Investor Fund to Vehicle Purchase or Investor-linked Vehicle Expense. An Investor-funded Expense is created and fully allocated by a Company-level Accountant; no Branch draft is allowed.
- A Branch Accountant may create a Vehicle Purchase or direct Vehicle Expense funded only by Company Running Capital for their authorized Branch. A Company-level Accountant may do this in any Branch of the same Company.
- Company Running Capital is recorded as the exact Vehicle-linked source amount without an advance-funded pool. Actual cash is recorded separately through Accounting only when it moves.
- Company-only Purchase requires Vehicle Management + Accounting. Investor-Fund Purchase requires Vehicle Management + Investment + Accounting. Company-only Purchase does not require Investment.
- These decisions do not add lender finance/EMI, Garage Job expenses, Profit distribution, or offline-write behavior to this workflow.
- Keep Phase 5 automation minimal. Do not add new automated approval or posting workflows as blockers to the core Vehicle/Fund work; defer additional automation until the system is ready, preserving separately approved automation decisions for later implementation.

### ADDITION — manual review after a used/returned Fund Credit attribution correction (Q133–Q134)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A full wrong-Investor Fund Credit attribution correction may be recorded even when the credit already has Vehicle Fund-use or principal-return history.
- Preserve every original Fund-use and principal-return record and its actual Cash/Bank movement exactly as recorded. Do not automatically reassign, edit, reverse, or recreate those records as part of the credit correction.
- The Accountant manually reviews and prepares the affected Investor calculations. Do not automatically recalculate or post historical Investor Profit, settlement, overpayment, or cash adjustments from this correction.

**Scope**
- A full append-only Investor attribution correction for one confirmed Fund Credit that has prior use and/or principal-return activity.

**Preserve unchanged**
- Original credit UUID, amount, source Branch, Accounting source link, actual cash movement, linked use/return records and prior actual payments. The correction itself creates no cash event.

**Supersedes**
- SUPERSEDES Q71's automatic historical Investor-calculation recalculation for a corrected credit with linked Vehicle use or principal-return history. The original receipt date remains the correction's effective date. Q72's separate adjustment treatment remains manual for this case.

**Implementation impact**
- Store an audited typed correction and expose that linked use/return history remains unchanged and requires Accountant review. Keep the existing Investment module gate and source-Branch authorization. No automatic Profit/settlement calculation or posting is part of Phase 5.

### ADDITION — Q100 Investor calculation refresh timing — 2026-11-17

**Status:** APPROVED BUSINESS DECISION — SCOPE RESOLUTION
**Effective documentation state:** Current V2 addition

**Rule**
- Phase 5 records approved Sale corrections, actual Buyer refunds, and their Accounting source events under their existing module gates. It does not calculate or refresh Investor Profit entitlements or periods.
- Defer Q100's derived Investor calculation refresh for those Sale changes to Phase 8. Phase 5 must not create an Investor Profit payment, settlement, or additional Cash/Bank event as a side effect.
- In Phase 8, derive affected Investor calculations from authoritative Sale, receipt, refund, and Accounting source history, keeping effective dates and correction-recorded timestamps distinct.

**Scope**
- Implementation timing for the calculation-only refresh described by Q100 after Q98 Sale-price corrections and Q99 Buyer refunds.

**Preserve unchanged**
- Q98/Q99 Sale correction, Buyer refund, module-gate, and actual Accounting movement rules remain in effect in Phase 5.
- Q133–Q134 manual review after a used/returned Fund Credit attribution correction remains separate and unchanged.

**Supersedes**
- SUPERSEDES the earlier Q100 Phase 5 implementation timing only. It does not remove the Phase 8 calculation requirement or change the source-record and cash-movement rules.

**Implementation impact**
- Do not add Investor agreement snapshots, Investor Profit result screens, or automatic calculation refresh to Phase 5. The current Phase 5 message that Profit calculations are not refreshed remains accurate.

### ADDITION — Phase 8 reconciliation, Loss, principal and existing settlement (2026-11-19)

**Status:** APPROVED BUSINESS DECISIONS. These rules govern Phase 8 implementation; they do not assert that the features are implemented.

- Assign a Vehicle's deal-level Investor Profit to the Investor reconciliation period containing the actual Sale date. Show any confirmed deal-level Profit payment against that same entitlement as Paid and deduct it exactly once from the period's remaining payable. Keep payment and calculation records separate.
- A same-Company Company-level Accountant manually confirms each Vehicle Loss with a recorded reason and its Investor/Company impacts. A calculated negative result alone does not debit Investor Fund or post a cash movement. Existing approved future-Profit loss offsets and the exceptional Exit rule remain separately governed.
- Ordinary principal withdrawal is limited to Available Fund: exclude principal committed to open Vehicles and outstanding refund obligations. Preserve the existing Company-wide Fund and Branch authorization rules.
- A Phase 8 Investor Profit or settlement correction spanning Branches is available only to the same-Company Company-level Accountant. This is action-specific authority, not a general cross-Branch grant.
- When Investment is OFF and Accounting is ON, a same-Company Company-level Accountant may continue only authorized steps of an Investor Exit/settlement already started before the OFF transition. New Fund credit, ordinary withdrawal, or new Exit initiation remains subject to its normal module gate. Every actual payment still needs its own Accounting authorization and cash event.

**Supersedes:** Earlier unresolved wording only for these five decisions. Effective agreement snapshot sourcing, exact Loss impact amounts, adjustment history and other unreconciled requirements remain subject to their separately approved rules.

### ADDITION — Phase 8 Monthly Interim payment Branch authority (2026-11-19)

**Status:** APPROVED BUSINESS DECISION

- A Branch Accountant may record an actual Monthly Interim payment only in their authorized payment Branch.
- A same-Company Company-level Accountant may record that payment in any Branch of the Company.
- This is action-specific authority. It does not permit cross-Branch Investor/Fund reads or other financial mutations.
- The actual payment remains a separately confirmed Investment record linked to one Accounting Cash/Bank movement; configuration or a calculated due amount is not Paid.

**Scope:** Actual Monthly Interim payment confirmation and its Company/Branch authorization.

### ADDITION — Q135 Monthly Interim partial payments and monthly cap (2026-11-19)

**Status:** APPROVED BUSINESS DECISION

- An Investor's configured Monthly Interim amount may be paid in partial or repeated payments within the same calendar month.
- The sum of actual Interim payments for that Investor and month must not exceed that month's effective configured amount, across all Company Branches.
- A failed or repeated request must not create another payment or Cash/Bank movement. The payment history remains source-linked and separate from final Profit reconciliation.

**Scope:** Monthly Interim actual payment amount/cap only. It does not turn a paid Interim advance into a final payable or settlement.

### ADDITION — Editable Loss impact before Accountant confirmation (2026-11-19)

**Status:** APPROVED BUSINESS DECISION

- Show the calculated Vehicle Loss and a suggested Investor/Company split for Accountant review. A Company-level Accountant may edit the impact amounts and must explicitly confirm them with a reason; no Loss impact is posted automatically.
- The Investor Loss percentage need not equal the Investor Profit percentage. The agreement-based split may be displayed as a suggestion, not enforced as the final Loss allocation.
- Preserve the original calculation, confirmed amounts, actor, reason and history. Confirmation alone does not debit Investor Fund, move Cash/Bank or settle Exit.
- This supersedes earlier wording that requires the agreement percentage to determine the final Investor Loss share. Existing explicitly confirmed Loss offset and Exit rules continue to apply to the confirmed impact.

### IMPLEMENTATION VERIFICATION — Phase 8 financial source guards (2026-11-22)

**Status:** Implemented and verified locally on the audit branch; not a deployment claim.

- Exit Profit payout database guards compare the latest confirmed position with current period sources. Sale corrections and Investor calendar changes invalidate stale payout attempts without requiring a newer reconciliation row.
- Owner Profit-period SQL source fingerprints match the Python canonical hash for empty and populated periods. Loss offsets and Exit Loss applications share a serialized Investor-level cap.
- Verification used disposable PostgreSQL 15 with Django 5.2.18. The focused Phase 8 regression batch passed 32 tests, including stale direct-write rejection, no surviving payment/accounting artifacts after rejection, and cross-path Loss concurrency.
- Local checks passed: `manage.py check`, `manage.py makemigrations --check --dry-run`, and `git diff --check`. No React source changed in this closure slice.
- Source changes remain local to `codex/audit` until its push is verified. No deployment or production database was involved.
