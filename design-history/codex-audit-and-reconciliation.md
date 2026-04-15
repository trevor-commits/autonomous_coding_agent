# Codex Implementation Spec Audit & Reconciliation

> Historical archive note: this document preserves an intermediate reconciliation state and may contain superseded vocabulary or layout assumptions. Use `../canonical-architecture.md`, `../STRUCTURE.md`, `../RULES.md`, and `../REPO_MAP.md` for current guidance.

**Date:** April 12, 2026
**Context:** Codex produced a detailed implementation spec. Claude (me) produced a delegation architecture (v2). This document audits where they agree, where they disagree, who is right, and what the final merged design should be.

---

## The Core Disagreement

There is one fundamental architectural disagreement between the two specs:

**Codex says:** Use a deterministic state machine as the inner loop. Fixed phases, fixed transitions, fixed escalation rules. No AI in the control path.

**Claude (v2) says:** Use Claude as an autonomous manager agent that makes dynamic delegation decisions in a loop. The executor enforces hard guardrails, but Claude decides what happens next.

**Trevor said:** "I want the agent delegation. I don't care about the risks."

**My audit verdict:** Codex is ignoring your explicit requirement. Its spec is excellent engineering for a deterministic pipeline, but you specifically asked for AI-driven delegation — agents that manage other agents. Codex's state machine doesn't do that. It's a fixed pipeline with AI workers plugged into predetermined slots. That's not delegation, it's a CI/CD pipeline with LLM steps.

However, Codex is right about *several* things that my v2 was weaker on. The reconciliation below takes the delegation model you want and hardens it with the operational rigor Codex brings.

---

## Point-by-Point Audit

### 1. OpenClaw

| | Codex | Claude |
|---|---|---|
| **Position** | Keep it as outer control plane/session router | Drop it entirely |
| **Rationale** | Useful for session routing, task queue, status reporting | Wrong tool — messaging-bot framework, crash-prone, poor observability |

**Verdict: Codex is wrong here, but for an interesting reason.**

Codex read the OpenClaw docs and latched onto the "control plane" framing without weighing the operational evidence. Multiple practitioners have reported that OpenClaw's Gateway is a single point of failure with poor crash recovery. Codex itself noted this: "If the process crashed, the entire pipeline went silent with no signal that anything had broken." And then still recommended it.

The functions Codex wants OpenClaw for (session routing, task queue, status reporting) are trivially handled by the executor script + a SQLite database + a simple task queue. You don't need a messaging-bot framework for that.

**Decision: OpenClaw stays out. The executor handles session routing, the run store handles task queue/status.**

### 2. State Machine vs. AI Manager

| | Codex | Claude |
|---|---|---|
| **Position** | Hard deterministic state machine with fixed transitions | Claude as autonomous manager making dynamic decisions |
| **Rationale** | Predictable, debuggable, no improvisation | Flexible, can adapt to unexpected situations, actual delegation |

**Verdict: Both are partially right. The reconciliation is a hybrid.**

Codex's state machine is good engineering — the states it defines (INTAKE, PLAN, PREPARE_WORKSPACE, IMPLEMENT, LOCAL_VERIFY, LAUNCH_APP, UI_VERIFY, REPAIR, AUDIT, FINAL_GATE, COMPLETE, BLOCKED) are the right states. But its transition rules are too rigid for what you want.

My v2 gives Claude full control, which is what you asked for, but Codex correctly identifies that some transitions should be deterministic regardless of what the AI thinks:

- If hooks fail → the system MUST go to REPAIR, not let Claude decide to skip it
- If the same failure appears 3 times → the system MUST escalate, not let Claude try a 4th time
- If budget is exhausted → the system MUST stop

**Reconciled design: Claude is the manager, but the executor enforces mandatory state transitions as hard constraints.** Claude decides *how* to implement, *what* to delegate, and *when* to adjust strategy. The executor enforces *that hooks must pass before proceeding*, *that budget limits are respected*, and *that repeated failures trigger escalation*. Claude operates within a guardrailed state space, not a fixed pipeline.

