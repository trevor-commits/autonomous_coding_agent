# Implementation Plan

**Date:** April 12, 2026
**Authority:** `canonical-architecture.md` is the source of truth for all architectural decisions referenced here.
**Purpose:** This is the step-by-step execution plan — what to build, in what order, who builds it, what to test, and how to know each step is done before moving to the next.

---

## How to Use This Document

Each phase has a checklist of deliverables. Do not advance to the next phase until every checklist item in the current phase is verified. Each deliverable specifies who is responsible (Trevor, Codex, or Claude), what the deliverable is, how to verify it works, and what to do if it doesn't.

Phases are sequential. Within a phase, items marked "parallel-safe" can be worked on simultaneously.

---

## Prerequisites

Before any phase begins, confirm the following:

- [ ] You have a target repo to automate (a real project with frontend + backend, not a toy)
- [ ] The target repo builds and runs locally on your machine today (manually)
- [ ] You have working API keys: `OPENAI_API_KEY` (for Codex) and `ANTHROPIC_API_KEY` (for Claude)
- [ ] Codex CLI is installed and functional (`codex --version` returns a version)
- [ ] Node.js and npm/pnpm are installed
- [ ] Python 3.10+ is installed
- [ ] Git is installed and configured with credentials
- [ ] Playwright is installed or installable (`npx playwright install`)

If any prerequisite fails, fix it before proceeding. The system cannot compensate for a broken local environment.

---

## Phase 0: Repo Preparation and Manual Baseline

**Goal:** Prove the target repo is automation-ready. Establish the contracts. Create benchmark tasks. Validate every tool works independently.

**Duration estimate:** 2-4 days

**Why this phase exists:** If the repo can't be reliably set up, built, tested, and launched by a human following explicit commands, no agent system will succeed on it. This phase forces that proof.

### 0.1 Write the Repo Contract

**Owner:** Trevor
**Deliverable:** `.agent/contract.yml` in the target repo

Write the repo contract following the schema in `canonical-architecture.md` Section 8.1. This file declares how your repo works — what commands set it up, build it, test it, launch it, and verify the UI.

```yaml
# .agent/contract.yml
version: 1
stack: fullstack-web   # or: backend-api, static-site, monorepo, etc.

commands:
  # REQUIRED — system returns UNSUPPORTED without these
  setup: "npm install"
  test: "npm run test -- --bail"
  app_up: "npm run dev"
  app_health: "http://127.0.0.1:3000/api/health"

  # OPTIONAL but strongly recommended
  format: "npx prettier --write --check ."
  lint: "npm run lint -- --max-warnings 0"
  typecheck: "npm run typecheck"
  app_down: "kill"
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

**Verification:**
- [ ] `.agent/contract.yml` exists in the target repo
- [ ] Every `commands.*` entry is a real command that works when you run it manually
- [ ] `commands.app_health` returns 200 when the app is running
- [ ] If `ui.critical_flows` are defined, you can manually verify each assertion is true

**If it fails:** Fix the repo. Add missing scripts. Add a health endpoint. Create `.env.example`. The contract is not aspirational — it documents what already works.

### 0.2 Validate the Contract Manually

**Owner:** Trevor
**Deliverable:** A manual run-through proving every contract command works

Run each command in order on a clean checkout:

```bash
# 1. Setup
git clone <repo> /tmp/test-checkout
cd /tmp/test-checkout
cp .env.example .env  # fill in local dev values
npm install           # or whatever commands.setup says

# 2. Quality gates
npm run lint -- --max-warnings 0    # commands.lint
npm run typecheck                    # commands.typecheck
npm run test -- --bail               # commands.test

# 3. App launch
npm run dev &                        # commands.app_up
sleep 5
curl -s http://127.0.0.1:3000/api/health  # commands.app_health — should return 200

# 4. UI smoke (if defined)
npx playwright test                  # commands.ui_smoke

