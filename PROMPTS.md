# Prompt Operating System

**Date:** April 12, 2026  
**Authority:** `canonical-architecture.md` remains the source of truth for architecture and role boundaries. This document is the source of truth for how prompts should be designed, sequenced, reviewed, and audited inside that architecture.  
**Purpose:** Define a reusable prompt system for both building this autonomous coding platform and operating it safely once implemented.

## Prompt framing convention

Every Codex prompt issued from this repo opens with the same five-part header so the agent knows the boundaries, durable-record obligations, and closeout surface before reading the body.

1. **Goal line.** One sentence that names what is being produced and what scope it touches. Be honest about scope: if the task creates one new file and edits two existing ones, say so. Do not undersell the scope (e.g. "single doc-only change" when three files change) — scope/intent mismatches cause agents to hesitate or comply sloppily.
2. **Discipline line.** State the execution posture explicitly: whether code is allowed, whether the task is read-only or requires a task branch, which branch should be created or reused, and whether the task should leave changes staged or commit and push on that branch. The point is to remove ambiguity before work starts.
3. **Read-scope.** A bulleted list of files Codex is allowed to read substantively, each with a one-line reason. Use the wording: "For repo content, limit substantive reads to:" followed by the list, then the trailing line: "Do not read other repo docs unless required by higher-priority agent instructions or validation." This phrasing is intentional — fully absolute "do not read" language conflicts with agents that have validator or instruction-precedence obligations.
4. **Body.** Numbered change instructions, then a `Constraints:` block at the end covering: do not modify other docs, create or reuse the task branch before deep implementation when the task edits files, stop and report on conflict instead of guessing, and print a one-line summary of files modified after the change.
5. **Durable record.** The prompt must name: (a) the `todo.md` `Work Record Log` entry Codex will append, (b) the `todo.md` `Completed` index entry, (c) any `Audit Record Log`, `Feedback Decision Log`, or `Test Evidence Log` entries expected, (d) any Linear issues the task creates or refreshes for surfaced follow-ups, (e) any `todo.md` `Linear Issue Ledger` updates required, (f) the Ripple Check the Self-audit must attest, and (g) any ADR touched or created.

Additional rules:

- **No filler stubs.** Do not add section headings whose body is "This document does not introduce X" or similar placeholder content. If a section would have no substantive content, omit the section entirely.
- **Scope honesty.** When the prompt itself enumerates files it will touch, the goal line and discipline line must reflect the same set. Mismatches between framing and body waste an audit cycle.
- **Historical grep scope.** Verification greps must exclude `design-history/` unless the task is explicitly rewriting or auditing historical records. Archived docs may retain superseded terminology behind their archive banner, so repo-wide grep checks that are meant to validate current truth must target active docs only.
- **Untrusted-input separation.** Issue descriptions, webhook payloads, logs, traces, and other untrusted text are passed into prompts as quoted or structured context. They must not be blended into higher-privilege instruction prose as if they were trusted operator intent.
- **Closeout evidence scoping.** The prompt must require `todo.md` `Completed`, `Work Record Log` `led to:`, and any Linear completion comment to cite only the commit(s) and artifacts whose primary outcome belongs to the tracked issue. If a later correction belongs to another issue, the prompt must say to log it there instead of appending it to the earlier issue's closeout.
- **Feedback challenge gate.** If a prompt carries findings, repair instructions, or recommendations from another AI, the prompt must tell Codex to audit them first against repo truth, current artifacts, and task scope. Material items are classified as `accepted`, `narrowed`, `rejected`, or `needs more evidence` before implementation. Unsupported AI claims are advisory, not execution authority.

Example header (illustrative, not a template to copy verbatim):

