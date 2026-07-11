# Участие в разработке

[English version](./CONTRIBUTING.md)

Orcestr Auth — публичная основа авторизации, выделенная из реальной разработки Orcestr.
Изменения должны сохранять явные границы безопасности и оставаться применимыми вне основного
приложения.

## Разработка

Проверки backend:

```bash
cd backend
uv sync --frozen
uv run pytest -q
uv build
```

Проверки frontend:

```bash
cd frontend
npm ci
npm test
npm run pack:dry-run
```

## Checklist изменения

В pull request укажите:

- какой публичный пакет и контракт изменён;
- влияние на browser-cookie и bearer flows;
- последствия для sessions, tokens, redirects, OAuth или CSRF;
- влияние на схему/миграции и связь с моделью пользователя приложения;
- обновления английской и русской документации или текстов форм;
- как изменение проверялось в consumer-приложении.

Не редактируйте сгенерированный `dist/` вручную. Не коммитьте credentials, raw tokens,
локальные package paths и production-данные пользователей.
