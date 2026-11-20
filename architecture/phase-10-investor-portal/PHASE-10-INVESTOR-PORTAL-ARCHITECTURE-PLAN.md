# Phase 10 — Investor Portal: Architecture Plan

**Status:** `IMPLEMENTATION IN PROGRESS — PHASE 8 / PHASE 9 ACCEPTANCE BLOCKED`

**Roadmap status:** `BLOCKED — PHASE 9 ACCEPTANCE AND AUTHORITATIVE PHASE 8 POSITIONS INCOMPLETE`. Read-only portal and identity work is implemented locally, but payout/reconciliation/settlement data remain unavailable. This document does not authorize guessed financial outcomes.

The Exit request screen explains the approved normal three-month notice, the new-credit/new-purchase restriction, Company Accountant cancellation approval and that expiry does not settle or release committed funds. The initial notice deadline is derived from the recorded request time using three calendar months in UTC, with month-end clamping. The Company-level Accountant can append an audited extension and the bound Investor can see the resulting deadline. The Accountant review UI also shows pending cancellation requests and reasons and invokes the existing approve/reject API; it refreshes from the server after successful review. The final settlement workflow remains unimplemented. No browser verification is claimed.

## Outcome and boundary

An Investor signs in and views only their permitted Company-scoped Fund, Stock Vehicles, Interim, Profit/reconciliation, recoverable, Exit and settlement positions. They may submit a normal Exit request, and the approved cancellation request remains subject to Company-level Accountant approval. The [Malayalam scope](PHASE-10-SCOPE-DRAFT-ML.md) and V2 roles/modules/UI documents govern the product surface. Investment/Accounting/Vehicle/Garage remain the financial source owners; the portal is a restricted projection and request surface.

## Existing baseline and resolved identity gate

The initial inventory found no safe Investor binding or self-service endpoint. That inventory is historical: the implementation now has versioned Company-scoped bindings and a server-resolved self endpoint. Operational Investor APIs remain separate and must not be exposed to Investor-role accounts.

**Approved identity rule (2026-11-19):** A same-Company Company-level Accountant verifies, creates and revokes the account-to-Investor binding. One account may have at most one active Investor profile per Company, and one Investor profile may have at most one active login account. Name/phone matching does not establish ownership. Revocation or loss of membership/role immediately denies self access while preserving history.

## Domain ownership and read projection

| Portal section | Authoritative source | Projection rule |
| --- | --- | --- |
| Overview / Fund position | Investment Fund credit/use/return and Phase 8 position | Own confirmed credits, available/committed principal and history; exclude other Investors and Company pool internals |
| My Stock Vehicles | Vehicle + Investment responsibility + Sale/Garage source | Only Vehicles assigned to the bound Investor, with approved status/result fields; do not expose internal cost, protected share configuration, or Buyer balances |
| Interim payouts | Investment and Accounting actual payment links | Due/suggested and confirmed Paid are separate; no synthetic payment |
| Profit / reconciliation / recoverable | Phase 8 versioned Investor position | Show source period, calculation status, actual retained payments, open balance and corrections without promising an undecided entitlement |
| Exit / settlement | Investment Exit state and Phase 8 settlement position | Show notice, approved extension, outstanding obligations and actual payment history; request actions are separate |

The projection must derive from current authoritative positions with source versions or update timestamps. It must not cache a second editable Fund balance or financial ledger. Company/Investor filters are applied server-side before pagination and serialization. Exclude Accounting account details, other Investor data, protected configuration, internal cost or Garage contact data unless a specific V2 rule authorizes them.

## API and command design

Create a dedicated, additive authenticated Investor self-service API namespace. The final URL shape should follow the repository's `api/v1/tenants/<company_id>/...` routing convention after inspection. The server resolves Investor identity from the session, active Company membership, Investor role and approved binding; callers do not select the Investor record for a private read. Use focused endpoints or a bounded overview response for Fund, Vehicles, Interim, Profit/reconciliation, Exit and settlement. Include canonical IDs, effective dates, confirmed/calculated status, source version and pagination where lists can grow. Avoid a broad response that leaks unrelated data.

The normal Exit request command records Terms & Conditions acceptance/version, effective request time, notice state, actor, Company and idempotency key in the owning Investment workflow. It rejects duplicate or invalid lifecycle transitions and does not itself pay principal or Profit. The cancellation request records a separate pending request; same-Company Company-level Accountant approval is required before reactivation. A notice expiry, portal button or pending suggestion never closes settlement. Existing Investment/Accounting module gates and the Phase 8 decision on minimum module-OFF settlement actions must be applied to the exact command; do not infer a general OFF bypass.

