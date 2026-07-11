# План выделения Orcestr Auth

Статус: локальная реализация завершена 11.07.2026. Этот документ фиксирует целевую архитектуру, границы
библиотеки и порядок переноса действующей авторизации из `orcestr`.

## 1. Решение в одном абзаце

`orcestr-auth` создаётся как отдельный монорепозиторий одного bounded context —
аутентификации и управления пользовательскими сессиями. В нём совместно живут
Python backend-пакет, независимое frontend-ядро, React-адаптер и готовые формы на
`@orcestr/ui`. Страницы, маршруты, продуктовый branding, tenant-memberships,
permissions и бизнес-роли остаются в приложениях. Будущие платежи не добавляются
в этот репозиторий: для них создаётся отдельный `orcestr-billing`.

## 2. Зачем выделяем библиотеку

- Один раз реализовать безопасный browser-auth flow и переиспользовать его.
- Исключить разные реализации `next`, OAuth callback, refresh и logout в проектах.
- Иметь один контракт между Python backend и TypeScript frontend.
- Переиспользовать готовые формы без навязывания страниц и маршрутизации.
- Централизованно исправлять security-проблемы и обновлять зависимые проекты.
- Сохранить удобную разработку рядом с `orcestr`, как сейчас с `orcestr-ui`.
- В production всегда собираться только с опубликованными фиксированными версиями.

## 3. Что это не такое

`orcestr-auth` не должен превращаться в общий репозиторий всего фреймворка.

В него не входят:

- UI-примитивы и layout-компоненты общего назначения;
- страницы Next.js и route registry конкретного приложения;
- tenant/workspace memberships и продуктовые permissions;
- роли модулей Deliveries, Beauty, Jewelry и других продуктов;
- подписки, тарифы, эквайринг и платежи;
- продуктовые email-шаблоны и конкретный провайдер отправки писем;
- бизнес-аудит приложения, не относящийся к событиям безопасности;
- профиль сотрудника и его предметные данные.

## 4. Предлагаемая структура репозитория

```text
orcestr-auth/
├── backend/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/orcestr_auth/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── contracts/
│   │   ├── fastapi/
│   │   ├── sqlalchemy/
│   │   ├── oauth/
│   │   ├── websocket/
│   │   └── testing/
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   └── packages/
│       ├── core/
│       ├── react/
│       └── forms/
├── contracts/
│   ├── openapi/
│   └── generated/
├── examples/
│   └── fastapi-next-or-react/
├── docs/
│   ├── architecture/
│   ├── integration/
│   └── security/
├── scripts/
├── .github/workflows/
├── CHANGELOG.md
├── LICENSE
└── PLAN.md
```

Это монорепозиторий исходников, но артефакты публикуются отдельно и имеют свои
версии.

## 5. Публикуемые пакеты

### 5.1 Backend

```text
Distribution: orcestr-auth
Python import: orcestr_auth
```

На первом этапе публикуется один Python-пакет. Внутри него сохраняются строгие
слои, чтобы позднее при необходимости выделить адаптеры без переписывания core.

Предполагаемые optional extras:

```text
orcestr-auth[fastapi]
orcestr-auth[sqlalchemy]
orcestr-auth[oauth]
orcestr-auth[all]
```

В Orcestr можно сначала использовать `[all]`, а после стабилизации сузить набор.

### 5.2 Frontend

```text
@orcestr/auth-core
@orcestr/auth-react
@orcestr/auth-forms
@orcestr/auth-next
```

Next.js является обязательным first-class consumer первой версии. При этом
Next.js-зависимости нельзя помещать в универсальные `auth-core`, `auth-react` и
`auth-forms`: server/proxy интеграция изолируется в `@orcestr/auth-next`.

## 6. Ответственность frontend-пакетов

### 6.1 `@orcestr/auth-core`

Не зависит от React, React Query, Next.js и `@orcestr/ui`.

Содержит:

- типы auth API и стабильные коды ошибок;
- HTTP client/configuration contract;
- безопасную обработку `next` и защиту от open redirect;
- post-auth target и правила его очистки;
- построение login/register/logout/OAuth URL;
- OAuth state helpers и проверку callback-параметров;
- browser session flow: login, refresh, logout, current user;
- CSRF header policy для cookie-auth запросов;
- нормализацию ошибок backend;
- общие locale/surface hints без знания маршрутов конкретного продукта.

