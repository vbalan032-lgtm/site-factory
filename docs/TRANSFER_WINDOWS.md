# Перенос Site Factory на другой Windows ПК

## 1. Подготовить компьютер

Установите:

- Windows 11 и PowerShell 5.1 или новее;
- Git;
- Python 3.12+ с доступной командой `py -3` или `python`;
- Node.js 22 LTS либо 24 и npm;
- Codex CLI, IDE extension или приложение, которое поддерживает project skills в `.agents/skills`;
- Docker Desktop только если нужен контейнерный smoke/build.

Не переносите папки пользовательского профиля Codex, OAuth-файлы, `.env`, SSH-ключи и токены. На втором ПК авторизация выполняется отдельно средствами Codex, GitHub и ОС.

## 2. Получить фабрику

Предпочтительный путь: клонировать приватный репозиторий и checkout нужного release tag. Альтернатива: передать три release-файла `site-factory-v1.0.0.zip`, `site-factory-v1.0.0.zip.sha256` и `site-factory-v1.0.0.manifest.json` через доверенный канал.

Проверьте архив до распаковки:

```powershell
$Expected = (Get-Content .\site-factory-v1.0.0.zip.sha256).Split()[0]
$Actual = (Get-FileHash .\site-factory-v1.0.0.zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Actual -ne $Expected) { throw "Checksum mismatch" }
Expand-Archive .\site-factory-v1.0.0.zip -DestinationPath C:\Tools -Force
Set-Location C:\Tools\site-factory
python -m factory.bootstrap verify --archive ..\..\site-factory-v1.0.0.zip --checksum ..\..\site-factory-v1.0.0.zip.sha256 --manifest ..\..\site-factory-v1.0.0.manifest.json
```

## 3A. Создать новый сайт

```powershell
.\bootstrap.ps1 -Mode New -Target C:\Work\my-site -ProjectId my-site -ProjectName "Название проекта"
.\bootstrap.ps1 -Mode New -Target C:\Work\my-site -ProjectId my-site -ProjectName "Название проекта" -Apply
.\bootstrap.ps1 -Mode Doctor -Target C:\Work\my-site
```

Bootstrap уже синхронизирует `project_id` в project config, graph profile, project knowledge seed, `package.json` и lockfile. Затем заполните source-of-truth документы, начиная с `docs/source-index`, и при необходимости измените mapping путей в `.site-factory/project.json`.

## 3B. Подключить существующий сайт

Сначала убедитесь, что target находится под Git и рабочие изменения сохранены понятным способом. `Attach` не создаёт backup всего репозитория и не заменяет контроль версий.

```powershell
.\bootstrap.ps1 -Mode Attach -Target C:\Work\existing-site -ProjectId existing-site -ProjectName "Название проекта"
.\bootstrap.ps1 -Mode Attach -Target C:\Work\existing-site -ProjectId existing-site -ProjectName "Название проекта" -Apply
```

После Attach сопоставьте существующие source-of-truth и lifecycle paths в `.site-factory/project.json`. Затем выполните Doctor. Если target уже содержит файл с тем же путём, что factory skill, Attach остановится и ничего не перезапишет.

## 4. Подготовить Codex

```powershell
.\bootstrap.ps1 -Mode ConfigureCodex -Target C:\Work\my-site
.\bootstrap.ps1 -Mode ConfigureCodex -Target C:\Work\my-site -Apply
```

Команда пишет только безопасный справочный `.site-factory/codex-config.example.toml` без активных настроек. Она не меняет глобальную конфигурацию. Сверьте [CODEX_SETUP_WINDOWS.md](CODEX_SETUP_WINDOWS.md), отдельно авторизуйте нужные интеграции и откройте Codex из корня целевого проекта, чтобы `.agents/skills` были обнаружены.

## 5. Установить зависимости и проверить starter

```powershell
Set-Location C:\Work\my-site
npm ci
npm run lint
npm run typecheck
npm run build
```

Для Attach используйте команды качества самого проекта. Не заменяйте его package manager или lockfile командами фабрики.

## 6. Обновлять фабрику

Checkout или распакуйте новую release-версию, затем:

```powershell
.\bootstrap.ps1 -Mode Update -Target C:\Work\my-site
.\bootstrap.ps1 -Mode Update -Target C:\Work\my-site -Apply
.\bootstrap.ps1 -Mode Doctor -Target C:\Work\my-site
```

Если Update сообщает drift, не удаляйте lock и не применяйте force. Сохраните diff изменённого skill, решите, переносить ли локальное изменение в саму фабрику, и только затем восстановите чистый snapshot или выпустите новую версию.

## 7. Что передавать коллеге

- URL приватного репозитория или три проверенных release-файла;
- версию/tag фабрики;
- эту инструкцию;
- доступ к репозиторию конкретного сайта;
- отдельно, через secret store, необходимые учетные данные.

Не передавайте `node_modules`, `.next`, `.git` из чужого проекта, пользовательскую папку Codex, MCP credentials, `.env` или историю команд с токенами.
