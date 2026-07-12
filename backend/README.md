<p align="right">
  <strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/backend/README.ru.md">Русский</a>
</p>

<p align="center">
  <a href="https://orcestr.com">
    <img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" />
  </a>
</p>

# orcestr-auth

[![PyPI](https://img.shields.io/pypi/v/orcestr-auth)](https://pypi.org/project/orcestr-auth/)
[![Python](https://img.shields.io/pypi/pyversions/orcestr-auth)](https://pypi.org/project/orcestr-auth/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](../LICENSE)

Python authentication core and FastAPI/SQLAlchemy adapters for the
[Orcestr](https://orcestr.com) ecosystem.

The application keeps its real user model and product lifecycle. The package owns password,
token, session, cookie, recovery, OAuth and WebSocket authentication mechanics.

## Install

```bash
pip install "orcestr-auth[all]"
```

Optional groups:

| Extra | Includes |
| --- | --- |
| `fastapi` | dependencies, cookie/CSRF flow and router factory |
| `sqlalchemy` | auth models, direct user repository and Alembic operations |
| `oauth` | GitHub, Google and Yandex provider clients |
| `all` | every first-party adapter |

## Main APIs

| Import | Purpose |
| --- | --- |
| `orcestr_auth` | config, password helpers, token codec and extension ports |
| `orcestr_auth.sqlalchemy` | `create_auth_models`, `UserFieldMap`, user repository |
| `orcestr_auth.services` | sessions, verification/reset codes and WebSocket tickets |
| `orcestr_auth.oauth` | optional provider clients and normalized profiles |
| `orcestr_auth.fastapi` | auth dependencies, redirect policy and router factory |
| `orcestr_auth.migrations` | versioned Alembic operations for auth-owned schema |

## SQLAlchemy Wiring

Attach auth tables to the application's registry and real user primary key:

```python
from orcestr_auth.sqlalchemy import UserFieldMap, create_auth_models

auth_models = create_auth_models(
    registry=Base.registry,
    user_model=UserORM,
)

user_fields = UserFieldMap(
    id=UserORM.id,
    username=UserORM.username,
    email=UserORM.email,
    password_hash=UserORM.password_hash,
    is_active=UserORM.is_active,
    email_verified_at=UserORM.email_verified_at,
)
```

This creates direct indexed queries and real foreign keys. It does not create a second user
table and does not use runtime reflection.

## FastAPI Wiring

```python
from orcestr_auth.fastapi import create_auth_dependencies, create_auth_router

auth_dependencies = create_auth_dependencies(
    config=auth_config,
    session_dependency=get_control_db_session,
    user_model=UserORM,
    user_fields=user_fields,
    models=auth_models,
)

router = create_auth_router(
    config=auth_config,
    application_dependency=get_auth_http_application,
    current_user_dependency=auth_dependencies.current_user,
    register_model=RegisterRequest,
    user_response_model=UserRead,
)
```

The consumer implements the small `AuthHttpApplication` boundary for product-specific work:
user creation, legal acceptance, tenant bootstrap, email delivery, audit and rate limits.
Standard endpoints, cookies and token responses remain library-owned.

## Security Model

- browser tokens live in HttpOnly cookies and never appear in browser auth JSON;
- cookie mutations require the configured CSRF header;
- refresh tokens are opaque, hashed, rotated and replay-protected;
- access JWTs validate issuer, audience, expiry, type, JTI and server session state;
- recovery codes are hashed, expiring, attempt-limited and one-time;
- OAuth validates redirects and supports state/PKCE without implicit account linking;
- WebSocket access uses short-lived one-time tickets.

See [security invariants](https://github.com/Artasov/orcestr-auth/blob/main/docs/security/invariants.md)
and [architecture boundaries](https://github.com/Artasov/orcestr-auth/blob/main/docs/architecture/boundaries.md).

## Development

```bash
uv sync --frozen
uv run pytest -q
uv build
```

## Ecosystem

- All auth packages: [Orcestr Auth repository](https://github.com/Artasov/orcestr-auth)
- UI system: [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui)
- Product: [orcestr.com](https://orcestr.com)

## License

Licensed under the [Mozilla Public License 2.0](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE).
Commercial use is permitted; see the repository
[NOTICE](https://github.com/Artasov/orcestr-auth/blob/main/NOTICE) and
[trademark policy](https://github.com/Artasov/orcestr-auth/blob/main/TRADEMARKS.md).