Core не должен самостоятельно рисовать UI и не должен импортировать router
конкретного фреймворка.

### 6.2 `@orcestr/auth-react`

Зависит от `@orcestr/auth-core`, React и React Query. Не зависит от
`@orcestr/ui`.

Содержит:

- `AuthProvider`;
- `useAuth` и `useCurrentUser`;
- login/register/logout/refresh mutations;
- hooks для password reset и email verification;
- session bootstrap и согласованную React Query cache policy;
- headless form hooks;
- guards и декларативные auth-state компоненты без оформления;
- callbacks для навигации, а не жёсткую привязку к Next router.

React и React Query указываются как `peerDependencies`.

### 6.3 `@orcestr/auth-forms`

Зависит от `@orcestr/auth-react` и использует `@orcestr/ui`.

Содержит готовые формы, но не страницы:

- `LoginForm`;
- `RegisterForm`;
- `ForgotPasswordForm`;
- `ResetPasswordForm`;
- `VerifyEmailForm`;
- `ChangePasswordForm`;
- `OAuthButtons`.

Формы отвечают за поля, валидацию, loading/error/success состояния и вызов auth
use cases. Они не владеют route, metadata, логотипом и redirect конкретного
приложения.

`RegisterForm` должен поддерживать extension slots/props для продуктовых полей и
legal acceptance. Сама auth-библиотека не должна владеть перечнем юридических
документов Orcestr: приложение передаёт требования и отображение через контракт.

React, React DOM, React Query и `@orcestr/ui` должны быть `peerDependencies`,
чтобы consumer не получил вторые экземпляры библиотек.

### 6.4 Где находится layout страницы

Auth-библиотека не экспортирует страницы или page shell. `orcestr-ui` также не добавляет
отдельный wrapper только для форм: для простых публичных экранов достаточно семантических
`main`/`header`/`footer` и базовых `Box`, `Flex`, `Card`. Полноценный application chrome уже
покрывает `AppShell`.

Приложение самостоятельно собирает страницу и передаёт навигацию форме:

```tsx
<main className='auth-page'>
    <Card>
        <LoginForm
            registerHref='/register'
            forgotPasswordHref='/forgot-password'
            onSuccess={handleLoginSuccess}
        />
    </Card>
</main>
```

### 6.5 `@orcestr/auth-next`

Пакет входит в первую версию, потому что Orcestr и основные consumer-приложения
используют Next.js. Он остаётся тонким адаптером и не содержит форм или страниц.

Содержит:

- server-safe helpers для App Router;
- helpers для `proxy.ts`/middleware;
- сохранение и проверку `next` при серверных redirect;
- интеграцию auth cookies с Next request/response;
- адаптер навигации для auth callbacks;
- защиту от расхождения browser и server redirect logic.

Страницы `app/login`, `app/register` и остальные route files по-прежнему создаёт
приложение. `auth-next` помогает им подключить общий auth flow, но не владеет URL
структурой продукта.

### 6.6 Локализация форм

Русский и английский обязательны в первой версии. `@orcestr/auth-forms` содержит
встроенные типизированные словари `ru` и `en` без обязательной зависимости от
внешнего i18n-framework.

Публичный API должен поддерживать:

```tsx
<AuthI18nProvider locale='ru'>
    <LoginForm />
</AuthI18nProvider>
```

или эквивалентный `locale` на уровне forms provider. Приложение может передать
частичные overrides для product wording, но обязательные ключи и оба базовых
словаря поставляются библиотекой. Backend возвращает стабильные machine-readable
error codes, а пользовательский текст выбирается frontend по locale.

### 6.7 UI управления сессиями

Session management UI означает экран со списком браузеров/устройств, датами
входа и кнопками принудительного отзыва каждой сессии. Такой UI в первую версию
и текущий scope библиотеки не входит; `SessionList` не создаём.

Это не отменяет серверное управление сессиями: ротация, replay detection,
logout текущей сессии и security-revoke продолжают работать. Приложение при
необходимости сможет построить отдельный UI позднее поверх backend API.

## 7. Ответственность backend-пакета

### 7.1 Domain/application core

В core переносим:

