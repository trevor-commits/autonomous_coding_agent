# Document Guide

**Date:** April 14, 2026
**Purpose:** Explain how the repo is organized now that active source-of-truth docs and archived history are separated.

## Quick Reference — Where to Find Things

If you are an agent beginning a session, read [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md) first. If you are orienting as a human, start with [README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/README.md) and then use this guide for reading order and lookup.

Use these files for current truth:

- [PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md): repo purpose, primary users, non-goals, success criteria.
- [canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md): authoritative architecture.
- [LOGIC.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LOGIC.md): conceptual behavior and control flow.
- [RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md): enforceable constraints and stop conditions.
- [STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md): file placement, repo boundary, runtime-state placement.
- [PROMPTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROMPTS.md): prompt-system source of truth.
- [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md): build order and phase verification.

Use `todo.md` for durable working records:

- `Active Next Steps`: execution-ready work
- `Suggested Recommendation Log`: deferred or optional ideas
- `Audit Record Log`: audits and findings
- `Test Evidence Log`: verification runs and results
- `Feedback Decision Log`: plan refinements, accepted guidance, rejected guidance
- `Completed`: durable record of landed milestones and repo changes

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

### [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md)

The execution roadmap. Read this when deciding what phase comes next or how a milestone is verified.

### [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md)

Repo-local working instructions for agents. Read this at the start of an agent session.

### [README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/README.md)

The front page. Read this first when landing in the repo without context.

## Working Governance Records

### [todo.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/todo.md)

This is the durable working record for the project. It holds the active queue, completed work trail, suggested ideas, audit log, test evidence, and feedback decisions.

## Design History

Everything historical now lives under [design-history/](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history). Start with [design-history/README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/README.md) before reading archived material. Those files preserve prior reasoning and may contain superseded terminology or file-layout assumptions by design.

Key historical records:

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

- Use `todo.md` for the decision trail: active work, suggested ideas, audit outcomes, test evidence, and feedback decisions.
- Use `todo.md`'s `Completed` section for the landed change trail: what documentation or structure edits actually landed and when.

That split prevents chat-only memory and keeps the repo explainable to both people and agents.

## Quick Reference

| Question | Document |
|----------|----------|
| What is the repo for? | `PROJECT_INTENT.md` |
| What is the architecture? | `canonical-architecture.md` |
| How does it work conceptually? | `LOGIC.md` |
| What is allowed or forbidden? | `RULES.md` |
| Where does this file go? | `STRUCTURE.md` |
| How do prompts and audits work? | `PROMPTS.md` |
| What should be built next? | `IMPLEMENTATION-PLAN.md` |
| What should an agent read first? | `AGENTS.md` |
| How do I find the right file fast? | `GUIDE.md` section `Quick Reference — Where to Find Things` |
| Where are audits, ideas, and feedback decisions recorded? | `todo.md` |
| What changed recently in the repo? | `todo.md` section `Completed` |
| Where is the old material? | `design-history/` |