Use a shared error vocabulary for unauthenticated, no active binding, forbidden Company/Investor, module unavailable, stale position, duplicate request and policy-blocked calculation. Return no private existence hint for another Investor's ID. A failed request cannot display success. Idempotent replay returns the original outcome and cannot create a second Exit transition.

## Data model and migration plan

Inspect the existing account, membership, role, Investor and Exit schemas before fixing model names. Add only the binding and Exit/request/history records that are absent from the accepted Phase 8 baseline. Enforce same-Company FKs and active binding constraints at the service layer and database where feasible. Decide binding cardinality before adding uniqueness. Preserve historical access and Exit events; do not backfill a binding by matching name/phone. Any legacy Investor account without a verified binding stays private-data denied until provisioned through an audited action. Verify fresh/replay PostgreSQL migrations and rollback behavior on disposable data.

## Authentication, authorization and privacy

- Reuse current authenticated session/CSRF and Company context. Enforce active account, membership, Investor role, module state and bound Investor on every list/detail/read/command.
- Test IDOR by changing Company ID, guessed Investor/Vehicle/period IDs, filters, pagination and stale URLs. A role or frontend route guard never replaces object authorization.
- An Investor cannot post Fund credit/use, Vehicle cost, Profit/Interim payment, Loss, reconciliation approval, settlement closure or Owner/Company financial changes.
- Protect browser caches and request keys by authenticated account + Company + bound Investor. Clear private state on logout, account switch, role/binding revocation and expiry. Do not persist private financial truth as an independent offline database in this phase.

## React UI plan

Extend the existing Investor role navigation and route allowlist only for approved destinations: Overview, Fund Position, My Stock Vehicles, Interim Payouts, Profit/Reconciliation and Exit/Settlement. Reuse current design tokens, responsive shell and page patterns. Use compact mobile views, visible statuses for calculated/eligible/paid, source date and last update, clear pending versus confirmed Exit state, and accessible Terms acceptance. Avoid displaying blocked Profit as payable. Show loading, empty, error, disabled and expired-session states; refresh canonical data after successful request and after reload.

## Ordered implementation and verification

1. **Dependency gate:** verify Phase 9 completion and Phase 8 authoritative fields; list any policy-blocked portal fields. Do not mark a blocked amount eligible or paid.
2. **Identity binding:** lock cardinality/authority, add audited binding and safe provisioning/revocation, then test cross-Company and cross-Investor denial before exposing private reads.
3. **Read projection:** add the bounded self API and serializers from authoritative sources; test list/detail/filter/pagination, correction refresh and no private field leakage.
4. **Exit requests:** add normal Exit and cancellation request commands through Investment, with Terms/notice, idempotency, Accountant approval, concurrency and audit tests.
5. **React portal:** connect approved routes and states to the self API; test route protection, wrong-session cache clearing, errors, narrow-phone layout and reload persistence.
6. **Integrated acceptance:** disposable PostgreSQL backend/API/migration checks, React tests/lint/build and authenticated browser journeys for at least two Investors in one Company and Investors in different Companies. Confirm no new Accounting movement from a portal read or Exit request.

## Decision and release gates

The approved binding, Sale-date gross-profit placement, manual Loss review, Available-Fund withdrawal, and Accountant-confirmed Company distributable amount/carryforward decisions are recorded in V2 and related Phase 8 architecture. Their dependent payment, reconciliation, settlement, and Owner-distribution records are not implemented yet. Keep affected portal amounts unavailable or clearly unreconciled; do not imply payable or paid. Phase 10 is complete only after Phase 9 acceptance and authoritative Phase 8 positions, with backend authorization, no critical privacy defect, and successful browser/reload acceptance. Local, CI, staging and production evidence remain separate.

## References

- `planning/V2-DEVELOPMENT-ROADMAP.md`, Phase 10.
- `docs-final-v2/02-user-roles-permissions.md`, `03-system-modules.md`, `05-vehicle-investor-finance-workflow.md`, `07-ui-navigation-structure.md`.
- `architecture/phase-08-integrated-finance/PHASE-08-INTEGRATED-FINANCE-ARCHITECTURE.md` and `phase-09-main-system-core/PHASE-09-MAIN-SYSTEM-ARCHITECTURE-PLAN.md`.
- Current `apps/accounts`, `apps/investment`, `apps/vehicles`, `apps/accounting`, `apps/garage`, and `demo/react/src` source.

## Approved identity decision — 2026-11-19

The pre-decision identity gate above is historical. A same-Company Company-level Accountant verifies and creates/revokes the account-to-Investor link. Each account may have at most one active Investor profile in its Company, and each Investor profile at most one active login account. The link retains history and never derives from a name or phone match. Existing operational Investor APIs must not be exposed to Investor role; self-service uses a dedicated server-resolved binding and Company/role/status/module checks. These decisions authorize identity implementation but do not establish that the portal is available or that Phase 9 has passed.