Think of it this way: Codex designed a train on rails. I designed a car on an open road. The right answer is a car with guardrails — Claude drives, but certain lanes and stop signs are non-negotiable.

### 3. Defect Packet Format

| | Codex | Claude |
|---|---|---|
| **Position** | Formal JSON schema with severity, repro steps, evidence, suspected scope | Informal descriptions in review feedback |

**Verdict: Codex is clearly right.** This is one of the strongest parts of Codex's spec. Structured defect packets with `defect_id`, `severity`, `type`, `repro_steps`, `expected`, `observed`, `evidence`, and `suspected_scope` are vastly better than free-form text feedback. This eliminates the "vague reviewer" failure mode that both specs identified.

**Decision: Adopt Codex's defect packet schema exactly.** All verification output (hooks, Playwright, Claude visual review) must produce this format. The manager agent receives defect packets and routes them to the builder with specific, structured context.

### 4. Run Contract Schema

| | Codex | Claude |
|---|---|---|
| **Position** | Formal JSON schema with objective, scope, acceptance, constraints | Markdown task spec + acceptance criteria files |

**Verdict: Codex is right.** A machine-readable contract is better than markdown files for an autonomous system. The manager agent can parse JSON reliably. Markdown requires interpretation. Codex's schema with `allowed_paths`, `forbidden_paths`, `functional` acceptance checks, `quality_gates`, `ui_checks`, and `constraints` is the right approach.

**Decision: Adopt Codex's run contract schema.** The human writes the contract (or a template fills in defaults). The manager reads it as structured data, not prose.

### 5. Memory/Storage Model

| | Codex | Claude |
|---|---|---|
| **Position** | 4-layer model: repo truth, run truth, operational memory, optional semantic retrieval. SQLite + artifact folder. | File-based markdown in `docs/agent-memory/`. Simple, git-tracked. |

**Verdict: Codex's model is more rigorous. My model is more practical for v1.**

Codex's 4-layer separation (repo truth, run truth, operational memory, semantic retrieval) is architecturally correct. But it requires standing up SQLite, defining schemas for 9+ tables, and building a retrieval layer before you can run your first task. That's infrastructure work that delays first value.

However, Codex's `agent-state.md` equivalent — the run journal + defect store + artifact store — solves a real problem my v1 memory design was too thin on: cross-iteration state for the manager agent.

**Reconciled design:**

**Phase 1:** File-based memory (my approach) + Codex's artifact folder structure + Codex's run contract as JSON. No SQLite yet.

**Phase 2:** Migrate to SQLite when the file-based approach becomes a bottleneck (likely around 20-30 completed runs when querying past failures becomes slow).

The directory layout from Codex is good. Adopt it:
```
.autoclaw/
  runs/<run_id>/
    contract.json
    plan.json
    state.json          # manager's working state (replaces agent-state.md)
    defects/
    artifacts/
      screenshots/
      videos/
      logs/
    reports/
```

### 6. Agent Roster

Both specs converge on the same core roster with minor naming differences:

| Role | Codex Name | Claude Name | Agreement? |
|------|-----------|------------|------------|
| Top-level controller | manager (deterministic) | manager (Claude AI) | Disagree on implementation |
| Planner | planner (Claude) | planner (Claude) | Agree |
| Builder | builder (Codex) | builder (Codex) | Agree |
| Hook runner | local-verifier | hooks (deterministic) | Agree |
| App launcher | app-supervisor | orchestrator step | Codex is better — separate concern |
| UI tester | ui-verifier | ui-verifier | Agree |
| Code reviewer | auditor (Claude) | reviewer (Claude) | Agree |
| Release gate | release-checker | completion checklist | Codex is better — explicit agent |

**Verdict:** Codex's separation of `app-supervisor` as a distinct concern is correct. Launching and managing the dev server is a specific responsibility that shouldn't be mixed into the builder or verifier. Adopt this.

Codex's `release-checker` as a distinct deterministic step is also correct. Final gate should not be AI-judged — it should be a checklist of hard requirements.

**Decision: Adopt Codex's roster with the manager changed from deterministic to Claude-driven.**

