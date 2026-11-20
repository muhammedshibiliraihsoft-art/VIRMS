# Phase 8 — Integrated Finance, Settlement, Corrections, and Company Accounting

**Status:** `PHASE 8 IMPLEMENTATION COMPLETE LOCALLY — PHASE 9 NOT STARTED`

**Implementation status:** Verified in the local Phase 8 worktree on 2026-11-20. This does not claim authenticated browser, CI, staging, production or deployment verification; consolidated browser acceptance belongs to Phase 9.

**Company Loss carryforward:** Company period confirmation persists source versions, prior Loss carryforward and liability review. Owner allocations use the protected effective-dated split snapshot and exact `allocate_owner_distribution` calculation; actual partial payouts are separately recorded through Accounting.

**Payment safety gate:** The temporary `PRINCIPAL_RECOVERY_REQUIRED` gate has been replaced by source-linked Investor principal and Company Running Capital recovery, Buyer principal refund reserves, and current recovery-position checks before deal-level Profit payment. Source corrections require Accountant review; existing payments and idempotent replays remain retained.

**Exit funding gate:** New Fund credit and new Investor-funded Vehicle Purchase commands reject an Investor with a requested Exit or cancellation pending. They check the same locked Investor within the transaction used by Exit submission and cancellation review; approved cancellation permits new funding again. Existing funded Vehicle work is unaffected. PostgreSQL API coverage checks both open states and the approved cancellation path. Separate two-thread PostgreSQL tests verify serialization of Exit submission against Fund credit and Investor-funded Purchase. This does not implement final Exit settlement.

**Exit notice extension:** The initial three-calendar-month notice deadline derives from the request's immutable UTC creation instant with month-end clamping. A same-Company Company Accountant can append a later deadline with a reason while Investment is ON; PostgreSQL guards enforce scope, immutable origin, ordering and audit. The Accountant screen supports the action and the bound Investor view shows the deadline. Final settlement is implemented below; authenticated browser and staging/production behavior remain unverified.

**Loss confirmation decision:** The later V2 05 addition resolves the earlier conflict: a Company Accountant reviews and may edit the Investor and Company Loss amounts before explicit confirmation with a reason. The Investor Loss percentage need not equal the Profit percentage. The confirmed amounts must sum exactly to the Vehicle Loss; confirmation does not debit Fund or move Cash/Bank. The previous agreement-based calculation remains a suggestion only.

The Vehicle financial-position response supplies an optional `suggested_loss_split` for a negative calculated result when the applicable agreement snapshot is available. The UI labels it as an editable suggestion and sends explicit Investor/Company amounts and a reason for confirmation. Investment stores the original suggested amounts alongside the final signed impacts; existing historical confirmations retain null suggestion fields. PostgreSQL constraints and deferred audit guards enforce signs, totals, snapshot and audit metadata for new records. The additive projection is excluded from the source fingerprint to preserve existing immutable confirmation versions. Loss confirmation itself creates no cash movement; authorized offsets remain separately recorded.

**Known test consequence of payment safety gate:** The Phase5WorkspaceView React test that expects a new Profit payment to succeed currently fails because the action is intentionally disabled pending principal recovery. On the last targeted run, 14 of 15 tests passed. Preserve the successful-payment test and restore the workflow only after the authoritative recovery prerequisite is implemented; a blocked-payment test alone does not prove payout completeness.

**Worktree inspected:** `codex/phase5-investment-foundation` at `d57a9208`; local implementation updates reviewed 2026-11-19.

## Outcome and scope

Join authoritative Phase 4–7 sources into one Company financial position: collected Buyer money, Investor principal recovery, actual Company Running Capital, positive Investor/Company shares, Investor period reconciliation and Exit, Company result, and Owner Distribution. Show calculated positions without treating them as paid. Keep the [Malayalam scope draft](PHASE-08-SCOPE-DRAFT-ML.md) as the product scope; the V2 documents listed below govern business rules.

Later approved V2 additions resolved Sale-date deal Profit placement and payment deduction, manual Loss confirmation authority, Available-Fund withdrawal, Company-level cross-Branch correction scope, continuation of an Exit already started before Investment is switched off, Company Accountant confirmation with negative-result carryforward, ordinary Investor Profit payment authority, and verified Vehicle Company Share recognition as non-cash Company Accounting Income. These decisions remove the named business-rule blockers; implementation and acceptance remain incomplete. Source-derived gross calculations must not imply a confirmed payable, and missing ledgers/APIs remain disabled.

