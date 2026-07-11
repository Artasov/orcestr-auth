# Подключение к Orcestr

[English version](./orcestr.md)

Основной репозиторий Orcestr является reference consumer для всех backend- и frontend-пакетов.

## Локальная разработка

Соберите frontend-пакеты и атомарно установите все sibling libraries:

```powershell
cd C:\main\dev\orcestr-auth\frontend
npm run build

cd C:\main\dev\orcestr\frontend
npm run libs:local
```

Подключите Python-пакет editable без изменения project metadata:

```powershell
cd C:\main\dev\orcestr\backend
uv run --no-sync python scripts/use_local_orcestr_auth.py --local
```

Frontend обновляет только пять известных Orcestr packages в `node_modules`, поэтому npm не
оставляет устаревший `file:` package с той же dev-версией. Installers не меняют tracked
manifests и lock-файлы.

## Published mode

Orcestr фиксирует точные версии `orcestr-auth`, четырёх npm auth packages и `@orcestr/ui`.
Production использует `uv sync --frozen` и `npm ci`; Docker build context не зависит от sibling
repositories.

Перед production build:

```powershell
cd C:\main\dev\orcestr
.\scripts\check-published-dependencies.ps1
```

Guard отклоняет `file:`, `link:`, editable и локальные development paths в manifests/locks.

## Границы reference consumer

В Orcestr остаются `UserORM`, legal acceptance, tenant bootstrap, country policy, audit/rate
limits, email delivery, application pages и surface-aware redirects. Общая механика
импортируется из auth packages и не дублируется локально.
