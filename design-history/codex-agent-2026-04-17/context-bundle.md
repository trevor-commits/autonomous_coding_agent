# Контекстный bundle

Открывай этот файл только если `phase-card.md` и `ultra-context.md` уже не дают ответа на текущий шаг.

## Проект

- Цель: Build a narrow, reliable autonomous coding harness for this repository that accepts a coding objective or eligible Linear issue, executes bounded implementation work through a deterministic Python supervisor, verifies results locally including UI checks, and produces readiness evidence.
- Язык контента: `en`
- Архетип: `automation-script`
- Capabilities: `automation, api, ai`
- Маршрут реализации: `./playbooks/automation-script.md`

## Current Phase

- Фаза: `execution`
- Режим токенов: `ultra`
- Режим оркестрации: `solo`
- Политика чтения docs: `summary-first, quiz-first, docs-last`
- Сначала открой: `phase-card.md, ultra-context.md, active-context.md, implementation-plan.md`

## Product DNA

- core_promise: дать автономии полезную силу без потери deterministic control
- interface_energy: служебная и доказательная
- trust_signal: артефакты, guardrails, queue legality, repo-visible closeout
- ... ещё 4 пункт(ов), открывай подробные файлы только если они реально нужны.

## Профиль дизайна

- visual_intensity: спокойный
- composition_mode: служебный и объяснимый
- shape_language: минимальный
- allow_complex_shapes: False
- ... ещё 4 пункт(ов), открывай подробные файлы только если они реально нужны.

## Источники стиля

- нет внешних style-inputs

## Правила уникальности

- Не существует одного универсального шаблона, который подходит всем проектам.
- Не выбирай решение только потому, что оно дефолтное для библиотеки или фреймворка.
- Не повторяй один и тот же визуальный стиль во всех проектах.
- Не заполняй пробелы типичным SaaS-набором без продуктового обоснования.
- ... ещё 1 пункт(ов), открывай подробные файлы только если они реально нужны.

## Варианты плана

- `minimum`: close only the repo-local unblockers and do not start target-repo onboarding yet
- `optimal`: close the repo-local unblockers and onboard the first target repo so the path to Phase 3 is honest
- `expanded`: the optimal path plus webhook-ready intake and stronger audit surfaces before Claude strategy

## Стек

- runtime: Python 3.10+ local supervisor
- builder: Codex CLI as sole writer
- audit_path: Claude Code plus Cowork plus Trevor verify
- queue_and_routing: Linear issues normalized by supervisor
- verification: deterministic command runners plus Playwright UI checks
- ... ещё 1 пункт(ов), открывай подробные файлы только если они реально нужны.

## Активные роли

- `project-discovery`
- `solution-architect`
- `backend-builder`
- `automation-builder`
- `qa-reviewer`
- `deploy-operator`

## Критерии качества

- `repo-truth-aligned`
- `queue-contract-bounded`
- `single-writer-preserved`
- `failure-paths-defined`
- `env-documented`
- `dependency-hygiene`

## Scope guardrails

- Не добавляй функции, которые пользователь явно не просил, без отдельного блока рекомендаций.
- В первую версию включай только то, что нужно для одного рабочего сценария.
- Советы по улучшению отделяй от обязательного scope.
- Любое расширение scope после плана требует явного подтверждения пользователя.

## Открывай полные docs только если

- только если выбранный вариант плана меняет ближайший execution slice
- только если без имени первого target repo нельзя закрыть следующий шаг честно
- только если короткой approval-сводки уже недостаточно для решения

## Current Queue

- `approval` (done): Получить одно явное подтверждение плана до начала продуктовых правок
- `execution` (in_progress): Реализовать одобренный repo-local slice и только потом расширяться в target-repo execution
- `verification` (pending): Провести QA-проверку и пройти критерии качества
- `handoff` (pending): Подготовить отчёт по проверке, чеклист секретов и финальный handoff

## Правила экономии токенов

- Сначала читай `phase-card.md`, потом `ultra-context.md`.
- Открывай `context-bundle.md` только если коротких файлов уже недостаточно.
- Открывай полные docs только по текущим триггерам фазы.
- Используй `state.json` для маршрутизации решений, а не для полного перечитывания проекта.
- Если план уже заморожен, не пересобирай стек, роли и packs без явной причины.