## Verified source boundary

| Existing source | Current owner | Phase 8 reads or writes |
| --- | --- | --- |
| Cash/Bank accounts, events, applications, movements, typed links | `apps/accounting` | Read actual money; create an Accounting event/movement only for a newly confirmed actual payment or receipt |
| Investor, Fund credits/use/returns, agreement/interim settings | `apps/investment` | Read principal and effective snapshots; own new Investor entitlement, reconciliation, adjustment, and Exit records |
| Vehicle, purchase, direct expenses, funding allocation | `apps/vehicles` | Read approved cost and its Fund/Running Capital sources; do not copy the cost |
| Stock Job cost links and Garage charge/receipt sources | `apps/garage` | Read linked Stock cost and Company Garage revenue sources; do not create a second Vehicle cost or receipt |
| Confirmed Sale, Buyer receipts/refunds, correction history | `apps/vehicles` | Read current Sale position and actual collection; recompute affected derived positions after corrections |
| Company role grants, Branch assignments, module revisions | `apps/accounts`, `apps/tenants` | Authorize every read and command on the server; persist the effective revision used for a financial command |

Repository inspection found `AccountingSourceLink`, `AccountingEvent`, `AccountingApplication`, `VehicleSale` and its receipt/refund/correction endpoints, Garage Stock cost links, versioned `VehicleResultConfirmation`, Investor Profit calendar configuration, Investor account binding, Exit request history, immutable Investor Vehicle Profit and Monthly Interim payment records with explicit Accounting source links. Interim payment now supports partial/repeated payments under the Investor's monthly cap, with a Company-wide locked total. Period reconciliation/restatement, final Exit settlement, Company period confirmation, Owner allocation, and Owner payment remain absent. Existing models and routes remain authoritative for their own records.

## Financial position and recognition

1. Read one effective, audited cost per purchase, direct Vehicle Expense, and eligible Stock Job cost. Read one current corrected Sale price and each actual Buyer receipt/refund. Preserve original effective dates separately from correction-recorded timestamps.
2. Derive current Buyer receivable/refund payable from the Sale owner's existing rules. An unpaid amount is not collected cash. A pending refund is not distributable cash or final settlement.
3. Reconcile outstanding Investor-funded principal and the exact Vehicle-linked Company Running Capital separately. The normal positive mixed-funding path requires full Buyer collection before final Vehicle settlement. A provisional position during partial collection is read-only.
4. Once the approved positive result is eligible, use the effective Investor agreement snapshot applicable to that Vehicle. Derive the Company Share as the remainder; final posted shares must sum exactly to the approved positive result. Apply fixed-precision INR arithmetic and the V2 rounding rule. No fixed 33%, 65%, or 67% is embedded in code. A verified Company-level Accountant confirmation recognizes the positive Company Share as a typed, non-cash Accounting Income event in the same transaction.
5. Distinguish an economic classification/recovery from actual cash. A capital recovery cannot create a second Buyer receipt, Company Income, Vehicle Expense, or Profit. Any actual new payout/repayment posts once through Accounting with an explicit source relationship.
6. Q100 Sale price corrections and Buyer refunds invalidate affected derived Investor positions. Rebuild the proposed calculation from authoritative history; never silently revise an actual earlier payout or create a cash movement. Q133–Q134 used/returned Fund Credit attribution corrections remain flagged for manual Accountant review, without automatic reassignment of old Fund-use/return rows.

Each Investor has a separate Profit calendar. The approved default is six months; the same-Company Company-level Accountant may set a start date and duration in months or years. A change starts at the next incomplete period boundary and cannot overlap a completed calculation. Vehicle result belongs to the period containing its Sale date, even when final Buyer collection arrives later; after collection, restate the affected period with audit history. Do not split Vehicle Profit by Fund credit lot. Immutable deal-level Investor Profit payments are recorded against one confirmed Sale result and one Accounting cash movement; confirmed Monthly Interim payments also create exactly one linked Accounting cash movement and are projected separately as Paid facts into the period containing the effective payment date. The period and bound Investor portal keep deal Profit and Interim Paid amounts separate; neither creates a payable/open balance. Durable period reconciliation and historical restatement records still need implementation.

