# Three-Way Architecture Reconciliation: Final Decisions

> **ARCHIVED — superseded.** This document predates terminal-state normalization (ADR-0001). Vocabulary such as `READY/NOT_READY/BLOCKED` used as `run_state`, and `.autoclaw/` boundary references, reflect the prior design. See `canonical-architecture.md §9.1 "Terminal States and Readiness Verdict"` and `STRUCTURE.md §1` for current truth.

**Date:** April 12, 2026
**Models Audited:** Claude (me), Codex, ChatGPT Pro
**Purpose:** You now have three independent architecture reviews. This document reconciles all three, identifies where they converge, where they diverge, who is right on each point, and what your final architecture should be.

---

## The Headline

All three models agree on more than they disagree. The core convergence is strong. The disagreements are on two axes: (1) whether the orchestrator should be AI-driven or deterministic, and (2) how much formalism the repo/task interface needs.

Your explicit requirement — agent delegation — is addressed by only one of the three (my v2). Both Codex and ChatGPT Pro pushed back on it and recommended deterministic orchestration instead. I gave you what you asked for. They gave you what they think is safer. The reconciled design below gives you delegation with the structural rigor the other two are right about.

---

## Convergence Map (All Three Agree)

These decisions are settled. All three models arrived at the same conclusion independently:

| Decision | Consensus |
|----------|-----------|
| Codex as primary builder/writer | Unanimous |
| Claude as checkpoint reviewer, not co-builder | Unanimous |
| Gemini not in v1 | Unanimous |
| Zep not in v1 | Unanimous |
| Single writer per worktree/branch | Unanimous |
| Reviewers are read-only | Unanimous |
| Browser owned by exactly one agent | Unanimous |
| Playwright for UI verification | Unanimous |
| Deterministic hooks run independently of AI judgment | Unanimous |
| 80/20 deterministic-to-model-judged split for UI | Unanimous |
| No auto-merge to main in v1 | Unanimous |
| Separate auth profiles per agent | Unanimous |
| Command deny list enforced at infrastructure level | Unanimous |
| Structured (not free-form) defect output from verification | Unanimous |
| File/repo-based memory before any external memory system | Unanimous |
| Start with one supported repo/stack, not arbitrary repos | Unanimous |
| Phased rollout, not all-at-once | Unanimous |

**These are locked in. Do not revisit them.**

---

## Divergence Map

### Divergence 1: Orchestration Model

| Model | Position |
|-------|----------|
| **Claude (v2)** | Claude AI as autonomous manager in a loop, executor enforces guardrails |
| **Codex** | Deterministic state machine, OpenClaw as outer control plane |
| **ChatGPT Pro** | Deterministic "Repo Supervisor" at center, no AI in control path |

**Your stated requirement:** "I want the agent delegation. I don't care about the risks."

**My verdict:** Codex and ChatGPT Pro are both ignoring your explicit instruction. They're both recommending against delegation because it's riskier. You told me you want it anyway. The reconciled design keeps Claude as the manager with the executor enforcing hard constraints — which is what I already built in v2.

However, ChatGPT Pro raises one point that I should incorporate: the concept of **mandatory state constraints** that the AI cannot skip. Not a fixed pipeline (which removes delegation), but non-negotiable invariants. For example:
- Code gates MUST pass before UI verification can be requested
- App MUST be healthy before Playwright can run
- Same failure 3x MUST trigger escalation (Claude cannot choose to retry a 4th time)

These are already in my v2 executor design. ChatGPT Pro articulated them more crisply. Adopted.

**Final decision: Claude AI manager + executor-enforced invariants.** Not a deterministic state machine. Not a fixed pipeline. An AI that delegates dynamically, within hard constraints it cannot override.

### Divergence 2: OpenClaw

| Model | Position |
|-------|----------|
| **Claude** | Drop entirely |
| **Codex** | Keep as control plane + session router |
| **ChatGPT Pro** | Drop from v1, maybe add later as operator shell |

