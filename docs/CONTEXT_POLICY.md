# Context Economy Policy

Эта политика ограничивает объём контекста, который загружается на одном factory stage. Она дополняет graph-first routing и не заменяет канонические project knowledge files.

## Бюджеты

- tiny operation: 800–1 200 токенов контекста;
- normal page/content stage: 1 500–2 500;
- QA, legal, pricing, claims или proof review: 2 500–4 000;
- full cross-cutting audit: только по явному запросу.

## Порядок загрузки

1. Прочитать `.site-factory/project.json`.
2. Получить compact graph-first context pack для `project`, `route`, `stage` и `lifecycle`.
3. Использовать source-index и distilled knowledge раньше raw sources.
4. Открывать raw sources только для точных claims, proof, pricing, legal, дат, customer names, конфликтов или полного аудита.
5. Применить allowlist текущего stage, provenance, relevance, deduplication и token budget.
6. Зафиксировать использованные источники, assumptions, gaps и approval gates в handoff.

## Fallback

Если Graphify недоступен, используется filesystem fallback по тем же stage allowlists и ограничениям. Отсутствие графа не даёт права расширять claims, одобрять creative, выполнять Git, staging или production.

## Stage allowlists

- Strategy: master context, brand, product, business architecture, personas, sitemap и source-index.
- Copy: strategy allowlist, brand, forbidden phrases, claims/proofs и relevant page brief.
- SEO/GEO: approved copy, SEO/GEO maps и точные proof slices.
- Visual: brand, approved blueprint, asset manifest и rights notes.
- Frontend: approved contract/copy/assets, touched code и technical docs.
- QA: changed artifacts, checklists, exact disputed evidence и release gate.
