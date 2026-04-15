# Autonomous Coding Agent

This repository holds the active source-of-truth documentation, planning artifacts, schemas, and governance records for an autonomous coding system. Historical drafts and reconciliation material are archived under `design-history/` so the root stays focused on current guidance.

## Start Here

- Need reading order, document roles, and file lookup: [GUIDE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/GUIDE.md), especially `Quick Reference — Where to Find Things`
- Agent session bootstrap: [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md)

## Active Docs

Read these when working on the current system:

1. [PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md)
   What the repo is for, who it serves, what is out of scope, and how success is judged.

2. [canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md)
   Source of truth. Build from this.

3. [LOGIC.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LOGIC.md)
   Conceptual explanation of how the system behaves.

4. [RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md)
   Enforceable constraints and stop conditions.

5. [STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md)
   File placement, repo boundary, runtime-state placement, and archive boundary.

6. [PROMPTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROMPTS.md)
   Prompt-system source of truth.

7. [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md)
   Build order, verification expectations, and phase exits.

8. [LINEAR.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR.md)
   Linear governance for this repo. The board is routing metadata only; repo docs remain authoritative.

9. [todo.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/todo.md)
   Active queue, suggestion backlog, audit trail, test evidence, and feedback decisions.

## Design History

Archived drafts, reconciliation docs, old architecture summaries, and audit records now live under [design-history/](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history). Start with [design-history/README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/README.md) before opening historical documents.

## Feedback, Audits, And Idea Tracking

This repo keeps durable governance records instead of leaving them in chat:

- `todo.md` `Active Next Steps`: execution-ready work
- `todo.md` `Suggested Recommendation Log`: deferred or optional ideas
- `todo.md` `Audit Record Log`: audits and review outcomes
- `todo.md` `Feedback Decision Log`: requests, plan refinements, accepted/rejected guidance
- `todo.md` `Completed`: what changed in the repo itself

## Current Direction

The settled architecture is a deterministic supervisor with a bounded AI strategy layer, Codex as sole writer, Playwright as sole browser owner, contract-driven automation, and structured evidence for readiness decisions.

## Next Build Focus

The next implementation work should follow the phased plan in `canonical-architecture.md`, starting with:

1. deterministic supervisor foundation
2. single-writer builder loop
3. app supervisor and UI verification
4. bounded strategy-layer integration
5. contract-driven CI integration in the first implementation repo after the local flow is proven
