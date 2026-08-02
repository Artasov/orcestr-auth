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
npm install @orcestr/ui @tanstack/react-query react react-dom react-icons
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
import { AuthI18nProvider, LoginForm } from "@orcestr/auth-forms";

<AuthI18nProvider locale="ru">
  <LoginForm
    next="/dashboard"
    registerHref="/register?next=%2Fdashboard"
    onSuccess={(user) => router.replace("/dashboard")}
  />
</AuthI18nProvider>;
```

Сообщения выбираются по стабильным API error codes вроде `invalid_credentials`, а не по
английскому fallback-тексту сервера. Поэтому смена locale применяется и к validation/request
errors, и к подписям формы.

Формы принимают callbacks, ссылки, slots и product extensions, включая registration
`extraPayload` и `legalContent`. Consumer собирает страницы из семантического HTML и
существующих layout primitives `@orcestr/ui`; application routes и surface-aware navigation
остаются локальными.

## Компоненты OAuth-кнопок

По умолчанию OAuth-провайдеры отображаются стандартными полноразмерными кнопками. Продукт может
одним компонентом заменить все кнопки, отдельно переопределить нужных провайдеров и выбрать
компоновку группы, не копируя логику авторизации:

```tsx
import { LoginForm, type OAuthProviderButtonProps } from "@orcestr/auth-forms";
import { IconButton, Tooltip } from "@orcestr/ui";
import { FcGoogle } from "react-icons/fc";

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
    placement: "after-submit",
    direction: "row",
    justify: "center",
    buttonComponents: { google: GoogleButton },
  }}
/>;
```

Компонент получает провайдера, локализованную доступную подпись и готовое действие `onClick`.
Client ID, PKCE, state, redirect URI и навигация остаются внутри библиотеки.

`placement` принимает `before-fields`, `after-submit` или `after-links` и одинаково работает в
формах входа и регистрации.

## Версионированное принятие документов

`LoginForm` и `RegisterForm` могут защищать password- и OAuth-действия общей настраиваемой
модалкой юридических документов. Сами документы принадлежат приложению и могут загружаться из БД;
пакет отвечает за отображение, обязательные и необязательные галочки, продолжение действия и
перенос payload через OAuth callback state.

```tsx
<LoginForm
  legalConsent={{
    documents: legalDocuments.map((document) => ({
      id: document.slug,
      title: document.title,
      version: document.version,
      href: `/legal/${document.slug}`,
      required: document.required,
      acceptance: {
        document_slug: document.slug,
        version: document.version,
        language: document.language,
      },
    })),
  }}
/>
```

Для отключения gate используется `enabled: false`. Если backend ожидает другой контракт, можно
задать `payloadKey` или `buildPayload`. Количество документов не ограничено.
