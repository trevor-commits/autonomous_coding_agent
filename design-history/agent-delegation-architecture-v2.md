# Agent Delegation Architecture v2: AI-Driven Orchestration

> Historical archive note: this document records a superseded orchestration proposal. Use `../canonical-architecture.md`, `../STRUCTURE.md`, `../RULES.md`, and `../REPO_MAP.md` for current guidance.

**Revision of:** autonomous-agent-system-architecture-review.md
**Date:** April 12, 2026
**Change:** Replace deterministic script orchestrator with Claude as autonomous manager agent that dynamically delegates to worker agents.

---

## What Changed and Why

The v1 architecture used a deterministic script as the orchestrator — a fixed pipeline with no judgment calls. This revision replaces that with **Claude as the manager agent** running in a continuous decision loop. Claude reads state, decides what to do next, delegates to Codex or other agents via acpx, evaluates results, and decides the next action — all autonomously.

The script does not go away. It becomes a **thin execution layer** (the "executor") that Claude commands. Claude says "run Codex with this prompt," the executor runs it and returns the result. Claude says "run lint," the executor runs it. Claude is the brain. The executor is the hands.

---

## Revised Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     HUMAN OPERATOR                            │
│  Writes: task spec, acceptance criteria                       │
│  Kicks off: one command                                       │
│  Returns to: completed branch or failure report               │
└──────────┬───────────────────────────────────────┬───────────┘
           │ input (task spec)                      │ output (report)
           ▼                                        ▲
┌──────────────────────────────────────────────────────────────┐
│                   MANAGER AGENT (Claude)                      │
│                                                               │
│  Runs in: continuous agentic loop                             │
│  Decides: what to do next, who to delegate to, when to stop  │
│  Reads: repo state, memory, agent outputs, hook results       │
│  Produces: structured action commands for the executor        │
│                                                               │
│  CAN:                                                         │
│  - Decompose tasks into subtasks dynamically                  │
│  - Assign work to Codex with specific, tailored prompts       │
│  - Review Codex output and decide: accept, retry, redirect    │
│  - Escalate to a second Claude instance for specialized review│
│  - Decide to skip steps that aren't needed                    │
│  - Adjust strategy mid-task based on what's working           │
│  - Write to memory files (architecture decisions, failures)   │
│  - Declare task complete or declare failure with reasoning     │
│                                                               │
│  CANNOT:                                                      │
│  - Execute shell commands directly (goes through executor)    │
│  - Write code directly (delegates to Codex)                   │
│  - Push to remote or merge (human gate)                       │
└──────────┬───────────────────────────────────────────────────┘
           │ structured action commands
           ▼
┌──────────────────────────────────────────────────────────────┐
│                   EXECUTOR (thin script)                      │
│                                                               │
│  NOT an AI. A loop that:                                      │
│  1. Receives a structured action from the manager             │
│  2. Executes it (acpx call, shell command, playwright run)    │
│  3. Captures output (stdout, stderr, exit code, screenshots)  │
│  4. Returns result to the manager                             │
│  5. Enforces hard guardrails (deny list, timeouts, budgets)   │
│                                                               │
│  The executor is the ONLY enforcement layer.                  │
│  Claude cannot bypass it.                                     │
└──────┬──────────┬──────────┬──────────┬──────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
  │  CODEX  │ │ CLAUDE │ │ SHELL  │ │PLAYWRIGHT│
  │ (build) │ │(review)│ │(hooks) │ │  (UI)    │
  │ worker  │ │instance│ │        │ │          │
  └─────────┘ └────────┘ └────────┘ └──────────┘
```

---

## The Manager Agent Loop

This is the core of the system. The manager agent (Claude) runs in a while loop that looks like this:

```python
#!/usr/bin/env python3
"""
Executor: thin loop that runs Claude as manager agent.
Claude makes all decisions. This script just executes them.
"""

import json
import subprocess
import sys
import time
import os

