<p align="right"><a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/core/README.md">English</a> · <strong>Русский</strong></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" /></a></p>

# @orcestr/auth-core

[![npm](https://img.shields.io/npm/v/@orcestr/auth-core)](https://www.npmjs.com/package/@orcestr/auth-core)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Независимый от framework browser-клиент авторизации для экосистемы Orcestr. В пакете нет
зависимости от React, UI kit или Next.js.

## Установка

```bash
npm install @orcestr/auth-core
```

## Что входит

- `AuthClient` с cookie credentials, CSRF header и одним автоматическим refresh/retry;
- typed contracts пользователя, методов, routes и OAuth;
- проверка безопасного внутреннего `next` и helpers для auth URL;
- OAuth authorize URL для GitHub, Google и Яндекса;
- lifecycle browser state и PKCE verifier.

## Использование

```ts
import { AuthClient, safeRedirectPath } from '@orcestr/auth-core';

export const auth = new AuthClient({
    routes: {
        methods: '/api/v1/auth/methods/',
        login: '/api/v1/auth/login/',
        register: '/api/v1/auth/register/',
        me: '/api/v1/auth/me/',
        refresh: '/api/v1/auth/refresh/',
        logout: '/api/v1/auth/logout/',
        passwordResetRequest: '/api/v1/auth/password/reset/request/',
        passwordResetConfirm: '/api/v1/auth/password/reset/confirm/',
        emailVerificationCode: '/api/v1/auth/email/verification-code/',
        emailConfirm: '/api/v1/auth/email/confirm/',
        oauthCallback: (provider) => `/api/v1/auth/oauth/${provider}/callback/`,
    },
});

const next = safeRedirectPath(searchParams.get('next'), '/overview');
```

Навигация и product-specific fallback targets остаются в приложении.

Репозиторий и полная архитектура: [Orcestr Auth](https://github.com/Artasov/orcestr-auth).