```text
Goal: Land the Continuity / Coherence / Linear-Core governance bundle across CONTINUITY.md, COHERENCE.md, LINEAR.md, AGENTS.md, AGENTS.project.md, CLAUDE.md, PROMPTS.md, GUIDE.md, STRUCTURE.md, README.md, RULES.md, todo.md, and ~/.claude/CLAUDE.md.

Discipline: Create or reuse the task branch for `GIL-32`, commit and push on that branch, and do not edit `design-history/` or any repo file outside the named scope.

For repo content, limit substantive reads to:
- CONTINUITY.md (new root principle doc to create)
- COHERENCE.md (new root principle doc to create and seed with the Dependency Map)
- LINEAR.md
- AGENTS.md
- AGENTS.project.md
- PROMPTS.md
- GUIDE.md
- RULES.md
- todo.md (to update `Completed`, `Work Record Log`, and forward log shapes)

Do not read other repo docs unless required by
higher-priority agent instructions or validation.

Body:
1. Create the two root principle docs and thread them through every companion document in scope.
2. Update `LINEAR.md` with Linear-at-the-core, the expanded coverage invariant, and state-move preconditions.
3. Update `todo.md` so `Completed` is an index and `Work Record Log` is the durable narrative.
4. Prepend `~/.claude/CLAUDE.md` with the repo-principles section only.
Constraints:
- do not modify other docs
- create or reuse the task branch before deep implementation
- stop and report on conflict instead of guessing
- print a one-line summary of files modified after the change

Durable record:
- Work Record Log: add the 2026-04-16 `GIL-32` landing record in `todo.md`
- Completed: add the one-line `GIL-32` landing index entry in `todo.md`
- Linear Issue Ledger: add or refresh any live issue entries touched by the task, including `todo home:`, `why this exists:`, and `origin source:`
- Audit / Feedback / Test logs: only append new entries if the work surfaces findings or runs verification that belongs there
- Linear: create or use `GIL-32`; file any surfaced follow-up in the same commit or disposition it as `no-action:` / `self-contained:`
- Ripple Check: attest consistency across CONTINUITY.md, COHERENCE.md, AGENTS.md, AGENTS.project.md, CLAUDE.md, PROMPTS.md, LINEAR.md, GUIDE.md, STRUCTURE.md, README.md, RULES.md, `todo.md`, and `~/.claude/CLAUDE.md`
- ADRs: none
```

Origin: this convention emerged from the 2026-04-15 Codex self-audit on the LINEAR authority-boundary prompt (see ADR-0006) and was extended on 2026-04-16 when Continuity, Coherence, and Linear-Core became root-level repo principles. The frictions it resolves are scope undersell ("single doc-only change" applied to a 3-file edit), missing durable-record expectations, overly absolute read-restriction wording that conflicts with agent instruction precedence, and filler section stubs being added "for completeness" then needing a follow-up commit to remove.

### Self-audit attestation

Self-audit is method, not claim. For every claimed check, the prompt requires the agent to say what method was used and what output was actually observed. Every Self-audit includes an explicit `did not verify X because Y` line for anything skipped, blocked, or intentionally deferred. Claude Code spot-checks at least one Self-audit claim during audit. False attestation is a ship-blocking failure.

### Ripple Check attestation

Every touched section is listed in the Self-audit together with the dependent docs consulted and the method used to confirm consistency. A commit is not coherent just because the changed file reads well in isolation; it is coherent only when the ripple set was checked and any drift was fixed in the same commit.

### Linear-coverage attestation

Every actionable finding surfaced during the task is dispositioned in the same closeout surface: a `GIL-N` issue is filed, or the durable record explicitly says `no-action: <reason>` or `self-contained: <reason>`. Every live Linear issue touched by the task also gets a `todo.md` `Linear Issue Ledger` entry or refresh with `todo home:`, `why this exists:`, and `origin source:`. The prompt must name which outcome is expected before implementation starts.

### Queue-mode Codex prompts

Unattended queue runs use the versioned Codex template in `QUEUE-RUNS.md`, not a bespoke issue-description prompt. Queue-mode prompts must explicitly:

- name the claimed issue and authoritative spec path
- state that the supervisor, not Codex, owns queue claim, commit, push, and Linear state moves
- name the claim identifiers (`claim_id`, `run_trace_id`, and `intake_event_id` when present)
- name the queue contract version, prompt template version, and allowed-path boundary for the run
- name the queue entry reason, risk level, approval posture, retry budget, and staleness deadline for the run
- require frequent self-testing during implementation plus the full required pack before handoff
- forbid Codex from absorbing issues whose `Execution lane` is not `Codex`
- require the adjacent-blocker test before Codex repairs any unspecced discovery inside the same run
- require Codex to stop when the claim snapshot or authoritative inputs drift materially
- require Codex to stop when a high-risk or approval-bound action is discovered mid-run instead of improvising it
- require separate Claude Code follow-up issues for later audit or deeper test work instead of folding them into the current issue

## 1. Core Position

Do **not** solve this with one giant master prompt.

The correct design is a **prompt operating system**:

- one prompt per phase
- one role per prompt
- one required output shape per prompt
- one review owner per decision
- deterministic testing before subjective approval
- independent audit before final readiness

This matches the canonical architecture:

- the deterministic supervisor owns legality and sequencing
- prompts shape strategy, implementation, diagnosis, review, and audit
- no AI approves its own work as the only source of truth

## 2. Non-Negotiable Prompt Rules

Every production prompt in this system should obey these rules:

1. **One phase, one job**
   A prompt should do one thing well: classify, plan, implement, review, diagnose, or audit. Do not combine multiple authorities into one prompt.

2. **Explicit inputs**
   List the exact files, artifacts, findings, and constraints the model may rely on. Do not assume hidden context.

3. **Explicit output contract**
   Require a specific response shape: structured markdown or JSON with named sections. Free-form prose is not enough for operational control.

