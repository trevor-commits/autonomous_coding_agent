# Canonical Architecture Synthesis

> Historical archive note: this document preserves prior reasoning and intermediate terminology. Do not implement from it directly; use `../canonical-architecture.md`, `../STRUCTURE.md`, `../RULES.md`, and `../REPO_MAP.md` for current guidance.

**Date:** April 12, 2026  
**Purpose:** Capture the full architecture feedback given so far by Codex, Claude, and ChatGPT Pro, explain how the design evolved, and state the current source-of-truth position for this project.

## Status

This document is the canonical synthesis of the architecture discussion history.

It does not erase the earlier documents. Those remain useful as design history:

- `autonomous-agent-system-architecture-review.md`
- `agent-delegation-architecture-v2.md`
- `codex-audit-and-reconciliation.md`
- `three-way-reconciliation-final.md`

However, those documents represent intermediate stages in the design process. This file explains how the discussion evolved and where the architecture landed.

The forward-looking source of truth is now:

- `canonical-architecture.md`

## The Original Goal

The goal never changed during this discussion:

Build an autonomous multi-agent coding system that can:

- take a coding objective
- implement backend and frontend code
- run linting, formatting, typechecking, and tests
- launch the application locally
- verify the frontend visually and functionally
- retry based on failures
- use multiple specialized agents with minimal human hand-holding
- do this in a way that is realistic to operate, not just impressive in theory

The real debate was not about the goal. The debate was about what should sit at the center of the system and who should own correctness.

## Your Initial Architecture Direction

You initially proposed a stack centered around:

- OpenClaw as orchestration / delegation / routing
- `acpx` as unified invocation surface
- Codex as the primary builder / tester
- Claude as planner / reviewer / architecture auditor / quality gate
- Gemini as optional
- Zep as memory layer

You also set strong constraints and preferences:

- Codex should be the workhorse.
- Claude should be planner / reviewer, not main builder.
- The system should be highly autonomous once started.
- Frontend visual verification matters.
- Multiple agents should not edit the same code surface in an unstructured way.
- Stability matters more than cleverness.
- Role separation, permissions, and isolation matter.
- You wanted real delegation, not just a linear code-generation script.

Those constraints shaped every later recommendation.

## The First Major Question

The architecture debate eventually collapsed into one core question:

**Who should own workflow correctness?**

That means:

- phase transitions
- retry limits
- gate ordering
- app lifecycle sequencing
- readiness criteria
- stop conditions
- completion authority

All later feedback was really about this question.

## Codex's First Position

Codex's earliest consistent position was:

- the system is conditionally sound
- multi-agent can work
- Codex should be the main builder
- Claude should be used selectively
- browser/UI verification should be separate from code writing
- memory should be structured rather than transcript-based
- the center of the system should be a deterministic task runner / state machine

The key idea was:

**AI should help make strategy decisions, but the runtime should own correctness.**

Codex's early recommended shape was:

- deterministic manager/runtime at the center
- planner
- builder
- app supervisor
- UI verifier
- auditor
- release checker
- structured artifacts
- structured defect packets
- phased rollout

This was the first complete proposal for a "deterministic supervisor with AI workers."

## Claude's `agent-delegation-architecture-v2.md`

Claude then produced a more aggressively agentic architecture in `agent-delegation-architecture-v2.md`.

The main change in that design was explicit:

- replace the deterministic orchestrator with Claude as an autonomous manager agent
- keep the executor as a thin command runner and guardrail layer
- let Claude dynamically decide what happens next in a loop

Claude's framing in that document was:

- "Claude is the brain"
- "the executor is the hands"
- Claude decomposes tasks dynamically
- Claude delegates to Codex
- Claude decides when to run hooks
- Claude decides when to escalate to reviewer
- Claude writes to memory
- Claude declares completion or failure

That design had meaningful strengths:

- it took your requirement for delegation seriously
- it provided detailed manager prompts
- it documented delegation patterns clearly
- it described realistic stuck-builder and UI-fix loops

But it also made one very strong architectural assumption:

**the manager model should sit above the workflow**

That became the central disagreement.

## Codex's Critique of Claude `v2`

Codex rejected `agent-delegation-architecture-v2.md` as the core control-plane design.

The critique had several parts.

### 1. Workflow correctness was too prompt-dependent

Claude `v2` made the model primary and the executor secondary. That meant:

- completion depended too much on what Claude decided to request
- transitions were too prompt-shaped
- correctness was enforced after the fact instead of built into the run graph

Codex argued that this produces a system that feels autonomous while becoming less reliable.

