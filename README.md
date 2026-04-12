# Autonomous Coding Agent

This repository currently contains the architecture and implementation-planning documents for an autonomous multi-agent coding system.

## Document Order

Read these in this order:

1. `canonical-architecture.md`
   Source of truth. Build from this.

2. `AGENTS.md`
   Repo-local instructions for future agents working in this repository.

3. `canonical-architecture-synthesis.md`
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
