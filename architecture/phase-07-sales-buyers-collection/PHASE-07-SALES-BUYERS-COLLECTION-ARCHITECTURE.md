# Phase 7 — Sales, Buyers, and Collection architecture

**Status:** `COMPLETE LOCALLY` — implementation and local automated/browser verification passed 2026-11-18. CI, staging/production runtime, and deployment remain UNVERIFIED.

## Outcome and boundary

An authorized Accountant can trace a Stock Vehicle from its confirmed Sale through the agreed Buyer price, each actual Buyer receipt, the remaining receivable, an audited price correction, and each actual Buyer refund. The same source records must remain available to Phase 8 reconciliation. Phase 7 closes when these flows work together after Phase 6 Stock Vehicle costs have been recorded and the combined flow has passed the required regression and browser checks.

Phase 8 owns Investor principal recovery, Running Capital recovery, Profit/Loss allocation, Investor settlement, Company result, Owner distribution, and period close. Phase 7 does not post those outcomes from a Sale or an expected collection. Media publication and a reusable Buyer CRM/profile are outside this phase. The approved minimum Buyer record is the name and phone snapshot on the Sale. A separate Buyer identity is not required for the existing Sale and collection flows.

## Phase 7 included scope

- Confirm the Sale of a purchased Stock Vehicle and store the agreed price, Sale date, and Buyer name/phone snapshot.
- Record actual Buyer receipts in partial amounts and derive the received, remaining receivable, and refund-payable positions from the Sale and its cash records.
- Correct the agreed Sale price through versioned history with the prior/new price, reason, effective date, recorded time, and backend actor attribution.
- Record actual Buyer refunds separately, bounded by the current refund-payable amount.
- Link each actual receipt/refund to its typed Accounting source and one Cash/Bank movement; retain Sale and Vehicle identity across reload.
- Reuse Phase 6 Stock Vehicle cost links without creating a duplicate Vehicle cost or Sale expense; enforce existing Company, Branch, role, module, idempotency, and concurrency controls.

## Explicitly outside Phase 7

- Investor principal/Running Capital recovery, Profit/Loss allocation, Investor or Owner payouts, Company result, settlement, and period close (Phase 8).
- Separate Buyer CRM/profile, media publication, and offline financial writes.

## Verified implementation baseline

- `VehicleSale` has a Company, Vehicle UUID, original Branch, agreed price, Buyer name/phone, Sale date, and actor. The first successful Sale save confirms Sold. A Vehicle can have one confirmed Sale. The server requires a recorded Stock Vehicle Purchase before Sale.
- `VehicleSaleReceipt` stores each actual partial Buyer collection. `VehicleSaleRefund` stores each actual Buyer refund. `VehicleSaleCorrection` preserves the original Sale and each price change with actor, reason, version, and Sale effective date.
- Sale list/detail, create, receipt, refund, and correction routes already exist under `apps/vehicles/urls.py`. React exposes Vehicle Sales, Collections, and Sale Corrections & Refunds through the Phase 5 API and existing navigation.
- A Buyer receipt creates one `VEHICLE_SALE_RECEIPT` Accounting event, one positive Cash/Bank movement, and a typed source link in one domain mutation. A Buyer refund creates one `VEHICLE_SALE_REFUND` event, one negative movement, and a typed link. Neither operation is a second Sale or an automatic Profit payment.
- The backend derives Sale price, received/refunded totals, net received, receivable, and refund payable from source records. It locks the Sale during financial writes, uses idempotency keys, and rejects receipt/refund amounts above the current valid position.
- Phase 6 Stock Vehicle work links approved costs to the Vehicle identity. Phase 7 consumes the linked Vehicle/source relationship and does not copy a Garage cost into a second Sale expense.

The pre-existing Phase 5 implementation supplied the Sale, receipt, refund, and correction commands. Phase 7 closure identified that saved Sale correction history was not returned to the React client or visible after reload. The additive correction-history response and UI below close that gap without changing financial calculations, permissions, routes, or schema. The older `architecture/01` and `02` maps contain dated statements that Sales APIs are absent; the Phase 7 checkpoints appended to those two maps supersede those statements for current implementation status.

## Ownership and relationships