### 7. Git/Worktree Strategy

Both specs agree completely:
- One task = one branch
- One branch = one writable worktree
- Builder is the only committer
- Reviewers are read-only
- No auto-merge in v1
- Push task branch automatically
- Rollback = revert to last green checkpoint commit

**Decision: Agreed. No changes needed.**

### 8. Permissions Model

Both specs agree on the same model with Codex being slightly more explicit:

**Codex adds one important detail I missed:** "Do not rely on interactive approvals for ACP sessions. OpenClaw's ACPX path is non-interactive and can fail on permission prompts; if you allow autonomous write/exec, do it only inside the isolated builder runtime, not globally."

This is a real operational concern. acpx with `--approve-all` in the builder context, `--deny-all` in reviewer contexts.

**Decision: Adopt Codex's permission matrix with the acpx flag guidance.**

### 9. Browser Verification

Both specs agree on the core design:
- One browser owner (ui-verifier)
- Isolated profile per run
- Deterministic Playwright first, model-judged second
- 80/20 deterministic/model split
- Structured defect output

Codex adds the app-supervisor concept, which is better than my approach of having the orchestrator launch the app inline.

**Decision: Agreed. Adopt Codex's app-supervisor separation.**

### 10. Guardrails

Both specs converge. Codex adds two important items I understated:

1. **"Codex hooks are useful, but they are still partial and experimental. Use external wrappers and policy scripts as the primary enforcement layer, not hooks alone."** — This is correct. Do not depend on Codex's built-in hooks as your only safety net.

2. **"No edits outside allowed paths"** — Codex's run contract has `allowed_paths` and `forbidden_paths`. This is better than my general deny list because it's scoped per task.

**Decision: Adopt Codex's path-scoping from the run contract, enforce in the executor.**

### 11. Cost Strategy

Both specs agree: expensive model at checkpoints, cheap worker in the loop, targeted checks before full suite, cache what's stable.