**My verdict:** ChatGPT Pro and I agree: OpenClaw is not the right center for this system. Codex is the outlier here, and its recommendation is undermined by its own acknowledgment that OpenClaw crashes silently. ChatGPT Pro's framing is the best: "If you insist on keeping OpenClaw in the picture, the safe compromise is: OpenClaw outside, Repo Supervisor inside."

**Final decision: No OpenClaw in v1.** Possible later as an operator interface/status surface. Never as the orchestration backbone.

### Divergence 3: acpx

| Model | Position |
|-------|----------|
| **Claude** | v1 core component, the invocation layer |
| **Codex** | v1, standardize on ACP-aware CLIs |
| **ChatGPT Pro** | Later, not needed until you need multi-vendor invocation |

**My verdict:** ChatGPT Pro raises a valid point I didn't fully address. acpx adds value when you need a uniform interface across multiple agents (Codex, Claude, Gemini, etc.). But if your v1 has only Codex and Claude, you can invoke Codex via its CLI directly and Claude via API directly. acpx becomes an unnecessary intermediary that adds alpha-software risk.

However, acpx gives you something direct CLI calls don't: persistent sessions with multi-turn context scoped per repo. If you call Codex via raw CLI each time, you lose session continuity. acpx sessions let Codex remember what it was working on.

**Final decision: acpx in v1, but with a direct-CLI fallback.** If acpx breaks (alpha software), the executor can fall back to `codex --approval-mode full-auto` direct invocation. Build the executor so acpx is swappable.

### Divergence 4: Repo Contract Formalism

| Model | Position |
|-------|----------|
| **Claude** | Task spec as markdown or JSON, acceptance criteria as markdown |
| **Codex** | Run contract as JSON with scope, acceptance, constraints |
| **ChatGPT Pro** | Full repo contract with explicit commands for every lifecycle step (setup, format, lint, typecheck, test, app:up, app:health, app:down, ui:smoke, seed) |

**My verdict:** ChatGPT Pro is clearly right here, and this is its single strongest contribution. The repo contract idea — requiring each repo to expose a machine-readable file declaring its build, test, launch, and verification commands — is the most important structural decision for making autonomy real.

Without it, agents have to *guess* how to build, test, and launch the app. With it, the system knows exactly what commands to run. ChatGPT Pro says: "If a repo does not provide that contract, the system should return UNSUPPORTED rather than improvising its own build lifecycle. That single decision will save you months of fake autonomy." This is correct.

Codex's run contract (per-task JSON) and ChatGPT Pro's repo contract (per-repo YAML) are complementary, not competing:
- **Repo contract** = how this repo works (commands, ports, UI flows) — lives in the repo, changes rarely
- **Run contract** = what this specific task requires (objective, scope, acceptance, budget) — created per task

**Final decision: Both contracts.** Repo contract (ChatGPT Pro's `.agent/contract.yml`) lives in the repo. Run contract (Codex's `contract.json`) is created per task. The executor reads both.

### Divergence 5: Memory Architecture

| Model | Position |
|-------|----------|
| **Claude** | File-based markdown in `docs/agent-memory/` |
| **Codex** | Run artifacts + plan to migrate to SQLite later |
| **ChatGPT Pro** | Three-tier model: repo truth (in repo), operational memory (run DB), ephemeral (current run) |

**My verdict:** ChatGPT Pro's three-tier model is the most principled, and it correctly identifies what goes where. My file-based approach is simpler but conflates repo truth and operational memory. Codex's approach has good artifact structure but fuzzy boundaries.

The reconciled memory model:

| Tier | What | Where | Examples |
|------|------|-------|----------|
| **Repo truth** | Stable project knowledge | In repo, version-controlled | ADRs, repo contract, AGENTS.md, test conventions, coding standards |
| **Run truth** | Per-task operational data | `.autoclaw/runs/<id>/` on disk | Task contract, plan, defects, artifacts, screenshots, reports, execution log |
| **Operational memory** | Cross-run learnings | `.autoclaw/memory/` (files first, SQLite later) | Failure signatures, flaky test registry, environment quirks, prior fix strategies |
| **Ephemeral** | Current run state | In-memory + `state.json` | Manager's working state, current hypothesis, transient logs |