- выпуск и проверку access JWT;
- обязательные claims: issuer, audience, issued-at, JWT ID и session ID;
- opaque refresh tokens и хранение только их hash;
- ротацию refresh token;
- обнаружение replay и отзыв скомпрометированной session family;
- сроки жизни access/refresh сессий;
- logout одной сессии и logout всех сессий пользователя;
- password hashing policy;
- password reset token/code flow;
- email verification flow;
- OAuth state, PKCE, account linking rules;
- одноразовые WebSocket tickets;
- rate-limit policy и security event contract;
- единый набор машинных кодов ошибок;
- clock/random/token-hasher abstractions для детерминированных тестов.

### 7.2 FastAPI adapter

В адаптер переносим router factories и dependencies для:

- browser login/register/logout/refresh/current-user;
- explicit token login/refresh для API clients и тестов;
- email verification;
- forgot/reset password;
- OAuth start/callback/link/unlink;
- WebSocket ticket issue;
- session list/revoke, если этот API будет публичным.

Router factory должен принимать конфигурацию и реализации интерфейсов. Он не
должен импортировать глобальный `app`, Orcestr settings или Orcestr DB session.

### 7.3 Cookies и CSRF

Библиотека задаёт безопасные механизмы и конфигурацию:

- HttpOnly access/refresh cookies;
- Secure, SameSite, Path и Domain;
- единое удаление cookies с теми же атрибутами;
- CSRF-проверку изменяющих cookie-auth запросов;
- allowlist доверенных origins;
- запрет возврата browser tokens в JSON;
- отдельные token endpoints для осознанных non-browser clients.

Конкретные имена cookies, domain, secure mode и origins передаются приложением.

### 7.4 Публичное подключение модели пользователя

Принятое решение: таблицей и ORM-моделью пользователя владеет приложение.
Auth-библиотека не создаёт второго пользователя и ничего не синхронизирует.
Связь всех auth-сущностей строится относительно настоящего primary key
переданного `UserORM`.

Обычное подключение должно быть декларативным:

```python
auth = configure_auth(
    session_dependency=get_control_db_session,
    user_model=UserORM,
    fields=UserFields(
        id=UserORM.id,
        username=UserORM.username,
        email=UserORM.email,
        password_hash=UserORM.password_hash,
        is_active=UserORM.is_active,
        email_verified=UserORM.email_verified,
    ),
    registration_handler=OrcestrRegistrationHandler(),
)
```

Конфигурация создаётся один раз при запуске. Библиотека заранее связывает
переданные SQLAlchemy attributes и строит прямые запросы к `UserORM`. На каждом
запросе не должно быть runtime-reflection, поиска полей по строкам или
преобразования через промежуточную таблицу.

Для стандартного приложения достаточно передать модель, mapping полей и session
dependency. Собственный repository писать не требуется.

### 7.5 Внутренние порты и расширение нестандартных проектов

Внутри библиотеки остаются протоколы:

```text
UserRepository
AuthSessionRepository
PasswordResetRepository
OAuthAccountRepository
EmailVerificationRepository
EmailSender
SecurityEventSink
RateLimiter
TransactionManager
Clock
TokenHasher
```

`configure_auth` автоматически создаёт стандартный `SqlAlchemyUserRepository`
поверх переданного `UserORM`. Protocol нужен под капотом для unit-тестов и как
точка расширения. Проект передаёт собственную реализацию только тогда, когда его
пользователи находятся не в обычной SQLAlchemy-модели или требуют нестандартных
операций.

Orcestr предоставляет только интеграции, которые действительно специфичны для
приложения: registration handler, control session, почту, Redis и audit sink.

### 7.6 Auth-таблицы, общий registry и реальные foreign keys

Auth-библиотека владеет определениями auth-таблиц, но подключает их к SQLAlchemy
registry/metadata приложения:

```python
auth_models = create_auth_models(
    registry=Base.registry,
    user_model=UserORM,
)
```

Фабрика выполняется один раз во время импорта моделей и создаёт стабильные ORM
классы для sessions, password reset, email verification, OAuth accounts и
WebSocket tickets. Она определяет тип ID и target table из `UserORM` и создаёт
обычные физические foreign keys:

```text
identity_auth_session.user_id -> user.id
identity_password_reset.user_id -> user.id
identity_email_verification.user_id -> user.id
identity_oauth_account.user_id -> user.id
identity_websocket_ticket.user_id -> user.id
```

Все таблицы находятся в той же metadata, что и модели приложения. Поэтому
SQLAlchemy, Alembic, `create_all` в тестах и foreign-key resolution видят одну
согласованную схему.

