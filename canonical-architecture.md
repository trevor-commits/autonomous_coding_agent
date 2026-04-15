# Canonical Architecture

**Date:** April 12, 2026  
**Status:** Source of truth  
**Supersedes as implementation authority:** design-history and reconciliation documents  
**Companion history document:** `canonical-architecture-synthesis.md`

## 1. Purpose

This document defines the architecture to build going forward.

It is not a debate log and it is not a design-history narrative. It is the canonical implementation target for the autonomous coding system in this repository.

This architecture is designed to satisfy the actual operating goal:

Build a system that can autonomously:

- accept a coding objective
- plan the work
- implement backend and frontend changes
- run deterministic quality gates
- launch the app locally
- verify the UI functionally and visually
- route failures back into repair loops
- use specialized agents safely
- produce a ready/not-ready outcome with artifacts

The design prioritizes:

- correctness over theatrics
- reproducibility over improvisation
- single-writer safety over parallel chaos
- bounded AI strategy over AI-owned workflow correctness
- repo-operability over generic cross-repo fantasy

## 2. Executive Architecture Decision

The system is:

**a deterministic autonomous delivery harness with a bounded AI strategy layer**

That means:

- the runtime owns workflow correctness
- AI agents provide planning, delegation strategy, implementation, diagnosis, and review
- no model owns phase transitions or completion authority
- one builder writes code
- one verifier owns the browser
- structured contracts and structured artifacts are required

This is not:

- an AI manager that arbitrarily drives the whole workflow
- a swarm of writers editing the same surface
- a generic "works on any repo" platform
- a transcript-sharing memory system

## 3. Core Principles

### 3.1 Runtime Owns Correctness

The deterministic supervisor is the source of truth for:

- legal phases
- required transitions
- budget and timeout enforcement
- path and command restrictions
- app lifecycle ordering
- verification ordering
- checkpoint commits
- final readiness authority

No model may override these rules.

### 3.2 AI Owns Strategy, Not Legality

The AI strategy layer is used for:

- task decomposition
- builder prompt shaping
- repair direction
- stall diagnosis
- review and audit
- selective re-planning

The AI does not decide whether a required gate can be skipped. It does not decide whether the run is ready without the supervisor's evidence checks.

### 3.3 One Writer

Only one code-writing agent may mutate a run worktree.

This is non-negotiable in v1.

### 3.4 One Browser Owner

Only one verifier may own the browser for a run.

This is non-negotiable in v1.

### 3.5 Contracts Before Autonomy

The system does not improvise a repo's lifecycle.

Every supported repo must expose an explicit automation contract. Every task run must expose an explicit run contract.

### 3.6 Artifacts Over Vibes

Defects, readiness, and progress must be backed by artifacts:

- logs
- exit codes
- diffs
- screenshots
- traces
- structured reports

### 3.7 Boring First

The initial system should be narrow and reliable:

- one supported repo family
- one writer
- one browser verifier
- one review path
- no multi-writer parallelism
- no semantic memory service
- no auto-merge or auto-deploy

## 4. High-Level System Shape

```text
Human kickoff
  ->
Deterministic Supervisor
  - validates repo contract + run contract
  - creates worktree and run store
  - controls phase transitions
  - enforces budgets, locks, guardrails
  ->
AI Strategy Layer
  - planner
  - builder task shaping
  - stall diagnosis
  - review / audit prompts
  ->
Execution Lanes
  - Codex Builder (sole writer)
  - Deterministic Verifier
  - App Supervisor
  - UI Verifier (Playwright)
  - Claude Reviewer / Auditor
  ->
Artifacts + Reports
  ->
Ready / Blocked / Unsupported
```

## 5. Top-Level Components

## 5.1 Deterministic Supervisor

The deterministic supervisor is the center of the architecture.

Responsibilities:

- parse and validate repo contract
- parse and validate run contract
- create run directory and worktree
- enforce single-writer lock
- enforce browser-owner lock
- manage phase transitions
- dispatch legal actions
- run required deterministic gates
- start and stop the app
- capture artifacts and reports
- enforce retries, budgets, and stop conditions
- own checkpoint commits
- decide final run state

