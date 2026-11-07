# Phase 4 — Company Accounting Foundation: Deep Architecture Plan

**Status:** PHASE_4_CODE_ARCHITECTURE_READY_FOR_IMPLEMENTATION
**Mode:** Plan only. No Phase 4 application code or schema has been implemented.
**Repository baseline inspected:** D:/VIRMS/tmp/audit-consolidation-20261102, branch codex/audit, commit 73797b16aa35db776b5601fe1483c2be8de6c100.
**Finding:** No Phase 4-specific architecture plan was found. This file is the first Phase 4 architecture draft.

## 1. Executive summary

Phase 4 establishes the smallest Company-scoped Accounting backend that can preserve classified financial records and link future source events without counting one economic event twice. It reuses the current Django/DRF modular monolith and existing React Accounting screens. It does not create a generic ERP, double-entry accounting engine, or speculative Investment, Vehicle, Garage, Sales, Inventory, Payroll, Tax, or Owner Distribution workflows.

V2 requires Company Income, Company Expense, actual Receipt, and actual Payment records with Company ownership, optional Branch attribution, source, actor, time, and history. V2 leaves Company distributable-Profit basis, period close/carryforward, and recognition of Company Share, Garage Revenue, and common Expenses unresolved. Those calculations and Owner Distribution stay blocked until the user supplies the missing business rules.

The user has confirmed that the Accountant is the primary role for manually adding Company Income and Expenses. Accountant-created standalone entries require a description and source reference. Only Company-level Accountants may manage Company Cash/Bank accounts or post across Branches; Branch Accountants stay within their assigned Branch. Owner posting access is deferred for a later decision.

**Readiness:** The bounded business and technical contract is now locked: Other Income creates Income only; Receipt and Payment are separate, linked actual-money events; partial/multiple applications are allowed; applications above Income/Expense outstanding amounts are rejected; corrections preserve actual cash events and reallocate their applications through append-only history; negative account balances are allowed; account archive requires a zero balance; categories are Company-wide; and Company/Branch Accountant scopes are defined. Initial category labels are intentionally deferred, so there are no automatic seed labels and the Company Accountant creates active categories before posting. Before implementation, reconcile the now-resolved Company-level cross-Branch correction rule in `docs-final-v2/02-user-roles-permissions.md` and review the concrete UI controls flagged `UI_CHANGE_REQUIRED`. This status means the architecture is ready; it does not authorize application-code implementation. Profit recognition, period close, carryforward, Owner Distribution, and Owner posting remain outside this bounded implementation.

## 2. Sources inspected and evidence boundary

### Verified from repository

- Current backend apps are apps.accounts, apps.tenants, apps.common, and core. No Accounting app, model, serializer, service, URL, or migration exists.
- Shared persistent records use the UUID/timestamp base in apps/common/models/base.py. Company is apps.tenants.Tenant; Branch belongs to a Company and is a distinct operational attribution.
- DRF defaults to core.permissions.DenyByDefault. Existing apps.accounts.policy.require_action denies calls that pass a module argument and has no Accounting business actions. Phase 3 module-state metadata is not itself business-action authorization.
- React has Accounting views, forms, selectors, and summary widgets. Expense, Payment, and OtherIncomeReceipt are held in the shared in-memory Data object; form handlers directly mutate that object. These flows do not persist to Accounting APIs.
- Existing React entry points include FinancialLedgerView, CompanyResultView, SharedFormModal, and DashboardFinancialView. Preserve their product UI.
- codex/audit has pre-existing local documentation edits from the preceding task. Preserve them. The separate D:/VIRMS staging worktree is dirty and is outside this document's write target.

### Verified from current V2 documents

- docs-final-v2/09-company-accounting-owner-distribution.md owns Accounting behavior. Documents 01, 02, 04, 06, and the roadmap define business and engineering boundaries.
- Company is the ledger owner across its Branches. Branch records attribution; it is not another ledger-owning Company.
- Accounting owns actual Company receipts/payments and the accounting representation of recognized income/expense. Garage, Sales, and Investment own their operational/source records and link Accounting events rather than create duplicate amounts.
- The bounded accounting scope supports Vehicle resale and Garage operations. Cash/Bank basics and receivables are included where relevant; supplier payables, advanced inventory, and full tax/ERP suites are not mandatory.
- Financial events require fixed-precision money, history, authorization, atomic writes, duplicate protection, and linked corrections. A suggestion, reminder, or calculation is not an actual financial event.
- Phase 4 is NOT STARTED. Foundational work may proceed while distributable-Profit basis and period close/carryforward remain unresolved.

### Not verified

No staging/production database, deployed role, live API, or production data was inspected. The local Docker database used for the prior app run is a development database with a superuser role; it is not evidence of deployment permissions.

## 3. Goal, scope, and exit boundary

### Goal

Create and verify the Company Accounting persistence and API boundary so approved records are written once, read only within authorized Company/Branch scope, and referenced by later modules.

### Phase 4 includes

- A separate apps.accounting Django domain module, subject to final boundary review.
- Company-owned accounting records with Branch attribution under the existing Tenant/Branch identities.
- Backend validation and default-deny authorization for approved Phase 4 actions.
- Actual income/expense and receipt/payment records only where their recognition/source semantics are settled.
- Named Company Cash/Bank accounts, date/reasoned opening balances, and linked internal transfers with derived balances.
- Accountant-managed Company Income/Expense categories that archive instead of deleting history.
- Company/Branch read projections and React query/service integration for existing Accounting views.
- Immutable financial history and a linked correction path for only the correction cases whose meaning is approved.
- Tenant/Branch isolation, posting-limit, duplicate-request, transaction, failure, migration, and compatibility tests.

### Phase 4 excludes

- Vehicle, Investor/Fund, Running Capital contribution/recovery, Garage Job, Sales, Buyer collection/refund, Inventory, payroll, CRM, and full ERP implementations. Those modules remain future source owners.
- Final Company Profit, distributable Profit, period close/carryforward, Owner allocation/payment, automatic Loss treatment, or Owner posting access.
- Any change to approved React layout, route identity, navigation structure, component hierarchy, or visual design.

### Exit condition

An approved accounting record has one Company identity and no more than one Branch attribution, is authorized and persisted once, preserves source/history, and appears consistently in authorized Accounting views. No unresolved Profit/period rule is treated as decided.

## 4. Ownership and module boundaries

| Concern | Owner | Phase 4 boundary |
|---|---|---|
| Company identity and membership | apps.tenants / apps.accounts | Reuse Tenant UUID, membership, grants, Branch assignments, and scope selectors. Do not duplicate identity or ownership tables. |
| Accounting records and read models | Proposed apps.accounting | Own classified Company accounting records and source links; do not own Vehicle, Job, Sale, Investor, or Buyer records. |
| Actual receipt/payment identity | Accounting | One canonical persisted event identity. Later source modules reference it; they do not keep an independent mutable copy of the amount. |
| Cash/Bank account identity and balance | Accounting | Company-level Accountant manages named Company accounts and sees consolidated balances. Branch Accountant sees only movement data for their Branch, not Company account balances. Opening balances and transfers are separate immutable events. |
| Income/Expense categories | Accounting | Company-level Accountant manages one Company-scoped list; Branch Accountants use but cannot change the shared list; removal means archive. Initial seed labels are deferred; do not invent them. Used categories cannot be hard-deleted. |
| Operational source event | Its future owning module | Investment, Garage, and Sales create their own source records and link Accounting events through explicit reviewed relationships. |
| Company module availability | Phase 3 module-state foundation | Accounting writes require the Company accounting module to be enabled. History reads remain scoped and do not imply mutation permission. |
| Audit/history | Existing account audit boundary plus Accounting event history | Store actor, Company, Branch attribution, and reason where required in the same transaction as the consequential write. |

A Company or Branch selector is not authorization. Resolve current Company membership and Branch scope on the backend for every query and mutation.

### Reuse of current role and scope identities

Do not add separate `COMPANY_ACCOUNTANT` and `BRANCH_ACCOUNTANT` role codes. The current identity model has `CompanyRoleGrant.Role.ACCOUNTANT`; an active Accountant grant with `branch_id = null` is Company-wide, while a Branch-bound Accountant grant is Branch-scoped and must also have the matching active `BranchAssignment`. The current generic `require_action` checks `BranchAssignment` whenever a Branch is selected, even if a Company-wide grant exists. The Phase 4 Accounting action policy must explicitly let a Company-wide Accountant act across all Branches in the same Company, as now approved, while preserving the old assignment requirement for every existing non-Accounting action. Branch-bound grants authorize only their specific assigned Branch. Never derive authority from the selected Branch or frontend context. Company Accountant access to another Branch's confirmed record means linked, reasoned correction history, not direct overwrite.

## 5. Proposed persistence boundary

V2 requires four distinct meanings: Company Income, Company Expense, actual Receipt, and actual Payment. The Phase 4 boundary also includes named Cash/Bank accounts, opening balance movements, and internal account transfers. It does not settle cash-versus-accrual recognition, so a receipt never automatically creates recognised Income.

In plain terms, Income/Expense classify the Company's financial result; Receipt/Payment record money actually received/paid. A customer charge is not a Receipt, and an Expense may exist before its Payment. A Receipt does not automatically create recognized Income until the applicable recognition rule is approved. They are record types within the same Company Accounting module, not separate Garage and Investor accounting systems.

The implementation uses one narrow event-and-movement design, not a general ERP journal:

| Record | Required meaning and constraints |
|---|---|
| `AccountingAccount` | UUID; Company FK; type `CASH` or `BANK`; operator label; active/archive state; created/archived timestamps and actor references. Only Company-level Accountant may create/archive. Its balance is always derived from movement legs. One active normalized label per Company/type. |
| `AccountingCategory` | UUID; Company FK; `INCOME` or `EXPENSE` kind; label; active/archive state; created/archived timestamps and actor references. Company-level Accountant creates/archives; Branch Accountants use the shared list. A record references a category with `PROTECT`; archive prevents new use and preserves history. Initial labels are not seeded until supplied. |
| `AccountingEvent` | UUID; Company FK; optional Branch FK; event kind `INCOME`, `EXPENSE`, `RECEIPT`, `PAYMENT`, `OPENING_BALANCE`, or `TRANSFER`; positive INR decimal; `effect_sign` `+1` for an original/replacement or `-1` for a reversal; nullable protected self-FKs `reversal_of` and `replaces_event`; correction reason on reversal/replacement; effective/recorded time, actor, required description/source reference, and category only for Income/Expense. Receipt/Payment is an actual money event; its relationship to Income/Expense is stored separately in `AccountingApplication`, not by mutating the event. A corrected replacement has the same event kind, points to the event it replaces, and is the sole current successor; reversal and replacement are separate immutable rows. |
| `AccountMovement` | UUID; protected Event FK and Account FK; signed fixed-precision delta. Receipt and opening balance create one positive movement, Payment one negative movement, and Transfer exactly two equal/opposite movements. Income/Expense do not move cash merely because they are classified. Enforce one movement per `(event_id, account_id)`; service validation enforces the required one-leg or two-leg event shape. |
| `AccountingApplication` | UUID; Company FK; source-event FK (`RECEIPT` or `PAYMENT`); target-event FK (`INCOME` or `EXPENSE`); positive INR amount; `effect_sign` `+1` for an active application or `-1` to reverse a prior application; protected self-FK `reversal_of`; actor, timestamp and reason for reallocation. A Receipt applies to exactly one Income; a Payment applies to exactly one Expense. One Income/Expense can receive multiple partial Receipt/Payment events. Reallocation is append-only and changes no Cash/Bank movement. |
| `AccountingIdempotencyRecord` | Company FK; actor FK; client key; method/path; canonical request hash; completed HTTP result. Unique `(company, actor, key)`; same key cannot represent another path or body. Retain with its financial record history. |

