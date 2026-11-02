# VIRMS React frontend

This is the existing React 19, Vite, TypeScript and Tailwind v4 VIRMS reference shell with Phase 2 session-auth integration. The current business pages and their sample records remain prototype/reference data; Phase 1 does not provide business APIs for those modules.

## Local development

Start Django separately at `http://127.0.0.1:8001` after configuring its private local environment and an isolated PostgreSQL database. Do not run migrations against staging or production. Then start this frontend:

```powershell
npm ci
npm run dev
```

The Vite development and preview servers proxy same-origin `/api/v1` requests to the local Django server. Platform Back Office accounts are handed to the existing Django Admin at `/admin/`; Vite proxies that path and Django static assets locally. Override `VIRMS_API_TARGET` only with another `http` loopback origin. The value is server-side Vite configuration, not a `VITE_*` browser variable, and must contain no credentials. Production hosting is not configured; it must provide same-origin `/api/v1`, `/admin/`, and `/static/` routing or receive a separately reviewed CORS/CSRF deployment design.

## Available checks

```powershell
npm run test
npm run lint
npm run build
```

The browser session and CSRF token are cookie-based. Authentication credentials and query data are not written to local storage. The Vite server never runs Django migrations automatically.
