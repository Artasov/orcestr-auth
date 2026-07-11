# Contributing

[Русская версия](./CONTRIBUTING.ru.md)

Orcestr Auth is a public authentication foundation extracted from real Orcestr product work.
Changes must keep security boundaries explicit and remain usable outside the main application.

## Development

Backend checks:

```bash
cd backend
uv sync --frozen
uv run pytest -q
uv build
```

Frontend checks:

```bash
cd frontend
npm ci
npm test
npm run pack:dry-run
```

## Change Checklist

Describe in the pull request:

- which public package and contract changed;
- browser-cookie and bearer-flow impact;
- session, token, redirect, OAuth or CSRF implications;
- schema/migration impact and compatibility with application-owned users;
- English and Russian documentation or form-copy updates;
- how the change was tested in a consumer application.

Do not edit generated `dist/` output by hand. Never commit credentials, raw tokens, local
package paths or production user data.
