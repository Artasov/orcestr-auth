<p align="right">
  <a href="./README.md">English</a> · <strong>Русский</strong>
</p>

<p align="center">
  <a href="https://orcestr.com">
    <img src="./assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" />
  </a>
</p>

# Orcestr Auth

[![PyPI](https://img.shields.io/pypi/v/orcestr-auth)](https://pypi.org/project/orcestr-auth/)
[![npm](https://img.shields.io/npm/v/@orcestr/auth-core)](https://www.npmjs.com/package/@orcestr/auth-core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Переиспользуемая основа авторизации для экосистемы [Orcestr](https://orcestr.com).

Orcestr Auth задаёт единый проверенный контракт для Python/FastAPI backend, браузерного
клиента, React Query, готовых форм на `@orcestr/ui` и защитных helpers для Next.js. Модель
пользователя, страницы, брендинг, юридические документы, тенанты и permissions остаются в
приложении.

## Статус

| Пункт | Значение |
| --- | --- |
| Версия | `0.1.0` |
| Статус | Dev / Beta |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2 |
| Frontend | React 19, React Query 5, Next.js 16 |
| OAuth | GitHub, Google и Яндекс, каждый включается независимо |

Пока пакеты находятся в beta, public API продолжает формироваться.

## Пакеты

| Пакет | Назначение | Документация |
| --- | --- | --- |
| `orcestr-auth` | Python core и адаптеры FastAPI, SQLAlchemy, OAuth | [EN](./backend/README.md) · [RU](./backend/README.ru.md) |
| `@orcestr/auth-core` | Browser API client, безопасные redirects и OAuth state/PKCE | [EN](./frontend/packages/core/README.md) · [RU](./frontend/packages/core/README.ru.md) |
| `@orcestr/auth-react` | React Query provider и headless auth hooks | [EN](./frontend/packages/react/README.md) · [RU](./frontend/packages/react/README.ru.md) |
| `@orcestr/auth-forms` | Готовые формы RU/EN на `@orcestr/ui` | [EN](./frontend/packages/forms/README.md) · [RU](./frontend/packages/forms/README.ru.md) |
| `@orcestr/auth-next` | Next.js proxy и server redirect helpers | [EN](./frontend/packages/next/README.md) · [RU](./frontend/packages/next/README.ru.md) |

## Что входит

| Зона | Содержимое |
| --- | --- |
| Identity security | password hashing, JWT validation, cookie policy и CSRF protection |
| Sessions | серверные сессии, opaque refresh tokens, rotation и replay revocation |
| Recovery | хешированные одноразовые коды подтверждения email и смены пароля |
| OAuth | опциональные GitHub, Google и Яндекс с state, PKCE и проверкой redirect URI |
| WebSocket | короткоживущие одноразовые tickets вместо access token в URL |
| Persistence | auth-модели в registry приложения с настоящими FK на пользователя |
| HTTP | FastAPI dependencies и router factory для browser и bearer flows |
| Frontend | безопасный `next`, refresh/retry, React Query hooks, формы и Next.js guards |
| Локализация | полные встроенные словари русского и английского с typed overrides |

## Граница ответственности

```text
Приложение                               Orcestr Auth
─────────────────────────────────────    ────────────────────────────────────
Таблица пользователя и product profile   Механика аутентификации
Страницы, URL, брендинг и metadata        Сессии, cookies и rotation токенов
Legal acceptance и tenant bootstrap      Auth-таблицы и адаптеры
Permissions и product navigation         Клиенты, hooks и формы
```

`UserORM` остаётся моделью приложения. Backend-пакет один раз получает модель и mapping
полей, строит прямые SQLAlchemy-запросы и подключает auth-таблицы к той же metadata. Вторая
таблица пользователей и reflection-based repository consumer-приложению не нужны.

## Установка

Backend со всеми официальными адаптерами:

```bash
pip install "orcestr-auth[all]"
```

Frontend разделён на слои, поэтому приложение устанавливает только нужные пакеты:

```bash
npm install @orcestr/auth-core
npm install @orcestr/auth-react @tanstack/react-query
npm install @orcestr/auth-forms @orcestr/ui
npm install @orcestr/auth-next
```

Подключение и примеры описаны в README каждого пакета.

## Архитектура

```text
orcestr-auth (Python)
├── core: config, passwords, tokens и extension ports
├── sqlalchemy: user adapter и auth model factory
├── services: sessions, codes и WebSocket tickets
├── oauth: GitHub, Google и Яндекс provider clients
└── fastapi: dependencies, redirect policy и router factory

@orcestr/auth-core
├── @orcestr/auth-react
│   └── @orcestr/auth-forms → @orcestr/ui
└── @orcestr/auth-next
```

Подробная документация:

- [Оглавление документации](./docs/README.ru.md)
- [Архитектурные границы](./docs/architecture/boundaries.ru.md)
- [Инварианты безопасности](./docs/security/invariants.ru.md)
- [Подключение к Orcestr](./docs/integration/orcestr.ru.md)
- [Инструкция по релизу](./docs/RELEASE.ru.md)
- [План реализации и принятые решения](./PLAN.md)

## Разработка

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

Соседний checkout Orcestr является reference consumer. Локальные installers подключают
исходники, не записывая `file:` или editable paths в production manifests и lock-файлы.

## Релиз

Теги `auth-v*` публикуют Python-пакет в PyPI и четыре npm-пакета в порядке зависимостей.
Workflow проверяет совпадение всех версий с тегом, запускает tests/build/package checks и
использует Trusted Publishing/provenance.

Полная инструкция: [docs/RELEASE.ru.md](./docs/RELEASE.ru.md).

## Экосистема Orcestr

- Продукт и документация: [orcestr.com](https://orcestr.com)
- UI-система: [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui)

## Maintainer

Публичные обновления ведёт [@Artasov](https://github.com/Artasov).

## Лицензия

MIT. См. [LICENSE](./LICENSE).
