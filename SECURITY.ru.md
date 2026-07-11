# Политика безопасности

[English version](./SECURITY.md)

## Поддерживаемые версии

Пока пакеты находятся в beta, исправления безопасности выпускаются из default branch.

## Сообщение об уязвимости

Не создавайте публичный issue. Передайте информацию maintainer приватно через GitHub.

Укажите пакет и версию, сценарий атаки, необходимые права, возможную утечку данных, контекст
browser/backend и минимальное воспроизведение. Не отправляйте настоящие tokens, credentials
или персональные данные.

## Критичные зоны

Особого review требуют JWT validation, password hashing, refresh rotation/replay, cookies,
CSRF, safe redirects, OAuth state/PKCE/linking, verification/reset codes, WebSocket tickets,
rate limits, audit data, SQLAlchemy ownership и release artifacts.

Полный контракт описан в
[docs/security/invariants.ru.md](./docs/security/invariants.ru.md).
