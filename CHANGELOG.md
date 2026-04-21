# Changelog

## 2026-04-21

- Landed `GIL-11` / `ADR-0005`:
  - added the Codex conversation-lifecycle decision under `design-history/ADR-0005-codex-conversation-lifecycle.md`
  - codified required new-conversation triggers, permitted same-conversation exceptions, and the round-3 restart rule
  - tightened the repo's live handoff/governance surfaces so "fresh conversation" points to an explicit accepted boundary instead of a vague guideline

## 2026-04-19

- Merged the `codex/gil29-ui-verifier` runtime line into `main`:
  - added the first `GIL-23` benchmark fixture suite under `fixtures/`
  - added the first `GIL-29` app-launch and UI-verification slice with `supervisor/app_supervisor.py` and `supervisor/ui_verifier.py`
  - brought forward the `GIL-59` through `GIL-62` Phase 3 repair wave
  - closed the `GIL-69` through `GIL-71` follow-up audit gaps by enforcing run budgets, rejecting `repo_path` mismatches, and preserving all UI failure fingerprints in retry/report state
- Started the first `GIL-30` bounded-Claude strategy slice:
  - added `supervisor/strategy_claude.py` with Anthropic Messages API transport, typed-action parsing, prompt-pack rendering, per-run planner routing, and fallback to the simple strategy
  - materialized the first Phase 4 prompt pack under `supervisor/prompts/`
  - wired `supervisor/main.py` to accept `--strategy claude` while keeping the supervisor in control of legality and fallback behavior
  - added targeted unit coverage for Claude strategy prompt routing, fallback handling, usage accounting, and main-loop compatibility
- Extended `GIL-30` into the review/final-gate path:
  - wired `AUDIT_READY` candidate review and `FINAL_GATE` final-audit decisions into `execute_run`
  - allowed review-driven `request_builder_task` actions during `AUDIT_READY` and `FINAL_GATE`
  - fixed backend-only review flow so green no-UI candidates can legally pause in `AUDIT_READY`
  - stopped treating historical repaired fingerprints as unresolved final-gate blockers
  - added focused coverage for review-requested rebuilds, final-audit blocks, and the widened phase/action legality
- Extended `GIL-30` into trace-backed benchmark grading:
  - added per-run benchmark metrics to readiness reports (`strategy_name`, `builder_turns`, `run_duration_seconds`, `total_cost_dollars`)
  - added `supervisor/benchmark_eval.py` to compare benchmark report sets and render markdown or JSON summaries
  - added focused coverage for report-metric emission, historical-report compatibility, and benchmark comparison summaries
- Completed the first live `GIL-30` benchmark-proof pass:
  - hardened the builder timeout path so missing builder worktrees degrade to a blocked run instead of an adapter crash
  - recorded eight paired live benchmark artifacts for `benchmark-001` through `benchmark-004` under `design-history/artifacts/gil30-benchmark-comparison-2026-04-19/`
  - captured the current Phase 4 result in durable comparison summaries: both `simple` and `claude` timed out after one builder turn on every positive fixture, so no Claude-only wins are proven under the current builder lane

## 2026-04-20

- Landed `GIL-10` / `ADR-0004`:
  - added the ChatGPT Pro strategic-audit cadence under `design-history/ADR-0004-chatgpt-pro-strategic-audit-cadence.md`
  - codified the phase-boundary, Phase 1 checkpoint, quarterly, and ad hoc audit triggers for Pro
  - recorded the required audit-brief shape, output format, and `ADR-0002` disagreement path
- Landed `GIL-8` / `ADR-0002`:
  - added the audit tiebreaker protocol under `design-history/ADR-0002-audit-tiebreaker-protocol.md`
  - indexed the ADR from the design-history guide surfaces
  - updated the durable queue so `GIL-8` is closed and the deferred `GIL-30` builder-envelope revisit remains recorded for later

## 2026-04-17

- Added the first `GIL-57` manual queue-intake slice:
  - added `supervisor/queue_intake.py` with Linear issue parsing, eligibility filtering, local claim storage, run-contract normalization, a manual drain runner, and a GraphQL-backed Linear client
  - extended `supervisor/verifier.py` and the run-contract schema/parser so queue-normalized verification packs can constrain deterministic gates per issue-run
  - extended `supervisor/main.py` with a manual `--queue-drain` entrypoint alongside the existing single-run path
  - documented the queue-mode issue metadata needed for the first manual drain slice in `QUEUE-RUNS.md` and `LINEAR.md`
  - added queue-focused supervisor coverage in `tests/test_queue_intake.py`
- Added the first `GIL-28` builder-loop slice:
  - added a real Codex CLI builder adapter in `supervisor/builder_adapter.py`
  - added a minimal rule-based builder strategy in `supervisor/strategy_simple.py`
  - added the first runnable supervisor main loop in `supervisor/main.py`
  - added integration tests for session reuse, build -> verify -> retry, and policy blocking
- Recorded the `GIL-9` architecture-checkpoint repair:
  - repaired strategy action payload drift from `task_description` / `command_name` to `description` / `name`
  - narrowed `schemas/strategy-decision.schema.json` to the current smallest-v1 action surface
  - updated `LOGIC.md` and `RULES.md` to remove stale checkpoint/failure-signature strategy actions
  - added `design-history/ADR-0003-phase-1-architecture-checkpoint.md`

## 2026-04-16

- Added the first `GIL-27` verification-and-reporting slice:
  - added deterministic verification runners in `supervisor/verifier.py`
  - added run-local failure fingerprint persistence in `supervisor/fingerprints.py`
  - added final JSON + markdown report generation in `supervisor/reports.py`
  - normalized readiness and failure-fingerprint schemas to the current snake_case runtime contract
  - added unit coverage for verifier, fingerprinting, and report generation
- Added the first `GIL-26` contract-and-guardrails slice:
  - split repo-contract and run-contract schemas into distinct machine boundaries
  - added repo/run contract parsing in `supervisor/contracts.py`
  - added `.autoclaw/runs/<run_id>/` storage scaffolding in `supervisor/run_store.py`
  - added shell/path/budget policy enforcement in `supervisor/policy.py`
  - added builder worktree + single-writer lease management in `supervisor/worktree_manager.py`
  - added unit coverage for contract parsing, policy decisions, run-store creation, and worktree discipline
- Added the first `GIL-25` supervisor foundation slice:
  - shared runtime enums and immutable run snapshots in `supervisor/models.py`
  - deterministic phase-machine enforcement in `supervisor/state_machine.py`
  - typed action validation in `supervisor/actions.py`
  - manual strategy parsing for early testing in `supervisor/strategy_api.py`
  - unit tests covering phase legality, terminal-state rules, and action validation
