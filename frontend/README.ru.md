<p align="right"><a href="./README.md">English</a> · <strong>Русский</strong></p>

<p align="center"><a href="https://orcestr.com"><img src="../assets/orcestr-banner.webp" alt="Баннер Orcestr" width="100%" /></a></p>

# Frontend workspace Orcestr Auth

Frontend workspace собирает четыре независимо публикуемых пакета вокруг одного browser auth
контракта.

| Пакет | Слой |
| --- | --- |
| [`@orcestr/auth-core`](./packages/core/README.ru.md) | framework-independent client, redirects и OAuth |
| [`@orcestr/auth-react`](./packages/react/README.ru.md) | React Query provider и hooks |
| [`@orcestr/auth-forms`](./packages/forms/README.ru.md) | готовые локализованные формы на `@orcestr/ui` |
| [`@orcestr/auth-next`](./packages/next/README.ru.md) | Next.js request/proxy helpers |

## Разработка

```bash
npm ci
npm run typecheck
npm test
npm run pack:dry-run
```

TypeScript project references фиксируют порядок packages. Published inter-package dependencies
используют точные версии; React, React Query, Next.js и `@orcestr/ui` остаются peer dependencies,
чтобы consumer владел единственным runtime instance.
