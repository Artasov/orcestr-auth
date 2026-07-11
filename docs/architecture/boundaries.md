# Architecture boundaries

[Русская версия](./boundaries.ru.md)

## Repository Shape

Orcestr Auth is one monorepository because its Python and frontend packages implement one HTTP
and security contract and must be verified together. Each artifact is still independently
installable and has its own package README.

## Ownership

The consumer application owns:

- its user table and product profile fields;
- pages, route registry, branding and metadata;
- legal acceptance, tenant/workspace bootstrap and memberships;
- permissions, product navigation, audit storage and email delivery.

Orcestr Auth owns:

- password hashing and token validation;
- browser cookies, CSRF policy and bearer flow;
- server sessions and refresh rotation/replay handling;
- recovery codes, OAuth exchange and WebSocket tickets;
- auth-table definitions and standard SQLAlchemy/FastAPI adapters;
- browser client, React hooks, forms and Next.js guards.

## User Model

The application passes its SQLAlchemy registry, `UserORM` and a `UserFieldMap`. The library
creates auth models in the same metadata and real foreign keys to the actual primary key.
`SqlAlchemyUserRepository` then issues direct queries against mapped columns.

Repository protocols remain internal extension points for unusual consumers. A normal
application does not implement repository boilerplate or expose its entire domain model.

## Product Hooks

`AuthHttpApplication` is the explicit boundary for registration, login policy, legal
acceptance, tenant bootstrap, audit, rate limits and email delivery. The reusable router owns
the endpoint matrix and safe browser/token response behavior.

## Frontend Layers

```text
@orcestr/auth-core -> @orcestr/auth-react -> @orcestr/auth-forms -> @orcestr/ui
                  \-> @orcestr/auth-next
```

`auth-core` is framework-independent. React and Next.js adapters depend on it, but not on each
other. Forms use the headless React hooks and UI kit. Forms never own pages. Consumers compose
simple pages from semantic HTML and existing UI primitives; route files stay in the application.
