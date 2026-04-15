# Autonomous Multi-Agent Coding System: Architecture Review & Redesign

> Historical archive note: this document is preserved as context, not as current architecture. Use `../canonical-architecture.md`, `../STRUCTURE.md`, `../RULES.md`, and `../GUIDE.md` for current guidance.

**Prepared for:** Trevor (trevor@gillettewsc.com)
**Date:** April 12, 2026
**Role:** Principal AI Systems Architect / Adversarial Reviewer

---

## 1. Executive Verdict

**Conditionally sound.** The concept of an autonomous multi-agent coding loop is viable, but the proposed stack has a critical structural weakness: **OpenClaw is the wrong control plane for this system.**

### The Single Most Important Architecture Change

**Replace OpenClaw as the orchestration layer with a deterministic script-driven pipeline (shell scripts + GitHub Actions or a simple state machine in Python/Node), using acpx as the agent invocation layer directly.**

Here is why:

OpenClaw is a messaging-app-oriented agent framework designed for WhatsApp/Telegram/Discord interaction. It runs as a long-lived Node.js Gateway process. Multiple practitioners have reported that when the Gateway crashes, the entire pipeline goes silent with no audit trail. It was not designed to be a reliable CI/CD-style orchestration backbone. Its strengths (conversational UX, multi-platform messaging integration) are irrelevant to your use case. Its weaknesses (crash recovery, deterministic flow control, auditability) are directly in the critical path.

You do not need a conversational agent framework to orchestrate agents. You need a reliable execution pipeline that calls agents at defined checkpoints. That is a fundamentally different thing, and conflating the two will cost you months of debugging flaky orchestration instead of building the actual system.

**acpx already provides the structured agent invocation surface you need.** A simple orchestration script that calls `acpx codex "do X"`, checks exit codes, runs deterministic hooks, and calls `acpx claude "review Y"` at checkpoints will be more reliable on day one than OpenClaw will be after weeks of configuration.

---

## 2. Reality Check on the Stack

| Component | Verdict | Rationale |
|-----------|---------|-----------|
| **OpenClaw** | **Not in v1. Maybe never.** | Wrong tool for the job. You need deterministic pipeline orchestration, not a messaging-bot framework. OpenClaw adds a crash-prone, hard-to-debug intermediary between you and the agents. The OpenClaw Gateway is a single point of failure with poor observability. If you want a UI later, bolt one onto the pipeline — do not build the pipeline inside a chat framework. |
| **acpx** | **v1, core component.** | This is the right abstraction. It gives you structured, session-aware, protocol-based invocation of Codex, Claude, and others from a single CLI surface. It is in alpha, which is a real risk, but the alternative (PTY scraping or bespoke adapters) is worse. Pin a version. Write integration tests against it. |
| **Codex** | **v1, primary worker.** | Correct choice as the workhorse. Full-auto mode, subagent spawning, and Rust-based performance make it the best available autonomous builder. Key limitation: no MCP/local tool integration and limited multi-file coordination in very large codebases. Plan for this. |
| **Claude** | **v1, selective reviewer/planner.** | Correct role assignment. Claude should not be writing code in the hot loop. Use it for: initial planning, architecture review at milestones, debugging failures Codex cannot resolve after N retries, and final audit before merge. |
| **Gemini** | **Not in v1.** | There is no clear, non-redundant role for Gemini in this system right now. Adding a third model increases complexity, auth surface, cost, and failure modes without a demonstrated capability gap. Revisit only if you hit a specific task where Codex and Claude both underperform. |
| **Zep** | **Not in v1. Simpler alternative first.** | Zep is a powerful temporal knowledge graph, but it is massive overkill for the first version. Your memory needs are: architecture decisions, prior failure logs, acceptance criteria, and project context. Markdown files in the repo (a `docs/memory/` directory with structured files) will serve this purpose with zero infrastructure, zero latency concerns, and full git history. Agents can read these files directly. Move to Zep only when you have evidence that file-based memory is the bottleneck. |
| **Browser automation** | **v1, but isolated and simple.** | Critical for frontend verification. But it must be owned by exactly one agent at a time, use a dedicated browser profile, and run after the build agent has finished and the app is launched. Playwright is the correct tool. Do not try to have the builder and the verifier share a browser session. |
| **Hooks / guardrails** | **v1, implement first.** | Deterministic hooks (lint, format, typecheck on every file save; test on every meaningful change) are the highest-ROI investment in the system. They catch problems before expensive model calls. Implement these before anything else. |
| **Worktrees / branch isolation** | **v1, simplified.** | One worktree for the builder. The reviewer reads from that worktree but does not write to it. No per-agent branches in v1 — one working branch per task, one agent writing at a time. This eliminates merge conflicts entirely. |
| **MCP tools** | **Later, not v1.** | MCP integration adds complexity. Codex does not support MCP currently. Claude does, but you are not using Claude as a worker. Defer this until you need specific tool integrations that cannot be handled by shell commands. |

---

## 3. Recommended System Architecture (v1)

### Top-Level Orchestration Design

The orchestrator is a **deterministic state machine** implemented as a shell script or Python script. It is not an AI agent. It does not make judgment calls. It follows a defined pipeline with explicit checkpoints where it invokes AI agents via acpx.

```
┌──────────────────────────────────────────────────┐
│              PIPELINE ORCHESTRATOR                │
│        (shell script / Python state machine)      │
│                                                   │
│  Reads: task spec, acceptance criteria            │
│  Drives: acpx calls, hook execution, state mgmt  │
│  Writes: logs, reports, state files               │
└──────┬───────────┬──────────┬──────────┬─────────┘
       │           │          │          │
       ▼           ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
  │  CODEX  │ │ CLAUDE │ │ HOOKS  │ │PLAYWRIGHT│
  │ (build) │ │(review)│ │(determ)│ │  (UI)    │
  │ via     │ │ via    │ │ shell  │ │ via      │
  │ acpx    │ │ acpx   │ │ cmds   │ │ script   │
  └─────────┘ └────────┘ └────────┘ └──────────┘
```

### Agent Topology

**Serial by default.** The pipeline runs one agent at a time in a defined sequence. There is no concurrent multi-agent execution in v1. This is deliberate: concurrency introduces collision risks, debugging complexity, and race conditions that will consume more time than they save at this scale.

The execution order for a single task cycle is:

1. Orchestrator reads task spec
2. Claude plans (via acpx) — produces implementation plan
3. Codex builds (via acpx) — implements the plan
4. Deterministic hooks run (lint, format, typecheck, test)
5. If hooks fail → Codex fixes (loop, max N retries)
6. App launches (deterministic script)
7. Playwright runs UI verification
8. If UI fails → Codex fixes (loop, max N retries)
9. Claude reviews (via acpx) — final audit
10. If review fails → Codex addresses review items (loop, max 2 retries)
11. Orchestrator reports status

### Who Runs Where

| Component | Runtime | Location |
|-----------|---------|----------|
| Orchestrator | Local machine or CI runner | Host |
| Codex | Cloud execution via acpx | OpenAI infra |
| Claude | API via acpx | Anthropic infra |
| Hooks | Local shell | Same worktree as builder |
| Playwright | Local headless browser | Host, dedicated profile |
| Memory | Markdown files in repo | `docs/agent-memory/` |

### What Each Agent Can and Cannot Do

**Codex (Builder)**
- CAN: read files, write files, run shell commands, run tests, install dependencies, modify any file in the worktree
- CANNOT: push to remote, merge branches, delete branches, access secrets beyond what is in `.env.example`, launch browsers, make network requests to production systems

**Claude (Reviewer)**
- CAN: read files, read diffs, read test output, read logs, produce structured review feedback, produce implementation plans
- CANNOT: write files, run commands, modify the worktree, commit, push

**Playwright (UI Verifier)**
- CAN: launch headless browser, navigate to localhost, take screenshots, run assertion scripts, produce pass/fail reports
- CANNOT: modify code, commit, access external URLs

### Where Things Should Live

- **Browser automation:** Isolated Playwright scripts in `tests/e2e/`, run by the orchestrator after the app is launched, never by the builder agent simultaneously
- **Testing:** Unit/integration tests run as deterministic hooks by the orchestrator. E2E tests run via Playwright after app launch. The builder (Codex) can also run tests during its build loop.
- **Memory:** `docs/agent-memory/` directory with structured markdown files. Categories: `architecture-decisions.md`, `failure-log.md`, `acceptance-criteria.md`, `project-context.md`
- **Review:** Claude invoked at defined checkpoints only (post-plan, post-build, pre-merge). Review output is a structured JSON/markdown report, not free-form conversation.

