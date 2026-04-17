# Changelog

## 2026-04-16

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