В Orcestr при переносе существующие ORM-классы заменяются экспортами из фабрики
с теми же table/column names. Схема БД не пересоздаётся и данные не копируются.

### 7.7 Alembic migrations

Миграция должна быть воспроизводимой для конкретной версии библиотеки:

- библиотека содержит неизменяемые versioned migration operations;
- consumer Alembic revision вызывает конкретную versioned operation и передаёт
  имя user table/column и тип ID;
- импорт моделей вызывает `create_auth_models` до формирования
  `target_metadata`;
- revision names auth-библиотеки имеют отдельный стабильный namespace;
- обновление Python-пакета без применения требуемой DB migration запрещено
  startup/CI compatibility check;
- существующая Orcestr schema при первом переносе сравнивается с generated
  metadata, и перенос классов не должен создавать ложный schema diff.

Consumer revision не должен вызывать изменяемую функцию вида `upgrade_latest`:
он всегда ссылается на зафиксированную операцию конкретной schema version.

### 7.8 Производительность SQLAlchemy adapter

Repository protocol не добавляет сетевой или DB-слой. Его стандартная реализация
выполняет тот же прямой SQLAlchemy `SELECT`/`UPDATE`, который сегодня написан в
Orcestr. Один вызов Python-метода не является значимой стоимостью относительно
запроса к PostgreSQL.

Обязательные правила:

- username/email хранятся нормализованными и ищутся по уникальным индексам;
- refresh token ищется по уникальному hash;
- session lookup использует индекс по session ID и составные индексы по
  `user_id/status/revoked_at`;
- OAuth identity имеет unique constraint `(provider, provider_user_id)`;
- reset/verification token hashes уникальны и индексированы вместе с expiry;
- обычный login не загружает memberships, roles и profile relations;
- одна auth-операция работает в одной control DB session/transaction;
- нет N+1, скрытых повторных запросов и обязательного Redis-cache пользователя;
- query count и основные query plans фиксируются integration/performance tests.

### 7.9 Регистрация и продуктовые данные

Библиотека умеет создать базового пользователя через стандартный handler. Для
Orcestr передаётся `OrcestrRegistrationHandler`, который в той же control DB
transaction создаёт необходимые legal acceptance, tenant, workspace и
membership. Auth core не знает структуры этих продуктовых таблиц.

### 7.10 Control DB

В Orcestr auth всегда работает через control DB session. Библиотечный адаптер не
должен случайно использовать tenant/domain session. Это фиксируется отдельным
integration-тестом.

### 7.11 OAuth-провайдеры в комплекте

Первая версия включает готовые adapters для:

- GitHub;
- Google;
- Яндекс.

Все три провайдера опциональны. Приложение может не включить ни одного, включить
один или любую комбинацию. Отсутствие credentials для выключенного provider не
является ошибкой конфигурации.

Backend получает явный список enabled providers и их server-side credentials.
Frontend получает только безопасное описание enabled providers и показывает в
`OAuthButtons` соответствующие кнопки. Client secret никогда не попадает во
frontend config. Каждый adapter использует общий state/PKCE/callback/account
linking security flow библиотеки и собственную нормализацию provider profile.

## 8. Что переносим из текущего Orcestr

### Backend

- `core/auth/jwt.py` — после удаления Orcestr-specific settings imports;
- cookie helpers;
- auth dependencies и разделение cookie/bearer flow;
- identity auth services;
- auth session, refresh rotation и replay protection;
- OAuth service и callback security;
- email verification;
- password reset;
- WebSocket ticket auth;
- фабрика auth-моделей, привязанная к registry приложения;
- стандартный SQLAlchemy user adapter;
- auth schemas и error codes;
- соответствующие unit/security tests.

### Frontend

- `safeNext` и post-auth target;
- auth API requests;
- OAuth helpers/callback logic;
- login/register/forgot/reset/verify form logic;
- auth cache/provider/hooks;
- общие auth-copy keys, если они не продуктовые;
- обязательные русские и английские словари форм;
- Next.js proxy/server redirect helpers в `@orcestr/auth-next`.

### Что остаётся в Orcestr

- реальные Next.js pages и route files;
- route registry модулей;
- выбор landing/dashboard для Deliveries, Beauty, Jewelry;
- логотипы, SEO metadata и продуктовые тексты;
- tenant memberships, roles и permissions;
- legal documents/acceptance policy приложения;
- `UserORM` как каноническая модель пользователя приложения;
- `OrcestrRegistrationHandler` для legal/tenant/workspace/membership flow;
- credentials и включение нужных OAuth providers;
- конфигурация email sender;
- wiring в FastAPI app и Next.js app.

