# Инварианты безопасности

[English version](./invariants.md)

Эти правила являются частью публичного контракта и не могут ослабляться как compatibility
fallback.

## Browser и tokens

- Browser access и refresh tokens хранятся в HttpOnly cookies и не возвращаются в browser JSON.
- Cookie-authenticated mutations требуют настроенный CSRF header.
- Bearer endpoints явные и возвращают tokens только клиентам, выбравшим этот flow.
- JWT validation проверяет signature, issuer, audience, expiry, token type, JTI и session state.
- Raw tokens и credentials не попадают в logs, audit payloads или package artifacts.

## Sessions

- Refresh tokens opaque и случайные; в БД хранится только hash.
- Каждый успешный refresh ротирует token.
- Повторное использование старого refresh token отзывает всю server-side session family.
- Logout отзывает серверную сессию до удаления cookies.
- Критичные lookup используют стабильные индексы и не зависят от runtime reflection.

## Recovery

- Коды password reset и email verification хешируются, истекают и одноразовые.
- Количество попыток и частота повторной отправки ограничены.
- Password reset не раскрывает существование email сверх product policy.

## OAuth

- Включаются только явно настроенные GitHub, Google и Яндекс providers.
- Browser authorization использует непредсказуемый state и PKCE.
- Backend проверяет callback redirect origins.
- Provider identity не привязывается неявно к password-аккаунту по совпавшему email; linking
  требует отдельного authenticated product flow.

## Navigation и WebSocket

- `next` принимает только безопасные внутренние paths и отклоняет external, malformed и
  auth-loop targets.
- WebSocket URL не содержит долгоживущий access token; используется короткоживущий одноразовый
  ticket.

## Время и storage

- Backend считает время в UTC.
- Auth-таблицы используют общую metadata приложения и настоящие foreign keys на user model.
