PRODUCTION ENGINEERING, PERFORMANCE, RELIABILITY & SAFETY STANDARDS
Reusable Standard for Production Software
Version: 1.0 FINAL
Status: LOCKED ENGINEERING SOURCE OF TRUTH
Scope: All production web applications / software developed under this workflow

0. PURPOSE
ഈ document business rules define ചെയ്യുന്നതല്ല.
ഇത് implementation സമയത്ത് Codex, developers, auditors എന്നിവർ follow ചെയ്യേണ്ട:
Performance
Reliability
Error Handling
Mobile UX
Image/Media
Backend
Database
Network
Security
Observability
Scalability
Deployment
Recovery
Production Readiness
standards define ചെയ്യുന്നു.

1. CORE PHILOSOPHY
ENG-CORE-001 — Developer Laptop Is Not Production
Application fast laptop + strong Wi-Fi മാത്രം നോക്കി build ചെയ്യരുത്.
Real user may have:
3–4 GB RAM phone
slower CPU
weak Wi-Fi
mobile data
unstable network
small screen
old Android
iPhone Safari
keyboard-open viewport
PDF-ലും developer environment vs 360px / low-RAM / weak-network phone difference പ്രധാന failure source ആയി കാണിക്കുന്നു.

ENG-CORE-002 — Working Is Not Done
Feature complete ആകാൻ:
Correctness + Security + Data Integrity + Failure Safety + Performance + Mobile Usability + Scalability + Observability + Regression Safety
consider ചെയ്തിരിക്കണം.

ENG-CORE-003 — Optimization Must Not Damage Functionality
Performance വേണ്ടി:
required feature remove ചെയ്യരുത്
image visibly blur ചെയ്യരുത്
financial accuracy reduce ചെയ്യരുത്
security weaken ചെയ്യരുത്
tenant isolation bypass ചെയ്യരുത്

2. RISK-BASED ENGINEERING GATES
ഓരോ task-നും എല്ലാ standards മുഴുവൻ run ചെയ്യേണ്ടതില്ല.
LEVEL A — ALWAYS
Relevant meaningful change-ൽ always check:
Correctness
Security
Permissions
Error handling
Data safety
Regression
Performance impact

LEVEL B — WHEN APPLICABLE
Feature touch ചെയ്താൽ മാത്രം:
Images
Caching
Pagination
Background jobs
Public API
Mobile forms
Third-party services
Heavy JS libraries

LEVEL C — HIGH-RISK
Mandatory deeper verification when touching:
Finance
Authentication
Authorization
Tenant isolation
Database migrations
Investor funds
Payments
Sale
Cash/Bank
Profit calculation
Financial corrections

LEVEL D — MILESTONE / RELEASE
Full audit only:
Phase completion
Production release
Infrastructure change
Major schema change
Architecture milestone
Original checklist also classifies work by tiers and requires evidence rather than subjective “looks fine” sign-off.

3. MOBILE-FIRST RESPONSIVE STANDARD
ENG-RESP-001
Every major screen must work from approximately:
360px mobile width upward.
No:
fixed desktop-only widths
sideways page scrolling
clipped content
The source guide explicitly recommends testing at 360px and preventing horizontal overflow.

ENG-RESP-002 — Mobile Is Not Small Desktop
Desktop, tablet and phone may share business logic.
But interaction/presentation may differ.
Desktop
mouse/keyboard friendly
richer table views
multi-column layouts
Tablet
touch-first
reduced columns
portrait + landscape
Phone
one-hand friendly
thumb reachable
compact
no tiny controls

ENG-RESP-003 — Touch Targets
Touch targets should normally be at least:
44–48px
with adequate separation.
No hover-only critical controls.

4. IMAGE & MEDIA ENGINEERING
ENG-IMG-001 — Quality First
Image optimization must not visibly destroy clarity.
Goal:
Maximum practical quality + minimum reasonable size + fast delivery