# 5. Cleanup
kill %1                              # commands.app_down
```

**Verification:**
- [ ] Every command exits 0 (or expected success)
- [ ] App health returns 200 within 30 seconds of launch
- [ ] No manual steps were needed beyond what the contract declares
- [ ] Clean checkout works (no hidden state dependencies)

**If it fails:** The repo is not automation-ready. Fix the scripts, add missing dependencies to `package.json`, fix flaky tests, add the health endpoint. Do not proceed until this works cleanly.

### 0.3 Write Benchmark Run Contracts

**Owner:** Trevor
**Deliverable:** 3-5 run contract JSON files in `.autoclaw/benchmark-tasks/`

Create tasks of varying complexity that you will use to validate the system at each phase. These must be real tasks you would actually want done, not synthetic toy examples.

**Task 1 — Small (backend-only):**
```json
{
  "run_id": "benchmark-001",
  "repo_path": "/path/to/repo",
  "objective": "Add a GET /api/users/:id endpoint that returns user data by ID",
  "scope": {
    "allowed_paths": ["src/api/", "src/models/", "tests/"],
    "forbidden_paths": [".env", "infra/", "deploy/"]
  },
  "acceptance": {
    "functional": [
      "GET /api/users/1 returns user object with id, name, email",
      "GET /api/users/999 returns 404",
      "Response matches existing API conventions"
    ],
    "quality_gates": ["lint passes", "typecheck passes", "tests pass"],
    "ui_checks": []
  },
  "constraints": {
    "single_writer": true,
    "auto_push": false,
    "auto_merge": false,
    "max_repair_loops": 4,
    "max_iterations": 50,
    "max_cost_dollars": 10.0,
    "hard_timeout_seconds": 3600
  }
}
```

**Task 2 — Medium (frontend + backend):**
A task that requires both a new API endpoint and a new UI page/component with tests.

**Task 3 — Medium with UI verification:**
A task that modifies existing UI and requires visual verification (e.g., "add a settings page").

**Task 4 — Fix task:**
A task that requires fixing a known bug (introduce one intentionally for benchmarking).

**Task 5 — Refactor task (optional):**
A task that changes existing code structure without changing behavior.

**Verification:**
- [ ] Each JSON file is valid and parseable
- [ ] Each task has clear, testable acceptance criteria
- [ ] Scope paths exist in the repo
- [ ] Tasks span the range: backend-only, frontend+backend, UI-critical, fix, refactor
- [ ] You could manually verify "done" for each task by checking the acceptance criteria

### 0.4 Validate External Tools Independently

**Owner:** Trevor (parallel-safe — do all at once)
**Deliverable:** Proof each tool works in isolation

**Codex:**
```bash
# Verify Codex can interact with the repo
cd /path/to/repo
codex "Read the file src/index.ts and describe what it does"
# Expected: coherent response about the file
```

**Claude API:**
```bash
# Verify Claude API works (via curl or SDK)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":100,"messages":[{"role":"user","content":"Say hello"}]}'
# Expected: valid response
```

**Playwright:**
```bash
cd /path/to/repo
npm run dev &
sleep 5
npx playwright test --reporter=list
kill %1
# Expected: tests run and produce results
```

**Verification:**
- [ ] Codex reads files and responds coherently
- [ ] Claude API returns valid responses
- [ ] Playwright runs tests against the local app
- [ ] No auth errors, no timeouts, no missing dependencies

### 0.5 Create the Run Directory Structure

**Owner:** Trevor or Codex
**Deliverable:** `.autoclaw/` directory in the target repo

```bash
mkdir -p .autoclaw/runs
mkdir -p .autoclaw/memory
mkdir -p .autoclaw/benchmark-tasks

# Add to .gitignore (runs are ephemeral, memory is optional to track)
echo ".autoclaw/runs/" >> .gitignore
```

Place benchmark task JSONs in `.autoclaw/benchmark-tasks/`.

Create initial empty memory files:
```bash
echo '[]' > .autoclaw/memory/failure-signatures.json
echo '[]' > .autoclaw/memory/flaky-tests.json
echo '{}' > .autoclaw/memory/fix-strategies.json
echo '# Environment Quirks' > .autoclaw/memory/environment-quirks.md
```

**Verification:**
- [ ] `.autoclaw/` directory structure exists
- [ ] `.autoclaw/runs/` is gitignored
- [ ] Benchmark task files are in `.autoclaw/benchmark-tasks/`
- [ ] Memory files exist with empty initial content

### Phase 0 Exit Criteria

All of the following must be true:
- [ ] Repo contract exists and every command works manually
- [ ] 3-5 benchmark run contracts exist with testable acceptance criteria
- [ ] Codex, Claude API, and Playwright all work independently
- [ ] `.autoclaw/` directory structure exists
- [ ] A clean checkout + contract commands produces green gates and a running app

**Do not proceed to Phase 1 until all Phase 0 criteria are met.**

---

## Phase 1: Deterministic Supervisor Foundation

**Goal:** Build the runtime core that will own workflow correctness for the entire system.

**Duration estimate:** 1-2 weeks

**Who builds it:** Codex

**What Claude does:** Audits the output after each major module.

### 1.1 Supervisor Modules to Build

Give Codex the following prompt (adapted from the ChatGPT Pro prompt that all three models agreed on). This builds the entire supervisor foundation:

**Codex Prompt:**
```
Read the following files before starting:
- canonical-architecture.md (Sections 5.1, 8, 9, 13, 15, 18, 19, 20)
- AGENTS.md
- .agent/contract.yml

