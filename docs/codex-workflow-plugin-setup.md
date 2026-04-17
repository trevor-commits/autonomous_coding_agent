# Codex Workflow Plugin Setup

This document is the durable setup and state companion for the installed
operator plugins currently enabled for this repo's use: `Autopilot`, `HOTL`,
`Cavekit`, `Brooks Lint`, and `Sentry`.

Use this file for:

- the exact plugin identifiers and marketplace source
- the current enabled state in Codex
- the repo's intended use and non-use boundaries
- the settings posture for these plugins in this repo

Do not use this file to change the canonical plugin stance. The current
use/defer decision still lives in
`docs/codex-april-16-2026-impact.md` `Plugin decision ledger`.

## Scope

These are operator-side workflow, review, and observability plugins, not
runtime dependencies of the v1 autonomous coding harness.

- They are installed in the operator's Codex environment, not committed into
  this repo as repo-local plugin bundles.
- They may help shape work, decompose work, or discipline implementation.
- They do not replace repo truth, supervisor legality, `todo.md`, or Linear.

## Current install state

As of 2026-04-17, the local Codex environment has the personal marketplaces
`gillettes-local-plugins` and `codex-local-plugins`, plus curated plugin
sources such as `openai-curated`. The five operator plugins below are enabled
in `~/.codex/config.toml`.

| Repo name | Codex plugin id | Display name | Marketplace | Local source root | Enabled state |
|---|---|---|---|---|---|
| `codex-project-autopilot` | `codex-project-autopilot` | `Codex Project Autopilot` | `gillettes-local-plugins` | `/Users/gillettes/plugins/codex-project-autopilot` | enabled |
| `hotl` | `hotl` | `HOTL` | `gillettes-local-plugins` | `/Users/gillettes/plugins/hotl` | enabled |
| `cavekit` | `ck` | `Cavekit` | `gillettes-local-plugins` | `/Users/gillettes/plugins/cavekit` | enabled |
| `brooks-lint` | `brooks-lint` | `brooks-lint` | `codex-local-plugins` | `/Users/gillettes/.codex/plugins/cache/codex-local-plugins/brooks-lint/1.0.0` | enabled |
| `sentry` | `sentry` | `Sentry` | `openai-curated` | `/Users/gillettes/.codex/plugins/cache/openai-curated/sentry/314574a046f21938025ae443f9c6dbbd0c2c9b7a` | enabled |

Important identifier note:

- `Cavekit` is installed under the plugin id `ck`.
- The repo should refer to it as `Cavekit` in human-facing docs, but the local
  technical id is `ck`.
- `Brooks Lint` is installed under the plain plugin id `brooks-lint`.
- `Sentry` is installed under the plain plugin id `sentry`.

Session-surface note:

- Enabled in operator config does not guarantee that every Codex thread exposes
  the plugin as a callable surface. The current-thread accessible subset is
  tracked separately in `docs/codex-app-marketplace-evaluations.md`; this file
  records operator install truth, not per-thread tool exposure.

## Evidence surface

The install state above is grounded in the local Codex files, not chat memory:

- `~/.agents/plugins/marketplace.json`
- `~/.codex/config.toml`
- each plugin's local `.codex-plugin/plugin.json`
- Brooks Lint's example repo config `.brooks-lint.example.yaml`
- this repo's committed `.brooks-lint.yaml`

This repo does not commit those home-directory files. This document exists so
later sessions can reason about the actual operator environment without
pretending those home files are part of repo truth.

## Repo operating split

These plugins should not overlap as co-equal workflow owners.

### `Autopilot`

Use for:

- vague project intake
- discovery questions
- brief creation
- route selection
- handoff framing before any real spec or implementation work

Do not use for:

- bounded repo tasks that already have a clear `GIL-N`
- direct implementation once the route is known
- final review or completion authority

Expected stop condition:

- stop after the brief, assumptions, route recommendation, and handoff framing
- hand off to `Cavekit` for spec-heavy work or `HOTL` for execution

### `Cavekit`

Use for:

- requirements
- acceptance criteria
- build-task decomposition
- dependency-aware build packets
- pre-build traceability when the direction is known but the spec is weak

Do not use for:

- rediscovering already-approved product direction
- small fixes
- owning the implementation loop end to end

Expected stop condition:

- stop once the spec, acceptance criteria, and task decomposition are clear
- hand off to `HOTL` for execution

### `HOTL`

Use for:

- bounded implementation execution
- review discipline
- verification discipline
- resumable execution once a real plan exists

Do not use for:

