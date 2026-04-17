# Codex Plugin Operator Cheat Sheet

This is the operational companion to
`docs/codex-april-16-2026-impact.md`.

- The impact memo answers: should this repo adopt or defer a plugin?
- This cheat sheet answers: if the plugin is available, what exact job should
  it own?

## One-owner rule

- One plugin should own one phase of a task at a time.
- Repo docs stay authoritative. Plugins may structure work, but they do not
  replace `PROJECT_INTENT.md`, `PROMPTS.md`, `QUEUE-RUNS.md`, or `todo.md`.
- If two plugins want to own planning, pick one and make the other a supporting
  review layer only.

## Default split

| Plugin | Let it own | Start with it when | Hand off to | Prompt to use |
|---|---|---|---|---|
| `Autopilot` | project intake, discovery questions, briefing, route selection, final handoff framing | the work starts as a vague or multi-surface idea and the route is still unclear | `Cavekit` if a real spec is needed; `HOTL` once implementation should begin | `Use Autopilot to turn this rough idea into a project brief, ask what is missing, and recommend a build route. Do not start coding yet.` |
| `Cavekit` | requirements, acceptance criteria, dependency-aware build-task decomposition | the general direction is known but the spec and build packets are still weak | `HOTL` for execution, or `CodeRabbit` once a local diff exists | `Use Cavekit to turn this approved direction into requirements, acceptance criteria, and build tasks. I want the spec before implementation.` |
| `HOTL` | bounded implementation discipline, review, verification, and resume | a real task or plan exists and code work is about to start | `CodeRabbit` or Claude Code review after the implementation slice lands | `Use HOTL to execute this bounded plan with verification gates. Verify each step and do not claim success without evidence.` |
| `CodeRabbit` | deterministic pre-audit: PR review, mechanical bugs, security signals, missing tests, lint-style findings | a bounded diff or PR already exists and you want fast review signal before higher-cost human or Claude review | Claude Code, Trevor, or a HOTL repair loop | `@coderabbit Review this diff for mechanical bugs, security issues, and missing tests.` |
| `Brooks Lint` | second-pass structural review: decay risks, architecture smells, maintainability, and test-quality signal | a bounded diff, PR, or repo slice exists and you want a book-grounded design-quality pass after the fast mechanical review | Codex or `HOTL` for fixes; Claude Code or Trevor for final judgment | `Use Brooks Lint to review this diff for decay risks, maintainability issues, and test-quality smells. Keep the report evidence-backed and non-blocking.` |
| `Sentry` | read-only production triage: recent issues, issue events, and error summarization | a real Sentry org/project exists and local auth is configured, and the task is operational debugging rather than architecture work | Codex or `HOTL` repair work once a concrete defect is identified | `Use Sentry to inspect recent production issues for this project and summarize the top unresolved errors without changing anything.` |
| `plugin-eval` | evidence-backed comparison of plugin, model, or workflow choices | the question is whether a new plugin or workflow actually helps | the impact memo, an ADR, or a follow-up spike | `Use plugin-eval to compare baseline versus [plugin/workflow] on representative tasks and report where it helps, hurts, or adds noise.` |

## Current repo status

- `Autopilot`, `HOTL`, and `Cavekit` are now actually installed and enabled in
  Codex through the personal marketplace `gillettes-local-plugins`.
- `Cavekit` is installed under the plugin id `ck`.
- `Brooks Lint` is installed and enabled through `codex-local-plugins`, and
  this repo now carries a minimal `.brooks-lint.yaml` boundary config so
  archive/runtime output paths do not pollute default Brooks review scope.
- `Sentry` is enabled through `openai-curated`, but it still requires local
  `SENTRY_AUTH_TOKEN` auth plus a real org/project before it becomes usable.
- The exact install state, identifiers, auth prerequisites, and settings
  posture for these plugins now live in `docs/codex-workflow-plugin-setup.md`.
- `CodeRabbit` has committed repo-local settings at `.coderabbit.yaml`.
- The exact field-by-field settings and rationale now live in
  `docs/coderabbit-review-settings.md`.
- The repo decision is to try `CodeRabbit` first for dedicated PR-review
  quality. `GitHub Copilot` remains the cheaper GitHub-native fallback, not
  the active trial.
- The intended review flow is: Codex or `HOTL` lands a bounded diff, then
  `CodeRabbit` reviews the diff for mechanical issues, then Claude Code or
  Trevor handles the deeper architectural and acceptance pass.
- The remaining activation step is still manual: GitHub App install and
  authorization for this repository.
- Until that is active, treat `CodeRabbit` as chosen-but-not-yet-proven here
  and fall back to Claude Code or Trevor review for the same pre-audit slot.
- After activation, calibrate it on 3-5 real PRs before enabling stronger
  request-changes or pre-merge gating behavior.

## Settings rule

- `Autopilot`, `HOTL`, and `Cavekit` currently have no repo-committed settings
  file; their settings posture here is operational, not YAML-driven.
- `Brooks Lint` is the middle case: it supports optional repo-local tuning via
  `.brooks-lint.yaml`, and this repo currently uses that only for boundary
  exclusions (`design-history/`, `.autoclaw/`, `worktrees/`) rather than risk
  tuning.
- `CodeRabbit` is the opposite: its active repo-local behavior is expected to
  live in `.coderabbit.yaml`.
- `Sentry` has no repo-committed config here; keep auth and org/project
  defaults in local environment variables, not in tracked files.
- Do not invent extra repo-local config for `Autopilot`, `HOTL`, `Cavekit`, or
  `Sentry` unless we actually decide their behavior should become part of repo
  truth instead of operator preference.

## Do not overlap them like this

- Do not let `Autopilot` and `Cavekit` both write the primary plan for the
  same task.
- Do not use `HOTL` to rediscover product direction that should have been
  settled upstream.
- Do not let `CodeRabbit`, `Brooks Lint`, or `plugin-eval` become workflow
  owners. They are review or measurement layers.
- Do not let `Sentry` turn into a vague "monitoring plugin" placeholder in
  docs-first work. It only earns runtime attention when there is a real Sentry
  project and a real production issue to inspect.
- For small repo-local doc edits or narrow fixes, skip `Autopilot` and
  `Cavekit`; start with direct execution or `HOTL`.

## Additional candidates researched

| Plugin | Why it could help | Current stance |
|---|---|---|
| `Session Orchestrator` | Offers wave execution, quality gates, bootstrap checks, VCS integration, and clean close-out as a full session envelope. | Interesting, but too close to this repo's unresolved queue and supervisor substrate questions to adopt casually. Study later. |
| `Agent Message Queue` | Provides a real file-based handoff bus for multi-agent or cross-session work instead of ad hoc messages in docs or chat. | Useful only if cross-session agent handoffs become a real bottleneck. Premature for the current repo. |
| `Claude Code for Codex` | Lets Codex launch tracked Claude review, rescue, and background work from inside the same Codex thread. | Later or conditional. It overlaps the current Codex-to-Claude review bridge unless tracked Claude jobs become concretely valuable. |
| `Registry Broker` | Adds brokered specialist delegation and recoverable external-agent selection. | Do not adopt now. It adds delegation infrastructure before this repo has proven the need for a broker layer. |
| `ECC` | Huge cross-agent skill and workflow library with TDD, security, verification, and autonomous-development patterns. | Treat as a source library, not a workflow owner. Harvest ideas selectively; do not install wholesale. |

## Cavekit note

`Cavekit` is the current verified Blueprint-family match. Its current command
surface is `ck` / `Cavekit`; the old `bp` aliases are deprecated in favor of
`/ck:*`.
