# Site Factory

Обезличенная loop-фабрика русскоязычных сайтов под управлением Codex. Она переносит проверенный семистадийный цикл Page Factory, Website Factory, SEO, GEO, контракты артефактов, knowledge graph и Loop Engine в любой совместимый Next.js 16 проект.

Фабрика не содержит бренд, домен, продуктовые утверждения, персональные пути или секреты исходного проекта. Контекст каждого сайта задаётся в `.site-factory/project.json` и в source-of-truth документах самого сайта.

## Что входит

- 56 локальных Codex skills в двух профилях: `core` и `nextjs-ui`;
- безопасные режимы `New`, `Attach`, `Doctor`, `Update`, `ConfigureCodex`, `Pack`, `Verify`;
- хешированный `.site-factory/lock.json` и блокировка обновления при локальном drift;
- нейтральный starter: Next.js 16.2.12, React 19.2.4, TypeScript, Tailwind CSS 4, npm lockfile и Dockerfile;
- 164 regression-теста фабрики и clean-room тесты переноса;
- Windows CI и воспроизводимая ZIP-упаковка с manifest и SHA-256.

## Быстрый старт на Windows 11

Требования: Git, Python 3.12+, PowerShell 5.1+, Node.js 22 или 24, npm и установленный Codex.

Сначала выполните dry-run:

```powershell
.\bootstrap.ps1 -Mode New -Target C:\Work\new-site -ProjectId new-site -ProjectName "Новый сайт"
```

Если план корректен, примените его:

```powershell
.\bootstrap.ps1 -Mode New -Target C:\Work\new-site -ProjectId new-site -ProjectName "Новый сайт" -Apply
Set-Location C:\Work\new-site
npm ci
npm run lint
npm run typecheck
npm run build
```

Для подключения существующего репозитория используйте `Attach`. Этот режим не копирует starter и не меняет приложение или бизнес-документы:

```powershell
.\bootstrap.ps1 -Mode Attach -Target C:\Work\existing-site -ProjectId existing-site -ProjectName "Существующий сайт"
.\bootstrap.ps1 -Mode Attach -Target C:\Work\existing-site -ProjectId existing-site -ProjectName "Существующий сайт" -Apply
.\bootstrap.ps1 -Mode Doctor -Target C:\Work\existing-site
```

Полная инструкция по переносу: [docs/TRANSFER_WINDOWS.md](docs/TRANSFER_WINDOWS.md). Архитектура и правила развития: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Профили

- `core`: Website Factory, Webpage Factory, SEO, GEO, Loop Engine, контракты и knowledge graph.
- `nextjs-ui`: shadcn, UI/UX проверки, React/Next best practices, canvas и внутренний `design-taste-frontend`.

Оба профиля ставятся по умолчанию. Минимальная установка:

```powershell
.\bootstrap.ps1 -Mode New -Target C:\Work\new-site -ProjectId new-site -ProjectName "Новый сайт" -Profile core -Apply
```

## Безопасность

Dry-run является поведением по умолчанию. `Attach` останавливается при коллизии factory-owned файлов. `Update` останавливается при drift и не меняет project-owned файлы. `ConfigureCodex` создаёт только пример внутри проекта и не редактирует пользовательский профиль Codex. Commit, push, release, staging и production не выполняются bootstrap-скриптом.
