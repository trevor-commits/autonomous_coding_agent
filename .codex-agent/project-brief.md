# Краткий бриф проекта

## 1. Что это за проект

- Тип проекта: automation harness with API-routing sidecar needs
- Рабочее название: Autonomous Coding Agent control-plane
- Для кого: Trevor as operator, plus later audit sessions that need durable
  repo-visible truth
- Главная ценность: bounded autonomous execution with deterministic legality,
  verification, and artifact-backed closeout

## 2. Что должно работать в первой версии

- Главный сценарий v1: choose a real target repo, normalize a bounded coding
  task, execute it through the deterministic supervisor, and produce truthful
  ready/blocked evidence
- Что обязательно входит:
  - repo-local governance and branch/Linear lifecycle alignment
  - first implementation repo selection and Phase 0 baseline work
  - deterministic supervisor + single-writer Codex path
  - Phase 3 app launch and Playwright verification for one real repo
- Что пока не входит:
  - multi-writer execution
  - auto-merge or auto-deploy
  - Phase 4 Claude strategy layer
  - Phase 5 memory/resume hardening

## 3. Как пользователь проходит сценарий

1. The operator chooses a bounded coding objective or a queue-ready Linear issue
   tied to repo truth.
2. The supervisor validates and normalizes the work, then Codex implements
   inside the bounded scope.
3. Deterministic checks and UI verification run, and the operator receives a
   truthful ready/blocked outcome with artifacts.

## 4. Что влияет на сложность

- Нужен ли backend: yes, the supervisor and queue/control logic are backend code
- Нужна ли база: only durable run/artifact state when justified; no broad app DB
- Нужна ли авторизация: operator/service auth only, not end-user product auth
- Нужна ли админка: no generic admin panel
- Нужны ли оплаты: no
- Нужен ли ИИ: yes, Codex build lane and Claude audit lane are core

## 5. Что делает проект уникальным

- Характер продукта: strict, operator-facing, evidence-first
- Ось уникальности: runtime-owned correctness instead of AI-owned process
- Что помогает вызывать доверие: clear legality, one writer, explicit artifacts,
  repo-visible closeout
- На что проект не должен быть похож: generic AI swarm, generic SaaS control
  plane, or prompt theater disguised as automation
- Какие шаблонные решения здесь лишние: default dashboards, vague agent-manager
  claims, and hidden side effects
- Уровень визуальной смелости: low; clarity beats decoration
- Нужны ли сложные формы / асимметрия / перекрытия: no

## 6. Ограничения и пожелания

- Что важно по скорости: move only as fast as the next milestone stays honest
- Что важно по качеству: deterministic legality, clear evidence, no silent
  widening of scope
- Нужен ли деплой сразу: no, local truth against one real target repo matters first
- Есть ли обязательные сервисы или ограничения: Linear, Codex CLI, Claude,
  Git, Python, Playwright; avoid broad new infra without a concrete need

## 7. Данные и безопасность

- Какие данные реально собираем: repo metadata, issue metadata, run artifacts,
  logs, traces, screenshots, reports
- Есть ли чувствительные данные: yes, service tokens and target-repo local env
- Нужны ли роли и права доступа: yes for operator/service boundaries, not for
  broad end-user auth
- Какие секреты и ключи точно понадобятся: Linear auth, Codex auth path,
  Claude access path, optional webhook secret, target-repo env values
- Что нельзя хранить или показывать в клиенте: tokens, secrets, privileged env
  values, or raw sensitive payloads

## 8. Что я рекомендую упростить

- Do not expand into Phase 4 or Phase 5 before one real target repo proves the
  narrower harness.
- Do not build new UI/control-plane surfaces unless the current repo work
  specifically requires them.

## 9. Открытые вопросы

- Which first implementation repo Trevor wants to onboard.
- Whether the next approved slice should stay repo-local only or include
  target-repo onboarding immediately.

## 10. Готовность к планированию

- Статус: да
- Почему: the repo goal, v1 boundary, and current dependency gap are clear
  enough to present bounded plan variants without pretending execution can start
  blindly.
