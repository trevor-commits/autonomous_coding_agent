# Autonomous Coding Agent

This repository currently contains the architecture and implementation-planning documents for an autonomous multi-agent coding system.

## Document Order

New here? Start with `GUIDE.md` — it explains what every document is and when to read it.

Agents: read `AGENTS.md` immediately after this file. The numbered order below is the human onboarding path for understanding the architecture and its companion docs.

Otherwise, read these in this order:

1. `canonical-architecture.md`
   Source of truth. Build from this.

2. `LOGIC.md`
   Conceptual explanation of how the system works — the run lifecycle, delegation model, failure handling, verification logic, memory tiers, and how all the pieces connect. Read this to understand the *why* behind the architecture.

3. `RULES.md`
   Every enforceable rule in the system — ownership boundaries, forbidden operations, shell policy, contract requirements, phase transition rules, stop conditions, permission model, and v1 exclusions. Read this to know what is and is not allowed.

4. `PROMPTS.md`
   The prompt operating system — how prompts should be designed, sequenced, reviewed, re-audited, and tied to deterministic testing. Includes the prompt library for both building the platform and operating it.

5. `STRUCTURE.md`
   Where things go and where to find them. Explains every folder in the repo and the target repo, what belongs in each, who manages it, and when it gets created. Keep this updated as folders are added.

6. `AGENTS.md`
   Repo-local instructions for future agents working in this repository.

7. `IMPLEMENTATION-PLAN.md`
   What to build, in what order, who builds it, how to verify each step. The execution roadmap.

8. `canonical-architecture-synthesis.md`
   Design history and explanation of how the architecture converged.

## Design-History Documents

These remain useful for context, but they are not the implementation authority:

- `FINAL-ARCHITECTURE-DECISION.md`
- `autonomous-agent-system-architecture-review.md`
- `agent-delegation-architecture-v2.md`
- `codex-audit-and-reconciliation.md`
- `three-way-reconciliation-final.md`

Use them as history, not as the final architectural target.

## Current Direction

The settled architecture is:

- deterministic supervisor at the center
- bounded AI strategy layer
- Codex as sole writer
- Claude as planner / stall diagnoser / auditor
- Playwright as sole browser owner
- repo contract + run contract as the automation interface
- structured artifacts and defect packets as the evidence model

## Next Build Focus

The next implementation work should follow the phased plan in `canonical-architecture.md`, starting with:

1. repo contract for the first supported repo
2. deterministic supervisor foundation
3. single-writer builder loop
4. app supervisor and UI verification
5. bounded strategy-layer integration
