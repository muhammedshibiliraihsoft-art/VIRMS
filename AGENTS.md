# VIRMS agent instructions

- Communicate with the user in Malayalam/Manglish or English. Never use Tamil.
- For product behavior, consult only the relevant sections of README.md and `/docs-final-v2/`; reuse verified findings while those sources are unchanged. `/docs-final-v2/` is the current approved/target direction; explicitly unresolved items remain `BUSINESS DECISION REQUIRED`. Current source code documents only implemented behavior. `/docs-final/` and `/docs-legacy/` are historical/superseded. Consult the relevant `/architecture/01`–`04` map sections when that distinction affects the task. `/system-design/` and older architecture plans are historical V1-derived proposals unless a section has been explicitly reconciled with V2.
- Do not invent business, economic, permission or privacy rules. Escalate a genuine canonical conflict or missing required decision before implementing that behavior.
- Plan and audit only the requested phase. Check main/staging and completed work when a dependency, integration boundary, or branch decision requires it; do not pre-write other phase plans.
- Respect branch governance. Do not commit, push, merge, deploy or change frozen canonical documents without the applicable user authorization.
- Apply focused task tests, related batch regression and meaningful phase audits under the applicable `/docs-final-v2/` engineering standards. Stop after the requested goal; do not auto-start the next goal or phase.
- Update persistent documentation only after a completed and accepted development phase, or when the user explicitly requests it. During an unfinished phase, report needed document changes briefly in the task response. Preserve mandatory pre-implementation decisions, approvals, migration plans, and security records. At phase close, update only affected living documents whose verified truth changed; prefer GPT-6 Luna for documentation-only work when available without assuming automatic switching.
- Classify work as ROUTINE, STANDARD or HIGH-RISK. Architecture, finance, corrections, tenancy, authorization, security, concurrency, financial migrations and settlement are HIGH-RISK; use the strongest reasoning configuration available in the active environment or recommend operator selection if automatic routing is unavailable. Do not depend on a named model.

## Golden Rule — Dirty Work and Planning Efficiency

- At the start of a requested phase, inspect and record the current branch, worktree, dirty files, and relevant diffs once. Preserve all existing dirty work and identify its ownership before editing.
- Isolate the requested phase from unrelated work by scope and file ownership. Do not modify, reset, clean, stash, overwrite, or re-audit unrelated changes; this rule must not alter other project roles or workflows.
- Do not repeat a full-repository audit or complete Git inventory after every micro-change. Re-check only changed regions, affected dependencies, unresolved failures, or assumptions that changed.
- Use focused plans and focused tests during each cohesive slice, then one consolidated phase verification at phase completion. Avoid duplicate planning, repeated documentation reads, and low-value retests.
- If a dirty change overlaps the requested scope and ownership is unclear, preserve it, report the conflict, and make the smallest reversible change possible; do not silently assume it is disposable.
