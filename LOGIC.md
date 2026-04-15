# System Logic

**Date:** April 12, 2026
**Authority:** `canonical-architecture.md` is the source of truth for all architectural detail. This document explains the logic at a conceptual level — how the system thinks, why it does what it does, and how the pieces connect.

## What This System Does

This system takes a coding objective (a run contract), validates that the target repo is automation-ready (via a repo contract), and then autonomously plans, implements, tests, launches, verifies, and reports on the work — without human intervention between kickoff and result.

While work is active, `run_state = IN_PROGRESS`. For the canonical `run_state` and `readiness_verdict` vocabulary and legality rules, see `canonical-architecture.md §9.1 "Terminal States and Readiness Verdict"`.

## The Central Logic: Who Owns What

The entire system rests on one rule: **the deterministic supervisor owns workflow correctness; AI owns strategy within bounded phases.**

That means the supervisor — ordinary Python code, not a prompt loop — decides:

- what phase the run is in
- what transitions are legal
- whether gates must run
- whether the app must be healthy before UI verification starts
- whether the run can be declared complete
- when to stop

The AI strategy layer decides:

- how to decompose the objective into milestones
- what to tell the builder to do next
- how to interpret a failure
- whether to try a different approach or escalate
- what to look for in a code review

The supervisor asks the AI "what should happen next?" The AI answers by choosing from a menu of typed domain actions the supervisor exposes for the current phase. The supervisor then executes whatever the AI chose — but only if it's legal. The AI never bypasses the supervisor. It never issues raw shell commands, git mutations, or filesystem writes directly. It picks from a bounded action graph.

This split exists because workflow correctness that depends on a model remembering to do the right thing is not workflow correctness — it's hope. The supervisor makes correctness structural.

## The Run Lifecycle

Every run follows the same phase machine. Phases are sequential, with repair loops allowed within certain phases. The supervisor enforces mandatory transitions — no phase can be skipped by the AI or the builder.

### Phase flow:

```
INTAKE
  → validate repo contract + run contract
  → if invalid: `run_state = UNSUPPORTED` (terminal)

PREPARE_WORKSPACE
  → create run directory, worktree, branch
  → acquire single-writer lease
  → initialize state

BUILD
  → ask strategy layer what the builder should do
  → dispatch milestone-scoped work to Codex
  → Codex writes code in exactly one worktree

LOCAL_VERIFY
  → run deterministic gates: format, lint, typecheck, test
  → if pass: checkpoint candidate
  → if fail: fingerprint the failure, route back to BUILD (within retry limit)
  → if repeated same fingerprint beyond threshold: `run_state = BLOCKED`

APP_LAUNCH
  → start app from repo contract commands
  → wait for health endpoint
  → if unhealthy after timeout: route to builder or `run_state = BLOCKED`

UI_VERIFY
  → run Playwright against the live app
  → capture screenshots, traces, console logs, network errors
  → generate structured defect packets for failures
  → if defects exist: route to builder, re-verify (within repair limit)

AUDIT_READY
  → optional: Claude reviews the diff + artifacts
  → structured findings with severity codes

FINAL_GATE
  → rerun authoritative required gates
  → verify all required artifacts exist
  → confirm no unresolved high-severity findings
  → emit `readiness_verdict = READY`, `readiness_verdict = NOT_READY`, or `readiness_verdict = NEEDS_MORE_EVIDENCE`
  → if `readiness_verdict = NEEDS_MORE_EVIDENCE` and the evidence loop budget remains: gather more evidence and re-run FINAL_GATE
  → if `readiness_verdict = READY` and the legality invariant passes: `run_state = COMPLETE` (terminal)
  → else: `run_state = BLOCKED` (terminal)
```

The repair loops (BUILD ↔ LOCAL_VERIFY, BUILD ↔ UI_VERIFY) are where most of the autonomous work happens. The supervisor counts retries, fingerprints failures, and enforces ceilings. If the same failure keeps recurring, the system escalates or blocks rather than spinning forever.

## How Delegation Works

