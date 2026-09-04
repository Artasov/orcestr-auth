# Changelog

## Next

- Allowed `.localhost` OAuth callback origins when the FastAPI development policy explicitly
  enables localhost, while continuing to reject lookalike domains.
- Added `useAuthMethods` with hydration-safe browser-origin discovery and origin-scoped caching.
- Added localized loading/error/retry states for login and registration method discovery.
- Prepared patch releases `orcestr-auth` 0.4.2, `@orcestr/auth-react` 0.4.2 and
  `@orcestr/auth-forms` 0.5.2.
- Added a structural `AuthClientContract` for browser-compatible native/IPC transports while
  keeping the existing `AuthClient` and provider OAuth surface directly assignable.
- Added an optional OAuth button authorization transport, one-shot visible-provider hints and an
  explicit login option for legal consent handled by an outer OAuth flow; web defaults are unchanged.
- Added non-cookie `POST /token/logout/` with a required refresh token, optional Bearer access
  token, no-store response and no cookie CSRF dependency.
- Prepared patch releases `orcestr-auth` 0.4.1, `@orcestr/auth-core` 0.4.1,
  `@orcestr/auth-react` 0.4.1 and dependency-aligned `@orcestr/auth-forms` 0.5.1.
- Added stateless OAuth 2.1 public/native client helpers with secure state,
  PKCE S256, validated callbacks and authorization-code/refresh token grants.
- Added default-deny client-token isolation, server-session-backed scope guards, an optional
  userinfo hook, strict native redirect schemes and `offline_access`-gated refresh tokens.
- Prepared the 0.4.0 release of `@orcestr/auth-core`, `@orcestr/auth-react`
  and `@orcestr/auth-next`, and the 0.5.0 release of `@orcestr/auth-forms`.
- Updated `@orcestr/auth-forms` for the `@orcestr/ui` 0.7 component contract.
- Added version-aware local legal-consent persistence and optional first-checkbox select-all behavior.
- Added controlled OAuth placement before fields, after submit, or after navigation links.
- Added a reusable versioned legal-consent gate shared by login, registration and OAuth.
- Added login metadata payloads and OAuth callback payload transfer for server-side acceptance audit.

## 0.3.1 - Unreleased

- Fixed optional authentication so an expired or invalid browser session
  returns `401` and can be refreshed instead of silently becoming anonymous.
- Added semantic accent-hover links to the ready auth forms.
- Added reusable and provider-specific OAuth button components with configurable layout.

## 0.3.0 - Unreleased

- Added Orcestr ecosystem branding and the shared repository banner.
- Added complete English/Russian repository, workspace and package documentation.
- Added PyPI/npm metadata, package licenses, governance files and GitHub templates.
- Aligned CI and multi-registry release presentation with `orcestr-ui`.
- Replaced the duplicated frontend error parser with `@orcestr/core`.
- Added stable typed auth error codes shared by Python and EN/RU forms.
- Added a single-flight session refresh policy and shared safe redirects.
- Removed string-based error translation and legacy auth error envelopes.
- Moved cookie response helpers into the explicit FastAPI adapter boundary.
- Fixed the `fastapi` extra to install the SQLAlchemy runtime required by the
  dependency and router adapters.

## 0.1.0

- Python token, cookie, session rotation, verification/reset code, WebSocket,
  SQLAlchemy and OAuth provider adapters.
- Configurable application-owned `UserORM` with shared metadata and real FKs.
- Frontend core, React Query, RU/EN forms and Next.js proxy packages.
- Optional GitHub, Google and Yandex OAuth providers.