ENG-IMG-002 — Preserve Original
Store original upload securely.
Generate contextual variants:
Thumbnail
Small
Medium
Large
Original

ENG-IMG-003 — Never Load Full Original in Cards
List/grid/card surfaces must load correctly sized variants.
Use:
WebP / AVIF where appropriate
responsive delivery
srcset
sizes
DPR-aware variants
The guide similarly recommends WebP/AVIF and screen-sized responsive sources.

ENG-IMG-004 — Reserved Image Slots
Every image must have:
known width/height
or aspect-ratio
stable responsive slot
Image load കഴിഞ്ഞ് layout jump ചെയ്യരുത്.
This directly prevents the late-image layout shift described in the source guide.

ENG-IMG-005 — Loading Priority
First visible screen
Load first.
Below fold
Lazy load.
Near future page
Low-priority prefetch allowed.
Distant pages
Do not load.

ENG-IMG-006 — Image Failure Is Local
One image failure must never create:
whole-page error
whole app network error
blocked business data
infinite spinner
Only affected image slot should degrade.

ENG-IMG-007 — Project-Specific Slow Image Rule
Current vehicle/image-heavy project:
If image is slow:
Image is taking longer to load. Please check your network.
Message appears only in image area.
Text/data/actions remain usable.
Connection improves → retry image automatically/controlled.

5. IMAGE PAGINATION & PREFETCH
ENG-PAGE-001
Never load entire media collection.
Use:
server-side pagination
cursor pagination where justified
incremental loading

ENG-PAGE-002
Page/batch size must be configurable.
Example only:
Mobile:
~6–8
Larger screen:
~8–12
These are not hard-coded business rules.

ENG-PAGE-003 — Look-Ahead Loading
Current page visible items load normally.
As user approaches page end:
prefetch next metadata
optionally prefetch first few thumbnails
Do not prefetch multiple full future pages.

6. JAVASCRIPT & DEPENDENCY EFFICIENCY
ENG-JS-001
Do not install a large library for a tiny requirement when a reliable native/lightweight solution exists.
The source guide gives the example of avoiding a ~400KB date-picker dependency when native HTML can satisfy the requirement.

ENG-JS-002
Use:
route splitting
dynamic imports
lazy components
tree shaking
dead-code elimination

ENG-JS-003
Heavy features load only when needed where practical:
Calendar
Charts
PDF
Maps
Rich editors
AI modules
Heavy animation libraries

ENG-JS-004
Production assets must be:
minified
compressed
cached
fingerprinted/hashed

ENG-JS-005 — Dependency Budget
Before adding a dependency evaluate:
bundle size
runtime cost
parse cost
memory
security
maintenance
native alternative

7. INITIAL RENDERING
ENG-LOAD-001 — No Blank White Screen
Show quickly:
shell
layout
skeleton
essential structure
Do not block first paint waiting for all JavaScript.
The guide explicitly recommends getting a skeleton/page shell visible immediately.

ENG-LOAD-002
Core data must not depend on:
images
analytics
chat widgets
optional scripts
animation packages

8. MOBILE INPUT & FORM ENGINEERING
ENG-FORM-001
Mobile input text should normally be:
16px or greater
to prevent unwanted iPhone/Safari focus zoom.
The guide specifically identifies sub-16px fields as a cause of unwanted zoom.

ENG-FORM-002 — Correct Keyboard
Use correct semantic field/input mode.
Examples:
Text → normal keyboard
Phone → telephone keypad
Integer → numeric keypad
Decimal/Money → decimal keypad
Email → email keyboard
OTP → numeric + one-time-code

ENG-FORM-003
Numeric-looking identifiers are not automatically mathematical numbers.
Examples:
OTP
phone
PIN
postal code
IDs
Leading zeros must survive.

ENG-FORM-004 — Keyboard Safety
Keyboard open ആയാൽ:
current field hide ചെയ്യരുത്
submit action disappear ചെയ്യരുത്
validation error hidden ആകരുത്
Use modern dynamic viewport handling where appropriate.
The source guide highlights keyboard-covered forms/buttons and recommends dynamic viewport handling and focusing the invalid field.