The supervisor must be implemented as ordinary code, not as an LLM prompt loop.

## 5.2 AI Strategy Layer

The AI strategy layer is pluggable and bounded by the supervisor.

It is asked questions like:

- what is the next milestone?
- what should the builder do next?
- how should this failure be interpreted?
- should we escalate to reviewer?
- what are the most likely touched files?

It is **not** allowed to redefine the workflow.

The supervisor should expose a bounded interface for future strategy calls such as:

```text
get_strategy_decision(current_phase, current_state, recent_artifacts) -> StrategyDecision
```

The `StrategyDecision` may only select among actions legal in the current phase.

The strategy layer must not emit arbitrary shell-like or git-like commands.
It must choose from typed domain actions exposed by the supervisor.

Bad examples:

```json
{ "type": "git_command", "command": "git add -A && git commit -m 'done'" }
```

```json
{ "type": "run_hook", "command": "npm run test -- --bail" }
```

```json
{ "type": "write_memory", "path": "docs/agent-memory/failure-log.md", "content": "..." }
```

Good examples:

```json
{ "action": "checkpoint_candidate", "reason": "targeted gates passed for milestone M2" }
```

```json
{ "action": "run_contract_command", "name": "test", "scope": "targeted" }
```

```json
{ "action": "record_failure_signature", "fingerprint": "test-auth-empty-email", "evidence_refs": ["artifacts/logs/test.txt"] }
```

This rule exists to prevent the strategy layer from regaining control of the workflow through a side door.

## 5.3 Codex Builder

Codex is the primary builder and only code writer in v1.

Responsibilities:

- inspect relevant files
- implement milestone-scoped changes
- run allowed local checks as requested or permitted
- respond to structured failure and defect packets
- summarize remaining risks and blocking issues

Non-responsibilities:

- branch switching
- merging
- pushing
- browser ownership
- completion authority

## 5.4 Deterministic Verifier

This lane runs required deterministic checks such as:

- format
- lint
- typecheck
- unit tests
- integration tests

It produces structured outputs with:

- command
- exit code
- stdout
- stderr
- duration
- failure fingerprint when applicable

## 5.5 App Supervisor

This is a separate component from the builder and from the general verifier.

Responsibilities:

- start the app from contract-defined commands
- wait for health endpoint readiness
- record process metadata
- manage shutdown
- capture launch and runtime logs

The app supervisor exists because app lifecycle is infrastructure, not cognition.

## 5.6 UI Verifier

This lane owns:

- browser process
- browser profile
- Playwright execution
- screenshots
- traces
- console capture
- network failure capture

It has read-only repo access and may not edit code.

## 5.7 Claude Reviewer / Auditor

Claude is used selectively for:

- initial planning on ambiguous work
- stall diagnosis after repeated failures
- final audit after code and UI are green candidates

Reviewer output must be structured and actionable. Style commentary should not drive the loop.

## 5.8 Release / Readiness Checker

This is a deterministic final gate.

Responsibilities:

- rerun authoritative required checks
- confirm required artifacts exist
- confirm unresolved high-severity findings are absent or declared
- emit a `readiness_verdict` of `READY`, `NOT_READY`, or `NEEDS_MORE_EVIDENCE`

No model may unilaterally mark a run `READY` or set `run_state = COMPLETE`.

## 6. Excluded Components in v1

The following are intentionally excluded from the v1 core:

- OpenClaw as control plane
- Gemini as active worker
- Zep or any external semantic memory layer
- multi-writer parallelism
- autonomous merge to main
- autonomous deployment to production
- broad plugin marketplace integrations
- transcript-based shared memory

These may be revisited later only if metrics justify them.

## 7. Control-Plane Ownership

This is the most important architectural rule in the system.

### 7.1 The Supervisor Owns

