<p align="right"><strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/react/README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# @orcestr/auth-react

[![npm](https://img.shields.io/npm/v/@orcestr/auth-react)](https://www.npmjs.com/package/@orcestr/auth-react)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Headless React Query bindings for `@orcestr/auth-core`. The package does not depend on a UI
kit or routing framework.

## Install

```bash
npm install @orcestr/auth-core @orcestr/auth-react @tanstack/react-query
```

## Usage

Place it inside your application `QueryClientProvider`:

```tsx
import { AuthProvider, useCurrentUser, useLogout } from '@orcestr/auth-react';

export function Providers({ children }) {
    return <AuthProvider client={authClient}>{children}</AuthProvider>;
}

export function ProfileAction() {
    const user = useCurrentUser();
    const logout = useLogout();
    // Render with your own UI and router.
}
```

## Hooks

`useCurrentUser`, `useLogin`, `useRegister`, `useLogout`,
`usePasswordResetRequest`, `usePasswordResetConfirm`, `useEmailVerification` and
`useAuthClient`.

Pages, navigation callbacks and visual components remain consumer-owned. Ready forms are
available separately in [`@orcestr/auth-forms`](https://github.com/Artasov/orcestr-auth/tree/main/frontend/packages/forms#readme).
