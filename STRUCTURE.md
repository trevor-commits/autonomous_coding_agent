# Folder Structure

**Date:** April 12, 2026
**Authority:** `canonical-architecture.md` (Sections 12, 15) and `IMPLEMENTATION-PLAN.md` define the layouts referenced here.

**Purpose:** This document explains where things go and where to find things. It lists folders (not individual files), describes what each folder is for, and states who is responsible for it. Keep this document updated as new folders are added.

---

## This Repository (Architecture + Supervisor)

This repo holds two things: the architecture/planning documents and (once implementation starts) the supervisor runtime code.

```
/
├── .agent/
├── .autoclaw/
├── supervisor/
├── tests/
├── worktrees/
└── (root-level docs)
```

### Root-Level Documents

The root of the repo contains the core architecture, planning, and operating documents. These are the files that define the project.

**What goes here:** Architecture specs, rules, logic docs, agent instructions, the implementation plan, the changelog, the README, and design-history documents. All markdown.

**What does NOT go here:** Source code, runtime artifacts, test data, configuration files for other tools. Those go in their respective folders.

**Who manages this:** Trevor (human) for architectural changes. Codex for changelog entries. Claude for audits and strategy-layer design docs.

### `.agent/`

The repo contract lives here.

**What goes here:** `contract.yml` — the machine-readable declaration of how the target repo works (setup, test, lint, typecheck, app launch, health check, UI smoke, critical flows, environment variables).

**What does NOT go here:** Run contracts (those go in `.autoclaw/benchmark-tasks/` or are passed at runtime). Agent prompts or strategy prompts (those go in `supervisor/prompts/`).

**Who manages this:** Trevor. The repo contract is stable, version-controlled repo truth. It should only change when the repo's actual lifecycle changes.

### `.autoclaw/`

All runtime and operational data lives under this directory.

```
.autoclaw/
├── benchmark-tasks/
├── memory/
└── runs/
```

**`.autoclaw/benchmark-tasks/`** — Benchmark run contract JSON files used to validate the system at each phase. Created during Phase 0. Version-controlled.

**`.autoclaw/memory/`** — Cross-run operational memory. Failure signatures, flaky test registry, environment quirks, prior fix strategies. Built up automatically over repeated runs. Optionally version-controlled.

**`.autoclaw/runs/`** — Per-run directories. Created by the supervisor at the start of each run. Gitignored (ephemeral to the run, preserved for post-mortem but not committed). Each run gets its own subdirectory:

```
.autoclaw/runs/<run_id>/
├── contract.json
├── plan.json
├── state.json
├── execution.log
├── defects/
├── artifacts/
│   ├── screenshots/
│   ├── videos/
│   ├── logs/
│   └── traces/
└── reports/
    ├── final-report.json
    └── final-summary.md
```

**Who manages this:** The supervisor creates and writes to run directories. The supervisor writes to memory after runs. Trevor creates benchmark tasks. No agent writes directly to `.autoclaw/` outside the supervisor's control.

### `supervisor/`

The supervisor runtime — all Python source code for the deterministic supervisor.

```
supervisor/
├── __init__.py
├── main.py
├── contracts.py
├── state_machine.py
├── policy.py
├── worktree_manager.py
├── verifier.py
├── app_supervisor.py
├── fingerprints.py
├── checkpoints.py
├── reports.py
├── actions.py
├── strategy_api.py
├── strategy_simple.py
├── strategy_claude.py
├── builder_adapter.py
├── ui_verifier.py
├── flaky_tests.py
├── run_store.py
└── prompts/
```

**What goes here:** All supervisor modules. The phase machine, policy engine, worktree manager, verifier, app supervisor, fingerprinting, checkpointing, reporting, typed action graph, strategy implementations, builder adapter, UI verifier, and the entry point.

**`supervisor/prompts/`** — Claude strategy-layer prompt templates (planner, builder task shaper, stall diagnosis, checkpoint review, final audit). Created by Claude in Phase 4.

**What does NOT go here:** Test files (those go in `tests/`). Architecture documents (those stay at the root). Runtime artifacts (those go in `.autoclaw/runs/`).

**Who manages this:** Codex builds the modules (Phases 1–3, 5). Claude designs the strategy prompts (Phase 4). Claude audits all code after each phase.

**Build order** (maps to implementation phases):

| Phase | Modules added |
|-------|--------------|
| 1 | contracts, state_machine, policy, worktree_manager, verifier, app_supervisor, fingerprints, checkpoints, reports, actions, strategy_api, run_store, main |
| 2 | builder_adapter, strategy_simple |
| 3 | ui_verifier (+ updates to strategy_simple) |
| 4 | strategy_claude, prompts/ |
| 5 | flaky_tests (+ hardening updates across existing modules) |

### `tests/`

All test files for the supervisor.

```
tests/
├── test_state_machine.py
├── test_policy.py
├── test_contracts.py
├── test_fingerprints.py
├── test_worktree.py
├── test_actions.py
├── test_builder_adapter.py
├── test_strategy_simple.py
├── test_strategy_claude.py
└── test_ui_verifier.py
```

**What goes here:** Unit and integration tests for supervisor modules. Each supervisor module should have a corresponding test file.

**What does NOT go here:** Benchmark tasks (those go in `.autoclaw/benchmark-tasks/`). Playwright UI test suites for the target repo (those live in the target repo, not here).

**Who manages this:** Codex writes tests alongside each module. Claude reviews test coverage during audits.

### `worktrees/`

Runtime worktree directory. Created by the supervisor's worktree manager during runs.

```
worktrees/
└── <run_id>/
    └── builder/
```

**What goes here:** Git worktrees for active runs. One worktree per run. The builder (Codex) gets write access to exactly one worktree.

**Lifecycle:** Created at PREPARE_WORKSPACE, used during BUILD and repair loops, cleaned up after run completion (or preserved for debugging).

**Who manages this:** The supervisor's worktree_manager module. No agent creates or deletes worktrees directly.

---

## Target Repo (The Repo Being Automated)

The target repo is the project the system operates on — not this repo. It has its own structure, but the system adds two things to it:

```
<target-repo>/
├── .agent/
│   └── contract.yml
└── .autoclaw/
    ├── benchmark-tasks/
    ├── memory/
    └── runs/
```

**`.agent/contract.yml`** — The repo contract. Written by Trevor in Phase 0. Describes how the repo works.

**`.autoclaw/`** — Same layout as described above. The supervisor creates this when running against the target repo.

Everything else in the target repo is the repo's own code, config, and tests — the system reads and modifies it through the builder, but the structure is whatever the repo already has.

---

## What Does NOT Exist Yet

The following folders do not exist until their respective implementation phases create them. Do not create them prematurely:

| Folder | Created in |
|--------|-----------|
| `supervisor/` | Phase 1 |
| `tests/` | Phase 1 |
| `supervisor/prompts/` | Phase 4 |
| `worktrees/` | Created at runtime by supervisor |
| `.autoclaw/runs/<run_id>/` | Created at runtime by supervisor |

---

## Rules for Keeping This Organized

- New source code goes in `supervisor/`. Do not scatter Python files at the root.
- New tests go in `tests/`. Mirror the module name with a `test_` prefix.
- New architecture/planning docs go at the root as markdown. Update README.md when adding one.
- New runtime artifacts go in `.autoclaw/runs/<run_id>/`. Never at the root or in `supervisor/`.
- New strategy prompts go in `supervisor/prompts/`. Not at the root, not in `.autoclaw/`.
- New benchmark tasks go in `.autoclaw/benchmark-tasks/`.
- If you add a new top-level folder, update this document.
