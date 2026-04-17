# Codex Workflow Plugin Setup

This document is the durable setup and state companion for the three
non-curated workflow plugins currently installed for this repo's operator use:
`Autopilot`, `HOTL`, and `Cavekit`.

Use this file for:

- the exact plugin identifiers and marketplace source
- the current enabled state in Codex
- the repo's intended use and non-use boundaries
- the settings posture for these plugins in this repo

Do not use this file to change the canonical plugin stance. The current
use/defer decision still lives in
`docs/codex-april-16-2026-impact.md` `Plugin decision ledger`.

## Scope

These are operator-side workflow plugins, not runtime dependencies of the v1
autonomous coding harness.

- They are installed in the operator's Codex environment, not committed into
  this repo as repo-local plugin bundles.
- They may help shape work, decompose work, or discipline implementation.
- They do not replace repo truth, supervisor legality, `todo.md`, or Linear.

## Current install state

As of 2026-04-17, the local Codex environment has a personal marketplace named
`gillettes-local-plugins` registered from `/Users/gillettes`, and the three
workflow plugins below are enabled in `~/.codex/config.toml`.

| Repo name | Codex plugin id | Display name | Marketplace | Local source root | Enabled state |
|---|---|---|---|---|---|
| `codex-project-autopilot` | `codex-project-autopilot` | `Codex Project Autopilot` | `gillettes-local-plugins` | `/Users/gillettes/plugins/codex-project-autopilot` | enabled |
| `hotl` | `hotl` | `HOTL` | `gillettes-local-plugins` | `/Users/gillettes/plugins/hotl` | enabled |
| `cavekit` | `ck` | `Cavekit` | `gillettes-local-plugins` | `/Users/gillettes/plugins/cavekit` | enabled |

Important identifier note:

- `Cavekit` is installed under the plugin id `ck`.
- The repo should refer to it as `Cavekit` in human-facing docs, but the local
  technical id is `ck`.

## Evidence surface

The install state above is grounded in the local Codex files, not chat memory:

- `~/.agents/plugins/marketplace.json`
- `~/.codex/config.toml`
- each plugin's local `.codex-plugin/plugin.json`

This repo does not commit those home-directory files. This document exists so
later sessions can reason about the actual operator environment without
pretending those home files are part of repo truth.

## Repo operating split

These three plugins should not overlap as co-equal workflow owners.

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

## Settings posture for this repo

Unlike `CodeRabbit`, these three plugins currently have no repo-committed
settings file such as a `.yaml`, `.json`, or hook file checked into this repo.
That is intentional.

Current posture:

- `enabled in Codex`: yes
- `repo-local config file`: none
- `default owner`: none; the user or operator chooses when to invoke them
- `auto-run`: no
- `workflow authority`: no
- `repo-truth authority`: no

What "settings" means here is therefore procedural rather than config-file
driven:

1. Keep all three enabled in the operator environment.
2. Invoke them intentionally by phase, not all at once.
3. Keep outputs subordinate to repo truth.
4. Reconcile any accepted output into repo docs and `todo.md`.
5. Do not count installation alone as "tried here" in the canonical ledger.

## Prompt posture

Use prompt wording that enforces phase boundaries:

- `Autopilot`: `Use Autopilot to turn this rough idea into a brief, ask only the missing questions, recommend a route, and stop before coding.`
- `Cavekit`: `Use Cavekit to turn this approved direction into requirements, acceptance criteria, and build tasks. Stop before implementation.`
- `HOTL`: `Use HOTL to execute this bounded plan with verification discipline. Do not claim success without evidence.`

Avoid prompts that let multiple plugins own the same phase:

- do not ask `Autopilot` and `Cavekit` to both generate the primary plan
- do not ask `HOTL` to rediscover product direction
- do not ask any of the three to become the source of truth for acceptance
  criteria, decisions, or closeout records

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
