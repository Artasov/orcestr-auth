# Релизы Orcestr Auth

[English version](./RELEASE.md)

Каждый пакет имеет независимую версию и отдельный релизный тег. Обновление одного пакета не
переиздаёт остальные пакеты.

Корневой helper `scripts/release.mjs` и общие конфигурации PyCharm в `.run` автоматизируют
изменение версии, обновление lock-файла, релизный commit и отдельный тег пакета. По умолчанию они
создают commit и тег только локально; для публикации всё равно требуется явный push.

| Пакет | Тег | Workflow |
| --- | --- | --- |
| `orcestr-auth` | `python-vX.Y.Z` | `.github/workflows/release.yml` |
| `@orcestr/auth-core` | `auth-core-vX.Y.Z` | `.github/workflows/npm-release.yml` |
| `@orcestr/auth-react` | `auth-react-vX.Y.Z` | `.github/workflows/npm-release.yml` |
| `@orcestr/auth-forms` | `auth-forms-vX.Y.Z` | `.github/workflows/npm-release.yml` |
| `@orcestr/auth-next` | `auth-next-vX.Y.Z` | `.github/workflows/npm-release.yml` |

## Однократная настройка

- Репозиторий: `Artasov/orcestr-auth`.
- PyPI Pending или обычный Trusted Publisher:
  - owner: `Artasov`;
  - repository: `orcestr-auth`;
  - workflow: `release.yml`;
  - environment: `pypi`.
- npm Trusted Publisher для каждого npm-пакета:
  - organization/user: `Artasov`;
  - repository: `orcestr-auth`;
  - workflow: `npm-release.yml`;
  - environment: `npm`.
- GitHub environments: `pypi` и `npm`.

npm разрешает настроить Trusted Publishing только после появления пакета. Поэтому каждый
npm-пакет первый раз публикуется вручную, после чего для него настраивается publisher. Python-пакет
может быть создан первым запуском workflow через Pending Trusted Publisher в PyPI.

## Релиз Python-пакета

1. Обновите только `backend/pyproject.toml` и при необходимости `backend/uv.lock`.
2. Обновите `CHANGELOG.md` и документацию backend.
3. Проверьте пакет локально:

```powershell
cd backend
uv sync --frozen
uv run pytest -q
uv build --no-sources
```

4. Из корня репозитория создайте релизный commit и тег helper-командой (либо запустите
   соответствующую конфигурацию PyCharm `release Python patch/minor/major`):

```powershell
node scripts/release.mjs python patch
git push origin main
git push origin python-v0.1.1
```

Python workflow проверяет только версию backend, публикует пакет через PyPI OIDC и создаёт
отдельный GitHub Release.

Если тег уже существует, но его push event был пропущен, откройте **Actions → Publish Python
package → Run workflow** и укажите версию без префикса, например `0.1.1`. Перед публикацией
workflow извлечёт содержимое существующего тега `python-v0.1.1`.

## Релиз npm-пакета

1. Обновите `version` только у выпускаемого пакета.
2. Если изменились его внутренние зависимости, обновите их точные версии и выполните
   `npm install`, чтобы пересобрать `frontend/package-lock.json`.
3. Обновите `CHANGELOG.md` и документацию пакета.
4. Проверьте frontend локально:

```powershell
cd frontend
npm ci
npm test
npm run pack:dry-run
```

5. Из корня репозитория создайте релизный commit и тег helper-командой (либо используйте
   соответствующую конфигурацию PyCharm). Например, patch-релиз React-пакета:

```powershell
node scripts/release.mjs react patch
git push origin main
git push origin auth-react-v0.1.1
```

Доступные цели: `python`, `core`, `react`, `forms` и `next`; типы релиза: `patch`, `minor` и
`major`. Флаг `--dry-run` показывает результат без изменений, а `--push` сразу отправляет созданный
релиз. Команда без `--dry-run` намеренно отказывается работать при грязном Git worktree.

Отправляйте релизные теги по одному. Не используйте `git push --tags` для пачки релизов: GitHub не
создаёт tag push events, если одновременно отправлено больше трёх тегов. Режим helper-команды
`--push` всегда отправляет только собственный тег.

npm workflow определяет по тегу ровно один пакет, проверяет его версию, тестирует workspace,
публикует только выбранный пакет с provenance и создаёт отдельный GitHub Release.

Если тег уже существует, но его push event был пропущен, откройте **Actions → Publish npm package
→ Run workflow**, выберите пакет и укажите версию без префикса тега. Перед публикацией workflow
извлечёт содержимое существующего тега выбранного пакета.

Внутренние зависимости намеренно зафиксированы точными версиями. Новая версия core не требует
релиза React, forms или Next.js, пока им не понадобились изменения из новой версии core.

## Первая публикация npm

Авторизуйтесь и опубликуйте пакеты из `frontend` в порядке зависимостей:

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

Когда все четыре пакета появились в npm, настройте Trusted Publishing для каждого из них. Не
отправляйте четыре релизных тега версии `0.1.0` после ручной публикации: версии npm неизменяемы, и
workflow попытается опубликовать их повторно. Автоматические релизы по тегам начинаются со
следующей версии.

## После публикации

1. Проверьте страницу в registry и двуязычный README выпущенного пакета.
2. Зафиксируйте его точную версию в manifests Orcestr и пересоберите нужный lock-файл.
3. Запустите `scripts/check-published-dependencies.ps1`.
4. Соберите затронутый production image без соседних репозиториев.
5. Перед деплоем запустите относящиеся к изменению auth integration tests.

Нельзя обновлять production manifests Orcestr до версии, которой ещё нет в registry.
