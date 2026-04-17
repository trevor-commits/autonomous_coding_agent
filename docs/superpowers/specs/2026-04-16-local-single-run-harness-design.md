# Local Single-Run Harness Design

Date: 2026-04-16
Status: Approved design baseline
Primary issue: `GIL-52`
Related issues: `GIL-25`, `GIL-26`, `GIL-27`, `GIL-28`, `GIL-29`

## Purpose

Define the next runnable implementation slice for this repository now that Trevor has decided to keep the repository as the implementation repo for the autonomous coding agent runtime.

This document is not the canonical architecture. It is the approved design baseline for the next vertical slice that should be built on top of the current supervisor foundation already present in this repo.

## Current Repo State

This repo is no longer purely architecture and governance.

The `supervisor/` package already contains an initial deterministic control-plane foundation:

- `supervisor/models.py`
- `supervisor/state_machine.py`
- `supervisor/actions.py`
- `supervisor/strategy_api.py`
- `supervisor/closeout_evidence.py`
- `tests/test_state_machine.py`
- `tests/test_actions.py`
- `tests/test_closeout_evidence.py`

That means the next design must extend the existing foundation instead of replacing it with a second greenfield structure.

## Approved Decisions

1. This repository remains the implementation repo for the autonomous coding agent runtime.
2. The next runnable milestone is a local single-run harness, not queue-first execution and not app/browser orchestration first.
3. Strong Linear involvement is required from day one, but Linear remains routing metadata rather than runtime authority.
4. Durable repo writeback is required so design decisions, implementation records, test evidence, and surfaced follow-up work do not die in chat.
5. Branch lifecycle visibility must be tracked across git, `todo.md`, and a Linear mirror so mystery branches do not accumulate.

## Goal

Build the first supervisor slice that can execute one bounded autonomous coding run against one target repo using an explicit run contract and a target repo contract, then emit a durable artifact bundle and deterministic terminal state.

Success means:

- one CLI command starts one run
- the supervisor validates both contracts
- the supervisor creates a run store under `.autoclaw/runs/<run-id>/`
- the supervisor invokes Codex as the sole writer for the run
- deterministic local verification executes through the target repo contract
- the supervisor emits a readiness report and final state
- the run remains traceable back to a `GIL-N` issue and durable repo records

## Non-Goals For This Slice

- No unattended Linear queue execution
- No webhook or reconciliation intake
- No Playwright or browser-owner logic
- No Claude review lane automation
- No broad retry or repair loop orchestration beyond simple structured failure capture
- No branch automation in the supervisor yet
- No deep package reshuffle of the existing `supervisor/` foundation before a real end-to-end run exists

## Recommended Build Shape

The next slice should extend the current flat `supervisor/` package instead of immediately reorganizing it into nested subpackages.

Keep these existing modules in place:

- `models.py`
- `state_machine.py`
- `actions.py`
- `strategy_api.py`
- `closeout_evidence.py`

Add the next modules beside them:

```text
supervisor/
  __init__.py
  actions.py
  closeout_evidence.py
  models.py
  state_machine.py
  strategy_api.py
  cli.py
  repo_contract.py
  run_contract.py
  run_store.py
  leases.py
  shell_adapter.py
  codex_adapter.py
  run_service.py
  report_service.py
tests/
  test_actions.py
  test_closeout_evidence.py
  test_state_machine.py
  test_repo_contract.py
  test_run_contract.py
  test_run_store.py
  test_run_service.py
fixtures/
  run-contracts/
```

Why this shape:

- it preserves the already-landed foundation instead of forcing a package move before there is runtime proof
- it isolates contract parsing, run-store persistence, lease ownership, adapters, and orchestration into clear seams
- it keeps the phase machine and typed-action legality model as the center of the supervisor, which matches `canonical-architecture.md`

## Contract Split

The implementation must separate two different contract types clearly:

### Repo Contract

The target repo automation surface in `.agent/contract.yml`.