ENG-FORM-005 — Large Form Preview
Long/critical forms:
Enter → Review → Confirm → Save
where appropriate.

9. NETWORK TIMEOUT STANDARD
ENG-NET-001
No request may run forever.
Every external/network request requires sensible timeout behavior.

ENG-NET-002
Every loading state must eventually become:
success
empty
validation error
network error
timeout
server error
retry
Infinite spinner = bug.

10. RETRY STANDARD
ENG-RETRY-001
Read operations may retry when safe.
Writes must not blindly retry.

ENG-RETRY-002
Automatic retry should use bounded:
exponential backoff
jitter
where appropriate.

ENG-RETRY-003
Localized failure should offer localized retry.
Do not force full-page reload unnecessarily.

11. IDEMPOTENCY & DUPLICATE SAFETY
ENG-IDEMP-001
Critical writes must be safe against duplicate processing.
Especially:
Payments
Investor Funds
Sales
Cash/Bank
Financial corrections

ENG-IDEMP-002
Rapid double-click/tap must not create duplicate write.
Use:
disabled submit
operation identifiers
idempotency keys
DB constraints where appropriate
The source checklist explicitly treats idempotency, partial failures and concurrent writes as data-safety concerns.

12. CIRCUIT BREAKER & DEPENDENCY RESILIENCE
ENG-CB-001
Circuit breaker belongs primarily around unstable external/backend dependencies where repeated failure may cascade.
Concept:
Closed → Open → Half-Open → Closed

ENG-CB-002
Circuit breaker does not replace frontend handling.
Frontend still needs:
timeout
retry
fallback
local error
graceful state

ENG-CB-003 — Graceful Degradation
Optional system failure must not kill core system.
Examples:
AI down → core ERP works
Image CDN slow → text works
Analytics fails → app works

13. ERROR HANDLING
ENG-ERR-001 — No Silent Failure
User-triggered operations must never silently fail.
If backend/database errors:
UI must not:
show success
show nothing
reset form silently

ENG-ERR-002 — Structured Errors
Backend should return predictable:
error code
safe message
field errors
request ID

ENG-ERR-003 — Field Errors
Show close to field.

ENG-ERR-004 — Form Errors
Show summary if multiple/business-level error exists.

ENG-ERR-005 — Preserve Input
Submission fail → keep entered values.
Especially finance/long forms.

ENG-ERR-006 — No False Success
Show success only after server/database confirms success.

14. ERROR BOUNDARIES
One frontend component crashing must not blank the entire application where isolation is feasible.
Affected component should show localized fallback.

15. NETWORK FEEDBACK
Where detectable:
Offline → “You appear to be offline.”
Timeout → “The request is taking longer than expected.”
Server issue → “Service is temporarily unavailable.”
Validation → exact correction.
Never convert one broken image into global “network unavailable”.

16. STATIC CACHE & COMPRESSION
Use appropriate:
Brotli
gzip
Cache-Control
hashed filenames
long-lived static caching
The guide explicitly recommends compression and long-lived caching for static assets.

17. FINANCIAL CACHE SAFETY
Financial truth must not become stale merely for speed.
Cache rules must respect data sensitivity.

18. FONT DELIVERY
Use:
font-display: swap
Avoid blocking text.
Load only required font weights.
The guide recommends immediate fallback text and limiting font weights.

19. SAFE-AREA SUPPORT
Phone UI must respect:
notch
system navigation
bottom home indicator
safe areas
Use safe-area inset handling where relevant.

20. THIRD-PARTY SCRIPT POLICY
Core application first.
Load later where possible:
analytics
heatmaps
chat
tracking tools
The guide recommends delaying these until the application is usable.
Remove tools nobody uses.