Build a Python supervisor for an autonomous multi-agent coding system.

Core rule: The supervisor is the source of truth for workflow correctness.
Do not build an AI-managed control loop. Build a deterministic phase machine
with a bounded decision API that an AI strategy layer can plug into later.

Create these modules inside a `supervisor/` directory:

1. contracts.py
   - Parse .agent/contract.yml (repo contract)
   - Parse run contract JSON
   - Validate required fields exist
   - Return UNSUPPORTED with reason if minimum requirements not met
   - Enforce allowed_paths / forbidden_paths from run contract

2. state_machine.py
   - Implement the phase machine with states:
     INTAKE, UNSUPPORTED, PREPARE_WORKSPACE, BUILD, LOCAL_VERIFY,
     APP_LAUNCH, UI_VERIFY, AUDIT_READY, FINAL_GATE, COMPLETE, BLOCKED
   - Define legal transitions between phases
   - Reject illegal transition attempts
   - Track current phase, phase history, and timestamps

3. policy.py
   - Three shell classes: auto_allow, auto_deny, escalate
   - Command deny list (git push, sudo, ssh, scp, rm -rf outside worktree, etc.)
   - Path restriction enforcement (allowed_paths, forbidden_paths)
   - Budget enforcement (max_iterations, max_cost_dollars, hard_timeout_seconds)
   - Single-writer lock (one writable worktree per run)

4. worktree_manager.py
   - Create worktree for a run: worktrees/<run_id>/builder
   - Create run branch: run/<task-slug>/<run_id>
   - Acquire and release single-writer lease
   - Create checkpoint tags: autobot/<run_id>/start, autobot/<run_id>/last-green, autobot/<run_id>/cp-NN
   - Rollback to checkpoint

5. verifier.py
   - Run contract commands (setup, format, lint, typecheck, test) and capture:
     command name, exit code, stdout, stderr, duration, failure fingerprint
   - Return structured verification results
   - Support targeted (changed files only) and full verification modes

6. app_supervisor.py
   - Launch app from repo contract (commands.app_up)
   - Wait for health endpoint (commands.app_health) with configurable timeout
   - Capture PID, port, launch logs
   - Clean shutdown (commands.app_down or kill)
   - Return structured launch result

7. fingerprints.py
   - Normalize failure fingerprints from: phase, command, error signature, relevant paths
   - Detect repeated fingerprints (same failure appearing N times)
   - Persist fingerprints to run directory
   - Load prior fingerprints from .autoclaw/memory/failure-signatures.json

8. checkpoints.py
   - Create checkpoint commit (supervisor owns commits, not builder)
   - Structured commit message format: [autobot/<run_id>] <type>: <description>
   - Tag checkpoints
   - Track last-green checkpoint

9. reports.py
   - Generate machine-readable final report (JSON):
     run_id, final_state, phases_completed, commands_run, failures, changed_files,
     checkpoint_refs, artifact_manifest, unresolved_blockers
   - Generate human-readable summary (Markdown):
     what changed, what passed, what failed, what's unresolved, next steps

10. actions.py
    - Define the typed action graph (not raw shell):
      collect_context, request_builder_task, run_contract_command, launch_app,
      stop_app, run_ui_suite, checkpoint_candidate, rollback_to_checkpoint,
      record_failure_signature, record_decision, propose_terminal_state
    - Validate actions are legal for current phase
    - Actions resolve to supervisor-controlled implementations
    - Actions may NOT carry arbitrary shell payloads

11. strategy_api.py
    - Define the interface: get_strategy_decision(state, allowed_actions) -> StrategyDecision
    - Implement a MANUAL strategy (reads decisions from stdin or a file) for Phase 1 testing
    - Placeholder for future Claude integration
    - The strategy layer can only choose from actions the supervisor exposes for the current phase