Responsibilities:

- deterministic setup command
- deterministic verification commands
- app lifecycle contract when applicable
- optional UI smoke contract when later phases need it

### Run Contract

The per-run task contract that tells the supervisor what one bounded autonomous run is allowed to do.

Responsibilities:

- identify the run
- identify the linked Linear issue
- point at the authoritative repo spec for the task
- scope allowed and forbidden paths
- define acceptance and verification expectations
- define retry, iteration, and timeout constraints

### Required Naming Correction

The current [`schemas/run-contract.schema.json`](/Users/gillettes/Coding Projects/Autonomous Coding Agent/schemas/run-contract.schema.json) file actually describes the repo contract shape, not the per-run task contract.

The next implementation slice should fix that mismatch explicitly:

- rename the current schema to `schemas/repo-contract.schema.json`
- create a true `schemas/run-contract.schema.json` for the per-run task shape
- update any references in docs, fixtures, and implementation code in the same change

Do not keep the naming drift just because it already exists.

## Required Run Contract Fields

The first real run contract should require at least:

- `run_id`
- `linear_issue_id`
- `repo_path`
- `authoritative_spec_path`
- `origin_source`
- `execution_mode`
- `objective`
- `scope.allowed_paths`
- `scope.forbidden_paths`
- `acceptance.functional`
- `acceptance.quality_gates`
- `constraints.max_repair_loops`
- `constraints.max_iterations`
- `constraints.hard_timeout_seconds`

Recommendation:

`linear_issue_id` should be mandatory for all real runs, including manual single-run execution. That keeps runtime artifacts, repo records, and operator routing aligned from day one instead of treating Linear linkage as a later retrofit.

## Runtime Flow

The first runnable path should be:

1. `python3 -m supervisor.cli run --contract <run-contract.json>`
2. load and validate the run contract
3. load and validate the target repo `.agent/contract.yml`
4. create `.autoclaw/runs/<run-id>/`
5. persist normalized input artifacts and initial state
6. acquire the single-writer lease
7. invoke Codex with a bounded builder prompt derived from repo truth plus the run contract
8. run deterministic local verification through the target repo contract
9. write a readiness report and terminal state

## Phase Model For This Slice

The current `supervisor/state_machine.py` already defines the broader canonical phase set:

- `INTAKE`
- `PREPARE_WORKSPACE`
- `BUILD`
- `LOCAL_VERIFY`
- `APP_LAUNCH`
- `UI_VERIFY`
- `AUDIT_READY`
- `FINAL_GATE`

Do not replace that model for the first slice.

Instead, milestone 1 should use a constrained subset of the existing model:

- `INTAKE`
- `PREPARE_WORKSPACE`
- `BUILD`
- `LOCAL_VERIFY`
- `FINAL_GATE`

`APP_LAUNCH`, `UI_VERIFY`, and `AUDIT_READY` remain part of the canonical runtime vocabulary but are not yet required for this slice's happy path.

This keeps the implementation aligned with the already-landed foundation and avoids design drift between docs and code.

## Artifact Layout

The first run should produce a small but disciplined artifact bundle:

```text
.autoclaw/runs/<run-id>/
  state.json
  repo-contract.json
  run-contract.json
  execution.log
  builder/
    codex-input.md
    codex-output.md
  verification/
    checks.json
    command-logs/
  reports/
    readiness-report.json
```

Each artifact path must be stable and machine-readable so later queue, audit, and browser work can layer on top without changing the meaning of a completed run.

## Runtime Responsibilities

### `repo_contract.py`

- load `.agent/contract.yml`
- validate required fields
- normalize commands and optional surfaces
- produce structured validation errors

### `run_contract.py`

- load one per-run JSON contract
- validate required fields including `linear_issue_id`
- normalize scope and constraints
- reject underspecified or malformed contracts before the run starts

### `run_store.py`

