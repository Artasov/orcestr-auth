# Example integration

[Русская версия](./README.ru.md)

The production reference consumer is the sibling `orcestr` repository. It uses:

- `create_auth_models(registry=Base.registry, user_model=UserORM)`;
- `UserFieldMap` and the standard direct SQLAlchemy adapter;
- `create_auth_dependencies` with the control DB session;
- `create_auth_router` with a small Orcestr-specific `AuthHttpApplication`;
- `AuthProvider`, `AuthI18nProvider` and ready forms inside application pages;
- `@orcestr/auth-next` from the application-owned Next.js proxy.

This directory intentionally contains no duplicate demo application; integration
is continuously verified against the real Orcestr project.
