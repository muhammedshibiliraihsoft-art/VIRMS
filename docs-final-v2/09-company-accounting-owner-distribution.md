# 09 — Company Accounting & Owner Distribution

Status: DRAFT V2 — Company finance source after approval

## Boundary and authority

Each Company/Tenant has one bounded accounting system covering its Branches. Accounting is the authoritative Company financial backbone for actual Company income, Expense, receipt, payment, Running Capital and Owner Distribution records. Investment owns Investor Fund and positive Investor entitlement; Garage owns work and customer charges. Accounting links to those source events without duplicating an economic amount or turning a Branch into another ledger-owning Company. Cross-Company postings or reporting are forbidden.

The current scope is the accounting needed for Vehicle resale and Garage operations, not a generic ERP. Cash/Bank basics and customer receivables are in scope where relevant; supplier payable and advanced inventory are not mandatory without a confirmed need. Applicable GST/Tax/Invoice details may be retained but no full tax suite is required.

## Company financial records

Record classified Company Income, Expense, actual Receipt and actual Payment with amount, Company, relevant Branch attribution, source, actor, timezone-aware time and history. Cash/Bank basics identify the real payment/receipt channel or position where required. They do not replace source transaction identity or permit manual balance overwrite. A Company-wide Expense may originate in an operational Branch and carry a common-company-expense category/label; it remains part of consolidated Company result. Branch filtering must identify that classification instead of silently pretending it is an independent Branch Company.

External-customer Garage charges and receipts contribute Garage Revenue and related receivable positions under the Company accounting boundary. Buyer Sales and receipts for funded Stock Vehicles remain linked to the Stock Vehicle Sale workflow in 05. A receipt may appear in an Investment, Garage and Accounting view but must have one authoritative source and one economic cash effect. A due amount, agreed price, suggestion or reminder is not an actual receipt.

## Positive Vehicle Company Share

For a positive completed funded Stock Vehicle result, calculate the proposed Investor Share under the applicable effective configurable agreement and derive Company Share as the remainder of that approved positive result. The current business standard may be configured as 33% Investor Share, but no Tenant is forced to use it and no 33%, 65% or 67% share is hard-coded. Platform Back Office administers protected Investor positive-share agreement configuration; Accountant uses the approved effective value for authorized postings. The confirmed Company Share enters the Company financial layer and is not a direct Owner payment. Preserve the underlying Vehicle, Investor agreement snapshot, Sale, collection and any linked correction. Final Investor/Company Vehicle settlement requires full Buyer Sale collection and resolution of applicable refund positions.

Company Running Capital is the exact separately sourced actual Company contribution to an approved Vehicle cost. It is neither Company Share nor Investor principal, Company Profit, interest, premium or another return category. For a normal positive Vehicle after full Buyer collection, reconcile actual Investor principal, identify and recover/reconcile actual Vehicle-linked Company Running Capital as capital, then determine the remaining actual positive economic result for configured Investor/Company allocation. Approved Vehicle cost is counted once; recovered capital is not a second Expense, new Company Income, Company Share, Garage Revenue or Profit. An editable recovery suggestion does not change the open position; only a separately authorized confirmed actual recovery does. Partial collection may show provisional positions but cannot finalize Vehicle settlement. Loss treatment remains manual under 05.

## Company result and distributable Profit

The conceptual Company result is:

`Vehicle-business Company Share + Garage Revenue + Other Company Income − Company Expenses = Company Profit/Loss`

Keep source transactions and their classification traceable so the same Vehicle cost, Garage Job cost, receipt or Company Share does not enter this equation twice. Branch-filtered views use original attribution while Company totals consolidate all Branches. A Company Profit/Loss result is not automatically an Owner payable, and a calendar period ending does not transfer funds. The amount that is actually distributable requires a confirmed Company-level position.

**BUSINESS DECISION REQUIRED:** Define the exact distributable-Profit basis, period close/carryforward treatment, and recognition of Company Share, Garage Revenue and common Expenses. The conceptual equation does not by itself authorize an automatic Owner payment or decide cash-versus-accrual treatment.

## Owner allocation and payout

Owner Distribution occurs from confirmed Company-level distributable Profit on a configured Half-yearly/six-month or Annual/one-year period, separate from Investor six-month/annual Profit reconciliation and the three-month Investor Exit notice. Platform Back Office administers the protected effective recipient list and nonnegative percentages summing to exactly 100% of a positive Owners distribution pool, with specific backend action permission, version/history and audit. Accountant uses the effective approved split for authorized distribution confirmation; Owner has read visibility without protected-percentage mutation. The documented current standard configuration is 48.5% / 51.5%; it remains replaceable for the applicable Company and period, never hard-coded as two permanent Owner columns. A zero distributable amount produces no positive Owner allocation.

Use INR fixed-precision decimal arithmetic. Retain high precision for percentage intermediates, round final posted money to two decimal places with `ROUND_HALF_UP`, and avoid binary floating point. For an approved positive distribution amount, calculate each recipient's raw share at high precision and provisional two-decimal share with `ROUND_HALF_UP`. Compute the residual between the approved amount and sum of provisional shares. If positive, add one paise at a time to the recipient most under-allocated relative to raw share; if negative, subtract one paise at a time from a recipient most over-allocated, never allowing a negative allocation. Recompute differences after each step and break equal priorities using stable configured recipient order. Continue until every final allocation is nonnegative and the sum equals the approved distribution exactly. This rule has no fixed Owner count. Preserve the effective recipient/percentage snapshot for the confirmed period.

Calculated and Eligible are not Paid. Owner Distribution is human-confirmed as actual individual payments within authorized Company scope. A recipient's new confirmed payment must be positive and no greater than that recipient's current outstanding approved amount, with atomic concurrency and duplicate protection. A partial actual payment leaves the remainder payable; a reminder or suggested allocation cannot mark it Paid. Later legitimate correction retains original allocation and payment history and reconciles one current open position through linked adjustments/recoveries, without silent netting against Investor Fund or Company Running Capital.

Under 01's automation levels, backend-derived Company/Branch totals and exact approved-allocation arithmetic are Level 1 calculations. Proposed distributable amount once its approved basis exists, Owner allocation and Running Capital recovery are Level 2 editable suggestions where permitted. Period due, unpaid recipient position and other open Company obligations are Level 3 reminders/statuses. Actual Company receipts/payments, confirmed capital recovery, approved distribution and individual Owner payments are Level 4 human-confirmed events; protected percentage changes instead require Platform Back Office confirmation. Exceptional Company/Running-Capital Loss impacts and sensitive corrections are Level 5 manual decisions with reason and audit, followed by authorized confirmation for any actual financial event. Period close or a suggestion never automatically distributes money.

## Loss, corrections and audit

New Stock Vehicle Loss and Running-Capital Loss impacts remain manual under 01 and 05. Do not apply Owner distribution percentages to a negative Vehicle result or create automatic Owner loss-contribution obligations. Company accounting records the manually confirmed Company impact and actual financial transactions with reason/history. Corrections preserve original source, actor, time, values and classification; linked adjustments rather than silent deletion restore the current Company and recipient positions. Reports and caches are rebuildable from authoritative transactions.