### Synchronous vs. Checkpoint-Based

| Operation | Mode | Rationale |
|-----------|------|-----------|
| Hook execution (lint, format, typecheck) | Synchronous, blocking | Must pass before proceeding |
| Codex build | Synchronous, blocking | Next steps depend on output |
| Test execution | Synchronous, blocking | Must pass before UI verification |
| App launch | Synchronous, blocking | Must be running before Playwright |
| Playwright UI checks | Synchronous, blocking | Results feed back to builder |
| Claude plan review | Checkpoint (before build) | Can be skipped for small tasks |
| Claude code review | Checkpoint (after build passes) | Blocks merge but not build |
| Claude final audit | Checkpoint (before merge) | Required gate |

### Serialized vs. Parallelized

**Everything is serialized in v1.** The only parallelization opportunity that is safe in v1 is running independent test suites simultaneously (e.g., unit tests + lint + typecheck). The agents themselves must run serially.

Parallelization candidates for later phases: independent feature branches built by separate Codex instances, parallel test sharding, parallel UI verification of independent routes.

---

## 4. Exact Agent Roster

### v1 Agents

#### 1. Pipeline Orchestrator

| Field | Value |
|-------|-------|
| **Name** | `orchestrator` |
| **Purpose** | Drive the pipeline state machine, invoke agents, run hooks, manage retries, produce reports |
| **Underlying model/tool** | None. Deterministic script (bash or Python). No AI. |
| **Permissions** | Full filesystem read/write, shell execution, acpx invocation |
| **Tools allowed** | acpx CLI, git, npm/yarn, shell commands, Playwright runner |
| **Tools denied** | Direct model API calls (all model calls go through acpx) |
| **Expected inputs** | Task specification file (markdown or YAML), acceptance criteria file |
| **Expected outputs** | Execution log, status report, pass/fail determination |
| **Escalation rules** | If any agent fails after max retries → stop pipeline, produce failure report, notify human |
| **Handoff** | Never hands off. It is the top-level controller. |
| **Persistence** | Ephemeral per task run. State persisted to log files. |

#### 2. Planner

| Field | Value |
|-------|-------|
| **Name** | `planner` |
| **Purpose** | Read task requirements, produce implementation plan with milestones, identify architecture decisions |
| **Underlying model/tool** | Claude via acpx (`acpx claude`) |
| **Permissions** | Read-only filesystem access (via acpx session context) |
| **Tools allowed** | File reading, grep, glob |
| **Tools denied** | File writing, shell execution, git operations |
| **Expected inputs** | Task spec, current codebase state, architecture decisions from memory, prior failure logs |
| **Expected outputs** | Structured implementation plan (markdown): milestones, file changes needed, test strategy, acceptance criteria, risk flags |
| **Escalation rules** | If task spec is ambiguous → produce plan with explicit assumptions, flag for human review |
| **Handoff** | Hands plan to orchestrator, which passes it to builder |
| **Persistence** | Ephemeral. Plan output saved to `docs/agent-memory/current-plan.md` |

#### 3. Builder

| Field | Value |
|-------|-------|
| **Name** | `builder` |
| **Purpose** | Implement code changes according to plan, fix test failures, fix lint/format/type errors |
| **Underlying model/tool** | Codex via acpx (`acpx codex`) in full-auto mode |
| **Permissions** | Full read/write on working branch worktree, shell execution for build/test commands |
| **Tools allowed** | File read/write, shell commands (build, test, lint, format), git add/commit on working branch only |
| **Tools denied** | git push, git merge, git branch delete, network requests to external services, browser launch |
| **Expected inputs** | Implementation plan, codebase, hook failure output, UI failure reports |
| **Expected outputs** | Modified codebase, passing hooks, commit(s) on working branch |
| **Escalation rules** | If stuck after 3 retries on same error → escalate to Claude for diagnosis. If stuck after 5 total retries → stop and report. |
| **Handoff** | After all hooks pass → orchestrator runs UI verification. After UI passes → orchestrator invokes reviewer. |
| **Persistence** | Session persists for duration of task (acpx session scoped to repo). Destroyed after task completion. |

#### 4. UI Verifier

| Field | Value |
|-------|-------|
| **Name** | `ui-verifier` |
| **Purpose** | Launch headless browser, verify frontend renders correctly, check for visual regressions, verify interactive elements work |
| **Underlying model/tool** | Playwright scripts + Claude for screenshot analysis (via acpx) |
| **Permissions** | Read-only on codebase, localhost network access only, screenshot capture |
| **Tools allowed** | Playwright API, screenshot capture, localhost HTTP requests, file write for reports/screenshots |
| **Tools denied** | Code modification, git operations, external network access |
| **Expected inputs** | Running app on localhost, acceptance criteria, baseline screenshots (if available) |
| **Expected outputs** | Pass/fail report with screenshots, list of visual/functional defects, structured feedback for builder |
| **Escalation rules** | If app fails to launch → report to orchestrator (infrastructure issue, not code issue). If >3 visual defects → flag for human review. |
| **Handoff** | Failure report goes to orchestrator, which passes it back to builder for fixes |
| **Persistence** | Ephemeral per verification run |

#### 5. Code Reviewer / Auditor

| Field | Value |
|-------|-------|
| **Name** | `reviewer` |
| **Purpose** | Review diffs for correctness, security, maintainability. Verify plan was followed. Check for antipatterns. Final quality gate. |
| **Underlying model/tool** | Claude via acpx (`acpx claude`) |
| **Permissions** | Read-only on codebase and diffs |
| **Tools allowed** | File reading, diff reading, grep, glob |
| **Tools denied** | File writing, shell execution, git operations |
| **Expected inputs** | Git diff (working branch vs base), implementation plan, acceptance criteria, test results, UI verification report |
| **Expected outputs** | Structured review report: pass/fail, blocking issues, non-blocking suggestions, risk assessment |
| **Escalation rules** | If blocking issues found → report to orchestrator for builder to fix. If security concern → stop pipeline, flag human. |
| **Handoff** | If pass → orchestrator proceeds to merge readiness. If fail → orchestrator sends feedback to builder. |
| **Persistence** | Ephemeral per review |

### Agents Deferred to Later Phases

| Agent | Phase | Rationale |
|-------|-------|-----------|
| **Test-fixer (specialized)** | Phase 2 | In v1, the builder handles test fixes. Separate only if builder proves bad at targeted test repair. |
| **Release/readiness checker** | Phase 3 | In v1, the orchestrator handles merge criteria checking deterministically. |
| **Spec agent** | Phase 3 | In v1, task specs are human-written. Auto-spec generation is a distinct capability. |
| **Debugger (specialized)** | Phase 2 | In v1, Claude serves as the escalation debugger. Separate only if escalation volume is high. |

---

## 5. Execution Flow: Start to Finish

Here is the complete lifecycle for a real task, with every step:

### Phase A: Setup (Deterministic)

```
A1. Orchestrator reads task spec from `tasks/current-task.md`
A2. Orchestrator reads acceptance criteria from `tasks/current-acceptance.md`
A3. Orchestrator creates working branch: `git checkout -b agent/task-<id>`
A4. Orchestrator reads `docs/agent-memory/` for context
A5. Orchestrator logs task start to `docs/agent-memory/execution-log.md`
```

### Phase B: Planning (Claude)

```
B1. Orchestrator invokes planner:
    acpx claude "Read the task spec at tasks/current-task.md,
    the acceptance criteria at tasks/current-acceptance.md,
    the architecture decisions at docs/agent-memory/architecture-decisions.md,
    and the failure log at docs/agent-memory/failure-log.md.
    Produce an implementation plan. Output as structured markdown."

B2. Orchestrator saves plan output to docs/agent-memory/current-plan.md
B3. [OPTIONAL] Orchestrator pauses for human approval of plan
    (configurable: --auto-approve or --require-plan-approval)
```

### Phase C: Implementation (Codex)

