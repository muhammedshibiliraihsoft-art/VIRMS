# Phase 8 Closure Implementation Plan

> **For agentic workers:** Follow this plan in order. The Superpowers `executing-plans` workflow may be used; its commit steps do not apply because this project requires separate authorization. Mark a gate complete only from observed evidence.

**Goal:** Correct the remaining financial database guard and prove Phase 8 settlement safety, then report whether Phase 8 can close.

**Architecture:** Keep Python services as the business source of truth and enforce the same critical bounds at PostgreSQL write boundaries. Use forward migrations for SQL guards and focused tests for stale sources and concurrent settlements.

**Tech stack:** Python 3.12, Django 5.2.18, PostgreSQL 15, React/Vitest.

**Spec:** This plan and the relevant Phase 8 sections of `docs-final-v2/`; code paths named below define observed current behavior.

## Completion checklist

- [x] B1 Owner payout: the worktree's `0044` migration and focused PostgreSQL test passed on Django 5.2.18. **Recheck** empty period fingerprint, Owner split change, predecessor carryforward, and SQL error reason before accepting B1 fully.
- [ ] B2 Exit Profit: prove whether a latest reconciliation with changed underlying sources permits direct payout; fix with exact source parity if it does.
- [ ] B3 Loss race: prove ordinary offset and Exit Loss application share the cap under concurrent writes; fix only if the race fails.
- [ ] Final focused integration gate and honest Phase 8 closure decision.

## Review focus

- Empty period and populated period hashes must match Python exactly.
- The Owner payment's pending Accounting event must not invalidate its own confirmation.
- Owner split or preceding carryforward changes must invalidate a payout.
- A newer source without a newer reconciliation must invalidate Exit Profit payout.
- Two Loss settlement paths must not commit more than the confirmed Loss.

**Target:** `D:\VIRMS\tmp\phase8-audit-corrections-20261120`, branch `codex/phase8-audit-corrections` at `166d4df` when inspected on 22 Nov 2026. Scope is Phase 8 only. Do not commit, push, merge, deploy, or update living docs without the user's later instruction.

## Start here

1. Read applicable `AGENTS.md`; check HEAD, branch, `git status`, and the affected diff once. Preserve all dirty work. At plan creation, `apps/accounting/tests/test_api.py` was modified and `apps/accounting/migrations/0044_owner_payment_source_freshness.py` was untracked. Their owner and validation status are unknown. **Inspect and continue these changes; do not replace or discard them.** If HEAD or these files change, use the current state.
2. Use only a fresh disposable PostgreSQL database. Never run synthetic financial mutations on staging or production. Verify Python 3.12 and Django 5.2.18. Reuse prior React evidence unless relevant UI changes.
3. Implement the three blockers below in order. Keep each correction source-linked, same-Company, transaction safe, and compatible with existing history. No new business policy.

## B1 — Owner payout freshness (confirmed defect)

**Evidence:** A valid direct DB Owner payout was accepted after a new income made the latest period confirmation stale. Python rejects stale sources; the existing SQL guard in `apps/accounting/migrations/0043_owner_payment_latest_confirmation_guard.py` checks only confirmation version. The in-progress `0044` migration and focused test now pass; remaining B1 boundary checks above still need evidence.

**Implementation:** Continue the existing `0044_owner_payment_source_freshness.py` and test diff; preserve their dirty state. Check the SQL helper against `apps/accounting/company_periods.py:current_confirmation_ids`: period Accounting event fingerprint, applicable Owner split, and predecessor carryforward freshness. Account for the pending Owner payment event so its own event does not invalidate the fingerprint. Keep the existing latest-version, allocation cap, role, Accounting ON, event, movement, and tenant checks. Repair `0044` only where a focused failing case proves a mismatch; first verify whether this migration has been applied to any database that must be preserved.

**Acceptance:** Focused PostgreSQL test must show valid partial payment succeeds; after an authorized source change, a structurally valid direct insert fails for **freshness** and leaves no payment/event/movement; old-version and cap checks still pass. Compare SQL fingerprint with Python for at least empty and populated periods. Reject failures caused by an unrelated constraint as inconclusive.

## B2 — Exit Profit reconciliation freshness

**Evidence to verify:** `apps/investment/migrations/0051_phase8_settlement_guard_parity.py` checks latest reconciliation version, Principal, Loss and signed payable. Python in `apps/investment/exit_settlement.py` checks current calculated source. A latest reconciliation may become stale without a newer row.

**Implementation:** Build one positive direct-SQL payout control in disposable PostgreSQL; change an underlying financial source through an authorized correction; retry with the latest-but-stale position. If the DB accepts it, add a forward guard migration that enforces current source parity. `apps/investment/finance.py:summarize_investor_profit_periods` hashes current Vehicle results, Deal payments, Interim payments and Loss offsets; `apps/investment/services.py:list_investor_profit_period_projection` compares that hash with reconciliation. Match those exact inputs and canonical ordering; do not add a weaker proxy. Preserve signed cap `confirmed_net - paid - future_applied + recovery_received + future_recovered`, Principal/Loss ordering, tenant/Accounting checks, and append-only history. If exact parity is not safely achievable, leave B2 blocked and report the specific gap.

**Acceptance:** Valid control succeeds; stale direct payout fails specifically for source freshness, with no surviving cash/audit artifacts. Include signed boundary checks around zero using existing focused tests where applicable.

## B3 — Cross-path Loss race

**Implementation:** In two separate PostgreSQL transactions for the same Company, Investor and confirmed Loss, race an ordinary offset (for example ₹80) against an Exit Loss application (₹60) when the Loss cap is ₹100. Exercise both serial orders and one interleaving. The ordinary path's `investment_assert_profit_loss_offset_bounds()` and Exit path's `investor_exit_loss_application_guard()` in `0051` both lock the Investor row; verify the committed sum and rollback behavior before changing the lock design.

**Acceptance:** Committed total never exceeds the confirmed Loss; no duplicate movement or partial event survives. If the test reveals a race, fix the shared lock/cap path and rerun only this focused test.

## Final gate and report

- Run affected Django tests on disposable PostgreSQL with pinned runtime, `manage.py check`, `makemigrations --check --dry-run`, and `git diff --check`. Run React tests/lint/build only if relevant frontend source changes; previous 16 focused React tests, lint and build passed on this SHA.
- Verify final Git status and the exact files changed. Phase 8 can close only when B1–B3 pass with direct evidence. Otherwise report the exact remaining blocker and stop; a time target cannot turn missing proof into PASS.
- Report the result to the user first. **Do not update docs until the user separately instructs it.**
