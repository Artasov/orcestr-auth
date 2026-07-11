<p align="right"><a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/next/README.md">English</a> · <strong>Русский</strong></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" /></a></p>

# @orcestr/auth-next

[![npm](https://img.shields.io/npm/v/@orcestr/auth-next)](https://www.npmjs.com/package/@orcestr/auth-next)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Тонкие Next.js proxy и server redirect helpers для `@orcestr/auth-core`. Пакет не содержит
страниц или product route registry.

## Установка

```bash
npm install @orcestr/auth-core @orcestr/auth-next next
```

## Использование

```ts
import { authLoginRedirect } from '@orcestr/auth-next';

export function proxy(request: NextRequest) {
    return authLoginRedirect(request, {
        accessCookieName: 'orcestr_access',
        refreshCookieName: 'orcestr_refresh',
        loginPath: '/login',
        isProtectedPath: (pathname) => pathname.startsWith('/deliveries/'),
    });
}
```

Exports: `hasAuthSession`, `authLoginRedirect` и `requestAuthNext`.

Consumer определяет public/protected routes, host-aware visible paths и итоговую навигацию.
Так сохраняется единая redirect safety policy без переноса application pages в библиотеку.
