# Контракт графа знаний

Каноническими остаются файлы проекта. Graphify — производный, пересобираемый индекс для поиска связей и сокращения загружаемого контекста.

- Каждый профиль и запрос изолирован по `project_id`.
- Узел хранит путь, fingerprint, provenance и evidence path; устаревший результат исключается.
- `EXTRACTED` имеет приоритет над `INFERRED`; `AMBIGUOUS` не входит в обычный контекст.
- Claim, Approval, конфликт, изменившийся fingerprint и release evidence требуют чтения точного файла.
- Недоступный, повреждённый или устаревший граф включает stage allowlist fallback и не меняет lifecycle страницы.
- Секреты, dependencies, generated output, rollback archive и migration archive не индексируются.
- Граф не разрешает claims, creative approval, Git, staging или production.
- Замена базы выполняется новым provider adapter без изменения семи page stages.

Перед extraction профиль материализуется в `graphify-out/.corpus`: туда копируются только разрешённые corpus roots после exclusions. Graphify не сканирует исходный repository root. Raw node-link output нормализуется по реальной схеме Graphify (`source_file`, `file_type`, `links`), фильтруется по corpus manifest и атомарно объединяется с deterministic factory catalog. Публикация сохраняет предыдущий здоровый граф при пустом, повреждённом или неожиданно уменьшившемся результате.

Локальный privacy-preserving режим использует Graphify `code-only` для AST и проверяемый `PROJECT_KNOWLEDGE.json` для ключевой бизнес-семантики. Seed-файл не становится источником истины: каждый узел обязан ссылаться на существующий канонический файл, его fingerprint и конкретный раздел. Для другого бизнеса заменяются профиль и seed-данные, а provider и семь page stages остаются прежними. Внешний LLM backend разрешается только отдельным решением владельца.

Stage budget ограничивает graph summaries и прямые provider queries. Точное чтение safety-critical файла может превысить мягкий бюджет; router фиксирует это как fallback reason. Sensitive result вне stage allowlist не используется как summary.

Профиль проекта: `docs/system/knowledge-graph/GRAPH_PROFILE.json`. Generated `graphify-out/` не коммитится без отдельного решения владельца.
