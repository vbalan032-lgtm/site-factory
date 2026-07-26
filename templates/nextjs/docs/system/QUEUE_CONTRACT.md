# QUEUE_CONTRACT

Date: 2026-07-12

Status: active_v3_contract

## Владельцы состояния

| Файл | Владелец | Назначение |
|---|---|---|
| `docs/site/PAGE_QUEUE.md` | Loop Engine | Единственный canonical page lifecycle state |
| `docs/system/NEXT_TASK.md` | Loop task selector | Ровно одна выбранная page-stage операция |
| `docs/system/STATUS.md` | Generated output | Русскоязычная панель владельца |
| `docs/system/LOOP_LOG.md` | Loop state updater | Краткая append-only история |
| `docs/tasks/BACKLOG.md` | Website/Growth planning | Нестраничные и ещё не поставленные в page queue задачи |
| `docs/release/PR_QUEUE.md` | PR watchdog | Состояние remote PR после отдельного разрешения |

## PAGE_QUEUE

Обязательные колонки:

```markdown
| Page ID | Route | Priority | Status | Stage | Blocker | Iteration Stage | Notes |
|---|---|---|---|---|---|---|---|
```

- `Status` использует только lifecycle из `STATUS_MODEL.md`.
- `Stage` содержит один из семи Webpage Factory stages.
- `Blocker` не заменяет lifecycle status.
- `Iteration Stage` заполняется только для growth iteration.
- Section/block statuses запрещены.

## NEXT_TASK

`NEXT_TASK.md` содержит только:

```markdown
# NEXT_TASK

- page: page-home
- stage: 02-creative-blueprint
- owner: webpage-factory/02-creative-blueprint
- approval: creative_pending
- inputs: ["docs/pages/home/PAGE_CONTRACT.md"]
- output: docs/pages/home/CREATIVE_BLUEPRINT.md
```

`inputs` — inline JSON list строк. `NEXT_TASK.md` не дублирует business context, source documents, quality checklist или объяснение selector. Эти данные находятся в page artifacts и owning skill.

## Порядок обновления

1. Прочитать `PAGE_QUEUE.md` и текущий `NEXT_TASK.md`.
2. Проверить output artifact owning stage.
3. Проверить lifecycle transition и approval scope.
4. Подготовить новые версии queue, next task и generated status во временных файлах.
5. Заменить целевые файлы только после успешной подготовки.
6. Добавить одну краткую запись в `LOOP_LOG.md`.

При любой ошибке validation canonical lifecycle остаётся прежним. Blocker записывается отдельно самым маленьким безопасным state update.

## Selection mapping

| Current status | Selected stage |
|---|---|
| `queued` | `01-page-contract` |
| `contract_ready` | `02-creative-blueprint` |
| `creative_approved` | `03-conversion-copy` |
| `copy_ready` | `04-page-assets` |
| `assets_ready`, `assets_not_needed` | `05-full-page-build` |
| `built` | `06-integrated-qa-refinement` |
| `qa_passed`, `staging_ready`, `released`, `growth` | `07-release-growth` с подходящим mode |

## Safety

- Не выбирать Webblock Factory для обычного page production.
- Не загружать всю skill family для одного stage.
- Не обновлять `STATUS.md` вручную.
- Не выполнять commit, remote Git, staging или production без соответствующего approval.
