# Application integration

[Русская версия](./application.ru.md)

This guide describes the boundary between Orcestr Auth packages and any
application that consumes them. It intentionally uses neutral routes, domains
and storage names.

## Frontend packages

Install only the layers the application needs:

```bash
npm install @orcestr/auth-core @orcestr/auth-react
npm install @orcestr/auth-forms @orcestr/auth-next
```

- `@orcestr/auth-core` owns the transport-independent client and auth contracts.
- `@orcestr/auth-react` owns session state and React hooks.
- `@orcestr/auth-forms` provides optional ready-made forms.
- `@orcestr/auth-next` provides Next.js request and redirect helpers.

The application owns pages, route names, branding, tenant bootstrap and the
destination after authentication.

```tsx
<AuthProvider client={authClient}>
    <LoginForm onSuccess={() => router.replace('/dashboard')} />
</AuthProvider>
```

## Backend package

```bash
pip install orcestr-auth
```

The application supplies database sessions, persistence adapters, OAuth
credentials, email delivery and product policy. The package supplies auth use
cases, stable error codes, FastAPI integration and security-sensitive flow
mechanics.

Mount routes under an application-owned prefix:

```python
app.include_router(auth_router, prefix="/api/auth")
```

## Local package testing

Test unpublished frontend packages through generated npm tarballs and the
Python package through an editable installation in a development environment.
Do not commit local `file:`, `link:` or editable paths to consumer manifests or
lock files.

Production builds should pin published versions and install from registries
with locked dependencies.

## Responsibility boundary

Auth packages do not own application permissions, billing, business roles,
legal-document policy, product analytics, pages or navigation. Consumer code
must compose those concerns around the auth contracts rather than adding them
to the library.
