# System Rules

**Date:** April 12, 2026
**Authority:** `canonical-architecture.md` is the source of truth. Every rule in this document is derived from that spec. If this document and the canonical architecture ever conflict, follow the canonical architecture.

**Purpose:** This document lists the specific, enforceable rules of the system — the things that must always be true, the things that are always forbidden, and the boundary conditions that trigger specific behaviors. `LOGIC.md` explains how the system works conceptually. This document says what it is and is not allowed to do.

---

## Ownership Rules

### The supervisor owns:

- Phase transitions (which phase the run is in, what the next legal phase is)
- Whether verification must run (not optional, not skippable by AI)
- Whether the app must be healthy before UI verification starts
- Retry ceilings and stop conditions
- Checkpoint commits (the builder does not commit)
- Budget enforcement (iterations, cost, wall-clock time)
- Final completion authority (`run_state = COMPLETE` requires `readiness_verdict = READY` plus deterministic evidence)
- Command policy (allow, deny, escalate)
- Worktree creation and single-writer lease management
- App lifecycle (launch, health check, shutdown)
- Artifact and report generation
- Run directory management
- Queue intake, claim/release, and queue-state automation permitted by `QUEUE-RUNS.md`

### The AI strategy layer owns:

- Task decomposition into milestones
- Builder prompt composition (what to tell Codex)
- Retry strategy within budget (try a different approach vs. same approach)
- Stall diagnosis (when the builder is stuck on repeated failures)
- Review timing proposals (when to invoke reviewer)
- Audit findings (severity-coded, actionable)
- Re-planning based on evidence

### The AI strategy layer does NOT own:

- Phase transitions
- Whether required gates can be skipped
- Whether the run is ready (that requires deterministic evidence)
- Shell, git, or filesystem mutation primitives
- Commit authority
- Browser control
- App lifecycle decisions

---

## Single-Writer Rules

- Only one code-writing agent may mutate a run worktree. Non-negotiable in v1.
- The builder (Codex) gets exactly one writable worktree per run.
- No other agent may write to the worktree: not the reviewer, not the strategy layer, not the UI verifier.
- The supervisor enforces single-writer via a lease mechanism. A second writer cannot acquire the lease while the first holds it.

---

## Single-Browser-Owner Rules

- Only one verifier may own the browser for a run. Non-negotiable in v1.
- One isolated browser profile per run (temp directory, no carried state).
- The builder cannot control the browser.
- The reviewer cannot control the browser.
- Localhost access only — no external URLs.
- No concurrent browser agents on the same app instance.

---

## Commit Rules

- The supervisor owns checkpoint and landing commits, not the builder.
- The builder edits files but does not have commit authority.
- Commit message format: `[autoclaw/<run_id>] <type>: <description>`
- Checkpoint tags follow the pattern: `autoclaw/<run_id>/start`, `autoclaw/<run_id>/last-green`, `autoclaw/<run_id>/cp-NN`
- Rollback restores the worktree to the last known-good checkpoint rather than relying on ad hoc cleanup.

---

## Git Rules — Forbidden Operations for the Builder

The builder (Codex) is forbidden from running:

- `git push`
- `git pull`
- `git merge`
- `git rebase`
- `git checkout`
- `git switch`

The builder may use read-only git inspection commands (e.g., `git log`, `git diff`, `git status`).

---

## Typed Action Rules

- The AI strategy layer communicates with the supervisor through typed domain actions only.
- Actions may NOT carry arbitrary shell payloads.
- Actions may NOT bypass path, writer, or browser ownership rules.
- Actions are legal only in specific phases — the supervisor rejects out-of-phase actions.
- Actions resolve to supervisor-controlled implementations, not raw command execution.

### Forbidden action patterns (never allowed):

```json
{ "type": "git_command", "command": "git add -A && git commit -m 'done'" }
{ "type": "run_hook", "command": "npm run test -- --bail" }
{ "type": "write_memory", "path": "docs/agent-memory/failure-log.md", "content": "..." }
```

### Required action patterns (always use these):

```json
{ "action": "request_builder_task", "prompt": "...", "milestone": "M2" }
{ "action": "run_contract_command", "name": "test", "scope": "targeted" }
{ "action": "checkpoint_candidate", "reason": "targeted gates passed for milestone M2" }
{ "action": "record_failure_signature", "fingerprint": "...", "evidence_refs": [...] }
{ "action": "propose_terminal_state", "run_state": "BLOCKED", "reason": "Retry threshold exceeded" }
```

---

## Shell Policy Rules

### Auto-allow:

- Repo contract commands (setup, lint, typecheck, test, app_up, app_health, app_down, ui_smoke, seed_testdata)
- Safe repo-local reads
- Safe file operations inside allowed paths

### Auto-deny:

- `git push`, `git pull`, `git merge`, `git rebase`, `git checkout`, `git switch`
- `sudo`
- `ssh`, `scp`
- `rm -rf` outside the run worktree
- Direct edits to secret files (`.env`, credentials, keys)
- Arbitrary external network fetches unless explicitly allowed

