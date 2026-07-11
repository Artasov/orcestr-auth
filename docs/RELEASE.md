# Releasing Orcestr Auth

[Русская версия](./RELEASE.ru.md)

Every package has an independent version and release tag. Updating one package never republishes
the other packages.

| Package | Tag | Workflow |
| --- | --- | --- |
| `orcestr-auth` | `python-vX.Y.Z` | `.github/workflows/release.yml` |
| `@orcestr/auth-core` | `auth-core-vX.Y.Z` | `.github/workflows/npm-release.yml` |
| `@orcestr/auth-react` | `auth-react-vX.Y.Z` | `.github/workflows/npm-release.yml` |
| `@orcestr/auth-forms` | `auth-forms-vX.Y.Z` | `.github/workflows/npm-release.yml` |
| `@orcestr/auth-next` | `auth-next-vX.Y.Z` | `.github/workflows/npm-release.yml` |

## One-Time Setup

- Repository: `Artasov/orcestr-auth`.
- PyPI Pending or existing Trusted Publisher:
  - owner: `Artasov`;
  - repository: `orcestr-auth`;
  - workflow: `release.yml`;
  - environment: `pypi`.
- npm Trusted Publisher for each npm package:
  - organization/user: `Artasov`;
  - repository: `orcestr-auth`;
  - workflow: `npm-release.yml`;
  - environment: `npm`.
- GitHub environments: `pypi` and `npm`.

npm Trusted Publishing can only be configured after a package exists. Publish each npm package
manually once, then configure the publisher above. The Python package can be created by PyPI's
Pending Trusted Publisher during its first workflow run.

## Python Release

1. Update only `backend/pyproject.toml` and `backend/uv.lock` when required.
2. Update `CHANGELOG.md` and backend documentation.
3. Verify locally:

```powershell
cd backend
uv sync --frozen
uv run pytest -q
uv build --no-sources
```

4. Commit the release state and push a matching tag:

```powershell
git tag -a python-v0.1.0 -m "orcestr-auth 0.1.0"
git push origin main
git push origin python-v0.1.0
```

The Python workflow verifies only the backend version, publishes through PyPI OIDC and creates a
package-specific GitHub Release.

## npm Package Release

1. Update the `version` of only the package being released.
2. If its internal dependencies changed, update their exact versions and run `npm install` to
   regenerate `frontend/package-lock.json`.
3. Update `CHANGELOG.md` and the package documentation.
4. Verify locally:

```powershell
cd frontend
npm ci
npm test
npm run pack:dry-run
```

5. Commit and push the tag belonging to that package. For example, a React package release is:

```powershell
git tag -a auth-react-v0.1.1 -m "@orcestr/auth-react 0.1.1"
git push origin main
git push origin auth-react-v0.1.1
```

The npm workflow resolves exactly one package from the tag, checks that package's version, tests
the workspace, publishes only the selected workspace with provenance, and creates a
package-specific GitHub Release.

Internal dependencies remain exact by design. A new core version does not force releases of
React, forms or Next.js unless they need to consume that core version.

## Initial npm Publication

From `frontend`, authenticate and publish in dependency order:

```powershell
npm login
npm whoami
npm ci
npm test
npm publish --workspace @orcestr/auth-core --access public
npm publish --workspace @orcestr/auth-react --access public
npm publish --workspace @orcestr/auth-forms --access public
npm publish --workspace @orcestr/auth-next --access public
```

After all four packages exist, configure npm Trusted Publishing for each package. Do not push the
four `0.1.0` release tags after manual publication because npm versions are immutable and the
workflow would attempt to publish them again. Automated tag releases start with the next version.

## After Publishing

1. Verify the registry page and bilingual README for the package that was released.
2. Pin its exact version in Orcestr manifests and regenerate the relevant lock file.
3. Run `scripts/check-published-dependencies.ps1`.
4. Build the affected production image without sibling repositories.
5. Run the relevant auth integration tests before deployment.

Never update Orcestr production manifests to a version that is not visible in its registry.