```
C1. Orchestrator invokes builder:
    acpx codex "Read the implementation plan at docs/agent-memory/current-plan.md.
    Implement all changes described. After each milestone, run:
    - npm run lint
    - npm run typecheck
    - npm run test
    Fix any failures. Commit after each passing milestone."

C2. Codex works in full-auto mode, iterating until hooks pass or retry limit hit.
C3. On completion, Codex reports status via acpx session.
```

### Phase D: Deterministic Verification (Hooks)

```
D1. Orchestrator runs independently (does not trust Codex's self-reported status):
    - npm run lint          → must exit 0
    - npm run format:check  → must exit 0
    - npm run typecheck     → must exit 0
    - npm run test          → must exit 0

D2. If any fail:
    D2a. Orchestrator passes failure output back to builder (max 3 retries)
         acpx codex "The following hook failed: [hook output]. Fix it."
    D2b. If 3 retries exhausted → escalate to Claude for diagnosis
         acpx claude "The builder failed to fix this after 3 attempts: [output].
         Diagnose the root cause and provide specific fix instructions."
    D2c. Pass Claude's diagnosis to builder for 2 more attempts
    D2d. If still failing → stop pipeline, report failure
```

### Phase E: App Launch (Deterministic)

```
E1. Orchestrator launches app:
    npm run dev &
    APP_PID=$!
    wait_for_port 3000 --timeout 30

E2. If app fails to start → pass error to builder for fix, retry Phase C-D
```

### Phase F: UI Verification (Playwright + Claude)

```
F1. Orchestrator runs Playwright test suite:
    npx playwright test tests/e2e/

F2. For visual verification beyond automated assertions:
    - Playwright captures screenshots of key routes
    - Orchestrator invokes Claude with screenshots:
      acpx claude "Review these screenshots against the acceptance criteria
      in tasks/current-acceptance.md. Report any visual defects."

F3. If defects found:
    F3a. Orchestrator compiles defect list
    F3b. Passes to builder: acpx codex "Fix these UI defects: [list]"
    F3c. Re-run Phase D, E, F (max 2 UI fix cycles)

F4. Kill app process: kill $APP_PID
```

### Phase G: Code Review (Claude)

```
G1. Orchestrator generates diff:
    git diff main...agent/task-<id> > /tmp/task-diff.patch

G2. Orchestrator invokes reviewer:
    acpx claude "Review this diff against the implementation plan
    at docs/agent-memory/current-plan.md and acceptance criteria at
    tasks/current-acceptance.md. Check for: correctness, security,
    maintainability, test coverage, adherence to plan.
    Output: structured review with pass/fail and blocking issues."

G3. If blocking issues:
    G3a. Pass to builder: acpx codex "Address these review items: [items]"
    G3b. Re-run Phase D, E, F, G (max 2 review cycles)

G4. If pass → proceed to merge readiness
```

### Phase H: Merge Readiness (Deterministic)

```
H1. Orchestrator checks:
    - All hooks pass (lint, format, typecheck, test)
    - UI verification passed
    - Code review passed
    - All acceptance criteria met
    - No uncommitted changes
    - Branch is up to date with main

H2. If all pass:
    - Generate summary report to docs/agent-memory/execution-log.md
    - Log architecture decisions if any
    - Log any failure patterns to docs/agent-memory/failure-log.md
    - Report: "Task complete. Branch agent/task-<id> ready for merge."

H3. If configured for auto-merge:
    git checkout main && git merge agent/task-<id> --no-ff
```

### Retry Budget Summary

| Phase | Max Retries | Escalation |
|-------|-------------|------------|
| Hook fixes (Codex) | 3 | Escalate to Claude for diagnosis |
| Hook fixes post-diagnosis | 2 | Stop pipeline |
| UI fixes | 2 | Stop pipeline |
| Review fixes | 2 | Stop pipeline |
| App launch | 2 | Stop pipeline |
| **Total max Codex invocations per task** | **~12** | — |
| **Total max Claude invocations per task** | **~4** | Plan + diagnosis + UI review + code review |

---

## 6. Branch, Worktree, and Repo Strategy

### Recommended Strategy: Single Working Branch, Single Worktree

**Do not use multiple worktrees or per-agent branches in v1.** The complexity is not justified when only one agent writes at a time.

```
main (protected)
  └── agent/task-<id> (working branch, one per task)
```

### Rules

**Who can commit:**
- Codex (builder) — the only agent that writes code, therefore the only agent that commits
- Orchestrator — may commit documentation updates to `docs/agent-memory/` after task completion

**Who cannot commit:**
- Claude (reviewer) — read-only, produces reports only
- Playwright (UI verifier) — writes screenshots/reports to a temp directory, never to the repo

**How diffs move between agents:**
- The orchestrator generates diffs (`git diff`) and passes them as input to Claude
- Claude produces structured feedback (not patches)
- The orchestrator passes feedback to Codex as plain text instructions
- At no point does Claude produce code that gets applied to the worktree

**Preventing concurrent destructive edits:**
- Only one agent writes at any time (serialized execution enforces this)
- The orchestrator is the only process that invokes agents
- No agent can invoke another agent directly

**Partial progress and rollback:**
- Codex commits after each passing milestone (small, incremental commits)
- If the pipeline fails and cannot recover:
  - The branch is left in place for human inspection
  - The orchestrator logs the failure state
  - `git reset --hard` to last known good commit is available but requires human approval
- The orchestrator never force-pushes or deletes branches without human confirmation

### When to Introduce Worktrees (Phase 3+)

Multiple worktrees become useful when you want to:
- Run parallel tasks on independent features
- Have a clean worktree for UI verification while the builder continues on another task
- Run integration tests against a stable snapshot while the builder iterates

At that point, the strategy becomes:
```
main (protected)
  ├── agent/task-<id-1> (worktree 1, builder A)
  ├── agent/task-<id-2> (worktree 2, builder B)
  └── verify/task-<id-1> (worktree 3, read-only, UI verifier)
```

---

## 7. Auth, Isolation, and Permissions Model

### Agent Auth Separation

| Agent | Auth Mechanism | Isolation |
|-------|---------------|-----------|
| Codex | OpenAI API key via acpx config | acpx session scoped to repo directory |
| Claude | Anthropic API key via acpx config | acpx session scoped to repo directory |
| Playwright | No API auth needed | Dedicated browser profile directory |
| Orchestrator | Git credentials (for push if enabled) | Runs as host process |

### Secrets Handling

- API keys stored in environment variables, never in repo files
- `.env` file is gitignored and never read by agents directly
- acpx reads API keys from environment or its own config file
- Codex sandbox does not have access to host environment variables beyond what acpx explicitly passes
- No agent can read another agent's API key

**Secret categories:**
| Secret | Who Needs It | How Provided |
|--------|-------------|--------------|
| OpenAI API key | acpx (for Codex) | `OPENAI_API_KEY` env var |
| Anthropic API key | acpx (for Claude) | `ANTHROPIC_API_KEY` env var |
| Git credentials | Orchestrator only | Host git credential store |
| App secrets (DB, etc.) | Codex (for running app) | `.env.local` template, non-production values only |

### Filesystem Access Partitioning

| Agent | Read Access | Write Access |
|-------|------------|-------------|
| Codex | Entire worktree | Entire worktree (working branch only) |
| Claude | Entire worktree (via acpx context) | None |
| Playwright | `tests/e2e/`, app on localhost | `test-results/` directory only |
| Orchestrator | Everything | `docs/agent-memory/`, orchestration logs |

### Shell Command Permissions

| Agent | Shell Access |
|-------|-------------|
| Codex | Full (within acpx sandbox): build, test, lint, install, file operations |
| Claude | None |
| Playwright | Playwright CLI only, no arbitrary shell |
| Orchestrator | Full host shell access |

### Browser Profile Isolation

- Playwright uses a **dedicated profile directory** created fresh for each verification run: `--user-data-dir=/tmp/playwright-profile-<task-id>/`
- No browser state persists between runs
- No agent other than the UI verifier interacts with the browser
- Browser runs in **headless mode** by default (headed mode available for debugging)

### Network Restrictions

| Agent | Network Access |
|-------|---------------|
| Codex | npm registry (for installs), no production APIs |
| Claude | None (API-only via acpx) |
| Playwright | localhost only |
| Orchestrator | npm registry, git remote |

### Which Agents Should Be Read-Only

