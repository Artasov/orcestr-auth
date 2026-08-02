# Подключение к приложению

[English](./application.md)

Это руководство описывает границу между пакетами Orcestr Auth и любым
приложением-потребителем. В примерах намеренно используются нейтральные маршруты,
домены и названия хранилищ.

## Frontend-пакеты

Установи только необходимые приложению уровни:

```bash
npm install @orcestr/auth-core @orcestr/auth-react
npm install @orcestr/auth-forms @orcestr/auth-next
```

- `@orcestr/auth-core` отвечает за независимый от UI клиент и auth-контракты.
- `@orcestr/auth-react` отвечает за состояние сессии и React hooks.
- `@orcestr/auth-forms` предоставляет необязательные готовые формы.
- `@orcestr/auth-next` предоставляет helpers для запросов и redirects в Next.js.

Страницы, названия маршрутов, брендинг, tenant bootstrap и адрес после
авторизации принадлежат приложению.

```tsx
<AuthProvider client={authClient}>
    <LoginForm onSuccess={() => router.replace('/dashboard')} />
</AuthProvider>
```

## Backend-пакет

```bash
pip install orcestr-auth
```

Приложение передаёт сессии базы данных, persistence-адаптеры, OAuth credentials,
отправку писем и продуктовую политику. Пакет предоставляет auth use cases,
стабильные коды ошибок, интеграцию с FastAPI и чувствительную к безопасности
механику flows.

Маршруты подключаются под префиксом, которым владеет приложение:

```python
app.include_router(auth_router, prefix="/api/auth")
```

## Проверка локальных пакетов

Неопубликованные frontend-пакеты проверяй через npm-архивы, а Python-пакет —
через editable installation в среде разработки. Не коммить локальные `file:`,
`link:` и editable paths в manifest- и lock-файлы приложения.

Production-сборки должны использовать фиксированные опубликованные версии и
устанавливать зависимости из registry по lock-файлам.

## Граница ответственности

Auth-пакеты не владеют permissions приложения, billing, бизнес-ролями,
политикой юридических документов, продуктовой аналитикой, страницами и
навигацией. Приложение собирает эти возможности вокруг auth-контрактов, а не
добавляет их в библиотеку.