### 2. Single-writer and repo isolation were not enforced strongly enough

Claude's design still left too much responsibility in general actions like `git_command` and free-form manager choices. It did not sufficiently formalize:

- one writer per worktree
- reviewer read-only boundaries
- commit authority
- rollback semantics

### 3. Completion was not runtime-owned

Claude's prompt said not to declare complete without verification, but the executor did not yet treat that as a mandatory precondition. That left room for false-green outcomes.

### 4. Memory was too markdown-heavy

Claude's file-based memory model was simple, but it blended:

- stable project truth
- current run state
- operational lessons
- delegation history

into human-friendly files in a way that would not scale cleanly.

### 5. Browser verification was too manager-centric

The manager still interpreted browser outcomes and routed work at a fairly free-form level rather than through a dedicated verification lane with structured output.

### 6. The cost and latency model was understated

A manager loop that keeps rebuilding context and making top-level decisions each iteration becomes expensive in both dollars and time.

### 7. Guardrails were not enough

Regex denies are not the same as capability boundaries. Codex pushed for stronger runtime ownership of what can happen when.

The result of this critique was not "no delegation." It was:

**delegation is good, but AI should not own workflow correctness.**

## ChatGPT Pro's Architecture Contribution

You then brought in a long architecture review from ChatGPT Pro.

This was the first third-party proposal that strongly reinforced Codex's main structural claim, but it added several important ideas that were not yet explicit enough in the earlier specs.

### What ChatGPT Pro got most right

#### 1. The Repo Contract

This was ChatGPT Pro's strongest idea.

It proposed that autonomy should not begin on arbitrary repos. Instead, every supported repo should expose a machine-readable contract describing how it works.

That includes commands such as:

- setup
- lint
- typecheck
- test
- app_up
- app_health
- app_down
- optional UI smoke and test-data seed commands

The key implication was:

**if the repo does not define its automation surface, the system should return `UNSUPPORTED` instead of improvising.**

This reframed the problem in a very useful way:

- the main system is not "the agents"
- the main system is the delivery harness plus the repo's declared lifecycle

That insight materially improved the design.

#### 2. OpenClaw should not be in the v1 core loop

ChatGPT Pro argued that OpenClaw could be useful later as an outer shell, operator surface, or messaging layer, but it should not own:

- git safety
- app lifecycle
- branch/worktree semantics
- browser leases
- readiness gates

That matched Codex's general skepticism about putting a chat-oriented orchestration layer at the center of a repo delivery harness.

#### 3. Deterministic Repo Supervisor at the center

ChatGPT Pro's "Repo Supervisor" made the runtime the explicit owner of:

- worktree creation
- gate ordering
- retries
- app launch
- artifact capture
- readiness checks

That aligned strongly with Codex's earlier position.

#### 4. Unsupported repo is a valid outcome

This matters operationally because it prevents fake autonomy. The system should be allowed to say:

- the repo is not yet automation-ready
- fix the contract first
- then run autonomous delivery

#### 5. Better operational framing

ChatGPT Pro emphasized:

- repo readiness over model cleverness
- fixture drift as a real failure mode
- bad acceptance criteria as a real failure mode
- browser verification as an expensive, brittle system unless tightly structured

That was useful hardening.

## Codex's Response to ChatGPT Pro

Codex's reaction to ChatGPT Pro was broadly favorable.

Codex's conclusion was:

- this architecture is materially better than Claude `v2`
- it is the first version that is clearly buildable
- it gets the center of gravity right
- it is strongest on repo contract, delivery harness, and role separation

Codex still tightened a few points:

- `acpx` could still make sense in v1 if unified invocation mattered immediately
- the design still needed exact schemas
- the runtime must remain the final authority
- browser verification should emit defect tickets, not prose

At that stage, Codex's position was:

- proceed with the ChatGPT Pro direction
- but keep the runtime primary
- and keep AI bounded

## Claude's First Reconciliation Document

Claude then produced `codex-audit-and-reconciliation.md`, which was an attempt to merge:

- Claude `v2`
- Codex's critiques
- ChatGPT Pro's architecture

That document made important progress.

Claude explicitly adopted or endorsed several things that Codex and ChatGPT Pro had been right about:

- run contract as JSON
- formal defect packets
- app supervisor as separate concern
- release checker as deterministic final gate
- path-scoped permissions
- stronger artifact structure
- external guardrails over model hooks
- no OpenClaw in v1

Claude also conceded that:

- Codex was right about structured defect output
- Codex was right about machine-readable run contracts
- the runtime needed stronger separation of concerns

However, Claude still preserved one crucial default:

