<p align="right"><a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/react/README.md">English</a> · <strong>Русский</strong></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" /></a></p>

# @orcestr/auth-react

[![npm](https://img.shields.io/npm/v/@orcestr/auth-react)](https://www.npmjs.com/package/@orcestr/auth-react)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Headless React Query bindings для `@orcestr/auth-core`. Пакет не зависит от UI kit и routing
framework.

## Установка

```bash
npm install @orcestr/auth-core @orcestr/auth-react @tanstack/react-query
```

## Использование

Разместите provider внутри `QueryClientProvider` приложения:

```tsx
import { AuthProvider, useCurrentUser, useLogout } from '@orcestr/auth-react';

export function Providers({ children }) {
    return <AuthProvider client={authClient}>{children}</AuthProvider>;
}

export function ProfileAction() {
    const user = useCurrentUser();
    const logout = useLogout();
    // Используйте собственные UI и router.
}
```

## Hooks

`useCurrentUser`, `useLogin`, `useRegister`, `useLogout`,
`usePasswordResetRequest`, `usePasswordResetConfirm`, `useEmailVerification` и
`useAuthClient`.

Страницы, navigation callbacks и визуальные компоненты остаются в consumer. Готовые формы
доступны отдельно в [`@orcestr/auth-forms`](https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/forms/README.ru.md).
