# STATUS_MODEL

Date: 2026-07-12

Status: active_v3_contract

## Назначение

Это каноническая модель состояния страниц project для семиэтапной Webpage Factory и Loop Engine. `docs/site/PAGE_QUEUE.md` хранит lifecycle; blocker, approval и growth iteration не подменяют последний успешно достигнутый статус.

## Lifecycle страницы

```text
queued
-> contract_ready
-> creative_approved
-> copy_ready
-> assets_ready | assets_not_needed
-> built
-> qa_passed
-> staging_ready
-> released
-> growth
```

| Status | Значение | Следующий штатный переход |
|---|---|---|
| `queued` | Страница поставлена в очередь | `contract_ready` |
| `contract_ready` | Проверен `PAGE_CONTRACT.md` | `creative_approved` после creative approval |
| `creative_approved` | Согласован `CREATIVE_BLUEPRINT.md` | `copy_ready` |
| `copy_ready` | Проверен финальный русский `PAGE_COPY.md` | `assets_ready` или `assets_not_needed` |
| `assets_ready` | Проверен условный `ASSET_MANIFEST.md` | `built` |
| `assets_not_needed` | Stage 4 подтвердил отсутствие отдельных ассетов | `built` |
| `built` | Проверен `BUILD_REPORT.md` | `qa_passed` |
| `qa_passed` | Проверен `QA_REPORT.md` | `staging_ready` |
| `staging_ready` | Staging evidence готов | `released` после production approval и подтверждённого production action |
| `released` | Production release подтверждён | `growth` |
| `growth` | Страница остаётся выпущенной и участвует в цикле роста | `growth` с отдельным `iteration_stage` |

## Blocker

`Blocker` — отдельное поле `PAGE_QUEUE.md`. Ошибка build, отсутствующий proof, конфликт fingerprint или ожидаемое согласование не переводят страницу в универсальный статус `blocked` и не стирают последний успешный lifecycle status.

После устранения blocker очищается, а pipeline продолжает работу с сохранённого статуса.

## Growth iteration

Для released-страницы статус `growth` сохраняет release evidence. Поле `Iteration Stage` указывает, какой этап создаёт следующую версию: `01-page-contract`, `02-creative-blueprint`, `03-conversion-copy`, `04-page-assets`, `05-full-page-build` или `06-integrated-qa-refinement`.

## Approval scopes

- `creative` разрешает переход `contract_ready -> creative_approved`.
- `production` разрешает переход `staging_ready -> released` только вместе с подтверждённым production action.
- Claims, security и staging approvals не заменяют creative или production approval.
- Approval обязан содержать `scope` и `state: approved`.

## Validation gate

Перед изменением lifecycle:

1. Owning stage создаёт или обновляет свой artifact.
2. Artifact validator подтверждает schema, stage, artifact status, язык и handoff.
3. Loop Engine проверяет допустимость lifecycle transition и approval scope.
4. Только после обеих проверок обновляются queue, task, generated status и append-only log.

Failed validation оставляет canonical state без изменений и создаёт blocker/evidence для owning stage.

## Глобальные правила

- Одновременно активна не более чем одна страница и один page stage.
- Block statuses отсутствуют в штатной модели.
- Failed build и failed CI имеют приоритет над новой работой.
- `STATUS.md` генерируется и не является источником истины.
- Production, remote Git и meaningful commits остаются отдельными approval gates.
