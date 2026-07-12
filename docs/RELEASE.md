# Releasing Orcestr Auth

[Русская версия](./RELEASE.ru.md)

Every package has an independent version and release tag. Updating one package never republishes
the other packages.

The root `scripts/release.mjs` helper and the shared PyCharm configurations in `.run` automate
version bumps, lock-file updates, release commits and package-specific tags. They create the
commit and tag locally by default; publishing still requires an explicit push.

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

4. From the repository root, create the release commit and tag with the helper (or run the
   matching `release Python patch/minor/major` PyCharm configuration):

```powershell
node scripts/release.mjs python patch
git push origin main
git push origin python-v0.1.1
```

The Python workflow verifies only the backend version, publishes through PyPI OIDC and creates a
package-specific GitHub Release.

If the tag already exists but its push event was missed, open **Actions → Publish Python package
→ Run workflow** and enter the version without the prefix, for example `0.1.1`. The workflow
checks out the existing `python-v0.1.1` tag before publishing.

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

5. From the repository root, create the release commit and tag with the helper (or use the
   matching PyCharm configuration). For example, a React patch release is:

```powershell
node scripts/release.mjs react patch
git push origin main
git push origin auth-react-v0.1.1
```

Available targets are `python`, `core`, `react`, `forms` and `next`; release parts are `patch`,
`minor` and `major`. Add `--dry-run` to preview or `--push` to create and immediately push the
release. The non-dry-run command intentionally refuses to work with a dirty Git worktree.

Push release tags one at a time. Do not use `git push --tags` for a batch of releases: GitHub does
not create tag push events when more than three tags are pushed together. The helper's `--push`
mode always pushes only its own tag.

The npm workflow resolves exactly one package from the tag, checks that package's version, tests
the workspace, publishes only the selected workspace with provenance, and creates a
package-specific GitHub Release.

If a tag already exists but its push event was missed, open **Actions → Publish npm package → Run
workflow**, choose the package and enter the version without the tag prefix. The workflow checks
out that existing package tag before publishing.

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
