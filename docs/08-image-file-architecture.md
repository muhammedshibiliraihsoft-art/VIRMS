# 08 — IMAGE & FILE ARCHITECTURE

Vehicle Investment, Modification & Resale Management System

Version: Draft v1.0
Status: REVIEW REQUIRED — LOCK AFTER APPROVAL


## 1. PURPOSE

This document defines the architecture for Vehicle image:

- ownership
- upload
- storage
- optimization
- variants
- display
- full-screen viewing
- performance
- permissions
- failure handling
- public delivery

Current scope is primarily Vehicle images.

Image processing must never materially slow down the core software experience.


## 2. CORE IMAGE RULES

IMG-001
Every image belongs to a specific Vehicle.

IMG-002
Each Vehicle may have a maximum of:

`4 active images`

The limit must be enforced by the backend, not only by the frontend.

IMG-003
Vehicle images are business records linked using immutable Vehicle/Image UUIDs.

Filename, image order or image URL must never be used as identity.

IMG-004
Image quality must remain visually clear after optimization.

Goal:

`High visual quality + reasonable file size + fast delivery`

IMG-005
Image loading must never block:

- Vehicle data
- financial data
- page navigation
- forms
- actions
- application shell

IMG-006
One failed/slow image must affect only that image slot.


## 3. SHARED MEDIA / VEHICLE PUBLICATION MODULE

Use one shared module:

`Media / Vehicle Publication`

Do NOT create duplicate image modules for Accountant and Media User.

The same module is available according to role permissions.

### Accountant

May manage:

- Vehicle images
- permitted Vehicle/public details
- public display price
- publication status
- permitted vehicle/publication status

### Media User

May manage only permitted public-facing:

- Vehicle images
- Vehicle public details
- public display price where authorized
- publication status
- permitted public Vehicle status

Media User must never access:

- Investor Fund
- Investor private data
- Purchase Cost
- Internal Expenses
- Internal Profit/Loss
- Investor Share
- Owner Shares
- Settlement finance
- financial corrections
- protected configuration

### Owner

Read-only image/media visibility.

### Investor

Own Vehicle images and approved public-level Vehicle images only, according to existing permission rules.


## 4. VEHICLE IMAGE SET

A Vehicle image collection contains:

- 1–4 active images
- display order
- one Primary/Public Image
- upload metadata
- processing status

The Primary/Public Image is used by default for:

- Vehicle cards
- lists
- public catalog
- public API
- previews

Authorized users must be able to manage image order and choose the Primary image.

Changing Primary image does not change image identity.


## 5. IMAGE UPLOAD FLOW

Conceptual workflow:

Select Vehicle
→ Select Image(s)
→ Client-side basic validation
→ Secure Upload
→ Backend validation
→ Store Original
→ Generate Optimized Variants
→ Attach to Vehicle
→ Mark READY

Possible processing states:

- UPLOADING
- PROCESSING
- READY
- FAILED

The application must remain usable while image processing occurs.

Do not keep the entire page blocked until all image variants finish processing.


## 6. UPLOAD VALIDATION

Validate at minimum:

- authenticated user
- role permission
- Tenant/Vehicle access
- Vehicle UUID
- maximum 4 active images
- accepted image type
- file signature / actual MIME type
- file size
- valid image dimensions
- corrupted file detection

Do not trust:

- filename extension
- browser MIME value alone
- client-provided storage path

Maximum upload file size must be configurable.

Do not use an unnecessarily low hard-coded limit that destroys practical image quality.


## 7. ORIGINAL IMAGE

The original uploaded image should be preserved securely.

Original exists for:

- archival quality
- future regeneration of variants
- future format/quality changes
- controlled high-quality access

The raw original must NOT normally load in:

- cards
- lists
- tables
- grids
- normal Vehicle previews

Original storage and optimized delivery are separate concerns.


## 8. IMAGE VARIANTS

Generate contextual variants from the original:

1. Thumbnail
2. Small
3. Medium
4. Large
5. Original

Conceptual usage:

| Variant | Typical Use |
|---|---|
| Thumbnail | small lists / selectors |
| Small | compact cards / phone previews |
| Medium | normal Vehicle detail |
| Large | full-screen / large display |
| Original | archival / controlled explicit use |

Exact pixel dimensions and compression quality are technical configuration values and should remain adjustable without changing business logic.


## 9. FORMAT & COMPRESSION

Generated delivery variants should use modern optimized formats where supported:

- AVIF
- WebP
- suitable fallback format where required

Compression must prioritize:

`clarity first`

Do not aggressively compress an image merely to reach an arbitrary tiny byte size.

Optimization should consider:

- source dimensions
- target display dimensions
- format
- visual quality
- device pixel ratio
- network cost

Large images should be automatically resized/compressed to practical production sizes.

The user must not be required to manually compress images before upload.


## 10. ORIENTATION & METADATA

On processing:

- respect camera orientation
- normalize image orientation
- preserve required visual quality
- remove unnecessary/private metadata where appropriate

Sensitive metadata such as GPS/location metadata should not be exposed publicly by default.


## 11. STORAGE ARCHITECTURE

Image binary files belong in dedicated object/file storage, not inside normal relational database fields.

Database stores image metadata such as:

- Image UUID
- Vehicle UUID
- Tenant context
- storage reference/key
- variant references
- width
- height
- aspect ratio
- format
- file size
- display order
- Primary flag
- processing status
- uploaded by
- created timestamp

Do not make storage provider URLs permanent business identity.

The exact storage/CDN provider belongs to deployment architecture and may be changed later without redesigning Vehicle records.


## 12. VEHICLE RELATIONSHIP

Relationship:

`Vehicle 1 → maximum 4 active Vehicle Images`

Each image belongs to exactly one Vehicle in the current scope.

Relevant Tenant context is inherited/validated through the Vehicle.

An image must never become visible under an unauthorized Tenant merely because a URL or Image UUID is known.


## 13. IMAGE VIEWING — NORMAL UI

Vehicle list/grid/card:

- use Thumbnail/Small variant
- never load Original
- reserve image aspect ratio before load
- prevent layout shift
- lazy-load images not currently visible

Vehicle detail:

- show optimized preview
- show all available Vehicle images
- allow image selection
- current image changes without full page reload

Image display must remain visually clean and consistent across:

- Desktop
- Tablet
- Phone


## 14. FULL-SCREEN IMAGE VIEWER

Selecting an image must allow a dedicated full-screen image viewer.

Viewer requirements:

- image receives maximum practical screen area
- no normal software card/container border around the image
- no unnecessary decorative UI
- dark/neutral viewing backdrop where appropriate
- preserve image aspect ratio
- never distort or stretch image
- smooth opening/closing
- lightweight interaction only

The viewer should use the best optimized variant appropriate to the current screen.

Do not automatically download the raw Original merely because the viewer is full-screen.


## 15. SWIPE / GALLERY NAVIGATION

When a Vehicle has multiple images:

Phone / Tablet:
- horizontal swipe between images

Desktop:
- next/previous controls
- keyboard navigation where appropriate
- thumbnail/direct selection may also be available

Swipe/navigation must feel immediate and lightweight.

Avoid heavy animation libraries for a simple gallery.

Do not implement distracting transition effects.


## 16. ADJACENT IMAGE PRELOAD

When full-screen viewing Image 2:

- current image loads at required priority
- next/previous optimized image may be prefetched
- do not unnecessarily load all raw Originals

Because each Vehicle has maximum four images, controlled adjacent preloading is acceptable.

Prefetch must not compete aggressively with critical application requests.


## 17. RESPONSIVE IMAGE DELIVERY

Frontend should request an image appropriate to:

- viewport
- display slot
- DPR/device density

Use responsive image delivery concepts such as:

- `srcset`
- `sizes`
- appropriate image variants

Example principle:

Phone card
→ Small

Desktop card
→ Small/Medium

Vehicle detail
→ Medium/Large

Full-screen
→ Large / best device-appropriate optimized version

Do not send a 4K/original image to a small card.


## 18. LOADING PRIORITY

Loading priority:

### First visible / important Vehicle image
Load normally/high priority where justified.

### Below-fold images
Lazy load.

### Full-screen selected image
High priority after user selection.

### Adjacent gallery images
Low-priority controlled prefetch.

### Images on distant pages
Do not load.

Core application data must render independently of images.


## 19. PLACEHOLDER & LAYOUT STABILITY

Before image loading completes:

- reserve image slot using known aspect ratio
- show lightweight placeholder/skeleton where appropriate

Image arrival must not cause:

- major layout shift
- card jumping
- buttons moving unexpectedly
- content reflow that damages usability


## 20. SLOW IMAGE BEHAVIOR

If an image takes unusually long:

show a localized message inside that image area, for example:

`Image is taking longer to load. Please check your network.`

Requirements:

- page remains usable
- Vehicle text remains visible
- actions remain usable
- no whole-page loading screen
- no infinite spinner
- allow controlled retry

Improved network conditions may trigger a safe retry.


## 21. IMAGE FAILURE

A broken image must degrade locally.

Do not:

- crash Vehicle page
- block Vehicle API response
- block financial information
- display infinite spinner
- force full application reload

Show:

- placeholder
- failure state
- retry action where useful