- early product discovery
- replacing repo truth or queue authority
- forcing heavy workflow ceremony onto trivial doc or typo edits

Expected stop condition:

- stop once the bounded implementation slice is complete and verified
- hand off to `CodeRabbit`, Claude Code, or Trevor for deeper review as needed

### `Brooks Lint`

Use for:

- second-pass design and maintainability review
- architecture-decay and tech-debt scans on bounded repo slices
- test-quality review when the question is "are these tests actually healthy?"

Do not use for:

- default review ownership on every change
- replacing `CodeRabbit`, Claude Code, or Trevor as the final judge
- inventing repo-risk tuning beyond the current boundary exclusions without an
  explicit decision

Expected stop condition:

- stop after producing a bounded review or audit report
- hand off to Codex or `HOTL` for fixes, then to Claude Code or Trevor for the
  final call

### `Sentry`

Use for:

- read-only issue triage
- recent event inspection
- production-error summarization when a real Sentry org/project exists

Do not use for:

- storing auth in repo files
- write actions or incident-state mutation from this repo
- pretending observability is part of the v1 core runtime contract

Expected stop condition:

- stop after identifying the relevant issue/event cluster and summarizing the
  concrete production defect
- hand off to Codex or `HOTL` for the actual repair work

## Settings posture for this repo

These plugins do not all share the same settings model.

Current posture:

- `enabled in Codex`: yes
- `default owner`: none; the user or operator chooses when to invoke them
- `auto-run`: no
- `workflow authority`: no
- `repo-truth authority`: no

Per-plugin config posture:

- `Autopilot`, `HOTL`, `Cavekit`: no repo-committed config file; settings are
  operational and phase-bound.
- `Brooks Lint`: repo-local boundary config present at `.brooks-lint.yaml`.
  It excludes `design-history/`, `.autoclaw/`, and `worktrees/` from default
  Brooks analysis and leaves all risk defaults intact. Generated
  `.brooks-lint-history.json` is intentionally gitignored here.
- `Sentry`: no repo-committed config file. Usable setup is local-only:
  `SENTRY_AUTH_TOKEN` is required; `SENTRY_ORG`, `SENTRY_PROJECT`, and
  `SENTRY_BASE_URL` are the normal optional defaults; none of those belong in
  tracked repo files.

What "settings" means here is therefore procedural rather than config-file
driven:

1. Keep the enabled plugins enabled in the operator environment.
2. Invoke them intentionally by phase, not all at once.
3. Keep outputs subordinate to repo truth.
4. Reconcile any accepted output into repo docs and `todo.md`.
5. Do not count installation alone as "tried here" in the canonical ledger.
6. Keep Sentry auth local and keep Brooks risk tuning minimal unless the repo
   deliberately wants Brooks-specific policy in version control.

## Prompt posture

Use prompt wording that enforces phase boundaries:

- `Autopilot`: `Use Autopilot to turn this rough idea into a brief, ask only the missing questions, recommend a route, and stop before coding.`
- `Cavekit`: `Use Cavekit to turn this approved direction into requirements, acceptance criteria, and build tasks. Stop before implementation.`
- `HOTL`: `Use HOTL to execute this bounded plan with verification discipline. Do not claim success without evidence.`
- `Brooks Lint`: `Use Brooks Lint to review this bounded diff or repo slice for decay risks, maintainability issues, and test-quality smells. Keep the report evidence-backed and non-blocking.`
- `Sentry`: `Use Sentry to inspect recent issues and events for this real project and summarize the top unresolved production errors without changing anything.`

Avoid prompts that let multiple plugins own the same phase:

- do not ask `Autopilot` and `Cavekit` to both generate the primary plan
- do not ask `HOTL` to rediscover product direction
- do not ask `Brooks Lint` to become the first or only reviewer
- do not ask `Sentry` to stand in for architecture review or deterministic
  verification
- do not ask any of these plugins to become the source of truth for
  acceptance criteria, decisions, or closeout records

## What counts as "used here"

For this repo's plugin ledger:

- installed and enabled in Codex counts as installed state
- operator guidance written into repo docs counts as documented operating
  policy
- a real plugin-backed repo task or implementation slice is what flips a
  plugin from installed to genuinely tried here

That distinction matters. This repo should not confuse "available in the
operator environment" with "proven on real work."

## Maintenance rule

If any of these change, update this doc in the same commit as the relevant
ledger or cheat-sheet change:

- marketplace name
- plugin id
- enabled/disabled state
- local source root
- the repo's intended operating split
- the presence of any new repo-committed config for these plugins
- Sentry auth prerequisites or the chosen repo policy for Brooks history/config