12. run_store.py
    - Create run directory: .autoclaw/runs/<run_id>/
    - Initialize: contract.json, state.json, execution.log, defects/, artifacts/, reports/
    - Write and update state.json after every action
    - Append to execution.log

13. main.py
    - Entry point: accepts repo path and run contract JSON
    - Validates repo contract
    - Creates run store and worktree
    - Runs the supervisor loop:
      read state -> get legal actions -> get strategy decision -> execute action ->
      update state -> check mandatory transitions -> repeat until terminal
    - Produces final report on completion or failure

14. Tests (in tests/ directory):
    - test_state_machine.py: phase legality, transition validation, illegal rejection
    - test_policy.py: deny list enforcement, path restrictions, budget limits
    - test_contracts.py: valid/invalid contract parsing, UNSUPPORTED detection
    - test_fingerprints.py: normalization, dedup, persistence
    - test_worktree.py: creation, lease, checkpoint, rollback
    - test_actions.py: phase-legal action validation, illegal action rejection

Non-goals for this phase:
- No Claude/AI integration yet (use manual strategy)
- No Playwright integration yet
- No auto-merge or deploy
- No multi-writer support

Log what you build in a CHANGELOG.md in this repo.
```

### 1.2 Audit the Supervisor

**Owner:** Claude (me)
**Trigger:** After Codex delivers the supervisor modules

I will audit for:
- [ ] Phase machine correctly rejects illegal transitions
- [ ] Policy engine correctly blocks denied commands
- [ ] Path restrictions are enforced (builder cannot write to forbidden_paths)
- [ ] Budget limits actually terminate the run when exceeded
- [ ] Single-writer lock prevents concurrent worktree access
- [ ] Checkpoint commits have correct format and tags
- [ ] UNSUPPORTED is returned for repos missing required contract fields
- [ ] Typed actions reject raw shell payloads
- [ ] Reports contain all required fields
- [ ] Tests pass and cover the critical paths

### 1.3 Manual Integration Test

**Owner:** Trevor
**Deliverable:** Run the supervisor manually against benchmark task 1 (backend-only)

Use the manual strategy mode. You play the AI strategy layer — the supervisor asks you what to do, you type a legal action, the supervisor executes it. This validates the entire runtime without any AI in the loop.

```bash
cd /path/to/repo
python supervisor/main.py \
  --repo-path . \
  --run-contract .autoclaw/benchmark-tasks/benchmark-001.json \
  --strategy manual
```

Walk through: INTAKE → PREPARE_WORKSPACE → BUILD (you type `request_builder_task` with a description) → LOCAL_VERIFY → ... → COMPLETE or BLOCKED.

**Verification:**
- [ ] Supervisor creates worktree and run directory
- [ ] Supervisor reads and validates both contracts
- [ ] Phase transitions work correctly
- [ ] Verification commands run and capture output
- [ ] Checkpoint commits are created at the right times
- [ ] Final report is generated
- [ ] Execution log captures all actions
- [ ] The manual strategy API is usable

### Phase 1 Exit Criteria

- [ ] All 14 modules exist and are functional
- [ ] All tests pass
- [ ] Manual integration test completes benchmark task 1 with you as the strategy layer
- [ ] Supervisor correctly blocks illegal commands, paths, and phase transitions
- [ ] Claude has audited the code and no P0/P1 issues remain open
- [ ] CHANGELOG.md is updated

**Do not proceed to Phase 2 until all Phase 1 criteria are met.**

---

## Phase 2: Single Builder Loop

**Goal:** Integrate Codex as the sole writer. Achieve end-to-end autonomous code task completion (for code-only tasks, no UI verification yet).

**Duration estimate:** 1-2 weeks

**Who builds it:** Codex

### 2.1 Builder Adapter

**Codex Prompt:**
```
Read canonical-architecture.md Sections 5.3 and 10.2.
Read supervisor/actions.py and supervisor/strategy_api.py.

Build a builder adapter module: supervisor/builder_adapter.py

Requirements:
1. Define a BuilderAdapter interface with methods:
   - start_session(worktree_path, run_context) -> session
   - send_task(session, prompt, timeout) -> BuilderResult
   - close_session(session)

