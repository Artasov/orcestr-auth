# Security invariants

[Русская версия](./invariants.ru.md)

These rules are part of the public contract and cannot be relaxed as a compatibility fallback.

## Browser and Tokens

- Browser access and refresh tokens are HttpOnly cookies and are not returned in browser JSON.
- Cookie-authenticated mutations require the configured CSRF header.
- Bearer endpoints are explicit and return tokens only to clients that request that flow.
- JWT validation checks signature, issuer, audience, expiry, token type, JTI and session state.
- Raw tokens and credentials never enter logs, audit payloads or package artifacts.

## Sessions

- Refresh tokens are opaque, random and stored only as hashes.
- Every successful refresh rotates the token.
- Reuse of an old refresh token revokes its complete server-side session family.
- Logout revokes the server session before clearing cookies.
- Critical lookups use stable indexed columns and do not depend on runtime reflection.

## Recovery

- Password reset and email verification codes are hashed, expiring and one-time.
- Attempts and resend frequency are limited.
- Password reset requests do not reveal whether an email exists beyond product policy.

## OAuth

- Only explicitly configured GitHub, Google and Yandex providers are enabled.
- Browser authorization uses unpredictable state and PKCE.
- Callback redirect origins are validated by the backend.
- A provider identity is never implicitly linked to an existing password account by matching
  email; linking requires an explicit authenticated product flow.

## Navigation and WebSocket

- `next` accepts safe internal paths only and rejects external, malformed and auth-loop targets.
- WebSocket URLs never carry long-lived access tokens; they use one-time short-lived tickets.

## Time and Storage

- Backend time is evaluated in UTC.
- Auth tables share application metadata and use real foreign keys to the configured user model.