## Domain records and migration boundary

The implementation design must first inventory existing columns, constraints, and migrations in `apps/investment`, `apps/vehicles`, `apps/garage`, and `apps/accounting`. New Phase 8 records should be narrow and source-linked:

- A versioned Vehicle financial calculation/confirmation with Company, Vehicle/Sale, source version or snapshot, effective agreement, exact principal and Running Capital positions, positive result, Investor/Company shares, actor, reason, and status. Calculation versions must not pretend to be cash events.
- Investor period configuration/version and durable reconciliation/restatement records with links to eligible Vehicle results and actual retained Interim/deal payments. Sale-date inclusion and Interim-as-Paid are approved; a persisted current payable/recoverable position and adjustment history are not implemented.
- Investor Exit/settlement position with Company-wide source references, open obligations, actual principal/Profit payments, status history, actor and reason. Cross-Branch finalization is Company-level Accountant only.
- Explicit adjustment/recovery records for later source corrections and actual partial repayments. Preserve the original payment and correction chain; derive one current open balance.
- Company result period, confirmed distributable pool, protected Owner split snapshot, recipient allocations and partial actual payouts. No distributable pool or period close can be posted before its basis is approved.

These are record responsibilities, not final table names or a migration approval. Use FKs or equally enforceable typed relationships to the owning source; reject free-form polymorphic IDs. Every new row is Company-scoped. Store Branch provenance on source-linked entries without creating separate Branch-owned Investor funds. Add only the constraints/indexes needed by the approved slice, then verify fresh and replayed PostgreSQL migrations. Do not backfill historical entitlement or payment from Sale price alone.

## Command and API contract

Use additive, authenticated Company-scoped read endpoints for Vehicle position, Investor period position, Exit preview, Company result, and Owner allocation preview. Responses identify source versions, calculation status, actual paid amount, open balance, and blockers. A preview has no financial side effect and may be refreshed after a source correction.

Use separate commands for confirmed principal/Running Capital recovery, eligible Investor payout, Interim payout, reconciliation, Exit payment/closure, adjustment repayment, Company period confirmation, and Owner payout. Final routes, request fields, and permission names are set only after the owning slice and its business gate are approved. A command must require the server-owned source ID, expected version, amount where money moves, Cash/Bank account, idempotency key, and reason where V2 requires one. Client totals, Branch selections, and labels cannot authorize or define money.

For an actual cash command: authenticate and resolve Company/role/Branch; check the current module revision; lock the owning open position; rederive its cap from authoritative records; validate amount and exact source relationship; commit the domain record, Accounting event/movement/application/link, audit, and idempotency response in one database transaction. Replay returns the original result; a different payload with the same key conflicts. No partial commit or second cash effect is acceptable.

**Module OFF:** normal reads may continue under existing access rules. Do not infer a new settlement exception from the Phase 4 Accounting exception. The action-specific minimum old-obligation commands for Investment, Vehicle, and Accounting remain decision-gated. Source corrections already authorized by existing modules keep their existing gates; Phase 8 derived refresh itself creates no cash event.

## Authorization, UI, and error behavior

Enforce Company isolation on every source join and read. Branch Accountant sees only authorized Branch positions; a consolidated Investor Fund/Exit or Company Owner distribution view requires its existing Company-level authority. Accounting's cross-Branch correction grant does not extend automatically to Investment, Garage, or Vehicle. Owner is read-only; Platform Back Office manages only protected configurations assigned to it by V2.

Keep existing React routes and composition. Add compact source and calculation detail, status, blockers, confirmation, and audit history to the owning screens. A failed command cannot display success. Reload must return the same canonical position. Pending refund, partial collection, unresolved Loss, stale source version, module OFF, and missing policy decision need distinct, understandable disabled/error states.

## Slice order and verification gates