2. Implement CodexAdapter that:
   - Starts a Codex session scoped to the worktree
   - Sends implementation prompts to Codex
   - Captures Codex's output (files changed, commands run, self-reported status)
   - Supports session continuity (multi-turn within a run)
   - Has configurable timeout per task

3. Implement a DirectCLIAdapter as fallback:
   - Uses `codex exec` for stateless one-shot tasks
   - Less capable but works if session management breaks

4. The adapter must NOT let the builder:
   - Commit (supervisor owns commits)
   - Push
   - Switch branches
   - Control a browser
   - Write outside allowed_paths

5. Builder prompts should include:
   - The current milestone objective
   - Relevant file paths from the plan
   - The repo contract commands (so builder can run targeted checks)
   - Any prior failure fingerprints for this milestone
   - Instruction to NOT commit, push, or switch branches

6. Add tests: test_builder_adapter.py
   - Mock Codex responses
   - Verify session lifecycle
   - Verify forbidden operations are not included in prompts

Log changes in CHANGELOG.md.
```

### 2.2 Automated Strategy (Simple Rule-Based)

**Codex Prompt:**
```
Read supervisor/strategy_api.py and supervisor/state_machine.py.

Implement supervisor/strategy_simple.py — a rule-based strategy that can drive
the supervisor through a complete task without AI or human input.

Rules:
- In BUILD phase: issue request_builder_task with the run contract objective
- After BUILD: always transition to LOCAL_VERIFY
- In LOCAL_VERIFY: run all available contract commands (lint, typecheck, test)
- If LOCAL_VERIFY passes: issue checkpoint_candidate
- If LOCAL_VERIFY fails (attempt < max_repair_loops):
  issue request_builder_task with failure details and ask builder to fix
- If LOCAL_VERIFY fails (attempt >= max_repair_loops):
  propose_terminal_state BLOCKED
- After successful checkpoint: if more milestones, back to BUILD; else propose COMPLETE
- Handle UNSUPPORTED, BLOCKED as terminal

This is a dumb strategy — it doesn't decompose tasks into milestones, it doesn't
diagnose stalls, it doesn't do anything clever. It just loops build → verify → fix.
That is correct for Phase 2. The smart strategy comes in Phase 4.

Add tests: test_strategy_simple.py
Log changes in CHANGELOG.md.
```

### 2.3 End-to-End Test: Automated Build Loop

**Owner:** Trevor + Claude (audit)
**Deliverable:** Run benchmark tasks 1 and 4 (backend-only and fix task) fully autonomously

```bash
python supervisor/main.py \
  --repo-path /path/to/repo \
  --run-contract .autoclaw/benchmark-tasks/benchmark-001.json \
  --strategy simple
```

**Verification:**
- [ ] Supervisor starts, validates contracts, creates worktree
- [ ] Codex receives build task and writes code
- [ ] Supervisor runs deterministic gates independently (does not trust Codex's self-report)
- [ ] On failure, supervisor routes failure back to Codex with structured fingerprint
- [ ] Retry loop works (Codex attempts fix, gates re-run)
- [ ] On success, supervisor creates checkpoint commit
- [ ] Final report is generated with all required fields
- [ ] Benchmark task 1 completes successfully (code + tests pass)
- [ ] Benchmark task 4 (fix) completes successfully

### 2.4 Measure Phase 2 Baselines

**Owner:** Trevor
**Deliverable:** Baseline metrics for later comparison

Run each benchmark task 3 times. Record:

| Metric | Task 1 | Task 4 |
|--------|--------|--------|
| Completion rate (out of 3 runs) | | |
| Average iterations to completion | | |
| Average Codex invocations | | |
| Average time (minutes) | | |
| Average cost (estimate) | | |
| Retry count per run | | |

These baselines are what you compare against when adding the AI strategy layer in Phase 4.

### Phase 2 Exit Criteria

- [ ] Builder adapter works with Codex (session-based or direct CLI)
- [ ] Simple strategy drives the full build → verify → fix → checkpoint loop
- [ ] Benchmark task 1 (backend-only) completes autonomously at least 2/3 runs
- [ ] Benchmark task 4 (fix) completes autonomously at least 2/3 runs
- [ ] Supervisor never lets Codex commit, push, or write to forbidden paths
- [ ] Baseline metrics recorded
- [ ] Claude has audited the builder adapter and strategy
- [ ] CHANGELOG.md updated

**Do not proceed to Phase 3 until all Phase 2 criteria are met.**

---

## Phase 3: App Launch + UI Verification

**Goal:** Launch the app autonomously, run Playwright, capture artifacts, generate defect packets, and route UI failures back to the builder for repair.

**Duration estimate:** 1-2 weeks

**Who builds it:** Codex

### 3.1 Playwright Integration

**Codex Prompt:**
```
Read canonical-architecture.md Sections 5.5, 5.6, 16, 17.
Read the repo contract at .agent/contract.yml (ui section).