## Local implementation checkpoint — 2026-11-19

**Verified from source:** the authenticated Investor portal resolves its identity from a same-Company active binding; Company Accountant binding read/create/revoke retains history; the self projection includes own Fund position, own Investor-funded Vehicles, Sale-date gross result periods, the bound Investor's own deal Profit/Interim paid facts, configured Interim amount/status, and Exit/cancellation requests. A separate paginated endpoint returns only the bound Investor's own Interim payment ID, month, effective date and amount. It does not expose another Investor's payment data, a reconciled payable/open balance, payment actions, final Exit settlement or Owner actions.

**Fund history read:** `GET /api/v1/tenants/{company_id}/investment/portal/self/fund-history/?page=N` returns 20 server-paginated entries for the bound Investor only: their current-attribution Fund credits, principal returns, Vehicle Fund commitments, and linked commitment adjustments. The SQL union is Company/Investor filtered before pagination. It omits bank/cash-account details and external references. Pagination and unbound/foreign-company denial are covered by disposable-PostgreSQL tests.

**Interim paid history:** `GET /api/v1/tenants/{company_id}/investment/portal/self/interim-payment-history/?page=N` returns 20 server-paginated actual payments for the bound Investor only, without account IDs, bank references, or other Investor records. The Profit period projection and portal show Interim Paid separately from deal Profit paid; no final payable is asserted.

**Privacy and correction behavior:** the Investor projection no longer includes Vehicle cost, protected agreement percentage, Sale price, Buyer collection/receivable/refund amounts, or unconfirmed Vehicle calculation. React parses explicit allowlists for Vehicle, Fund summary/activity, profit periods, and Exit history. If a Fund attribution correction affects an existing Fund use or return, both Investors involved see `MANUAL_REVIEW_REQUIRED`; derived Fund totals are returned as unavailable instead of exposing a misleading available/committed balance. Historic use and return entries remain linked to their original source; this projection does not reassign them.

**Local checks:** the full React suite passed 231 tests and configured lint passed; production build passed with a 751.70 KB main-chunk warning. Focused React portal/API checks passed 24 tests. On disposable PostgreSQL, a preceding 36-test sale/payment/finance/portal run passed before the final module-revision field addition; after that addition the payment API and concurrent-cap tests passed 2/2, with fresh migrations. Django check, migration drift check, Python compilation, and `git diff --check` passed. Full Phase 8/9/10 browser acceptance, CI, staging, production, and deployment remain `UNVERIFIED`; Phase 10 remains incomplete because the Investor Portal has no confirmed private payable/recoverable projection or final settlement position.

### Q135 Monthly Interim history extension — 2026-11-19

The private portal now includes the bound Investor's paginated actual Interim payment history and shows confirmed Interim Paid amounts separately in each displayed Profit period. The self-history serializer returns only payment ID, payment month, effective timestamp and amount. A disposable-PostgreSQL test verifies self-binding, own-record filtering, foreign-Company denial and exclusion of other Investor amounts. Targeted React portal/API checks passed 32 tests after this extension; the full browser/reload acceptance gate is still outstanding.

### Accountant period snapshot availability — 2026-11-19

The Company Accountant now has an append-only, versioned Investor period snapshot/restate API and review UI. It records the confirmed calculation and restatement delta without creating a payable, recoverable or cash event. The private Investor self projection now includes that bound Investor's latest snapshot, confirmation version/time, and freshness status. A changed source shows the saved historical calculation and pending difference as awaiting review; an attribution correction requiring manual review hides period amounts. Internal source fingerprints, Accountant reasons and actor IDs remain private. The portal still has no confirmed payable/recoverable, payment action, or final Exit settlement view. Phase 10 is not complete.

### Private confirmed calculation display — 2026-11-19

The portal's source hash now matches the Accountant projection by using individual confirmed deal-profit payment IDs and effective timestamps, current confirmed Vehicle-result source versions, Interim payment IDs/dates and valid Loss-offset links. This prevents a false `RESTATEMENT_REQUIRED` caused only by the portal's former aggregation of deal payments. The Investor sees only the latest snapshot for their own binding; changed source status and signed calculation are explicitly not a payable, payment instruction or settlement. The API test verifies current and stale snapshots, omission of Accountant reason/source fingerprint/actor ID, and unchanged Accounting movement count. Focused React portal/API tests passed 29 tests; `npx tsc --noEmit` passed. Full authenticated browser/reload and Phase 9 integrated acceptance remain outstanding.