## 9. API-контракт между backend и frontend

Источником истины является OpenAPI, сгенерированный backend auth router.

```text
Python schemas/routes
        ↓
auth OpenAPI artifact
        ↓
generated TypeScript client/types
        ↓
@orcestr/auth-core
        ↓
@orcestr/auth-react
        ↓
@orcestr/auth-forms
```

Правила:

- TypeScript request/response types не дублируются вручную.
- CI падает, если generated contract неактуален.
- Ошибки имеют стабильный `code`, а текст локализуется frontend.
- Breaking API change требует согласованного обновления Python и npm packages.
- Browser endpoints и token endpoints явно различаются в контракте.

## 10. Локальное подключение и production/deploy

Это обязательная часть переноса. Поведение должно повторять проверенную модель
`orcestr-ui`: локально разработчик может использовать sibling-репозиторий, но
tracked manifests и lock-файлы всегда указывают на опубликованные версии.

### 10.1 Как сейчас работает `orcestr-ui`

В текущем Orcestr:

- `frontend/package.json` содержит точную версию `@orcestr/ui`;
- `package-lock.json` разрешает её в npm registry;
- локальный `scripts/use-local-orcestr-ui.mjs` выполняет временный
  `npm install --no-save --package-lock=false ...@file:../../orcestr-ui`;
- локальная установка не изменяет tracked package manifest и lock;
- production Docker build получает контекст `./frontend` и выполняет `npm ci`;
- sibling `../orcestr-ui` физически не попадает в Docker context;
- поэтому deployment гарантированно использует опубликованную зафиксированную
  версию.

Для `orcestr-auth` нужен тот же инвариант.

### 10.2 Frontend auth packages в Orcestr

В `orcestr/frontend/package.json` должны быть точные версии:

```json
{
  "@orcestr/auth-core": "0.1.0",
  "@orcestr/auth-react": "0.1.0",
  "@orcestr/auth-forms": "0.1.0"
}
```

`package-lock.json` должен указывать на registry tarballs, а не `file:` links.

Добавляется единый локальный скрипт, например:

```text
frontend/scripts/use-local-orcestr-libraries.mjs
```

Он по флагам/переменным окружения временно устанавливает sibling packages:

```text
ORCESTR_UI_LOCAL=1
ORCESTR_AUTH_LOCAL=1
```

или отдельная команда:

```text
npm run auth:local
```

Локальная команда должна использовать:

```text
npm install --no-save --package-lock=false --install-links=true \
  @orcestr/auth-core@file:../../orcestr-auth/frontend/packages/core \
  @orcestr/auth-react@file:../../orcestr-auth/frontend/packages/react \
  @orcestr/auth-forms@file:../../orcestr-auth/frontend/packages/forms
```

Точные пути проверяются скриптом через `package.json.name`. Ошибка отсутствующего
sibling-репозитория должна быть явной.

Production правила:

- Dockerfile не копирует `../orcestr-auth`;
- Docker build продолжает использовать context `./frontend`;
- dependency stage выполняет `npm ci` по committed lock;
- local env flags не передаются в production build;
- CI запрещает `file:`, `link:` и абсолютные локальные пути в committed lock;
- Next `transpilePackages` дополняется опубликованными auth-пакетами только если
  формат их сборки действительно этого требует.

### 10.3 Backend auth package в Orcestr

В `orcestr/backend/pyproject.toml` фиксируется опубликованная версия:

```toml
dependencies = [
    "orcestr-auth[all]==0.1.0",
]
```

`uv.lock` должен содержать wheel/sdist из выбранного registry с hash.

Для локальной разработки добавляется скрипт, который после обычного `uv sync`
временно ставит sibling package editable:

```text
uv pip install --editable ../../orcestr-auth/backend
```

Скрипт не меняет `pyproject.toml` и `uv.lock`. Для возврата к опубликованной
версии выполняется `uv sync --frozen` или отдельная команда `auth:published`.

Рекомендуемые команды/переменные:

```text
ORCESTR_AUTH_LOCAL=1
backend/scripts/use-local-orcestr-auth.ps1
backend/scripts/use-local-orcestr-auth.sh
```

Либо один кроссплатформенный Python-скрипт.

Production правила:

