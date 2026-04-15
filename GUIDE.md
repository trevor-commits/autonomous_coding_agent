# Document Guide

**Date:** April 14, 2026
**Purpose:** Explain how the repo is organized now that active source-of-truth docs and archived history are separated.

## Fastest Paths

If you are trying to find a file quickly, start with [REPO_MAP.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/REPO_MAP.md). If you want the recommended reading order and document roles, stay here. If you are an agent beginning a session, read [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md) first and then use `REPO_MAP.md` for lookup.

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

### [REPO_MAP.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/REPO_MAP.md)

The fastest lookup reference. Read this when you know what you want and need the right file immediately.

## Working Governance Records

### [todo.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/todo.md)

This is the durable working record for the project. It holds the active queue, completed work trail, suggested ideas, audit log, test evidence, and feedback decisions.

### [WORK-LOG.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/WORK-LOG.md)

This is the dated record of what landed in the repo. Use it to see which documentation or structure changes were actually made.

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
- Use `WORK-LOG.md` for the change trail: what documentation or structure edits actually landed and when.

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
| How do I find the right file fast? | `REPO_MAP.md` |
| Where are audits, ideas, and feedback decisions recorded? | `todo.md` |
| What changed recently in the repo? | `WORK-LOG.md` |
| Where is the old material? | `design-history/` |