- legality of actions
- phase transitions
- whether verification must run
- whether UI verification is allowed yet
- whether app health is sufficient
- retry ceilings
- stop conditions
- final completion authority

### 7.2 The AI Strategy Layer Owns

- decomposition
- prioritization within the allowed phase
- prompt composition for the builder
- diagnosis of novel failures
- whether to invoke reviewer when escalation is permitted
- how to frame repair work

### 7.3 Why This Split Exists

Without this split, the system becomes:

- harder to debug
- more likely to fake completion
- more likely to skip required gates
- more expensive due to repeated top-level reasoning
- less safe around stateful resources such as git, browser, and app lifecycle

## 8. Contracts

The system uses two different contracts.

## 8.1 Repo Contract

The repo contract describes how a supported repo works.

Suggested location:

```text
.agent/contract.yml
```

This is stable, version-controlled repo truth in the target repo's `.agent/` contract surface; see `STRUCTURE.md` for the control-plane versus target-repo boundary.

### Required responsibilities of the repo contract

- define supported stack/repo type
- declare setup/build/test/launch commands
- declare app health mechanism
- declare the deterministic verification commands that local runs and CI must share
- optionally declare UI smoke command and test data seed command
- declare critical UI flows and breakpoints where relevant
- declare required environment variables or templates

### Minimum v1 required fields

At minimum, v1 requires the repo contract to define:

- `commands.setup`
- `commands.test`
- `commands.app_up`
- `commands.app_health`

Optional but strongly preferred:

- `commands.lint`
- `commands.typecheck`
- `commands.format`
- `commands.app_down`
- `commands.ui_smoke`
- `commands.seed_testdata`

If the minimum required fields are missing, the run ends with `run_state = UNSUPPORTED`.

### Example repo contract

```yaml
version: 1
stack: fullstack-web

commands:
  setup: "npm install"
  lint: "npm run lint -- --max-warnings 0"
  typecheck: "npm run typecheck"
  test: "npm run test -- --bail"
  app_up: "npm run dev"
  app_health: "http://127.0.0.1:3000/api/health"
  app_down: "npm run stop"
  ui_smoke: "npx playwright test"
  seed_testdata: "npm run seed:test"

ui:
  base_url: "http://127.0.0.1:3000"
  breakpoints:
    - "390x844"
    - "1440x900"
  critical_flows:
    - id: login
      route: "/login"
      assertions:
        - "login form visible"
        - "submit with test credentials succeeds"
        - "redirects to dashboard"
        - "no console errors"

env:
  required_vars:
    - "DATABASE_URL"
    - "JWT_SECRET"
  template: ".env.example"
```

### CI Integration Principle

GitHub Actions or any other CI system is an external validator, not a workflow owner.

That means:

- CI may rerun contract-defined gates and publish artifacts
- CI may block merges through required status checks
- CI may trigger a supervisor run or report results to an orchestrator
- CI may not redefine repo behavior that belongs in the repo contract
- CI may not become the authority for phase legality or completion semantics

The repo contract remains the source of truth for what a supported repo must run.
CI should call the same contract-defined commands the supervisor uses rather than
hardcoding repo-specific behavior into workflow YAML.

For the first implementation repo, the preferred CI shape is:

- Gate A: fast sanity (`format`, `lint`, `typecheck`, minimal smoke where applicable)
- Gate B: unit tests plus coverage
- Gate C: fast smoke integration / UI verification subset

Each gate should emit structured artifacts that the orchestrator and reviewer lanes
can consume without scraping raw logs. Preferred artifact set:

- `junit.xml`
- `coverage.xml`
- `lint-report.json` when supported by the toolchain
- `smoke-results.json` or an equivalent normalized summary

This architecture repo should document that pattern now, but actual GitHub Actions
implementation belongs in the first real implementation repo or shared CI-template
repo after the local contract-driven flow is proven manually.

## 8.2 Run Contract

The run contract defines what this specific task requires.

This is per-run operational truth, not long-lived repo truth.

### Responsibilities of the run contract

