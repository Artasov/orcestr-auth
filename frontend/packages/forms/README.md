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

### Loading available methods

Load methods through the headless hook and pass its state to the form:

```tsx
import { useAuthMethods } from "@orcestr/auth-react";
import { LoginForm } from "@orcestr/auth-forms";

function Login() {
  const methods = useAuthMethods();
  return <LoginForm
    methods={methods.data}
    methodsPending={methods.isPending}
    methodsError={methods.error}
    onRetryMethods={() => void methods.refetch()}
  />;
}
```

RegisterForm accepts the same props. Pending/error states render a localized status or retry
button and block submission/OAuth, instead of silently rendering an incomplete form.
`AuthMethodsStatus` is also exported for custom form compositions.

A provider is visible only when it is both allowed by `allowed_oauth_providers` and has a
non-empty `oauth_client_ids[provider]`. An allowed provider without credentials is intentionally
hidden. A failed `/auth/methods/` request is a separate error, not an empty provider list.

For subdomain development origins such as `http://deliveries.localhost:8934`, the backend must
enable `OAuthRedirectPolicy(allow_localhost=True)` in development only. Production origins must
be configured explicitly. The OAuth provider must also accept the exact callback URI; allowing
an origin in this library does not register it in Google/GitHub's console.

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

### Custom OAuth transport and provider hints

The web default still builds the provider URL and assigns it to `window.location.href`. Desktop
and other hosted surfaces can replace only that transport while keeping the same buttons and
legal-action orchestration:

```tsx
<LoginForm
  methods={methods}
  oauthLegalConsent={false}
  oauthButtons={{
    autoAuthorizeProvider: providerHint,
    authorizeHandler: (provider, clientId, next, callbackPayload) =>
      nativeAuthorize({ provider, clientId, next, callbackPayload }),
  }}
/>
```

`autoAuthorizeProvider` runs at most once per mounted button group, after the requested provider
is both visible in `methods.allowed_oauth_providers` and configured with a non-empty client ID. It
also waits while the form is disabled. This supports a trusted provider hint without making an
unavailable provider start authorization.

OAuth uses the `legalConsent` gate by default, exactly as before. Set `oauthLegalConsent={false}`
only when an outer authorization flow presents and records the same documents; password login
continues to use the configured legal gate.

## Versioned legal consent

`LoginForm` and `RegisterForm` can guard password and OAuth actions with the same configurable
legal-document modal. Documents are application-owned and may come from a database; the package
only handles presentation, required/optional checkboxes, action continuation, and payload transfer
through the OAuth callback state.

```tsx
<LoginForm
  legalConsent={{
    selectAllOnFirstDocumentCheck: true,
    storage: { key: "my-product:auth-legal-consent" },
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
a different acceptance contract. Any number of required or optional legal documents is supported.

`selectAllOnFirstDocumentCheck: true` makes the first document checkbox act as a compact
select-all control: checking it selects every document and clearing it clears the selection. Leave
the option unset when each consent must be chosen independently.

Accepted `id` and `version` pairs are cached in the browser's `localStorage` by default. When every
current required document has a matching cached version, the modal is skipped and the current
documents are still included in the login, registration or OAuth payload. A new required document
or a changed required version opens the modal again; matching prior selections are restored.
Optional-document changes do not force the gate to reopen.

Use `storage: { key: "your-product:legal-consent" }` to isolate multiple policies on one origin, or
`storage: false` to disable browser persistence. The default key is
`@orcestr/auth-forms:legal-consent`. The cache is a user-experience optimization, not a legal audit
record or security boundary: the backend must continue to validate and persist accepted document
versions from the submitted payload.