1. **Read-only source reconciliation:** Vehicle cost, Sale collection, Investor/Running Capital position and Q100 invalidation. Verify no duplicate cost/cash and same-Company joins.
2. **Confirmed positive Vehicle position:** agreement snapshot, full-collection gate, separate capital and positive shares, one audited confirmation. Verify concurrent confirmation and correction/retry behavior.
3. **Investor period and Interim:** immutable deal Profit payments and Monthly Interim payments are implemented with source-linked actual Cash/Bank movements; Interim supports partial payments under a locked monthly cap. Projection and portal display paid facts separately by effective date. Durable period reconciliation, historical restatement, overpayment recovery and final payable/recoverable remain incomplete.
4. **Investor Exit and Loss:** implement action-specific manual authority and closure only after Loss/settlement decisions. Verify cross-Branch scope, open obligations, principal cap and actual cash links.
5. **Company result and Owner Distribution:** implement after distributable basis, recognition, period close/carryforward decisions. Verify exact 100% split, paise remainder, partial recipient payouts and source corrections.
6. **Integrated UI and audit:** focused API, permissions, tenant isolation, concurrency/idempotency, migration, React reload/error and browser workflow checks on disposable PostgreSQL.

After each slice, run focused regressions for affected Phase 4–7 flows. A final risk-based audit must establish the actual implemented end state. CI, staging, production, and deployed database permissions remain `UNVERIFIED` until observed; architecture publication alone does not change roadmap completion.

## Decision register before implementation lock

| Gate | Current V2 boundary | Affected slice |
| --- | --- | --- |
| Deal Profit versus period reconciliation; eligible principal and withdrawals | `BUSINESS DECISION REQUIRED` in V2 05 | Investor period, Interim, payout |
| Manual Loss impact and confirmation authority | `BUSINESS DECISION REQUIRED` in V2 05 | Loss, Exit closure, Company result |
| Distributable Profit recognition, period close/carryforward | `BUSINESS DECISION REQUIRED` in V2 09 | Company result, Owner Distribution |
| Cross-Branch Phase 8 correction authority | `BUSINESS DECISION REQUIRED` in roadmap; action-specific existing grants remain | Corrections and restatement |
| Minimum old-obligation settlement while module OFF | `BUSINESS DECISION REQUIRED` in roadmap | Commands and module gates |

## Sources

- `planning/V2-DEVELOPMENT-ROADMAP.md`, Phase 8.
- `docs-final-v2/02-user-roles-permissions.md`, `04-data-model-relationships.md`, `05-vehicle-investor-finance-workflow.md`, and `09-company-accounting-owner-distribution.md`.
- `architecture/phase-04-company-accounting-foundation/`, `phase-05-investment-vehicle-running-capital/`, `phase-06-garage-jobs/`, and `phase-07-sales-buyers-collection/`.
- Current `apps/accounting`, `apps/investment`, `apps/vehicles`, and `apps/garage` model/API source.

## Approved decision reconciliation — 2026-11-19

The decision register above is a historical pre-implementation gate snapshot. The user has now approved these Phase 8 rules, recorded in V2 `02`, `05`, and `09`:

- Deal-level Profit belongs to the Sale-date Investor period; confirmed deal-level payments reduce that period's payable once.
- Each Vehicle Loss is confirmed manually, with reason and impacts, by a same-Company Company-level Accountant. A negative calculation does not debit Fund or move cash.
- Ordinary principal withdrawal uses Available Fund only. Committed Vehicle principal and outstanding refund obligations are unavailable.
- Cross-Branch Investor Profit/settlement corrections are same-Company Company-level Accountant actions only.
- An Exit/settlement begun before Investment switched OFF may continue through specifically authorized Company-level Accountant actions while Accounting is ON; new Investment actions remain gated.
- The Company-level Accountant reviews income, expenses and liabilities and manually confirms distributable amount. Negative Company period results carry forward; only a positive amount after prior Loss is covered can be considered for Owner Distribution.
- A verified positive Vehicle result recognizes its Company Share as Company Accounting Income through an exact typed `VehicleResultConfirmation` source link; this is not a cash event. A later verified source version reverses the old recognition once and records the replacement.
- Ordinary Investor Vehicle Profit payment may be recorded by a Branch Accountant only in the authorized Sale Branch, or by a same-Company Company-level Accountant in any Company Branch.

These decisions remove the named business-decision gates only to the stated extent. Implementation still needs verified effective agreement snapshots, source recognition, typed adjustment/payment records, transaction controls, migrations, and actual acceptance evidence. No Phase 8 completion claim follows from this section.

