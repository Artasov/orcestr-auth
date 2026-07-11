<p align="right"><strong>English</strong> · <a href="./README.ru.md">Русский</a></p>

<p align="center"><a href="https://orcestr.com"><img src="../assets/orcestr-banner.webp" alt="Orcestr banner" width="100%" /></a></p>

# Orcestr Auth frontend workspace

The frontend workspace builds four independently publishable packages around one browser auth
contract.

| Package | Layer |
| --- | --- |
| [`@orcestr/auth-core`](./packages/core/README.md) | framework-independent client, redirects and OAuth |
| [`@orcestr/auth-react`](./packages/react/README.md) | React Query provider and hooks |
| [`@orcestr/auth-forms`](./packages/forms/README.md) | ready localized `@orcestr/ui` forms |
| [`@orcestr/auth-next`](./packages/next/README.md) | Next.js request/proxy helpers |

## Development

```bash
npm ci
npm run typecheck
npm test
npm run pack:dry-run
```

The TypeScript project references enforce package order. Published inter-package dependencies
use exact versions; React, React Query, Next.js and `@orcestr/ui` remain peer dependencies where
the consumer must own a single runtime instance.
