# 09 — Media, storage and publication design

> **Reconciliation status: HISTORICAL / SUPERSEDED V1-DERIVED TECHNICAL DESIGN.** **CURRENT TARGET:** `/docs-final-v2/`. **CURRENT IMPLEMENTED:** repository source, as distinguished in the four living maps. The former `/docs-final/` and `/docs-legacy/` are historical. This document was derived from V1 rules and is not an approved V2 schema, API, permission, financial workflow, or implementation contract. Reuse a statement only where its business meaning is explicit in V2 and its technical claim is independently verified. Missing V2 code is an **IMPLEMENTATION GAP**, not evidence for V1. Unresolved meaning is **BUSINESS DECISION REQUIRED**. The remaining unreconciled content below is **HISTORICAL / SUPERSEDED**. See `/architecture/03-ARCHITECTURE-CONFLICT-MAP.md`.


Canonical sources: docs-final/02, 07, 08, 06 and production engineering standards.

## Asset identity and flow

Image UUID belongs to the Vehicle record; Vehicle supplies Tenant scope. Storage key/URL is replaceable infrastructure metadata, never an identity or permission token. Maximum four active images per Vehicle; if any active images exist, exactly one is Primary/Public. Accountant and Media share the capability with different field grants. Public availability/publication never changes the core Vehicle lifecycle.

1. Authenticate and authorize role, Vehicle and Tenant. Reserve an upload intent against the Vehicle under a lock so parallel Accountant/Media attempts cannot exceed four active slots.
2. Accept a bounded upload through a backend-controlled flow or short-lived tightly scoped upload authorization. A browser receives no permanent/admin R2 credential. Temporary objects are private and non-public.
3. Validate actual file signature/MIME, corruption/malicious content, dimensions, size and orientation. Reject mismatches; filename and browser MIME are not authority.
4. Preserve a secured original, strip unnecessary private metadata from delivery variants, and generate Thumbnail, Small, Medium and Large optimized versions. Store variant metadata/status in PostgreSQL.
5. Finalize image state under Vehicle lock, choose/repair Primary deterministically and record actor/time. Failed processing leaves a retryable Failed state and local UI fallback. Orphan temporary objects are cleaned after reconciliation.

R2 object write and PostgreSQL commit are not one ACID transaction. Use a Pending record/intent, idempotent object key scoped to image UUID/version, post-write verification and compensating cleanup. Publication reads only Ready assets whose approved Vehicle/publication state permits them. Any asynchronous processing is a technical option only when workload justifies a job system; an initial bounded synchronous path or simple retryable worker may be chosen in a phase plan after measurement.

## Adapter and access

Define a small S3-compatible object port for put, get/stream, delete, metadata and short-lived authorized delivery. Its Cloudflare R2 implementation and credentials live in infrastructure configuration. A replacement compatible provider changes adapter/configuration, not Vehicle/Image identity or business rules. R2 bucket, endpoint, region/signature settings, access keys and public/custom media URL come from secure environment configuration; production originals do not live on application-server disk.

Originals and internal variants are private by default. Authorized private delivery checks current User/Tenant/Vehicle scope or issues a short-lived scoped URL after that check. Public URLs or CDN access expose only permitted optimized versions for explicitly published eligible Vehicles. A known Image UUID or object URL never authorizes internal access. Unpublishing stops future public projection, invalidates/version-shifts cached references as appropriate, and never exposes the raw original. Public API returns safe metadata and normally the optimized Primary image; an approved gallery can return only allowed variants.

## Display, history and failure

Small selectors use Thumbnail, cards/phone preview Small, Vehicle detail Medium or suitable Large, full-screen device-appropriate Large. Reserve aspect ratio, use responsive source selection, lazy-load below-fold assets, and prefetch adjacent full-screen images conservatively. Viewer supports touch swipe and keyboard controls without hiding Vehicle text when media fails. Originals remain available for controlled archival/regeneration, not ordinary browsing.

Replacement/removal archives the old image record and preserves audit, repairs Primary, then safely cleans obsolete binaries after records settle. Changed variants use versioned immutable keys to avoid stale CDN images. A processing/storage failure is localized: show placeholder/retry, preserve Vehicle/finance access, log safe diagnostics and avoid infinite retries.
