<p align="right">
  <a href="https://github.com/Artasov/orcestr-auth/blob/main/backend/README.md">English</a> · <strong>Русский</strong>
</p>

<p align="center">
  <a href="https://orcestr.com">
    <img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" />
  </a>
</p>

# orcestr-auth

[![PyPI](https://img.shields.io/pypi/v/orcestr-auth)](https://pypi.org/project/orcestr-auth/)
[![Python](https://img.shields.io/pypi/pyversions/orcestr-auth)](https://pypi.org/project/orcestr-auth/)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](../LICENSE)

Python core авторизации и адаптеры FastAPI/SQLAlchemy для экосистемы
[Orcestr](https://orcestr.com).

Приложение сохраняет настоящую модель пользователя и product lifecycle. Пакет владеет
механикой паролей, токенов, сессий, cookies, восстановления доступа, OAuth и WebSocket auth.

## Установка

```bash
pip install "orcestr-auth[all]"
```

Опциональные группы:

| Extra | Содержимое |
| --- | --- |
| `fastapi` | dependencies, cookie/CSRF flow и router factory |
| `sqlalchemy` | auth models, прямой user repository и Alembic operations |
| `oauth` | provider clients для GitHub, Google и Яндекса |
| `all` | все официальные адаптеры |

## Основные API

| Import | Назначение |
| --- | --- |
| `orcestr_auth` | config, password helpers, token codec и extension ports |
| `orcestr_auth.sqlalchemy` | `create_auth_models`, `UserFieldMap`, user repository |
| `orcestr_auth.services` | sessions, verification/reset codes и WebSocket tickets |
| `orcestr_auth.oauth` | опциональные provider clients и нормализованные profiles |
| `orcestr_auth.fastapi` | auth dependencies, redirect policy и router factory |
| `orcestr_auth.migrations` | versioned Alembic operations для auth-схемы |

## Подключение SQLAlchemy

Auth-таблицы подключаются к registry приложения и настоящему primary key пользователя:

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

Так сохраняются прямые индексированные запросы и настоящие foreign keys. Вторая таблица
пользователей и runtime reflection не создаются.

## Подключение FastAPI

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

Auth services выбрасывают общий `orcestr_core.ApiError`. Один раз зарегистрируй в приложении
middleware и handlers из Core, затем подключи auth router:

```python
from fastapi import FastAPI
from orcestr_core.fastapi import RequestIdMiddleware, register_api_error_handlers

app = FastAPI()
app.add_middleware(RequestIdMiddleware)
register_api_error_handlers(app)
app.include_router(router)
```

Так стабильные auth-коды вроде `invalid_credentials`, структурированные validation fields и
`x-request-id` используют тот же envelope, что и остальной product API.

Consumer реализует небольшой интерфейс `AuthHttpApplication` для product-specific операций:
создания пользователя, legal acceptance, tenant bootstrap, отправки писем, аудита и rate
limits. Стандартные endpoints, cookies и token responses остаются в библиотеке.

## Явные token sessions

Non-browser first-party clients могут использовать endpoints, которые подключает
`create_auth_router`: `POST /token/login/`, `POST /token/refresh/` и
`POST /token/logout/`. Login/refresh возвращают настроенный token response и не устанавливают
cookies. Logout принимает refresh token в том же теле `RefreshTokenInput` и опциональный access
token в header `Authorization: Bearer ...`, передаёт оба значения в
`AuthHttpApplication.logout` и отвечает пустым `204`. Token responses и logout получают
`Cache-Control: no-store`.

В этом flow не используются cookie CSRF headers. Client обязан держать access token в памяти,
хранить refresh token в защищённом системном хранилище и атомарно заменять его после каждой
успешной ротации.

## OAuth 2.1 для public clients

Native/public clients регистрируются с точным allowlist redirect URI. Client secret не
используется, а Authorization Code всегда требует PKCE S256:

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

Каждый продукт должен явно перечислить собственный полный набор scopes по принципу least
privilege. Refresh token возвращается только для grant со scope `offline_access`; в
online-only ответе поле `refresh_token` отсутствует.

Создайте `OAuth2AuthorizationService` на той же control DB session, auth models и user
repository, затем подключите адаптер:

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

Адаптер предоставляет `GET /authorize/` для проверенного UI context,
`POST /authorize/` для выдачи code, `POST /token/` для grants `authorization_code` и
`refresh_token`, `POST /revoke/`, а при передаче явной principal dependency —
`GET /userinfo/`. Application hook `userinfo(principal)` определяет поля ответа: claims
`profile` и `email` следует отдавать только при наличии соответствующего scope в
`principal.scopes`. Token/revoke принимают JSON или
`application/x-www-form-urlencoded`; все ответы запрещено кэшировать. Для authorization POST
с cookie обязателен `X-Requested-With: XMLHttpRequest`.

Обычные dependencies `current_user` по умолчанию отклоняют access tokens, привязанные к
OAuth client. Endpoint для OAuth client должен явно использовать
`auth_dependencies.require_oauth2_scopes("required_scope")`. Эта bearer-only dependency
сверяет подписанный JWT с активной серверной session, включённой регистрацией client и
выданными/зарегистрированными scopes. Service-level `revoke()` возвращает `True` только при
фактическом отзыве активной client session, поэтому consumer не обязан писать ложный success
audit; RFC-совместимый HTTP endpoint по-прежнему всегда отвечает пустым `200`.

Redirect URI допускают HTTPS, HTTP только для loopback и private-use native scheme в
reverse-domain формате, например `com.orcestr.realtranslate`. Userinfo, fragments, опасные
schemes и malformed URI отклоняются до точного сравнения с allowlist.

После неизменяемой схемы v0.1 примените `orcestr_auth.migrations.v0_4.upgrade`: migration
добавляет таблицу authorization codes и nullable client/scope bindings для sessions.

## Модель безопасности

Для FastAPI OAuth callback настройте `OAuthRedirectPolicy` с доверенными
`allowed_origins`/`allowed_domains` приложения. `allow_localhost=True` дополнительно разрешает
localhost, его поддомены (например, `deliveries.localhost`), `127.0.0.1` и `::1` по HTTP/HTTPS.
Включайте опцию только в development. Похожие адреса вроде `localhost.example.com` не входят
в это разрешение. Точный callback URI нужно отдельно зарегистрировать у OAuth-провайдера:
эта политика определяет только origins, которые принимает приложение.

- browser tokens находятся в HttpOnly cookies и не возвращаются в browser auth JSON;
- cookie mutations требуют настроенный CSRF header;
- refresh tokens opaque, хешируются, ротируются и защищены от replay;
- access JWT проверяют issuer, audience, expiry, type, JTI и серверную сессию;
- recovery codes хешируются, истекают, ограничивают попытки и используются один раз;
- OAuth проверяет redirects, поддерживает state/PKCE и не делает неявный account linking;
- native OAuth использует точные зарегистрированные redirects, короткоживущие хэшированные
  one-time codes и PKCE S256, а refresh rotation привязана к client и выданному scope;
- client-bound access tokens запрещены для обычных API dependencies и требуют явный scope
  guard с проверкой server-side session;
- WebSocket использует короткоживущие одноразовые tickets.

См. [инварианты безопасности](https://github.com/Artasov/orcestr-auth/blob/main/docs/security/invariants.ru.md)
и [архитектурные границы](https://github.com/Artasov/orcestr-auth/blob/main/docs/architecture/boundaries.ru.md).

## Разработка

```bash
uv sync --frozen
uv run pytest -q
uv build
```

## Экосистема

- Все auth-пакеты: [репозиторий Orcestr Auth](https://github.com/Artasov/orcestr-auth)
- Общие API-контракты: [Orcestr Core](https://github.com/Artasov/orcestr-core)
- UI-система: [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui)
- Продукт: [orcestr.com](https://orcestr.com)

## Лицензия

Проект распространяется по [Mozilla Public License 2.0](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE).
Коммерческое использование разрешено; см.
[NOTICE](https://github.com/Artasov/orcestr-auth/blob/main/NOTICE) и
[политику использования бренда](https://github.com/Artasov/orcestr-auth/blob/main/TRADEMARKS.md).
