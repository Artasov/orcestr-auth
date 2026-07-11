<p align="right"><strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/next/README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# @orcestr/auth-next

[![npm](https://img.shields.io/npm/v/@orcestr/auth-next)](https://www.npmjs.com/package/@orcestr/auth-next)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Thin Next.js proxy and server redirect helpers for `@orcestr/auth-core`. The package does not
contain pages or a product route registry.

## Install

```bash
npm install @orcestr/auth-core @orcestr/auth-next next
```

## Usage

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

Exports: `hasAuthSession`, `authLoginRedirect` and `requestAuthNext`.

The consumer defines public/protected routes, host-aware visible paths and final navigation.
This keeps one redirect safety policy without moving application pages into the library.