Build supervisor/ui_verifier.py:

1. Launch Playwright with:
   - Isolated browser profile (temp directory per run)
   - Headless mode by default (configurable for debug)
   - Configured viewports from repo contract breakpoints

2. Run the UI smoke suite (commands.ui_smoke from repo contract)

3. Capture artifacts per test:
   - Screenshots on failure
   - Playwright traces
   - Console log capture
   - Network error capture

4. Generate defect packets (JSON) for each failure:
   {
     "defect_id": "uuid",
     "severity": "P0" | "P1" | "P2",
     "type": "ui-functional" | "ui-visual" | "ui-console" | "ui-network",
     "summary": "description",
     "repro_steps": ["step1", "step2"],
     "expected": "what should happen",
     "observed": "what actually happened",
     "evidence": {
       "screenshot": "path",
       "console_log": "path",
       "trace": "path"
     },
     "suspected_scope": ["src/components/Foo.tsx"],
     "failure_fingerprint": "normalized-string"
   }

5. Store all artifacts in .autoclaw/runs/<run_id>/artifacts/

6. Return structured result: pass/fail with defect packet list

7. Browser ownership rules:
   - Only the UI verifier opens a browser
   - One browser profile per run
   - Clean profile (no state from prior runs)
   - localhost only (no external URLs)

Add tests: test_ui_verifier.py (mock Playwright results)
Log changes in CHANGELOG.md.
```

### 3.2 Update Strategy for UI Loop

**Codex Prompt:**
```
Update supervisor/strategy_simple.py to handle app launch and UI verification phases:

After LOCAL_VERIFY passes:
- Transition to APP_LAUNCH
- Launch app via app supervisor
- If health check fails: route to builder for fix, retry (max 2)
- If healthy: transition to UI_VERIFY
- Run Playwright suite
- If defect packets exist: route defects to builder, re-run LOCAL_VERIFY then UI_VERIFY
- If no defects: transition to FINAL_GATE
- Max 2 UI repair cycles before BLOCKED

Update builder prompts to include defect packet content when routing UI failures.

Log changes in CHANGELOG.md.
```

### 3.3 End-to-End Test: Full Frontend Task

**Owner:** Trevor + Claude (audit)
**Deliverable:** Run benchmark tasks 2 and 3 (frontend+backend and UI verification tasks)

**Verification:**
- [ ] App launches from repo contract commands
- [ ] Health endpoint is checked before Playwright runs
- [ ] Playwright tests execute and produce artifacts (screenshots, traces)
- [ ] Failed tests generate structured defect packets
- [ ] Defect packets are routed back to Codex with specific instructions
- [ ] Codex fixes UI issues and re-verification works
- [ ] Artifacts are stored in the run directory
- [ ] Benchmark task 2 or 3 completes with UI verification passing

### Phase 3 Exit Criteria

- [ ] App supervisor launches and shuts down the app reliably
- [ ] Playwright runs with isolated browser profile
- [ ] Defect packets are generated for UI failures
- [ ] UI failure → builder fix → re-verify loop works
- [ ] Screenshots and traces are captured in artifacts
- [ ] At least one frontend benchmark task completes with UI verification
- [ ] Claude has audited the UI verifier and defect packet generation
- [ ] CHANGELOG.md updated

**Do not proceed to Phase 4 until all Phase 3 criteria are met.**

---

## Phase 4: AI Strategy Layer + Review

**Goal:** Replace the simple rule-based strategy with Claude as a bounded strategy layer. Add code review and stall diagnosis.

**Duration estimate:** 1-2 weeks

**Who designs it:** Claude (me)
**Who integrates it:** Codex

### 4.1 Strategy Layer Design (Claude's Responsibility)

**Deliverables from Claude:**

1. **Planner prompt** — Given a run contract and repo context, decompose the objective into milestones. Output: structured JSON with milestone ID, description, files to touch, tests to add, dependencies.

2. **Builder task shaper prompt** — Given a milestone, repo context, and prior failures, produce the optimal prompt to give Codex. Output: specific, scoped builder instruction.

3. **Stall diagnosis prompt** — Given repeated failure fingerprints and builder attempts, diagnose the root cause and recommend a different approach. Output: structured diagnosis with specific fix direction.

4. **Checkpoint review prompt** — Given a diff and acceptance criteria, review for correctness, security, and plan adherence. Output: structured findings with severity, file, evidence, and fix instruction.

5. **Final audit prompt** — Given the complete diff, artifacts, and acceptance criteria, produce a readiness verdict. Output: PASS/FAIL with blocking issues.

6. **StrategyDecision schema** — JSON schema defining exactly what the strategy layer returns for each phase, using only typed domain actions.

All prompts will be designed to produce structured output compatible with the typed action graph. No raw shell commands.

### 4.2 Claude Strategy Integration

**Codex Prompt:**
```
Read canonical-architecture.md Sections 5.2 and 7.
Read supervisor/strategy_api.py and supervisor/actions.py.
Read the strategy prompts provided by Claude (in supervisor/prompts/ directory).