## 22. CACHE & CDN DELIVERY

Optimized immutable image variants should support efficient CDN/browser caching.

Use:

- cache-friendly versioned/hashed objects
- long-lived caching for immutable variants
- new object/version when image content changes

Do not repeatedly re-download unchanged Vehicle images.


## 23. REPLACEMENT / REMOVAL

Authorized media management must support correcting an incorrect Vehicle image.

A replacement should not overwrite unrelated Vehicle image records silently.

When an image is removed from active display:

- detach/deactivate safely
- update Primary image when required
- preserve appropriate audit metadata
- clean obsolete storage asynchronously where safe

Removing one image must not affect other Vehicle images.


## 24. CONCURRENCY & FOUR-IMAGE LIMIT

The `maximum 4 active images` rule must remain correct even when:

- two tabs upload simultaneously
- Accountant and Media User upload at the same time
- a request is retried

Backend must perform a concurrency-safe limit check.

Do not rely only on:

`if frontend count < 4`

Upload/finalize operations should be duplicate-safe where appropriate.


## 25. PUBLIC VEHICLE IMAGE DELIVERY

Only explicitly published/eligible Vehicle media may be exposed through public Vehicle access.

Public API/list responses should normally return:

- Primary/Public optimized image
- safe image metadata/URLs required by the client

If a public Vehicle detail/gallery is approved, it may return the permitted gallery variants.

Public APIs must not expose:

- private storage paths
- upload internals
- protected original URLs
- unrelated internal Vehicle data
- financial data


## 26. PERFORMANCE INVARIANTS

IMG-PERF-001
Images must never delay core business data unnecessarily.

IMG-PERF-002
Cards/lists never use full Original images.

IMG-PERF-003
Only appropriate responsive variants are requested.

IMG-PERF-004
Below-fold media is lazy-loaded.

IMG-PERF-005
Image processing should not block normal request processing where background processing is appropriate.

IMG-PERF-006
A slow/failing image remains an image-level failure.

IMG-PERF-007
Avoid heavy gallery/image libraries unless clearly justified.

IMG-PERF-008
Image caching must prevent unnecessary repeated network transfer.


## 27. SECURITY REQUIREMENTS

Image upload requires backend authorization.

Validate:

- role
- Vehicle access
- Tenant context
- file type/content
- upload size
- image validity

Use controlled storage access.

Never expose internal storage credentials.

Public access must use public-safe delivery rules.

Media User permissions remain limited to public/media scope.

Image metadata must not become a path to internal financial information.


## 28. CURRENT NON-SCOPE

Do not introduce without a later approved requirement:

- unlimited Vehicle images
- video processing pipeline
- advanced photo editor
- AI image generation/editing
- image comments/social features
- separate Accountant image module
- separate Media User image module
- storing binary images directly in normal database rows
- loading raw originals in normal UI
- heavy gallery animation system


## 29. END-TO-END FLOW

Authorized Accountant / Media User
→ Select Vehicle
→ Add up to 4 Images
→ Validate
→ Upload Original
→ Process
→ Generate Optimized Variants
→ Attach to Vehicle
→ Choose/maintain Primary Image
→ Display optimized previews
→ Open Full-Screen Viewer
→ Swipe / Navigate
→ Public delivery only when eligible


## 30. NON-NEGOTIABLE RULES

1. Maximum 4 active images per Vehicle.
2. Every image belongs to a Vehicle.
3. Accountant and Media User use the same Media / Vehicle Publication module.
4. Media User never receives internal finance access.
5. Original quality source is preserved securely.
6. Normal UI never loads full Original unnecessarily.
7. Generate optimized Thumbnail/Small/Medium/Large variants.
8. Automatic compression must preserve practical visual clarity.
9. Thumbnail/list images and full-screen images use different appropriate variants.
10. Image selection opens a clean full-screen viewer.
11. Multi-image Vehicles support swipe/navigation.
12. Full-screen viewer must not be surrounded by normal software card borders.
13. Images must not block core software loading.
14. Below-fold images lazy-load.
15. Adjacent gallery preloading must be controlled.
16. Image failure remains local.
17. Layout must not jump when images load.
18. Four-image limit is backend-enforced and concurrency-safe.
19. Public delivery exposes only safe/published media.
20. Storage/provider choice must remain replaceable without changing Vehicle identity.


## 31. DOCUMENT STATUS

08 — IMAGE & FILE ARCHITECTURE

Version: Draft v1.0
Status: REVIEW REQUIRED

After approval:

Status:
`LOCKED — AUTHORITATIVE SOURCE OF TRUTH FOR IMAGE / MEDIA ARCHITECTURE`