## Local implementation checkpoint — 2026-11-19

**Verified from the repository:** effective agreement snapshots are used by the versioned Vehicle result confirmation; Investor calendars are stored as append-only versions; Sale-date gross Profit and Investor Loss shares are calculated; and a Company Accountant-only `GET /investment/investors/{investor_id}/profit-periods/` projection is wired to the Accountant UI. The projection now includes actual deal-level payment total as a separately labelled fact, while its status remains `NOT_RECONCILED`; it does not expose provisional net payable. An immutable deal-payment record, typed one-to-one Accounting source link, transactional cash movement, Sale-Branch authorization, idempotency, and payment cap are implemented locally. The Investor Portal reads the bound Investor's own recorded deal-payment totals and still exposes no payment action. The portal also has server-resolved account binding, Exit request/cancellation, and Company Accountant binding read/link/revoke UI. Company Result is connected to the existing Accounting Result report and is explicitly not final distributable Company Profit.

**Still incomplete:** persisted period reconciliation and adjustment/recovery history; final Exit settlement; Company period confirmation and negative carryforward persistence; protected Owner split snapshots, exact allocations, and actual partial payouts; and completed Main System acceptance/browser proof. Company Share recognition and ordinary deal-level Investor payout are implemented only in part and do not complete these missing workflows. Phase 8 is therefore not complete and Phase 9/10 acceptance remains blocked.

## Investor period snapshot and restatement implementation checkpoint — 2026-11-19

**Verified from repository and disposable PostgreSQL:** InvestorProfitPeriodReconciliation stores append-only, versioned Company Accountant confirmations. POST /investment/investors/{investor_id}/profit-period-reconciliations/ requires a reason and the expected 64-character source fingerprint; it is idempotent, Company-scoped, checks Investment + Vehicle Management + Accounting revisions, rejects stale/unassigned sources, and creates no Accounting event or Cash/Bank movement. Migrations investment.0020 and 0021 create the typed snapshot and PostgreSQL immutability/source guards.

The confirmed calculation snapshot records Sale-period gross Investor Profit, actual deal Profit paid, actual Monthly Interim paid, confirmed non-cash Loss offsets, and the resulting signed calculation position. It is explicitly **not** a payable, Investor Fund debit, cash settlement, or final Exit. Later source changes keep the earlier snapshot, expose RESTATEMENT_REQUIRED with a separately calculated pending difference, and require a new confirmation version; prior periods and actual payments are not silently edited. The Accountant UI requires an explicit reason and labels the position as not payable.

**Checks actually run for this slice:** the focused disposable-PostgreSQL test passed, including fresh migrations, Company/Branch permission, idempotent retry, unchanged AccountMovement count on confirmation, database immutability, and a later actual deal Profit payment that produced a -₹100.00 pending restatement before version 2 was confirmed. Two focused React/API files passed 25 tests; npx tsc --noEmit passed. No browser, CI, staging, or production proof is established.

**Still incomplete:** final Exit/settlement and post-Exit recoverable handling; principal and Company Running Capital recovery; persisted Company period confirmation and negative carryforward; protected Owner split snapshots, exact allocations, and actual partial payouts; Investor Portal display of a confirmed private reconciliation position; and integrated Phase 9 browser acceptance. Phase 8–10 remain incomplete.

## Monthly Interim payment implementation checkpoint — 2026-11-19

Q135 is recorded in the canonical V2 finance decisions. `InvestorInterimPayment` is append-only, uses a typed Accounting source link and one Cash/Bank movement, and enforces the effective monthly amount across Company Branches with both service-level locking and a PostgreSQL deferred guard. Partial/repeated payments are supported. The Company Accountant projection and bound Investor portal show actual Interim Paid separately from deal Profit paid; neither confirms a final payable. The Investor self-history endpoint is server-paginated and binding-scoped.

On disposable PostgreSQL, `python manage.py test apps.investment.tests --verbosity 1` passed 41 tests, including fresh migrations through Accounting `0024`, API/module/Branch gates, replay, source-link/cash assertions, portal privacy, and concurrent monthly-cap enforcement. Targeted React portal/API checks passed 32 tests. These checks verify this slice only; full Phase 8–10 acceptance, browser verification, CI, staging, and production remain outstanding.