- Claude manager remained primary
- executor remained subordinate, even if stronger than before

Claude's merged framing at that stage was:

**AI manager with executor-enforced invariants**

That was a significant improvement over pure `v2`, but the default authority was still model-first.

## Codex's Critique of Claude's Reconciliation

Codex pushed back again, but more precisely this time.

The key argument was:

**Delegation does not require an AI to own the control path.**

Codex argued that a deterministic supervisor can still support real delegation:

- the strategy layer can decide what the builder should do next
- the strategy layer can decide whether to escalate to reviewer
- the strategy layer can interpret failure packets and choose a repair direction
- the strategy layer can re-plan

while the runtime still owns:

- whether the next phase is legal
- whether gates must run
- whether the app must be healthy before UI verification
- whether the system is allowed to declare readiness

Codex sharpened the difference with this framing:

- in Claude's model, the manager is primary and the executor is a cop
- in the better model, the executor is primary and the manager is a strategist inside a controlled action graph

That distinction was the turning point in the conversation.

## Claude's Concession

After that critique, Claude conceded the architectural point.

This was the most important convergence moment in the whole discussion.

Claude explicitly accepted:

- delegation does not require AI ownership of state transitions
- the executor should be the "brain" for workflow correctness
- Claude should be the "brain" for strategy
- a deterministic supervisor can still ask Claude what the builder should do next
- hooks, readiness, and completion should not depend on prompt compliance

Claude rewrote the model in practical terms:

Old framing:

- Claude says run hooks
- Claude says declare complete
- executor checks whether to allow it

Corrected framing:

- supervisor enters BUILD phase
- supervisor asks AI what to tell Codex to do next
- Codex writes code
- supervisor automatically runs hooks because the phase requires it
- supervisor decides if the run can legally move on
- supervisor asks AI again only within that allowed next-action space

Claude's concession narrowed the real disagreement dramatically.

At that point, the architecture became:

- runtime-first
- strategy-second

## The Final Prompt Direction

After Claude conceded the architecture point, Codex wrote the prompt that should be given to Codex for the first implementation phase.

That prompt said:

- build the executor foundation first
- make it deterministic
- parse repo contract and run contract
- enforce phases
- enforce shell policy and path restrictions
- create run directories and worktrees
- run deterministic verification
- launch app through an app supervisor
- fingerprint failures
- own checkpoint commits
- expose a future decision API for a later AI strategy layer
- do **not** yet implement Claude manager integration

This reflected the design position reached after the whole debate:

**build the harness first, then plug in the strategy layer**

## What Each AI Got Right

### What Codex got right

- Codex should be the primary builder.
- Claude should be checkpoint planner/reviewer, not co-builder.
- Browser ownership should be separate from code writing.
- Workflow correctness should belong to the runtime.
- Structured memory is better than transcript sharing.
- Defect packets should be formal and machine-readable.
- App supervisor and release checker should be separate deterministic concerns.
- A bounded AI strategy layer is compatible with real delegation.

### What Claude got right

- Your delegation requirement was real and should not be hand-waved away.
- AI judgment is genuinely useful for:
  - decomposition
  - prompt crafting
  - failure interpretation
  - retry strategy
  - re-planning
- Delegation patterns should be documented explicitly.
- The strategy layer needs a strong prompt and clear action schema.
- A purely rigid pipeline will not handle novel situations well.
- Claude eventually corrected the control-plane inversion and accepted the runtime-first model.

### What ChatGPT Pro got right

- The repo contract is critical.
- Unsupported repo should be a first-class outcome.
- Repo readiness matters more than agent cleverness.
- OpenClaw should stay out of the v1 core.
- The app should expose a health check as part of contract.
- Better failure modes include:
  - fixture drift
  - bad acceptance criteria
  - browser flake
  - environment drift
- Shell policy should include:
  - allow
  - deny
  - escalate
- Operational memory should be separated from repo truth.

## What Each AI Got Wrong or Underweighted

### Codex's weaker spots

- Early versions did not state the repo contract idea clearly enough.
- Early summaries could read as if a deterministic supervisor meant "not really delegated," even though that was not the intended architecture.
- `acpx` may have been underemphasized in situations where session continuity matters materially.

### Claude's weaker spots

- `v2` gave too much authority to the manager model.
- The early executor was too subordinate.
- Memory started too markdown-centric.
- Browser verification was initially too manager-mediated.
- Completion and progression were initially too dependent on prompt behavior.

### ChatGPT Pro's weaker spots

