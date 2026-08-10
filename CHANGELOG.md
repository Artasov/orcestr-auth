# Changelog

## Next

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
