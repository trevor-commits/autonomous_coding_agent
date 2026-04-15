# Repo Map

This is the fastest lookup document in the repo. Use it when you know what you need and want to find the right file without scanning every markdown document.

## Start Here

If you are new to the repository, read [README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/README.md) first for the high-level orientation, then [GUIDE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/GUIDE.md) for reading order. If you are an agent starting work, read [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md) first, then come back here for file lookup.

## Active Source Of Truth

Use these files for current truth, not the archive:

- [PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md): what the repo is for, who it serves, non-goals, and success criteria.
- [canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md): the authoritative system design.
- [LOGIC.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LOGIC.md): conceptual explanation of system behavior and control flow.
- [RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md): enforceable constraints and stop conditions.
- [STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md): where files belong in this repo, the target repo, and runtime storage.
- [PROMPTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROMPTS.md): prompt-system source of truth.
- [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md): build order, verification expectations, and phase exits.

## Governance And Working Logs

These are the files to use when work changes over time:

- [todo.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/todo.md): active next steps, completed work, audit records, testing evidence, feedback decisions, and suggestion backlog.
- [WORK-LOG.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/WORK-LOG.md): dated summary of concrete documentation and structure changes that landed in the repo.
- [design-history/AUDIT-2026-04-14.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/AUDIT-2026-04-14.md): the most recent Phase 0 cleanup audit report.

When the user gives feedback, requests a plan refinement, or asks for an audit or follow-up change, record the durable decision in `todo.md` instead of leaving it only in chat. `WORK-LOG.md` records what changed; `todo.md` records why, what is next, and what was accepted, deferred, or rejected.

## Schemas And Future Code Surfaces

- [schemas/](/Users/gillettes/Coding Projects/Autonomous Coding Agent/schemas): JSON Schemas for machine-crossing boundaries.
- `supervisor/`: reserved for deterministic runtime code when implementation starts.
- `fixtures/`: reserved for benchmark inputs and reusable validation fixtures.
- `tests/`: reserved for automated tests.
- `prompts/`: reserved for extracted prompt templates if they move out of markdown docs.
- `policies/`: reserved for repo-local policy assets if they become a dedicated surface.

## Design History

Everything historical lives under [design-history/](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history). Read [design-history/README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/README.md) before opening archived material. Those files preserve prior reasoning and draft architectures; they are not implementation authority and may contain superseded terminology or structure assumptions.

## Where To Look By Question

- What is the repo trying to do: `PROJECT_INTENT.md`
- What is the current architecture: `canonical-architecture.md`
- What is allowed or forbidden: `RULES.md`
- Where should a new file go: `STRUCTURE.md`
- How do prompts, audits, and review loops work: `PROMPTS.md`
- What should be built next: `IMPLEMENTATION-PLAN.md`
- What changed recently: `WORK-LOG.md`
- What audits, ideas, or feedback changed the plan: `todo.md`
- Why an older decision was made: `design-history/`
