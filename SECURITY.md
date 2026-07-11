# Security Policy

[Русская версия](./SECURITY.ru.md)

## Supported Versions

Security fixes are handled on the default branch while the packages remain in beta.

## Reporting a Vulnerability

Do not open a public issue for vulnerabilities. Report security problems privately to the
maintainer through GitHub.

Include the affected package/version, attack scenario, required privileges, data exposure,
browser/backend context and a minimal reproduction when possible. Never include real tokens,
credentials or personal data.

## Sensitive Areas

Extra review is required for changes involving JWT validation, password hashing, refresh
rotation/replay, cookies, CSRF, safe redirects, OAuth state/PKCE/linking, verification/reset
codes, WebSocket tickets, rate limits, audit data, SQLAlchemy ownership or release artifacts.

The complete contract is documented in
[docs/security/invariants.md](./docs/security/invariants.md).