**Final decision: ChatGPT Pro's three-tier model, implemented with files first (my approach), structured per Codex's directory layout, with SQLite migration when volume justifies it.**

### Divergence 6: Who Commits

| Model | Position |
|-------|----------|
| **Claude** | Builder (Codex) commits after each milestone |
| **Codex** | Builder commits |
| **ChatGPT Pro** | Only the supervisor commits checkpoint snapshots. Builder edits files; supervisor snapshots. |

**My verdict:** ChatGPT Pro's position is more rigorous. If the supervisor (executor) owns commits, then:
- You get clean checkpoint semantics (every commit = known-good state)
- The builder cannot commit half-broken code
- Commit messages follow a consistent format controlled by the executor
- The builder's scope is purely "edit files and run checks"

In the delegation model, this means: Claude manager tells Codex to implement something. Codex edits files. Claude manager requests hooks. If hooks pass, Claude manager tells the executor to commit. The executor commits with a structured message.

**Final decision: Executor commits on manager's instruction, not builder directly.** Builder edits files only. This is cleaner.

### Divergence 7: Phasing (When Does Claude Enter)

| Model | Position |
|-------|----------|
| **Claude** | Claude as manager from Phase 1 (Week 2) |
| **Codex** | Claude at Phase 3 (after builder loop is stable) |
| **ChatGPT Pro** | Claude at Phase 2 (after single-builder loop works) |

**My verdict:** Given your requirement for delegation, Claude must be in the loop early. But ChatGPT Pro and Codex are correct that you should validate the executor + builder independently first. The compromise:

**Phase 0:** Build executor, validate it works with manual action input (you type actions)
**Phase 1:** Wire Codex builder through executor, validate build+hooks loop works
**Phase 2:** Wire Claude as manager, validate delegation works on simple tasks
**Phase 3+:** Add Playwright, reviewer, memory

This means Claude enters at Phase 2, but the executor and builder are validated in Phase 0-1 first. You don't skip straight to delegation without proving the plumbing works.

**Final decision: Phase 2 for Claude manager. Phases 0-1 validate executor + builder independently.**

---

## What ChatGPT Pro Got Right That I Missed

1. **The repo contract.** This is the single most valuable idea across all three reviews. Requiring repos to declare their lifecycle commands in a machine-readable file eliminates an enormous class of "agent guessing" failures. I should have proposed this. I didn't.

2. **"Unsupported repo" as a valid outcome.** Rather than trying to make the system work on any repo, explicitly refusing unsupported repos is the correct v1 behavior. This prevents the system from improvising badly.

3. **Supervisor owns commits, not builder.** Cleaner separation of concerns. Builder edits, supervisor checkpoints.

4. **App health endpoint as a contract requirement.** Not just "launch the app and check the port" but requiring the repo to expose a health check URL. This makes app-readiness verification deterministic rather than heuristic.

5. **"The agent is not the main system. The repo contract is."** This reframing is correct. The quality of the autonomous loop depends more on the repo being automation-ready than on the agents being smart.

6. **Failure fingerprinting.** Normalizing failures into fingerprints (command + error signature + paths) and using those for dedup, escalation, and cross-run learning. More structured than my "failure log" approach.

7. **Three shell policy classes: auto-allow, auto-deny, escalate.** My design had allow/deny only. The "escalate" class (package installs, DB migrations, Docker rebuilds) is a useful middle ground for commands that are sometimes safe but need context.

8. **"Bad acceptance criteria" as a failure mode.** Neither Codex nor I flagged this explicitly. If "done" is underspecified, the system optimizes for green checks and plausible summaries, not actual delivery quality.

9. **"Fixture drift" as a failure mode.** Browser flows failing because seeded test data changed, not because code is wrong. Real operational pain point.