- A standalone Income/Expense is permitted for an authorised Accountant with mandatory description and source reference. It may later be explicitly linked to a Garage, Sales, or Investment source; it is never silently converted into a new source-owned record.
- An opening balance is a dated, reasoned event against exactly one named Cash/Bank account. It changes only that account balance; it is neither Income nor Expense.
- An internal transfer has exactly one source and one destination account in the same Company, must use different accounts, and must be committed with both movement legs atomically. It is neither Income nor Expense.
- Keep recognised Income/Expense distinct from actual Receipt/Payment. Never infer one from another until recognition rules are approved.
- Persist an explicit source relationship when the owning source model exists. Do not add a free-form polymorphic source ID with no FK or integrity check merely to anticipate Phase 5–7 models.
- Do not store editable aggregate balances or hardcoded dashboard totals. Derive account balance as the sum of that account's committed signed movements through the requested `effective_at`; derive classified Company/Branch result only from Income and Expense events (`effect_sign × amount`, Income positive and Expense negative). Receipt, Payment, Opening Balance, and Transfer never enter that result merely because they move money. Apply Company/Branch authorization before aggregating.
- Preserve confirmed records. Corrections append a reversal event that retains the original kind/amount/source/Branch/account and points to the original, plus an optional corrected replacement event. Reversals have the opposite effect; the original is never rewritten or deleted.
- Store money as INR fixed-precision decimal with two fractional digits. API amounts are decimal strings; JavaScript floating-point values are never authoritative.

### Database constraints and query indexes

- `AccountingAccount`: protected Company FK; `account_type` check is `CASH` or `BANK`; archive is a state transition, not deletion; unique active normalized `(company_id, account_type, label)`.
- `AccountingCategory`: protected Company FK; `kind` check is `INCOME` or `EXPENSE`; protected referenced rows; unique active normalized `(company_id, kind, label)`.
- `AccountingEvent`: positive amount check; INR only; required source/description; protected Company, Branch, category, and actor references. Services validate that `branch.tenant_id == company_id` and category belongs to the same Company. Branch membership in the URL is never accepted as record ownership.
- `AccountingEvent` correction links: a reversal points to one original event and has `effect_sign=-1`; a replacement points to the event it supersedes and has `effect_sign=+1` and the same event kind. Partial unique constraints allow at most one full reversal and one replacement per source event. Net correction-chain amount is the sum of each event amount times its effect sign; the chain produces one current economic Income/Expense, not an original plus a second Expense.
- `AccountingApplication`: positive amount; same-Company source/target; only Receipt → Income and Payment → Expense; reject self-links, reversed targets, wrong event kinds, and cross-Company links. Branch-crossing is authorized only for Company-level Accountant; Branch-scoped actors must use source/target/events in their own Branch. Services enforce one current target per cash event and allocated amount equal to that Receipt/Payment amount. Neither Receipt nor Payment applications may exceed the target's current outstanding amount. Reversal rows must point to an unreversed original application and preserve its source/target/amount.
- `AccountMovement`: nonzero fixed-precision delta; protected event and account references; unique `(event_id, account_id)`; services enforce one leg for Receipt/Payment/Opening Balance and exactly two equal/opposite legs on distinct same-Company accounts for Transfer.
- `AccountingIdempotencyRecord`: unique `(company_id, actor_id, key)`; canonical request hash includes method and relative path; key/status/result are retained with history. Do not apply a short TTL to financial commands.
- `AccountingApplication`: unique at-most-one full reversal per application; index by `(company_id, target_event_id, id)` and `(company_id, source_event_id, id)` for outstanding and reallocation queries. Cross-row net-allocation rules are enforced in locked domain commands and concurrency tests.
- Index event lists by `(company_id, effective_at DESC, id)` and `(company_id, branch_id, effective_at DESC, id)`; add `(company_id, event_type, effective_at DESC)` and `(company_id, category_id, effective_at DESC)` where query plans justify. Index movement lookup by `(account_id, event_id)`.
- Receipt/source-reference uniqueness is source-specific. Garage's later receipt integration must enforce its approved Company-wide unique external reference without imposing a false unique rule on all unrelated Company receipts.

## 6. API, service, and permission boundary

### API contract

Mount under the existing Company-scoped route pattern: `/api/v1/tenants/{company_id}/accounting/`. The path's `company_id` is a selector, never authority; resolve it through the current authenticated Company membership for every request. Use the existing session/CSRF authentication, `IsAuthenticated`, default-deny permissions, request IDs, and DRF page pagination (20 rows by default). List responses retain DRF's `{count, next, previous, results}` shape. Use snake_case fields to match current backend responses.

All mutating requests require `Idempotency-Key`, distinct from `X-Request-ID`. The frontend creates one key per user intent and reuses it for retries. A database unique constraint claims the key within Company and actor scope with a hash of the method, path, and canonical request body, and stores the completed response. Same key, path, and body replays the prior response; reuse for a different method/path/body returns `409`. A concurrent duplicate is serialized on the unique key; it replays the completed response or returns `409` on bounded database lock timeout. Do not rely on client-side disabling or `X-Request-ID` as duplicate protection.

| Method and path | Request and behavior | Scope and response |
|---|---|---|
| `GET /accounts/` | Query `page`; return `{id, account_type, label, is_active}`. Include signed computed `current_balance` (which may be negative) and `balance_as_of` for Company-level Accountant and Owner with Company-wide read scope. Branch-scoped Accountant/Owner may see active account label/type needed to record or review their Branch movements, never total Company balance. | Paginated DRF shape; read scope follows Company/Branch grant. Owner is read-only. |
| `POST /accounts/` | `{account_type: "CASH" or "BANK", label}`. Opening amount is a separate event. | Company-level Accountant only; `201` with server UUID/timestamps. |
| `PATCH /accounts/{account_id}/` | `{is_active: false}` archives. No hard delete or label rename in this slice. | Company-level Accountant only; `200` only when the serialized current balance is exactly zero; otherwise `409 ACCOUNT_BALANCE_NONZERO`. Historic movements remain readable; archived account cannot receive new movements. |
| `GET /categories/` | Query `page`; return `{id, kind, label, is_active}`. | Company-wide list. Authorized Owner/Accountant may read within Company/Branch scope; Branch Accountants can select active shared categories. Paginated. |
| `POST /categories/` | `{kind: "INCOME" or "EXPENSE", label}`. | Company-level Accountant only; `201`. Active normalized label unique per Company and kind. |
| `PATCH /categories/{category_id}/` | `{is_active: false}` archives. | Company-level Accountant only; `200`. Used categories remain attached to old events and are not hard-deleted. |
| `GET /events/` | Filters `event_type`, `branch_id`, `category_id`, `account_id`, `effective_after`, `effective_before`, `page`. Return event type, amount, Branch, category/account references, source/description, actor and timestamps. | Company-level may query all or filter any Branch. Branch-level is forced to its assigned Branch; attempts to request another Branch fail closed. Paginated. |
| `GET /events/{event_id}/` | Return event details and linked correction/movement references. | Same Company/Branch scope as list. Out-of-scope and absent UUIDs return indistinguishable `404`. |
| `POST /incomes/`, `POST /expenses/` | `{amount, effective_at?, branch_id?, category_id, description, source_reference}`. Amount is an INR decimal string with two fractional digits. When the preserved form has no effective-date input, the server assigns timezone-aware current time; a retry with the same idempotency key replays the committed event and timestamp. | Accountant. Company-level may choose a Branch or `null`; Branch-level is forced to an explicitly granted Branch. `201` confirmed event. |
| `POST /receipts/`, `POST /payments/` | Receipt: `{amount, effective_at, branch_id?, account_id, income_event_id, description, source_reference}`. Payment: `{amount, effective_at, branch_id?, account_id, expense_event_id, description, source_reference}`. Each command creates one immutable AccountingEvent, one AccountMovement and one AccountingApplication in the same transaction. Each applies to one target; an Income/Expense may have multiple partial Receipts/Payments. An amount above the current target balance returns `409 ACCOUNTING_TARGET_BALANCE_EXCEEDED`. The selected named Cash/Bank account identifies which balance changes; no separate payment-method field is required. | Same role/Branch rule. `account_id` must identify an active account in this Company. `201` confirmed event. |
| `POST /opening-balances/` | `{account_id, amount, effective_at, reason, source_reference}`; creates the account's dated opening movement, separate from Income. | Company-level Accountant only; one initial opening event per account, with a correction path that preserves the original. `201`. |
| `POST /transfers/` | `{from_account_id, to_account_id, amount, effective_at, reason, source_reference}`; atomically creates equal/opposite movements. | Company-level Accountant only; both active accounts must belong to this Company and be different. `201`. |
| `POST /events/{event_id}/corrections/` | `{reason, replacement?: <same-event-kind replacement>}`; atomically preserves the original and creates a linked full reversal, plus a corrected replacement when supplied. Persist `reversal_of` and `replaces_event` IDs so history can be reconstructed without inferring from timestamps. If an Income or Expense has active applications, a replacement of the same kind is required; preserve each actual Receipt/Payment and Cash/Bank movement, append reversals for old applications and new applications to the replacement. Reject when the replacement amount cannot cover all reallocated applications. This produces one net current Income/Expense position, not a second economic event. Opening Balance requires its account; Transfer requires distinct same-Company source/destination accounts. A replacement cannot change the original event kind. | Originating Branch Accountant may correct only own Branch records; Company-level Accountant may correct any Company record. `201` returns correction/reversal and optional replacement IDs with the original ID. |

Event responses use a common snake_case envelope `{id, company_id, branch_id, event_type, amount, currency: "INR", category_id?, application_ids?, description, source_reference, effective_at, recorded_at, actor_id, effect_sign, reversal_of_id?, replaces_event_id?}` plus kind-specific movement references: `account_id` for Receipt/Payment/Opening Balance and `from_account_id`/`to_account_id` for Transfer. Event detail includes immutable correction/application history and derived `outstanding_amount` for current Income/Expense records where authorized. Inapplicable references are omitted or null consistently. Accounts and categories return their UUID and timestamps. Never accept `company_id`, `actor_id`, correction links, `effect_sign`, movement delta, or derived balance from the client. No endpoint finalizes Company Profit or a period.