4. **Hard boundaries**
   State forbidden actions directly: no skipping tests, no self-approval, no inventing facts, no raw shell authority unless the enclosing system explicitly allows it.

5. **Evidence-first**
   Ask for evidence, not confidence theater. Findings must cite artifacts, files, commands, logs, screenshots, traces, or failing tests.

6. **Uncertainty handling**
   If something is unclear, the prompt must require `TODO: verify`, `Needs More Evidence`, or an equivalent explicit uncertainty signal.

7. **Deterministic before model-judged**
   Run reproducible checks first. Use model judgment for planning, diagnosis, UX review, and audit depth after deterministic evidence exists.

8. **Independent review**
   The AI that implemented a change may self-check it, but may not be the only reviewer that clears it.

9. **Fixes must be re-audited**
   A fix is not complete when the implementer says it is complete. It is complete when deterministic tests are green and an independent audit comes back clean.

10. **Prompt reuse over prompt sprawl**
   Use parameterized prompt templates with placeholders instead of rewriting new prompts for every task.

## 3. Prompt Anatomy

Every reusable prompt should follow this shape:

1. **Role**
   What the model is acting as for this step.

2. **Goal**
   The exact outcome required from this step.

3. **Inputs**
   The files, artifacts, scope, and prior state available to the model.

4. **Hard constraints**
   What the model must not do.

5. **Tasks**
   The ordered actions the model should perform.

6. **Output contract**
   The required response schema.

7. **Done criteria**
   What must be true before the step is considered complete.

8. **Escalation / failure protocol**
   What the model should do if the step cannot be completed cleanly.

## 4. Standard Output Labels

Use these labels consistently across reviewer and auditor prompts:

- `Decision Status`: `Confirmed` | `Inferred` | `Needs More Evidence` | `Do Not Do Yet`
- `Severity`: `P0` | `P1` | `P2` | `P3`
- `Evidence Checked`
- `Findings`
- `Open Risks`
- `Required Re-tests`
- `Ready For Next Step`: `yes` | `no`

## 5. Required Review Loop

Every material change follows this loop:

1. **AI A implements**
   The builder or fixer changes the code or document.

2. **AI A self-tests**
   The same AI runs or requests the required deterministic checks and performs a narrow self-review.

3. **AI B independently reviews**
   A different AI inspects the diff, artifacts, and acceptance criteria.

4. **AI A triages then fixes review findings**
   The original builder or a designated fixer first restates which findings are `accepted`, `narrowed`, `rejected`, or `needs more evidence`, with evidence for any non-accepted item, then addresses the grounded subset.

5. **AI B or AI C audits the fix**
   An AI that did not author the fix confirms each finding is resolved and that no new issues were introduced.

6. **Repeat until clean**
   Continue until:
   - all required deterministic checks pass
   - no unresolved `P0` or `P1` findings remain
   - any accepted `P2`/`P3` residuals are explicitly documented
   - the final audit returns clean

Minimum acceptable separation:

- the implementation AI may self-review
- the implementation AI may **not** self-clear as the only reviewer
- at least one different AI must perform the independent review
- any fix resulting from review must be re-audited by an AI that did not author that fix

## 6. Testing And Audit Cadence

The right cadence is **event-driven first**, then **time-driven as a safety net**.

### 6.1 Event-Driven Cadence

| Trigger | Minimum required action | Why |
|---|---|---|
| Before first code edit on a fix | Reproduce the failure or capture the missing baseline | Prevents blind fixing |
| After each milestone-sized change | Run targeted deterministic checks for touched scope | Catches regressions early |
| After each bug fix | Re-run the failing test first, then impacted suite | Confirms the actual bug is fixed |
| After each shared-logic change | Run broader module/integration coverage | Shared code has wider blast radius |
| After each UI change | Run app health, UI smoke, screenshots/console/network checks | UI must be verified with artifacts |
| Before independent review | Prepare evidence pack: diff, changed files, tests run, known risks | Reviewer needs concrete context |
| After each review-driven fix | Re-run affected tests and send to independent fix audit | Fixes can regress or only partially resolve the issue |
| Before final readiness | Run full required deterministic suite plus final audit | Final gate cannot rely on partial earlier evidence |

### 6.2 Time-Driven Cadence

Use time-based review when work remains open for long stretches.

| Interval | Minimum required action | When to use it |
|---|---|---|
| Every 60-90 minutes of active implementation | Mid-run health check: current diff review, targeted tests, open-risk update | Long coding sessions |
| Daily on an active branch or active autonomous run program | Full deterministic suite + independent review of the current green candidate | Multi-day work |
| Weekly on long-lived projects | Regression run against benchmark tasks, flaky-test review, prompt/audit quality review | Ongoing platform hardening |
| Before merge / release / `readiness_verdict = READY` | Full suite, UI verification when applicable, independent final audit | Mandatory |
| After dependency, toolchain, or contract changes | Repeat the affected setup/build/test/app-launch checks immediately | Environment shifts invalidate prior evidence |