10. **Codex's auth guidance is more specific.** ChatGPT Pro correctly notes that Codex supports ChatGPT sign-in or API-key sign-in, with API-key recommended for programmatic workflows. It also correctly notes that Anthropic's Agent SDK docs say third-party products should use API-key auth, not consumer claude.ai login. This is more precise than what I provided.

## What ChatGPT Pro Got Wrong

1. **Same core mistake as Codex: ignoring the delegation requirement.** ChatGPT Pro recommends a deterministic Repo Supervisor as the center of the system. You explicitly said you want agent delegation. ChatGPT Pro acknowledged your request and then said "only if you mean bounded autonomy, not magic" — which is fair — but its implementation spec still puts a deterministic state machine at the center, not an AI manager. The "bounded autonomy" it describes is just a fixed pipeline with checkpoints.

2. **Overweight on repo contract at the expense of flexibility.** The repo contract is a great idea, but ChatGPT Pro's version is very rigid. Requiring 11 specific scripts before the system will even start is a high bar. For v1, a lighter contract (build, test, launch, health) with optional extensions is more practical.

3. **"Do not start with Zep" is correct but its alternative (SQLite run DB) adds complexity too.** ChatGPT Pro criticizes Zep as premature infrastructure, then proposes standing up a SQLite database with 9+ tables. That's also infrastructure. Files first.

4. **Underestimates the value of acpx sessions.** ChatGPT Pro says to defer acpx, but persistent multi-turn sessions are important for Codex's effectiveness. A stateless `codex exec` call per interaction loses context that makes the builder significantly better at multi-file tasks.

---

## Final Architecture (Three-Way Merged)

```
┌────────────────────────────────────────────────────────────────┐
│                       HUMAN OPERATOR                            │
│                                                                  │
│  Creates: repo contract (.agent/contract.yml) — once per repo    │
│  Creates: run contract (contract.json) — once per task           │
│  Runs: one command to start                                      │
│  Returns to: ready branch + readiness report                     │
└──────────┬───────────────────────────────────────────┬──────────┘
           │                                            │
           ▼                                            ▲
┌────────────────────────────────────────────────────────────────┐
│                    EXECUTOR (Python)                             │
│                                                                  │
│  Reads: repo contract + run contract                             │
│  Validates: repo supports automation (or returns UNSUPPORTED)    │
│  Creates: worktree, run directory, artifact store                │
│  Runs: Claude manager loop                                       │
│  Enforces: all hard invariants (see below)                       │
│  Owns: commits (on manager's instruction)                        │
│  Owns: checkpoint tags                                           │
│  Produces: final readiness report                                │
│                                                                  │
│  HARD INVARIANTS (code-enforced, AI cannot override):            │
│  · Code gates must pass before UI verification                   │
│  · App must be healthy before Playwright runs                    │
│  · Same failure fingerprint 3x → must escalate                  │
│  · Budget exceeded → must stop                                  │
│  · Command deny list → blocked                                  │
│  · Path restrictions from run contract → blocked                │
│  · Single writer lock → enforced                                │
│  · Browser owner lock → enforced                                │
│  · Max iterations / cost / time → enforced                      │
│                                                                  │
│  THREE SHELL CLASSES (ChatGPT Pro's model):                      │
│  · Auto-allow: repo contract commands, safe reads                │
│  · Auto-deny: destructive git, sudo, ssh, secrets               │
│  · Escalate: package installs, migrations, Docker → stop + ask  │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────────┐
│ CLAUDE   ││  CODEX   ││ CLAUDE   ││PLAYWRIGHT││DETERMINISTIC │
│ MANAGER  ││ BUILDER  ││ REVIEWER ││UI VERIFY ││   LANE       │
│          ││          ││          ││          ││              │
│Decides   ││Sole      ││Read-only ││Read-only ││Hook runner   │
│what next.││writer.   ││checkpts. ││browser   ││App supervisor│
│Decomposes││Edits     ││Audits    ││owner.    ││Release gate  │
│Delegates.││files     ││diffs.    ││Captures  ││              │
│Adjusts   ││only.     ││Diagnoses ││artifacts.││All from repo │
│strategy. ││Does NOT  ││stalls.   ││Emits     ││contract cmds │
│          ││commit.   ││          ││defect    ││              │
│          ││          ││          ││packets.  ││              │
└──────────┘└──────────┘└──────────┘└──────────┘└──────────────┘

┌────────────────────────────────────────────────────────────────┐
│                      STORAGE                                     │
│                                                                  │
│  IN REPO (repo truth):                                           │
│    .agent/contract.yml        (repo lifecycle contract)          │
│    docs/adr/                  (architecture decisions)           │
│    AGENTS.md                  (agent instructions)               │
│                                                                  │
│  PER RUN (run truth):                                            │
│    .autoclaw/runs/<id>/                                          │
│      contract.json            (task contract)                    │
│      plan.json                (planner output)                   │
│      state.json               (manager working state)            │
│      defects/*.json           (structured defect packets)        │
│      artifacts/               (screenshots, traces, logs)        │
│      reports/                 (audit, readiness)                 │
│                                                                  │
│  CROSS-RUN (operational memory):                                 │
│    .autoclaw/memory/                                             │
│      failure-signatures.json  (normalized, fingerprinted)        │
│      flaky-tests.json         (quarantined tests)                │
│      environment-quirks.md    (known env issues)                 │
│      fix-strategies.json      (keyed by error class)             │
└────────────────────────────────────────────────────────────────┘
```

