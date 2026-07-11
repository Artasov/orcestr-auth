# Release Orcestr Auth

[Русская версия](./RELEASE.ru.md)

One `auth-vX.Y.Z` tag releases the Python package and all four npm packages. During the first
beta stage they intentionally share one version to keep the cross-package contract auditable.

## One-Time Setup

- Repository: `Artasov/orcestr-auth`.
- PyPI project: `orcestr-auth` with Trusted Publishing for `.github/workflows/release.yml`.
- npm packages: `@orcestr/auth-core`, `@orcestr/auth-react`, `@orcestr/auth-forms`,
  `@orcestr/auth-next` with npm Trusted Publishing/provenance.
- GitHub environments: `pypi` and `npm` if approval gates are required.

## Before a Release

1. Update versions in `backend/pyproject.toml` and every frontend package manifest.
2. Update inter-package exact dependencies and both lock files.
3. Update `CHANGELOG.md` and package documentation.
4. Run:

```powershell
cd backend
uv sync --frozen
uv run pytest -q
uv build

cd ..\frontend
npm ci
npm test
npm run pack:dry-run
```

5. Inspect the wheel/sdist and npm tarball lists for secrets, local paths and missing README
   files.
6. Commit the release state and create the matching tag, for example `auth-v0.1.0`.

## Workflow Order

The release workflow:

1. verifies that every package version equals the tag;
2. runs backend and frontend tests/builds;
3. builds and publishes `orcestr-auth` to PyPI;
4. publishes npm packages in dependency order: core, react, forms, next;
5. creates a GitHub Release only after both registries succeed.

Never update Orcestr production manifests to a version that is not visible in its registry.

## After Publishing

1. Verify PyPI and all four npm package pages and bilingual READMEs.
2. Pin exact versions in Orcestr manifests and regenerate locks.
3. Run `scripts/check-published-dependencies.ps1`.
4. Build production images without sibling repositories.
5. Run auth integration tests and only then deploy.