- **Claude**: Always read-only. Produces text output only.
- **Playwright**: Read-only on code. Write-only to test-results directory.

### Approval Model

**Default: auto-approve with stop conditions.**

The pipeline runs fully autonomously unless:
1. The plan phase produces a risk flag → pause for human review
2. Claude's code review identifies a security concern → stop
3. Any agent exceeds its retry budget → stop
4. The task has been running longer than a configurable timeout → stop
5. Codex attempts a command on the deny list → block and continue

**Configurable gates:**
- `--require-plan-approval`: Human must approve plan before build starts
- `--require-merge-approval`: Human must approve before merge
- `--auto-approve`: Full autonomy (default for known-safe task types)

---

## 8. Frontend Visual Verification Design

### Architecture

Frontend verification is a **two-layer system**: deterministic Playwright assertions (fast, reliable, catches regressions) plus model-judged screenshot review (catches subjective quality issues).

### Who Does What

| Step | Owner | Method |
|------|-------|--------|
| Launch app | Orchestrator | `npm run dev` + port wait |
| Run E2E tests | Orchestrator → Playwright | `npx playwright test` |
| Capture screenshots | Playwright | Configured in test scripts |
| Compare to baselines | Playwright | `toMatchSnapshot()` pixel comparison |
| Judge visual quality | Claude (via acpx) | Screenshot + acceptance criteria |
| Report defects | Orchestrator | Compiles Playwright + Claude output |
| Fix defects | Codex (via acpx) | Receives structured defect list |

### How Regressions Are Detected

**Layer 1 — Deterministic (Playwright):**
- Pixel-diff comparison against baseline screenshots (`toMatchSnapshot` with configurable threshold)
- DOM assertion checks (element exists, text content correct, interactive elements clickable)
- Responsive viewport checks (desktop, tablet, mobile)
- Accessibility checks via `@axe-core/playwright`

**Layer 2 — Model-Judged (Claude):**
- Screenshots of key routes sent to Claude with acceptance criteria
- Claude evaluates: layout correctness, visual consistency, obvious rendering errors, alignment issues
- Claude produces structured output: `{ route: "/dashboard", pass: false, defects: ["navbar overlaps content on mobile viewport"] }`

### Avoiding Session/Tab Collisions

- Only one browser instance exists at any time
- The orchestrator ensures the builder is idle before launching Playwright
- Playwright creates a fresh browser context per test file
- No browser state persists between runs
- App server is launched on a fixed port (configurable, default 3000)
- Port availability is checked before launch

### Acceptance Criteria for UI Correctness

Acceptance criteria live in `tasks/current-acceptance.md` and must include:

1. **Route list**: Every route that must render
2. **Element assertions**: Key elements that must exist on each route
3. **Interaction flows**: Click sequences that must work (e.g., "login form submits and redirects to dashboard")
4. **Visual baselines**: Reference screenshots for pixel comparison (if available)
5. **Responsive requirements**: Viewports that must work
6. **Accessibility requirements**: WCAG level (if applicable)

### Deterministic vs. Model-Judged

| Check Type | Method | When |
|------------|--------|------|
| Element exists | Deterministic (Playwright) | Every run |
| Text content correct | Deterministic (Playwright) | Every run |
| Click flow works | Deterministic (Playwright) | Every run |
| Pixel-diff within threshold | Deterministic (Playwright snapshot) | Every run |
| Layout "looks correct" | Model-judged (Claude + screenshot) | After all deterministic checks pass |
| "Matches design mockup" | Model-judged (Claude + screenshot + mockup) | When mockup provided in acceptance criteria |

**Ratio target:** 80% deterministic, 20% model-judged. Model-judged checks are expensive and non-deterministic. Use them for genuine subjective quality, not for things that can be asserted programmatically.

---

## 9. Hooks, Guardrails, and Policy Automation

### Implement First (v1 Day 1)

#### 1. Format-on-Save Hook
```bash
# Runs after every file write by Codex
npx prettier --write "**/*.{ts,tsx,js,jsx,json,css,md}"
```
**Why first:** Eliminates formatting noise from diffs, prevents formatting-only review comments.

#### 2. Lint + Typecheck After Every Build Cycle
```bash
npm run lint -- --max-warnings 0
npm run typecheck
```
**Why first:** Catches errors before expensive test runs.

#### 3. Test After Every Meaningful Change
```bash
npm run test -- --bail  # Stop on first failure for fast feedback
```

#### 4. Command Deny List
Block Codex from running:
```
git push
git push --force
git branch -D
git reset --hard (on main)
rm -rf /
curl (to external hosts)
wget
ssh
scp
```
**Implementation:** acpx `--deny-commands` flag or wrapper script that intercepts shell commands.

#### 5. Commit Message Structure
All Codex commits must follow:
```
[agent/codex] <type>: <description>

<body>

Milestone: <milestone-id from plan>
```
Types: `feat`, `fix`, `test`, `refactor`, `style`, `docs`

#### 6. Branch Naming Convention
```
agent/task-<id>
```
No other branch names permitted for automated work.

### Implement Second (v1 Week 2+)

#### 7. Doc Update Reminder
After modifying public API files, the orchestrator appends to the builder's next prompt: "You modified public API files. Update relevant documentation if needed."

#### 8. Summary Report Generation
After every task completion (success or failure), the orchestrator generates:
```markdown
## Task Report: <task-id>
- Status: PASS / FAIL
- Duration: X minutes
- Codex invocations: N
- Claude invocations: N
- Retries: N (hook: X, UI: Y, review: Z)
- Acceptance criteria: X/Y met
- Files changed: N
- Test coverage delta: +/-N%
```

#### 9. "Stop and Escalate" Conditions
The pipeline must halt and notify a human if:
- Any agent has been retrying the same error for >15 minutes
- Codex attempts to modify files outside the repo
- Claude's review identifies a security vulnerability
- Total task runtime exceeds configurable timeout (default: 60 minutes)
- Codex's commit count exceeds 20 for a single task (indicates thrashing)

#### 10. Stale Memory Cleanup
Before each task run, the orchestrator checks:
- `docs/agent-memory/failure-log.md` — entries older than 30 days get archived
- `docs/agent-memory/current-plan.md` — deleted (fresh plan each task)

---

## 10. Memory and Context Strategy

### What Lives in Durable Memory (`docs/agent-memory/`)

| File | Contents | Updated By |
|------|----------|-----------|
| `architecture-decisions.md` | ADRs: key choices, rationale, constraints | Orchestrator (after Claude review) |
| `failure-log.md` | Past failures: error, root cause, resolution | Orchestrator (after each failure) |
| `project-context.md` | Tech stack, conventions, patterns, folder structure | Human (initially), orchestrator (appends) |
| `acceptance-criteria-history.md` | Past acceptance criteria and whether they passed | Orchestrator |

### What Lives in Repo Files (Not Memory)

- Code conventions → `.eslintrc`, `.prettierrc`, `tsconfig.json`
- Project structure → the actual directory structure (self-documenting)
- Test patterns → existing test files (agents learn by reading them)
- Dependencies → `package.json`, `package-lock.json`

### What Is Ephemeral Per-Run Context

- Current implementation plan → `docs/agent-memory/current-plan.md` (overwritten each task)
- Build logs → `/tmp/agent-logs/<task-id>/`
- Screenshots → `/tmp/agent-screenshots/<task-id>/`
- Playwright reports → `/tmp/agent-reports/<task-id>/`

### How Architecture Decisions Are Stored

ADR format in `architecture-decisions.md`:
```markdown
### ADR-<number>: <title>
**Date:** YYYY-MM-DD
**Status:** accepted | superseded by ADR-<N>
**Context:** Why this decision was needed
**Decision:** What was decided
**Consequences:** What this means for future work
**Source:** Task <task-id>, identified during [planning|review|failure]
```

### How Prior Failures Are Stored and Retrieved

Failure log format in `failure-log.md`:
```markdown
### Failure-<number>: <short description>
**Date:** YYYY-MM-DD
**Task:** <task-id>
**Phase:** [build|hooks|ui-verification|review]
**Error:** <exact error message, truncated to 500 chars>
**Root cause:** <diagnosis>
**Resolution:** <what fixed it>
**Prevention:** <what to do differently next time>
```