- It initially pushed hard enough on the deterministic center that it risked underrepresenting your delegation requirement.
- It was somewhat too ready to defer `acpx`.
- Its alternative to Zep could itself become premature infrastructure if overbuilt too early.

## The Main Architectural Evolution

The conversation moved through four recognizable stages.

### Stage 1: Component stack thinking

The discussion began around components:

- OpenClaw
- `acpx`
- Codex
- Claude
- Gemini
- Zep

This was still mostly about which tools belonged in the stack.

### Stage 2: AI manager thinking

Claude `v2` turned the system into:

- a thin executor
- a primary AI manager
- delegated workers underneath

This maximized the appearance of agency, but over-centralized correctness in the model loop.

### Stage 3: Delivery harness thinking

ChatGPT Pro, reinforced by Codex, pulled the discussion toward:

- repo contract
- deterministic supervisor
- worktree discipline
- app supervisor
- browser owner
- release checker
- artifact bundle
- failure fingerprints

This made the system much more operationally grounded.

### Stage 4: Final responsibility split

After Codex's critique and Claude's concession, the final split became:

- runtime owns correctness
- AI owns strategy
- builder writes code
- verifier verifies
- reviewer audits
- repo contract defines lifecycle
- run contract defines task requirements

That is the design point reached so far.

## The Current Source-of-Truth Architecture

The current architecture position is:

- No OpenClaw in the v1 core loop.
- `acpx` may be used behind an adapter, not as an irreplaceable foundation.
- Codex is the sole persistent builder / writer.
- Claude is used for planning, stall diagnosis, and checkpoint/final audit.
- Playwright is the separate UI verifier and sole browser owner.
- A deterministic executor/supervisor sits at the center.
- The executor/supervisor owns:
  - phase machine
  - worktrees
  - gate ordering
  - retries
  - app lifecycle
  - checkpoint commits
  - readiness authority
- The AI strategy layer is pluggable and bounded.
- Repo contract defines per-repo automation surface.
- Run contract defines per-task objective, scope, acceptance, and constraints.
- Defects are emitted as structured packets.
- Run artifacts are stored in a structured run directory.
- Memory is split into:
  - repo truth
  - run truth
  - operational memory
- No Zep in v1.
- No Gemini in v1.
- No multi-writer concurrency in v1.
- No auto-merge in v1.

## Why This Is the Point We Are At

This design is where the discussion landed because each round exposed a different failure mode and pushed the architecture toward a more durable split.

### The original plan exposed the ambition

It made clear that:

- this is not just about code generation
- you want actual autonomous delivery
- you want specialization and delegation
- you care about browser/UI reality

### Claude `v2` exposed the temptation

It showed how natural it is to think:

- "if I want delegation, the manager model should own the loop"

That is seductive because it looks more agentic.

### Codex exposed the control-plane flaw

It forced the distinction between:

- AI strategy
- workflow correctness

That distinction is what the design now rests on.

### ChatGPT Pro exposed the missing harness realism

It contributed the repo contract, unsupported-repo posture, and stronger runtime operational framing.

### Claude's concession resolved the core disagreement

Once Claude accepted that the runtime should be primary and the AI should be the strategist, the architecture stopped being a philosophical debate and became an implementable system design.

## What Is Settled

These points should be treated as settled unless strong implementation evidence later contradicts them:

- Codex is the primary builder.
- Claude is checkpoint planner/reviewer, not co-writer.
- Gemini is not in v1.
- Zep is not in v1.
- One writer per worktree.
- One browser owner per run.
- Reviewer roles are read-only.
- Playwright is the UI verification tool.
- Deterministic verification runs independently of model judgment.
- Structured defect packets are required.
- Repo contract and run contract should both exist.
- App launch/health should be runtime-owned.
- Readiness should be runtime-owned.
- OpenClaw stays out of the v1 core loop.
- The executor should be built before the AI strategy layer is fully integrated.

## What Is Still Open

These questions remain open and should be resolved during implementation rather than by more abstract debate:

- What is the minimum viable repo contract for v1?
- Should `acpx` be used in the first implementation or added behind the adapter immediately after the supervisor is stable?
- What exact decision API should connect the supervisor to the later Claude strategy layer?
- What exact artifact and failure-fingerprint schemas should be standardized first?
- When does file-based operational memory become heavy enough to justify a move to SQLite or similar?

## Canonical Summary

The architecture is no longer:

- "an AI manager that runs a coding system"

It is now:

**a deterministic autonomous delivery harness with a pluggable AI strategy layer, a single Codex writer, a separate UI verifier, structured repo and run contracts, and structured artifacts that make delegation safe and repeatable.**

That is the current source-of-truth position.
