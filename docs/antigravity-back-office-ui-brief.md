# VIRMS Back Office UI — Antigravity Brief

**Status:** UI implementation brief; not implemented yet  
**Prepared:** 2026-11-17  
**Target:** `demo/react` frontend in the current VIRMS worktree

## Goal

Give Platform Back Office users a clear, responsive VIRMS landing page for reaching the administration screens they use most. Keep the visual language consistent with the existing VIRMS main interface. The dashboard is a navigation and orientation layer; Django Admin remains the source of truth for the actual administrative actions.

This brief does not authorize changes to backend permissions, business rules, database/schema, or module state. It does not replace Django Admin forms.

## Verified current behavior

- Frontend stack: React 19, TypeScript, Vite, Tailwind CSS v4, React Router, and TanStack Query (`demo/react/README.md`, `docs-final-v2/06-technical-architecture-engineering-operations.md`).
- `AuthContext` identifies a Platform user from the server-provided top-level `AuthMe.roles` value containing `back_office` (`demo/react/src/auth/AuthContext.tsx`).
- `AppRoutes` currently redirects authenticated Platform users to `/admin/` (`demo/react/src/auth/AppRoutes.tsx`).
- Vite forwards `/admin/`, `/static/`, and `/api/v1` to Django in local development. Production must provide equivalent same-origin routing, as documented in `demo/react/README.md`.
- Current registered administration areas include Companies, Branches, Users, Company memberships, Company role grants, Branch assignments, and versioned Company module state. The module-state configuration screen is `/admin/tenants/companymodulestate/configure/` (`apps/tenants/admin.py`, `apps/accounts/admin.py`).
- The Platform role is separate from Company business roles. The Back Office dashboard must not grant Company finance-posting authority (`architecture/02-API-FLOW.md`, `docs-final-v2/02-user-roles-permissions.md`).
- The existing main interface uses the VIRMS orange theme tokens, Plus Jakarta Sans, light/dark styling, and solid dashboard surfaces (`demo/react/src/index.css`).

## Recommended UI shape

Create a focused Platform Back Office home inside the existing React application. Keep it visually related to the VIRMS main shell, but do not force the Company-business `AppShell` navigation or Company dashboards onto Platform users.

### Header

- VIRMS identity and the page title **Platform Back Office**.
- Show the authenticated Login ID from existing auth context when available.
- Provide a compact, clearly labelled sign-out action using the existing logout flow.
- Do not show Company/Branch as selected context unless it is explicitly present in the authenticated server context.

### Main content

Use compact, clearly grouped navigation items with a short description and a visible link affordance:

| Group | Item | Existing destination |
|---|---|---|
| Companies & locations | Companies | `/admin/tenants/tenant/` |
| Companies & locations | Branches | `/admin/tenants/branch/` |
| Accounts & access | User accounts | `/admin/accounts/user/` |
| Accounts & access | Company memberships | `/admin/tenants/tenantmembership/` |
| Accounts & access | Company role grants | `/admin/tenants/companyrolegrant/` |
| Accounts & access | Branch assignments | `/admin/tenants/branchassignment/` |
| Company configuration | Module configuration | `/admin/tenants/companymodulestate/configure/` |

Keep the list easy to scan on a phone. On wide screens, arrange the groups in a compact grid that follows the existing content width and spacing. Each item should remain a touch-friendly, keyboard-accessible link.

Do not show fabricated counts, activity, health, enabled-module badges, audit history, financial settings, or protected-rate summaries. Add those only after an authoritative endpoint or existing permission-checked screen is verified and approved for this surface. The module-configuration link opens the existing form; it must not mutate module state from the dashboard itself.

## Route and navigation integration

- Replace the current Platform-only redirect behavior in `demo/react/src/auth/AppRoutes.tsx` with the Back Office home for authenticated users whose server-provided role includes `back_office`.
- Preserve the existing login, first-password-change, anonymous, unavailable, and Company-user route behavior.
- Keep Django Admin directly reachable. Use ordinary full-page anchors for `/admin/...` links so the request reaches Django through the configured proxy; do not use React Router links for these destinations.
- Keep the current `/api/v1/auth/me/` call as the source of Platform identity. Do not add a new dashboard API or request module state merely to render navigation links.
- Keep sign-out on the existing session/CSRF logout API and clear client auth/query state through the established auth context.

## Project UI standards

- Reuse existing colors and semantic theme variables such as `--theme-primary`, `--theme-primary-soft`, `--theme-card-bg`, and `--theme-card-border`; preserve light/dark behavior.
- Use the existing typography, spacing, card, button, focus, and border-radius patterns. Keep the page compact and content-first; avoid a new visual language, oversized hero area, heavy gradients, decorative charts, or shadow-heavy cards.
- Design mobile-first and verify layouts at 320, 768, 1024, and 1440 CSS pixels. Prevent horizontal overflow, clipped labels, and fixed navigation overlap. Keep text wrapping safe for long labels.
- Use semantic headings and links, visible keyboard focus, adequate contrast, and text labels alongside status/icon meaning. Icon-only controls need accessible names.
- Provide clear loading, signed-out/session-expired, forbidden, and unavailable states consistent with existing auth behavior; never render an empty or falsely successful dashboard.
- Keep implementation focused in the existing `demo/react/src/auth/` route/auth area and shared theme/components where reuse is appropriate. Do not refactor Company business screens to make room for this page.

## Security and data boundaries

- Frontend role checks are presentation only. Django Admin and the backend remain responsible for authentication, object scope, Company scope, action authorization, CSRF, validation, and audit.
- Never add a client-side permission bypass, trust a Company/Branch ID supplied by the URL as authorization, or fetch broad private Company data just to hide it in the UI.
- Do not change Django roles, `is_staff`, `is_superuser`, memberships, or Branch assignments as part of this frontend task.
- Do not link to unimplemented Audit, protected financial configuration, or financial-review screens. Do not imply that the dashboard itself changes permissions or module states.

## Acceptance criteria for Antigravity

1. An authenticated Platform Back Office user sees the new VIRMS-styled landing page rather than being immediately redirected to Django Admin.
2. Existing Company-user pages, role navigation, login, password-change, session, and logout behavior remain intact.
3. Every displayed administration link opens the matching existing Django Admin destination and retains server-side authorization.
4. No mock metrics, new backend endpoint, schema change, permission change, or module-state mutation is introduced.
5. The page is usable at 320/768/1024/1440px, keyboard navigable, and consistent with existing light/dark theme tokens.
6. Run the frontend's existing checks (`npm run test`, `npm run lint`, `npm run build`) in `demo/react`; report actual results and any pre-existing failures separately.

## Source references

- [React frontend README](../demo/react/README.md)
- [App routes](../demo/react/src/auth/AppRoutes.tsx)
- [Authentication context](../demo/react/src/auth/AuthContext.tsx)
- [Theme and shared UI tokens](../demo/react/src/index.css)
- [V2 UI and navigation direction](../docs-final-v2/07-ui-navigation-structure.md)
- [V2 roles and permissions](../docs-final-v2/02-user-roles-permissions.md)
- [V2 technical architecture](../docs-final-v2/06-technical-architecture-engineering-operations.md)
- [Current API flow map](../architecture/02-API-FLOW.md)
