<p align="right"><strong>English</strong> · <a href="https://github.com/Artasov/orcestr-auth/blob/main/frontend/packages/forms/README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="https://raw.githubusercontent.com/Artasov/orcestr-auth/main/assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# @orcestr/auth-forms

[![npm](https://img.shields.io/npm/v/@orcestr/auth-forms)](https://www.npmjs.com/package/@orcestr/auth-forms)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://github.com/Artasov/orcestr-auth/blob/main/LICENSE)

Ready authentication forms built with [`@orcestr/ui`](https://github.com/Artasov/orcestr-ui).
The package exports forms, not pages, routes, metadata or product branding.

## Install

```bash
npm install @orcestr/auth-core @orcestr/auth-react @orcestr/auth-forms
npm install @orcestr/ui @tanstack/react-query react react-dom react-icons
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
import { AuthI18nProvider, LoginForm } from "@orcestr/auth-forms";

<AuthI18nProvider locale="en">
  <LoginForm
    next="/dashboard"
    registerHref="/register?next=%2Fdashboard"
    onSuccess={(user) => router.replace("/dashboard")}
  />
</AuthI18nProvider>;
```

Messages are resolved from stable API error codes such as `invalid_credentials`, not from the
server's English fallback text. Locale changes therefore apply to validation and request errors
as well as labels.

Forms expose callbacks, links, slots and product extensions such as registration
`extraPayload` and `legalContent`. The consumer composes pages from semantic HTML and existing
`@orcestr/ui` layout primitives; application routes and surface-aware navigation stay local.

## OAuth button components

OAuth providers use the standard full-width button by default. A product can replace all provider
buttons with one component, override individual providers, and choose the group layout without
copying authorization logic:

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

The component receives the provider, a localized accessible label and the ready `onClick`
authorization action. Client IDs, PKCE, state, redirect URI and navigation remain library-owned.

`placement` accepts `before-fields`, `after-submit`, or `after-links` and works in both login
and registration forms.

## Versioned legal consent

`LoginForm` and `RegisterForm` can guard password and OAuth actions with the same configurable
legal-document modal. Documents are application-owned and may come from a database; the package
only handles presentation, required/optional checkboxes, action continuation, and payload transfer
through the OAuth callback state.

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

Set `enabled: false` to disable the gate. Use `payloadKey` or `buildPayload` when the backend uses
a different acceptance contract. Any number of legal documents is supported.
