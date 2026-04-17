# Document Guide

**Date:** April 15, 2026
**Purpose:** Explain how the repo is organized now that active source-of-truth docs and archived history are separated.

## Quick Reference — Where to Find Things

If you are an agent beginning a session, read [CONTINUITY.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/CONTINUITY.md) and [COHERENCE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/COHERENCE.md) first, then [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md) and its repo-local overlay [AGENTS.project.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.project.md). If you are orienting as a human, start with [README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/README.md) and then use this guide for reading order and lookup.

Use these files for current truth:

- [CONTINUITY.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/CONTINUITY.md): what must be recorded before work can survive a conversation boundary.
- [COHERENCE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/COHERENCE.md): what must ripple when a live doc changes, including the Dependency Map and Ripple Check.
- [PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md): repo purpose, primary users, non-goals, success criteria.
- [canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md): authoritative architecture.
- [LOGIC.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LOGIC.md): conceptual behavior and control flow.
- [RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md): enforceable constraints and stop conditions.
- [STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md): file placement, repo boundary, runtime-state placement.
- [PROMPTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROMPTS.md): prompt-system source of truth.
- [QUEUE-RUNS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/QUEUE-RUNS.md): exact operating contract for unattended supervisor-mediated queue execution of Linear issues.
- [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md): build order and phase verification.
- [docs/superpowers-playbook.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/superpowers-playbook.md): repo-specific guidance for which Superpowers skills are worth using in this architecture/governance repo.
- [docs/codex-april-16-2026-impact.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/codex-april-16-2026-impact.md): repo-local guidance for how the April 16, 2026 Codex update should change operator workflow and where plugin use/not-use decisions now live.
- [docs/codex-plugin-operator-cheatsheet.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/codex-plugin-operator-cheatsheet.md): practical operating split for `Autopilot`, `HOTL`, `Cavekit`, `CodeRabbit`, and `plugin-eval`, plus the current shortlist of further plugin candidates worth spiking later.
- [docs/coderabbit-review-settings.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/coderabbit-review-settings.md): exact CodeRabbit settings, path instructions, UI-only caveats, and the repo-specific rationale for the current review-trial posture.
- [docs/launch-plan.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/launch-plan.md): launch-scope reconciliation for rollout guidance, smoke-lane planning, and what is still future implementation.
- [docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md): approved design baseline for the first runnable local single-run harness on top of the current supervisor foundation.
- [LINEAR.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR.md): operator-board governance for Linear usage; repo docs remain authoritative.
- [LINEAR-BOOTSTRAP.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR-BOOTSTRAP.md): step-by-step Linear setup runbook and known-pitfalls list for bootstrapping new projects.
- [.coderabbit.yaml](/Users/gillettes/Coding Projects/Autonomous Coding Agent/.coderabbit.yaml): repo-local CodeRabbit PR-review configuration; GitHub App installation remains a manual operator step.

Use `todo.md` for durable working records:

- `Active Next Steps`: execution-ready work
- `Linear Issue Ledger`: every live Linear issue, its current status, repo-side home, why it exists, and origin source
- `Work Record Log`: what would otherwise die with the conversation
- `Completed`: one-line landing index
- `Suggested Recommendation Log`: deferred or optional ideas
- `Audit Record Log`: audits and findings
- `Test Evidence Log`: verification runs and results
- `Feedback Decision Log`: plan refinements, accepted guidance, rejected guidance

Where does X go:

- New schema or machine boundary: `schemas/`
- New benchmark fixture: `fixtures/`
- New supervisor test: `tests/`
- New runtime artifact: `.autoclaw/runs/<run-id>/`
- New policy rule or placement decision: `RULES.md` or `STRUCTURE.md`
- New ADR or archived reconciliation: `design-history/`

## How The Repo Is Organized

The repo now has three clear layers:

1. Active source-of-truth documents at the root.
2. Working governance records at the root.
3. Historical material under `design-history/`.

That split is intentional. Root files should answer "what is true now?" Historical files should answer "how did we get here?"