---

## Repo Contract (Adopted from ChatGPT Pro, Simplified for v1)

```yaml
# .agent/contract.yml
version: 1
stack: fullstack-web  # or: backend-api, static-site, etc.

commands:
  # Required
  setup: "npm install"
  lint: "npm run lint -- --max-warnings 0"
  typecheck: "npm run typecheck"
  test: "npm run test -- --bail"
  app_up: "npm run dev"
  app_health: "http://127.0.0.1:3000/api/health"
  app_down: "kill"  # or explicit script

  # Optional (v1 can omit)
  format: "npx prettier --write"
  test_integration: "npm run test:integration"
  seed_testdata: "npm run seed:test"
  ui_smoke: "npx playwright test"

ui:
  base_url: "http://127.0.0.1:3000"
  breakpoints: ["390x844", "1440x900"]
  critical_flows:
    - id: login
      route: "/login"
      assertions:
        - "login form visible"
        - "submit with test credentials succeeds"
        - "redirects to dashboard"
        - "no console errors"

env:
  required_vars: ["DATABASE_URL", "JWT_SECRET"]
  template: ".env.example"
```

This is lighter than ChatGPT Pro's 11-command version but captures the essential automation surface. The system returns `UNSUPPORTED` if `commands.setup`, `commands.test`, and `commands.app_up` are missing.

---