When Codex or Claude is invoked, the orchestrator includes relevant failure log entries in the prompt: "Previous similar failures and their resolutions: [relevant entries]."

### How to Avoid Memory Pollution

1. **Orchestrator is the only writer to memory files** — agents produce reports, orchestrator decides what to persist
2. **Fixed schemas** — every memory file has a defined format, free-form text is not allowed
3. **Size limits** — `failure-log.md` capped at 50 entries, oldest archived
4. **Relevance filtering** — orchestrator only includes memory entries relevant to the current task type when building agent prompts
5. **Regular pruning** — stale entries (>30 days with no re-occurrence) are archived

### Zep: Should You Use It?

**Not in v1. Probably not in v2 either.**

Zep's temporal knowledge graph is designed for systems with thousands of conversation turns, complex entity relationships, and cross-session retrieval needs. Your system has:
- A handful of structured memory files
- ~4 Claude invocations per task
- No entity relationship complexity
- Memory that fits comfortably in context windows

File-based memory with grep is more than sufficient. It is also:
- Zero infrastructure
- Zero latency
- Fully version-controlled
- Readable by any agent without an API call
- Debuggable by a human with a text editor

**Move to Zep when:** You have >100 completed tasks, the failure log is too large to include in prompts, and you need semantic search over past failures. That is Phase 5+ at earliest.

---

## 11. Cost Strategy

### Where to Use the Expensive Model (Claude)

Claude should be invoked **at most 4 times per task:**

1. **Planning** (once): Produces implementation plan
2. **Diagnosis** (0-1 times): Only if Codex is stuck after retries
3. **UI review** (0-1 times): Screenshot analysis after deterministic checks pass
4. **Code review** (once): Final quality gate

**Estimated Claude cost per task:** ~$0.50-$2.00 depending on codebase size and diff length.

### Where to Use the Cheaper/Faster Worker (Codex)

Codex handles all iterative work:
- Code writing
- Test fixing
- Lint/format fixing
- UI defect fixing
- All retry loops

**Estimated Codex cost per task:** Variable. Full-auto mode with retries could be $2-$10. The key cost driver is retry count.

### How Often Review/Audit Passes Should Happen

| Review Type | Frequency | Cost Impact |
|-------------|-----------|-------------|
| Claude plan review | Once per task | Low |
| Claude code review | Once per task (after all hooks pass) | Low |
| Claude UI review | Once per task (after Playwright passes) | Low |
| Claude diagnosis | 0-1 per task (only on stuck failures) | Low |
| **Never:** Claude on every file change | — | This would 10x cost |
| **Never:** Claude in the retry loop | — | Retry loops are Codex's job |

### What Should Be Cached or Memoized

- **Implementation plans** for similar task types — if you build similar features repeatedly, cache plan templates
- **Failure resolutions** — the failure log serves as a cache, include relevant entries in Codex prompts to avoid re-discovering the same fix
- **Lint/typecheck results** — only re-run on changed files (most build tools do this automatically)
- **Playwright baselines** — persist screenshot baselines in the repo to avoid re-capturing

### Likely Cost Sinks

| Cost Sink | How It Happens | Mitigation |
|-----------|---------------|------------|
| Codex retry loops | Codex cannot fix a test, retries the same approach | Max retry limit (3), then escalate to Claude for different approach |
| Claude on large diffs | Sending entire codebase to Claude for review | Send only the diff + relevant file context, not the whole repo |
| UI verification loops | Visual defect → fix → new defect → fix → new defect | Max 2 UI fix cycles, then stop |
| Session token bloat | Long acpx sessions accumulate context | Start fresh sessions for each major phase, not one session per task |
| Unnecessary planning | Claude plans for trivial tasks | Skip planning for tasks flagged as "small fix" or "single file change" |

### How to Minimize Wasted Review Calls

1. **Never invoke Claude review if hooks are failing** — fix hooks first, then review
2. **Never invoke Claude review on formatting-only changes** — deterministic hooks handle this
3. **Batch review** — one review call at the end, not incremental reviews
4. **Skip planning for small tasks** — configurable threshold based on estimated scope

---

## 12. Failure Mode Matrix

| # | Failure Mode | How It Manifests | How to Detect | How to Recover | v1 Blocker? |
|---|-------------|------------------|---------------|----------------|-------------|
| 1 | **Agent stuck in retry loop** | Same error repeats 3+ times, Codex applies same fix repeatedly | Orchestrator counts retries, detects identical error messages | Escalate to Claude for alternative diagnosis. If still stuck, stop pipeline. | No — retry limits prevent infinite loops |
| 2 | **Conflicting edits** | Two agents modify same file simultaneously | Cannot happen in v1 (serialized execution). In later phases: file lock or worktree isolation | Serialized execution (v1). Separate worktrees (later). | No |
| 3 | **False "done" state** | Codex reports success but hooks fail, or tests pass but app does not actually work | Orchestrator independently re-runs all hooks and UI checks | Independent verification layer (orchestrator never trusts self-reported status) | No — architecture prevents this |
| 4 | **Test flakiness** | Tests pass on one run, fail on next with identical code | Orchestrator detects test failure after previously passing run on same code | Re-run failing test 2x. If flaky, log as flaky test and exclude from blocking criteria. | Yes — flaky tests can stall the pipeline. Mitigation: flaky test detection and quarantine. |
| 5 | **Browser automation instability** | Playwright times out, cannot find elements, screenshots differ due to timing | Playwright exit codes, timeout logs | Retry with increased timeouts. Use `waitForSelector` aggressively. Fall back to non-visual verification. | Partially — headless rendering is generally stable, but timing-sensitive assertions can flake. |
| 6 | **Stale memory** | Failure log suggests fix that no longer applies, architecture decision references deleted code | Memory entries reference files/functions that do not exist in current codebase | Before using memory entries, verify referenced files/functions still exist. Prune stale entries. | No — mitigated by verification step |
| 7 | **Broken auth** | API key expired, rate limited, or revoked mid-task | acpx returns auth error | Retry with exponential backoff. If persistent, stop pipeline and notify human. | Yes — no auth = no agents. Mitigation: validate keys before task start. |
| 8 | **Flaky acpx (alpha software)** | Session drops, protocol error, unexpected response format | acpx exit code, malformed response | Retry the invocation. Start new session if session is corrupted. Pin acpx version. | Yes — alpha software. Mitigation: pin version, write integration tests, have fallback direct CLI invocation. |
| 9 | **Poor handoffs between agents** | Claude produces advice Codex cannot act on ("refactor the architecture") or Codex ignores review feedback | Review feedback does not result in corresponding code changes | Structure all handoffs as specific, actionable instructions with file paths and line numbers. Orchestrator validates that review items map to concrete changes. | Partially — prompt engineering is required |
| 10 | **Task decomposition failures** | Plan is too vague, milestones are too large, Codex tries to do everything at once | Build takes >30 minutes without a commit, or produces a massive single commit | Require plans to have milestones of <200 lines changed each. If a milestone takes >15 min, interrupt and split. | Partially — planning quality varies |
| 11 | **App fails to launch** | Port conflict, missing env vars, database not running | App process exits non-zero, port check times out | Kill conflicting process, ensure env vars are set, start required services. Builder fixes if code-related. | Yes — local environment setup must be deterministic. Mitigation: Docker or documented setup. |
| 12 | **Context window overflow** | Too much context passed to Claude (large codebase + large diff + large memory) | Claude returns truncated or degraded response, or acpx errors | Send only relevant file snippets and diff chunks, not entire files. Limit memory inclusion. | Partially — Claude's window is large but not infinite |
| 13 | **Codex sandbox limitations** | Codex cannot access local database, cannot run Docker, cannot reach local services | Build or test failures referencing connection errors | Ensure test/dev environment is self-contained (SQLite, in-memory DB, mocked services) | Partially — depends on project complexity |
| 14 | **Secrets leakage** | Codex commits .env file, or includes API key in code | Pre-commit hook scanning for secrets patterns, `.gitignore` verification | Block commit, strip secrets, alert human | Yes — must have secret scanning hook from day 1 |

---

## 13. Recommended MVP

### Include in MVP

1. **Orchestrator script** (bash or Python, ~200-400 lines)
   - Reads task spec
   - Invokes acpx for Claude (plan) and Codex (build)
   - Runs deterministic hooks
   - Launches app and runs Playwright
   - Invokes acpx for Claude (review)
   - Produces execution report
   - Manages retry budgets

