# Phase 1 correction audit — 2026-10-31

## Scope and baseline

Verified worktree: `D:/VIRMS/tmp/reviewed-backend-baseline`; branch `codex/audit`; starting HEAD `04c28471dc0de432c2a29a4cd01e0dbb3bbaf6a1`; origin `muhammedshibiliraihsoft-art/VIRMS`; compared with cached `origin/staging`. No remote-ref freshness claim. Existing five dirty V2 documents and Black cache were preserved. No commit, push, merge, deployment, frontend or finance change.

## Findings and corrections

| Finding | Verified failure / root cause | Correction / regression |
|---|---|---|
| A1: Accountant lifecycle | `policy.py` included reset/status/revoke Investor/Media in the ordinary Accountant action set. Existing positive API tests encoded that incorrect grant. | Removed those ordinary actions; scoped Platform lifecycle remains. Explicit Accountant service/API denial tests and Platform success/session tests. Provisioning permissions retained. |
| A2: temporal split rows | Chained reverse-relation filters in Company/Branch selectors and Admin managed scope could bind start and end predicates to different historical rows. | Correlated `Exists` queries bind each membership, grant and assignment to one effective row and the same membership/Branch. Expired+future membership/grant/assignment tests plus existing cross-Company/read tests. |
| A3: Login ID enumeration | Only existing Users acquired identifier state, so wrong-password requests crossed identifier throttle limits at different attempts. | Removed User-existence lookup. All valid canonical identifiers and sources use HMAC-distributed fixed slots (65,536 per kind per key generation), bounding cardinality. API status/detail/Retry-After and Admin form outcomes compared across active/inactive/missing accounts. Fixed cardinality test checks rotating inputs. |
| A4: stale operator lifecycle | Lifecycle commands refreshed the actor under lock but did not compare the incoming authentication snapshot, allowing a request admitted before revocation to mutate after it acquired the lock. | Recheck incoming password hash and epoch under the existing User lock, as provisioning already does. All lifecycle verbs reject a stale actor without mutation. |
| B1: missing Branch audit | `end_scope_row` omitted Branch for assignment and scoped-grant endings. | Record the locked row's Branch; tests check both event types. |
| B2: missing lifecycle reason | Approved Phase 1 plan requires recovery/status/revoke reasons, but service/API/Admin omitted them. | Require a nonempty string of at most 500 characters without control characters. API returns 400 after authorization for invalid/missing reason; Admin reset and action form collect it; service writes it to audit atomically. Forms explicitly prohibit credentials/secrets. No raw request/password payload is copied into audit. |
| B3: historical context prefetch | `/auth/me/` prefetched all historical grants and assignments and filtered in Python. | Filter both Prefetch querysets to the current interval in PostgreSQL. Regression checks context output and effective predicates on the actual prefetch SQL. |
| B4: documentation drift | Published Tenant Merge and plan contained shared-account/global-uniqueness ambiguity and older progress report overstated completeness. | Existing dirty Tenant Merge correction already specifies separate account UUIDs and was preserved. Updated plan identity/uniqueness override, maps, and progress pointer; original plan-only sections remain labelled historical. |

## API/data/security compatibility

Reset/status/revoke retain their UUID routes and success fields but now require `reason`; callers must supply a brief administrative explanation without credentials or personal secrets. All account lifecycle authority is scoped Platform control-plane authority. Accountant provisioning of permitted Investor/Media remains unchanged. Company/Branch read ordering and pagination remain intact.

Login slots can collide conservatively: unrelated identities/sources may share throttling. Successful login therefore does not clear shared identifier state; windows expire normally. The limit is per stable SECRET_KEY; old limiter keys after rollout/key rotation can be removed with the existing bounded prune command. This change resets the transient effective admission-key namespace; coordinate rollout across workers with a shared application key. Login rate limits remain shared PostgreSQL state. No schema migration is needed.

## Re-audit boundaries

Re-read API and Admin lifecycle adapters, policy, current-interval selectors, membership/Branch guards, session issuance/gate, provisioning, audit writer, migration mapping and regression paths. No ordinary lifecycle global-role bypass remains in these inspected paths. Direct privileged database/model writes are trusted administrative boundaries; database one-Company/history/canonical-ID guards remain covered by existing regressions. Initial migrations were not rewritten.

## Validation

Final full run: **144 discovered / 144 passed** in 144.071 seconds on empty disposable PostgreSQL 15.19; Django check, fresh full migrations and makemigrations --check --dry-run all passed. Existing-data upgrade/collision/history guards, migration-lock race, multiprocess admission, password race, session isolation and Admin regressions were included.

Command: `D:/VIRMS/tmp/phase1-clean-runtime/Scripts/python.exe D:/VIRMS/output/phase1-execution-2026-10-31/run_disposable_checks_selectable.py audit-corrections-final-regression`. Evidence: `D:/VIRMS/output/phase1-execution-2026-10-31/audit-corrections-final-regression.json`.

Black semantic check: 77 source files clean; isort and flake8 clean; git diff --check clean. Read-query tests remained at 6 Company / 8 Branch queries for 1 versus 25 records, with a 20-row page; PostgreSQL EXPLAIN compiled both selectors. Containers were stopped by the harness. No quantitative production latency/load benchmark was run; admission parity was tested by attempt count, response/status and Retry-After, and Admin errors.

No unresolved A-level defect was found in the inspected Phase 1 paths after the fixes and re-audit. This is a scoped code/disposable-DB assessment, not a guarantee about uninspected external consumers or real environment state.

 Earlier focused run: 14 discovered/14 passed, including API/Admin enumeration, temporal history, stale actors, reasons and Branch audit. Full migration replay and schema-drift check passed in that focused run. Evidence: `D:/VIRMS/output/phase1-execution-2026-10-31/audit-corrections-focused-v2.json`.

## Operational limits

Existing staging/production data, real migration ledgers, live backups, DB application privileges and cleanup scheduling were not inspected or changed. Run target-environment preflight and reviewed data mapping before a real cutover. No Phase 2 or product-wide readiness claim.