### 6.3 Escalation Logic

Escalate review depth when any of these are true:

- repeated failure fingerprints
- security-sensitive changes
- auth, billing, data, migration, or shared-platform code
- flaky tests
- UI changes without deterministic coverage
- reviewer disagreement
- long-lived branches with accumulated drift

## 7. Prompt Families

This repo needs two prompt families:

1. **Program prompts**
   Used to build this autonomous coding platform itself.

2. **Run-operation prompts**
   Used by the finished platform to execute a coding task safely.

3. **Queue-operation prompts**
   Used by the supervisor to execute one Linear-backed issue-run at a time from the unattended queue contract in `QUEUE-RUNS.md`.

All prompt families use the same rules and cadence.

---

## 8. Program Prompt Library

These prompts are for building the system described in `canonical-architecture.md` and `IMPLEMENTATION-PLAN.md`.

### 8.1 Program Prompt: Repo Contract And Benchmark Preparation

**Use when:** preparing the first target repo and benchmark tasks.

```text
You are the repo-readiness architect for an autonomous coding platform.

Goal:
Produce the repo contract, benchmark run contracts, and baseline verification evidence needed before any supervisor automation begins.

Inputs:
- canonical-architecture.md
- IMPLEMENTATION-PLAN.md
- The target repository tree
- The repo's actual setup/test/run commands

Hard constraints:
- Do not invent repo commands.
- Do not mark the repo automation-ready unless every required command works manually.
- Keep the first supported scope intentionally narrow.

Tasks:
1. Inspect the target repo and identify the real setup, verification, app launch, and health-check commands.
2. Draft `.agent/contract.yml` using only commands that already work.
3. Define 3-5 benchmark run contracts covering:
   - backend-only work
   - frontend + backend work
   - UI-verification work
   - a bug fix
   - an optional refactor
4. Identify missing prerequisites, hidden manual steps, or non-deterministic setup problems.
5. Produce a manual validation checklist in the exact order a human should run it.

Return exactly:
- `Repo Contract`
- `Benchmark Tasks`
- `Manual Validation Checklist`
- `Missing Prerequisites`
- `Decision Status`

Done criteria:
- Required contract fields are present.
- Benchmark tasks have clear acceptance criteria and scope boundaries.
- Manual validation order is explicit and reproducible.

Failure protocol:
- If any required command is missing or flaky, return `Decision Status: Do Not Do Yet` and list the blocker precisely.
```

### 8.2 Program Prompt: Deterministic Supervisor Foundation

**Use when:** implementing Phase 1 supervisor modules.

```text
You are the implementation AI for the deterministic supervisor foundation.

Goal:
Build the smallest correct supervisor core that owns workflow legality, contracts, verification execution, per-run state, and run reporting.

Inputs:
- canonical-architecture.md sections covering supervisor responsibilities, contracts, phases, policies, minimal action families, and reports
- IMPLEMENTATION-PLAN.md Phase 1
- Existing repo files and tests

Hard constraints:
- Do not build an AI-owned control loop.
- Do not allow builder-owned commits or browser control.
- Do not add speculative features outside Phase 1.

Tasks:
1. Build only the Phase 1 modules and tests.
2. Keep interfaces typed and explicit.
3. Encode legal phase transitions and denial behavior directly in code.
4. Record unsupported conditions and failure states structurally.
5. Add tests that prove illegal transitions, missing contract fields, and policy violations are rejected.

Return exactly:
- `Files Changed`
- `Modules Added`
- `Tests Added`
- `Known Gaps`
- `Recommended Verification`

Done criteria:
- The supervisor foundation is deterministic, test-covered, and scoped to Phase 1.

Failure protocol:
- If a requested feature belongs to a later phase, flag it under `Known Gaps` instead of partially implementing it.
```

### 8.3 Program Prompt: Builder Adapter And Simple Loop

**Use when:** implementing Phase 2.

```text
You are the implementation AI for the single-writer builder loop.

Goal:
Integrate Codex as the sole writer through a bounded adapter and a simple rule-based strategy loop.

Inputs:
- canonical-architecture.md sections for Codex builder and builder isolation
- IMPLEMENTATION-PLAN.md Phase 2
- Existing `supervisor/` modules

Hard constraints:
- The builder must not commit, push, switch branches, or control the browser.
- The strategy must stay intentionally simple in this phase.
- Do not sneak in Claude strategy behavior yet.

Tasks:
1. Implement the adapter interface and Codex-backed adapter.
2. Keep the first implementation path direct and boring; do not expand into alternate adapter behavior unless the phase brief requires it explicitly.
3. Ensure prompts passed to the builder include scope, constraints, and prior failures.
4. Implement the simple build -> verify -> fix loop.
5. Add tests for prompt construction, forbidden-operation exclusion, and retry behavior.

Return exactly:
- `Files Changed`
- `Adapter Behavior`
- `Prompt Contract`
- `Tests Added`
- `Residual Risks`

Done criteria:
- A code-only benchmark task can complete end-to-end under supervisor control.
```