Implement supervisor/strategy_claude.py:

1. Implements the get_strategy_decision interface
2. Calls Claude API with the appropriate prompt for the current phase:
   - BUILD phase: use planner prompt (first iteration) or builder task shaper (subsequent)
   - After repeated failure: use stall diagnosis prompt
   - AUDIT_READY phase: use checkpoint review prompt
   - FINAL_GATE phase: use final audit prompt
3. Parses Claude's structured response into typed StrategyDecision
4. Falls back to simple strategy if Claude returns unparseable output
5. Tracks Claude invocation count and cost for budget enforcement
6. Uses API-key auth (not consumer login)

Configuration:
- ANTHROPIC_API_KEY from environment
- Model: configurable (default: claude-sonnet-4-20250514)
- Max tokens per call: configurable
- Timeout per call: configurable

Add tests: test_strategy_claude.py (mock API responses)
Log changes in CHANGELOG.md.
```

### 4.3 Comparative Testing

**Owner:** Trevor
**Deliverable:** Run all 5 benchmark tasks with both strategies and compare

| Metric | Simple Strategy | Claude Strategy |
|--------|----------------|-----------------|
| Completion rate (out of 5 tasks) | | |
| Average iterations | | |
| Average cost | | |
| Average time | | |
| Tasks that simple couldn't solve but Claude could | | |
| Review catch rate (issues found by audit) | | |

**The Claude strategy should show improvement on:**
- Tasks requiring multi-milestone decomposition (tasks 2, 3)
- Tasks where the builder gets stuck (measured by fewer total retries)
- Quality (fewer issues in final audit)

**If Claude strategy is not measurably better:** The simple strategy is sufficient for that task class. Don't add complexity for its own sake.

### Phase 4 Exit Criteria

- [ ] Claude strategy layer implements all 5 prompt types
- [ ] Strategy layer only produces typed domain actions (no raw shell)
- [ ] Planner decomposes multi-file tasks into milestones
- [ ] Stall diagnosis helps resolve at least one builder stall that simple strategy couldn't
- [ ] Code review catches at least one real issue across the benchmark suite
- [ ] Comparative metrics show measurable improvement on complex tasks
- [ ] Claude has audited the integration
- [ ] CHANGELOG.md updated

**Do not proceed to Phase 5 until all Phase 4 criteria are met.**

---

## Phase 5: Operational Memory + Hardening

**Goal:** Use cross-run data to improve future runs. Harden the system for repeated use.

**Duration estimate:** 1-2 weeks

### 5.1 Failure Signature Learning

**Codex Prompt:**
```
Read supervisor/fingerprints.py and .autoclaw/memory/failure-signatures.json.

Enhance the fingerprint system:
1. After each run (success or failure), promote relevant fingerprints to
   .autoclaw/memory/failure-signatures.json with:
   - fingerprint
   - phase
   - command
   - root_cause (from diagnosis if available)
   - resolution (from successful fix if available)
   - last_seen date
   - occurrence_count
2. When building prompts for the builder, include relevant prior failure
   signatures and their resolutions
3. Implement TTL: archive entries not seen in 30 days
4. Implement dedup: don't store identical fingerprints

