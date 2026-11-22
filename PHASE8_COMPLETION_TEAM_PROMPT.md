# VIRMS Phase 8 — Completion Team Execution Prompt

Act as the senior financial systems implementation team responsible for completing and closing Phase 8.

## Target

- Repository/worktree: `D:\VIRMS\tmp\phase8-audit-corrections-20261120`
- Branch: `codex/phase8-audit-corrections`
- Verified baseline when this prompt was created: `166d4df66380f434b16a1fd8aa653319c3760d1c`
- Implementation plan: `PHASE8_FAST_CLOSURE_IMPLEMENTATION_PLAN.md`
- Risk: HIGH — financial integrity, PostgreSQL guards, transactions and concurrency

## Mandatory boundaries

1. Read applicable `AGENTS.md`, the implementation plan, current Git status and affected diffs once before editing.
2. Preserve every existing dirty change. Do not reset, clean, stash, restore or overwrite user work.
3. Continue the existing uncommitted Owner payout work:
   - `apps/accounting/migrations/0044_owner_payment_source_freshness.py`
   - `apps/accounting/tests/test_api.py`
4. Use only fresh disposable PostgreSQL for synthetic mutations. Never use staging or production data.
5. Use Python 3.12, Django 5.2.18 and PostgreSQL 15 for final backend evidence.
6. Do not invent financial or permission rules. Preserve same-Company scope, Accounting ON rules, roles, append-only history, idempotency and existing signed-money calculations.
7. Do not commit, push, merge or deploy. Do not update living docs until the user gives a separate instruction after Phase 8 closure is reported.
8. Do not start Phase 9 or Phase 10.

## Execute in this order

### 1. Complete Owner payout source freshness

- Review the existing `0044` migration against `apps/accounting/company_periods.py:current_confirmation_ids`.
- Ensure the SQL guard detects changes to:
  - period Accounting-event fingerprint;
  - applicable Owner split;
  - predecessor carryforward confirmation.
- Exclude the pending Owner-payment event from its own period fingerprint.
- Preserve the existing latest-version, payout cap, authorization, Accounting revision, event/movement and tenant checks.
- Before rewriting the uncommitted migration, confirm it has not been applied to a database that must be preserved.

Acceptance:

- Valid partial Owner payment succeeds.
- A structurally valid direct DB payment using the latest-but-stale confirmation fails specifically for source freshness.
- No payment, event, movement or audit artifact survives the failed transaction.
- Python and SQL source hashes match for empty and populated periods.
- Owner split and predecessor carryforward changes invalidate payment.

### 2. Close Exit Profit source freshness

- Create a valid direct-DB Exit Profit payment control in disposable PostgreSQL.
- Change an underlying period source through a supported correction path without creating a newer reconciliation.
- Retry payment against the latest-but-stale position.
- If accepted, add a forward migration enforcing exact source parity with:
  - `apps/investment/finance.py:summarize_investor_profit_periods`;
  - `apps/investment/services.py:list_investor_profit_period_projection`;
  - `apps/investment/exit_settlement.py`.
- Match the same Vehicle results, Deal payments, Interim payments, Loss offsets and canonical ordering. Do not use an approximate proxy.
- Preserve this signed cap exactly:

  `confirmed_net - profit_paid - future_applied + recovery_received + future_recovered`

- Preserve Principal-first and residual-Loss-first settlement order.

Acceptance:

- Valid current direct payout succeeds.
- Latest-but-stale direct payout fails specifically for source freshness.
- No payment, Accounting movement or audit artifact survives rejection.
- Existing signed boundaries around zero and repayment/recovery behavior remain valid.

### 3. Prove or fix the Loss cross-path race

- Use two independent PostgreSQL transactions for the same Company, Investor and confirmed Loss.
- Race an ordinary Profit/Loss offset of `80.00` against an Exit Loss application of `60.00` when confirmed Loss is `100.00`.
- Exercise both serial orders and one controlled interleaving.
- Verify both paths use a common lock/cap boundary through:
  - `investment_assert_profit_loss_offset_bounds()`;
  - `investor_exit_loss_application_guard()`.
- If the race fails, make the smallest forward-migration correction and rerun only the affected tests.

Acceptance:

- Combined committed settlement never exceeds `100.00`.
- One competing write blocks, serializes or fails cleanly.
- No duplicate cash movement, partial Accounting event or audit artifact survives.

## Final focused gate

Run only the meaningful checks needed for these changes:

1. Owner freshness test and boundary cases.
2. Exit Profit current/stale direct-DB cases and signed-position regression.
3. Loss cross-path concurrency test.
4. The previously selected Phase 8 backend regression set.
5. `manage.py check`.
6. `manage.py makemigrations --check --dry-run`.
7. `git diff --check`.
8. React tests/lint/build only if frontend source changed. Reuse the earlier successful evidence when frontend source is unchanged.

Verify actual committed database state after each concurrency or rejection case; command success alone is insufficient.

## Closure rule

Declare `PHASE 8 CLOSED LOCALLY` only when all three blockers pass with direct evidence and no A/B financial defect remains. If any gate fails, implement the bounded fix and rerun its focused test. If exact safe behavior requires an unresolved business rule, report `BUSINESS DECISION REQUIRED` with the precise dependency and stop only that dependent path.

## Required final report

Report in concise Malayalam:

- exact files changed and why;
- Owner freshness result;
- Exit Profit freshness result;
- Loss concurrency committed totals/result;
- commands actually run and pass/fail counts;
- final Git status;
- verdict: `PHASE 8 CLOSED LOCALLY` or the exact remaining blocker;
- confirmation that no commit, push, merge, deploy or living-doc update occurred.

Stop after the Phase 8 report. Wait for the user's separate instruction before updating docs.