- `DockerfileBase` копирует только committed `pyproject.toml` и `uv.lock`;
- `uv sync --frozen --no-dev --no-install-project` устанавливает опубликованный
  пакет;
- sibling directory не используется и не монтируется;
- локальный editable package не может попасть в image;
- deploy не выполняется, если lock-файл не соответствует manifest.

### 10.4 Registry

Registry — это хранилище, из которого package manager устанавливает готовую
версию библиотеки. Для frontend это npm registry, для Python backend — PyPI.

Принятое решение для первой версии:

- `@orcestr/auth-*` публикуются публично в npm registry, как `@orcestr/ui`;
- `orcestr-auth` публикуется публично в PyPI;
- перед первым release проверяется доступность Python distribution name.

Public означает, что любой может скачать исходный package artifact. Это не
раскрывает JWT secrets, OAuth client secrets, пароли или production config: они
никогда не входят в package и передаются только приложением через окружение.

Private registry потребовал бы авторизацию каждого developer/CI/deploy consumer
и отдельное обслуживание доступа, поэтому без отдельной коммерческой причины он
не используется. Publish tokens npm/PyPI хранятся только в CI secrets и не
попадают в репозиторий.

### 10.5 Release discipline

- Сначала build/test/pack всех изменённых пакетов.
- Проверить содержимое `npm pack --dry-run` и Python wheel.
- Опубликовать package versions.
- Затем обновить точные версии и lock-файлы в Orcestr.
- Прогнать Orcestr integration tests.
- Только после этого деплоить Orcestr.
- Никогда не деплоить Orcestr с version, которая ещё не опубликована.

## 11. Миграция без legacy/fallback

Мы не оставляем две параллельные реализации auth flow. Каждый этап заканчивается
переключением Orcestr на библиотечный код и удалением перенесённого локального
кода.

Временная совместимость допустима только внутри короткой миграционной ветки и не
должна попадать в итоговую архитектуру.

## 12. Этапы реализации

### Этап 0. Зафиксировать текущее поведение

- Довести текущие auth changes в Orcestr до зелёных targeted/integration tests.
- Зафиксировать endpoint matrix и browser/token flows.
- Зафиксировать security invariants тестами.
- Описать конфигурацию cookies, origins, JWT и OAuth providers.

Результат: проверяемая baseline-реализация, из которой можно безопасно извлекать.

### Этап 1. Scaffold репозитория

- Инициализировать Git repository в `orcestr-auth`.
- Создать Python package и npm workspaces.
- Настроить build, unit tests, typecheck и packaging checks.
- Настроить changelog/versioning.
- Добавить минимальный example consumer.

### Этап 2. Frontend core

- Перенести safe next и post-auth target.
- Перенести auth API contract/client.
- Перенести OAuth helpers и error normalization.
- Подключить `@orcestr/auth-core` к Orcestr локально.
- Удалить дубли из Orcestr после прохождения тестов.

### Этап 3. React и Next.js adapters

- Вынести provider, hooks, mutations и cache policy.
- Зафиксировать API callbacks для навигации.
- Не переносить страницы и product route registry.
- Подключить `@orcestr/auth-react` к Orcestr и удалить локальные аналоги.
- Сразу создать `@orcestr/auth-next` и перенести в него общие `proxy.ts`,
  server-cookie и server-redirect helpers.
- Оставить Next.js route files и продуктовые URL в Orcestr.

### Этап 4. Forms

- Использовать семантическую разметку и существующие layout primitives без отдельного form page component.
- Вынести формы в `@orcestr/auth-forms`.
- Добавить полные встроенные словари `ru` и `en` и typed override contract.
- Добавить `OAuthButtons`, показывающий только enabled providers.
- Передавать ссылки, slots и callbacks через props.
- Оставить Next pages в Orcestr как тонкую композицию layout + form.

### Этап 5. Backend pure core

- Вынести tokens, sessions, password reset, verification и OAuth rules.
- Добавить опциональные adapters GitHub, Google и Яндекс с общей
  state/PKCE/linking политикой.
- Ввести внутренние repository/clock/email/rate-limit protocols.
- Написать unit tests без FastAPI и реальной БД.
- Реализовать стандартный SQLAlchemy user adapter по model/field mapping.
- Подключить core к `UserORM` и control DB Orcestr через декларативную
  конфигурацию.

### Этап 6. FastAPI adapter

