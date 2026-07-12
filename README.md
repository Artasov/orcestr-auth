<p align="right">
  <strong>English</strong> · <a href="./README.ru.md">Русский</a>
</p>

<p align="center">
  <a href="https://orcestr.com">
    <img src="./assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" />
  </a>
</p>

# Orcestr Auth

[![PyPI](https://img.shields.io/pypi/v/orcestr-auth)](https://pypi.org/project/orcestr-auth/)
[![npm](https://img.shields.io/npm/v/@orcestr/auth-core)](https://www.npmjs.com/package/@orcestr/auth-core)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](./LICENSE)

Reusable authentication foundation for the [Orcestr](https://orcestr.com) ecosystem.

Orcestr Auth provides one tested contract across Python/FastAPI backends, browser clients,
React Query applications, ready `@orcestr/ui` forms and Next.js request guards. Applications
keep ownership of users, pages, branding, legal acceptance, tenants and permissions.

## Status

| Item | Value |
| --- | --- |
| Version | `0.2.0` |
| Status | Beta |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2 |
| Frontend | React 19, React Query 5, Next.js 16 |
| OAuth | GitHub, Google and Yandex, independently optional |

The public API is still being shaped while the packages are in beta.

## Packages

| Package | Purpose | Documentation |
| --- | --- | --- |
| `orcestr-auth` | Python core plus FastAPI, SQLAlchemy and OAuth adapters | [EN](./backend/README.md) · [RU](./backend/README.ru.md) |
| `@orcestr/auth-core` | Browser API client, safe redirects and OAuth state/PKCE | [EN](./frontend/packages/core/README.md) · [RU](./frontend/packages/core/README.ru.md) |
| `@orcestr/auth-react` | React Query provider and headless auth hooks | [EN](./frontend/packages/react/README.md) · [RU](./frontend/packages/react/README.ru.md) |
| `@orcestr/auth-forms` | Ready RU/EN forms built with `@orcestr/ui` | [EN](./frontend/packages/forms/README.md) · [RU](./frontend/packages/forms/README.ru.md) |
| `@orcestr/auth-next` | Next.js proxy and server redirect helpers | [EN](./frontend/packages/next/README.md) · [RU](./frontend/packages/next/README.ru.md) |

## What Is Included

| Area | Includes |
| --- | --- |
| Identity security | password hashing, JWT validation, cookie policy and CSRF protection |
| Sessions | server-side sessions, opaque rotating refresh tokens and replay revocation |
| Recovery | hashed one-time email verification and password reset codes |
| OAuth | optional GitHub, Google and Yandex adapters with state, PKCE and redirect validation |
| WebSocket | short-lived, one-time connection tickets instead of access tokens in URLs |
| Persistence | auth models attached to the application's SQLAlchemy registry with real user FKs |
| HTTP | reusable FastAPI dependencies and router factory for browser and bearer flows |
| Frontend | safe `next`, automatic refresh/retry, React Query hooks, forms and Next.js guards |
| Localization | complete built-in English and Russian form dictionaries with typed overrides |

## Ownership Boundary

```text
Application owns                         Orcestr Auth owns
─────────────────────────────────────    ────────────────────────────────────
User table and product profile           Authentication mechanics
Pages, URLs, branding and metadata       Sessions, cookies and token rotation
Legal acceptance and tenant bootstrap    Auth-table definitions and adapters
Permissions and product navigation       Reusable clients, hooks and forms
```

`UserORM` remains an application model. The backend package receives the model and field
mapping once, creates direct SQLAlchemy queries and attaches auth tables to the same metadata.
Consumers do not maintain a second user table or a reflection-based repository layer.

## Install

Backend with all first-party adapters:

```bash
pip install "orcestr-auth[all]"
```

Frontend packages are intentionally layered, so applications install only what they use:

```bash
npm install @orcestr/auth-core
npm install @orcestr/auth-react @tanstack/react-query
npm install @orcestr/auth-forms @orcestr/ui
npm install @orcestr/auth-next
```

See each package README for wiring and examples.

## Architecture

```text
orcestr-auth (Python)
├── core: config, passwords, tokens and extension ports
├── sqlalchemy: user adapter and auth model factory
├── services: sessions, codes and WebSocket tickets
├── oauth: GitHub, Google and Yandex provider clients
└── fastapi: dependencies, redirect policy and router factory

@orcestr/auth-core
├── @orcestr/auth-react
│   └── @orcestr/auth-forms → @orcestr/ui
└── @orcestr/auth-next
```

Detailed documentation:

- [Documentation index](./docs/README.md)
- [Architecture boundaries](./docs/architecture/boundaries.md)
- [Security invariants](./docs/security/invariants.md)
- [Orcestr integration](./docs/integration/orcestr.md)
- [Release guide](./docs/RELEASE.md)
- [Implementation plan and decisions](./PLAN.md)

## Development

```powershell
cd backend
uv sync --frozen
uv run pytest -q
uv build

cd ..\frontend
npm ci
npm test
npm run pack:dry-run
```

The shared [`.run`](./.run) configurations expose dependency installation and builds for Python,
Core, React, Forms and Next.js separately, plus `install all` and `build all` for the complete
workspace. Release configurations remain package-specific.

The sibling Orcestr checkout is the reference consumer. Its local installers use source
packages without writing `file:` or editable paths into production manifests and lock files.

## Release

Packages are released independently. `python-v*` publishes only `orcestr-auth`; tags
`auth-core-v*`, `auth-react-v*`, `auth-forms-v*` and `auth-next-v*` each publish only their
matching npm package. The workflows verify the selected version, run the relevant checks and use
Trusted Publishing/provenance.

Full instructions: [docs/RELEASE.md](./docs/RELEASE.md).

## Orcestr Ecosystem

- Product and documentation: [orcestr.com](https://orcestr.com)
- UI system: [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui)

## Maintainer

Public updates are maintained by [@Artasov](https://github.com/Artasov).

## License

Licensed under the [Mozilla Public License 2.0](./LICENSE). Commercial use is permitted; changes
to MPL-covered files remain subject to the MPL. Attribution and copyright notices are documented
in [NOTICE](./NOTICE). The Orcestr name and branding are governed separately by
[TRADEMARKS.md](./TRADEMARKS.md).
