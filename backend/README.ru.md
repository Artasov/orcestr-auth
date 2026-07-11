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
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

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

Consumer реализует небольшой интерфейс `AuthHttpApplication` для product-specific операций:
создания пользователя, legal acceptance, tenant bootstrap, отправки писем, аудита и rate
limits. Стандартные endpoints, cookies и token responses остаются в библиотеке.

## Модель безопасности

- browser tokens находятся в HttpOnly cookies и не возвращаются в browser auth JSON;
- cookie mutations требуют настроенный CSRF header;
- refresh tokens opaque, хешируются, ротируются и защищены от replay;
- access JWT проверяют issuer, audience, expiry, type, JTI и серверную сессию;
- recovery codes хешируются, истекают, ограничивают попытки и используются один раз;
- OAuth проверяет redirects, поддерживает state/PKCE и не делает неявный account linking;
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
- UI-система: [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui)
- Продукт: [orcestr.com](https://orcestr.com)

## Лицензия

MIT. См. [лицензию репозитория](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE).