Log changes in CHANGELOG.md.
```

### 5.2 Flaky Test Registry

**Codex Prompt:**
```
Build supervisor/flaky_tests.py:
1. Detect flaky tests: test passes on re-run without code changes
2. Register in .autoclaw/memory/flaky-tests.json with:
   - test name, file, last flake date, flake count
3. Quarantine policy: flaky tests don't block the run after N flakes
4. Surface flaky tests in the final report

Log changes in CHANGELOG.md.
```

### 5.3 Reliability Hardening

**Codex Prompt:**
```
Add robustness to the supervisor:
1. Graceful shutdown: if the process is killed, write current state and partial report
2. Resume capability: if a run was interrupted, detect the last checkpoint and offer to resume
3. Concurrent run prevention: lock file prevents two supervisor instances on the same repo
4. Rate limit handling: if Claude API returns 429, exponential backoff
5. acpx/Codex session recovery: if session drops, start a new one with context summary
6. Artifact cleanup: configurable retention (default: keep last 10 runs)

Log changes in CHANGELOG.md.
```

### Phase 5 Exit Criteria

- [ ] Prior failure signatures are included in builder prompts when relevant
- [ ] Flaky tests are detected, registered, and quarantined
- [ ] Supervisor handles interruption gracefully
- [ ] Concurrent run prevention works
- [ ] Rate limit backoff works
- [ ] Run all 5 benchmark tasks again. Compare metrics to Phase 4 baselines.
- [ ] CHANGELOG.md updated

---

## Phase 5+: Future Expansion (Not Scheduled)

These are recorded here for completeness. Do not start any of these until Phases 0-5 are stable and producing value on real tasks.

- **Multiple repo support:** Test the system on a second repo with a different stack
- **Parallel tasks:** Multiple worktrees for independent features
- **OpenClaw operator shell:** Chat-based status and kickoff interface
- **Zep memory:** Semantic search over operational memory (only if file-based becomes a bottleneck)
- **Specialized test-fixer agent:** Separate Codex instance for targeted test repair
- **Auto-PR creation:** `gh pr create` after READY state
- **CI integration:** Trigger runs from GitHub Actions or webhooks
- **Cost dashboard:** Track spend per task, per agent, over time

---

## Risk Mitigation Across All Phases

| Risk | Mitigation | Phase |
|------|-----------|-------|
| Repo not automation-ready | Phase 0 validates every contract command manually | 0 |
| acpx alpha instability | Builder adapter has direct-CLI fallback | 2 |
| Codex session drops | Session recovery with context summary | 5 |
| Claude API rate limits | Exponential backoff | 5 |
| False completion | Supervisor-enforced gates, COMPLETE requires evidence | 1 |
| Builder writes to forbidden paths | Policy engine blocks at execution time | 1 |
| Flaky tests stall the loop | Flaky test detection and quarantine | 5 |
| Cost blowup | Budget enforcement kills the run | 1 |
| Stale memory | TTL on operational memory entries | 5 |
| Multiple runs collide | Concurrent run prevention lock | 5 |

---

## Summary: Who Does What

| Phase | Trevor | Codex | Claude |
|-------|--------|-------|--------|
| 0 | Write repo contract, benchmark tasks, validate tools | (optional) Create directory structure | — |
| 1 | Manual integration test | Build all supervisor modules | Audit supervisor code |
| 2 | Run benchmarks, record metrics | Build builder adapter + simple strategy | Audit builder adapter |
| 3 | Run frontend benchmarks | Build UI verifier, update strategy | Audit UI verifier |
| 4 | Comparative testing | Integrate Claude strategy layer | Design all prompts + StrategyDecision schema |
| 5 | Run final benchmarks | Build memory, flaky test, hardening features | Audit everything |

---

## Definition of Done for the Entire System

The autonomous coding system is operational when:

- [ ] Given a run contract, it can autonomously complete a multi-file frontend+backend task
- [ ] It runs quality gates (lint, typecheck, test) independently of the builder
- [ ] It launches the app and verifies the UI with Playwright
- [ ] It routes failures back to the builder and retries within budget
- [ ] It produces a structured readiness report with artifacts
- [ ] It does all of this without human intervention between kickoff and result
- [ ] It costs less than $10 per typical task
- [ ] It completes 3/5 benchmark tasks autonomously on repeated runs
- [ ] It has been used on at least 10 real (non-benchmark) tasks successfully