21. ANIMATION STANDARD
Prefer:
transform
opacity
Avoid unnecessary:
parallax
backdrop blur
expensive scroll animation
Especially mobile/low-end devices.
Respect:
prefers-reduced-motion
The guide calls out GPU-heavy animations and recommends this exact class of simplification.

22. BACKEND PERFORMANCE
ENG-BE-001
Do filtering/search/sorting/pagination server-side for large datasets.
Do not fetch 10,000 records and filter in browser.

ENG-BE-002
Add DB indexes based on actual query patterns.

ENG-BE-003
Avoid N+1 queries.

ENG-BE-004
Dashboard should use purpose-built summary APIs instead of downloading entire datasets.

ENG-BE-005
Heavy async work should move to jobs when appropriate:
image processing
PDF
large report
notification
AI processing

23. DATABASE SAFETY
Critical writes should use transactions.
Prevent:
partial commits
lost updates
duplicate records
race conditions
Use appropriate:
DB constraints
locking
transaction boundaries
version checks
The checklist emphasizes concurrency, partial-write consistency, reversible/controlled migrations and bounded backfills.

24. SECURITY BASELINE
Every application must consider:
server-side validation
authentication
authorization
tenant isolation
object-level authorization
SQL injection
XSS
CSRF where applicable
SSRF
file uploads
secrets
rate limiting
dependency security
The checklist requires authorization checks per endpoint, server-side validation, secret scanning and public-endpoint rate limiting.

25. FILE UPLOAD SECURITY
Validate:
actual MIME
size
dimensions
permitted file type
corruption
malicious payload
Never trust filename extension alone.

26. SCALABILITY STANDARD
Do not hard-code current:
tenants
users
vehicles
images
investors
as architectural limits.

ENG-SCALE-002
Do not over-engineer for millions of users unnecessarily.
Build:
easy to extend, not absurdly complex.

27. AVAILABILITY & FAILURE ISOLATION
One optional dependency failure must not crash the complete application.
Add:
health checks
readiness checks
degraded mode
where appropriate.

28. FEATURE FLAGS / KILL SWITCHES
Do NOT require a feature flag for every tiny feature.
Use for:
risky features
large new modules
difficult rollback
staged rollout
operationally dangerous functionality
This intentionally narrows the uploaded checklist's stricter “every feature needs an off-switch” approach.

29. OBSERVABILITY
Logs should be structured.
Useful context may include:
request ID
endpoint
tenant
safe user reference
status
error type
Never log:
passwords
tokens
secrets

ENG-OBS-002
Support correlation/request IDs.
User reports reference ID → developer finds request quickly.

ENG-OBS-003
Monitor:
slow APIs
slow queries
failed jobs
repeated failures
image-processing failures

30. BACKGROUND JOB STANDARD
Jobs must be:
idempotent where required
retryable safely
bounded
observable
resumable for long processes
Do not require queues if there is no async workload.

31. API STANDARD
APIs should support consistent:
errors
pagination
filtering
sorting
validation
authorization
version evolution
rate limiting where public
Public/private response schemas must be separated where sensitive data exists.

32. DEPLOYMENT STANDARD
Use:
Local → Staging → Production
Do not test risky production changes directly on live data.

ENG-DEPLOY-002
Migration changes require:
compatibility consideration
rollback/recovery thinking
destructive-change protection

ENG-DEPLOY-003
Terraform/IaC is optional until infrastructure complexity justifies it.
Do not architect infrastructure so it becomes impossible later.

33. BACKUPS & RECOVERY
Production data requires backups.
Important backups must have a known restore procedure.
A backup that has never been restored/tested should not be blindly trusted.

34. PERFORMANCE BUDGETS
Performance must eventually be measurable.
Relevant metrics may include:
LCP
INP
CLS
JS size
route bundle
API p95
DB latency
image payload
query count
The uploaded checklist also uses measurable budget/sign-off fields rather than subjective speed claims.
Exact thresholds must be set per project.