## Active Source-Of-Truth Docs

### [CONTINUITY.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/CONTINUITY.md)

The continuity principle. Read this first when you need to know what must be durably written, signed, and pointed to before a task can be considered complete.

### [COHERENCE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/COHERENCE.md)

The coherence principle. Read this when a change might ripple across multiple live docs or when you need the append-only Dependency Map for companion-doc consistency.

### [PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md)

The canonical intent statement for the repository. Read this when you need the repo's purpose, primary users, non-goals, and success criteria in one place.

### [canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md)

The single authoritative design for the system. If any other document conflicts with it, this one wins.

### [LOGIC.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LOGIC.md)

The conceptual explanation of how the system behaves. Read this when you need the narrative of the control flow rather than the full spec.

### [RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md)

The enforceable rule index. Read this when the question is whether something is allowed, required, or terminal.

### [STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md)

The file-placement and boundary reference. Read this before creating new files or folders or when you need to know whether something belongs in this repo, a target repo, or runtime storage.

### [PROMPTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROMPTS.md)

The prompt-system source of truth. Read this before changing strategy prompts, review prompts, or audit loops.

### [QUEUE-RUNS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/QUEUE-RUNS.md)

The exact operating contract for unattended queue execution: eligible issue schema, supervisor loop, Codex queue prompt template, stop or skip policy, and logging plus commit flow.

### [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md)

The execution roadmap. Read this when deciding what phase comes next or how a milestone is verified.

### [docs/superpowers-playbook.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/superpowers-playbook.md)

The repo-local Superpowers guide. Read this when deciding which plugin skills
are actually worth using here instead of applying a generic implementation-heavy
workflow to a documentation-first repository.

### [docs/codex-april-16-2026-impact.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/codex-april-16-2026-impact.md)

The April 16, 2026 Codex-update impact memo. Read this when deciding whether a
new Codex product capability or plugin should change this repo's workflow now,
later, or not at all. The `Plugin decision ledger` section is the durable place
future sessions should update when a plugin is tried, approved, deferred, or
rejected.

### [docs/codex-plugin-operator-cheatsheet.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/codex-plugin-operator-cheatsheet.md)

The plugin operator cheat sheet. Read this when deciding which installed plugin
should own discovery, spec-writing, implementation discipline, deterministic
pre-audit, or plugin-evaluation work, and when you need the current shortlist
of additional workflow plugins worth later spikes.

### [docs/coderabbit-review-settings.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/coderabbit-review-settings.md)

The detailed CodeRabbit settings companion. Read this when you need the exact
field-by-field `CodeRabbit` settings, which values are encoded in
`.coderabbit.yaml`, which UI fields are intentionally blank, and which settings
carry support caveats such as slop detection.

### [docs/launch-plan.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/launch-plan.md)

The launch-scope reconciliation note. Read this when you need to distinguish between rollout pieces that already exist as documentation/process and future runtime or production capabilities that do not exist yet.

### [docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md)

The approved local single-run harness design baseline. Read this when planning
or implementing the next runnable supervisor slice so the work extends the
existing `supervisor/` foundation instead of reverting to a docs-only mental
model.

### [LINEAR.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR.md)

The Linear governance reference. Read this when configuring or using Linear so the board stays routing-only and repo truth stays in repo docs.

### LINEAR-BOOTSTRAP.md

The Linear setup runbook for new projects. Read this when configuring Linear from scratch so the screen-by-screen sequence and known pitfalls are followed without re-discovery.

### [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md)

Thin bootstrap file for agent sessions. Read this first so it can route you to the authoritative repo-local overlay.

### [AGENTS.project.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.project.md)

The authoritative repo-local agent overlay. Read this for repo-specific rules, role boundaries, completion authority, and mandatory markers.

### [README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/README.md)

The front page. Read this first when landing in the repo without context.

## Working Governance Records

### [todo.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/todo.md)

This is the durable working record for the project. It holds the active queue, the live Linear issue mirror with provenance, the completed work trail, suggested ideas, audit log, test evidence, and feedback decisions.