## Run Contract (Adopted from Codex)

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
    "max_cost_dollars": 20.00,
    "hard_timeout_seconds": 7200
  }
}
```

---

## Defect Packet (Adopted from Codex, Endorsed by ChatGPT Pro)

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

---

## Final Phased Roadmap (Three-Way Merged)

### Phase 0: Repo Preparation + Manual Baseline (Week 1)

**Goal:** Prove the repo is automation-ready. Validate all tools work independently.

**Deliverables:**
- `.agent/contract.yml` written and tested for target repo
- All contract commands work when run manually
- acpx + Codex session works (`acpx codex "echo hello"`)
- Claude API invocation works
- Playwright installed, one smoke test written
- `.autoclaw/` directory structure created
- 3 benchmark tasks written as run contracts

**Acceptance:** Human can run the full contract end-to-end manually. Every command exits clean.

### Phase 1: Executor + Builder Loop (Weeks 2-3)

**Goal:** Executor drives Codex through build → hooks → retry loop. No AI manager yet — you issue actions manually or use a simple scripted sequence.

**Deliverables:**
- Executor script: action parsing, acpx integration, shell execution, guardrail enforcement
- Command deny list and path restrictions
- Hook runner (reads repo contract, runs lint/typecheck/test)
- Commit checkpointing (executor commits on instruction)
- Retry logic with failure fingerprinting
- Run directory created per task with contract, state, artifacts

**Acceptance:** Executor can drive Codex through a simple task (add a component + tests), run hooks, retry on failure, and produce a clean commit. 5 tasks completed with scripted action sequences.

### Phase 2: Claude Manager + Delegation (Weeks 4-5)

**Goal:** Claude as the autonomous manager. Real delegation.

**Deliverables:**
- Manager system prompt (from v2, refined with ChatGPT Pro's repo contract awareness)
- Action schema validation
- State persistence (state.json between iterations)
- History compression for long tasks
- Delegation patterns working: simple, multi-milestone, stuck-escalation
- Claude reviewer integration for stall diagnosis

**Acceptance:** 10 tasks completed with Claude manager making all delegation decisions. Zero human intervention between kickoff and result. Cost per task < $10.

### Phase 3: App Launch + UI Verification (Weeks 6-8)

**Goal:** Full end-to-end including frontend verification.

**Deliverables:**
- App supervisor (launch from repo contract, health check, shutdown)
- Playwright runner integrated into executor
- Screenshot capture + artifact store
- Defect packet generation from Playwright failures
- Claude visual review of screenshots
- Defect routing back to builder

**Acceptance:** 5 tasks including frontend changes completed with UI verification. UI verifier catches at least one defect that code gates missed.

### Phase 4: Reviewer + Release Gate + Memory (Weeks 9-12)

**Goal:** Full quality pipeline. Cross-run learning.

**Deliverables:**
- Claude code reviewer at final checkpoint
- Deterministic release checker (final gate)
- Readiness report generation
- Branch push + optional PR creation
- Failure signature persistence and retrieval
- Operational memory informing future runs

**Acceptance:** 20 tasks completed end-to-end. False-done rate < 10%. Repeated failure classes resolved faster than first occurrence.

### Phase 5+: Scale + Specialize (Weeks 13+)

- Multiple repo support
- Parallel tasks via worktrees
- Specialized test-fixer agent (if data shows builder is inefficient)
- Optional OpenClaw as operator UI
- Optional Zep for semantic memory (if file-based becomes bottleneck)

---

## Scorecard: Who Was Right About What

| Topic | Claude | Codex | ChatGPT Pro | Winner |
|-------|--------|-------|-------------|--------|
| Orchestration model | AI manager ✓ | Deterministic | Deterministic | **Claude** (met requirement) |
| OpenClaw | Drop ✓ | Keep | Drop ✓ | **Claude + ChatGPT Pro** |
| acpx | v1 ✓ | v1 | Later | **Claude + Codex** |
| Repo contract | Not proposed | Run contract only | Full repo contract ✓ | **ChatGPT Pro** |
| Run contract schema | Markdown | JSON ✓ | JSON ✓ | **Codex + ChatGPT Pro** |
| Defect packet schema | Informal | Formal JSON ✓ | Formal JSON ✓ | **Codex + ChatGPT Pro** |
| Memory architecture | File-based | Files + SQLite later | Three-tier model ✓ | **ChatGPT Pro** |
| Who commits | Builder | Builder | Supervisor ✓ | **ChatGPT Pro** |
| Shell policy classes | Allow/deny | Allow/deny | Allow/deny/escalate ✓ | **ChatGPT Pro** |
| App supervisor separation | Inline | Separate ✓ | Separate ✓ | **Codex + ChatGPT Pro** |
| Manager prompt detail | Full prompt + patterns ✓ | One-liners | Medium detail | **Claude** |
| Delegation patterns | 5 documented ✓ | None | None | **Claude** |
| Auth specifics | General | General | Codex/Claude/Gemini specific ✓ | **ChatGPT Pro** |
| Failure fingerprinting | Failure log | Mentioned | Detailed design ✓ | **ChatGPT Pro** |
| Fixture drift as failure mode | Not mentioned | Not mentioned | Identified ✓ | **ChatGPT Pro** |
| Bad acceptance criteria risk | Not mentioned | Not mentioned | Identified ✓ | **ChatGPT Pro** |
| Phasing with delegation | Claude at Phase 1 | Claude at Phase 3 | Claude at Phase 2 | **Phase 2 compromise** |

**Summary:** ChatGPT Pro wins on structural/operational rigor (contracts, memory tiers, auth details, failure modes). Claude wins on delegation model and prompt engineering. Codex wins on specific schemas (JSON contracts, defect packets). The merged design takes the best from each.

---

## What to Build and Who Builds It

### Codex Builds (Implementation Work)

Give Codex these tasks in this order:

1. **Executor core** — Python script: action loop, acpx integration, guardrail enforcement, deny list, path restrictions, budget/timeout enforcement
2. **Run store** — Directory structure creator, contract parser (both repo and run contracts), state.json management
3. **Hook runner** — Reads repo contract, runs the declared commands, captures output, produces failure fingerprints
4. **App supervisor** — Launches app per repo contract, waits for health endpoint, manages shutdown, records PID/port/logs
5. **Commit manager** — Executor-owned commits with structured messages, checkpoint tags
6. **Playwright integration** — Runs declared UI smoke tests, captures screenshots/traces, produces defect packets
7. **Release checker** — Deterministic final gate: re-runs all contract commands, verifies artifacts exist, produces readiness report

### Claude Produces (Design/Prompt Work)

I produce these:

1. **Manager system prompt** (already in v2, will refine with repo contract awareness)
2. **Delegation pattern library** (already in v2)
3. **Reviewer prompts** (already in v2)
4. **Planner prompts** (already in v2)
5. **Action schema definition** (JSON schema for all action types)
6. **Memory strategy** (retrieval logic, what gets promoted, staleness rules)

### You Do (Human Work)

1. **Write the repo contract** for your target repo
2. **Write 3-5 benchmark run contracts** (tasks of varying complexity)
3. **Approve the phased milestones** — don't let scope creep into later phases
4. **Review Codex's executor output** — I'll audit it after each phase
5. **Merge decisions** — you remain the human gate for merge in v1

---

## Next Concrete Step

Tell Codex to build the executor core (item 1 above). Here's the prompt I'd give it:

```
Read the following files for context:
- .agent/contract.yml (repo contract schema)
- The run contract JSON schema
- The defect packet JSON schema