35. LOW-END DEVICE TESTING
Before important release test with:
~360px width
slow/3G-like network
CPU slowdown
cold cache
keyboard open
network disabled mid-request
The Codikko guide specifically proposes this DevTools test flow.

36. REAL DEVICE TEST
Important UI releases should be checked on actual:
Android
iPhone/iOS Safari where relevant
especially forms/mobile navigation.

37. CODEX TASK COMPLETION GATE
For every meaningful task, Codex should answer only relevant questions:
ALWAYS
Did the requested feature work?
Are permissions correct?
Can data be corrupted?
Can it silently fail?
Are relevant errors visible?
Are relevant tests passing?
Did existing behavior regress?
WHEN UI IS TOUCHED
mobile works?
keyboard works?
loading/error/empty states?
layout shifts?
touch targets?
WHEN DATA/API IS TOUCHED
authorization?
pagination?
validation?
transactions?
N+1?
indexes?
concurrency?
WHEN FINANCE IS TOUCHED
idempotency?
atomicity?
audit?
history preserved?
duplicate prevention?
tenant isolation?
WHEN IMAGE/MEDIA IS TOUCHED
correct variants?
lazy loading?
reserved slot?
slow image local failure?
original preserved?
storage/CDN safe?

38. MILESTONE / PHASE AUDIT GATE
At phase completion run broader review covering:
architecture
security
finance
tenant isolation
performance
data safety
scaling
deployment
recovery
observability
This is where the long checklist belongs.
Not after every tiny Codex task.

39. CODEX / DEEPSEEK WORKFLOW
Codex
Primary responsibility:
Implementation
Targeted tests
Task-level verification
Evidence/report

DeepSeek
Primary responsibility:
Independent milestone audit
Architecture audit
Security audit
Finance audit
Performance audit
Cross-module audit

Audit Finding Rule
DeepSeek finding ≠ automatically true.
Classify finding as:
VERIFIED — FIX
VALID / LOW PRIORITY
NOT REPRODUCIBLE
AUDITOR ASSUMPTION
BUSINESS DECISION REQUIRED
Only verified findings become Codex fix tasks.

40. GLOBAL FAILURE RULE
LOCKED — CRITICAL
No failure should become:
blank screen
silent error
infinite spinner
lost form input
duplicate transaction
false success
whole-page failure because one image failed
unexpected layout jump
unnecessary reload

41. GLOBAL PERFORMANCE RULE
LOCKED
Fast network → application should be fast.
Slow network → application should be smart.

42. GLOBAL CODE RULE
LOCKED
Users should not download, parse or execute code for functionality they are not currently using unless preloading is intentionally justified.

43. GLOBAL MEDIA RULE
LOCKED
Heavy media must degrade locally, not globally.

44. GLOBAL COMPLETION RULE
A production feature is complete only when relevant aspects of:
correctness
security
data safety
permissions
tenant isolation
failure handling
performance
mobile UX
observability
tests
have been considered.

45. ANTI-PATTERNS — AUTOMATIC RED FLAGS
“Works on my machine.”
Silent catch
Infinite retry
Infinite spinner
Unbounded query
Secrets in code/logs
Public endpoint with no authorization/rate policy where needed
Full dataset fetch for simple filtering
Full-resolution image loaded in thumbnail card
Financial write with no duplicate protection
Owner/tenant permission bypass
Destructive migration without recovery thinking
“We'll add tests later.”
Several of these also appear as automatic-fail patterns in the supplied completion checklist.

46. FINAL STATUS
Document: Production Engineering, Performance, Reliability & Safety Standards
Version: 1.0
Status: FINAL — LOCKED SOURCE OF TRUTH
This standard is reusable across projects.
Project-specific rules may extend this document but must not silently weaken:
Security
Data Integrity
Reliability
Failure Safety
Performance baseline
Authentication/password/account lifecycle is maintained in the separate Roles, Permissions & Authentication source-of-truth and is intentionally not duplicated here.
