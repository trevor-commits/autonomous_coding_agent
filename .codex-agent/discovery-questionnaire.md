# Квиз discovery

## Идея пользователя

Run Codex Project Autopilot inside the existing `Autonomous Coding Agent`
repository so the project gets a local `.codex-agent` state, a truthful
discovery summary, and a bounded approval-ready plan instead of ad hoc next
steps scattered across chat.

## Волна 1. Базовая картина

### Блок 1. Основа

#### Зачем я это спрашиваю

[Это нужно, чтобы понять тип проекта и его главную ценность.]

#### Вопросы

- Что ты хочешь сделать: сайт, бот, сервис или автоматизацию?
- Для кого это?
- Какую главную проблему это решает?
- Что пользователь должен получить в итоге?

#### Ответы пользователя

- This is an autonomous coding harness, not a marketing site or generic SaaS.
- It is for Trevor as the operator, plus later audit sessions that need
  durable repo-visible truth.
- It solves the problem that "AI autonomy" is not useful unless legality,
  scope, verification, and closeout remain deterministic and inspectable.
- The end result is a narrow harness that can accept a coding objective or
  eligible Linear issue, run through the deterministic supervisor, verify
  locally, and emit readiness evidence.

### Блок 2. Первая версия

#### Зачем я это спрашиваю

[Это нужно, чтобы не раздувать первую версию и не тащить лишние функции.]

#### Вопросы

- Что обязательно должно работать в v1?
- Что точно можно не делать сейчас?
- Что важнее: быстрее запустить или сделать с запасом?

#### Ответы пользователя

- v1 must keep the repo-local control-plane trustworthy, choose the first real
  target repo, and unlock the first truthful Phase 3 path.
- It does not need multi-writer autonomy, Phase 4 Claude strategy, or Phase 5
  memory hardening yet.
- Speed matters, but only if the next step is honest about dependencies and
  does not skip the target-repo prerequisite.

### Блок 3. Сложность

#### Зачем я это спрашиваю

[Это влияет на то, нужен ли backend, база, личный кабинет, оплата или ИИ.]

#### Вопросы

- Нужен ли личный кабинет?
- Нужно ли что-то хранить?
- Нужны ли оплаты?
- Нужен ли ИИ?
- Нужна ли админка?

#### Моя рекомендация, если пользователь не уверен

- [Например: если нужно быстрее запустить, пока можно без авторизации и админки.]

#### Ответы пользователя

- Personal accounts for end users are not part of this repo's own product
  surface.
- Some durable state exists for run artifacts and queue evidence, but a broad
  product database is explicitly out of scope for v1.
- Payments are not needed.
- AI is required: Codex is the sole writer and Claude remains in the audit path.
- A generic admin panel is not needed; operator control is through repo docs,
  Linear routing, and supervisor surfaces.

### Блок 3.6. Данные и безопасность

#### Зачем я это спрашиваю

[Это нужно, чтобы не тащить лишние персональные данные, сложную авторизацию и небезопасные ключи в первую версию.]

#### Вопросы

- Будут ли тут данные пользователей или только открытая информация?
- Нужно ли делить права доступа: пользователь, админ, оператор?
- Нужны ли ключи, токены, webhook secrets или сервисные доступы?
- Есть ли что-то, что нельзя хранить, логировать или показывать в клиенте?

#### Моя рекомендация, если пользователь не уверен

- [Например: если хочешь быстрее стартовать, лучше сначала без лишних персональных данных и сложной авторизации.]

#### Ответы пользователя

- The repo handles operator metadata, issue-routing metadata, repo contracts,
  run contracts, logs, reports, screenshots, traces, and verification output.
- Access separation matters for operator tools and service integrations, but
  broad end-user auth is not part of the first version.
- Secrets that matter include provider/API tokens, webhook secrets, and local
  auth paths for Codex/Claude/Linear integrations.
- Secrets, tokens, and privileged values must never be committed, echoed into
  logs, or exposed to any client-facing surface.

### Что уже ясно после первой волны

- The project is a deterministic autonomous delivery harness with repo docs as
  the source of truth.
- The repo is already beyond pure planning; Phase 1 and Phase 2 slices exist.
- The main unresolved dependency is still the first implementation repo needed
  to complete Phase 0 honestly and unlock end-to-end proof.

### Что ещё неясно

- Which real target repo should be onboarded first once repo-local unblockers
  are cleared.
- Whether Trevor wants to keep the next slice repo-local only for now, or use
  the next plan to unlock target-repo onboarding immediately.

### Блок 3.5. Уникальность проекта

#### Зачем я это спрашиваю

[Это нужно, чтобы не превратить проект в усреднённый шаблон и не подставить типовую структуру вместо живого продукта.]

#### Вопросы

- Что делает этот проект особенным именно для твоей аудитории?
- На что он точно не должен быть похож?
- Как должен ощущаться продукт: строго, утилитарно, дружелюбно, премиально, быстро, экспертно?
- Есть ли что-то, что ты точно не хочешь видеть: типовой лендинг, generic dashboard, лишний личный кабинет, перегруженные блоки?
- Есть ли сайты или стили, на которые стоит ориентироваться или, наоборот, не стоит быть похожими?
- Насколько смелый дизайн уместен: спокойный, выразительный или очень смелый?
- Нужны ли сложные формы, асимметрия, перекрытия, органические силуэты или лучше более строгий визуальный язык?

