<p align="right"><a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/core/README.md">English</a> · <strong>Русский</strong></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" /></a></p>

# @orcestr/auth-core

[![npm](https://img.shields.io/npm/v/@orcestr/auth-core)](https://www.npmjs.com/package/@orcestr/auth-core)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Независимый от framework browser-клиент авторизации для экосистемы Orcestr. В пакете нет
зависимости от React, UI kit или Next.js.

## Установка

```bash
npm install @orcestr/core @orcestr/auth-core
```

## Что входит

- `AuthClient` с cookie credentials, CSRF header и одним автоматическим refresh/retry;
- typed contracts пользователя, методов, routes и OAuth;
- проверка безопасного внутреннего `next` и helpers для auth URL;
- OAuth authorize URL для GitHub, Google и Яндекса;
- lifecycle browser state и PKCE verifier.
- stateless OAuth 2.1 authorization-code + PKCE helpers для public/native clients.

## Использование

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

`logging` принимает `true`, `false` или настройки `cutie-logs`. Чувствительные поля,
включая пароли и токены, автоматически скрываются.

Навигация и product-specific fallback targets остаются в приложении.

## Альтернативный transport приложения

`AuthClientContract<TUser>` — полный структурный контракт, который используют React adapter и
готовые формы. Стандартный `AuthClient` реализует его через browser cookies. Native-приложение
может реализовать те же методы через доверенный IPC bridge, сохранив поддержку email/password и
provider OAuth:

```ts
import type { AuthClientContract, AuthUser } from '@orcestr/auth-core';

export const nativeAuth: AuthClientContract<AuthUser> = createNativeAuthClient();
```

Реализация возвращает те же user/method contracts, включая `oauthCallback`, и отклоняет запросы
через `ApiError` из `@orcestr/core`, чтобы React hooks и локализованные формы работали одинаково.
Контракт не задаёт хранение токенов: native client должен держать access token вне renderer, а
refresh token — в защищённом системном хранилище.

## OAuth 2.1 для public/native clients

Desktop, mobile и другие public clients могут собрать authorization request и обменять код,
не включая client secret в приложение:

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

`createOAuthAuthorizationRequest` использует криптографически стойкие state и PKCE S256. SDK
не сохраняет state, verifier и полученные токены. Данные незавершённого flow хранятся только на
время authorization round trip, а приложение само выбирает память или защищённое системное
хранилище для токенов. Custom redirect scheme должен быть зарегистрирован в native-приложении
и точно добавлен в allowlist его OAuth client на authorization server. При разборе полного
callback URL всегда передавай `expectedRedirectUri`. Authorization и token endpoints должны
использовать HTTPS; HTTP разрешён только для `localhost`, `127.0.0.1` и `::1` при локальной
разработке. Встроенные credentials, query string и fragment отклоняются; authorization extensions
передаются через `additionalParameters`.

## Ошибки

При неуспешном запросе `AuthClient` выбрасывает `ApiError` из `@orcestr/core`. Для поведения и
локализации используй стабильные auth-коды:

```ts
import { isApiError } from '@orcestr/core';
import { AUTH_ERROR_CODES } from '@orcestr/auth-core';

try {
    await auth.login(username, password);
} catch (error) {
    if (isApiError(error) && error.code === AUTH_ERROR_CODES.invalidCredentials) {
        showLoginError('Неверный email, логин или пароль.');
    }
}
```

Готовые формы уже содержат английский и русский auth catalog. Headless consumers должны
передать собственный catalog и использовать серверный `message` только как безопасный
диагностический fallback.

Репозиторий и полная архитектура: [Orcestr Auth](https://github.com/Artasov/orcestr-auth).
