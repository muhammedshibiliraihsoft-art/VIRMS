# VIRMS agent instructions

- Communicate with the user in Malayalam/Manglish or English. Never use Tamil.
- Read README.md and the relevant documents under `/docs-final-v2/` before deriving current product behavior. `/docs-final-v2/` is the current approved/target direction; explicitly unresolved items remain `BUSINESS DECISION REQUIRED`. Current source code documents only implemented behavior. `/docs-final/` and `/docs-legacy/` are historical/superseded. Use the four `/architecture/01`–`04` maps to distinguish implemented state, V2 target, historical material and unresolved decisions. `/system-design/` and older architecture plans are historical V1-derived proposals unless a section has been explicitly reconciled with V2.
- Do not invent business, economic, permission or privacy rules. Escalate a genuine canonical conflict or missing required decision before implementing that behavior.
- Plan and audit only the current implementation phase after inspecting current main/staging and completed work. Do not pre-write all phase plans.
- Respect branch governance. Do not commit, push, merge, deploy or change frozen canonical documents without the applicable user authorization.
- Apply focused task tests, related batch regression and meaningful phase audits under the applicable `/docs-final-v2/` engineering standards.
- Classify work as ROUTINE, STANDARD or HIGH-RISK. Architecture, finance, corrections, tenancy, authorization, security, concurrency, financial migrations and settlement are HIGH-RISK; use the strongest reasoning configuration available in the active environment or recommend operator selection if automatic routing is unavailable. Do not depend on a named model.
