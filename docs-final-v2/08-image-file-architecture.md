# 08 — Image & File Architecture

Status: DRAFT V2 — media source after approval

## Scope and ownership

The approved Vehicle publication capability retains up to four active images per Vehicle, each with immutable Image UUID, stable Company Vehicle UUID, display order, processing status and relevant metadata. When active images exist, exactly one is Primary/Public for cards, previews and approved public access. The Company is the Tenant isolation boundary; image Branch context follows current Vehicle and event history, not an independent Tenant identity. Moving a Vehicle between Branches does not duplicate its images or change its Company identity.

Accountant and Media User share one Media/Vehicle Publication capability with different field permissions. Media handles images, approved public fields, display information, publication and public availability only. Media cannot alter Purchased, In Work, Ready, Listed or Sold or see Investor, Company, Job-cost or other internal finance. Owner sees authorized Company media; Investor sees own Stock Vehicle images and permitted public images. External customer Garage Job records are private by default; this document does not grant public publication of customer work.

## Upload and processing

1. Validate authenticated role, Company, Branch/resource scope, Vehicle UUID, accepted content, size, dimensions and concurrency-safe four-active-image limit on the backend.
2. Store the original securely, create an Image record, generate optimized Thumbnail, Small, Medium and Large variants, and mark processing Ready or Failed.
3. Keep processing local to media so Vehicle text, Garage operations and finance stay usable. Retried requests must not create duplicate images.

Do not trust extension, browser MIME, supplied path or client-side image count. Validate actual content/signature, corruption and malicious content. Upload size is configurable for practical quality. Preserve camera orientation and remove unnecessary/private metadata such as public GPS location.

## Storage and delivery

Store binaries in object/file storage; relational records retain identity, Vehicle/Company and relevant Branch context, variant references, dimensions/aspect ratio, format, size, order, Primary flag, uploader and time. Cloudflare R2 is the current canonical provider behind a replaceable S3-compatible adapter. Production uploads do not rely on the application server filesystem as authoritative storage. Endpoint, bucket, access keys, optional public URL and other provider values are secure environment configuration, never domain constants or browser credentials.

Preserve the original for archival and variant regeneration; ordinary cards/lists/previews do not load it. Small selectors use Thumbnail, phone/cards Small, detail Medium or device-appropriate Large, and full-screen an optimized Large. Use responsive source selection, reserved aspect ratio, below-fold lazy loading, conservative prefetch and local image-failure placeholders/retry. The full-screen viewer preserves aspect ratio and provides touch swipe, desktop next/previous and keyboard controls without heavy effects. Core data never waits for media transfer.

## Publication, replacement and caching

Only explicitly published/eligible Vehicle media reaches the public catalog/API through a dedicated safe projection. Public lists normally show the optimized Primary image and approved fields; approved detail/gallery may show permitted variants. Do not expose private paths, protected original URLs, internal Vehicle/Investor/Accounting/Garage data or storage credentials. Authorized replacement/removal retains audit history and repairs Primary selection. Obsolete binaries may be cleaned only after record state is settled. Immutable/versioned variants support cache reuse; content changes get a new version/object. An Image UUID or known URL is not permission.

## Current non-scope

No video-processing pipeline, advanced image editor, AI generation/editing or social/comment features. A public external-customer Garage gallery is not implied by Stock Vehicle publication rules and would require separate approval.
