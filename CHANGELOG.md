# Changelog

## 2026-04-17

- Fixed the `GIL-59` through `GIL-62` Phase 3 runtime follow-ups:
  - split retry budgets in `supervisor/main.py` so deterministic verification, app launch, and UI verification no longer consume the same repair counter
  - updated `supervisor/app_supervisor.py` to honor optional `commands.app_down` and record truthful `app_up` command results when launch fails early
  - updated `supervisor/main.py` readiness reporting to preserve cumulative changed files across multi-turn runs
  - updated `supervisor/ui_verifier.py` to emit per-failure defect packets and map expected behavior across multiple `ui_checks` instead of collapsing all `ui_smoke` failures into one packet
  - extended the focused app/UI/main-loop tests with regressions covering all four audit findings
- Added the first `GIL-29` app-launch and UI-verification slice:
  - added `supervisor/app_supervisor.py` so the runtime can launch the target app, poll localhost health, capture lifecycle logs, and stop the process cleanly
  - added `supervisor/ui_verifier.py` so the runtime can run the repo-owned `ui_smoke` command, pass isolated browser-profile and artifact env, and emit structured defect packets on failure
  - extended `supervisor/main.py` to route `LOCAL_VERIFY -> APP_LAUNCH -> UI_VERIFY -> FINAL_GATE`, send app-health and UI defects back through bounded builder repair loops, and carry UI command results into the final readiness report
  - extended `supervisor/strategy_simple.py` with targeted app-launch and UI-defect repair prompts instead of treating all failures like deterministic test failures
  - added focused tests for app lifecycle, UI verifier artifacts/defect packets, strategy repair prompts, and main-loop app/UI repair routing
- Added the first `GIL-23` benchmark fixture suite:
  - added ten control-plane-owned run-contract fixtures under `fixtures/`
  - split the suite between real positive tasks and supervisor-invariant guard cases
  - added coverage for forbidden-path writes, missing-evidence COMPLETE attempts, illegal phase transitions, single-writer lock violations, rollback correctness, and failure-fingerprint normalization
  - added `tests/test_benchmark_fixtures.py` so fixture count, schema validity, and real-scope coverage are enforced automatically
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
