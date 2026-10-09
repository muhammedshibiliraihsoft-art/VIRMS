# Authentication & Account Security

Vehicle Investment, Modification & Resale Management System

Version: Final v1.0
Status: LOCKED — AUTHENTICATION SOURCE OF TRUTH

Permissions and Tenant access belong to 02. Current security uses normal authentication, backend authorization, role permissions and audit. No separate secondary/protected password exists.

## Login and credentials

- Current default login is system-managed Username/Login ID + Password. Social login, mandatory email verification, email/OTP recovery, MFA, passkeys and SSO are not current requirements; future adoption must remain possible without compromising identity/history.
- Authorized administration creates an account with a temporary credential. The User must privately set a new password on first login before normal access.
- Logged-in Users can change their own password after current-password validation. Provide New Password and confirmation fields.
- Never store, log, expose, retrieve or display plaintext passwords. Use secure password hashing. Administrators may reset credentials but cannot learn a User's current or permanent password.
- Accept sufficiently long passphrases and password-manager-generated values; reject very weak/common passwords without forcing predictable composition rules. Permit paste and password-manager autocomplete. Password fields are masked by default with intentional show/hide control.

## Recovery and sessions

- With no current email/phone identity-verification flow, public self-service forgotten-password reset is not allowed. The User contacts an authorized administrator, who performs business identity verification and initiates a reset.
- Reset generates a temporary credential or equivalent controlled reset mechanism. The next successful login requires the User to set a new private password. Administrator does not choose and retain the permanent password.
- Traditional knowledge-based security questions must not be used for account recovery. Do not base recovery on guessable or discoverable personal facts such as birthplace, school, family names, favorite items, personal-history trivia, or similar answers. Current recovery remains the controlled administrator-assisted process above; this prohibition does not create or restore a separate protected business password.
- Support session revocation after password reset or suspected compromise so old sessions cannot remain usable indefinitely. Deactivated accounts cannot log in; reactivation preserves historical records.
- Account lifecycle supports activation, deactivation and reactivation through authorized administration. Role and Tenant membership changes preserve access history.

## Abuse protection and audit

- Apply rate limiting, progressive delay/backoff, suspicious-attempt protection and security logging to repeated login failures. Avoid unnecessary permanent lockouts.
- Login responses must not reveal whether a username exists; use safe generic failure wording.
- Administrative reset and other sensitive account actions record account, actor, time, Tenant/scope where relevant, and outcome. Audit never contains passwords, reset credentials, tokens or secrets.
- Backend session validation integrates with role, explicit Tenant assignment and object permission checks on every protected request. Possession of a session or Tenant UUID alone does not authorize a resource.
