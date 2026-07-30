<p align="right"><a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/forms/README.md">English</a> · <strong>Русский</strong></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" /></a></p>

# @orcestr/auth-forms

[![npm](https://img.shields.io/npm/v/@orcestr/auth-forms)](https://www.npmjs.com/package/@orcestr/auth-forms)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Готовые формы авторизации на [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui).
Пакет экспортирует формы, но не страницы, routes, metadata и product branding.

## Установка

```bash
npm install @orcestr/auth-core @orcestr/auth-react @orcestr/auth-forms
npm install @orcestr/ui @tanstack/react-query react react-dom
```

## Формы

- `LoginForm`
- `RegisterForm`
- `ForgotPasswordForm`
- `ResetPasswordForm`
- `VerifyEmailForm`
- `ChangePasswordForm`
- `OAuthButtons`

## Локализация

Полные английский и русский словари встроены в пакет. Приложение выбирает locale и может
переопределять product wording без копирования форм:

```tsx
import { AuthI18nProvider, LoginForm } from '@orcestr/auth-forms';

<AuthI18nProvider locale="ru">
    <LoginForm
        next="/deliveries/overview"
        registerHref="/register?next=%2Fdeliveries%2Foverview"
        onSuccess={(user) => router.replace('/deliveries/overview')}
    />
</AuthI18nProvider>;
```

Формы принимают callbacks, ссылки, slots и product extensions, включая registration
`extraPayload` и `legalContent`. Consumer собирает страницы из семантического HTML и
существующих layout primitives `@orcestr/ui`; application routes и surface-aware navigation
остаются локальными.

## Компоненты OAuth-кнопок

По умолчанию OAuth-провайдеры отображаются стандартными полноразмерными кнопками. Продукт может
одним компонентом заменить все кнопки, отдельно переопределить нужных провайдеров и выбрать
компоновку группы, не копируя логику авторизации:

```tsx
import {
    LoginForm,
    type OAuthProviderButtonProps,
} from '@orcestr/auth-forms';
import { IconButton, Tooltip } from '@orcestr/ui';
import { FcGoogle } from 'react-icons/fc';

function GoogleButton({ label, onClick }: OAuthProviderButtonProps) {
    return (
        <Tooltip content={label}>
            <IconButton type="button" aria-label={label} onClick={onClick} round>
                <FcGoogle />
            </IconButton>
        </Tooltip>
    );
}

<LoginForm
    methods={methods}
    oauthButtons={{
        direction: 'row',
        justify: 'center',
        buttonComponents: { google: GoogleButton },
    }}
/>;
```

Компонент получает провайдера, локализованную доступную подпись и готовое действие `onClick`.
Client ID, PKCE, state, redirect URI и навигация остаются внутри библиотеки.