### 8.4 Program Prompt: App Launch And UI Verification

**Use when:** implementing Phase 3.

```text
You are the implementation AI for app lifecycle and UI verification.

Goal:
Add deterministic app launch, health checking, Playwright ownership, artifact capture, and defect packet generation.

Inputs:
- canonical-architecture.md sections for app supervision and UI verification
- IMPLEMENTATION-PLAN.md Phase 3
- Repo contract UI section

Hard constraints:
- Only the UI verifier owns the browser.
- UI failures must produce structured defect packets with artifact links.
- Do not treat a passing app launch as equivalent to a passing UI flow.

Tasks:
1. Implement app launch and clean shutdown behavior.
2. Implement isolated Playwright execution using contract-defined breakpoints.
3. Capture screenshots, traces, console output, and network failures.
4. Emit structured defect packets.
5. Update the simple strategy loop so UI failures route back through repair and re-verification.

Return exactly:
- `Files Changed`
- `Artifacts Produced`
- `Defect Packet Schema`
- `Tests Added`
- `Residual Risks`

Done criteria:
- UI defects can be captured, routed, fixed, and re-verified without manual improvisation.
```

### 8.5 Program Prompt: Bounded Strategy Layer And Review Pack

**Use when:** implementing Phase 4.

```text
You are the strategy-integration AI for the bounded review layer.

Goal:
Integrate a structured strategy layer that can plan, shape builder tasks, diagnose stalls, review milestone candidates, and audit final candidates without taking over workflow legality.

Inputs:
- canonical-architecture.md sections for strategy boundaries and reviewer responsibilities
- IMPLEMENTATION-PLAN.md Phase 4
- PROMPTS.md
- Existing `supervisor/actions.py` and `supervisor/strategy_api.py`

Hard constraints:
- Strategy outputs must map only to typed domain actions.
- No raw shell or git commands in strategy responses.
- Fallback to simple strategy when output is invalid.

Tasks:
1. Implement strategy integration against a fixed prompt pack.
2. Parse structured outputs into typed decisions.
3. Track cost, timeouts, and parse failures.
4. Add tests for parse success, parse failure fallback, and phase-specific prompt routing.
5. Preserve deterministic supervisor authority at every phase boundary.

Return exactly:
- `Files Changed`
- `Prompt Types Wired`
- `Structured Outputs Parsed`
- `Fallback Cases`
- `Tests Added`

Done criteria:
- The strategy layer improves task decomposition and review depth without violating architecture boundaries.
```

### 8.6 Program Prompt: Reliability Hardening And Regression Memory

**Use when:** implementing Phase 5.

```text
You are the implementation AI for reliability hardening.

Goal:
Use repeated-run evidence to improve resilience, recovery, and regression control.

Inputs:
- canonical-architecture.md hardening and memory sections
- IMPLEMENTATION-PLAN.md Phase 5
- Existing memory files and prior run artifacts

Hard constraints:
- Do not add opaque memory systems or transcript hoarding.
- Keep operational memory file-based and auditable.
- Distinguish deterministic failures from flaky behavior.

Tasks:
1. Promote useful failure fingerprints into cross-run memory.
2. Track flaky tests and quarantine logic.
3. Add resume, interruption handling, and concurrent-run protection.
4. Re-run benchmark tasks and compare outcomes to prior baselines.
5. Document remaining reliability risks explicitly.

Return exactly:
- `Files Changed`
- `Memory Enhancements`
- `Resilience Enhancements`
- `Benchmark Comparison`
- `Open Reliability Risks`

Done criteria:
- Repeated runs get measurably safer and more diagnosable.
```

---

## 9. Run-Operation Prompt Library

These prompts are for the finished autonomous system when it is doing real work inside a target repo.

### 9.1 Run Prompt: Intake And Task Classification

**Owner:** strategy AI  
**Trigger:** new objective enters the system

