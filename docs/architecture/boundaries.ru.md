# Архитектурные границы

[English version](./boundaries.md)

## Структура репозитория

Orcestr Auth — монорепозиторий, потому что Python- и frontend-пакеты реализуют единый HTTP- и
security-контракт и должны проверяться вместе. При этом каждый artifact устанавливается
отдельно и имеет собственный package README в
[индексе пакетов](../../README.ru.md#пакеты).

## Ownership

Consumer-приложение владеет:

- таблицей пользователя и полями product profile;
- страницами, route registry, брендингом и metadata;
- legal acceptance, tenant/workspace bootstrap и memberships;
- permissions, product navigation, audit storage и отправкой писем.

Orcestr Auth владеет:

- password hashing и token validation;
- browser cookies, CSRF policy и bearer flow;
- серверными sessions и refresh rotation/replay handling;
- recovery codes, OAuth exchange и WebSocket tickets;
- auth-таблицами и стандартными SQLAlchemy/FastAPI adapters;
- browser client, React hooks, forms и Next.js guards.

## Модель пользователя

Приложение передаёт SQLAlchemy registry, `UserORM` и `UserFieldMap`. Библиотека создаёт
auth-модели в той же metadata и настоящие foreign keys на actual primary key.
`SqlAlchemyUserRepository` выполняет прямые запросы по mapped columns.

Repository protocols остаются внутренними extension points для нестандартных consumers.
Обычному приложению не требуется писать repository boilerplate или раскрывать весь domain
model.

## Product hooks

`AuthHttpApplication` — явная граница для registration, login policy, legal acceptance, tenant
bootstrap, audit, rate limits и email delivery. Переиспользуемый router владеет матрицей
endpoints и безопасным форматом browser/token responses.

## Frontend layers

```text
@orcestr/auth-core -> @orcestr/auth-react -> @orcestr/auth-forms -> @orcestr/ui
                  \-> @orcestr/auth-next
```

- [`@orcestr/auth-core`](../../frontend/packages/core/README.ru.md) — browser
  client и слой session/refresh;
- [`@orcestr/auth-react`](../../frontend/packages/react/README.ru.md) — headless
  React Query state и hooks;
- [`@orcestr/auth-forms`](../../frontend/packages/forms/README.ru.md) — готовые
  формы на [Orcestr UI](https://github.com/Artasov/orcestr-ui);
- [`@orcestr/auth-next`](../../frontend/packages/next/README.ru.md) — Next.js
  guards и безопасные server redirects.

`auth-core` не зависит от framework. React- и Next.js-адаптеры зависят от core, но не друг от
друга. Формы используют headless React hooks и UI kit, но не владеют страницами.
«Consumer-приложение» означает продукт, который подключает эти пакеты: он собирает страницы из
семантического HTML и существующих UI primitives, а route files остаются в этом приложении.