My v2 has higher cost per task ($3-8 vs Codex's implicit $1-3) because the Claude manager runs on every iteration. This is the cost of delegation. You accepted this.

**No changes needed.**

### 12. Phased Roadmap

Codex's phases:
```
Phase 0: task-runner + run contract + single builder + local verifier
Phase 1: branch/worktree isolation + commit checkpoints + app supervisor
Phase 2: Playwright + artifacts + defect packets
Phase 3: Claude checkpoint planner/auditor
Phase 4: normalized failure memory + environment profiles + optional Zep
```

My phases:
```
Week 1: Executor (action loop, acpx integration, guardrails)
Week 2: Manager prompt + action schema + manual testing
Week 3: Wire Claude as manager + simple tasks
Week 4: Memory + Claude reviewer integration
Week 5+: Playwright + visual verification
```

**Verdict: Codex's phasing is wrong for your requirement.** Codex delays Claude to Phase 3, which means you don't get agent delegation until late in the build. Since delegation is your core requirement, Claude as manager needs to be in Phase 1, not Phase 3.

However, Codex is right that you should validate the executor and builder independently before adding the manager brain. The reconciled phasing below addresses this.

---

## Where Codex Is Better Than My v2

1. **Defect packet schema** — Formal, machine-readable, with evidence links. Adopt.
2. **Run contract schema** — JSON with explicit scope, acceptance, constraints. Adopt.
3. **App-supervisor as separate concern** — Clean separation. Adopt.
4. **Release-checker as explicit final gate** — Deterministic, not AI-judged. Adopt.
5. **Path-scoped permissions per task** — `allowed_paths` / `forbidden_paths`. Adopt.
6. **Directory layout for runs/artifacts** — Well-structured. Adopt.
7. **"Codex hooks are partial and experimental"** — Important caveat. Adopt external enforcement.
8. **Non-interactive acpx guidance** — Use `--approve-all` / `--deny-all` appropriately. Adopt.

## Where My v2 Is Better Than Codex

1. **AI-driven delegation (core requirement)** — Codex ignores this entirely. You asked for it.
2. **No OpenClaw** — Codex keeps recommending it despite acknowledging its crash issues.
3. **Manager prompt engineering** — I provided the full system prompt. Codex provided one-liners.
4. **Delegation patterns** — I documented 5 concrete patterns (simple, multi-milestone, stuck, re-planning, UI loop). Codex has none.
5. **Sample manager session** — I showed a real 17-iteration example. Codex has an abstract flow.
6. **Cost modeling for delegation** — I modeled the real cost of Claude-in-the-loop ($3-8/task). Codex's cost model doesn't account for a manager agent.

## Where Both Are Wrong or Incomplete

1. **Neither spec addresses how to actually install and configure acpx + Codex + Claude end-to-end.** The first hour of implementation will be fighting tool setup, not architecture.
2. **Neither spec addresses what happens when the Claude manager's context window fills up** during a long task (50+ iterations). History compression is mentioned in my v2 but not designed.
3. **Neither spec addresses rate limiting.** If you're calling Claude every iteration, you'll hit rate limits on high-volume days.
4. **Neither spec addresses how to test the system itself.** How do you validate the orchestrator without running expensive real tasks?

---

## Reconciled Final Architecture

### The Merged Design

```
┌──────────────────────────────────────────────────────────┐
│                    HUMAN OPERATOR                          │
│  Writes: run contract (JSON)                               │
│  Runs: one command to start                                │
│  Returns to: ready branch + readiness report               │
└──────────┬─────────────────────────────────────┬──────────┘
           │                                      │
           ▼                                      ▲
┌──────────────────────────────────────────────────────────┐
│            EXECUTOR (Python, ~500 lines)                   │
│                                                            │
│  NOT an AI. A loop that:                                   │
│  1. Calls Claude manager with current state                │
│  2. Receives structured action(s)                          │
│  3. Validates against guardrails                           │
│  4. Executes (acpx, shell, playwright, file I/O)          │
│  5. Returns result to Claude manager                       │
│  6. Repeats until terminal state                           │
│                                                            │
│  ENFORCES (non-negotiable, code-level):                    │
│  - Budget limits (iterations, cost, time)                  │
│  - Command deny list                                       │
│  - Path restrictions (from run contract)                   │
│  - Single-writer lock                                      │
│  - Browser-owner lock                                      │
│  - Mandatory state transitions:                            │
│    · Hooks MUST pass before UI verification                │
│    · App MUST be running before Playwright                 │
│    · Same failure 3x → MUST escalate                       │
│    · Budget exceeded → MUST stop                           │
│  - Non-interactive acpx flags                              │
└──────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────────────────┐
│ CLAUDE   ││  CODEX   ││ CLAUDE   ││ DETERMINISTIC LANE   │
│ MANAGER  ││ BUILDER  ││ REVIEWER ││                      │
│          ││          ││          ││ ┌──────────────────┐  │
│ Decides  ││ Writes   ││ Reviews  ││ │ Hook runner      │  │
│ what to  ││ code,    ││ diffs,   ││ │ (lint/type/test) │  │
│ do next. ││ tests,   ││ diagnoses││ └──────────────────┘  │
│ Decom-   ││ fixes.   ││ failures,││ ┌──────────────────┐  │
│ poses    ││ Only     ││ audits   ││ │ App supervisor   │  │
│ tasks.   ││ writer.  ││ quality. ││ │ (launch/stop)    │  │
│ Delegates││          ││          ││ └──────────────────┘  │
│ to all   ││          ││          ││ ┌──────────────────┐  │
│ others.  ││          ││          ││ │ Playwright       │  │
│          ││          ││          ││ │ (UI verify)      │  │
└──────────┘└──────────┘└──────────┘│ └──────────────────┘  │
                                    │ ┌──────────────────┐  │
                                    │ │ Release checker  │  │
                                    │ │ (final gate)     │  │
                                    │ └──────────────────┘  │
                                    └──────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    RUN STORE                                │
│                                                            │
│  .autoclaw/runs/<run_id>/                                  │
│    contract.json          (Codex's schema)                 │
│    plan.json              (planner output)                 │
│    state.json             (manager working state)          │
│    defects/*.json         (Codex's defect packet schema)   │
│    artifacts/             (screenshots, videos, logs)      │
│    reports/               (audit, readiness)               │
│                                                            │
│  .autoclaw/memory/                                         │
│    architecture-decisions.md                                │
│    failure-signatures.json                                  │
│    environment-profiles.json                                │
│    project-context.md                                       │
└──────────────────────────────────────────────────────────┘
```

### How Delegation Works in the Merged Design

Claude manager operates within the executor's guardrail envelope. It can:

- **Decompose** a task into milestones dynamically (not pre-fixed)
- **Delegate** implementation to Codex with tailored, specific prompts
- **Delegate** review/diagnosis to a separate Claude reviewer instance
- **Request** hook execution, app launch, Playwright runs
- **Adjust strategy** when an approach isn't working (try different file, different pattern, different decomposition)
- **Read and write** memory files to learn from and record decisions
- **Declare** completion or failure with structured reasoning

It cannot:

- Bypass the executor's mandatory transitions (hooks must pass before UI verify)
- Exceed budget limits (executor kills the loop)
- Execute denied commands (executor blocks them)
- Write outside allowed paths (executor blocks it)
- Run indefinitely (hard timeout)

### Reconciled Phasing

```
Phase 0 (Week 1): Build the executor
  - Action loop, acpx integration, guardrail enforcement
  - Run contract parser
  - Run store directory structure
  - Shell execution with deny list
  - Logging
  - Test the executor by issuing actions manually (YOU are the manager)

Phase 1 (Week 2): Wire Claude as manager
  - Manager system prompt (from my v2, refined)
  - Action schema validation
  - State persistence (state.json between iterations)
  - History compression for long tasks
  - Run 5 simple tasks: "add a component", "fix this test"
  - Tune the prompt based on failures

Phase 2 (Week 3): Add builder + hooks
  - Codex integration via acpx (persistent sessions)
  - Deterministic hook runner (lint, format, typecheck, test)
  - Defect packet format (from Codex's schema)
  - Commit checkpointing
  - Run 10 tasks end-to-end through code completion

Phase 3 (Week 4): Add UI verification
  - App supervisor (launch/stop/health check)
  - Playwright runner
  - Screenshot capture + artifact store
  - Claude visual review of screenshots
  - Defect routing from UI verifier back to builder

Phase 4 (Week 5): Add reviewer + release checker
  - Claude reviewer instance for code audit
  - Release checker (deterministic final gate)
  - Readiness report generation
  - Branch push + PR creation

Phase 5 (Week 6+): Memory + hardening
  - Failure signature normalization and retrieval
  - Architecture decision recording
  - Environment profiles
  - Rate limit handling
  - Context window management for long tasks
  - Optional: SQLite migration for run store
```

### Reconciled Run Contract (Codex's Schema, Adopted)

```json
{
  "run_id": "uuid",
  "repo_path": "/absolute/path",
  "objective": "Implement user profile page with tests and E2E verification",
  "scope": {
    "allowed_paths": ["src/", "tests/", "docs/"],
    "forbidden_paths": [".env", "infra/prod/", "deploy/"]
  },
  "acceptance": {
    "functional": [
      "User can navigate to /profile",
      "Profile displays name, email, and avatar",
      "Profile data loads from API"
    ],
    "quality_gates": [
      "lint passes with zero warnings",
      "typecheck passes",
      "unit tests pass",
      "no new dependencies with known vulnerabilities"
    ],
    "ui_checks": [
      "Profile page renders at 1440px and 390px viewports",
      "No console errors on /profile route",
      "Avatar image loads without broken image icon"
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

### Reconciled Defect Packet (Codex's Schema, Adopted)

```json
{
  "defect_id": "uuid",
  "severity": "P0",
  "type": "ui-functional",
  "summary": "Save button remains disabled after valid form input",
  "repro_steps": [
    "Open /settings",
    "Fill display name field with valid input",
    "Observe save button state"
  ],
  "expected": "Save button enabled after valid input",
  "observed": "Button remains disabled",
  "evidence": {
    "screenshot": "artifacts/screenshots/settings-disabled.png",
    "console_log": "artifacts/logs/browser-console.txt",
    "trace": "artifacts/playwright-trace.zip"
  },
  "suspected_scope": ["src/components/SettingsForm.tsx", "src/hooks/useFormValidation.ts"]
}
```

### Reconciled Manager System Prompt

The full prompt from my v2 document stands, with these additions from Codex's spec:

**Added rules:**
- All verification output must use the defect packet schema. No free-form prose defects.
- Read the run contract's `scope.allowed_paths` and `scope.forbidden_paths` before delegating any implementation work. Instruct Codex to stay within scope.
- When delegating to the Claude reviewer, include: the diff, the run contract's acceptance criteria, the plan, and any relevant defect history. The reviewer is stateless — give it everything.
- After implementing a milestone, always request hooks BEFORE requesting UI verification. The executor enforces this, but don't waste an iteration by trying to skip it.
- Use the app-supervisor action to launch the app. Do not tell Codex to launch the app.

---

## Final Decision Matrix

| Decision Point | Codex's Position | My Position | Final Decision |
|---------------|-----------------|-------------|----------------|
| OpenClaw | Keep as control plane | Drop | **Drop** |
| Orchestration model | Deterministic state machine | Claude AI manager | **Claude AI manager with executor-enforced guardrails** |
| acpx | Keep | Keep | **Keep** |
| Codex as builder | Keep | Keep | **Keep** |
| Claude as reviewer | Checkpoint-only | Checkpoint-only | **Checkpoint-only, invoked by manager** |
| Gemini | Later | Not in v1 | **Not in v1** |
| Zep | Later | Not in v1 | **Not in v1** |
| Run contract format | JSON schema | Markdown files | **JSON schema (Codex wins)** |
| Defect format | Formal JSON packets | Informal text | **Formal JSON packets (Codex wins)** |
| Memory layer | 4-layer model + SQLite | File-based markdown | **File-based first, SQLite later (hybrid)** |
| App supervisor | Separate concern | Inline in orchestrator | **Separate concern (Codex wins)** |
| Release checker | Explicit deterministic agent | Completion checklist | **Explicit deterministic agent (Codex wins)** |
| Manager prompt | One-liner | Full system prompt + patterns | **Full system prompt (Claude wins)** |
| Delegation patterns | Not addressed | 5 documented patterns | **5 documented patterns (Claude wins)** |
| Phasing | Claude at Phase 3 | Claude at Week 1 | **Claude at Phase 1 (Trevor's requirement)** |
| Browser verification | Agree | Agree | **Agreed** |
| Git strategy | Agree | Agree | **Agreed** |
| Permissions | Agree + acpx flag detail | Agree | **Codex's version with acpx flags** |
| Guardrails | Agree + path scoping | Agree | **Codex's version with path scoping** |

---

## What to Build Next

The three documents together form the complete spec:

1. **autonomous-agent-system-architecture-review.md** — Foundation: stack decisions, agent roles, branch strategy, auth model, memory, cost, failure modes, MVP definition, roadmap
2. **agent-delegation-architecture-v2.md** — Delegation model: manager agent loop, executor design, system prompt, delegation patterns, action schema, sample session
3. **codex-audit-and-reconciliation.md** (this document) — Final decisions: reconciled architecture, adopted schemas from Codex, phasing, merged design

**Immediate next step:** Build the executor. That is the foundation everything else stands on. It's ~500 lines of Python. Once it works, you can test it manually (you issue actions) before wiring Claude as the manager.

**What to tell Codex to build:**
1. The executor script (Python, action loop, guardrail enforcement, acpx integration)
2. The run store directory structure with contract/defect/artifact schemas
3. The deterministic lane scripts (hook runner, app supervisor, Playwright runner, release checker)

**What to keep for Claude to produce:**
1. The manager system prompt (refined from v2)
2. The delegation pattern library
3. The reviewer prompts
4. The memory strategy and retrieval logic

This matches your operating model: Codex builds, Claude plans and reviews.