- identify the run
- declare the objective
- declare allowed and forbidden path scope
- declare acceptance criteria
- declare quality gates
- declare UI checks
- declare run constraints such as budgets and retry limits

### Example run contract

```json
{
  "run_id": "uuid",
  "repo_path": "/absolute/path",
  "objective": "Add user profile page with API integration and tests",
  "scope": {
    "allowed_paths": ["src/", "tests/", "docs/"],
    "forbidden_paths": [".env", "infra/", "deploy/"]
  },
  "acceptance": {
    "functional": [
      "User can navigate to /profile",
      "Profile displays name, email, avatar from API",
      "Profile handles loading and error states"
    ],
    "quality_gates": [
      "lint passes",
      "typecheck passes",
      "tests pass"
    ],
    "ui_checks": [
      "Profile renders at 390px and 1440px",
      "No console errors on /profile"
    ]
  },
  "constraints": {
    "single_writer": true,
    "auto_push": true,
    "auto_merge": false,
    "max_repair_loops": 4,
    "max_iterations": 100,
    "max_cost_dollars": 20.0,
    "hard_timeout_seconds": 7200
  }
}
```

## 9. Phase Machine

The supervisor must implement a deterministic phase machine.

Suggested v1 phases while `run_state = IN_PROGRESS`:

- `INTAKE`
- `PREPARE_WORKSPACE`
- `BUILD`
- `LOCAL_VERIFY`
- `APP_LAUNCH`
- `UI_VERIFY`
- `AUDIT_READY`
- `FINAL_GATE`

## 9.1 Terminal States and Readiness Verdict

This section is the source of truth for terminal-state vocabulary.

- `run_state` (what the supervisor concludes about the run overall) ∈ { `COMPLETE`, `BLOCKED`, `UNSUPPORTED`, `IN_PROGRESS` }.
- `readiness_verdict` (what the final readiness gate emits) ∈ { `READY`, `NOT_READY`, `NEEDS_MORE_EVIDENCE` }.

`run_state = COMPLETE` is legal ONLY when:

- `readiness_verdict = READY`
- all required artifacts named in the run contract exist
- all authoritative required checks passed on the final rerun
- no unresolved high-severity defect packets are open

Any other combination produces `run_state = BLOCKED` or `run_state = UNSUPPORTED` per stop conditions.

`NEEDS_MORE_EVIDENCE` is not terminal. It causes the supervisor to run one more evidence-gathering loop up to the configured bound; after that bound it degrades to `NOT_READY` and the run goes to `BLOCKED`.

Companion docs should reference this section rather than redefining the vocabulary.

## 9.2 Phase Responsibilities

### `INTAKE`

- validate repo contract
- validate run contract
- confirm run can begin

### `PREPARE_WORKSPACE`

- create run directory
- create or prepare worktree
- acquire single-writer lease
- initialize state

### `BUILD`

- ask strategy layer what builder should do next within scope
- dispatch milestone-scoped build work
- collect builder outputs

### `LOCAL_VERIFY`

- run required deterministic checks for the current candidate
- emit failure fingerprints on failure

### `APP_LAUNCH`

- launch app through app supervisor
- wait for health
- capture runtime metadata

### `UI_VERIFY`

- run UI verification
- emit structured UI defect packets

### `AUDIT_READY`

- optional review/audit checkpoint after green candidate

### `FINAL_GATE`

- rerun authoritative required gates
- verify required artifacts
- produce a `readiness_verdict`

## 9.3 Mandatory Transitions

The supervisor must enforce mandatory transitions such as:

- build candidate must pass required local verification before UI verification
- app must be healthy before Playwright runs
- repeated same failure fingerprint beyond threshold must escalate or block
- budget exhaustion must stop the run
- `run_state = COMPLETE` requires final gate evidence and `readiness_verdict = READY`

These must not depend on model compliance.

## 9.3 Typed Action Graph

The supervisor should expose a typed action graph rather than a raw command surface.

Suggested v1 action families:

- `collect_context`
- `request_builder_task`
- `run_contract_command`
- `launch_app`
- `stop_app`
- `run_ui_suite`
- `checkpoint_candidate`
- `rollback_to_checkpoint`
- `record_failure_signature`
- `record_decision`
- `propose_terminal_state`

Rules:

- actions are legal only in specific phases
- actions resolve to supervisor-controlled implementations
- actions may reference contract-defined commands by name
- actions may not carry arbitrary shell payloads
- actions may not bypass path, writer, or browser ownership rules

This keeps the AI layer expressive enough for delegation while preserving deterministic control-plane ownership.

## 10. Agent Roster

## 10.1 Planner

Backing model:

- Claude

Purpose:

- create milestone plan
- identify risks
- predict touched areas
- refine acceptance interpretation when the task is ambiguous

Permissions:

- read-only
- no shell
- no repo writes

Persistence:

- ephemeral

## 10.2 Builder

Backing model:

- Codex

Purpose:

- implement the code changes
- fix deterministic failures
- fix UI defect tickets

Permissions:

- write access to exactly one worktree
- safe shell inside allowed policy
- git read-only inspection commands

Denied:

- merge
- rebase
- push
- branch switching
- browser control
- writes outside run scope

Persistence:

- persistent for the run

## 10.3 UI Verifier

Backing tool:

- Playwright

Purpose:

- run critical flows
- capture screenshots/traces/logs
- emit defect packets

Permissions:

- browser control
- localhost access
- read-only repo access

Denied:

- source edits
- commits

Persistence:

- ephemeral per verification pass

## 10.4 Reviewer / Auditor

Backing model:

- Claude

Purpose:

- checkpoint review
- stall diagnosis
- final audit

Permissions:

- read-only selected files, diffs, and artifacts

Denied:

- source edits
- browser control
- git mutation

Persistence:

- ephemeral

## 10.5 Release Checker

Backing tool:

- deterministic scripts and report generation

Purpose:

- final gate
- final report
- authoritative readiness verdict

Permissions:

- read-only verification and artifact inspection

Persistence:

- deterministic system component

## 11. Delegation Model

This system does support delegation, but bounded delegation.

### Delegation means

- strategy layer chooses which worker should act next within legal options
- strategy layer shapes the builder prompt
- strategy layer may request a review or diagnosis when escalation is permitted
- strategy layer can re-plan based on evidence

### Delegation does not mean

- models owning phase transitions
- models deciding that required gates may be skipped
- models declaring `readiness_verdict = READY` or `run_state = COMPLETE` without deterministic evidence
- multiple writers improvising on the same worktree

## 12. Git and Worktree Strategy

The git model is intentionally conservative.

### 12.1 Branch model

- one run = one branch
- one branch = one writable worktree

### 12.2 Worktree model

Suggested layout:

```text
worktrees/<run-id>/builder
```

Future read-only exploration worktrees may exist later, but not in v1 as active writers.

### 12.3 Commit ownership

The supervisor owns checkpoint commits.

The builder edits files but does not own commit authority in v1.

This ensures:

- checkpoint commits represent known-good or intentionally recorded states
- commit message format is consistent
- partial broken work is less likely to be snapshot as progress

### 12.4 Rollback model

Use checkpoint tags or equivalent references such as:

- `autobot/<run-id>/start`
- `autobot/<run-id>/last-green`
- `autobot/<run-id>/cp-01`

Rollback should restore the run worktree to the last known-good checkpoint rather than relying on destructive ad hoc cleanup.

### 12.5 Forbidden git operations for builder

- `git push`
- `git pull`
- `git merge`
- `git rebase`
- `git checkout`
- `git switch`

## 13. Permission and Isolation Model

## 13.1 Filesystem

### Builder

- read-write on one worktree only

### UI verifier

- read-only repo access
- writable temp browser profile directory

### Reviewer

- no repo mount or read-only selected bundle only

### Supervisor

- full control over run directories, worktree orchestration, and artifact locations

## 13.2 Shell policy

Use three classes:

### Auto-allow

- repo contract commands
- safe repo-local reads
- safe file operations inside allowed paths

### Auto-deny

- destructive git operations
- `sudo`
- `ssh`
- `scp`
- deletion outside worktree
- direct edits to secret files
- arbitrary external network fetches unless explicitly allowed

### Escalate / block

- package installs with network
- migrations
- container rebuilds
- infra or CI changes
- auth-related config changes

In v1, "escalate" generally means stop and report rather than continue autonomously.

The strategy layer never receives direct authority to invoke shell, git, or filesystem mutation primitives outside these typed supervisor actions.

## 13.3 Auth

### Codex builder

- dedicated auth context
- isolated runtime or profile where feasible

### Claude reviewer/planner

- API-key or enterprise-compatible auth path
- not consumer web login assumptions embedded into orchestration

### Browser verifier

- test-user credentials only
- isolated session per run

## 13.4 Network

### Builder

- localhost access
- limited network only when explicitly required for supported setup windows

### UI verifier

- localhost plus explicitly approved hosts only

### Reviewer

- no shell/network side effects

## 14. Memory Model

The system uses a three-layer memory model.

## 14.1 Repo Truth

Stable project knowledge stored in version-controlled repo files.

Examples:

- repo contract
- ADRs
- AGENTS instructions
- coding conventions
- API and UI contracts
- environment templates

## 14.2 Run Truth

Per-run operational state and artifacts.

Suggested location:

```text
.autoclaw/runs/<run_id>/
```

This is supervisor-owned runtime storage rather than committed source in either repo; see `STRUCTURE.md` for the boundary rule.

Examples:

- run contract
- plan output
- state file
- defect packets
- screenshots
- traces
- logs
- reports

## 14.3 Operational Memory

Cross-run learnings that may improve future runs.

Suggested location:

```text
.autoclaw/memory/
```

This is supervisor-owned runtime storage rather than target-repo structure; see `STRUCTURE.md` for the boundary rule.

Examples:

- failure-signatures
- flaky-tests registry
- environment quirks
- prior fix strategies keyed by failure class

## 14.4 Non-goals for memory in v1

- no raw transcript retrieval as primary memory
- no chain-of-thought storage
- no external semantic memory system
- no promotion of undocumented assumptions into durable truth

File-based operational memory is acceptable in v1. A structured database may be introduced later only when scale justifies it.

## 15. Run Directory Layout

Suggested run layout:

```text
.autoclaw/
  runs/
    <run_id>/
      contract.json
      plan.json
      state.json
      execution.log
      defects/
      artifacts/
        screenshots/
        videos/
        logs/
        traces/
      reports/
        final-report.json
        final-summary.md
  memory/
    failure-signatures.json
    flaky-tests.json
    environment-quirks.md
    fix-strategies.json
```

## 16. Defect Packet Standard

All verification failures should be emitted as structured defect packets.

Example:

```json
{
  "defect_id": "uuid",
  "severity": "P0",
  "type": "ui-functional",
  "summary": "Save button disabled after valid form input",
  "repro_steps": [
    "Open /settings",
    "Fill display name with valid input",
    "Observe save button state"
  ],
  "expected": "Save button enabled",
  "observed": "Button remains disabled",
  "evidence": {
    "screenshot": "artifacts/screenshots/settings-save-disabled.png",
    "console_log": "artifacts/logs/console.txt",
    "trace": "artifacts/traces/settings-flow.zip"
  },
  "suspected_scope": ["src/components/SettingsForm.tsx"],
  "failure_fingerprint": "settings-save-disabled-after-valid-input"
}
```

Free-form reviewer prose should not be the main defect-routing mechanism.

## 17. Verification Strategy

## 17.1 Deterministic First

Verification order should be:

1. deterministic code gates
2. app health
3. deterministic UI verification
4. optional model judgment for ambiguous UI quality
5. final deterministic readiness gate

## 17.2 UI Verification Split

Target split:

- 80-90% deterministic
- 10-20% model-judged