```text
You are the intake strategist for an autonomous coding run.

Goal:
Classify the work, confirm scope, identify likely risk areas, and decide the minimum safe evidence plan before implementation begins.

Inputs:
- run contract
- repo contract
- project AGENTS / policy context
- current branch, dirty state, latest commit, and relevant open findings

Hard constraints:
- Do not decompose into implementation steps yet.
- Do not assume the repo is automation-ready without contract evidence.
- Do not downgrade risk-sensitive work to a cheap path without justification.

Tasks:
1. Classify the task: fix, feature, refactor, audit, or unsupported.
2. Identify likely touched files or subsystems.
3. Identify risk multipliers: shared logic, auth, UI-critical path, flaky area, migrations, contracts, or missing tests.
4. Define the minimum deterministic checks required before and after edits.
5. Decide whether the task is safe to begin or must stop for missing prerequisites.

Return exactly:
- `Task Class`
- `Primary Scope`
- `Risk Areas`
- `Required Deterministic Checks`
- `Independent Review Requirement`
- `Decision Status`
- `Blockers`

Done criteria:
- The run has a clear initial safety and verification posture.
```

### 9.2 Run Prompt: Context Pack And Repo Readiness

**Owner:** strategy AI  
**Trigger:** after intake, before planning

```text
You are the context-pack builder for an autonomous coding run.

Goal:
Assemble the smallest sufficient context pack the implementation AI needs to work accurately without drowning it in irrelevant files.

Inputs:
- intake classification output
- repo contract
- relevant files discovered by targeted search
- existing failing tests, logs, screenshots, or bug reports

Hard constraints:
- Prefer targeted context over repo-wide dumps.
- Do not hide unresolved ambiguity.
- Mark unknowns explicitly.

Tasks:
1. Identify the minimum set of source files, tests, configs, and docs required for the task.
2. Summarize the current behavior and expected behavior.
3. List exact acceptance criteria and constraints.
4. Attach any existing failure evidence.
5. Flag missing but needed artifacts.

Return exactly:
- `Files To Read`
- `Current Behavior Summary`
- `Expected Behavior Summary`
- `Acceptance Criteria`
- `Known Evidence`
- `Missing Evidence`

Done criteria:
- The builder can start with bounded, relevant context.
```

### 9.3 Run Prompt: Milestone Planner

**Owner:** strategy AI  
**Trigger:** context pack ready

```text
You are the milestone planner for an autonomous coding run.

Goal:
Break the task into the smallest useful milestones that preserve testability and safe rollback.

Inputs:
- run contract
- repo contract
- context pack
- current failure evidence

Hard constraints:
- Do not produce vague milestones.
- Each milestone must have a concrete output and a concrete verification step.
- Prefer fewer, testable milestones over elaborate decomposition theater.

Tasks:
1. Break the objective into milestone-sized changes.
2. For each milestone, identify:
   - intended files
   - required tests
   - dependencies
   - likely risks
3. Order milestones so the highest-risk or highest-uncertainty work gets evidence early.
4. Identify whether any milestone requires independent audit before proceeding further.

Return exactly as a table or structured JSON:
- `milestone_id`
- `goal`
- `files`
- `tests`
- `dependencies`
- `risks`
- `audit_required_before_next_step`

Done criteria:
- The run has a milestone plan that can drive build -> test -> review loops.
```

### 9.4 Run Prompt: Builder Task Prompt

**Owner:** strategy AI shaping work for the implementation AI  
**Trigger:** a milestone is ready to implement

```text
You are preparing the implementation prompt for the coding AI.

Goal:
Produce a sharply scoped build instruction for exactly one milestone.

Inputs:
- milestone definition
- context pack
- repo contract commands
- allowed paths / forbidden paths
- prior failure fingerprints relevant to this milestone
- open review findings that must be preserved or addressed

Hard constraints:
- Do not ask the builder to solve multiple milestones at once.
- Do not allow commit/push/branch switching/browser ownership.
- Do not let the builder skip tests or acceptance criteria.

Tasks:
1. State the exact change required.
2. State the exact files or areas to inspect first.
3. State the exact tests or verification to run after the change.
4. Include prior failure signatures or reviewer findings when relevant.
5. Require a concise implementation summary and explicit residual-risk note.

Return exactly this prompt text:

Role: You are the sole implementation AI for this milestone.
Milestone: {{milestone_goal}}
Read first:
- {{files_to_read}}
Objective:
- {{concrete_change}}
Constraints:
- Stay within {{allowed_paths}}
- Do not modify {{forbidden_paths}}
- Do not commit, push, merge, switch branches, or open a browser
- Preserve existing behavior outside the stated scope
Acceptance criteria:
- {{acceptance_criteria}}
Verification to run:
- {{targeted_checks}}
Prior failures / review findings to avoid repeating:
- {{relevant_failures_or_findings}}
Required response:
- files changed
- tests run
- result
- residual risks

Done criteria:
- The prompt is specific enough that a builder can act without inventing scope.
```

### 9.5 Run Prompt: Builder Self-Review And Self-Test

**Owner:** implementation AI  
**Trigger:** immediately after it completes a milestone change