## Design History

Everything historical now lives under [design-history/](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history). Start with [design-history/README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/README.md) before reading archived material. Those files preserve prior reasoning and may contain superseded terminology or file-layout assumptions by design.

Key historical records:

- [design-history/queue-upgrade-research-2026-04-16.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/queue-upgrade-research-2026-04-16.md)
- [design-history/canonical-architecture-synthesis.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/canonical-architecture-synthesis.md)
- [design-history/FINAL-ARCHITECTURE-DECISION.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/FINAL-ARCHITECTURE-DECISION.md)
- [design-history/autonomous-agent-system-architecture-review.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/autonomous-agent-system-architecture-review.md)
- [design-history/agent-delegation-architecture-v2.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/agent-delegation-architecture-v2.md)
- [design-history/codex-audit-and-reconciliation.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/codex-audit-and-reconciliation.md)
- [design-history/three-way-reconciliation-final.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/three-way-reconciliation-final.md)
- [design-history/feedback-reconciliation-2026-04-14.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/feedback-reconciliation-2026-04-14.md)
- [design-history/AUDIT-2026-04-14.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/AUDIT-2026-04-14.md)
- [design-history/ADR-0001-terminal-state-normalization.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/ADR-0001-terminal-state-normalization.md)

## Where Feedback, Audits, And Plan Refinements Live

When the repo changes because of an audit, user feedback, or plan refinement, the durable record should go in one of two places:

- Use `todo.md` for the decision trail: active work, live Linear issue coverage with provenance, suggested ideas, audit outcomes, test evidence, and feedback decisions.
- Use `todo.md`'s `Completed` section for the landed change trail: what documentation or structure edits actually landed and when.

That split prevents chat-only memory and keeps the repo explainable to both people and agents.

## Quick Reference

| Question | Document |
|----------|----------|
| What survives this conversation? | `CONTINUITY.md` |
| When I change X, what else must change? | `COHERENCE.md` |
| Where does surfaced work live? | `LINEAR.md` section `Linear-at-the-core` |
| What is the repo for? | `PROJECT_INTENT.md` |
| What is the architecture? | `canonical-architecture.md` |
| How does it work conceptually? | `LOGIC.md` |
| What is allowed or forbidden? | `RULES.md` |
| Where does this file go? | `STRUCTURE.md` |
| How do prompts and audits work? | `PROMPTS.md` |
| How does unattended Linear queue execution work? | `QUEUE-RUNS.md` |
| What should be built next? | `IMPLEMENTATION-PLAN.md` |
| Which Superpowers skills fit this repo versus adding overhead? | `docs/superpowers-playbook.md` |
| How should the April 16, 2026 Codex update affect this repo? | `docs/codex-april-16-2026-impact.md` |
| Where do plugin use/not-use and tried/not-tried decisions live? | `docs/codex-april-16-2026-impact.md` section `Plugin decision ledger` |
| How should `Autopilot`, `HOTL`, `Cavekit`, `CodeRabbit`, and `plugin-eval` be split operationally? | `docs/codex-plugin-operator-cheatsheet.md` |
| Where does the repo's CodeRabbit setup live? | `.coderabbit.yaml` |
| Where do the exact CodeRabbit settings and rationale live? | `docs/coderabbit-review-settings.md` |
| Which launch-related pieces are already real vs. still future work? | `docs/launch-plan.md` |
| How do I bootstrap Linear on a new project? | `LINEAR-BOOTSTRAP.md` |
| What should an agent read first? | `AGENTS.md`, then `AGENTS.project.md` |
| How do I find the right file fast? | `GUIDE.md` section `Quick Reference — Where to Find Things` |
| Where are audits, ideas, and feedback decisions recorded? | `todo.md` |
| Where do all live Linear issues get mirrored with why/source? | `todo.md` section `Linear Issue Ledger` |
| What changed recently in the repo? | `todo.md` section `Completed` (index) and `Work Record Log` (full record) |
| Where is the old material? | `design-history/` |