Errors follow the existing API shape `{detail, code, request_id, errors?}`. Use `400` for invalid input, `401` for unauthenticated, `403` for authenticated but unauthorized actions, `404` for absent/out-of-scope UUIDs, `409` for idempotency/state conflicts, and sanitized `500` for unexpected failures. Financial reads and writes set `Cache-Control: private, no-store`; preserve `X-Request-ID`.

Serializer validation delegates writes to domain commands/services. Views do not write ORM records directly. Return success only after commit. Extend the React API client with `PATCH` and a stable idempotency key per mutation intent; its existing request ID remains a trace ID.

### Authorization

Use a finite action allowlist through an Accounting-specific permission boundary integrated with the existing `apps.accounts.policy` contract: `accounting.event.read`, `accounting.income.create`, `accounting.expense.create`, `accounting.receipt.create`, `accounting.payment.create`, `accounting.event.correct`, `accounting.account.manage`, `accounting.category.manage`, `accounting.opening_balance.create`, and `accounting.transfer.create`. Do not add a wildcard Accounting permission. Read actions require an authorized Owner/Accountant Company or Branch grant. Ordinary writes require Accountant scope; account/category management, opening balance, and transfer require a Company-wide Accountant grant. Each write also checks the latest Company `accounting` module state at the command boundary; OFF/UNCONFIGURED denies new writes, while authorized history remains readable. The current `require_action(module=...)` rejection must not be bypassed: add explicit tested support for these actions and module-state enforcement at the narrowest existing policy/service boundary.

Financial business truth belongs in immutable `AccountingEvent` and `AccountMovement` history, not `AccountSecurityEvent`. Account/category create/archive actions retain their actor and timestamps on the non-deletable rows; no rename or unarchive path is included in this slice.

This narrow scope exception is a shared-authorization change: regression-test existing Phase 1–3 actions to prove they still require their prior Branch assignments and that the Company-wide bypass applies only to the explicit Accounting action allowlist.

- A Company-level Accountant may create/read/correct authorised records for any Branch in their Company and Company-wide records.
- A Branch-level Accountant may create/read/correct only records attributed to their assigned Branch. They cannot create Company-wide records or access another Branch.
- A Company-level Accountant may manage named Company Cash/Bank accounts, opening-balance entries, internal transfers, and the shared Company category catalogue.
- A Branch-level Accountant sees only movement data attributed to their assigned Branch; they do not receive a Company's consolidated Cash/Bank account balance.
- A correction/reversal follows the original record's Branch scope: the originating Branch Accountant may correct its own Branch record; a Company-level Accountant may correct any Company record. “Edit” of a confirmed record means create a linked reasoned correction/reversal; it never silently overwrites or deletes the confirmed history.
- Accountant/Operations is the primary role for approved manual Company Income/Expense entries and may perform only actions allowed by current Company, Branch, module, and object scope.
- Owner posting access remains deferred for a later business decision; current V2 provides Owner read visibility and does not authorize Owner financial posting.
- Platform Back Office configuration authority does not grant routine financial posting/confirmation.
- Investor and Media have no Accounting mutation authority.
- Unknown actions, disabled modules, stale scope, unassigned Branches, cross-Company objects, and unsupported record types fail closed.
- Add explicit Accounting actions through a reviewed policy boundary. Do not bypass `require_action` or assume module-state metadata already enforces business actions.
- Only a Company-level Accountant may create/archive shared Company categories. Archive prevents new use but never removes a used category or rewrites historical labels.
- Only a Company-level Accountant may create/archive named Cash/Bank accounts, post opening balances, or make internal transfers. These Company-level movements remain visible to the Company-level role.
- Branch-level Accountants may post Receipt/Payment events within their Branch using available Company accounts. The linked Income/Expense and cash event must also be within that same Branch for a Branch-scoped actor. Read results expose only Branch-attributed movements, not consolidated account balances.

## 7. Transaction, duplicate, and history rules

- Each consequential Accounting mutation and audit/history record commit in one database transaction.
- Validate Company/Branch relationships in services and database constraints where expressible.
- A retried command cannot create a second economic event. Use the persisted request idempotency record; same key/path/body replays, while a changed key scope or payload conflicts.
- A Receipt/Payment and its AccountMovement and AccountingApplication commit together. Application rows are append-only. Reallocation is a negative reversal row for the old application and a positive row for the replacement target; it changes no actual cash movement.
- Transfer posting locks both named accounts in deterministic UUID order and writes both legs in one transaction. Negative Cash/Bank balances are allowed, so insufficient balance never blocks a Payment or Transfer. An account balance is a sum of committed movement legs, never an editable field.
- Receipt posting locks the target Income, validates `receipt.amount <= income.outstanding_amount`, locks the active Cash/Bank account, and writes the Receipt event, positive movement, application, audit and idempotency result atomically. Concurrent Receipts against the same Income serialize on that Income row.
- Payment posting locks the target Expense, rejects a Payment above its remaining Expense amount, locks the Cash/Bank account, and writes the Payment event, negative movement, application, audit and idempotency result atomically. The account balance itself may go negative; this does not permit payment above the target Expense.
- Income or Expense correction with active applications locks the original/replacement target and all affected Receipt/Payment/application rows in stable UUID order. The transaction reverses the old Income/Expense, creates the corrected replacement, reverses old applications, creates new applications, and leaves actual Receipt/Payment events and Cash/Bank movement rows untouched. The replacement must cover all reallocated applications. Event-effect aggregation returns one net current business amount; no second cost/revenue is counted. Failure rolls back the entire correction.
- Account archive locks its account row and recomputes the signed balance in the same transaction; archive is denied unless that balance is exactly zero. This prevents a concurrent Payment/Transfer from passing the zero-balance check and then posting to an archived account.
- Transfer and opening-balance commands require Company-level Accountant scope because both alter a Company-owned account balance without belonging to one Branch's operational ledger.
- Opening balance creates one immutable, reasoned event; correcting it uses a linked adjustment/reversal, not balance overwrite.
- When consuming an outstanding position, lock the authoritative Income/Expense row and re-check the current amount and net applications inside the transaction. Do not use frontend totals for caps.
- Use PostgreSQL TransactionTestCase and independent connections for concurrency-sensitive posting tests.
- Never silently update/delete a confirmed record. A correction atomically inserts its reversal and optional replacement. A reversal uses the original event kind and amount with `effect_sign=-1`; a replacement has `effect_sign=+1`, the same event kind, and a persisted `replaces_event` link. Net effect across that correction chain counts one current economic record. A valid receipt refund is a distinct future business event, not a correction.
- `AccountingApplication` is also append-only. Reallocation appends a negative application that references the old application plus a positive application targeting the replacement; it has no cash effect and never changes the Receipt/Payment event.
- No period close, settlement, or payment is created from a calculation, reminder, import, or browser success state.

## 8. React integration and existing UI contract

Current React types include Expense, Payment, and OtherIncomeReceipt. The shared Data collection and selectors feed Company Income, Company Expenses, Garage Revenue, Company Result, Financial Ledger, and dashboard widgets. SharedFormModal currently inserts these records into local memory.

The current Company Expense form maps to one Company Expense record only. The current Other Income form maps to one Company Income record only; submit does not create a Receipt, even if its legacy `method` field has a value. The Income form needs the approved category and source/description. Actual Receipt is a separate event when money arrives, applies to that Income, and names the Cash/Bank account. The legacy method control must not imply or post a Receipt; replace it in the same form area with the category selector while preserving route and overall layout. The current `customerReceipt` form is Garage Job-specific and must not be reused as the standalone Income Receipt without a reviewed contract. Company Payment is a separate actual outflow linked to one Expense; it may be partial and an Expense may have multiple Payments.

Integration plan:

1. Keep existing routes, component hierarchy, layout, responsive behavior, and form presentation; replace only controls whose current meaning conflicts with the approved contract.
2. Map each approved form submit to a typed Accounting service request. Show success only after the API confirms commit.
3. Use the shared authenticated API client and Company-bound query cache. Query keys include authenticated user and Company; include Branch/filter dimensions where response scope requires them.
4. Invalidate or update only affected queries after success. Do not maintain a second mutable business-data store in parallel.
5. Convert Accounting views and KPI selectors to one canonical query/selector contract. Profit/result summaries remain blocked or expose only approved component totals until recognition rules are answered.
6. Remove a DEMO badge only for a flow whose backend read and mutation are implemented and verified. Badge changes report integration state; they do not change layout.

### UI approval boundary

The repository currently has no standalone Company Income Receipt or Expense Payment form, named Cash/Bank account maintenance, opening-balance, transfer, or dynamic Company category-management flow. The Company Expense form also lacks a source-reference and dynamic-category input. Phase 4 therefore needs minimal Accounting actions/forms in the existing Accounting surface. Required controls include distinct `Record Receipt` and `Record Payment` actions tied to Income/Expense, account selection, opening-balance/transfer actions, account/category management, and required Expense source/category inputs. Preserve routes and page composition; do not reuse the Garage Job Receipt flow. Mark these additions and replacement of the Other Income `method` control with a category selector `UI_CHANGE_REQUIRED`; review the concrete interaction before changing React. This is a functional control addition, not permission to redesign Accounting pages.

### Current-form mapping and identity caveats

| Existing UI value | Target contract | Safe mapping |
|---|---|---|
| `otherIncomeReceipts[]` record | Accounting `INCOME` event | Migrate this collection's meaning to Income only; never create a Receipt from it. Actual Receipt has a separate command and account movement. |
| `expenses[]` record with `category === 'Company'` | Accounting `EXPENSE` event | Map only records written by the Company Expense form. Vehicle/job cost records (`category === 'Vehicle'`, `investor`, `capital`, `jobId`) remain owned by their future source module and must not be duplicated as Company Expense. |
| Mock `id` / `actor` | Server UUID / authenticated actor | Ignore mock timestamp IDs and labels such as `inc-*` or `Accountant`; backend assigns stable identity and authenticated actor. Do not backfill prototype IDs as persisted records. |
| `source` / `description` | `source_reference` / `description` | Both are required backend inputs; do not keep the current handler's `Operational` fallback as a successful source. |
| Company Expense `description` / missing source field | `description` / `source_reference` | Preserve description; add the approved required source-reference input before API submission. |
| Company Expense `date` | `effective_at` | Current backend uses Django `TIME_ZONE = UTC` and `USE_TZ = True`; convert the existing date-only input to UTC midnight and retain server `recorded_at`. No Company-specific timezone field currently exists. |
| Company Expense `category === 'Company'` / hidden `costType` | Company `category_id` | The present Company expense handler writes `category='Company'`; its hidden default `costType` is not a dynamic Accounting category. Select an active Company `EXPENSE` category from the backend catalogue. Do not map Vehicle `costType` to the Company ledger. |
| `amount` JavaScript number | Decimal string | Convert from the form string to validated INR decimal text; do not use binary floating point for authoritative calculations. |
| `method` (`Cash`, `UPI`, `Bank transfer`) | No field on Income | Do not send this legacy Receipt-like control for Income. Use the approved category selector in the same existing form region; do not imply cash was received. |
| `garageId` / `Garage.id` (`g-1`, etc.) | Company Branch UUID | These are local mock Garage IDs, not verified backend Branch identities. Resolve the selected Branch from authenticated Company/Branch context and API data; never submit or map the mock string as a Branch UUID. Keep the existing field presentation and label where possible. |
| Existing `timestamp` display string | Server `effective_at` and `recorded_at` | The Other Income form has no effective-date input. Let the backend assign current timezone-aware `effective_at` and `recorded_at`; do not parse the UI display timestamp as authority. |
| Shared `Data.payments[]` | No bulk Phase 4 mapping | It currently mixes buyer, Job/customer, capital, and other source-specific movements. Do not copy the collection into Company Payment; each source owner must integrate its own canonical event in its roadmap phase. |