- Вынести schemas, router factories и auth dependencies.
- Передавать control session, `UserORM`, field mapping и registration handler
  через wiring Orcestr.
- Сохранить endpoint contract или сделать осознанную breaking migration.
- Перегенерировать frontend contract из library router.

### Этап 7. SQLAlchemy models и migrations

- Реализовать `create_auth_models(registry, user_model)` на общей metadata.
- Подключить существующие auth table names Orcestr без копирования данных.
- Заменить локальные ORM-классы Orcestr библиотечными экспортами.
- Добавить versioned Alembic operations и auth revision namespace.
- Проверить отсутствие schema diff после переноса ownership классов.
- Проверить upgrade с текущей Orcestr schema без потери сессий/пользователей.

### Этап 8. Публикация и production integration

- Опубликовать Python и npm packages.
- Зафиксировать версии в Orcestr manifests и locks.
- Добавить local sibling scripts для frontend и backend.
- Проверить Docker images без sibling folders.
- Прогнать auth integration tests на собранных production images.
- Выполнить обычный deploy Orcestr и проверить login/register/refresh/logout,
  password reset, OAuth и WebSocket connection.

## 13. Обязательные security-инварианты

- `next` принимает только допустимые внутренние цели или allowlisted origins.
- Browser login/register/refresh не возвращают refresh/access tokens в JSON.
- Refresh token opaque, хранится только hash и ротируется при использовании.
- Replay старого refresh token отзывает session family.
- JWT проверяет signature, issuer, audience, expiry, token type и session state.
- Logout действительно отзывает серверную сессию, а не только удаляет cookie.
- Password reset и verification tokens одноразовые и имеют expiry.
- Reset/verification endpoints имеют rate limiting и не раскрывают существование
  email сверх принятой политики.
- OAuth использует state и PKCE, проверяет redirect origin и не выполняет
  неявный account linking.
- WebSocket не получает долговечный access token через URL; используется
  одноразовый короткоживущий ticket.
- Cookie-auth mutations защищены от CSRF.
- Security-sensitive события уходят в audit sink без записи raw secrets/tokens.
- Время на backend считается в UTC.

## 14. Тестовая матрица

### Backend unit

- JWT claims/validation;
- refresh rotation/replay/revocation;
- cookie attributes/delete symmetry;
- password reset expiry/one-time use;
- email verification expiry/one-time use;
- OAuth state/PKCE/linking;
- provider contract tests для GitHub, Google и Яндекс;
- выключенные OAuth providers не требуют credentials и не регистрируют routes;
- WebSocket ticket one-time use;
- rate-limit policy;
- model/field mapping validation;
- SQLAlchemy adapter строит прямые запросы без runtime-reflection;
- repository contract tests.

### Backend integration

- FastAPI browser flow с cookies;
- explicit bearer token flow;
- control DB isolation;
- auth models и `UserORM` находятся в одной metadata;
- реальные foreign keys auth tables указывают на переданный `UserORM.id`;
- transaction rollback;
- concurrency refresh race;
- query-count tests для login/refresh/current-user;
- проверка индексов и критичных PostgreSQL query plans;
- logout one/all sessions;
- OpenAPI contract snapshot.

### Frontend

- malicious/external/malformed `next`;
- post-auth target lifecycle;
- OAuth callback success/error;
- form validation и backend error mapping;
- loading/double-submit protection;
- provider bootstrap/refresh/logout;
- формы не зависят от Next router;
- полный набор form copy keys присутствует в `ru` и `en`;
- locale switching и product text overrides;
- OAuth buttons соответствуют enabled providers;
- Next proxy/server redirect helpers совпадают с browser safe-next policy;
- package consumer test с одной копией React/React Query/UI.

### Orcestr integration

- Start Free/Sign In с каждого landing ведут в нужный модуль;
- после login/register пользователь возвращается в исходный surface;
- refresh работает после перезагрузки страницы;
- logout закрывает HTTP и WebSocket доступ;
- reset/verify/OAuth работают через реальные Orcestr pages;
- production Docker build использует registry packages;
- local dev использует sibling sources при включённом local mode.

## 15. CI/CD для `orcestr-auth`

Минимальные jobs:

- backend unit/integration tests;
- frontend unit tests и typecheck;
- OpenAPI/generated contract freshness check;
- build Python wheel/sdist;
- `npm pack --dry-run` и package exports test;
- example consumer build;
- проверка отсутствия secrets;
- dependency/security scan;
- release job по tag/manual approval.