### Escalate (stop and report in v1):

- Package installs with network access
- Database migrations
- Container rebuilds
- Infrastructure or CI configuration changes
- Auth-related config changes

The strategy layer never receives direct authority to invoke shell, git, or filesystem mutation primitives outside typed supervisor actions.

---

## Contract Rules

### Repo contract (target repo `.agent/contract.yml`):

- Must exist before a run can begin.
- Must define at minimum: `commands.setup`, `commands.test`, `commands.app_up`, `commands.app_health`.
- If minimum required fields are missing, the run ends with `run_state = UNSUPPORTED`. No improvisation.
- Optional but strongly recommended: `commands.lint`, `commands.typecheck`, `commands.format`, `commands.app_down`, `commands.ui_smoke`, `commands.seed_testdata`.

### Run contract (JSON, per-task):

- Must define: `run_id`, `repo_path`, `objective`, `scope` (allowed_paths, forbidden_paths), `acceptance` (functional, quality_gates, ui_checks), `constraints` (single_writer, max_repair_loops, max_iterations, max_cost_dollars, hard_timeout_seconds).
- Scope paths are enforced by the supervisor — the builder cannot write outside allowed_paths or inside forbidden_paths.

## Issue Queue Rules

- Linear issue metadata is routing input only. It may nominate work, but it may not issue arbitrary commands or replace the repo contract or run contract.
- The supervisor may claim only issues that satisfy the eligibility contract in `QUEUE-RUNS.md`.
- Non-Codex or manual-mode issues are skipped without mutation by the Codex queue.
- Queue-generated Claude Code audit or test follow-up issues must be filed as separate issues and do not block the queue from continuing once the current Codex issue has either landed or blocked cleanly.
- Codex self-testing is mandatory during queue runs: narrow deterministic checks after each material edit cluster, then the full required verification pack before handoff.
- The supervisor, not Codex, owns queue claim, queue release, landing commit, push, and any Linear issue-state move performed by queue automation.

---

## Phase Transition Rules

### Mandatory ordering:

- A build candidate must pass LOCAL_VERIFY before UI_VERIFY.
- The app must be healthy (APP_LAUNCH passed) before Playwright runs.
- FINAL_GATE requires rerun of authoritative gates — not a cached result from earlier.
- `run_state = COMPLETE` is legal only when `readiness_verdict = READY`, all required artifacts named in the run contract exist, all authoritative required checks passed on the final rerun, and no unresolved high-severity defect packets are open.

### COMPLETE legality invariant:

- `run_state = COMPLETE` is legal ONLY when:
  - `readiness_verdict = READY`
  - all required artifacts named in the run contract exist
  - all authoritative required checks passed on the final rerun
  - no unresolved high-severity defect packets are open
- `readiness_verdict = NEEDS_MORE_EVIDENCE` is not terminal. It triggers one more evidence-gathering loop up to the configured bound; after that bound it degrades to `NOT_READY` and the run goes to `BLOCKED`.

### Mandatory escalation:

- Repeated same failure fingerprint beyond threshold must escalate to stall diagnosis or `run_state = BLOCKED`.
- Budget exhaustion must stop the run immediately.

### Illegal transitions:

- No phase may be skipped by the AI or the builder.
- The AI cannot propose `run_state = COMPLETE` without the supervisor's evidence checks passing and `readiness_verdict = READY`.
- The supervisor rejects any transition attempt that violates the phase machine's legal transition graph.

---

## Stop Conditions

The supervisor must stop or block the run when any of the following occur:

- The repo contract is insufficient (missing required fields) → `run_state = UNSUPPORTED`
- A required command is missing or unsupported → `run_state = UNSUPPORTED`
- Codex CLI unavailable at Phase 0 entry → `run_state = UNSUPPORTED`
- The same failure fingerprint exceeds the retry threshold → `run_state = BLOCKED`
- App health does not stabilize within timeout → `run_state = BLOCKED`
- Budget is exhausted (max_iterations, max_cost_dollars, or hard_timeout_seconds) → `run_state = BLOCKED`
- Path or command restrictions are violated → `run_state = BLOCKED`
- An unresolved high-severity review finding remains at FINAL_GATE → `run_state = BLOCKED`
- A landing commit is prepared but push fails → `run_state = BLOCKED` and the queue controller stops before claiming another issue

Stop conditions are enforced by the supervisor. The AI cannot override them.

---

## Permission Rules

### Builder (Codex):

- Read-write on exactly one worktree
- Safe shell inside auto-allow policy
- Git read-only inspection commands
- No merge, rebase, push, branch switching
- No browser control
- No writes outside run scope (allowed_paths)
- Dedicated auth context, isolated runtime where feasible

### UI Verifier (Playwright):

- Browser control (sole owner)
- Localhost access plus explicitly approved hosts only
- Read-only repo access
- Writable temp browser profile directory
- No source edits, no commits

### Reviewer / Auditor (Claude):

- Read-only access to selected files, diffs, and artifacts
- No repo mount or read-only selected bundle only
- No source edits, no browser control, no git mutation
- No shell or network side effects

