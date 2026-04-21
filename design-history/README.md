# Design History

This folder holds historical architecture drafts, reconciliation documents, audit records, and ADRs that explain how the current repo state was reached.

These files are useful for context, but they are not the implementation authority. Current truth lives in:

- [../PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md)
- [../canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md)
- [../RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md)
- [../STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md)
- [../GUIDE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/GUIDE.md), especially `Quick Reference — Where to Find Things`

Some archived documents intentionally preserve superseded terminology, layout assumptions, or intermediate design states. That is expected. Treat them as historical evidence, not current operating instructions.

## Contents

- `queue-upgrade-research-2026-04-16.md`: internet-backed rationale, conversation-audit record, and decision memo for the webhook, triage, durability, observability, and eval upgrades to unattended queue execution.
- `codex-update-review-2026-04-16.md`: research pass over the Codex CLI v0.121.0 / v0.122.0-alpha release with a fit evaluation against the repo's authority model and a staged adoption-candidate list gated on Trevor selection.
- `canonical-architecture-synthesis.md`: narrative history of the architecture convergence.
- `FINAL-ARCHITECTURE-DECISION.md`: archived executive summary from the convergence phase.
- `autonomous-agent-system-architecture-review.md`: original architecture review.
- `agent-delegation-architecture-v2.md`: superseded AI-manager orchestration proposal.
- `codex-audit-and-reconciliation.md`: Claude vs. Codex reconciliation document.
- `three-way-reconciliation-final.md`: three-model reconciliation record.
- `feedback-reconciliation-2026-04-14.md`: April 14 feedback and repo-audit reconciliation record.
- `AUDIT-2026-04-14.md`: Phase 0 cleanup verification report.
- `ADR-0001-terminal-state-normalization.md`: current ADR for run-state/readiness vocabulary.
- `ADR-0002-audit-tiebreaker-protocol.md`: accepted protocol for resolving substantive Codex-versus-auditor disagreement with evidence restatement plus Trevor arbitration.
- `ADR-0003-phase-1-architecture-checkpoint.md`: accepted architecture checkpoint after the landed Phase 1 supervisor foundation, including the action-boundary drift repairs required before Phase 2.
- `ADR-0006-linear-authority-boundary.md`: Linear authority boundary audit and governance decision.
- `codex-cleanup-prompts.md`: archived prompt batch that drove the initial Phase 0 cleanup wave.