Публикация каждого package должна быть идемпотентной и не происходить из обычной
feature branch.

## 16. Версионирование

- Каждый публикуемый package имеет SemVer.
- На раннем этапе допустимы версии `0.x`, но breaking changes всё равно
  документируются.
- Python и npm версии не обязаны всегда совпадать.
- Изменение общего HTTP-контракта требует совместимых диапазонов и release notes.
- Orcestr использует точные versions, не `latest`, `*`, workspace или git HEAD.

## 17. Definition of Done

Выделение считается завершённым, когда:

- Orcestr использует опубликованные backend/frontend auth packages;
- локальный режим использует sibling `orcestr-auth` без изменения lock-файлов;
- production Docker build не видит sibling repository;
- страницы остаются в Orcestr, формы находятся в `@orcestr/auth-forms`;
- auth packages не экспортируют страницы или form-specific page shell;
- `@orcestr/auth-next` входит в первую версию, но не содержит страниц;
- формы имеют встроенные полные словари `ru` и `en`;
- GitHub, Google и Яндекс доступны как независимо включаемые providers;
- UI списка/управления сессиями отсутствует в текущем scope;
- auth core не импортирует Orcestr modules;
- стандартное подключение принимает control session, `UserORM` и field mapping;
- repository protocol остаётся внутренней деталью и не требует boilerplate от
  обычного consumer;
- auth tables имеют реальные FK на `UserORM.id` и общую metadata приложения;
- Orcestr-specific registration handler мал и явно отделён;
- критичные auth-запросы индексированы и не создают N+1;
- нет дублирующей legacy-реализации в Orcestr;
- contract generation и package checks работают в CI;
- security и Orcestr integration test matrix зелёная;
- выполнена ручная проверка production-like login/register/refresh/logout,
  reset/verify/OAuth/WebSocket flow.

## 18. Принятые продуктовые решения

- npm packages публикуются публично в npm registry.
- Python package публикуется публично в PyPI.
- `@orcestr/auth-next` входит в первую версию как тонкий Next.js adapter.
- Страницы и route files остаются в consumer-приложении.
- Формы имеют обязательные встроенные локализации `ru` и `en` с возможностью
  typed overrides.
- В комплект входят опциональные OAuth adapters GitHub, Google и Яндекс.
- Ни один OAuth provider не является обязательным.
- Session management UI и `SessionList` не входят в scope первой версии.
- Серверная безопасность и отзыв сессий остаются обязательной частью backend.
- `UserORM` принадлежит приложению; auth получает model/field mapping, создаёт
  стандартный adapter и подключает auth tables к registry приложения с
  реальными FK.

До scaffold остаётся только зафиксировать поддерживаемые диапазоны версий Python,
FastAPI, Next.js, React, React Query и `@orcestr/ui` на основе версий текущего
Orcestr. Это техническая фиксация peer/dependency ranges, а не открытый вопрос
архитектуры.

## 19. Статус реализации

Реализовано и проверено локально:

- Python package с core, FastAPI, SQLAlchemy, OAuth и versioned migration API;
- npm packages `auth-core`, `auth-react`, `auth-forms`, `auth-next`;
- формы без страниц, обязательные полные словари `ru`/`en`;
- GitHub, Google и Яндекс как независимо включаемые OAuth providers;
- auth-страницы собраны в Orcestr из семантической разметки и primitives `@orcestr/ui`;
- подключение Orcestr к библиотечным models, services, dependencies и router factory;
- browser cookie flow, bearer flow, refresh rotation/replay protection, reset,
  verification, OAuth и одноразовый WebSocket ticket;
- local sibling workflow без записи локальных путей в manifests/locks;
- build, package, security и release workflows;
- targeted backend integration tests и production Next.js build Orcestr.

До publication gate намеренно не выполняются только внешние операции:

- создание remote repository и push `orcestr-auth`;
- настройка PyPI/npm Trusted Publishing или локальная авторизация владельца;
- публикация `0.1.0` и фиксация опубликованных версий в manifests/locks Orcestr;
- production Docker build/deploy, который по правилу проекта не может ссылаться
  на неопубликованные или sibling packages.

Эти пункты не требуют изменений архитектуры или кода библиотеки, но требуют
владельца registry/repository. После выдачи доступа выполняется release workflow,
затем `scripts/check-published-dependencies.ps1`, production image build и deploy.
