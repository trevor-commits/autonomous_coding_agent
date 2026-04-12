# Final Architecture Decision — Archived Summary

**Date:** April 12, 2026
**Status:** Historical summary, superseded as implementation authority
**Current authority:** `canonical-architecture.md`
**Authority:** Trevor (human operator) makes final call on implementation

---

## One-Sentence Summary

Deterministic supervisor at the center, Claude as bounded strategy and audit, Codex as sole writer, Playwright as sole browser owner, repo contract + run contract as admission control, structured artifacts and failure fingerprints as shared operational memory.

## Status Note

This document remains a useful executive summary of the converged architecture discussion, but it is no longer the source of truth for implementation work.

Use these files instead:

1. `canonical-architecture.md` — source of truth
2. `AGENTS.md` — repo-local operating instructions
3. `README.md` — document index and orientation

---

## The Design

```
Human kickoff
  → Repo contract validator (.agent/contract.yml)
  → Deterministic Supervisor (Python)
       - phase state machine
       - worktree manager (single writer)
       - command/policy engine (allow/deny/escalate)
       - app supervisor
       - artifact store
       - checkpoint manager (supervisor owns commits)
       - readiness checker
       - decision API (typed domain actions)
            → Claude strategy layer (plan / decompose / stall diagnose / audit)
            → Codex builder adapter (sole writer, one writable worktree)
            → Playwright verifier (sole browser owner, defect packets)
  → Final report + READY / NOT_READY / BLOCKED
```

---

## Hard Ownership Rules

### Supervisor owns:
- Phase transitions (INTAKE → PLAN → BUILD → VERIFY → LAUNCH → UI_VERIFY → AUDIT → GATE → COMPLETE/BLOCKED)
- Worktree creation and single-writer lock
- App lifecycle (launch, health check, shutdown)
- Checkpoint commits (builder edits files, supervisor commits)
- Final readiness decision
- Artifact and report generation
- Budget/timeout enforcement
- Command policy (allow/deny/escalate)

### Claude strategy layer owns:
- Task decomposition into milestones
- Builder prompt crafting (what to tell Codex)
- Retry strategy within budget (try different approach vs same approach)
- Stall diagnosis (when builder is stuck)
- Review timing proposals
- Audit findings (severity-coded, actionable)

### Codex owns:
- Code edits in exactly one writable worktree
- Local targeted checks during implementation (lint, typecheck, test)
- Does NOT commit (supervisor commits on checkpoint)
- Does NOT control browser
- Does NOT own phase transitions

### Playwright owns:
- Browser session (one profile per run, isolated)
- Screenshots, traces, console logs, network capture
- Structured defect packets (JSON, not prose)
- Does NOT edit code
- Does NOT commit

### Reviewer (Claude, separate instance) owns:
- Read-only audit on diff + evidence
- Severity-coded findings
- Does NOT write code
- Does NOT own completion authority

---

## Key Design Decisions (Sourced)

| Decision | Source | Why |
|----------|--------|-----|
| Deterministic supervisor as center | Codex + ChatGPT Pro, Claude conceded | Workflow correctness must be system-enforced, not prompt-dependent |
| Typed domain actions, not raw shell | ChatGPT Pro | Prevents AI from re-taking control path via side door |
| Repo contract required | ChatGPT Pro | "Unsupported" > "improvise" — makes autonomy real |
| Run contract per task (JSON) | Codex | Machine-readable scope, acceptance, constraints |
| Structured defect packets (JSON) | Codex | Eliminates vague reviewer prose |
| Executor owns commits | ChatGPT Pro | Clean checkpoint semantics, builder cannot commit half-broken code |
| Three shell classes: allow/deny/escalate | ChatGPT Pro | Middle ground for sometimes-safe commands |
| App supervisor as separate concern | Codex + ChatGPT Pro | Infrastructure != cognition |
| Claude as bounded strategy, not traffic cop | All three (Claude conceded) | AI owns WHAT and HOW; supervisor owns WHEN and WHETHER |
| No OpenClaw in v1 | Claude + ChatGPT Pro | Gateway crash issues, wrong center for delivery harness |
| acpx behind adapter, not foundational | ChatGPT Pro | Useful but swappable; alpha software risk |
| No Gemini in v1 | All three | No clear non-redundant role |
| No Zep in v1 | All three | File-based memory sufficient until volume proves otherwise |
| Single writer per worktree | All three | Non-negotiable isolation |
| 80/20 deterministic/model-judged UI split | All three | Model judgment for ambiguity only |

