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
| `CodeRabbit` | deterministic pre-audit: mechanical bugs, security signals, missing tests, lint-style findings | local changes already exist and you want fast review signal before higher-cost human or Claude review | Claude Code, Trevor, or a HOTL repair loop | `@coderabbit Review the current changes for mechanical bugs, security issues, and missing tests.` |
| `plugin-eval` | evidence-backed comparison of plugin, model, or workflow choices | the question is whether a new plugin or workflow actually helps | the impact memo, an ADR, or a follow-up spike | `Use plugin-eval to compare baseline versus [plugin/workflow] on representative tasks and report where it helps, hurts, or adds noise.` |

## Current repo status

- `CodeRabbit` has committed repo-local settings at `.coderabbit.yaml`.
- The remaining activation step is still manual: GitHub App install and
  authorization for this repository.
- Until that is active, treat `CodeRabbit` as configured-but-not-yet-proven here
  and fall back to Claude Code or Trevor review for the same pre-audit slot.
- After activation, calibrate it on 3-5 real PRs before enabling stronger
  request-changes or pre-merge gating behavior.

## Do not overlap them like this

- Do not let `Autopilot` and `Cavekit` both write the primary plan for the
  same task.
- Do not use `HOTL` to rediscover product direction that should have been
  settled upstream.
- Do not let `CodeRabbit`, `Brooks Lint`, or `plugin-eval` become workflow
  owners. They are review or measurement layers.
- For small repo-local doc edits or narrow fixes, skip `Autopilot` and
  `Cavekit`; start with direct execution or `HOTL`.

## Additional candidates researched

| Plugin | Why it could help | Current stance |
|---|---|---|
| `Brooks Lint` | Adds a second-pass maintainability and test-quality review lens grounded in explicit engineering-source heuristics instead of only generic AI review. | Worth a bounded spike if `CodeRabbit` plus Claude review still misses decay/test-quality issues. Not a default reviewer yet. |
| `Session Orchestrator` | Offers wave execution, quality gates, bootstrap checks, VCS integration, and clean close-out as a full session envelope. | Interesting, but too close to this repo's unresolved queue and supervisor substrate questions to adopt casually. Study later. |
| `Agent Message Queue` | Provides a real file-based handoff bus for multi-agent or cross-session work instead of ad hoc messages in docs or chat. | Useful only if cross-session agent handoffs become a real bottleneck. Premature for the current repo. |
| `Claude Code for Codex` | Lets Codex launch tracked Claude review, rescue, and background work from inside the same Codex thread. | Later or conditional. It overlaps the current Codex-to-Claude review bridge unless tracked Claude jobs become concretely valuable. |
| `Registry Broker` | Adds brokered specialist delegation and recoverable external-agent selection. | Do not adopt now. It adds delegation infrastructure before this repo has proven the need for a broker layer. |
| `ECC` | Huge cross-agent skill and workflow library with TDD, security, verification, and autonomous-development patterns. | Treat as a source library, not a workflow owner. Harvest ideas selectively; do not install wholesale. |

## Cavekit note

`Cavekit` is the current verified Blueprint-family match. Its current command
surface is `ck` / `Cavekit`; the old `bp` aliases are deprecated in favor of
`/ck:*`.