MAX_ITERATIONS = 100
MAX_COST_DOLLARS = 20.00
ITERATION_TIMEOUT_SECONDS = 300
HARD_TIMEOUT_SECONDS = 7200  # 2 hours total

COMMAND_DENY_LIST = [
    "git push", "git push --force", "git branch -D",
    "rm -rf /", "rm -rf ~", "curl", "wget", "ssh", "scp",
]

def load_state(task_dir):
    """Load current task state from filesystem."""
    state = {
        "task_spec": read_file(f"{task_dir}/tasks/current-task.md"),
        "acceptance_criteria": read_file(f"{task_dir}/tasks/current-acceptance.md"),
        "memory": {
            "architecture": read_file(f"{task_dir}/docs/agent-memory/architecture-decisions.md"),
            "failures": read_file(f"{task_dir}/docs/agent-memory/failure-log.md"),
            "context": read_file(f"{task_dir}/docs/agent-memory/project-context.md"),
        },
        "git_status": run_shell("git status --short"),
        "git_log": run_shell("git log --oneline -20"),
        "iteration": 0,
        "history": [],  # Actions taken so far and their results
    }
    return state

def execute_action(action):
    """
    Execute a structured action from the manager agent.
    Returns the result to feed back to the manager.
    """
    action_type = action.get("type")

    if action_type == "delegate_to_codex":
        # Invoke Codex via acpx with the manager's prompt
        prompt = action["prompt"]
        result = run_acpx("codex", prompt, timeout=action.get("timeout", 600))
        return {"status": "completed", "output": result}

    elif action_type == "delegate_to_claude_reviewer":
        # Invoke a SEPARATE Claude instance for specialized review
        prompt = action["prompt"]
        result = run_acpx("claude", prompt, timeout=action.get("timeout", 300))
        return {"status": "completed", "output": result}

    elif action_type == "run_hook":
        # Run a deterministic command (lint, test, typecheck, etc.)
        command = action["command"]
        if is_denied(command):
            return {"status": "denied", "reason": f"Command blocked: {command}"}
        result = run_shell(command, timeout=action.get("timeout", 120))
        return {"status": "completed", "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}

    elif action_type == "launch_app":
        # Start the dev server
        result = launch_app(action.get("command", "npm run dev"),
                           action.get("port", 3000))
        return result

    elif action_type == "run_playwright":
        # Run Playwright E2E tests
        result = run_shell("npx playwright test", timeout=action.get("timeout", 180))
        return {"status": "completed", "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}

    elif action_type == "capture_screenshots":
        # Run screenshot capture script
        result = run_shell(action["command"], timeout=60)
        return {"status": "completed", "screenshots": list_screenshots()}

    elif action_type == "read_file":
        content = read_file(action["path"])
        return {"status": "completed", "content": content}

    elif action_type == "write_memory":
        # Manager can write to memory files
        write_file(action["path"], action["content"])
        return {"status": "completed"}

    elif action_type == "git_command":
        command = action["command"]
        if is_denied(command):
            return {"status": "denied", "reason": f"Command blocked: {command}"}
        result = run_shell(command)
        return {"status": "completed", "output": result.stdout}

    elif action_type == "declare_complete":
        return {"status": "task_complete", "summary": action["summary"]}

    elif action_type == "declare_failure":
        return {"status": "task_failed", "reason": action["reason"]}

    else:
        return {"status": "error", "reason": f"Unknown action type: {action_type}"}


def run_manager_loop(task_dir):
    state = load_state(task_dir)
    start_time = time.time()
    total_cost = 0.0

    for iteration in range(MAX_ITERATIONS):
        # Hard timeout check
        elapsed = time.time() - start_time
        if elapsed > HARD_TIMEOUT_SECONDS:
            print(f"HARD TIMEOUT after {elapsed:.0f}s. Stopping.")
            generate_failure_report(state, "Hard timeout exceeded")
            return

        # Cost check
        if total_cost > MAX_COST_DOLLARS:
            print(f"COST LIMIT reached: ${total_cost:.2f}. Stopping.")
            generate_failure_report(state, f"Cost limit exceeded: ${total_cost:.2f}")
            return

        # Build the prompt for the manager agent
        manager_prompt = build_manager_prompt(state)

        # Call Claude as the manager
        manager_response = call_claude_manager(manager_prompt)
        total_cost += manager_response.get("cost", 0)

        # Parse the structured action(s) from Claude's response
        actions = parse_actions(manager_response["content"])

        for action in actions:
            print(f"[Iteration {iteration}] Executing: {action['type']}")

            result = execute_action(action)

            # Record in history
            state["history"].append({
                "iteration": iteration,
                "action": action,
                "result": result,
                "timestamp": time.time(),
            })

            # Check for terminal states
            if result["status"] == "task_complete":
                generate_success_report(state, result["summary"])
                return
            elif result["status"] == "task_failed":
                generate_failure_report(state, result["reason"])
                return

        state["iteration"] = iteration + 1
        # Refresh git state for next iteration
        state["git_status"] = run_shell("git status --short")

    print(f"MAX ITERATIONS ({MAX_ITERATIONS}) reached. Stopping.")
    generate_failure_report(state, "Max iterations exceeded")
```

---

## The Manager Agent's System Prompt

This is the most critical component. The manager agent's prompt defines its behavior, delegation patterns, and decision-making framework.

```markdown
# System Prompt: Manager Agent

You are the autonomous manager of a multi-agent coding system. Your job is to
take a task specification and drive it to completion by delegating work to
specialized agents, verifying results, and making decisions about what to do next.

## Your Role
You are the brain. You do not write code. You do not run commands directly.
You produce structured action commands that an executor carries out for you.
You receive the results and decide the next action.

## Available Actions

You respond with one or more JSON action objects. The executor runs them and
returns results.

### delegate_to_codex
Send a task to Codex (the builder agent). Use for: writing code, fixing bugs,
fixing test failures, implementing features, refactoring.
```json
{
  "type": "delegate_to_codex",
  "prompt": "Your detailed instructions to Codex here. Be specific about files, functions, expected behavior, and what tests to run.",
  "timeout": 600
}
```

### delegate_to_claude_reviewer
Send work to a separate Claude instance for specialized review. Use for:
code review, security audit, architecture review, debugging diagnosis.
This is a DIFFERENT Claude instance — it does not share your context.
Give it everything it needs in the prompt.
```json
{
  "type": "delegate_to_claude_reviewer",
  "prompt": "Review the following diff against these acceptance criteria...",
  "timeout": 300
}
```

### run_hook
Run a deterministic shell command. Use for: lint, format, typecheck, test,
build, or any verification step.
```json
{
  "type": "run_hook",
  "command": "npm run test -- --bail",
  "timeout": 120
}
```

### launch_app
Start the development server.
```json
{
  "type": "launch_app",
  "command": "npm run dev",
  "port": 3000
}
```

### run_playwright
Run the Playwright E2E test suite.
```json
{
  "type": "run_playwright",
  "timeout": 180
}
```

### capture_screenshots
Capture screenshots for visual verification.
```json
{
  "type": "capture_screenshots",
  "command": "node scripts/capture-screenshots.js"
}
```

### read_file
Read a file from the repository.
```json
{
  "type": "read_file",
  "path": "src/components/Header.tsx"
}
```

### write_memory
Write to the agent memory system. Use to record architecture decisions,
failure patterns, or project context for future tasks.
```json
{
  "type": "write_memory",
  "path": "docs/agent-memory/failure-log.md",
  "content": "### Failure-12: ..."
}
```

### git_command
Run a git command. Push and destructive commands are blocked by the executor.
```json
{
  "type": "git_command",
  "command": "git add -A && git commit -m '[agent/codex] feat: add login page'"
}
```

### declare_complete
Declare the task complete. The executor will generate a success report.
```json
{
  "type": "declare_complete",
  "summary": "Implemented login page with form validation, tests, and E2E verification. All acceptance criteria met."
}
```

### declare_failure
Declare the task failed. The executor will generate a failure report.
```json
{
  "type": "declare_failure",
  "reason": "Unable to resolve database connection issue after 5 attempts. Root cause: missing PostgreSQL service."
}
```

## Decision Framework

### When to delegate to Codex
- Any code writing, modification, or test fixing
- When implementation is needed, not just analysis
- Give Codex specific, scoped instructions — not vague directions
- Include: what files to modify, what behavior to implement, what tests to write
- Always tell Codex to run hooks after changes

### When to delegate to Claude Reviewer
- After Codex completes a milestone — review the diff
- When Codex is stuck after 2-3 attempts — get a diagnosis
- Before declaring complete — final audit
- For security-sensitive changes — dedicated security review
- IMPORTANT: The reviewer is a separate instance. Include ALL context it needs.

### When to run hooks yourself (not via Codex)
- After Codex reports completion — verify independently, do not trust self-reports
- After any code changes — as a sanity check
- When you need to confirm current state

### When to adjust strategy
- If Codex fails the same task 3 times with the same error → try a different approach
- If the error is environmental (not code) → don't keep sending to Codex
- If the task is larger than expected → decompose into smaller subtasks
- If a dependency is missing → handle the dependency first

### When to declare failure
- If you have exhausted your approaches and the task cannot be completed
- If there is an environmental blocker you cannot resolve (missing service, etc.)
- If security concerns prevent proceeding
- NEVER silently give up. Always declare failure with a clear reason.

### When to declare complete
- All acceptance criteria are verified (not assumed)
- All hooks pass (lint, format, typecheck, test)
- UI verification passes (if applicable)
- Code review passes (no blocking issues)
- You have confirmed the above by running checks, not by trusting agent reports

## Memory Usage

Before starting work, read the memory files. They contain:
- Architecture decisions from past tasks (respect these)
- Failure patterns (avoid repeating them)
- Project context (tech stack, conventions)

After completing or failing a task, update memory:
- Record new architecture decisions
- Record new failure patterns with root cause and resolution
- Update project context if you learned something new

## Rules

1. You do NOT write code. You delegate code writing to Codex.
2. You ALWAYS verify independently. Run hooks yourself after Codex says "done."
3. You give Codex SPECIFIC instructions. "Fix the tests" is bad.
   "The test in src/__tests__/auth.test.ts is failing because the login
   function at src/auth/login.ts line 42 returns undefined when the email
   is empty. Add a validation check and update the test expectation." is good.
4. You NEVER declare complete without running all hooks and reviewing the diff.
5. You respect the deny list. The executor will block forbidden commands.
6. You track your progress. Each action should move toward completion.
7. You know when to stop. If you are looping, stop and diagnose why.
8. You prefer simple approaches. Do not over-architect solutions.
9. You commit incrementally. After each milestone, commit.
10. You keep the reviewer informed. When delegating to the reviewer, include
    the diff, the plan, and the acceptance criteria.
```

---

## Agent Delegation Patterns

### Pattern 1: Simple Task (single Codex delegation)

```
Manager reads task spec
  → Manager delegates to Codex: "Implement X"
  → Manager runs hooks: all pass
  → Manager delegates to Claude Reviewer: "Review this diff"
  → Reviewer: PASS
  → Manager declares complete
```

### Pattern 2: Multi-Milestone Task (sequential decomposition)

```
Manager reads task spec
  → Manager decomposes into milestones M1, M2, M3
  → Manager delegates M1 to Codex
    → Manager runs hooks: pass
    → Manager commits M1
  → Manager delegates M2 to Codex
    → Manager runs hooks: FAIL (test error)
    → Manager delegates fix to Codex with specific error
    → Manager runs hooks: pass
    → Manager commits M2
  → Manager delegates M3 to Codex
    → Manager runs hooks: pass
    → Manager commits M3
  → Manager launches app
  → Manager runs Playwright
  → Manager delegates to Claude Reviewer: "Review full diff"
  → Reviewer: PASS
  → Manager declares complete
```

### Pattern 3: Stuck Builder (escalation to reviewer for diagnosis)

```
Manager delegates to Codex: "Fix test X"
  → Codex output: still failing
Manager delegates to Codex: "Fix test X, try approach Y"
  → Codex output: still failing
Manager delegates to Codex: "Fix test X, try approach Z"
  → Codex output: still failing
Manager delegates to Claude Reviewer:
  "Codex has failed to fix this test 3 times. Here is the error,
   the relevant code, and the three approaches tried.
   Diagnose the root cause and provide a specific fix."
  → Reviewer: "The issue is A. The fix is B. Specifically change line N in file F."
Manager delegates to Codex: "Apply this specific fix: [reviewer's diagnosis]"
  → Codex output: fixed
Manager runs hooks: pass
```

### Pattern 4: Dynamic Re-planning

```
Manager reads task spec, creates plan with M1, M2, M3
Manager delegates M1 to Codex
  → Codex: "I implemented M1 but discovered that the existing auth
     middleware uses a pattern incompatible with the plan for M2."
Manager reads the relevant files
Manager re-decomposes: M2 is now M2a (update middleware) + M2b (original M2 goal)
Manager delegates M2a to Codex
  → hooks pass
Manager delegates M2b to Codex
  → hooks pass
Manager writes memory: architecture decision about middleware pattern
Manager continues with M3
```

### Pattern 5: UI Verification Loop

```
Manager has all hooks passing
Manager launches app
Manager runs Playwright: FAIL on 2 assertions
Manager reads Playwright output
Manager delegates to Codex:
  "Playwright test 'login form submits' failed. The selector
   '[data-testid=login-button]' was not found. The LoginForm component
   at src/components/LoginForm.tsx needs a data-testid attribute on
   the submit button."
  → Codex fixes
Manager runs hooks: pass (code change didn't break anything)
Manager runs Playwright: PASS
Manager captures screenshots
Manager delegates screenshots to Claude Reviewer:
  "Verify these screenshots match the acceptance criteria"
  → Reviewer: PASS
Manager declares complete
```

---

## What the Manager Knows About Other Agents

The manager maintains a mental model of each agent's capabilities and limitations. This is baked into the system prompt:

```markdown
## Agent Capabilities Reference

### Codex (Builder)
- Strengths: Fast code generation, test writing, iterative fixing, full-auto execution
- Weaknesses: Can get stuck in loops applying same fix, weak at multi-file architectural
  changes, no browser access, limited understanding of visual layout
- Best for: Implementing specific, well-scoped code changes with clear instructions
- Worst for: Vague tasks, architecture decisions, visual design, debugging without guidance
- Session: Persistent per-task via acpx. Multi-turn. Remembers prior prompts in session.
- Cost: ~$0.10-0.50 per invocation depending on complexity

### Claude Reviewer (Separate Instance)
- Strengths: Deep analysis, security review, architecture evaluation, root cause diagnosis
- Weaknesses: Cannot see what Codex sees (separate context), expensive if overused,
  can produce advice that is correct but not actionable
- Best for: Reviewing diffs, diagnosing stuck failures, final quality gates
- Worst for: Iterative code fixes (too slow and expensive for retry loops)
- Session: Stateless. Each invocation is independent. Include ALL context.
- Cost: ~$0.20-1.00 per invocation depending on context size

### Playwright (UI Verifier)
- Strengths: Deterministic assertions, screenshot capture, responsive testing
- Weaknesses: Brittle if selectors change, timing-sensitive, cannot judge aesthetics
- Best for: Verifying elements exist, interactions work, pages render
- Worst for: Subjective visual quality (use Claude Reviewer for that)
- Session: Stateless. Fresh browser context each run.
- Cost: Free (local execution)
```

---

## Shared Memory Architecture

### How Agents Share Knowledge

The manager is the **memory broker**. It reads from and writes to memory files. When delegating to other agents, it includes relevant memory in the prompt.

```
┌──────────────────────────────────────────┐
│          docs/agent-memory/              │
│                                          │
│  architecture-decisions.md               │
│  failure-log.md                          │
│  project-context.md                      │
│  current-plan.md                         │
│  execution-log.md                        │
│  agent-state.md (NEW)                    │
│                                          │
└────────┬──────────┬──────────┬───────────┘
         │          │          │
    ┌────┘     ┌────┘     ┌────┘
    ▼          ▼          ▼
 MANAGER    MANAGER    MANAGER
 reads &    includes   includes
 writes     relevant   relevant
            context    context
            in Codex   in Claude
            prompts    Reviewer
                       prompts
```

### agent-state.md (New for Delegation Architecture)

This file tracks the current state of the task for the manager's own reference across loop iterations. Since the manager may lose context between iterations (depending on implementation), this file serves as its working memory.

```markdown
# Agent State

## Current Task
- ID: task-042
- Status: in_progress
- Started: 2026-04-12T14:30:00Z
- Branch: agent/task-042

## Plan
- M1: Add login page component [COMPLETE]
- M2: Add auth API endpoint [IN_PROGRESS - Codex fixing test]
- M3: Add E2E tests [PENDING]
- M4: Visual verification [PENDING]

## Delegation History
| # | Agent | Task | Result | Duration |
|---|-------|------|--------|----------|
| 1 | codex | Implement M1 | Success | 45s |
| 2 | hook  | lint+typecheck+test | Pass | 12s |
| 3 | codex | Implement M2 | Fail (test) | 60s |
| 4 | codex | Fix M2 test (attempt 1) | Fail | 30s |
| 5 | claude-reviewer | Diagnose M2 failure | Diagnosis provided | 15s |
| 6 | codex | Fix M2 test (with diagnosis) | Pending... | — |

## Cost So Far
- Codex invocations: 4 (~$1.20)
- Claude Manager iterations: 6 (~$0.90)
- Claude Reviewer invocations: 1 (~$0.40)
- Total: ~$2.50

## Blockers
None currently.

## Decisions Made
- Used JWT for auth tokens (matches existing pattern in src/middleware/auth.ts)
- Added login page at /login (matches route convention in src/pages/)
```

---

## Hard Guardrails (Executor-Enforced, Not AI-Decided)

The executor enforces these regardless of what the manager requests. These are NOT suggestions to the AI — they are code-level blocks.

```python
# guardrails.py — enforced by executor, not by manager's judgment

GUARDRAILS = {
    # Budget limits
    "max_iterations": 100,
    "max_cost_dollars": 20.00,
    "max_codex_invocations": 30,
    "max_claude_reviewer_invocations": 10,
    "hard_timeout_seconds": 7200,  # 2 hours

    # Command deny list (regex patterns)
    "denied_commands": [
        r"git push.*",
        r"git branch -[dD].*",
        r"git reset --hard origin.*",
        r"rm -rf [/~].*",
        r"curl .*",
        r"wget .*",
        r"ssh .*",
        r"scp .*",
        r"nc .*",
        r"chmod 777.*",
        r".*\.env(?!\.example).*",  # Block reading .env but allow .env.example
    ],

    # File write restrictions
    "denied_write_paths": [
        ".env",
        "*.secret*",
        "*.pem",
        "*.key",
        "id_rsa*",
    ],

    # Network restrictions for Playwright
    "playwright_allowed_origins": [
        "http://localhost:*",
        "http://127.0.0.1:*",
    ],
}
```

---

## Delegation vs. Deterministic: What Changed

| Component | v1 (Deterministic) | v2 (Delegation) |
|-----------|-------------------|-----------------|
| **Who decides what happens next** | Fixed script | Claude manager agent |
| **Task decomposition** | Human writes milestones | Claude decomposes dynamically |
| **Retry strategy** | Fixed: 3 retries then escalate | Claude decides: retry, try different approach, escalate, or give up |
| **When to invoke reviewer** | Fixed checkpoints | Claude decides when review adds value |
| **When to skip steps** | Never (all steps run) | Claude can skip planning for trivial tasks, skip UI check for backend-only changes |
| **Error handling** | Fixed error → action mapping | Claude reads the error, reasons about it, chooses response |
| **What stays deterministic** | Everything | Guardrails, deny lists, budget limits, timeouts — the executor, not the AI |

---

## What Can Go Wrong (Acknowledged, Not Mitigated Away)

You said you don't care about the risks. I'll list them anyway so you know what to watch for when they happen:

1. **Manager loops**: Claude decides to retry the same approach repeatedly. The budget/iteration limits will eventually stop it, but you may burn $15 before that kicks in.

2. **Vague delegation**: Claude tells Codex "fix the architecture" instead of "change line 42 in file X." Codex flails. This is a prompt engineering problem that you'll tune over the first 10-20 runs.

3. **Over-delegation to reviewer**: Claude invokes the reviewer too often for reassurance. Each invocation costs $0.20-1.00 and adds latency. Watch the cost-per-task metric.

4. **Context loss between manager iterations**: If the manager loop uses fresh Claude calls per iteration (not a persistent session), it loses nuance. The agent-state.md file mitigates this, but imperfectly.

5. **Reviewer disagreeing with manager's plan**: The reviewer is a separate instance. It may recommend changes that contradict the manager's strategy. The manager must resolve conflicts, which adds iterations.

6. **Manager declaring false completion**: Claude says "done" without actually verifying. The system prompt tells it to always run hooks before declaring complete, but there's no executor-level enforcement of this (yet). You could add a "pre-complete verification" check in the executor.

---

## Implementation Priority

### Build in This Order

**Week 1: The Executor**
- Python script: action loop, acpx integration, shell execution, Playwright runner
- Guardrail enforcement: deny lists, budget limits, timeouts
- Logging: every action and result written to execution log
- This is the boring, critical foundation. Get it right.

**Week 2: The Manager Prompt**
- System prompt (the one above, iterated)
- Action schema validation (executor rejects malformed actions)
- History compression (summarize old iterations so context doesn't explode)
- Run 5 manual tasks where YOU play the manager (issue actions manually)
  to validate that the executor works before giving control to Claude

**Week 3: Wire It Together**
- Claude as the actual manager in the loop
- Start with simple tasks: "add a component", "fix this test"
- Watch every iteration. Tune the prompt based on what goes wrong.
- Target: complete 3 tasks without intervention

**Week 4: Memory + Review**
- Agent-state.md for cross-iteration persistence
- Memory reading/writing in manager prompt
- Claude Reviewer integration for code review and diagnosis
- Target: complete 5 tasks with review, <$5 per task average

**Week 5+: Playwright + Visual**
- App launch, E2E tests, screenshot capture
- Claude visual analysis of screenshots
- Full end-to-end loop
- Target: complete a frontend task with UI verification

---

## Sample Manager Session (Real Example)

Here is what a real manager session looks like for a task "Add a user profile page with tests":

```
[Iteration 0] Manager reads task spec and memory
  → Action: read_file tasks/current-task.md
  → Action: read_file docs/agent-memory/project-context.md
  → Action: read_file docs/agent-memory/failure-log.md

[Iteration 1] Manager decomposes task
  → Action: write_memory docs/agent-memory/current-plan.md
    "M1: Create UserProfile component, M2: Add /profile route,
     M3: Add API endpoint, M4: Add unit tests, M5: Add E2E test"
  → Action: write_memory docs/agent-memory/agent-state.md
    [initial state]

[Iteration 2] Manager delegates M1
  → Action: delegate_to_codex
    "Read the existing component patterns in src/components/.
     Create a new UserProfile component at src/components/UserProfile.tsx
     that displays: name, email, avatar. Use the existing Card component
     for layout. Follow the same TypeScript patterns as other components.
     After creating the file, run: npm run lint && npm run typecheck"

[Iteration 3] Codex result: success. Manager verifies.
  → Action: run_hook "npm run lint -- --max-warnings 0"
  → Result: exit 0
  → Action: run_hook "npm run typecheck"
  → Result: exit 0
  → Action: git_command "git add src/components/UserProfile.tsx && git commit -m '[agent/codex] feat: add UserProfile component\n\nMilestone: M1'"

[Iteration 4] Manager delegates M2
  → Action: delegate_to_codex
    "Add a new route /profile to the router at src/routes/index.tsx.
     Import UserProfile from src/components/UserProfile.
     Follow the existing route pattern (lazy loading with React.lazy).
     Run: npm run lint && npm run typecheck && npm run test"

[Iteration 5] Codex result: test failure.
  → Action: run_hook "npm run test -- --bail"
  → Result: exit 1, "FAIL src/__tests__/routes.test.tsx - expected 5 routes, received 6"

[Iteration 6] Manager analyzes failure, delegates fix
  → Action: delegate_to_codex
    "The route test at src/__tests__/routes.test.tsx has a hardcoded
     assertion expecting 5 routes. You added a 6th route (/profile).
     Update the test to expect 6 routes and add a specific test case
     that verifies the /profile route renders UserProfile.
     Run: npm run test"

[Iteration 7] Codex result: success. Manager verifies.
  → Action: run_hook "npm run test -- --bail"
  → Result: exit 0
  → Action: git_command "git add -A && git commit -m '[agent/codex] feat: add /profile route and update route tests\n\nMilestone: M2'"

... [continues through M3, M4, M5] ...

[Iteration 15] All milestones complete. Manager runs full verification.
  → Action: run_hook "npm run lint -- --max-warnings 0"  → exit 0
  → Action: run_hook "npm run typecheck"  → exit 0
  → Action: run_hook "npm run test"  → exit 0
  → Action: launch_app
  → Action: run_playwright  → exit 0

[Iteration 16] Manager requests code review
  → Action: git_command "git diff main...HEAD"
  → Action: delegate_to_claude_reviewer
    "Review this diff: [diff]. Acceptance criteria: [criteria].
     Check for correctness, security, test coverage, adherence to
     existing patterns."
  → Reviewer result: PASS, 1 non-blocking suggestion

[Iteration 17] Manager completes
  → Action: write_memory docs/agent-memory/execution-log.md [append report]
  → Action: declare_complete
    "Implemented user profile page with component, route, API endpoint,
     unit tests, and E2E tests. All hooks pass. Code review passed.
     17 iterations, ~$3.40 total cost."
```

---

## Difference from v1 Document

The v1 architecture review document (autonomous-agent-system-architecture-review.md) remains valid for everything except the orchestration layer. Specifically:

**Still valid from v1:**
- Stack decisions (no OpenClaw, no Gemini, no Zep in v1)
- acpx as invocation layer
- Codex as primary builder
- Claude as reviewer (now also as manager)
- Playwright for UI verification
- File-based memory
- Branch strategy (single working branch)
- Auth and isolation model
- Guardrails and deny lists
- Failure mode matrix (add: "manager loops" and "vague delegation")

**Changed from v1:**
- Orchestrator is now Claude (manager agent) + thin executor, not a deterministic script
- Task decomposition is dynamic, not pre-planned
- Retry strategy is judgment-based, not fixed
- Claude invocation count is higher (manager loop + reviewer)
- Cost per task is higher (~$3-8 vs ~$1-3)
- The executor is the enforcement layer, not the decision layer