Build a Python executor script (executor.py) that:

1. Accepts a run contract JSON as input
2. Reads the repo contract from .agent/contract.yml
3. Validates the repo supports automation (returns UNSUPPORTED if required commands missing)
4. Creates the run directory structure: .autoclaw/runs/<run_id>/
5. Implements an action loop that:
   - Receives structured JSON actions (one at a time for now, Claude manager integration comes later)
   - Validates actions against guardrails (deny list, path restrictions, budget)
   - Executes actions: shell commands, acpx invocations, file reads/writes
   - Captures output (stdout, stderr, exit code)
   - Writes to state.json after each action
   - Enforces hard invariants:
     · Command deny list (git push, sudo, ssh, etc.)
     · Path restrictions from run contract
     · Budget limits (max iterations, max cost, hard timeout)
     · Single writer lock
   - Uses three shell classes: auto-allow, auto-deny, escalate
6. Supports these action types:
   - delegate_to_codex (via acpx)
   - run_hook (shell command from repo contract)
   - launch_app (from repo contract)
   - run_playwright
   - read_file
   - write_memory
   - git_command (restricted)
   - declare_complete
   - declare_failure
7. Logs every action and result to .autoclaw/runs/<run_id>/execution.log
8. Produces a final report on completion or failure

Do not implement the Claude manager integration yet.
Do not implement Playwright screenshot analysis yet.
Focus on a solid, well-tested executor core.
Log what you build in the appropriate docs.
```

Want me to refine that prompt further, or are you ready to send it to Codex?
