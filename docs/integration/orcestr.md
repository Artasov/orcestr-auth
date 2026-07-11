# Orcestr integration

[Русская версия](./orcestr.ru.md)

The main Orcestr repository is the reference consumer for every backend and frontend package.

## Local Development

Build frontend packages, then install all sibling libraries atomically:

```powershell
cd C:\main\dev\orcestr-auth\frontend
npm run build

cd C:\main\dev\orcestr\frontend
npm run libs:local
```

Install the Python package editable without changing project metadata:

```powershell
cd C:\main\dev\orcestr\backend
uv run --no-sync python scripts/use_local_orcestr_auth.py --local
```

`frontend` refreshes only the five known Orcestr packages in `node_modules`, which prevents npm
from retaining stale `file:` packages with the same development version. Neither installer
modifies tracked manifests or lock files.

## Published Mode

Orcestr pins exact versions of `orcestr-auth`, all four npm auth packages and `@orcestr/ui`.
Production uses `uv sync --frozen` and `npm ci`; Docker build contexts never require sibling
repositories.

Before production build:

```powershell
cd C:\main\dev\orcestr
.\scripts\check-published-dependencies.ps1
```

This guard rejects `file:`, `link:`, editable and local development paths in manifests/locks.

## Reference Boundaries

Orcestr keeps `UserORM`, legal acceptance, tenant bootstrap, country policy, audit/rate limits,
email delivery, application pages and surface-aware redirects. Shared mechanics are imported
from the auth packages and are not duplicated locally.
