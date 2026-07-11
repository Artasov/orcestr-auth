# Пример интеграции

[English version](./README.md)

Production reference consumer — соседний репозиторий `orcestr`. Он использует:

- `create_auth_models(registry=Base.registry, user_model=UserORM)`;
- `UserFieldMap` и стандартный прямой SQLAlchemy adapter;
- `create_auth_dependencies` с control DB session;
- `create_auth_router` и небольшой Orcestr-specific `AuthHttpApplication`;
- `AuthProvider`, `AuthI18nProvider` и готовые формы внутри application pages;
- `@orcestr/auth-next` из application-owned Next.js proxy.

Здесь намеренно нет второго demo application: интеграция непрерывно проверяется на реальном
Orcestr, чтобы пример не расходился с production contract.
