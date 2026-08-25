<p align="right"><strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/core/README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# @orcestr/auth-core

[![npm](https://img.shields.io/npm/v/@orcestr/auth-core)](https://www.npmjs.com/package/@orcestr/auth-core)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Framework-independent browser authentication client for the Orcestr ecosystem. It has no
React, UI-kit or Next.js dependency.

## Install

```bash
npm install @orcestr/core @orcestr/auth-core
```

## Includes

- `AuthClient` with cookie credentials, CSRF header and one automatic refresh/retry;
- typed user, methods, route and OAuth contracts;
- safe internal `next` validation and auth URL helpers;
- GitHub, Google and Yandex OAuth authorize URLs;
- browser state and PKCE verifier lifecycle.
- stateless OAuth 2.1 authorization-code + PKCE helpers for public/native clients.

## Usage

```ts
import { AuthClient, safeRedirectPath } from '@orcestr/auth-core';

export const auth = new AuthClient({
    logging: {
        enabled: process.env.NODE_ENV !== 'production',
        label: 'AUTH',
        logRequestsDelay: true,
    },
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

`logging` accepts `true`, `false`, or `cutie-logs` options. Sensitive fields such as
passwords and tokens are redacted automatically.

Applications own navigation and product-specific fallback targets.

## Alternative application transports

`AuthClientContract<TUser>` is the complete structural boundary used by the React adapter and
ready forms. The standard `AuthClient` implements it with browser cookies. Native applications
can instead implement the same methods over a trusted IPC bridge while preserving the existing
email/password and provider OAuth capabilities:

```ts
import type { AuthClientContract, AuthUser } from '@orcestr/auth-core';

export const nativeAuth: AuthClientContract<AuthUser> = createNativeAuthClient();
```

Implementations return the same user and method contracts as `AuthClient`, including
`oauthCallback`, and reject with `ApiError` from `@orcestr/core` so React hooks and localized
forms keep the same behavior. The contract does not prescribe token persistence; native clients
should keep access tokens out of the renderer and store refresh tokens in platform-secure storage.

## OAuth 2.1 public/native clients

Desktop, mobile and other public clients can build an authorization request and exchange its
code without shipping a client secret:

```ts
import {
    OAuthTokenClient,
    createOAuthAuthorizationRequest,
    parseOAuthCallback,
} from '@orcestr/auth-core';

const redirectUri = 'com.example.desktop://oauth/callback';
const pending = await createOAuthAuthorizationRequest({
    authorizationEndpoint: 'https://auth.example.com/oauth/authorize',
    clientId: 'my-desktop-app',
    redirectUri,
    scope: ['profile'],
});

await openExternal(pending.authorizationUrl);

const callback = parseOAuthCallback(receivedDeepLink, {
    expectedState: pending.state,
    expectedRedirectUri: redirectUri,
});
const tokens = await new OAuthTokenClient({
    tokenEndpoint: 'https://auth.example.com/oauth/token',
    clientId: 'my-desktop-app',
}).exchangeAuthorizationCode({
    code: callback.code,
    redirectUri,
    codeVerifier: pending.codeVerifier,
});
```

`createOAuthAuthorizationRequest` uses cryptographically secure state and PKCE S256. The SDK
does not persist state, the verifier or returned tokens. Keep pending flow data only for the
authorization round trip, and let the application choose memory or platform-secure storage for
tokens. A custom redirect scheme must be registered by the native application and allowlisted
exactly for its OAuth client on the authorization server. Always pass `expectedRedirectUri` when
parsing a full callback URL. Authorization and token endpoints must use HTTPS, except for HTTP on
`localhost`, `127.0.0.1` or `::1` during local development; embedded credentials, query strings
and fragments are rejected. Pass authorization extensions through `additionalParameters`.

## Errors

`AuthClient` rejects failed requests with `ApiError` from `@orcestr/core`. Use stable auth codes
for behavior and localization:

```ts
import { isApiError } from '@orcestr/core';
import { AUTH_ERROR_CODES } from '@orcestr/auth-core';

try {
    await auth.login(username, password);
} catch (error) {
    if (isApiError(error) && error.code === AUTH_ERROR_CODES.invalidCredentials) {
        showLoginError('Invalid email, username or password.');
    }
}
```

Ready forms already map the auth catalog for English and Russian. Headless consumers should
provide their own catalog and treat the server `message` only as a safe diagnostic fallback.

Repository and complete architecture: [Orcestr Auth](https://github.com/Artasov/orcestr-auth).