Delegation in this system means the AI strategy layer chooses which worker should act next, shapes the prompt for that worker, interprets failures, and re-plans based on evidence. It does not mean the AI owns phase transitions, skips required gates, or declares completion without deterministic evidence.

The delegation flow within a BUILD phase looks like this:

1. Supervisor enters BUILD phase and asks strategy layer: "What should the builder do next?"
2. Strategy layer returns a typed action: `request_builder_task` with a scoped prompt and milestone ID.
3. Supervisor validates the action is legal for the current phase.
4. Supervisor dispatches the task to the Codex builder via the builder adapter.
5. Codex writes code in the worktree.
6. Supervisor automatically transitions to LOCAL_VERIFY (because the phase requires it — this is not the AI's decision).
7. Supervisor runs deterministic gates.
8. If gates fail, supervisor asks strategy layer: "This failed. What should the builder try differently?"
9. Strategy layer returns either a new `request_builder_task` (different approach) or `propose_terminal_state` with `run_state = BLOCKED` (giving up).
10. Loop continues within retry budget.

The key insight: the supervisor asks the AI questions at defined decision points. The AI never tells the supervisor "now run hooks" or "now commit." The supervisor already knows when to do those things because it owns the phase machine.

## The Typed Action Graph

The AI strategy layer communicates with the supervisor through typed domain actions, not raw commands. This is how delegation stays bounded.

Legal action families:

- `collect_context` — gather information about the repo state
- `request_builder_task` — ask the builder to implement something
- `run_contract_command` — run a repo-contract-defined command (by name, not arbitrary shell)
- `launch_app` / `stop_app` — app lifecycle
- `run_ui_suite` — trigger Playwright verification
- `checkpoint_candidate` — request a checkpoint commit
- `rollback_to_checkpoint` — revert to a known-good state
- `record_failure_signature` — log a failure fingerprint
- `record_decision` — log a strategic decision for audit trail
- `propose_terminal_state` — suggest a terminal `run_state` such as `COMPLETE`, `BLOCKED`, or `UNSUPPORTED` (supervisor still validates)

Each action is legal only in specific phases. The supervisor rejects actions that don't belong to the current phase. Actions resolve to supervisor-controlled implementations — the AI never passes arbitrary shell strings through the action graph.

## Contracts: How the System Knows What a Repo Can Do

The system does not improvise a repo's lifecycle. Two contracts define the automation surface:

**Repo contract** (`.agent/contract.yml`) — stable, version-controlled target-repo truth in the target repo's `.agent/` surface, describing how that repo works: setup, test, lint, typecheck, app launch, health check, UI smoke, critical flows, environment variables. If the minimum required fields (setup, test, app_up, app_health) are missing, the run ends with `run_state = UNSUPPORTED`. This is intentional — "unsupported" is better than "improvised and wrong."

**Run contract** (JSON, per-task) — operational, per-run, describes what this specific task requires: objective, allowed/forbidden file paths, acceptance criteria, quality gates, UI checks, budget constraints (max iterations, max cost, hard timeout). The run contract is what makes each run scoped and auditable.

## Single-Writer Isolation

Only one agent writes code per run. Codex gets exactly one writable worktree. No other agent — not Claude, not Playwright, not the reviewer — can mutate files in the worktree. The supervisor enforces this with a lease mechanism.

Codex edits files but does not commit. The supervisor owns checkpoint commits. This ensures commits represent intentional checkpoints (known-good or explicitly recorded states), not partial broken work that happened to be in the worktree when the builder stopped.

## Single-Browser-Owner Isolation

Only Playwright owns the browser. One isolated browser profile per run, localhost-only access, no state carried from prior runs. The builder cannot control the browser. The reviewer cannot control the browser. This prevents two agents from fighting over browser state and eliminates an entire class of race conditions.

## Failure Handling Logic

The system classifies failures into five categories: code failures (the builder's code is wrong), harness failures (the supervisor or adapter broke), environment failures (dependencies, network, OS), fixture failures (test data or seed state), and unsupported repo conditions (missing contract fields, missing commands).

For each failure, the supervisor:

1. Fingerprints the failure (phase + command + normalized error signature + relevant paths).
2. Checks if this fingerprint has been seen before in this run.
3. If repeated beyond threshold: escalate to stall diagnosis or block.
4. If novel: route back to builder with the structured failure details.
5. Records the failure in the run's execution log and defect directory.

Failure fingerprinting prevents the most common autonomous-system antipattern: trying the same broken thing in a loop. If the builder has failed three times with the same error, the strategy layer is asked for a different approach, not the same one again.

## Verification Logic

Verification is layered and ordered. The system never runs UI verification before code gates pass, and never runs code gates before the builder says it's done with a milestone.

The ordering is: deterministic code gates → app health → deterministic UI checks → optional model-judged UI quality → final deterministic readiness gate.

The target split for UI verification is 80-90% deterministic (route availability, click success, console cleanliness, network correctness) and 10-20% model-judged (semantic layout mismatches, polish issues, subjective correctness). Model judgment is the exception, not the default.

## Memory Logic

The system uses three tiers of memory, each with a different lifecycle:

**Repo truth** — version-controlled files in the repo (contract, ADRs, AGENTS.md, conventions). Stable, human-managed, survives across all runs.

**Run truth** — per-run state and artifacts in the supervisor-owned runtime workspace at `.autoclaw/runs/<run_id>/`. Created at run start, written throughout, preserved after completion, and gitignored rather than committed in either repo. It contains the contract, plan, state file, defect packets, screenshots, traces, logs, and final report. It is ephemeral to the run but preserved for post-mortem.

**Operational memory** — cross-run learnings in the supervisor-owned runtime workspace at `.autoclaw/memory/`. Failure signatures, flaky test registry, environment quirks, and prior fix strategies are built up automatically over time and remain gitignored runtime state rather than committed repo structure. This data is subject to TTL (stale entries archived after 30 days). This is what makes the system get better with repeated use — a failure that was diagnosed and fixed in run 7 can inform the builder's approach in run 12.

No raw transcript storage. No chain-of-thought preservation. No external semantic memory system in v1. File-based operational memory is sufficient until volume proves otherwise.

## Stop Logic

The supervisor stops or blocks when:

- The repo contract is insufficient (`run_state = UNSUPPORTED`).
- A required command is missing or unsupported.
- The same failure fingerprint exceeds the retry threshold.
- App health does not stabilize within timeout.
- Budget is exhausted (iterations, cost, or wall-clock time).
- Path or command restrictions are violated.
- An unresolved high-severity review finding remains at final gate.

Stop conditions are enforced by the supervisor, not by the AI strategy layer. The AI cannot override them.

## Reporting Logic

Every run produces two outputs: a machine-readable JSON report (`run_id`, `run_state`, `readiness_verdict`, `phases_completed`, `commands_run`, `failures`, `changed_files`, `checkpoint_refs`, `artifact_manifest`, `unresolved_blockers`) and a human-readable markdown summary (what changed, what passed, what failed, what's unresolved, what to do next).

These are generated by the supervisor's report module after the run reaches a terminal state. The report is written to the run directory and is the primary deliverable of a completed run.

## How This All Connects

```
Human writes run contract
  → Supervisor validates repo contract + run contract
  → Supervisor creates worktree + run store
  → Supervisor asks AI strategy layer: "Decompose this objective"
  → AI returns milestone plan using typed actions
  → For each milestone:
      Supervisor asks AI: "What should the builder do?"
      → AI returns request_builder_task
      → Supervisor dispatches to Codex
      → Codex writes code
      → Supervisor runs deterministic gates
      → If fail: AI diagnoses, adjusts approach, builder retries
      → If pass: Supervisor creates checkpoint commit
  → Supervisor launches app
  → Supervisor runs Playwright
  → If UI defects: routed to builder, re-verified
  → Supervisor runs final gate
  → Supervisor produces report
  → Terminal run_state: `COMPLETE`, `BLOCKED`, or `UNSUPPORTED`
```

The supervisor is the spine. The AI is the brain for strategy. The builder is the hands. The verifier is the eyes. The reviewer is the auditor. Each has exactly one job, bounded permissions, and no ability to override the others.
