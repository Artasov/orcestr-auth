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

Auth services raise the shared `orcestr_core.ApiError`. Register the Core middleware and
handlers once on the application, then include the auth router:

```python
from fastapi import FastAPI
from orcestr_core.fastapi import RequestIdMiddleware, register_api_error_handlers

app = FastAPI()
app.add_middleware(RequestIdMiddleware)
register_api_error_handlers(app)
app.include_router(router)
```

This preserves stable auth codes such as `invalid_credentials`, structured validation fields
and `x-request-id` in the same envelope as the rest of the product API.

The consumer implements the small `AuthHttpApplication` boundary for product-specific work:
user creation, legal acceptance, tenant bootstrap, email delivery, audit and rate limits.
Standard endpoints, cookies and token responses remain library-owned.

## Explicit token sessions

Non-browser first-party clients can use the explicit token endpoints mounted by
`create_auth_router`: `POST /token/login/`, `POST /token/refresh/` and
`POST /token/logout/`. Login and refresh return the configured token response and set no cookies.
Logout accepts the refresh token in the same `RefreshTokenInput` body and an optional access token
in the `Authorization: Bearer ...` header, passes both values to `AuthHttpApplication.logout`, and
returns an empty `204` response. Token responses and logout are marked `Cache-Control: no-store`.

This flow does not use cookie CSRF headers. The client is responsible for keeping access tokens in
memory, persisting refresh tokens in platform-secure storage, and replacing the stored refresh
token atomically after every successful rotation.

## OAuth 2.1 public clients

Register native/public clients with exact redirect URI allowlists. Client secrets are not
used; Authorization Code always requires PKCE S256:

```python
from orcestr_auth import AuthConfig, OAuth2ClientConfig

auth_config = AuthConfig(
    secret_key="...",
    oauth2_clients={
        "orcestr-real-translate": OAuth2ClientConfig(
            display_name="Orcestr Real Translate",
            redirect_uris=("com.orcestr.realtranslate://oauth/callback",),
            scopes=("openid", "profile", "email", "offline_access"),
        ),
    },
)
```

Each product must enumerate its complete, least-privilege scope set. A refresh token is
returned only when the grant includes `offline_access`; online-only grants contain no
`refresh_token` field.

Create `OAuth2AuthorizationService` from the same control-database session, auth models and
user repository, then mount the adapter:

```python
from orcestr_auth.fastapi import create_oauth2_router

oauth2_router = create_oauth2_router(
    config=auth_config,
    application_dependency=get_oauth2_application,
    current_user_dependency=auth_dependencies.current_user,
    oauth2_principal_dependency=auth_dependencies.require_oauth2_scopes("openid"),
    userinfo_response_model=UserInfoResponse,
)
app.include_router(oauth2_router, prefix="/api/v1/auth/oauth2")
```

The adapter exposes `GET /authorize/` for validated UI context, `POST /authorize/` for code
issuance, `POST /token/` for `authorization_code` and `refresh_token` grants, and
`POST /revoke/`, and—when its explicit principal dependency is supplied—`GET /userinfo/`.
The application `userinfo(principal)` hook decides the response fields; expose `profile` and
`email` claims only when those scopes are present on `principal.scopes`. Token and revoke endpoints accept JSON or
`application/x-www-form-urlencoded`; every response is non-cacheable. A cookie-authenticated
authorization POST must include `X-Requested-With: XMLHttpRequest`.

Ordinary `current_user` dependencies reject client-bound access tokens by default. Resource
endpoints intended for OAuth clients must opt in with
`auth_dependencies.require_oauth2_scopes("required_scope")`; this bearer-only dependency
checks the signed JWT against the live server session, enabled client registration and both
the granted and currently registered scopes. The service-level `revoke()` result is `True`
only when it actually revoked a live client session, allowing consumers to avoid false
success audit events; the RFC-compatible HTTP endpoint remains an empty `200` response.

Registered redirect URIs must use HTTPS, loopback-only HTTP, or a private-use reverse-domain
native scheme such as `com.orcestr.realtranslate`. Userinfo, fragments, dangerous schemes
and malformed URIs are rejected before exact allowlist matching.

Apply `orcestr_auth.migrations.v0_4.upgrade` after the immutable v0.1 schema when integrating
the new authorization-code table and nullable client/scope session bindings.

## Security Model

For FastAPI OAuth callbacks, configure `OAuthRedirectPolicy` with the application's trusted
`allowed_origins`/`allowed_domains`. `allow_localhost=True` additionally accepts localhost,
its subdomains (for example `deliveries.localhost`), `127.0.0.1` and `::1` over HTTP/HTTPS.
Enable this option only in development. Lookalikes such as `localhost.example.com` are not
included. Register the exact callback URI with each OAuth provider separately; this policy
only controls which origins the application accepts.

- browser tokens live in HttpOnly cookies and never appear in browser auth JSON;
- cookie mutations require the configured CSRF header;
- refresh tokens are opaque, hashed, rotated and replay-protected;
- access JWTs validate issuer, audience, expiry, type, JTI and server session state;
- recovery codes are hashed, expiring, attempt-limited and one-time;
- OAuth validates redirects and supports state/PKCE without implicit account linking;
- native OAuth uses exact registered redirects, short-lived hashed one-time codes and PKCE
  S256, with refresh rotation bound to the client and granted scope;
- client-bound access tokens are denied on ordinary API dependencies and require an explicit,
  server-session-backed scope guard;
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
- Shared API contracts: [Orcestr Core](https://github.com/Artasov/orcestr-core)
- UI system: [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui)
- Product: [orcestr.com](https://orcestr.com)

## License

Licensed under the [Mozilla Public License 2.0](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE).
Commercial use is permitted; see the repository
[NOTICE](https://github.com/Artasov/orcestr-auth/blob/main/NOTICE) and
[trademark policy](https://github.com/Artasov/orcestr-auth/blob/main/TRADEMARKS.md).