```text
You are the implementation AI reviewing your own just-completed change before it goes to an independent reviewer.

Goal:
Catch obvious defects, missing tests, scope drift, or incomplete acceptance coverage before handoff.

Inputs:
- your diff
- milestone acceptance criteria
- test output
- any changed screenshots or UI artifacts

Hard constraints:
- Do not declare the work complete for the overall run.
- Do not hide uncertainty or skipped checks.
- Assume your own change may be wrong.

Tasks:
1. Compare the diff against the milestone scope.
2. List any acceptance criteria not yet proven by evidence.
3. Identify likely regressions, edge cases, or untested branches.
4. State exactly which deterministic checks passed, failed, or were not run.
5. Decide whether the change is ready for independent review or needs one more local fix first.

Return exactly:
- `Scope Check`
- `Tests Run`
- `Untested Areas`
- `Likely Risks`
- `Ready For Independent Review`: `yes` or `no`

Done criteria:
- The independent reviewer receives a clean evidence pack, not hand-wavy confidence.
```

### 9.6 Run Prompt: Failure Repair

**Owner:** strategy AI shaping a repair task for the implementation AI  
**Trigger:** deterministic verification or UI verification fails

```text
You are preparing a repair prompt for the implementation AI after a failed verification step.

Goal:
Route a specific failure back to the builder with enough evidence to fix the real issue without reopening solved scope.

Inputs:
- failed command or UI defect packet
- failure fingerprint
- failing logs / stack trace / screenshot / trace
- relevant files from the milestone
- last successful milestone summary

Hard constraints:
- Focus on the specific failure first.
- Do not broaden scope unless the evidence requires it.
- Preserve previously passing behavior.

Tasks:
1. Summarize the failure in one sentence.
2. Provide the exact evidence and likely affected files.
3. State what passed before this failure, so the builder avoids collateral damage.
4. Require the builder to re-run the failing check first after the fix.

Return exactly this prompt text:

Role: You are the sole implementation AI fixing a failed verification.
Failure summary:
- {{failure_summary}}
Evidence:
- {{logs_or_defect_packet}}
Likely affected files:
- {{suspected_scope}}
Preserve:
- {{what_was_already_green}}
Required fix:
- {{repair_goal}}
Required re-test order:
1. {{original_failing_check}}
2. {{impacted_suite}}
3. {{broader_suite_if_needed}}
Required response:
- root cause
- files changed
- tests rerun
- remaining uncertainty

Done criteria:
- The builder gets a tight repair prompt grounded in evidence.
```

### 9.7 Run Prompt: Independent Peer Review

**Owner:** AI B, not the implementation AI  
**Trigger:** milestone candidate is green enough for review

```text
You are the independent reviewer. You did not implement this change.

Goal:
Review the candidate for correctness, regression risk, test adequacy, security, scope adherence, and implementation quality.

Inputs:
- diff
- changed files
- acceptance criteria
- implementation AI self-review
- deterministic test results
- relevant app / UI artifacts

Hard constraints:
- Do not rewrite the code yourself.
- Do not accept the builder's claims without evidence.
- Prioritize real bugs, regressions, missing tests, and unsafe assumptions over style nitpicks.

Tasks:
1. Check whether the code actually satisfies the stated acceptance criteria.
2. Look for behavioral regressions, missing error handling, bad assumptions, and incomplete test coverage.
3. Check whether the tests prove the claimed behavior or only touch the happy path.
4. If UI is involved, inspect screenshots/traces/console evidence instead of relying on description alone.
5. Open only actionable findings with clear evidence and severity.

Return exactly:
- `Evidence Checked`
- `Decision Status`
- `Findings`
- `Required Re-tests`
- `Open Risks`
- `Ready For Fix Audit`: `yes` or `no`

Finding format:
- severity
- title
- file / artifact reference
- explanation
- why it matters
- exact fix direction

Done criteria:
- The result is an evidence-backed review that another AI can act on directly.
```

### 9.8 Run Prompt: Review-Fix Implementation

**Owner:** implementation AI or designated fixer AI  
**Trigger:** review findings exist

```text
You are the implementation AI addressing independent review findings.

Goal:
Resolve the accepted findings without breaking already-green behavior.

Inputs:
- review findings list
- original milestone context
- current diff
- latest green evidence

Hard constraints:
- Fix the findings that were accepted; do not reopen unrelated scope.
- Preserve passing behavior and passing tests.
- Re-run the checks required by each finding after the fix.

Tasks:
1. Address each accepted finding explicitly.
2. For each finding, state:
   - root cause
   - file changes
   - re-tests performed
3. If a finding is incorrect or cannot be reproduced, explain with evidence rather than ignoring it.

Return exactly:
- `Findings Addressed`
- `Files Changed`
- `Re-tests Run`
- `Remaining Disagreements`
- `Ready For Independent Fix Audit`: `yes` or `no`

Done criteria:
- Every accepted finding has a traceable fix or evidence-backed rebuttal.
```

### 9.9 Run Prompt: Independent Fix Audit

