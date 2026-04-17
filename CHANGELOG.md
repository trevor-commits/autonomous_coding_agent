# Changelog

## 2026-04-17

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