- create the run directory
- persist `state.json`
- persist normalized contracts
- provide stable paths for logs, verification outputs, and reports

### `leases.py`

- enforce the single-writer lease for the run
- prevent double acquisition
- surface explicit structured lease failures

### `shell_adapter.py`

- execute deterministic contract-named commands
- capture exit code, stdout, stderr, duration, and working directory
- never accept arbitrary shell payloads from strategy decisions

### `codex_adapter.py`

- invoke Codex as the sole writer
- capture prompt input and model output into run artifacts
- return structured success and failure envelopes to the supervisor

### `run_service.py`

- orchestrate the vertical slice from intake through final report
- drive legal phase transitions through the existing state machine
- own the happy path and structured failure path for milestone 1

### `report_service.py`

- produce `readiness-report.json`
- include `run_id`, `linear_issue_id`, final state, verification summary, and artifact references

## Error Model

The first slice should keep terminal outcomes narrow:

### `UNSUPPORTED`

Use when:

- the repo contract is missing required fields
- the run contract is invalid
- Codex is unavailable
- the target repo cannot satisfy the minimum automation surface

### `BLOCKED`

Use when:

- lease acquisition fails
- Codex invocation fails
- local verification fails
- scope is violated
- timeout or iteration limits are exhausted

### `COMPLETE`

Use only when:

- deterministic checks passed
- required artifacts exist
- the readiness report is written
- the existing final-gate legality checks pass

Do not introduce richer terminal-state vocabulary in this slice unless runtime evidence proves the need.

## Branch Lifecycle Tracking

Branch tracking is required for operator visibility, but it should not move runtime truth out of git.

Use a three-surface model:

### Git is authoritative for:

- whether a branch exists
- what commit it points to
- whether it has been merged
- whether it has been deleted

### `todo.md` is authoritative for:

- why the branch exists
- which `GIL-N` issue it belongs to
- who created it
- when it was created
- what must happen before merge
- what must happen before delete or retention

### Linear mirrors:

- branch name
- branch status
- PR link
- merge target
- short retain reason when applicable

Required rule:

No branch without purpose, no purpose without issue linkage, and no merged branch without an explicit delete-or-retain decision.

Important repo-specific note:

This repository still keeps the current-checkout bias and should remain on `main` unless there is a concrete isolation reason. Branch lifecycle tracking applies when branches are created, but it does not change the standing rule that this repo should not create branches casually.

## Testing For This Slice

The next implementation pass should add:

- repo-contract schema tests
- run-contract schema tests
- run-store creation tests
- lease exclusivity tests
- adapter result-envelope tests
- one end-to-end fixture that exercises the single-run harness without queue or browser behavior

The existing `test_state_machine.py` and `test_actions.py` suites should remain the foundation for legality testing rather than being replaced.

## Mapping To Existing Linear Work

- `GIL-52` tracks this approved design baseline
- `GIL-25` remains the implementation lane for the deterministic supervisor foundation
- `GIL-26` should own contract parsing, run-store creation, shell/path guardrails, and single-writer control
- `GIL-27` should own verification runners and run-local reporting once the harness core exists
- `GIL-28` should layer Codex-builder integration and repair behavior after the single-run harness is stable
- `GIL-29` should add app launch and UI verification later

This keeps the design baseline separate from the implementation issues while still pointing directly into the existing phase path.

## Operator Workflow Implications

For this first slice, strong Linear involvement means:

- every real run links to a `GIL-N`
- every bounded implementation task keeps a repo-side `todo.md` home
- runtime artifacts and repo logs point back to the same issue ID
- branch purpose and lifecycle remain visible without treating Linear as runtime authority

For this first slice, it does not mean:

- queue mode
- webhook triggers
- Linear-owned phase transitions
- issue descriptions acting as executable commands

## Next Step After Approval

Once Trevor approves this written spec, the next step is a concrete implementation plan for the first local single-run harness pass on top of the current `supervisor/` foundation.
