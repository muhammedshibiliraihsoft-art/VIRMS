# Authentication & Account Security

Status: DRAFT V2 — supporting authentication source after approval

Permissions, Company/Branch membership, enabled-module state and object scope belong to 02. Current security uses normal authentication, backend authorization, role restrictions and audit. No separate secondary/protected business password exists.

Protected financial configuration uses Platform Back Office identity plus specific backend protected-action permission, effective/versioned changes and audit, including Investor positive-share agreements, Owner distribution percentages, sensitive Company defaults and protected business rates. Accountant operational transaction permission does not grant configuration mutation; Owner access is read-only. Platform configuration permission does not grant ordinary Tenant financial posting. A confirmed configuration change and a confirmed money event are separately authorized consequential actions.

## Login and credentials

- Default login is a system-managed Username/Login ID and Password. Social login, mandatory email verification, public email/OTP recovery, MFA, passkeys and SSO are not current requirements; future adoption must not break identity/history.
- Authorized administration provisions an account with a temporary credential. The User privately sets a new password on first login before ordinary protected access. Logged-in Users may change their own password after current-password validation using New Password and confirmation.
- Never store, log, expose, retrieve or display plaintext passwords. Use secure password hashing. Administrators may reset access but cannot learn or retain a User's private permanent password.
- Accept sufficiently long passphrases and password-manager-generated values; reject very weak/common passwords without predictable composition rules. Permit paste and password-manager autocomplete. Password fields are masked by default with intentional show/hide control.

## Recovery, session and lifecycle

- Without an approved email/phone identity-verification flow, public self-service forgotten-password reset is not allowed. A User contacts authorized administration, which verifies business identity and initiates a controlled temporary-credential or equivalent reset. The next successful login requires a new private password.
- Do not use knowledge-based security questions based on guessable personal facts. This prohibition does not introduce a separate protected business password.
- Support session revocation after reset or suspected compromise so old sessions cannot remain usable indefinitely. Deactivated accounts cannot log in; authorized reactivation retains historical business and access records.
- Account activation, deactivation, role change, Company membership, Branch assignment and Platform administration changes preserve history. A session, Company UUID or Branch UUID alone grants no protected resource access.

## Abuse protection and audit

Apply rate limiting, progressive delay/backoff, suspicious-attempt protection and security logging to repeated login failures, without unnecessary permanent lockout. Login failures use generic wording that does not reveal whether a Username exists. Sensitive reset/account actions record account, actor, time, Company/Branch scope where relevant and outcome, but never password, reset credential, token or secret. Every protected request validates current session, role, Company membership, Branch/resource scope and enabled module on the backend.