---

## Strategy API Interface

The Claude strategy layer does NOT emit raw actions. It chooses from typed domain actions the supervisor exposes for the current phase:

```python
# Correct — typed domain actions
{"action": "request_builder_task", "prompt": "...", "milestone": "M2"}
{"action": "run_contract_command", "name": "test", "scope": "targeted"}
{"action": "checkpoint_candidate", "reason": "M2 gates passed"}
{"action": "record_failure_signature", "fingerprint": "...", "evidence_refs": [...]}
{"action": "propose_terminal_state", "state": "COMPLETE", "summary": "..."}

# Wrong — raw shell/git (NOT allowed)
{"type": "run_hook", "command": "npm run test -- --bail"}
{"type": "git_command", "command": "git add -A && git commit -m 'done'"}
{"type": "write_memory", "path": "...", "content": "..."}
```

---

## Memory Model (Three-Tier)

| Tier | Location | Contents | Managed By |
|------|----------|----------|-----------|
| Repo truth | In repo, version-controlled | ADRs, repo contract, AGENTS.md, conventions | Human + supervisor |
| Run truth | `.autoclaw/runs/<id>/` | state.json, defects/, artifacts/, reports/ | Supervisor |
| Operational memory | `.autoclaw/memory/` | failure-signatures.json, flaky-tests.json, env-quirks.md, fix-strategies.json | Supervisor (after runs) |
| Ephemeral | In-memory + state.json | Current phase, hypothesis, transient logs | Supervisor (per run) |

---

## Build Order

1. Repo contract for target repo (.agent/contract.yml)
2. Deterministic supervisor + run store (Codex builds this — use ChatGPT Pro's prompt)
3. Codex builder adapter + single-writer worktree loop
4. Validate build → verify → checkpoint with manual decisions
5. Claude strategy API integration (Claude designs this)
6. App supervisor + Playwright + defect packets
7. Claude audit + readiness gate
8. Cross-run memory (only after repeated failure data exists)

---

## Documents Produced During This Design Review

1. `autonomous-agent-system-architecture-review.md` — Foundation (stack, roles, branch strategy, auth, cost, failures, MVP, roadmap)
2. `agent-delegation-architecture-v2.md` — Delegation model (superseded in orchestration approach, still valid for prompt library and delegation patterns)
3. `codex-audit-and-reconciliation.md` — Claude vs Codex reconciliation + adopted schemas
4. `three-way-reconciliation-final.md` — Three-model merge (scorecard, contracts, phasing)
5. `FINAL-ARCHITECTURE-DECISION.md` — Historical executive summary of the converged design discussion.

---

## What Remains Valid From Earlier Documents

- Agent prompts and delegation patterns from v2 (will be adapted to typed domain actions)
- Defect packet schema from Codex audit
- Run contract schema from Codex audit
- Repo contract from ChatGPT Pro (simplified for v1)
- Failure mode matrix from foundation document
- Cost strategy from foundation document
- Phased roadmap (adjusted: Claude enters after executor is validated)

---

## Next Actions

| Who | Does What |
|-----|----------|
| **Trevor** | Writes repo contract for target repo. Writes 3-5 benchmark run contracts. Uses `canonical-architecture.md` as the source of truth for implementation sequencing. |
| **Codex** | Builds deterministic supervisor foundation first, then the single-writer builder loop, following `canonical-architecture.md`. |
| **Claude** | Designs the bounded strategy layer for `get_strategy_decision()` after the supervisor foundation and single-builder loop are validated. Audits implementation output against `canonical-architecture.md`. |
| **ChatGPT Pro** | Available for second opinion on schemas, contracts, or adversarial review of built components. |
