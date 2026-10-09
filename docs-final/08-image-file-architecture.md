# 08 — Image & File Architecture

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH

## Scope and ownership

Each Vehicle has up to four active images, each with immutable Image UUID, Vehicle UUID, display order, processing status and relevant metadata. When active images exist, exactly one is the Primary/Public image used by cards, previews and approved public access. Image Tenant scope derives from the Vehicle and must be backend-validated. Storage keys and provider URLs are not business identity.

Accountant and Media User use one shared Media / Vehicle Publication capability under different permissions (02). Media handles images, approved public fields, display information, publication and public availability only; it cannot change Purchased, In Work, Ready, Listed or Sold or see internal finance. Owner can view authorized media; Investor sees own Vehicle images and permitted public images.

## Upload and processing

1. Validate authenticated role, Tenant/Vehicle access, Vehicle UUID, accepted image content, size, dimensions and the four-active-image limit on the backend.
2. Store the original securely, create an Image record, generate optimized Thumbnail, Small, Medium and Large delivery variants, and mark processing Ready or Failed.
3. Keep upload/processing localized so the main application and Vehicle text remain usable. Support safe retry and avoid duplicate images from request retries.

Do not trust filename extension, browser MIME, supplied storage path, or client-side count. Validate actual MIME/signature, corruption and malicious content. Upload size is configurable and must support practical quality. The four-active-image limit is concurrency-safe even with simultaneous Accountant/Media uploads.

## Original, metadata, and storage

- Preserve the original for archival and variant regeneration; do not load it in ordinary cards, lists, grids or previews. Full-screen viewing uses the best device-appropriate optimized variant, not automatically the raw original.
- Respect camera orientation; remove unnecessary/private metadata such as public GPS location. Keep visual clarity while automatically resizing/compressing practical delivery variants. Modern optimized formats may be used with suitable fallback.
- Store binaries in file/object storage; relational records retain UUIDs, Vehicle/Tenant context, variant references, dimensions/aspect ratio, format, size, order, primary flag, processing status, uploader and time.
- Storage provider may change without changing Vehicle/Image identity. Never expose storage credentials, private paths or protected original URLs through public APIs.

## Display and delivery

| Context | Delivery |
|---|---|
| Small list/selector | Thumbnail |
| Card or phone preview | Small |
| Vehicle detail | Medium or device-appropriate Large |
| Full-screen viewer | Device-appropriate optimized Large |
| Archival/controlled use | Original |

Use responsive source selection for viewport, slot size and display density. Reserve aspect ratio before loading to prevent layout jumps. Lazy-load below-fold images and avoid requesting distant-page media. A selected full-screen image has priority; adjacent images may be prefetched conservatively. Core data must not wait for image transfer.

The viewer gives the image practical screen space, preserves aspect ratio, avoids normal card borders, and supports swipe on touch devices plus next/previous and keyboard controls on desktop. Avoid heavy gallery dependencies and distracting effects.

Slow or broken images show a local placeholder/message and optional retry; they do not crash the page, hide Vehicle text, block finance, or cause an endless spinner.

## Publication, replacement, and caching

- Only explicitly published/eligible Vehicle media reaches public catalog/API responses. Public lists normally expose the optimized Primary image and safe metadata; an approved detail/gallery may expose permitted optimized variants.
- Authorized replacement/removal preserves appropriate audit history, repairs Primary selection when needed, and never silently overwrites unrelated image records. Obsolete binaries may be cleaned safely after record state is settled.
- Immutable/versioned optimized variants support browser/CDN caching; changed content uses a new version/object. Do not repeatedly transfer unchanged images.
- Image access always checks Vehicle/Tenant scope. Knowing an Image UUID or URL is not access permission. Public media responses never expose internal Vehicle or financial fields.

## Out of current scope — requires future approval

The current Vehicle image/media capability does not include a video-processing pipeline, an advanced photo/image editing suite, AI image generation or AI image editing, or image comments/social-interaction/social-media-style features. These capabilities may be considered only through a future explicitly approved requirement; their omission from the current architecture is not permission to implement them.
