# Архитектура Site Factory

## Граница продукта

Репозиторий фабрики владеет skills, runtime-контрактами, starter-шаблоном, bootstrap, тестами и release-упаковкой. Целевой сайт владеет приложением, брендом, продуктами, фактами, claims, персонами, sitemap, контентом, инфраструктурой и секретами.

## Конфигурация проекта

`.site-factory/project.json` хранит стабильный `project_id`, публичный язык, разрешённые латинские термины, технический профиль и все канонические пути. Runtime не должен выводить идентичность проекта из имени каталога или Git remote.

`.site-factory/lock.json` создаётся bootstrap-скриптом. Он фиксирует версию фабрики, выбранные профили, factory-owned roots и SHA-256 каждого установленного файла.

Для нового проекта используется `New`, для существующего проекта — `Attach` или `Adopt`, а для уже установленного вручную factory snapshot — `Register`. `Register` проверяет конфигурацию и записывает lock, не копируя starter и не перезаписывая приложение.

Поддерживаются технические профили `nextjs-16` и `static-html`. Static profile меняет маршрутизацию skills и quality checks; он не превращает generic factory в проектный starter.

## Жизненный цикл

1. Page Contract.
2. Creative Blueprint.
3. Conversion Copy.
4. Page Assets или явное `assets_not_needed`.
5. Full Page Build.
6. Integrated QA and Refinement.
7. Release and Growth с отдельными approval gates.

`PAGE_QUEUE.md` остаётся каноническим состоянием страниц. `NEXT_TASK.md` содержит ровно одну операцию. `STATUS.md` является производным русскоязычным отчётом, а `LOOP_LOG.md` хранит append-only историю.

## Владение файлами

- Factory-owned: только paths выбранных профилей в `.agents/skills`, перечисленные в lock.
- Project-owned: `.site-factory/project.json`, приложение, business/source documents, page artifacts, lifecycle state, CI/deploy настройки целевого проекта.
- Release-owned: ZIP, внешний manifest и checksum; они генерируются заново и не коммитятся.

## Обновление

`Update` сначала сверяет каждый установленный хеш и проверяет новые release-файлы на коллизии. Изменённый или удалённый factory-owned файл считается drift и блокирует обновление. Перед изменением создаётся ZIP-backup прежнего snapshot; при ошибке копирования старые файлы и lock восстанавливаются. При чистом snapshot обновляются только выбранные профили; project config и project-owned файлы не затрагиваются.

Context loading работает graph-first с stage-specific budget и allowlist. При недоступности Graphify применяется filesystem fallback; fallback не расширяет права на claims, approvals, Git, staging или production. Подробные правила находятся в `docs/CONTEXT_POLICY.md`, quality gates — в `docs/QUALITY_GATES.md`.

## Упаковка и релиз

`Pack` работает в dry-run без `-Apply`. Release ZIP строится только из явного allowlist репозитория, исключает secret-like файлы, backups и generated output и отказывается паковать символические ссылки. `Verify` требует точного совпадения checksum, имени/версии, внешнего и встроенного manifest и полного набора ZIP entries.

GitHub Release не запускается от push тега. Сначала человек отдельно создаёт и отправляет одобренный tag, затем вручную запускает workflow `Release` с тем же tag. Job использует GitHub Environment `release`; после создания приватного репозитория для этого Environment необходимо включить required reviewer. Workflow дополнительно сверяет tag с `factory_version`.

## Версионирование

Фабрика следует SemVer. Изменение схемы, lifecycle-контрактов или несовместимое поведение требует major-версии. Новые обратно совместимые skills и режимы требуют minor-версии. Исправления без изменения контракта требуют patch-версии.