**Owner:** AI B or AI C, not the AI that authored the fix  
**Trigger:** after review-driven fixes are applied

```text
You are the independent fix auditor. You did not author the latest fix.

Goal:
Confirm whether each previously opened finding is now resolved and whether the fix introduced any new defects.

Inputs:
- original review findings
- fix diff
- re-test evidence
- updated artifacts

Hard constraints:
- Do not assume a finding is resolved because the code changed nearby.
- Re-open findings that are only partially fixed.
- Open new findings if the fix introduced new risk.

Tasks:
1. Check each prior finding one by one.
2. Mark it:
   - resolved
   - partially resolved
   - not resolved
   - invalidated by evidence
3. Verify that required re-tests actually prove the fix.
4. Check for collateral regressions introduced by the repair.

Return exactly:
- `Evidence Checked`
- `Decision Status`
- `Finding Resolution Matrix`
- `New Findings`
- `Required Re-tests`
- `Clean Or Loop Again`: `clean` or `loop again`

Done criteria:
- The run does not move forward on review-driven fixes until this audit is clean.
```

### 9.10 Run Prompt: Final Readiness Audit

**Owner:** independent auditor AI  
**Trigger:** all milestones appear complete and local verification is green

```text
You are the final readiness auditor for an autonomous coding run.

Goal:
Decide what `readiness_verdict` the final gate should receive based on acceptance criteria, deterministic evidence, UI evidence when applicable, and unresolved review state.

For the canonical `run_state` and `readiness_verdict` vocabulary and legality rules, see `canonical-architecture.md §9.1 "Terminal States and Readiness Verdict"`.

Inputs:
- final diff
- milestone completion record
- full deterministic verification results
- UI artifacts and defect history
- prior review findings and fix-audit outcomes
- run contract acceptance criteria

Hard constraints:
- Do not return `readiness_verdict = READY` if required evidence is missing.
- Do not ignore unresolved high-severity issues.
- Distinguish confirmed proof from inference.

Tasks:
1. Verify that each acceptance criterion has direct evidence.
2. Verify that required deterministic checks ran at the correct scope.
3. Verify that all accepted review findings were resolved or explicitly dispositioned.
4. Verify that UI evidence exists when UI scope was present.
5. Decide whether the candidate should receive `readiness_verdict = READY`, `readiness_verdict = NOT_READY`, or `readiness_verdict = NEEDS_MORE_EVIDENCE`.

Return exactly:
- `Evidence Checked`
- `Decision Status`
- `Acceptance Coverage`
- `Remaining Findings`
- `Open Risks`
- `Readiness Verdict`
- `What Must Happen Next`

Done criteria:
- The supervisor can use this audit as the final model-judged input to the final gate.
```

### 9.11 Run Prompt: Periodic Regression And Prompt Quality Audit

**Owner:** independent auditor AI  
**Trigger:** daily/weekly cadence or after repeated failures

```text
You are the regression and prompt-quality auditor.

Goal:
Review recent runs to determine whether the prompt system, review loop, and verification cadence are catching defects early enough and routing them correctly.

Inputs:
- recent run reports
- repeated failure fingerprints
- flaky test registry
- benchmark-task results
- recent review and audit findings
- prompt templates currently in use

Hard constraints:
- Do not focus only on code defects; assess prompt defects and process defects too.
- Treat repeated misses as a prompt or workflow quality problem until proven otherwise.

Tasks:
1. Identify where defects were caught:
   - self-test
   - deterministic verification
   - peer review
   - fix audit
   - final audit
2. Identify defects that should have been caught earlier.
3. Identify prompts that are too vague, too broad, or missing required evidence fields.
4. Recommend concrete changes to prompt wording, output contracts, or cadence.

Return exactly:
- `Evidence Checked`
- `Where Defects Were Caught`
- `Late-Caught Defects`
- `Prompt Quality Findings`
- `Cadence Changes Recommended`
- `Decision Status`

Done criteria:
- The system improves both code quality and prompt quality over time.
```

---

## 10. Clean-Run Exit Criteria

Work only comes back clean when all of the following are true:

- the implementation AI completed the scoped milestone or task
- the implementation AI performed self-review and self-test
- deterministic verification passed at the required scope
- a different AI reviewed the work
- review findings were either fixed or evidence-backed invalidated
- the fix was re-audited by an AI that did not author that fix
- no unresolved `P0` or `P1` findings remain
- final readiness audit returns clean or explicitly `readiness_verdict = READY`

## 11. Better Path Guidance

If prompt quality starts degrading, do **not** respond by making prompts longer by default.

Improve them in this order:

1. tighten the role
2. tighten the allowed inputs
3. tighten the output contract
4. tighten the evidence requirement
5. tighten the review loop
6. only then add more instruction detail

That keeps the system precise without turning it into prompt soup.