Model judgment is appropriate for:

- semantic layout mismatches
- polish issues
- subjective correctness where no deterministic rule is practical

Model judgment is not appropriate for:

- route availability
- click success
- console cleanliness
- network correctness
- required state transitions

## 17.3 Browser Ownership Rules

- one verifier process per run
- one isolated browser profile per run
- no builder browser control in normal operation
- no concurrent browser agents on the same app instance

## 18. Failure Handling

The runtime must distinguish between:

- code failures
- harness failures
- environment failures
- fixture failures
- unsupported repo conditions

### Important failure classes

- repeated builder loop on same failure fingerprint
- conflicting or illegal file writes
- false-green candidate
- flaky tests
- browser flake
- stale or misleading memory
- broken auth
- fixture drift
- bad acceptance criteria
- unsupported repo lifecycle

### General runtime response

- fingerprint the failure
- classify the phase and type
- decide whether repair, escalation, or block is legal
- record artifacts
- avoid repeating the same approach indefinitely

## 19. Stop Conditions

The supervisor must stop or block when:

- the repo contract is insufficient
- a required command is unsupported
- the same failure fingerprint exceeds retry threshold
- app health does not stabilize
- budget is exhausted
- hard timeout is exceeded
- path or command restrictions are violated
- unresolved high-severity review finding remains at final gate

## 20. Reporting

Every run must produce:

### Machine-readable report

Containing at minimum:

- run id
- run_state
- readiness_verdict
- phases completed
- commands run
- failures encountered
- changed files
- checkpoint refs
- artifact manifest
- unresolved blockers

### Human-readable summary

Containing at minimum:

- what changed
- what passed
- what failed
- what remains unresolved
- what to do next

## 21. Open Questions

These remain open implementation choices rather than settled architecture changes:

- minimum viable repo contract fields beyond the v1 floor
- exact adapter choice for `acpx` vs direct Codex CLI fallback
- exact `StrategyDecision` schema
- exact failure fingerprint normalization rules
- when file-based memory should migrate to a database

These should be resolved based on implementation evidence, not more abstract argument.

## 22. Phased Implementation Plan

## Phase 0: Repo Preparation + Manual Baseline

Goal:

- prove the repo is automation-ready

Deliverables:

- repo contract
- benchmark tasks
- manual validation of setup/test/app_up/app_health
- initial run directory layout

## Phase 1: Deterministic Supervisor Foundation

Goal:

- build the runtime core

Deliverables:

- contract parsing
- phase machine
- shell policy
- worktree handling
- run state persistence
- deterministic verifier
- checkpointing

## Phase 2: Single Builder Loop

Goal:

- integrate Codex as sole writer

Deliverables:

- builder adapter
- repair loops based on deterministic failures
- structured failure fingerprints
- end-to-end code task completion without AI review dependency

## Phase 3: App + UI Verification

Goal:

- support real frontend verification

Deliverables:

- app supervisor
- Playwright integration
- screenshot and trace artifacts
- UI defect packet generation

## Phase 4: AI Strategy + Review

Goal:

- add bounded Claude strategy and review

Deliverables:

- planner interface
- stall diagnosis
- checkpoint review
- final audit

## Phase 5: Operational Memory Hardening

Goal:

- improve repeat-run efficiency without destabilizing v1

Deliverables:

- normalized operational memory
- flaky-test registry
- environment quirk registry
- optional structured DB migration if justified

## 23. Final Canonical Statement

The source-of-truth architecture for this repository is:

**A deterministic supervisor-centered autonomous delivery harness with:**

- **Codex as the sole writer**
- **Claude as bounded strategy, diagnosis, and review**
- **Playwright as the sole browser verifier**
- **repo contract + run contract as the required automation interface**
- **structured artifacts and defect packets as the evidence model**
- **single-writer and single-browser-owner isolation**
- **runtime-owned correctness and readiness**

Anything that conflicts with that statement should be treated as superseded design history unless future implementation evidence proves otherwise.
