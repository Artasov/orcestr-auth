<p align="right"><strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/core/README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# @orcestr/auth-core

[![npm](https://img.shields.io/npm/v/@orcestr/auth-core)](https://www.npmjs.com/package/@orcestr/auth-core)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Framework-independent browser authentication client for the Orcestr ecosystem. It has no
React, UI-kit or Next.js dependency.

## Install

```bash
npm install @orcestr/auth-core
```

## Includes

- `AuthClient` with cookie credentials, CSRF header and one automatic refresh/retry;
- typed user, methods, route and OAuth contracts;
- safe internal `next` validation and auth URL helpers;
- GitHub, Google and Yandex OAuth authorize URLs;
- browser state and PKCE verifier lifecycle.

## Usage

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

Applications own navigation and product-specific fallback targets.

Repository and complete architecture: [Orcestr Auth](https://github.com/Artasov/orcestr-auth).