2. **acpx** (pinned version, with Codex and Claude adapters)

3. **Codex** (full-auto mode, primary builder)

4. **Claude** (planner + reviewer, invoked at 3-4 checkpoints)

5. **Deterministic hooks** (lint, format, typecheck, test — shell commands)

6. **Playwright** (E2E tests + screenshot capture)

7. **File-based memory** (`docs/agent-memory/` with 4 structured markdown files)

8. **Secret scanning pre-commit hook**

9. **Command deny list** (block dangerous git/shell commands)

### Exclude from MVP

- OpenClaw (not needed, adds fragile intermediary)
- Gemini (no clear role)
- Zep (overkill, file-based memory is sufficient)
- MCP integrations (Codex does not support them)
- Multiple worktrees (one branch, one builder)
- Parallel agent execution (serialized is correct for v1)
- Auto-merge (human approves merge in v1)
- Specialized test-fixer agent (builder handles this)
- Specialized debugger agent (Claude handles escalation)

### What to Fake or Do Manually at First

- **Task specs**: Human writes these manually (auto-generation is a separate project)
- **Acceptance criteria**: Human writes these manually
- **Baseline screenshots**: Captured manually on first run, then maintained automatically
- **Merge**: Human reviews branch and merges manually
- **Environment setup**: Human ensures local env is ready before kickoff

### What Success Looks Like for the MVP

The system can:
1. Take a task spec and acceptance criteria as input
2. Produce an implementation plan without human intervention
3. Implement the plan and pass all hooks without human intervention
4. Launch the app and verify the UI without human intervention
5. Produce a review report without human intervention
6. Leave a clean, mergeable branch with a complete execution log

**Success metric:** Complete a real feature task end-to-end with zero human intervention between kickoff and merge review. The human only writes the spec and reviews the final branch.

**Realistic first milestone:** Complete a "add a new page/route with tests" task autonomously. Not a full-app build — a single well-scoped feature addition.

---

## 14. Implementation Roadmap

### Phase 0: Manual Baseline (Week 1)

**Goal:** Validate each tool works independently before connecting them.

**Actions:**
- Use `acpx codex` manually to build a small feature, confirm it works
- Use `acpx claude` manually to review a diff, confirm output is useful and structured
- Write and run Playwright E2E tests manually against the target app
- Write the hook scripts (lint, format, typecheck, test) and confirm they work
- Create the `docs/agent-memory/` directory structure with empty templates
- Create a sample task spec and acceptance criteria

**Acceptance criteria:**
- Each tool works in isolation
- acpx sessions are stable (create, prompt, close without errors)
- Playwright can capture screenshots and compare baselines
- Hooks run and return correct exit codes

**Risks:** acpx alpha instability. Mitigate by testing multiple acpx versions and pinning one that works.

**What to measure:** Success rate of individual tool invocations.

### Phase 1: Stable Single-Builder Loop (Weeks 2-3)

**Goal:** Orchestrator drives Codex through build → hooks → retry loop automatically.

**Components added:**
- Orchestrator script (core state machine)
- Codex integration via acpx
- Hook execution after build
- Retry logic with budget limits
- Basic execution logging

**What is NOT included:** Claude planning, Claude review, UI verification.

**Acceptance criteria:**
- Orchestrator successfully drives Codex to implement a simple task
- Hooks run automatically after build
- Retry loop works (Codex fixes hook failures up to retry limit)
- Pipeline stops cleanly when retry budget exhausted
- Execution log captures all steps

**Risks:** acpx session management, Codex prompt quality, retry loop effectiveness.

**What to measure:** Task completion rate, average retries, time per task.

### Phase 2: Add Selective Reviewer (Weeks 4-5)

**Goal:** Claude reviews code at end of build cycle. Claude plans at start.

**Components added:**
- Claude planning step (before Codex builds)
- Claude code review step (after hooks pass)
- Claude escalation diagnosis (when Codex is stuck)
- Structured review output format
- Review-to-builder feedback loop

**Acceptance criteria:**
- Claude produces useful plans that Codex follows
- Claude review catches real issues (not just nitpicks)
- Review feedback is actionable (Codex can fix identified issues)
- Escalation diagnosis helps Codex get unstuck at least 50% of the time

**Risks:** Claude advice being too vague or too expensive for the value. Review adding time without adding quality.

**What to measure:** Review catch rate (real issues found), escalation success rate, cost per task.

### Phase 3: Add Browser/UI Verifier (Weeks 6-8)

**Goal:** Playwright + Claude visual verification integrated into pipeline.

**Components added:**
- App launch step in orchestrator
- Playwright E2E test execution
- Screenshot capture and baseline comparison
- Claude screenshot analysis
- UI defect → builder feedback loop

**Acceptance criteria:**
- App launches automatically and is verified as running
- Playwright tests execute and produce pass/fail
- Screenshots are captured and compared to baselines
- Claude correctly identifies visual defects from screenshots
- Builder successfully fixes at least some UI defects from feedback

**Risks:** Timing-sensitive Playwright assertions, headless rendering differences, Claude visual analysis accuracy.

**What to measure:** UI defect detection rate, false positive rate, fix success rate.

### Phase 4: Add Memory Layer and Hardening (Weeks 9-12)

**Goal:** Memory files are populated and used effectively. Pipeline is hardened for reliability.

**Components added:**
- Architecture decision recording
- Failure log population and retrieval
- Memory pruning and staleness detection
- Secret scanning hook
- Command deny list enforcement
- Timeout enforcement
- Comprehensive error handling

**Acceptance criteria:**
- Memory entries improve Codex's success rate on repeated task types
- Failure log entries prevent re-discovery of known issues
- No secrets are ever committed
- Pipeline handles all expected failure modes gracefully
- Timeout prevents runaway tasks

**Risks:** Memory pollution, stale entries misleading agents.

**What to measure:** Task completion rate improvement over Phase 3, cost per task trend, failure recovery rate.

### Phase 5: Specialization and Parallelism (Weeks 13+)

**Goal:** Expand to parallel tasks, specialized agents, and more complex workflows.

**Components added:**
- Multiple worktrees for parallel tasks
- Specialized test-fixer agent (if data shows builder is inefficient at test repair)
- Task queue (multiple tasks in pipeline)
- Smarter memory retrieval (semantic search if file-based becomes insufficient)
- Zep integration (if needed)
- Configurable task profiles (small fix, feature, refactor)

**Acceptance criteria:**
- Two independent features can be built simultaneously without conflicts
- Task throughput increases linearly with parallel workers
- Cost per task does not increase with specialization

**Risks:** Coordination complexity, merge conflicts, resource contention.

**What to measure:** Throughput, cost efficiency, failure rate under parallelism.

---

## 15. Exact Deliverables

### A. Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────┐
│                     HUMAN OPERATOR                               │
│  Writes: task spec, acceptance criteria                          │
│  Reviews: final branch, execution report                         │
│  Approves: merge                                                 │
└──────────┬──────────────────────────────────────────┬────────────┘
           │ input                                     │ output
           ▼                                           ▲
┌──────────────────────────────────────────────────────────────────┐
│                   PIPELINE ORCHESTRATOR                           │
│  (deterministic script — bash or Python)                         │
│                                                                   │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │
│  │ State   │  │ Retry    │  │ Log      │  │ Report         │    │
│  │ Machine │  │ Manager  │  │ Writer   │  │ Generator      │    │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────────┬───────┘    │
│       │            │             │                   │            │
└───────┼────────────┼─────────────┼───────────────────┼────────────┘
        │            │             │                   │
   ┌────┴────────────┴─────────────┴───────────────────┴────┐
   │                    acpx (CLI)                           │
   │         Agent Client Protocol interface                 │
   └────┬──────────────┬──────────────┬─────────────────────┘
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────────┐
   │  CODEX  │   │  CLAUDE  │   │  DETERMINISTIC│
   │ Builder │   │ Planner/ │   │    HOOKS      │
   │         │   │ Reviewer │   │ (lint/test/   │
   │ Writes  │   │          │   │  format/type) │
   │ code,   │   │ Plans,   │   │               │
   │ tests,  │   │ reviews, │   │ Shell commands│
   │ fixes   │   │ diagnoses│   │ No AI needed  │
   └─────────┘   └──────────┘   └──────────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │  PLAYWRIGHT   │
                                 │  UI Verifier  │
                                 │               │
                                 │ Headless      │
                                 │ browser,      │
                                 │ screenshots,  │
                                 │ assertions    │
                                 └──────────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │  FILE-BASED   │
                                 │  MEMORY       │
                                 │               │
                                 │ docs/agent-   │
                                 │ memory/       │
                                 │ (markdown)    │
                                 └──────────────┘
