# Autonomous Coding Agent

This repository holds the active source-of-truth documentation, planning artifacts, schemas, and governance records for an autonomous coding system. Historical drafts and reconciliation material are archived under `design-history/` so the root stays focused on current guidance.

## Start Here

Read [CONTINUITY.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/CONTINUITY.md) and [COHERENCE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/COHERENCE.md) first. They state the root-level assumptions that every other rule in this repo depends on. [LINEAR.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR.md) section `Linear-at-the-core` is the third pillar.

- Need reading order, document roles, and file lookup: [GUIDE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/GUIDE.md), especially `Quick Reference — Where to Find Things`
- Agent session bootstrap: [AGENTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.md), then [AGENTS.project.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/AGENTS.project.md) for the authoritative repo-local overlay

## Active Docs

Read these when working on the current system:

1. [CONTINUITY.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/CONTINUITY.md)
   Root-level continuity principle: what must be written, signed, and pointed to before work survives the conversation that produced it.

2. [COHERENCE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/COHERENCE.md)
   Root-level coherence principle: Ripple Check, Dependency Map, and same-commit propagation for live-doc changes.

3. [PROJECT_INTENT.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROJECT_INTENT.md)
   What the repo is for, who it serves, what is out of scope, and how success is judged.

4. [canonical-architecture.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/canonical-architecture.md)
   Source of truth. Build from this.

5. [LOGIC.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LOGIC.md)
   Conceptual explanation of how the system behaves.

6. [RULES.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/RULES.md)
   Enforceable constraints and stop conditions.

7. [STRUCTURE.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/STRUCTURE.md)
   File placement, repo boundary, runtime-state placement, and archive boundary.

8. [PROMPTS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/PROMPTS.md)
   Prompt-system source of truth.

9. [IMPLEMENTATION-PLAN.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/IMPLEMENTATION-PLAN.md)
   Build order, verification expectations, and phase exits.

10. [docs/superpowers-playbook.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/superpowers-playbook.md)
   Repo-specific guidance for when Superpowers skills help in this
   documentation-first architecture/governance repo and when they add overhead.

11. [docs/codex-april-16-2026-impact.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/codex-april-16-2026-impact.md)
   Repo-local impact memo for the April 16, 2026 Codex update and the ongoing
   plugin decision ledger, including what to adopt now, what to defer for v1,
   and where future plugin use/not-use decisions should be updated.

12. [docs/codex-plugin-operator-cheatsheet.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/codex-plugin-operator-cheatsheet.md)
   Operational split for `Autopilot`, `HOTL`, `Cavekit`, `CodeRabbit`, and
   `plugin-eval`, plus the current shortlist of further plugin candidates worth
   spiking later.

13. [docs/coderabbit-review-settings.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/coderabbit-review-settings.md)
   Exact CodeRabbit settings, UI caveats, path instructions, and the
   repo-specific rationale behind the current review-trial posture.

14. [docs/launch-plan.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/launch-plan.md)
   Reconciles which launch-related lanes are already present as process/spec and which are still future implementation work.

15. [docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md)
   Approved design baseline for the first runnable local single-run supervisor
   slice, aligned to the supervisor foundation already landed in `supervisor/`.

16. [LINEAR.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR.md)
   Linear governance for this repo. The board is routing metadata only; repo docs remain authoritative.

17. [QUEUE-RUNS.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/QUEUE-RUNS.md)
   Exact operating contract for unattended supervisor-mediated queue execution of Linear issues.

18. [LINEAR-BOOTSTRAP.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/LINEAR-BOOTSTRAP.md)
   Linear setup runbook for new projects. Use when bootstrapping Linear from scratch.

19. [todo.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/todo.md)
   Active queue, suggestion backlog, audit trail, test evidence, and feedback decisions.

## Design History

Archived drafts, reconciliation docs, old architecture summaries, and audit records now live under [design-history/](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history). Start with [design-history/README.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/README.md) before opening historical documents.

Latest queue-upgrade rationale and conversation-audit record: [design-history/queue-upgrade-research-2026-04-16.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/design-history/queue-upgrade-research-2026-04-16.md)

## Feedback, Audits, And Idea Tracking

This repo keeps durable governance records instead of leaving them in chat:

- `todo.md` `Active Next Steps`: execution-ready work
- `todo.md` `Linear Issue Ledger`: every live Linear issue, its repo-side home, why it exists, and where it came from
- `todo.md` `Work Record Log`: what would otherwise be lost between conversations
- `todo.md` `Completed`: one-line landing index
- `todo.md` `Suggested Recommendation Log`: deferred or optional ideas
- `todo.md` `Audit Record Log`: audits and review outcomes
- `todo.md` `Feedback Decision Log`: requests, plan refinements, accepted/rejected guidance

## Review Tooling

This repo's CodeRabbit PR-review config lives at
[.coderabbit.yaml](/Users/gillettes/Coding Projects/Autonomous Coding Agent/.coderabbit.yaml).
Use it as the repo-local source for CodeRabbit review behavior. GitHub App
installation and authorization remain a manual operator step outside the repo.
The detailed settings rationale, UI caveats, and field-by-field review posture
live in
[docs/coderabbit-review-settings.md](/Users/gillettes/Coding Projects/Autonomous Coding Agent/docs/coderabbit-review-settings.md).

## Current Direction

The settled architecture is a deterministic supervisor with a bounded AI strategy layer, Codex as sole writer, Playwright as sole browser owner, contract-driven automation, structured evidence for readiness decisions, and supervisor-mediated unattended queue execution that treats Linear as routing metadata rather than a command surface. The current queue direction is webhook-first intake, pre-queue normalization, explicit risk and approval gates, and trace-linked observability plus eval evidence before autonomy expands.

## Next Build Focus

The next implementation work should follow the phased plan in `canonical-architecture.md`, starting with:

1. deterministic supervisor foundation
2. single-writer builder loop
3. app supervisor and UI verification
4. bounded strategy-layer integration
5. contract-driven CI integration in the first implementation repo after the local flow is proven
