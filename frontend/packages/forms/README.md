<p align="right"><strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/forms/README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# @orcestr/auth-forms

[![npm](https://img.shields.io/npm/v/@orcestr/auth-forms)](https://www.npmjs.com/package/@orcestr/auth-forms)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Ready authentication forms built with [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui).
The package exports forms, not pages, routes, metadata or product branding.

## Install

```bash
npm install @orcestr/auth-core @orcestr/auth-react @orcestr/auth-forms
npm install @orcestr/ui @tanstack/react-query react react-dom
```

## Forms

- `LoginForm`
- `RegisterForm`
- `ForgotPasswordForm`
- `ResetPasswordForm`
- `VerifyEmailForm`
- `ChangePasswordForm`
- `OAuthButtons`

## Localization

Complete English and Russian dictionaries are built in. The application selects a locale and
may override product wording without copying the forms:

```tsx
import { AuthI18nProvider, LoginForm } from '@orcestr/auth-forms';

<AuthI18nProvider locale="en">
    <LoginForm
        next="/deliveries/overview"
        registerHref="/register?next=%2Fdeliveries%2Foverview"
        onSuccess={(user) => router.replace('/deliveries/overview')}
    />
</AuthI18nProvider>;
```

Forms expose callbacks, links, slots and product extensions such as registration
`extraPayload` and `legalContent`. The consumer composes pages from semantic HTML and existing
`@orcestr/ui` layout primitives; application routes and surface-aware navigation stay local.