### Supervisor:

- Full control over run directories, worktree orchestration, and artifact locations

---

## Verification Rules

### Ordering:

1. Deterministic code gates (format, lint, typecheck, test)
2. App health check
3. Deterministic UI verification
4. Optional model-judged UI quality (ambiguity only)
5. Final deterministic readiness gate

### UI verification split target:

- 80–90% deterministic (route availability, click success, console cleanliness, network correctness, required state transitions)
- 10–20% model-judged (semantic layout mismatches, polish issues, subjective correctness where no deterministic rule is practical)

### Defect packets:

- All verification failures must be emitted as structured JSON defect packets.
- Free-form reviewer prose is not the primary defect-routing mechanism.
- Each packet must include: defect_id, severity, type, summary, repro_steps, expected, observed, evidence (screenshot, console_log, trace), suspected_scope, failure_fingerprint.

---

## Memory Rules

### Three tiers — do not mix them:

| Tier | Location | Lifecycle | Managed by |
|------|----------|-----------|-----------|
| Repo truth | In repo, version-controlled | Permanent, human-managed | Human + supervisor |
| Run truth | Supervisor-owned runtime `.autoclaw/runs/<run_id>/` | Per-run, preserved after completion, gitignored | Supervisor |
| Operational memory | Supervisor-owned runtime `.autoclaw/memory/` | Cross-run, subject to TTL, gitignored | Supervisor (post-run) |

### Non-goals for memory in v1:

- No raw transcript retrieval as primary memory
- No chain-of-thought storage
- No external semantic memory system (no Zep)
- No promotion of undocumented assumptions into durable truth

---

## Reporting Rules

Every run must produce both:

- **Machine-readable report (JSON):** `run_id`, `run_state`, `readiness_verdict`, `phases_completed`, `commands_run`, `failures`, `changed_files`, `checkpoint_refs`, `artifact_manifest`, `unresolved_blockers`.
- **Human-readable summary (Markdown):** what changed, what passed, what failed, what's unresolved, what to do next.

Reports are written to the run directory when the supervisor reaches a terminal `run_state`.

---

## Repo Governance Rules

These governance rules derive from `CONTINUITY.md`, `COHERENCE.md`, and `LINEAR.md` `## Linear-at-the-core`. They govern repo landings, audits, and task closeout discipline rather than supervisor runtime behavior.

### Continuity

- `R-CONT-01`: No landing commit without a `todo.md` `Work Record Log` entry.
- `R-CONT-02`: No Linear state move without the required Work Record entry on disk.
- `R-CONT-03`: Self-audit attestation must name the method used for each claimed check and include an explicit `did not verify X because Y` line.
- `R-CONT-04`: Claude Code must spot-check at least one attestation claim per audit and record the outcome in `todo.md` `Audit Record Log`.
- `R-CONT-05`: `design-history/` content is never rewritten to reflect new principles; only forward-facing docs change.

### Coherence

- `R-COH-01`: Every commit that touches a governance doc includes updates to all companion docs referencing the changed section. Ripple Check attestation in Self-audit is mandatory.
- `R-COH-02`: The Dependency Map in `COHERENCE.md` is updated in the same commit as any new inter-doc reference.
- `R-COH-03`: No orphan docs. Every live doc is indexed from `GUIDE.md` or referenced by at least one other live doc. Orphans are either indexed or retired in the same commit they are discovered.

### Linear-Core

- `R-LIN-01`: Every live Linear issue in a non-terminal state has a matching `todo.md` `Linear Issue Ledger` entry recording the issue ID, current status, `todo home:`, `why this exists:`, and `origin source:`.
- `R-LIN-02`: Every `todo.md` `Active Next Steps` item has a matching Linear issue annotated `(GIL-N)`, and that issue also appears in `Linear Issue Ledger`.
- `R-LIN-03`: Any surfaced follow-up implying future work is filed as a Linear issue in the same commit it is recorded, added to `Linear Issue Ledger` in the same commit, and given an explicit `origin source:` instead of being deferred to "later."
- `R-LIN-04`: Every log entry in `todo.md` (`Audit Record`, `Feedback Decision`, `Test Evidence`, `Suggested Recommendation`, `Work Record`) has a `linear:` field populated with a `GIL-N`, `no-action: <reason>`, or `self-contained: <reason>` value.
- `R-LIN-05`: Before any Linear state move or conversation exit, Cowork verifies Linear-coverage for findings surfaced in the interval. Missing ledger entries, missing provenance, status/home drift, or un-Linearized actionable findings block the state move. Linear still holds routing, scheduling, and coverage metadata only; acceptance criteria, decisions, audit conclusions, and reasoning stay in repo docs.

---

## v1 Exclusion Rules

The following are intentionally excluded from v1. Do not build them unless metrics from Phases 0–5 justify the addition:

- OpenClaw as control plane
- Gemini as active worker
- Zep or any external semantic memory layer
- Multi-writer parallelism
- Autonomous merge to main
- Autonomous deployment to production
- Broad plugin marketplace integrations
- Transcript-based shared memory