The Company-wide Accountant may attribute an entry to any Branch in the Company or leave it Company-wide where permitted. A Branch Accountant's API command must be bound to an active granted Branch, regardless of the selected UI context. Negative account balances are allowed, and an account with any nonzero current balance cannot be archived; these checks belong in backend commands, not frontend logic.

## 9. Migration and compatibility plan

1. Apply the accepted Phase 1–3 `accounts`, `tenants`, and `common` migrations first; add an Accounting app without replacing their initial migrations.
2. Add Accounting account/category/event tables with protected FKs to existing Company, Branch, and User identities.
3. Add dependent movement, application, and idempotency tables, then their uniqueness/check constraints and query indexes. Keep this order in one additive initial migration if no rollout need requires intermediate states.
4. Add no mock-data backfill. Prototype IDs and local records are not canonical finance history.
5. Apply and reverse-test migrations on isolated disposable PostgreSQL; verify fresh install, upgrade from Phase 3 schema, constraints, and protected rollback behavior.
6. Preserve Phase 1 account/Company/Branch APIs, Phase 2 authentication/context, Phase 3 module-state API, and all React route identities.
7. Do not run staging/production migrations or claim deployed role safety from local checks.

## 10. Implementation slices

| Slice | Scope | Dependencies | Exit evidence |
|---|---|---|---|
| P4-00 — Decision and contract lock | Translate accepted business decisions into exact model/API schemas and event transitions; keep Profit calculations blocked. | Accepted decisions; V2 documents; repository API conventions. | Reviewed technical contract with no inferred business semantics. |
| P4-01 — Accounting authorization | Add fail-closed Accounting actions resolving Company, Branch, role, and module state without weakening core policy. | Phase 3 module-state; review current require_action behavior. | Tests cover Accountant write, Owner read-only, Platform no routine posting, and cross-Company/Branch denials. |
| P4-02 — Persistence and services | Add approved minimal models, constraints, commands/services, audit/history, and idempotency. | P4-00 and P4-01. | Service tests cover valid, invalid, retry, concurrency, correction, and rollback cases. |
| P4-03 — Read/API contracts | Add scoped list/detail and only approved create/confirm/correction actions. | P4-02. | API tests cover response contract, isolation, denied paths, and stable errors. |
| P4-04 — React data integration | Connect approved existing Accounting forms/views/selectors; remove duplicate local accounting collections per migrated flow. | P4-03 and field mapping. | Frontend data tests, reload persistence, and no false-success behavior. |
| P4-05 — Regression and phase audit | Run related Phase 1–3 regressions, migrations, React tests/build/lint, and Accounting security/data-integrity audit. | P4-01–04. | Acceptance criteria pass with no UI/route regression. |

Each slice is independently testable. Do not migrate Accounting, Vehicle, Garage, Sales, and Investment in a single release.

## 11. Test architecture

- **Model/constraint:** required Company/Branch ownership, supported type, positive amount, immutable event/application history, category archive protection, movement-leg consistency, distinct transfer accounts, valid event/application kinds, one current application target per receipt/payment, unique reversal/idempotency identity.
- **Service/domain:** authorization before persistence, atomic audit, retry, opening-balance correction, transfer atomicity, linked partial Receipt and Payment outstanding-position concurrency, over-target denial for both Receipts and Payments, audited Receipt/Payment reallocation during Income/Expense correction, negative account balances, zero-balance-only account archive under concurrent writes, source links, correction preservation, and no duplicate economic effect.
- **API:** Company scope, Company-level versus Branch-level Accountant visibility/writes, Owner/Platform roles, module OFF, cross-Company UUID denial, Branch scope, validation/errors, no-store headers.
- **React data layer:** contract parsing, user+Company query keys, scoped invalidation, failures preserve form values, no local success without API success.
- **Regression:** Phase 1 authorization/session/Company/Branch, Phase 2 auth/context, Phase 3 module-state API/query, approved routes/UI.
- **Database:** disposable PostgreSQL for constraints, transactions, concurrency, migrations, and runtime-role tests. A local superuser test DB is not deployed least-privilege evidence.
- **Acceptance:** create Income/Expense, linked partial Receipt(s)/Payment(s), named account, category, opening balance, and transfer; verify list/detail and reload persistence; prove over-target Receipt/Payment is rejected, linked correction preserves actual money events and changes only the audited application, negative derived account balances are accepted, only zero-balance accounts archive, Branch Accountant cannot see another Branch's movements or consolidated account balances, and Company-level Accountant can; reject duplicate, over-scope, malformed, and failed writes without partial state; prove balances and views use the same canonical source.

## 12. Rollback and compatibility

- Roll back application code while retaining additive tables and confirmed history.
- Do not reverse/drop accounting tables after financial records exist. Guard reversal only where empty-state reversal is explicitly proven safe.
- Keep unmigrated forms in DEMO state. Never run local and backend mutations for one event.
- If rollout fails, disable the affected integration through its existing status/config boundary and preserve records; do not erase events or alter approved UI composition.
- No commit, push, staging, production, or deployment action is part of this plan.

## 13. Files expected to change during approved implementation

Likely new backend files: apps/accounting/apps.py, models (AccountingAccount, AccountingCategory, AccountingEvent, AccountingApplication, AccountMovement, AccountingIdempotencyRecord), services or commands, selectors, serializers, views, urls, admin, migrations, and focused tests.

Likely shared backend files: core/settings.py, core/urls.py, and the narrowest safe Accounting authorization/module-state integration point in apps/accounts/policy.py or a dedicated helper. Exact changes depend on the approved permission design.

Likely React data files: demo/react/src/api, query/hooks, Accounting types/selectors, shared form submit service, and Accounting view data consumers. Preserve routes and page composition. New Company Receipt/Payment, account/category management, opening-balance, and transfer controls, plus replacing the Other Income method field and adding Expense source/category inputs, are `UI_CHANGE_REQUIRED`; review their concrete interaction and authorize those visible control changes before React implementation. Do not reuse the Job-specific Customer Receipt form for standalone Income.

Update documentation only when verified truth changes: Data Flow, API Flow, Change Impact, Phase 4 execution report, and roadmap status. Do not rewrite canonical V2 business rules without explicit business approval.

## 14. Definition of Done

- Business decisions required for implemented flows are recorded; unresolved calculations remain blocked.
- Accounting has one canonical Company-owned persisted source and explicit links to source-owned records.
- Company and Branch access are enforced by backend queries and commands.
- Confirmed records cannot be silently rewritten or deleted.
- Duplicate/retry and concurrent requests cannot create duplicate/over-limit economic events.
- React Accounting views consume the same backend query/service contract; success follows committed API success.
- Existing visual UI, routes, Phase 1–3 behavior, and role permissions remain intact.
- PostgreSQL migrations, model/service/API/frontend tests, focused regressions, build/lint, and phase audit pass in an isolated environment.
- No staging/production claim is made without separately verified evidence.

## 15. Accepted business decisions

### Accepted decisions

1. Accountant may add standalone Company Income and Company Expense records with mandatory description/source reference. Owner posting is deferred.
2. Named Cash/Bank account balances are required; balances derive from immutable events and are never manually overwritten.
3. Opening balance is a dated, reasoned special entry.
4. Linked Cash-to-Bank and Bank-to-Bank transfers are required; they must not create Income or Expense.
5. Company Income/Expense categories use one flexible Company-wide list. Company-level Accountant adds/archives; Branch Accountants use the list but cannot change it. Used categories are never hard-deleted. Initial seed labels are deferred; do not invent them, and do not add Garage/Vehicle category foreign keys.
6. Company Profit is consolidated. Branch attribution enables Branch-wise reporting; it does not create a separate Branch profit owner or ledger.
7. Company-level Accountant may view/manage records for all Company Branches and Company-wide records. Branch Accountant may view/create/correct only their assigned Branch. Confirmed records are corrected through linked reversal/adjustment history, never silently overwritten or deleted.
8. Finalised Profit, distributable Profit, period close/carryforward, and Owner Distribution remain outside Phase 4.
9. Only Company-level Accountant may create/archive named Cash/Bank accounts.
10. Branch Accountants see Branch-attributed Cash/Bank movements only; Company-level Accountants see the consolidated balances and all Branch movements.
11. The current Other Income form creates Company Income only. An actual Receipt is recorded separately when money is received; the legacy payment method does not create or imply a Receipt. Company Expense and actual Payment are separate records connected by an application; one Expense can have multiple partial Payments.
12. A standalone actual Receipt applies to exactly one Income through a separately audited application record. One Income may be received in partial amounts through multiple linked Receipt events. A Receipt cannot exceed the Income's remaining amount. Reallocating a real Receipt after Income correction never changes its cash event or Cash/Bank movement.
13. Cash/Bank balances may be negative; a Payment or Transfer is recorded even when the source account's derived balance is insufficient. No separate loan, credit, interest, or expense event is inferred from a negative balance.
14. A named Cash/Bank account may be archived only after its derived current balance reaches exactly zero. The record and movement history remain retained after archive.
15. Every actual Payment applies to exactly one Expense; one Expense may be paid in partial amounts through multiple Payments. Payment application history is separate from Cash/Bank movements, and a Payment cannot exceed the Expense's remaining balance.
16. When an Expense with actual Payments is corrected, keep the Payment events and Cash/Bank movements immutable. Reallocate their applications to the corrected replacement Expense through append-only audit records. Reject a correction whose replacement cannot cover its applied Payments; do not count a second economic Expense.

### Intentionally deferred business rules