#### Моя рекомендация, если пользователь не уверен

- [Например: лучше выбрать один характер продукта, чем пытаться сделать “всё и сразу”.]

#### Ответы пользователя

- The product should feel strict, evidence-first, and operator-oriented rather
  than playful or generic.
- It must not look like a generic AI swarm, a vague control plane, or a
  dashboard built from default cards with unclear authority.
- The trust signal is deterministic control: one writer, one browser owner,
  clear legality, explicit artifacts, and repo-visible closeout.
- The anti-template constraint is strong: do not hide workflow correctness
  behind "AI magic" language or broad platform claims.
- Visual boldness is low; clarity, auditability, and precision matter more than
  style.
- Complex shapes and decorative asymmetry are unnecessary for this repo.

## Волна 2. Уточняющие вопросы

### Блок 4. Главный сценарий

#### Зачем я это спрашиваю

[Это нужно, чтобы понять один главный путь пользователя и не строить продукт вокруг второстепенных функций.]

#### Вопросы

- Опиши путь пользователя от начала до результата.
- Где он заходит?
- Что нажимает?
- Что видит в конце?
- Что будет считаться успешным результатом?

#### Ответы пользователя

- The operator starts with a bounded coding objective or a queue-eligible Linear
  issue tied to repo truth.
- The supervisor validates repo and run contracts, normalizes the work, and
  creates the bounded execution surface.
- Codex writes within the allowed scope, deterministic verification runs, and
  Playwright UI checks apply when the target repo requires them.
- The successful end state is a ready or blocked outcome backed by artifacts,
  not narration.

### Блок 5. Ограничения

#### Зачем я это спрашиваю

[Это влияет на выбор стека, глубину реализации и то, нужен ли запуск сразу в интернет.]

#### Вопросы

- Это должен быть просто MVP или уже готовый рабочий продукт?
- Нужен запуск в интернет сразу?
- Есть ли сервисы, которые уже точно надо использовать?
- Есть ли что-то, что использовать нельзя?

#### Ответы пользователя

- This is a real working MVP, but still intentionally narrow.
- Public internet deployment of this repo is not the next gate; truthful local
  execution against one real target repo is.
- Required services and tools are Linear, Codex CLI, Claude access, Git,
  Python, and Playwright.
- The repo should avoid broad new infra, broad new dependencies, and any scope
  that weakens deterministic ownership.

### Блок 6. Упрощение

#### Зачем я это спрашиваю

[Это нужно, чтобы убрать лишнюю сложность из первой версии и не переделывать проект из-за перегруза scope.]

#### Вопросы

- Если хочется запустить быстрее, согласен ли ты пока убрать лишнее?
- Что из этого можно отложить на потом: auth, база, админка, оплаты, ИИ?

#### Моя рекомендация, если пользователь не уверен

- [Например: лучше сначала проверить спрос без лишнего backend и авторизации.]

#### Ответы пользователя

- Yes: anything that does not directly help prove one end-to-end bounded run on
  a real repo can wait.
- The deferrable items are Phase 4 Claude strategy, Phase 5 memory/resume
  hardening, multi-writer execution, and broad platformization.

### Что уже понятно после двух волн

- The truthful next move is not "build more generic autonomy"; it is to choose
  a bounded plan that either stays repo-local on purpose or explicitly names
  the first implementation repo and unlocks the next real milestone.

## Вот что я уже понял

- This repo is the control-plane and source-of-truth home for the autonomous
  harness.
- The project's uniqueness is deterministic legality and artifact-backed
  closeout, not breadth of AI features.
- The most important current dependency is the first target repo selection.

## Вот что ещё неясно

- Which first implementation repo Trevor wants to use for the honest Phase 0
  baseline.
- Whether the next approved slice should stop at repo-local unblockers or also
  include target-repo onboarding.

## Рекомендованные дефолты

- Treat this as `automation-script` plus `api-integration-worker`, because the
  core product is a deterministic Python supervisor with external issue/API
  routing.
- Keep the orchestration mode `solo` until the target repo is chosen and the
  immediate critical path stops being blocked by one operator decision.

## Что делает проект уникальным

- Character: strict, narrow, evidence-first operator tooling.
- Uniqueness axis: runtime-owned correctness instead of AI-owned workflow
  theater.
- Anti-template rule: never present generic AI-manager language or generic SaaS
  UI as if that were the product.

## Открытые вопросы

- Which first implementation repo should Phase 0 target.
- Approve `минимум`, `оптимально`, or `с-запасом` as the next bounded route.

## Готово к планированию

да

## Security-заметки для плана

- Real data: repo metadata, issue-routing metadata, run artifacts, logs,
  screenshots, traces, and closeout evidence.
- Required secrets/access: Codex auth path, Claude access path, Linear auth,
  optional webhook secret, and any target-repo local env needed for validation.
- Simplify the start by keeping secrets out of repo docs and code, avoiding new
  hosted state unless a real target-repo scenario demands it, and deferring any
  new privileged action surface that is not required for the next milestone.