```

### B. Agent Roster Table

| Agent | Model/Tool | Role | Read | Write | Shell | Browser | Persistent |
|-------|-----------|------|------|-------|-------|---------|------------|
| Orchestrator | None (script) | Pipeline control | Yes | Logs+memory only | Full | No | Per-task |
| Planner | Claude via acpx | Implementation planning | Yes | No | No | No | Ephemeral |
| Builder | Codex via acpx | Code implementation | Yes | Full worktree | Full (sandboxed) | No | Per-task session |
| UI Verifier | Playwright + Claude | Frontend verification | Code: yes | test-results only | Playwright CLI | Headless, localhost | Ephemeral |
| Reviewer | Claude via acpx | Code review & audit | Yes | No | No | No | Ephemeral |

### C. Sample Agent Prompts/Instructions

**Planner Prompt (Claude):**
```
You are the planning agent for an autonomous coding system.

Read the following files:
- tasks/current-task.md (the task specification)
- tasks/current-acceptance.md (acceptance criteria)
- docs/agent-memory/architecture-decisions.md (prior decisions)
- docs/agent-memory/failure-log.md (prior failures, check for relevance)
- docs/agent-memory/project-context.md (tech stack and conventions)

Produce an implementation plan in this exact format:

## Implementation Plan

### Summary
One paragraph describing the overall approach.

### Milestones
For each milestone:
- **M<N>: <title>**
  - Files to create/modify: [list]
  - Changes: [specific description]
  - Tests to add: [list]
  - Estimated lines changed: <number>
  - Dependencies: [which milestones must complete first]

### Risk Flags
List anything that seems ambiguous, risky, or likely to cause problems.

### Architecture Decisions
List any new architectural choices this task requires.

Rules:
- Each milestone must be <200 lines of changes
- Every milestone must include its own tests
- Be specific about file paths and function names
- If the task spec is ambiguous, state your assumptions explicitly
- Do not produce code. Produce a plan only.
```

**Builder Prompt (Codex):**
```
You are the builder agent. Your job is to implement code changes according to a plan.

Read the implementation plan at docs/agent-memory/current-plan.md.

For each milestone in order:
1. Implement the changes described
2. Run: npm run lint && npm run typecheck && npm run test
3. If any check fails, fix the issue and re-run
4. When all checks pass, commit with message:
   [agent/codex] feat: <milestone description>
   Milestone: M<N>
5. Move to the next milestone

Rules:
- Follow the plan. Do not add features not in the plan.
- Do not modify files not listed in the plan unless necessary to fix a test.
- Do not skip tests. Every milestone must have passing tests.
- If you cannot fix a test after 3 attempts, stop and report the error.
- Do not run git push. Only commit locally.
- Do not modify .env files or any file matching *.secret*.
- Read existing test files to match testing patterns and conventions.
```

**Reviewer Prompt (Claude):**
```
You are the code review agent. Your job is to review changes for quality, correctness, and security.

You are reviewing the diff between main and the working branch.

Read:
- The diff provided below
- docs/agent-memory/current-plan.md (the implementation plan)
- tasks/current-acceptance.md (acceptance criteria)

Produce a review in this exact format:

## Code Review

### Verdict: PASS | FAIL

### Blocking Issues (must fix before merge)
For each:
- **File:** <path>
- **Line:** <number or range>
- **Issue:** <description>
- **Fix:** <specific instruction>

### Non-Blocking Suggestions
For each:
- **File:** <path>
- **Suggestion:** <description>

### Security Check
- [ ] No hardcoded secrets
- [ ] No SQL injection vectors
- [ ] No XSS vectors
- [ ] No unsafe dependencies added
- [ ] Input validation present where needed

### Plan Adherence
- [ ] All milestones implemented
- [ ] No scope creep (features not in plan)
- [ ] Tests match plan specifications

### Acceptance Criteria
For each criterion: MET | NOT MET | UNCLEAR
```

### D. Sample Policy/Guardrail Set

```yaml
# guardrails.yaml — loaded by orchestrator

retry_budgets:
  hook_fixes: 3
  hook_fixes_post_diagnosis: 2
  ui_fixes: 2
  review_fixes: 2
  app_launch: 2

timeouts:
  total_task: 3600        # 60 minutes
  single_agent_call: 600  # 10 minutes
  app_launch_wait: 30     # seconds
  playwright_test: 120    # seconds per test

command_deny_list:
  - "git push"
  - "git push --force"
  - "git branch -D"
  - "git reset --hard origin"
  - "rm -rf /"
  - "rm -rf ~"
  - "curl"
  - "wget"
  - "ssh"
  - "scp"
  - "nc "
  - "ncat"

commit_message_format: "[agent/codex] {type}: {description}\n\nMilestone: {milestone}"
branch_name_format: "agent/task-{id}"

required_hooks:
  - "npm run lint -- --max-warnings 0"
  - "npm run format:check"
  - "npm run typecheck"
  - "npm run test -- --bail"

stop_conditions:
  - "security_vulnerability_in_review"
  - "max_retries_exhausted"
  - "total_timeout_exceeded"
  - "commit_count_exceeds_20"
  - "agent_modifies_files_outside_repo"

auto_approve_gates:
  plan: false        # require human approval of plan in v1
  merge: false       # require human approval of merge in v1
  build: true        # auto-approve build steps
  review_fixes: true # auto-approve fixing review items
```

### E. Sample Kickoff Checklist

```markdown
## Pre-Task Kickoff Checklist

- [ ] Task spec exists at `tasks/current-task.md`
- [ ] Acceptance criteria exist at `tasks/current-acceptance.md`
- [ ] `main` branch is clean and up to date
- [ ] `npm install` completes without errors
- [ ] `npm run lint && npm run typecheck && npm run test` all pass on main
- [ ] `npm run dev` launches the app successfully
- [ ] API keys are set: OPENAI_API_KEY, ANTHROPIC_API_KEY
- [ ] `acpx codex "echo hello"` returns successfully
- [ ] `acpx claude "echo hello"` returns successfully
- [ ] Playwright is installed: `npx playwright install`
- [ ] No other agent tasks are running on this repo
- [ ] `docs/agent-memory/` directory exists with template files
- [ ] `.gitignore` includes `.env`, `*.secret*`, `test-results/`
- [ ] Secret scanning pre-commit hook is installed
```

### F. Sample Acceptance Checklist for "Task Complete"

```markdown
## Task Completion Checklist

### Deterministic Checks (all must pass)
- [ ] `npm run lint -- --max-warnings 0` exits 0
- [ ] `npm run format:check` exits 0
- [ ] `npm run typecheck` exits 0
- [ ] `npm run test` exits 0 with 100% test pass rate
- [ ] App launches on localhost without errors
- [ ] Playwright E2E tests pass
- [ ] No uncommitted changes in worktree
- [ ] All commits follow message format convention
- [ ] No secrets in any committed file (scanned)
- [ ] Branch is based on current main (no conflicts)

### Quality Checks (from Claude review)
- [ ] Code review verdict: PASS
- [ ] Zero blocking issues
- [ ] All acceptance criteria marked MET
- [ ] Security checklist all checked
- [ ] Plan adherence confirmed

### Documentation
- [ ] Execution log updated in docs/agent-memory/execution-log.md
- [ ] Architecture decisions recorded (if any)
- [ ] Failure patterns logged (if any)
- [ ] Execution report generated
```

### G. Sample Review Checklist for Claude's Audit Pass

```markdown
## Claude Audit Review Checklist

### Code Quality
- [ ] Functions are reasonably sized (<50 lines)
- [ ] No dead code added
- [ ] No commented-out code
- [ ] Variable and function names are descriptive
- [ ] No magic numbers without explanation
- [ ] Error handling is present and appropriate

