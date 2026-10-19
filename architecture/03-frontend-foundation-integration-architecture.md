# VIRMS — Frontend Foundation and Integration Architecture

> **Status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL PROPOSAL. CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the living maps. Missing V2 behavior is an **IMPLEMENTATION GAP**; unresolved meaning remains **BUSINESS DECISION REQUIRED**. This is not an approved V2 implementation contract. Do not infer V2 routes, permissions, page contracts or finance behavior from this proposal.

## Purpose and sequence

This file records a V1-derived frontend foundation proposal. Its sequencing and exit gate are not approved V2 requirements. Any later V2 frontend design must use the current target documents, verified backend contracts and current implementation evidence.

## Source Basis

### V2 target sources (business boundary only)

- `docs-final-v2/02-user-roles-permissions.md`
- `docs-final-v2/06-technical-architecture-engineering-operations.md`
- `docs-final-v2/07-ui-navigation-structure.md`
- `docs-final-v2/supporting/authentication-account-security.md`
- `docs-final-v2/supporting/production-engineering-standards.md`

### Historical System Design references

- `system-design/03-identity-tenancy-and-authorization.md`
- `system-design/07-backend-application-and-api-design.md`
- `system-design/08-frontend-and-ui-shell-design.md`
- `system-design/12-performance-observability-and-operations.md`
- `system-design/13-testing-verification-and-quality-strategy.md`
- `system-design/14-deployment-environments-and-release-design.md`

### Derived Architecture

- Use React 19, Vite, TypeScript, Tailwind CSS v4, React Router and TanStack Query.
- Provide one typed API-client boundary to real Django/DRF endpoints.
- Treat frontend permission and Tenant state as presentation/context only; the backend authorizes each request and object.
- Use TanStack Query for server state and local component/form state only for transient user input and presentation.

### Business decisions

No decisions are resolved by this historical proposal. Applicable V2 open decisions are listed in `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.

## Application shell and feature boundaries

Build the approved responsive shell and common interaction states as a small application foundation. Use the canonical shell reference and role-navigation rules; detailed module pages come with their integrated vertical slice. Routes organize the experience, lazy-loading where useful, but route guards only improve UX. A denied API response remains authoritative.

Feature areas consume API-client operations and authorized response types. Do not create a parallel frontend domain model that recalculates financial positions, decides eligibility or turns a disabled button into security. The frontend displays backend-provided current positions and action capability hints with source/context labels.

## Routing and role-aware navigation

- Use React Router for public-safe routes and authenticated application routes.
- Resolve authenticated identity, roles, authorized Company/Branch contexts and module availability from the backend session/API boundary.
- Render role-aware navigation based on returned capability hints; navigation visibility does not grant access.
- Resolve session expiry, forbidden, unavailable and not-found outcomes into explicit screen states.
- Changing Company/Branch context selects only from authorized contexts returned by the backend and refetches scoped resources. A client-supplied Company or Branch ID is never proof of access.

## Real API and authentication integration

The integration path is:

```text
React shell → typed API client → real DRF API → Django session/authentication
            → backend permission + Tenant/resource checks → PostgreSQL-backed response
```

Use VIRMS's Django/backend-controlled Username/Login ID and password flow. Integrate the approved secure session/cookie and CSRF mechanism for the deployment origin. Do not introduce a JWT/localStorage scheme, social login, self-service password recovery or another project's authentication behavior. Credentials and session tokens are not placed in application-managed persistent browser storage.

All reads and writes go through one API boundary with centralized base URL, credential/CSRF handling, request IDs and safe error translation. Financial amounts and authoritative calculations are sent/received in safe decimal representations; JavaScript floating-point arithmetic is not a business authority. A development mock may be used only as an isolated component aid; it cannot define request/response contracts, become the system integration path or satisfy the integration gate.

## Server state and Company/Branch context

TanStack Query owns request lifecycle, server cache, invalidation and refetch for API data. Query keys include the authenticated identity and authorized Company/Branch scope needed to prevent cross-session/Company cache reuse. On logout, account change or session loss, clear sensitive scoped caches. Mutations invalidate/refetch from committed backend responses; client optimistic updates must not present a financial write as committed before server confirmation.

Keep transient drafts, form values and view toggles in local state. Do not copy Fund balances, permissions, Company/Branch membership or derived finance into a competing global client store. Never trust cached role or Company/Branch state to authorize a request.

## Shared UI states and responsive behavior

The base shell supports:

- initial/loading, empty and stale/revalidating states
- field validation and business-rule rejection
- unauthorized/session-expired and forbidden
- privacy-safe not found
- conflict/stale version or idempotency conflict
- timeout, offline/interrupted request and server failure
- recoverable retry with bounded safe behavior and preserved form input where practical

Show success only after confirmed backend success. Disable duplicate submit for usability while relying on backend idempotency for correctness. Provide responsive desktop, laptop, tablet and lower-end-phone layout, safe areas, keyboard-open handling, accessible focus/touch targets, bounded payloads and usable slow-network states per canonical UI/production standards.

## Frontend Foundation integration exit gate

The Frontend Foundation passes only after a real end-to-end foundation path proves:

1. React shell loads in the configured environment.
2. User authenticates through the actual Django/backend-controlled session flow.
3. The API client makes a real request to DRF and handles CSRF/credentials as configured.
4. Backend authorization permits and denies requests based on role, membership and object scope.
5. An authorized Tenant-scoped response is rendered with the correct context.
6. Unauthorized, forbidden, loading, validation, conflict, timeout and server-error states are visible and safe.
7. No mock contract is the authoritative integration path; no client-side permission or financial rule can bypass the backend.
8. Relevant responsive and role-navigation checks pass.

## Frontend authority rule

Frontend is presentation and interaction only. It does not own business rules, financial calculations, permission decisions, Tenant access or audit truth. System Docs remain the technical contract; canonical business and permission documents remain the source of product behavior.
