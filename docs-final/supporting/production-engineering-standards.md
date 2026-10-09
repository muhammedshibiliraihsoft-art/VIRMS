# Production Engineering, Performance, Reliability & Safety Standards

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — SUPPORTING ENGINEERING SOURCE OF TRUTH

These are implementation quality standards, not independent business rules. Project-specific business, access and media behavior follow 01–08.

## Risk-based quality gates

- Correctness, authorization, Tenant isolation, data integrity, failure safety, performance, mobile usability, observability and regression safety are part of completion.
- Scale verification to the change: focused task tests; broader batch integration; deep phase audit at meaningful module/foundation/release boundaries. Do not repeat full project audits for tiny tasks.
- A performance change cannot remove required behavior, blur media unacceptably, reduce financial precision or weaken security.

## Mobile and frontend performance

- Design for lower-end phones, narrow screens, slow CPU, weak Wi-Fi and mobile data. Preserve usable layout with the keyboard open, adequate touch targets, correct input modes and safe-area support.
- Important UI releases should be checked near 360px width with slow/3G-like networking, CPU slowdown, cold cache, keyboard open and a network interruption during a request. Check actual Android and iPhone/iOS Safari where relevant, especially forms and mobile navigation.
- Avoid blank initial screens, excessive JavaScript, unnecessary dependencies and unbounded client-side tables. Split/load code where useful, measure real initial rendering, and keep the application shell stable.
- Support loading, empty, offline/timeout, validation and server-error feedback without false success or lost form data where avoidable. Consequential forms need a review step.
- Use semantic responsive layout, local error boundaries, accessible focus and keyboard controls, and restrained animation. Fonts and third-party scripts must not block core usability.

## Images and media

- Preserve secure originals; deliver optimized variants appropriate to displayed size and device. Never load raw originals in ordinary cards/lists or make a whole page wait for images.
- Reserve image aspect ratio to avoid layout jumps; lazy-load below-fold media; prefetch conservatively; paginate large media lists.
- Media failure is local with placeholder and retry. Compression preserves practical image clarity. Follow 08 for the current maximum of four active Vehicle images, upload security and public delivery.

## Network, API, and backend

- Set bounded timeouts and provide actionable timeout feedback. Retry only safe operations or requests protected by idempotency; use backoff rather than uncontrolled repeat storms.
- Where automatic retry is justified, use bounded exponential backoff and jitter. Writes must not blindly retry. Repeated dependency failures may need a circuit breaker; it does not replace frontend timeout, fallback and local error handling.
- Critical financial writes, uploads/finalization and settlement actions must resist double-clicks, network uncertainty, proxy retry, lost updates and concurrency. Buyer Payments cannot exceed current Remaining Receivable, Buyer refunds cannot exceed their outstanding correction-created payable, and Profit Payments cannot exceed current Outstanding Eligible Entitlement, including under simultaneous requests. Use appropriate transactions, constraints, locking/version checks and idempotency.
- Authoritative finance uses fixed-precision decimal arithmetic and the INR two-decimal `ROUND_HALF_UP` and deterministic residual-allocation rules in 05. Financial modules must not introduce binary floating-point authority or inconsistent rounding.
- Financial writes validate percentage bounds, nonnegative Outstanding Vehicle Principal and Available Fund, the Investor Principal Claim reconciliation including Owner return or Buyer principal-refund reserves larger than current Fund liquidity, and settlement closure conditions defined in 01, 04 and 05. Profit/Loss crossover corrections keep payout recovery, principal adjustments, Owner contributions, contribution returns and Buyer refund obligations separately traceable and cannot silently net them. Correcting the principal allocation of an existing Buyer receipt must not duplicate that receipt or its Fund effect; actual refund and payable/reserve release must be atomic and duplicate-safe.
- Optional dependency failures should degrade locally. Circuit breakers or kill switches are justified for risky dependencies/features, not required for every small feature.
- APIs provide consistent validation/errors, authorization, pagination, filtering/sorting, version evolution and public rate limiting where needed. Public and internal schemas are separate.
- Avoid N+1 queries, unbounded scans, excessive payloads and redundant requests. Measure query/response behavior and use indexes/caching based on evidence. Financial cache must remain reconciled with authoritative records.
- Set project-specific measurable performance budgets when implementation context is known. Relevant measurements include LCP, INP, CLS, JavaScript/route bundle size, API p95, database latency, image payload and query count; no arbitrary threshold is imposed by this document.
- Background jobs are bounded, observable, retry-safe, resumable for long work and Tenant-aware. Do not add a queue without an async workload.

## Availability, health, and readiness

- Production services provide lightweight health/liveness and readiness signals usable by monitoring and deployment infrastructure. A live process is not automatically ready to receive traffic.
- Readiness detects unavailable critical dependencies and startup, migration, or other states that prevent the required workload from being served safely. It must not produce a false-ready result. Non-critical degradation should remain localized and may be signaled separately.
- Checks expose no secrets or sensitive business data. Release/deployment validation verifies health and readiness behavior. Exact endpoints, paths, probes, and provider integration are implementation choices.

## Security, data, and operational safety

- Apply server-side validation, authentication, authorization, object checks, Tenant isolation, injection/XSS/CSRF/SSRF protection where applicable, secure secret handling, file validation and appropriate rate limiting.
- Validate actual uploaded content/MIME, size, dimensions, corruption and malicious content; never rely on filename extension alone.
- Database changes protect existing data, prevent partial writes and use controlled migration/backfill behavior. Large backfills are batched and resumable.
- Logs use safe structured context such as request ID, endpoint, Tenant and error class. Never log passwords, tokens or secrets. Monitor slow APIs/queries, failed jobs, repeated failures and media-processing failures.
- Production uses explicit environment identification, staging validation, safe deployment progression, backups, a tested restore path and a practical rollback/forward-fix route. Do not treat Production as a debugging sandbox.
- Infrastructure-as-code is optional until complexity justifies it. Avoid provider choices or infrastructure that block a controlled future adoption.
- Do not hard-code current Tenant/User/Vehicle/Investor counts as architectural limits. Explicit business limits, including the four-active-image rule, remain enforceable.

## Verification cadence

| Level | Trigger | Scope |
|---|---|---|
| Task | Each implementation change | Focused relevant tests and checks for changed behavior and obvious regressions |
| Batch | Logical related task set completes | Integration/regression across the batch |
| Phase | Major module, finance/auth/Tenant foundation, or production-readiness boundary | Deep relevant security, data, finance, performance, failure, history, observability and recovery audit |

Independent audit findings require reproduction/evidence against the actual repository before becoming fixes. Completion reports state what changed, how relevant behavior was verified and any material limitation.

## Automatic red flags

Silent catch, infinite retry/spinner, false success, lost form input, unbounded query, public endpoint without an appropriate authorization/rate policy, secrets in code or logs, full dataset fetch for simple filtering, full-resolution image in a thumbnail, financial write without duplicate protection, Owner/Tenant permission bypass, destructive migration without recovery, or deferring all relevant tests are release-blocking findings until resolved.