**Local verification evidence:** on disposable PostgreSQL `virms-phase8-10-test-20261119`, a preceding focused run passed 36 sale/payment/finance/portal tests; after adding the payment's Vehicle Management module revision, focused API and concurrent-cap tests passed 2/2 and the fresh test database applied all migrations. Django `check`, `makemigrations --check --dry-run`, Python compilation, and `git diff --check` passed. The current full React suite passed 231 tests across 39 files; configured lint and production build passed. The build reports a 751.70 KB main-chunk warning. Full authenticated browser acceptance, CI, staging, production, and deployment remain `UNVERIFIED`.

## Investor-confirmed snapshot in private Portal — 2026-11-19

The authenticated Investor self projection now includes the bound Investor's latest period snapshot, confirmed version/time, and source freshness status. The portal's source fingerprint uses individual deal payment IDs and effective timestamps, current Vehicle-result source versions, Interim payment IDs/dates, and only valid Loss-offset links, matching the Accountant calculation inputs. A changed source keeps the old signed snapshot visible as historical and shows a pending review difference; it is explicitly not a payable or deduction. Accountant reason, actor ID and source fingerprint are omitted. A Fund-attribution correction requiring manual review continues to suppress period amounts.

**Verified locally:** the focused Vehicle Sale API test passed on disposable PostgreSQL with fresh migrations, including current and stale portal snapshot behavior, private-field omission, and no additional cash movement. The portal and API test files passed 29 React tests, and `npx tsc --noEmit` passed. Authenticated browser reload, CI, staging and production remain `UNVERIFIED`.

**Checkpoint as of 2026-11-19 (superseded):** the items listed here were still incomplete at that date. See the Phase 8 closeout below for the verified current state.


### Confirmed follow-up decisions and current implementation

An authorized Loss offset may use any current, unpaid Profit of the same Investor, including an earlier or same-day Sale; it remains subject to Company/Branch authorization, current source checks and remaining balances. The offset is a separate non-cash record. Migration `0029_loss_offset_profit_dates` removes the old Sale-date ordering restriction while retaining the other database guards.

The user confirmed that only the Company-level Accountant may confirm Investor principal and Company Running Capital recovery from an actual Buyer receipt. That authorization is implemented with source-linked recovery records and correction/refund review; see the Phase 8 closeout below.

A Loss offset whose linked confirmed source is no longer current remains retained for audit but is excluded from both Accountant and Investor period calculations; the calculation is marked for review until the stale link is resolved.

## Phase 8 closeout — 2026-11-20

Verified local implementation covers source-linked Investor principal and Company Running Capital recovery, credit-lot allocations and refund reserves; current Investor period reconciliation and signed payable/recoverable positions with partial repayment/future-Profit adjustments; Company Exit principal, residual Loss and remaining Profit settlement with audited closure; Company period confirmation, negative carryforward, protected Owner split snapshots and partial Accounting payouts. The Accountant-controlled mixed-funded refund reserve and actual refund split remain explicit per-case inputs. Exit waivers remain unimplemented because their policy is open; closure requires balances to be cleared.

The Reconciliation & Settlement route now opens the implemented Investor period/Exit workspace. Owner payout uses the distinct `OWNER_DISTRIBUTION_PAYMENT` cash event, so it is visible in Accounting without becoming Company Income or Expense. PostgreSQL guards bind its event, exact outflow, allocation, module state and audit record.

**Verification:** a fresh disposable-PostgreSQL migration run and focused Owner payout test passed; `manage.py check` and `makemigrations accounting investment vehicles --check --dry-run --skip-checks` passed. One consolidated PostgreSQL batch discovered 112 tests: 110 passed; its two failures exposed an incorrect sign when reducing negative recoverable balances. The calculation was corrected and both affected PostgreSQL tests passed on rerun. React focused test groups passed (14/14, 27/27 and 27/27); `npx tsc --noEmit`, focused ESLint and `npm run build` passed. The build retains the existing >500 KB main-chunk warning. No authenticated browser, CI, staging, production, commit, push or deployment was performed.

Phase 9 consolidated browser acceptance and Phase 10 Investor Portal IDOR/reload verification remain out of scope for this Phase 8 closeout. Older dated checkpoints above describe their observation dates and are not current status.
