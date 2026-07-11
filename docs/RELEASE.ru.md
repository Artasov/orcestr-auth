# Релиз Orcestr Auth

[English version](./RELEASE.md)

Один тег `auth-vX.Y.Z` выпускает Python-пакет и четыре npm-пакета. На первом beta-этапе они
намеренно используют одну версию, чтобы общий контракт было легко проверять.

## Однократная настройка

- Репозиторий: `Artasov/orcestr-auth`.
- PyPI project: `orcestr-auth` с Trusted Publishing для `.github/workflows/release.yml`.
- npm packages: `@orcestr/auth-core`, `@orcestr/auth-react`, `@orcestr/auth-forms`,
  `@orcestr/auth-next` с npm Trusted Publishing/provenance.
- GitHub environments: `pypi` и `npm`, если нужны approval gates.

## Перед релизом

1. Обновите версии в `backend/pyproject.toml` и каждом frontend package manifest.
2. Обновите точные inter-package dependencies и оба lock-файла.
3. Обновите `CHANGELOG.md` и package documentation.
4. Запустите:

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

5. Проверьте wheel/sdist и списки npm tarball: там не должно быть secrets, локальных paths или
   пропущенных README.
6. Закоммитьте release state и создайте совпадающий тег, например `auth-v0.1.0`.

## Порядок workflow

Release workflow:

1. проверяет совпадение версии каждого package с тегом;
2. запускает backend и frontend tests/builds;
3. собирает и публикует `orcestr-auth` в PyPI;
4. публикует npm packages в порядке зависимостей: core, react, forms, next;
5. создаёт GitHub Release только после успеха обоих registries.

Нельзя обновлять production manifests Orcestr до версии, которой ещё нет в registry.

## После публикации

1. Проверьте PyPI, четыре npm package pages и двуязычные README.
2. Зафиксируйте точные версии в manifests Orcestr и пересоберите locks.
3. Запустите `scripts/check-published-dependencies.ps1`.
4. Соберите production images без sibling repositories.
5. Запустите auth integration tests и только после этого deploy.
