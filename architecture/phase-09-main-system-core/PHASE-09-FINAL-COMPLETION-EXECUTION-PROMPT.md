# VIRMS Phase 9 — Final Completion Execution Prompt

**Use:** Give this prompt and `PHASE-09-FINAL-COMPLETION-EXECUTION-GUIDE.md` to the implementing agent. The guide is authoritative for scope, journey details, acceptance, mobile coverage and final documentation. If this prompt and the guide appear to conflict, follow the guide and report the conflict before dependent work. Do not use the older acceptance matrix as current status without verifying it against this checkout.

## Mission

Complete the remaining Phase 9 Main System Core acceptance work for J01–J09 in `D:\VIRMS\tmp\phase9-baseline-review-d2efd314`. Finish missing live evidence, repair only confirmed acceptance-blocking defects, run one consolidated gate, and produce an evidence-based final report. Do not claim Phase 9 completion from existing code, a passing selected test batch, or this prompt alone.

The user explicitly authorizes reuse of the existing disposable PostgreSQL database `virms_phase9_closure` in container `virms-p9-closure-20261124`, currently exposed on `127.0.0.1:55441`, and the existing Company-wide Accountant test login **`p9_acceptance_1125`** with the **same password supplied by the user in this conversation**. Do not create another account or change this password just to test. The password is intentionally absent from repository files. In a new chat, ask the user for the existing password if it is unavailable; never guess it or recover it from another database. Verify that frontend `127.0.0.1:5174` and backend `127.0.0.1:8001` still point to this checkout and disposable database before a financial write.

## Mandatory starting state

1. Read applicable `AGENTS.md` and the complete English guide. Confirm worktree root, detached HEAD or branch, SHA, `git status`, existing staged/unstaged/untracked changes, process paths, database identity, migration state and Company/role context. Preserve dirty work. Do not reset, clean, stash, switch checkout or overwrite another agent's changes.
2. Use the repository-pinned Python 3.12 / Django 5.2.18 setup for automated checks. Identify the exact disposable test database and port before a test runner creates it. Treat previous 21/21 focused backend passes and earlier 4/4 timezone/Vehicle passes as dated evidence; inspect the exact test names/results before reusing them. Do not rerun passing suites merely to increase counts.
3. Establish one concise audit ledger with journey, action, role/Company/Branch, API, source row, typed link, event, movement, browser/reload evidence, test command/result and status. Keep credentials and private account details out of it. Record actual observed values, not expected values as if observed.

## Execute the remaining journeys

- **J01 Access:** Confirm login, Company/Branch context, CSRF, session, logout, role and module OFF boundaries. An unauthorized request must not expose a row or mutate data.
- **J02 Fund:** Prove actual credit, pooled availability, purchase allocation and a permitted partial principal return in the disposable database. Verify one Accounting cash movement per actual transfer, cap, retry and reload.
- **J03 Vehicle:** Trace one Vehicle identity through purchase, seller payment/refund, direct expense, correction and Branch move. Verify cost and original source Branch history after reload.
- **J04 Garage:** Exercise Stock Job linking once and external Customer Job charges, partial receipts, cost and refund. Confirm the approved Investment OFF behavior and persisted cash/source history.
- **J05 Sale:** Exercise partial Buyer receipt, current price correction, refund obligation and actual refund. A due amount is not Paid; same-key retry cannot create duplicate cash.
- **J06 Accounting:** Trace the actual transfers from J02–J05 through source row, typed source link, event and movement. Reconcile Company result separately from cash and Owner payout.
- **J07 Main finance:** Keep the existing `P9-TEST-001` historical-agreement issue visible. Its purchase agreement ID and percentage snapshot were both NULL; do not infer terms or silently backfill. Check for authoritative purchase-time terms. If absent, mark that record BUSINESS DECISION REQUIRED. Separately use a new valid disposable fixture with agreement *before* purchase to exercise Vehicle result, shares, recovery, period, partial payout, stale source, Loss, Exit and Owner flows through existing Phase 8 services.
- **J08 UI:** Check every required backend-connected Main page against its API and DB data, including loading, empty, 403/409/500/network, module OFF, disabled actions, refresh and logout/login persistence. Preserve approved cards, color, layout and routes. Complete the guide's mobile checklist at 320/390/768/1024/1440 px; mark an unavailable viewport check UNVERIFIED.
- **J09 Negative matrix:** Check cross-Company ID, wrong Branch, Owner/Investor/Media/Back Office write, module OFF, stale version, retry conflict, concurrent cap and rollback. Confirm denied requests leave no partial source, event or movement.

For each finding, write exact reproduction and evidence, classify A/B/C/D, then continue independent checks. Fix only a confirmed required A/B integration defect. Before shared finance, auth, tenant, API/schema or migration edits, prepare the impact report and follow the project approval gate. Before a material UI/card change, obtain the user's approval. Do not invent business terms or weaken tests. Use focused regression after each fix; conduct one final integrated gate after the fixes have stabilized.

## Final gate and deliverables

Apply Section 7 of the English guide exactly: relevant backend tests on disposable PostgreSQL, migration/schema checks, affected React tests/lint/build, authenticated J01–J09 browser evidence and responsive sweep. Report exact commands and discovered/run PASS/FAIL counts. Separate code checks, disposable DB, browser, CI, staging and production evidence. If a final gate defect appears, repair/check only that affected path and append the result; avoid a repeated broad audit.

Deliver one final report with exact worktree/HEAD/dirty state; journey-by-journey PASS/FAIL/BLOCKED/UNVERIFIED; changed files and reasons; persisted source/link/event/movement evidence; permission and concurrency results; mobile observations; confirmed defects; historical-data decisions; and remaining risks. Use `PHASE9 LOCALLY ACCEPTED` only when the guide's complete closure criteria are met. Otherwise give the precise `BLOCKED` or `PARTIAL/UNVERIFIED` reason. Local acceptance is not deployment acceptance.

At the end, apply Section 8 of the English guide for final documentation: update only affected living README and `/docs-final-v2/` implementation/verification sections after explicit Phase 9 acceptance, reconcile or replace stale Phase 9 matrix status with dated evidence, record mobile coverage and exclusions, and update roadmap status only if its end condition truly passed. Do not change frozen canonical business rules. This prompt does not authorize commit, push, merge, deploy, Phase 10, new reports or redesign.