| Source | Owner | Phase 7 relationship |
| --- | --- | --- |
| Stock Vehicle and Purchase | Vehicle Management | Stable Vehicle UUID; Sale requires a recorded Purchase |
| Garage Stock work and cost | Garage / Vehicle cost source | Linked by Vehicle UUID; costs remain in their original source and Branch history |
| Confirmed Sale and Buyer snapshot | Vehicle Management | One Sale per Vehicle; Buyer name/phone remain on that Sale |
| Buyer receipt, refund, and price correction | Vehicle Management | Separate, append-only child records of the Sale |
| Actual Cash/Bank movement | Accounting | One movement per actual receipt/refund, with an explicit typed source link |
| Investor/Company reconciliation and payment | Phase 8 | Consume Phase 7 sources after the required collection and cost checks |

Every record is scoped to one Company. Sale actions derive the authoritative Branch from the server-owned Vehicle/Sale source. A later Vehicle Branch movement does not rewrite the Sale's historical Branch. List/detail and mutation permissions must enforce the same Company, Branch, and role boundaries after reload and on idempotent replay.

## API and data flow

The existing React Sale form sends the Vehicle UUID, Branch, price, Buyer name/phone, and actual Sale date to the Sale create endpoint. A successful response supplies the canonical Sale ID and confirmed Sold position. The Sale list/detail API is the source for screen state after reload.

Each Buyer collection sends its Sale ID, Cash/Bank account, positive amount, external reference, actual effective date, and idempotency key. The backend checks current receivable under the Sale lock, authorizes the actor for the original Sale Branch and Accounting action, and commits the receipt, Accounting event, movement, typed link, and audit history together. The response and a subsequent read show the same received and outstanding totals.

A price correction records a new version and reason without rewriting the Sale or earlier money movements. A refund is a separate actual outflow bounded by the corrected refund payable. Both remain visible in Sale history. A refund cannot be represented by reducing an earlier receipt. The relevant Vehicle Management and Accounting module gates apply to these actions; Investor-funded Buyer receipts also require Investment ON under the existing service contract. Current approved module-OFF exceptions and warnings remain as documented in V2.

The Phase 7 API surface is the existing Sale list/create, detail, receipts, refunds, and corrections endpoints. No new route or schema is assumed merely because the roadmap describes Buyer records. Any new response field must be additive and derived from the canonical source. Existing callers, account choices, reference normalization, pagination, and error contracts must remain compatible.

## Phase 7 implementation and local verification — 2026-11-18

- Sale detail/list responses now return the ordered, append-only correction records (old/new price, reason, version, effective time, and recorded time). The React API parser accepts the additive field and remains compatible with responses that omit it. Sale and Vehicle views display the saved history after reload. Actor attribution remains on the correction and audit-event records in the backend; the compact history panel does not display the actor identity.
- The Phase 6 Stock Job cost and Phase 7 Sale integration regression confirms that the same Vehicle/source remains authoritative and no duplicate Accounting event is created.
- Disposable PostgreSQL backend checks passed: `python manage.py test apps.vehicles.tests.test_sale_api apps.garage.tests.test_api --verbosity 1` (57 tests) and `python manage.py test apps.vehicles.tests.test_sale_concurrency --verbosity 1` (3 Sale concurrency tests covering concurrent receipts, refunds, and correction versions). Django `check`, `makemigrations --check --dry-run`, and `migrate --check` passed; no schema or migration change was needed.
- React `npm test` passed 200 tests across 35 files; `npm run lint` and `npm run build` passed. Build output retains Vite's advisory that one JavaScript chunk exceeds 500 kB.
- A browser workflow on the disposable local database created a Stock Vehicle and Purchase, confirmed a Sale, recorded a partial Buyer receipt, corrected Sale price, recorded a partial Buyer refund, and reloaded. Correction reason/prices and derived totals persisted; at 390 px there was no horizontal document overflow. Database inspection found one Sale, one correction, one receipt, one refund, and exactly one Cash/Bank movement for each actual receipt/refund.
- Local evidence does not establish GitHub CI, staging/production behavior, or deployment. No persistent user database was changed.

## Acceptance and limits

Phase 7 is marked locally complete because Sale, Buyer snapshot, actual collections, receivable, correction history, and refund positions stayed consistent across Vehicle, Garage source links, Accounting, API, and React after reload; focused authorization/integration/concurrency regressions and the browser workflow passed on disposable PostgreSQL; and schema checks found no migration drift. A standalone Buyer profile is not an acceptance condition. CI, staging, production, and deployment require separate evidence.
