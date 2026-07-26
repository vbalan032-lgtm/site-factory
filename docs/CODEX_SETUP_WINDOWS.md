# Codex setup для Site Factory

## Обязательный минимум

- Codex с поддержкой project-local `.agents/skills`.
- Доступ Codex к корню целевого Git-репозитория.
- Superpowers skills для planning, TDD, debugging, review и verification: они являются внешней зависимостью runtime и устанавливаются штатным способом в пользовательский профиль Codex, а не копируются из чужого профиля.

## Интеграции полного цикла

- Context7: актуальная документация библиотек, когда локальной документации недостаточно.
- Playwright: Stage 6 browser/SSR/accessibility evidence и разрешённый staging smoke.
- GitHub: remote repository, pull requests, Actions и releases; токен только из OS environment или secret store.
- Graphify 0.9.13: необязательный graph provider; при недоступности действует проверяемый filesystem fallback.
- Image generation: только для явно требуемых растровых assets и с проверкой прав/brand fit.

`factory/codex-requirements.json` является машинно-читаемым перечнем. Bootstrap не устанавливает плагины и не копирует credentials, потому что источники, команды установки и политика авторизации зависят от актуальной сборки Codex.

## Проверка обнаружения

1. Откройте Codex из корня target.
2. Убедитесь, что доступны `context-pack-loader`, `01-page-contract`, `loop-daily-runner` и skills выбранного optional-профиля.
3. Попросите Codex прочитать `.site-factory/project.json` и выполнить read-only `Doctor`.
4. Не начинайте страницу, пока source-of-truth paths не заполнены и Doctor не объяснён.