- Owner financial posting access; the current V2 Owner read boundary remains in force.
- Cash-versus-accrual recognition, Company Profit finalization, distributable-Profit basis, period close/carryforward, and Owner Distribution.
- Any business category labels or recognition formulas not explicitly listed in V2; Accountants add/archive Company Income/Expense categories as needed.
- Initial Income and Expense category labels are deferred by the user. Do not seed labels from mock data; category-dependent posting stays unavailable until the Company Accountant creates active categories.
- Cross-Branch correction authority is approved for Phase 4 Company-level Accountants in this plan, but `docs-final-v2/02-user-roles-permissions.md` still lists it as `BUSINESS DECISION REQUIRED`; reconcile that canonical permissions text before Phase 4 implementation.

## Current V2 Business Decision Additions Referenced

- Canonical business decisions are recorded in [01 — Business Rules](../../docs-final-v2/01-business-rules.md#approved-business-decision-additions), [02 — User Roles and Permissions](../../docs-final-v2/02-user-roles-permissions.md#approved-business-decision-additions), [04 — Data Model Relationships](../../docs-final-v2/04-data-model-relationships.md#approved-business-decision-additions), and [09 — Company Accounting](../../docs-final-v2/09-company-accounting-owner-distribution.md#approved-business-decision-additions).
- This reference section does not replace earlier plan text. The canonical additions govern only the topics they explicitly resolve; unrelated approved architecture and remaining BDRs are preserved.
- Technical impact: future Phase 4 reporting consumes canonical Accounting events and retains correction history and authorization boundaries. This documentation reference does not implement or alter application code, APIs, schema, migrations, or React.

## Current V2 Business Decision Additions Referenced — 2026-11-03

- Current decisions: [01 — Business Rules](../../docs-final-v2/01-business-rules.md#approved-business-decision-additions), [02 — User Roles and Permissions](../../docs-final-v2/02-user-roles-permissions.md#approved-business-decision-additions), [04 — Data Model Relationships](../../docs-final-v2/04-data-model-relationships.md#approved-business-decision-additions), and [09 — Company Accounting](../../docs-final-v2/09-company-accounting-owner-distribution.md#approved-business-decision-additions).
- Technical impact: the Accounting OFF command must distinguish pre-existing obligations; Company reports bucket UTC instants by Asia/Kolkata calendar dates; opening movements may be negative; test-time editing applies to Income/Expense inputs and never to the computed Profit total. Once workflow validation is complete, the report is read-only, without implying period close or distributable-Profit finalization.
- This reference records current decisions but does not implement or amend earlier plan sections, code, APIs, schema, migrations, React, or UI.

## Phase 4 code contract reconciliation — 1A, 2A, 3C, 4A, 5A

**Status:** Architecture clarification for implementation planning only. This section supersedes earlier plan wording on the five named topics, including generic cash-event correction, unconditional Accounting OFF denial, and a blanket block on the bounded Accounting result. The canonical V2 additions linked above remain the business authority. Phase 4 application code, database schema, and React integration are not yet implemented.

### 1A — Correction command and immutable cash

- `POST /api/v1/tenants/{company_id}/accounting/events/{event_id}/corrections/` accepts only a confirmed current `INCOME` or `EXPENSE` event in Phase 4. Require `{reason, replacement: {amount, category_id, description, source_reference}}`; the replacement keeps the original event kind, Company, Branch attribution, and effective instant. Reject `RECEIPT`, `PAYMENT`, `OPENING_BALANCE`, and `TRANSFER` targets with a stable `409 ACCOUNTING_CORRECTION_UNSUPPORTED` response. Opening-balance correction needs its own reviewed command before activation; the earlier generic correction wording does not authorize cash-event reversal or refund.
- Within one transaction, lock the original/current Income or Expense and affected application/cash rows in stable order. Append one negative effect event for the old amount, one positive replacement, negative application rows reversing each active application, and positive rows applying the unchanged Receipt/Payment amounts to the replacement. Original and actual cash events and Cash/Bank movements are never updated or deleted. Reject a replacement smaller than the total active applications with `409 ACCOUNTING_TARGET_BALANCE_EXCEEDED`; rollback every inserted row on failure. A second correction targets the current replacement, not an older event; a unique reversal/successor constraint and idempotency key prevent duplicate effect.
- Reject correction of Company/Branch ownership or effective reporting date through this command. Both would need a separately specified correction contract. OFF permits only a correction needed to settle a pre-OFF Income/Expense obligation under the existing canonical rule; no new obligation may be created.

### 2A — Original-period restatement

- Original, reversal, and replacement Income/Expense events in one correction chain share the original `effective_at` UTC instant. New rows have their own server-assigned UTC `recorded_at`, actor, reason, and links. A report groups the signed net effect of the chain by the Asia/Kolkata calendar date of that original effective instant. Multiple later corrections continue to restate that same period; they do not add current-period Income or Expense.
- Period queries use half-open UTC bounds converted from Asia/Kolkata local midnight: monthly, H1 January 1–July 1, H2 July 1–January 1, annual January 1–January 1 of the next year. Compute H1, H2, and annual independently from authoritative events. Receipt/Payment and account movements are excluded from this Income-minus-Expense aggregation. Preserve recorded time in history and response; no period close or automatic distribution occurs.

### 3C — Version conflict with a safe commit gate

- Reuse the existing append-only `CompanyModuleState.version`; do not add a second version field. At command start record the latest `accounting` revision/version (unconfigured is version 0). Before any consequential Accounting insert, inside the same `transaction.atomic()` acquire `Tenant.objects.select_for_update()` for that Company, then reread the latest Accounting module revision. The existing module-state transition already locks that Tenant row before appending a revision. Keep this lock until the Accounting command commits.
- If the observed version changed, return `409 ACCOUNTING_MODULE_STATE_CHANGED` without an economic write; the client refreshes state and asks the operator to retry the same intent. Never silently retry a financial mutation or reuse an idempotency key with changed intent. If the version matches, enforce the current enabled state or the narrow OFF exception, then role/Branch/object checks, idempotency and financial caps, and commit. An OFF exception proves the target obligation's persisted creation time is strictly before the disabling revision's `effective_from` and that the command is a permitted Receipt, Payment, or necessary linked correction.
- Lock order for implementation: authenticated actor/session guard, Tenant row and revision check, then affected Income/Expense/account/application rows in deterministic UUID order, then writes/audit/idempotency result. A module transition that commits first makes a stale posting fail or pass only the OFF exception; a posting that holds the Tenant lock first commits before the OFF transition. Version checking without the shared final gate is insufficient. PostgreSQL independent-connection tests must force both interleavings, stale-version rejection, OFF exceptions, and no partial or duplicate writes.

### 4A — Bounded Accounting result read contract

- Add `GET /api/v1/tenants/{company_id}/accounting/reports/accounting-result/?period=monthly|h1|h2|annual&year=YYYY&month=1..12&branch_id=UUID` as a read-only projection, only after canonical Accounting events exist. `month` is required only for `monthly`; reject other invalid parameter combinations with `400`. Company-level Accountant and authorized Company-wide Owner may read all or one Company Branch; Branch-scoped readers are forced to their authorized Branch and cannot request Company totals. Apply the same module/read policy and out-of-scope response convention as other Accounting reads.
- Return `{period, year, month, branch_id, timezone: "Asia/Kolkata", starts_at, ends_before, income_amount, expense_amount, accounting_result_amount, currency: "INR", scope: "recorded_accounting_events"}` with fixed-precision decimal strings; `accounting_result_amount = income_amount - expense_amount`. The three amounts are derived from committed Accounting `INCOME` and `EXPENSE` correction chains in the selected window and scope. No separately editable Profit field, cash Receipt/Payment, Owner allocation, Investor Profit, Garage/Vehicle mock collection, or unsupported source is included. This is a bounded Accounting result; a full consolidated Company Profit label requires the separately unresolved source-recognition decisions and integrations. Empty periods return zeros with the same shape. Set private no-store headers.
- React uses one authenticated, Company/Branch/period-keyed query for this response. Current `CompanyResultView` computes cash-flow and mock-derived metrics, so it must not be relabeled as this result or fed a partial backend total while its other cards remain mock. Keep its existing presentation marked DEMO until a separate reviewed data mapping gives every displayed card a canonical source; a narrowly labeled Accounting result may be surfaced in the existing Accounting surface after its backend contract is verified. No automatic period close, settlement, or distribution.

### 5A — Existing UI control map and review gate

| Required action | Current React evidence | Smallest existing-surface placement |
|---|---|---|
| Create Income | `SharedFormModal` `otherIncome` has Branch, Source/Payer, Description, Amount, and Method; `FinancialLedgerView` has Company Income primary action. | Reuse the modal; use Source/Description for required provenance and replace the misleading Method selector with a Company category selector. Keep the existing row identity and layout. |
| Create Expense | `SharedFormModal` `companyExpense` has Branch, Description, Amount, Date; Company Expenses has a primary action. | Reuse the modal; add required source reference and category controls within the current scrollable form. |
| Record actual Receipt/Payment | Existing `customerReceipt` belongs to a Garage Job; Company Income/Expenses rows have no standalone cash action. | Add compact row actions on the existing Income/Expense registers, opening the shared modal in distinct Accounting Receipt/Payment modes with target ID, amount, account, source/reference, and date. Never route through the Job receipt mode. |
| Account/category management | No named account or Company category management flow exists. `App.tsx` currently routes `Accounting` to the Garage Revenue register, so it is not a dedicated Accounting management screen. | Candidate placement is compact secondary actions in the existing Company Income/Expenses register headers, with shared-modal styling for create/archive and account selection. Confirm the rendered placement before React work. Category management is Company Accountant only. |
| Opening balance/transfer | No corresponding controls exist. | Candidate placement is beside account management in those existing register headers; modal fields include signed opening amount/date/reason or two distinct accounts/amount/date/reason. Confirm the rendered placement before React work. Company Accountant only. |

Preserve route keys, page composition, spacing system, row/list density, and responsive behavior. Inspect the complete rendered desktop/mobile forms before implementation; present the exact control placement for review. Any placement that requires changing the approved composition remains `UI_CHANGE_REQUIRED` and waits for explicit UI approval. Backend integration replaces local Accounting mutation only for verified flows; no success state precedes API commit, and unmigrated flows retain their DEMO badge.

**Architecture exit checks:** review the selected contracts against canonical V2 and the current policy; verify correction kinds, effective-period grouping, OCC/OFF race tests, scope/report tests, and UI mapping before changing application code. Phase 4 readiness is not established by this document update alone; implementation and runtime verification remain separate gates.

## Final Phase 4 architecture lock — 2026-11-03

**Status: PHASE_4_CODE_ARCHITECTURE_READY_FOR_IMPLEMENTATION for the bounded Accounting foundation.** This section resolves the remaining contract conflicts in this draft. It is the current technical authority where earlier sections disagree; canonical V2 approved additions remain the business authority. Source recognition for Company Share, Garage Revenue, and common Expenses, plus distributable Profit, period close/carryforward, Investor Profit, and Owner Distribution remain outside this Phase 4 slice. No Phase 4 application implementation or runtime proof is asserted.

### Correction resource boundary

- The generic `/events/{id}/corrections/` route is restricted to `INCOME` and `EXPENSE` exactly as specified in 1A. Its serializer rejects all other event kinds before the domain command. A correction of an applied Income/Expense must replace the record and reallocate the unchanged cash applications atomically. The original effective instant is retained as specified in 2A.
- Opening balance uses its own `POST /opening-balances/{event_id}/corrections/` command, Company Accountant only. Input is `{reason, replacement_amount, source_reference}` where the signed replacement amount may be positive, negative, or zero. The account and original effective instant are fixed. Append a reversal event and movement with the opposite of the original signed delta. For a nonzero replacement, also append a replacement event and movement with the new signed delta; zero means reversal only, with no zero-amount event. Preserve every prior row. Lock the Tenant gate and the account, apply idempotency, and enforce one current successor or terminal reversal. `AccountingEvent.amount` is the positive absolute magnitude; the signed account effect is represented by `AccountMovement.delta`. No synthetic Income/Expense is created.
- Transfer uses its own `POST /transfers/{event_id}/reversals/` command, Company Accountant only, with `{reason, source_reference}`. Append one linked reversal event and two movement legs exactly opposite the original legs, against the same two accounts; do not delete or edit the original. Reversal is permitted once and uses idempotency, Tenant gate, both account locks in stable UUID order, and one atomic transaction. A different intended transfer is a separately authorized new transfer, never an implicit replacement. Receipt/Payment correction/refund remains outside Phase 4 without its own approved business contract.

### Module state and authorization lock

- 3C means optimistic comparison of the already persisted Accounting module revision, followed by a final Tenant row lock and revision recheck in the posting transaction. This final lock is required because the current module-state command also takes the Tenant row lock; a version check alone cannot serialize OFF with a posting. No new version field or migration is required for this guard. A stale revision yields `409` and no write; do not automatically retry a financial request. Verify actor, Company, Branch, module-state exception, target ownership, and idempotency inside the command boundary.
- Earlier blanket OFF-denial wording is superseded only for the canonical pre-OFF Income Receipt, Expense Payment, and necessary linked correction exception. Module OFF never grants a role permission. Company Accountant cross-Branch correction is Accounting-specific; other module policies retain their existing checks.

### Read model and UI placement lock

- 4A is the bounded committed-Accounting Income-minus-Expense report contract above. Its label is **Accounting Result**. It is not final consolidated Company Profit and never includes local mock values. The existing `CompanyResultView` cash and future-source cards retain their DEMO status until all of their data sources are canonical; no mixed-source total is presented as a real result.
- 5A uses existing `FinancialLedgerView` Company Income and Company Expenses routes, their flex-wrapping header action area, their final table action column, and the scrollable `SharedFormModal`. Add a compact `Record Receipt` row action to Company Income and `Record Payment` to Company Expenses, each passing its own event UUID; use the existing primary actions for Income/Expense creation. Add a compact secondary `Accounting tools` action in the same header area, opening shared-modal modes for accounts, categories, opening balance, and transfer. The action is visible only to a Company-level Accountant; Branch Accountants see only permitted record actions. The existing `Accounting` route currently aliases Garage Revenue and is not repurposed. No new route or page composition is required. Any rendered layout conflict at tablet/mobile widths is an implementation review failure to resolve within the existing design system before release.
- The existing `otherIncome` Method control is replaced by category selection because Income alone does not record cash. The Expense form gains source reference and category within its current scrollable body. Form success waits for the committed API response. This is the reviewed minimum visible control addition authorized by 5A, with no redesign of existing page composition.

### Implementation and verification gates

- Implement in the existing P4-00 through P4-05 slices. Backend models/migrations, commands, API, and React integration all remain in Phase 4; do not stop after backend delivery. The module-state OCC test must force both OFF/write orderings on independent PostgreSQL connections. Correction tests must prove one economic Income/Expense result, immutable Receipt/Payment movements, original-period restatement, and safe opening/transfer reversal. API tests cover role/Company/Branch/object scope and idempotency. React tests cover current-route preservation, modal placement at desktop/tablet/phone widths, API failure state, reload persistence, and DEMO status for unmigrated views.
- The implementation is complete only when the above contracts are built and verified against disposable PostgreSQL and the approved React UI. Staging/production database permissions and deployment remain separately unverified. No commit, push, or deployment is implied by this architecture lock.

## Canonical V2 reconciliation — locked Phase 4 additions

- Canonical authority: [01 — Business Rules](../../docs-final-v2/01-business-rules.md#approved-business-decision-additions), [02 — User Roles and Permissions](../../docs-final-v2/02-user-roles-permissions.md#approved-business-decision-additions), [04 — Data Model Relationships](../../docs-final-v2/04-data-model-relationships.md#approved-business-decision-additions), and [09 — Company Accounting](../../docs-final-v2/09-company-accounting-owner-distribution.md#approved-business-decision-additions). These additions govern the bounded Accounting Result, signed/zero Opening Balance behavior, Owner read-only permission, and Accounting-specific cross-Branch correction.
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: this plan's statements that Owner posting is deferred for a later decision. Owner posting is denied for Phase 4 Accounting.
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: this plan's statement that Company-level cross-Branch correction still needs canonical reconciliation. It is resolved for Accounting within the same Company only; broad correction authority and all non-Accounting cross-Branch permissions remain unresolved/default-deny.
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the plan's blanket block on any Accounting Income-minus-Expense result pending cash-versus-accrual or distributable-Profit decisions. The bounded Accounting Result is approved as defined above; final consolidated Company Profit and operational source recognition remain unresolved.
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: any plan interpretation that permits posting a zero Opening Balance. Zero creates no economic event; reversal-only correction of a prior nonzero opening event remains permitted by its dedicated command.
- These additions authorize no implementation, schema/API change, or UI redesign. Existing routes, role identities, Company/Branch boundaries, module ownership, immutable history, and Phase 1–3 behavior remain unchanged.

## Final Phase 4 surgical correction lock — Opening Balance and Cash Event Corrections

This section is the current technical authority for the exact topics below and supersedes only conflicting earlier statements. The V2 additions in 01/04/09 remain the business authority. No code, schema, API, or React implementation is performed by this documentation change.

### Signed Opening Balance creation

- `POST /opening-balances/` accepts `{account_id, signed_amount, effective_at, reason, source_reference}`. Reject `signed_amount == 0` without creating an event or movement. Persist `AccountingEvent.amount = abs(signed_amount)` and exactly `AccountMovement.delta = signed_amount`; positive increases, negative decreases.
- Opening Balance is Company Accountant only, Company-owned, not Income or Expense, and excluded from Accounting Result. It may be historical but `effective_at` must not be in the future. Do not create Loan, Interest, Expense, Credit, Liability, or another balancing event.
- The dedicated `POST /opening-balances/{event_id}/corrections/` remains separate: positive/negative replacement allowed; zero means reversal-only; append immutable history and preserve the account and original effective instant.

### Wrong-target-only Receipt/Payment application reallocation

- When a real Receipt/Payment is correct and only its linked target is wrong, use `POST /applications/{application_id}/reallocations/` with `{new_target_event_id, reason}`. Validate event kind (Receipt→Income, Payment→Expense), same Company, ordinary role/Branch scope, module-state rules, current target, and outstanding limits.
- Atomically append a negative `AccountingApplication` reversing the old application and a positive application to the new target. Retain the original Receipt/Payment, its `AccountMovement`, amount, account, and effective date unchanged. Record correction actor, recorded time, reason, links, audit, and idempotency result. Do not create or reverse a cash event. A request that changes any cash fact must use the dedicated event-correction command instead.

### Wrong actual Receipt/Payment fact correction

- Dedicated future commands under the existing boundary:
  - `POST /api/v1/tenants/{company_id}/accounting/receipts/{event_id}/corrections/`
  - `POST /api/v1/tenants/{company_id}/accounting/payments/{event_id}/corrections/`
- Request requires `reason`; include replacement values only when a replacement is needed. Allowed values: `amount`, `account_id`, same-kind target (`income_event_id` or `expense_event_id`), `effective_at`, `description`, and `source_reference`. Company ownership, event type, and historical actor identity are immutable. Correction actor is the current authorized user. Require `Idempotency-Key`.
- If the cash fact should be removed, atomically append `ORIGINAL → REVERSAL` and no replacement. If it should be corrected, atomically append `ORIGINAL → REVERSAL → REPLACEMENT`. Preserve the original; append a linked same-type reversal, an equal/opposite movement on the original account, and a negative application reversing the old target application. When a replacement is supplied, append the same event type, correct movement, and application. Never convert Receipt to Payment or vice versa, or mutate/delete original rows.
- The reversal retains the original event's `effective_at` so its opposite movement neutralizes the erroneous movement at the same point in the derived balance history; `recorded_at` is the current correction time. This reversal is corrective history, not a new actual cash movement. Any replacement that represents actual money must use an effective instant no later than server time.
- Reversal uses original amount/account/target references as history links; replacement may use another active account and an authorized same-Company target. The replacement cash event must have `effective_at <= server_now`. A wrong-target-only request is rejected from these endpoints and directed to application reallocation. Actual refund/recovery after money moved is not a correction and remains a separately approved future workflow; do not invent it.
- Revalidate after correction: total active Receipt applications cannot exceed current Income amount; total active Payment applications cannot exceed current Expense amount. Preserve over-receipt/overpayment rejection, Company isolation, Branch authorization, module-state rules, account activity rules, idempotency, and all target constraints. Reject an invalid replacement without partial writes; create no balancing transaction.
- For a cash event that existed before Accounting was disabled, correction while OFF is allowed only when it is necessary to resolve the same pre-OFF obligation/event under the existing narrow Accounting OFF exception. OFF never authorizes unrelated/new cash activity.

### Future-dated actual cash events

- Reject `effective_at > server_now` for new Receipt, Payment, Transfer, and corrected replacement Receipt/Payment. The server compares timezone-aware instants; client clock and timezone do not grant future authority. These are actual money movements, not plans.
- Opening Balance may be historical but never future-dated. A planned payment/transfer requires a separate future scheduling model, outside this Phase 4 contract.

### Atomicity and deterministic locking

- One database transaction includes the correction event(s), movement(s), application reversal/reallocation, audit history, and idempotency result.
- After the existing Tenant/module-state gate, lock the original/current cash event, current and replacement Income/Expense targets, involved accounts, and affected applications in deterministic UUID order. Recheck account active status and target balances after locks. Keep the Tenant lock through commit so module OFF cannot race the correction.
- Enforce one current correction successor, one reversal per source row/application, and idempotency. A second concurrent correction must fail with a stable conflict and no partial event, movement, application, or audit. Do not transparently retry a changed financial intent.
- Branch-bound Accountant corrections remain inside assigned Branch scope. Company-level Accountant may act across Branches within the same Company for Accounting only. Owner stays read-only; Platform Back Office has no routine posting authority; Investor/Media have no Accounting mutation authority.

### Superseded earlier technical wording

- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: Phase 4 API text saying Receipt/Payment corrections are outside scope. Wrong cash facts can be corrected through their dedicated append-only reversal/replacement commands; wrong-target-only changes use application reallocation and leave cash unchanged.
- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: generic event correction wording implying cash corrections share the Income/Expense correction endpoint. They use separate typed Receipt and Payment routes.
- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: any Opening Balance request/model wording using unsigned `amount`, allowing a zero posting, or allowing a future date. Use signed `signed_amount`; zero posts nothing.
- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: any Phase 4 contract allowing future-dated Receipt, Payment, or Transfer. The effective instant cannot be later than server time.
- Existing refund/recovery statements are unchanged: correction fixes an incorrect recorded fact; a later real refund/recovery is a separate actual event and remains future/BDR. No Company Share/Garage Revenue/common Expense recognition, final Company Profit, distributable Profit, period close, Investor reconciliation, manual Loss, or Platform private-finance support decision is resolved here.

## Final Phase 4 correction, Accounting OFF, and account archive lock — 2026-11-03

This section supersedes only earlier technical statements about correction outcomes, Branch reattribution, Accounting OFF eligibility, and account archive eligibility. The approved business authority is in the new additions to V2 `01`, `02`, `04`, and `09`. It changes no application code, database schema, existing API, or React UI in this documentation task.

### Explicit correction outcome

- Every supported correction UI/API must explicitly choose `REVERSE_ONLY` or `REVERSE_AND_REPLACE`; each replacement is the same record kind. Reversal-only is allowed only when the specific original record does not represent a distinct economic event (for example, a false or duplicate record); it must not erase a distinct real cash movement. If the event represented by that record occurred but was recorded incorrectly, require a replacement. Preserve amount limits and one-economic-effect aggregation.
- For Income/Expense correction, reject `REVERSE_ONLY` while active Receipt/Payment applications remain. The actual cash applications must first be reallocated through the audited application flow, or safely reversed and reapplied to a same-kind replacement in the same atomic correction. Reject if cash history cannot remain attached to a valid target within current limits. Never orphan a real Receipt/Payment or its AccountMovement. If a distinct real Income/Expense event occurred with incorrect facts, require a corrected replacement.
- A correct Receipt/Payment assigned to the wrong Income/Expense uses application reallocation only. It does not offer a cash reversal choice and does not mutate the Receipt/Payment or AccountMovement.
- Keep the dedicated Opening Balance correction. A signed zero replacement means terminal reversal-only with no zero event. For Transfer, retain `POST /transfers/{event_id}/reversals/` for reversal-only; add a distinct proposed `POST /transfers/{event_id}/corrections/` for a real but misrecorded Transfer that requires a linked same-kind replacement. The replacement request contains `{reason, replacement: {from_account_id, to_account_id, amount, effective_at, description, source_reference}}`; it remains Company Accountant only, within the same Company, uses two distinct active accounts, requires idempotency, and commits reversal plus both original/replacement movement legs atomically. A later unrelated transfer remains a new Transfer.
- For the existing Income/Expense, Receipt/Payment, and Opening Balance correction resources, add an explicit `outcome` field to the request contract. `REVERSE_ONLY` rejects replacement fields (Opening Balance encodes this as `replacement_amount: "0.00"`); `REVERSE_AND_REPLACE` requires a same-kind replacement object or a nonzero signed Opening Balance amount. Any cash replacement remains actual, same-kind, and not future-dated. A Receipt remains a Receipt; a Payment remains a Payment.

### Replacement Branch attribution and permission

- Add optional `branch_id` to same-kind Income/Expense and Receipt/Payment replacement values. If omitted, inherit the original record's Branch. `null` represents Company-wide only where that record type already permits it.
- The backend derives actor scope. Company-level Accountant may correct/reattribute within this Company to any Company Branch or Company-wide where supported. Branch Accountant is forced to the original authorized Branch and cannot change it or select another Branch. Reversal rows always retain original Branch attribution. This does not grant any cross-Branch permission outside Accounting.
- Wrong-target application reallocation retains the actual Receipt/Payment event's original Branch attribution; only the application target changes. Cross-Branch target correction is allowed only under the already approved same-Company Company-level Accountant permission.

### Accounting OFF eligibility and serialization

- Use the immutable current `CompanyModuleState` row whose `state="disabled"`; its server-assigned `effective_from` is the OFF boundary. This is supported by the existing `apps.tenants.models.module_state.CompanyModuleState` model and append-only state command; no new module-state column is proposed.
- While OFF, the original root Accounting entry and every Income/Expense target obligation affected by correction or reallocation must have server `recorded_at < disabled.effective_from`. Equality, missing timestamps, a post-OFF root, or a post-OFF target fails closed. The request must be necessary to resolve that same pre-OFF record/obligation.
- Reversal, application, audit, and replacement rows may be recorded after OFF only as linked append-only correction history for the eligible pre-OFF chain; they cannot create an unrelated root event, new Income/Expense obligation, or target. If a correction touches linked root cash events, those roots must also predate OFF. Normal Company/Branch/role/object/idempotency checks remain mandatory.
- Preserve the existing Tenant row lock through commit. Read the current disabled revision under that gate and compare immutable server timestamps after locking all affected records; do not auto-retry a rejected financial intent. New root writes remain denied while OFF.

### Account archival eligibility

- Keep the existing Company Accountant archive permission and row lock. Before archiving, recompute the signed balance and inspect immutable account history in the same transaction.
- Archive is allowed only when the derived balance is exactly zero **and** no historical AccountingEvent or AccountMovement has referenced the account. Any historical movement/event blocks archive even if later reversed and even if the net balance is zero. Return a stable conflict such as `409 ACCOUNT_HAS_HISTORY`; preserve `ACCOUNT_BALANCE_NONZERO` for nonzero balance. Do not delete movement/event rows or add an unarchive path.
- This gate is stricter than earlier plan statements that used only the current balance. Add race tests proving an in-flight posting/correction cannot pass the check and then leave history on an archived account.

### Superseded technical statements

- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: the account archive condition at the API table, data migration section, acceptance criteria, and transaction rules that requires only zero balance. The current condition is zero balance plus no historical event/movement.
- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: the Transfer reversal-only contract where a real Transfer occurred but its facts were wrong. Such a correction requires a linked same-kind replacement; a false/nonexistent transfer can be reversed without replacement.
- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: optional/unspecified replacement choices for supported correction forms. Use explicit outcome and same-kind validation; keep application-only target reallocation separate.
- SUPERSEDES EARLIER STALE/INCOMPLETE TECHNICAL STATEMENT: Accounting OFF correction wording that checks only the cash event or only one obligation. Every affected root entry and target must predate the current immutable disabled revision.

### Verification gates for this lock update

- Tests must cover both outcomes for every supported correction kind; false/duplicate event reversal; misrecorded real event requiring replacement; rejection of a wrong-kind replacement; Income/Expense correction with existing applications; no-cash-movement guarantees for wrong-target reallocation; Transfer same-kind replacement with atomic two-account legs; replacement Branch scope; Branch Accountant reattribution denial; Company's cross-Branch Accounting allowance; OFF timestamp before/equal/after boundary; and rejection of post-OFF targets.
- Account tests must prove archive rejection with history at zero balance, after full reversal, and under concurrent posting/correction; archive success only with zero balance and no history. Re-run Phase 1–3 permission/route regression to prove this remains Accounting-only.
- These are required future implementation tests; this architecture update does not claim that they have run or that Phase 4 is implemented.

## Final Phase 4 reconciliation lock — 2026-11-03

**Current status: `PHASE_4_CODE_ARCHITECTURE_READY_FOR_IMPLEMENTATION` for the bounded Company Accounting foundation.** This appended section is the current technical authority for OFF ordering, settlement versus correction, effective-date boundaries, correction UI access, and stale summary/risk statements. Canonical V2 additions remain the business authority. No code, schema, API, React, migration, or runtime implementation is performed by this documentation review.

### OFF settlement and correction are separate command cases

- Preserve the approved ordinary OFF settlement: an authorized user may post a new Receipt to an Income root recorded before the current OFF revision or a new Payment to an Expense root recorded before it. Atomically create the settlement's AccountingEvent, AccountMovement, and AccountingApplication. That new Application is ordinary settlement history, not correction/reallocation history; the OFF correction gate must not block it.
- For correction/reallocation while OFF, every affected original root event (including any existing Receipt/Payment whose application is changed) and original root Income/Expense obligation must predate the current disabled revision. A standalone application reallocation may target only an already-existing eligible root obligation; it cannot target an unrelated post-OFF root.
- A same-kind correction replacement and its linked reversal/application rows may be written after OFF only within the same atomic correction of eligible pre-OFF roots. Reapplying the pre-OFF cash applications to that correction-child Income/Expense target is permitted as part of that correction. The child target is not a new root obligation.
- A Receipt/Payment created during the current OFF revision through ordinary settlement records that disabled revision and cannot itself be corrected/reallocated while that same revision remains OFF. Re-enable Accounting before its ordinary correction. This does not narrow or remove the existing settlement exception.

### Prove OFF ordering with immutable revision identity

- The current `apps.tenants.models.module_state.CompanyModuleState` model is versioned, immutable, and written under a Company/Tenant row lock; its state codes are `enabled`/`disabled`. Phase 4 must reuse that exact history.
- Add a protected FK such as `module_state_revision` from each `AccountingEvent` and `AccountingApplication` to the exact `CompanyModuleState` row used by the write. `AccountMovement` inherits the provenance through its AccountingEvent FK. The Accounting command obtains the current module revision and writes all rows under the same Tenant lock used by the module-state command.
- Validate that the referenced revision belongs to the event's Company and has `module_code="accounting"`; the client cannot submit this FK/version. A root is pre-OFF only when its stored revision version is lower than the current disabled revision version. Root history, not a replacement/correction child, determines eligibility.
- Use revision ordering as the authoritative serialized cutoff. `recorded_at` and `effective_from` remain immutable audit timestamps; application-server clock comparison alone is not the permission check. Missing or cross-Company/module revision references fail closed.
- Put the FK in the initial Accounting migration, which depends on the existing tenants module-state migration (`tenants.0003_company_module_state`). No change to the existing tenants table or module-state schema is required. No backfill is needed before an Accounting persistence table exists; any imported history without valid provenance must be rejected or explicitly migrated before use.

### Correction outcome and effective-date contracts

- Keep `REVERSE_ONLY` and `REVERSE_AND_REPLACE` as explicit outcomes for supported correction forms. Reversal-only may remove only a false/duplicate record that does not represent a distinct economic event or cash movement. A misrecorded distinct event requires a same-kind replacement. Income/Expense with active Receipt/Payment applications cannot use reversal-only until those applications are safely reallocated; a replacement correction must reapply them atomically and preserve outstanding limits.
- **Income/Expense:** replacement keeps the original `effective_at`; signed net effect stays in the original effective reporting period. The Phase 4 correction serializer does not accept a replacement `effective_at`. Moving a recognized event into another period is outside this rule and requires a separate business decision.
- **Receipt/Payment:** a wrong-target-only correction changes application history only and preserves the cash event/movement. A wrong cash fact uses the typed same-kind correction: reversal at the original instant, with a same-kind replacement when the actual event occurred but was misrecorded. The replacement may carry the corrected actual `effective_at` but never a future instant. Receipt remains Receipt and Payment remains Payment.
- **Opening Balance:** keep its separate command and immutable account/original instant. The UI/API outcome maps `REVERSE_ONLY` to `replacement_amount: "0.00"` (no zero event) and `REVERSE_AND_REPLACE` to a nonzero signed amount. Do not say that this flow rejects all replacement fields; the zero value is its explicit reversal-only representation.
- **Transfer:** keep `POST /transfers/{event_id}/reversals/` for a false/nonexistent transfer. For a distinct real but misrecorded transfer, use the proposed typed `POST /transfers/{event_id}/corrections/` with `outcome="REVERSE_AND_REPLACE"` and a same-kind replacement, both active Company accounts, stable account locks, two movement legs, and one transaction. A separate later transfer remains a separate action.
- All correction commands require reason, idempotency, actor/Company/Branch validation, same-kind links, module-state checks, and atomic event/movement/application/audit writes. Do not create a refund or balancing transaction.

### Correction access in the approved React surface

- Repository evidence: current `FinancialLedgerView` Company Income columns are Timestamp/Source/Description/Method/Amount and Company Expenses columns are Date/Description/Branch/Amount; neither register currently has an `actions` column. `SharedFormModal` has no Accounting correction, event history, Opening Balance, or Transfer correction mode. These are current demo limitations, not implemented UI behavior.
- Supersede the earlier 5A placement assumption that a final table action column already exists. Do not silently add a new table column or change page composition. Use the already planned compact `Accounting tools` action in the existing Company Income/Expenses header action area; inside the existing scrollable shared-modal surface, provide the scoped/paginated Accounting event list/detail and its record actions.
- In that event history, selecting an Income offers `Record Receipt` and `Correct`; selecting an Expense offers `Record Payment` and `Correct`; Receipt, Payment, Opening Balance, and Transfer rows offer their typed `Correct` action only to authorized roles. The correction form makes `REVERSE_ONLY` versus `REVERSE_AND_REPLACE` explicit and exposes only fields permitted for that event kind. Opening Balance uses its zero/nonzero signed amount mapping above.
- Use the existing `GET /events/` filters/pagination and `GET /events/{id}/` detail contract; do not require manually entered UUIDs or repurpose the Garage Job receipt flow. Keep current routes and layout. UI/API success is shown only after backend commit; failure preserves entered values and displays the API error. If the selected placement cannot fit the existing responsive modal/header behavior, stop that UI subtask as `UI_CHANGE_REQUIRED` rather than redesigning the page.

### Superseded summaries and current risk classification

- SUPERSEDES EARLIER STALE/INCOMPLETE SUMMARY: account archive is **not** permitted solely because balance is zero; it requires zero balance and no historical AccountingEvent/AccountMovement. A reversal does not erase that history.
- SUPERSEDES EARLIER STALE/INCOMPLETE SUMMARY: “corrections preserve actual cash and reallocate applications” describes only wrong-target reallocation. Wrong cash facts have dedicated same-kind reversal/replacement; wrong target has application-only reallocation.
- SUPERSEDES EARLIER STALE/INCOMPLETE SUMMARY: Owner Accounting posting is not deferred; Owner is read-only. Same-Company Company-level Accountant cross-Branch Accounting correction is resolved and does not grant authority in other modules.
- SUPERSEDES EARLIER STALE/INCOMPLETE SUMMARY: `CHANGE-RISK-003` must not classify the approved Accounting cross-Branch correction or pre-OFF Accounting settlement as BDRs. Remaining BDRs are Investor eligible-principal/withdrawal and reconciliation scope, manual Loss actor/impact, Company Share/Garage Revenue/common Expense recognition, final consolidated/distributable Company Profit, period close/carryforward, Owner Distribution, Platform private-support reads, and cross-Branch/OFF behavior for other modules.
- The older risk table and executive summary remain historical text under the append-only documentation rule. This latest overlay is the current Phase 4 status; it does not claim Phase 4 APIs, schema, UI, or tests exist.

### Final implementation gate tests

- PostgreSQL concurrency: normal Receipt/Payment settlement versus OFF in both lock orderings; settlement Application created while OFF for a pre-OFF root; correction/reallocation rejection for roots written under the current disabled revision; eligible root correction whose linked replacement/application rows are written under OFF; no partial writes or silent retry.
- Provenance: every AccountingEvent/AccountingApplication references an existing same-Company Accounting module revision; wrong Company/module and missing references fail closed; root revision precedes current OFF while correction children may reference current OFF.
- Corrections: both outcomes per supported kind; false/duplicate versus misrecorded distinct event; application-only reallocation leaves cash unchanged; active Income/Expense application limits; original-period Income/Expense restatement; Receipt/Payment corrected actual date and future-date rejection; Opening Balance zero/nonzero mapping; Transfer same-kind replacement with atomic movement legs.
- Permission and compatibility: Company Accountant can reattribute only within Company; Branch Accountant cannot change Branch; Owner mutations denied; no cross-Branch grant leaks to Phase 1–3 or other modules; preserve all existing routes.
- Archive and UI: reject archive for any history even at zero balance/after reversal and under concurrent writes; allow only zero/no-history account. Test the scoped event-history modal, correction outcome validation, failed-request behavior, reload/query invalidation, and desktop/tablet/phone overflow within the existing page composition.
- These tests are required before Phase 4 implementation is considered complete. They have not been run in this documentation-only architecture reconciliation.

### Correction outcome choices in every supported form

- Every supported correction form presents both explicit outcomes: `REVERSE_ONLY` and `REVERSE_AND_REPLACE`; do not silently hide or preselect one outcome based only on the record type.
- Validate the selected outcome against the actual event and its linked applications. If the record represents a distinct real economic/cash event, reject `REVERSE_ONLY` with an actionable explanation and require the same-kind replacement. For Income/Expense with active applications, also require safe reallocation or atomic reapplication before reversal can complete.
- Keep kind-specific fields and constraints: Opening Balance maps `REVERSE_ONLY` to `replacement_amount: "0.00"` without creating a zero event; a real but misrecorded Transfer requires a same-kind replacement; false/duplicate events may use reversal-only. This adds no new page or route and does not change the approved layout.

## Phase 4 implementation and verification checkpoint — 2026-11-03

**Current status: PHASE_4_IMPLEMENTATION_COMPLETE_LOCAL for the bounded Company Accounting Foundation.** The implementation is in the current dirty local `codex/audit` worktree; it is not committed or pushed. This checkpoint supersedes earlier statements in this plan that Phase 4 code, schema, UI integration, and tests do not exist. Those statements remain historical snapshots of the architecture-only stage.

### Confirmed decision implementation

- An Accounting account with any financial history cannot be archived, even when its derived balance is zero. Only a zero-balance account with no event/movement history can be archived.
- OFF/write ordering uses the persisted module-state revision plus the final serialized Company/Tenant lock and revision recheck. A stale write fails with conflict; financial requests are not automatically retried.
- While Accounting is OFF, correction/reallocation is limited to eligible pre-OFF root records and targets. Ordinary Receipt/Payment settlement remains a distinct allowed operation for eligible pre-OFF obligations.
- Every supported correction form exposes both `REVERSE_ONLY` and `REVERSE_AND_REPLACE`. Backend validation binds the selected outcome to whether a real economic/cash event occurred; it does not allow reversal-only to erase a distinct real movement.

### Implemented and locally verified scope

- Django Accounting persistence, migrations, Company/Branch authorization, services, DRF endpoints, append-only financial history, idempotency, transaction/concurrency controls, and Accounting Result projection are present.
- The existing React Accounting surface uses the shared API/query boundary for its supported Accounting workflows. Existing route identities and page composition are retained; no visual redesign is part of this checkpoint.
- Local disposable-PostgreSQL tests, frontend tests/lint/build, migration/schema checks, and a browser reload-persistence smoke check are summarized in [Phase 4 execution evidence](../../docs/phase4-execution-progress.md).

### Explicitly outside this completion claim

Vehicle, Investment, Garage, and Sales do not yet create their domain source events in Accounting; those later vertical integrations remain in their roadmap phases. Final Company Share/Garage Revenue/common Expense recognition, distributable Profit, period close/carryforward, Investor Profit, Owner Distribution, and production/staging runtime or database-role verification are not included. No claim of production deployment or production readiness is made.

## Phase 4 final audit checkpoint — 2026-11-04

The 2026-11-03 implementation checkpoint above is extended with the following repository and disposable-database evidence; its scope boundaries remain unchanged.

- Accounting migrations now refuse reverse operations while any catalogue or financial-history/idempotency row exists. Empty rollback/reapply remains verified. Tests cover full rollback, partial downgrade guards, and empty-schema reversibility.
- An isolated PostgreSQL NOLOGIN test role with only `SELECT`/`INSERT` grants was denied `UPDATE`, `DELETE`, and `TRUNCATE` on the append-only Accounting history tables. This verifies the test role only; deployed runtime-role privileges remain `UNVERIFIED`.
- Both Receipt/Accounting-OFF lock orderings passed: OFF-first rejects a stale write with conflict and no partial event; Receipt-first commits against the enabled revision before OFF commits. Requests are not silently retried.
- The approved decisions remain represented in code: accounts with any history cannot be archived; while OFF, correction/reallocation is limited to eligible pre-OFF records; all supported correction forms expose both `REVERSE_ONLY` and `REVERSE_AND_REPLACE` with kind/history validation.
- On 2026-11-04, the full Account/Company/Branch backend regression ran **296/296 tests passed** on isolated PostgreSQL 15. React ran **101/101 tests passed**, configured lint passed, and `tsc && vite build` passed. The main bundle still emits its advisory size warning. Django checks found no issues or model drift. All migrations applied to a new isolated database, then `migrate --check --plan` reported no planned operations.
- The preceding 2026-11-03 local browser smoke remains the evidence for Income reload persistence; this checkpoint made no frontend source change and did not repeat the browser session.

These results support `PHASE_4_IMPLEMENTATION_COMPLETE_LOCAL` for the bounded Company Accounting Foundation only. Staging/production role grants and deployment remain unverified, and the out-of-scope source-module integrations and final Profit/distribution decisions remain separate roadmap work. No commit, push, merge, or deployment occurred.