### Correctness
- [ ] Changes match the implementation plan
- [ ] Edge cases are handled
- [ ] Null/undefined checks where needed
- [ ] API contracts match between frontend and backend

### Testing
- [ ] New code has corresponding tests
- [ ] Tests cover happy path and error cases
- [ ] Tests are not trivially always-passing
- [ ] No test code in production files

### Security
- [ ] No hardcoded credentials or secrets
- [ ] User input is validated/sanitized
- [ ] No SQL injection vectors
- [ ] No XSS vectors (output is escaped)
- [ ] Dependencies do not have known vulnerabilities

### Architecture
- [ ] Changes follow existing codebase patterns
- [ ] No unnecessary new dependencies
- [ ] No circular dependencies introduced
- [ ] File placement follows project structure conventions

### Performance
- [ ] No obvious N+1 query patterns
- [ ] No unnecessary re-renders in React components
- [ ] No blocking operations in request handlers
```

---

## 16. Red-Team Section: Why This Plan Might Fail Anyway

### 1. acpx Is Alpha Software and You Are Building On Quicksand

acpx explicitly states it is in alpha and "CLI/runtime interfaces are likely to change." You are proposing to make it the sole communication layer between your orchestrator and every agent. When acpx breaks — and alpha software breaks — your entire system is dead. There is no fallback. You are betting the farm on a tool that has not committed to API stability. If Peter Steinberger's move to OpenAI changes the project's priorities, or if the non-profit foundation deprioritizes acpx, you are stuck maintaining a fork of alpha software.

### 2. Codex's Full-Auto Mode Is Not Actually Fully Autonomous

Codex "full-auto" sounds impressive but in practice it means "runs without approval gates." It does not mean "reliably completes complex tasks." Codex is good at discrete, well-scoped changes. It is demonstrably weak at multi-file coordination in large codebases and has no MCP or local tool integration. The gap between "Codex can write a function" and "Codex can build a feature end-to-end including tests and frontend" is enormous and largely unmeasured in production conditions. You may find that Codex's retry loops burn significant budget on tasks that require architectural understanding it does not have.

### 3. The Orchestrator Is Where All the Hard Problems Live

This plan describes the orchestrator as "a simple script." It is not simple. It must: manage state across multiple agent invocations, parse structured output from agents (which may not follow the requested format), handle partial failures gracefully, manage retries with backoff, coordinate app launch and teardown, pipe the right context to the right agent at the right time, enforce guardrails, and produce useful reports. This is a real software project, not a script. If you treat it as a script, it will become an unmaintainable tangle of bash within weeks.

### 4. Claude's Review May Not Be Worth the Cost

Claude will produce reviews. Those reviews will contain reasonable-sounding feedback. But you have no guarantee that the feedback will be: specific enough for Codex to act on, correct in context (Claude may not understand the full codebase), or worth the time cost of another build-review-fix cycle. There is a real risk that the review loop becomes a formality that adds time and cost without catching real issues, because the kinds of bugs that matter (integration issues, race conditions, business logic errors) are hard to catch from a diff alone.

### 5. Frontend Visual Verification Is the Hardest Part and You Might Underinvest

Model-judged screenshot analysis is non-deterministic. Claude might say the layout is fine when it is broken, or flag a false positive that sends Codex on a wild goose chase. Playwright assertions are deterministic but require someone to write good assertions in the first place. If the E2E test suite is thin, the visual verification step provides false confidence. If you do not invest heavily in writing good Playwright tests, this entire layer is theater.

### 6. Memory Will Become a Liability Before It Becomes an Asset

Every memory system eventually becomes a graveyard of stale, misleading, or contradictory information. Your failure log will grow. Architecture decisions will become outdated. Project context will drift. If agents start acting on stale memory, they will make worse decisions than they would with no memory at all. The pruning and validation mechanisms described in this plan are necessary but insufficient — they require the orchestrator to be smart about relevance, which is itself a hard problem.

### 7. You Are Underestimating the Local Environment Problem

The plan assumes the app can be launched locally with `npm run dev`. In reality, many apps require: a database, environment variables, third-party service connections, specific Node/Python versions, system dependencies, Docker, or other infrastructure. If the local environment is not perfectly reproducible, the "launch app and verify UI" step will fail for reasons that have nothing to do with code quality. This infrastructure problem is likely to consume more debugging time than the actual code generation.

### 8. The "Autonomous" Part Is Aspirational

In practice, you will be babysitting this system for the first 20-50 runs. Every failure mode will be novel. Every prompt will need tuning. Every handoff will have edge cases. The system will not be truly autonomous until you have iterated on it extensively, and by then you will have spent more time building and debugging the system than you would have spent just writing the code yourself. The ROI only turns positive if you have a high volume of repetitive, well-scoped tasks — not one-off features.

### 9. You Might Be Building a Rube Goldberg Machine

The honest question: is the problem you are solving (coding is slow) actually best addressed by a multi-agent orchestration system? Or would you get 80% of the value from a simpler approach: one good coding agent (Codex or Claude Code) with a human in the loop at checkpoints, plus a good CI pipeline? The multi-agent system is more interesting but interest is not the same as effectiveness.

---

## 17. Final Recommendation

### Preferred Final Design

The design described in this document: **deterministic orchestrator script + acpx + Codex (builder) + Claude (planner/reviewer) + Playwright (UI verifier) + file-based memory.** No OpenClaw. No Gemini. No Zep. Serial execution. One working branch per task. One agent writing at a time.

### The Design You Are Most Likely to Successfully Operate

**Phase 1 only: orchestrator + Codex + hooks.** No Claude in the loop yet. Just a script that gives Codex a task, runs hooks, retries on failure, and reports results. This is the minimum system that proves the concept. It is boring. It will work. Everything else is premature until this works reliably.

### Fastest Path to First Real Value

1. Write the orchestrator script (2-3 days)
2. Get acpx + Codex working on a real task (1 day)
3. Add hook automation (1 day)
4. Run 10 real tasks, fix failures, tune prompts (1-2 weeks)
5. Only then add Claude, Playwright, memory

**First real value arrives when Codex can complete a well-scoped task (add a route, add a component, fix a bug) without human intervention between kickoff and merge review.**

### Top 3 Mistakes to Avoid

1. **Building the orchestration layer inside OpenClaw.** This will consume weeks fighting a framework designed for a different purpose. Use a script. It is less exciting and far more reliable.

2. **Adding all agents and capabilities simultaneously.** Every component you add before the previous one is stable multiplies your debugging surface. Phase the rollout aggressively. Do not move to Phase 2 until Phase 1 has completed 10 tasks successfully.

3. **Optimizing for autonomy before optimizing for reliability.** The system that requires human intervention at 2 checkpoints but works every time is infinitely more valuable than the system that is "fully autonomous" but fails unpredictably and requires 30 minutes of debugging to figure out why. Build for reliability first. Remove human checkpoints only when data shows they are unnecessary.

---

## Sources

- [OpenClaw GitHub / Documentation](https://docs.openclaw.ai/cli/acp)
- [acpx on GitHub](https://github.com/openclaw/acpx)
- [acpx on npm](https://www.npmjs.com/package/acpx)
- [Zep AI - Agent Memory Platform](https://www.getzep.com/)
- [Zep Temporal Knowledge Graph Architecture (arXiv)](https://arxiv.org/abs/2501.13956)
- [LangChain vs AutoGen vs CrewAI vs OpenClaw Comparison](https://sparkco.ai/blog/ai-agent-frameworks-compared-langchain-autogen-crewai-and-openclaw-in-2026)
- [OpenClaw Multi-Agent Orchestration Guide](https://zenvanriel.com/ai-engineer-blog/openclaw-multi-agent-orchestration-guide/)
- [Deterministic Multi-Agent Dev Pipeline in OpenClaw](https://dev.to/ggondim/how-i-built-a-deterministic-multi-agent-dev-pipeline-inside-openclaw-and-contributed-a-missing-4ool)
- [Claude Code vs Codex CLI Comparison](https://www.nxcode.io/resources/news/claude-code-vs-codex-cli-terminal-coding-comparison-2026)
- [ChatGPT Codex Review (April 2026)](https://automationatlas.io/answers/chatgpt-codex-review-2026/)
- [OpenAI Codex Product Page](https://openai.com/codex/)
- [AI Agent Memory Systems Comparison 2026](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)
