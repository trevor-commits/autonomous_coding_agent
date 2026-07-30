# AGENTS.project.md

## Purpose

Repo-local instructions for agents working in this repository.

## Repo Principles

Continuity lives in `CONTINUITY.md`. Conversation memory is temporary; only repo files survive. Every bounded task must leave a durable Work Record, a signed Self-audit, and a stable pointer so the reasoning does not die with the chat.

Coherence lives in `COHERENCE.md`. When one live governance surface changes, every live document that depends on it changes in the same commit, and the Ripple Check is attested before landing.

Linear-Core lives in `LINEAR.md` `## Linear-at-the-core`. Repo docs hold truth; Linear holds routing and coverage. Any surfaced follow-up that implies future work must become a `GIL-N` issue or an explicit `no-action:` / `self-contained:` disposition in the durable record, and every live Linear issue must appear in `todo.md` with a durable home, `why this exists:`, and `origin source:`. All three are loaded before any task. Violating any of them is a ship-blocking failure.

## Source Of Truth

The canonical architecture for this project lives in:

- `canonical-architecture.md`

If another document conflicts with it, follow `canonical-architecture.md`.

The design-history narrative lives in:

- `design-history/canonical-architecture-synthesis.md`

Older architecture documents now live under `design-history/` and are historical context only unless explicitly referenced for a specific comparison task.

## What This Repository Is

This repository currently holds architecture, planning, and source-of-truth documentation for an autonomous coding system.

For quick file lookup and reading order, use `GUIDE.md`, especially the `Quick Reference — Where to Find Things` section.

It is not yet the implementation repository for the supervisor/runtime itself unless and until code is added for that purpose.

## Working Rules

1. Preserve the distinction between:
   - source-of-truth docs
   - design-history docs
2. Do not re-open settled architecture decisions casually.
3. Prefer updating `canonical-architecture.md` when the source-of-truth design changes.
4. Prefer updating `design-history/canonical-architecture-synthesis.md` only when recording meaningful design-history evolution.
5. If adding new docs, update `README.md` so future sessions can orient quickly.
6. If implementation starts in this repo, keep the runtime architecture consistent with the canonical document:
   - deterministic supervisor owns workflow correctness
   - bounded AI strategy layer owns planning/strategy only
   - Codex is sole writer
   - Playwright is sole browser owner
7. Do not treat anything under `design-history/` as authoritative unless the user explicitly asks for historical comparison.

## Current Priority

The next implementation work should align with the phased plan in `canonical-architecture.md`, starting with:

1. repo contract definition
2. deterministic supervisor foundation
3. single-writer builder loop
4. app supervisor and UI verification
5. bounded strategy API integration

## Editing Guidance

- Keep architecture statements concrete and implementation-oriented.
- Prefer structured sections over loose brainstorming.
- When changing the canonical architecture, explain the reason clearly and keep the document internally consistent.
- When in doubt, reduce ambiguity rather than adding optionality.

## Repo Working Expectations

- Use `CONTINUITY.md`, `COHERENCE.md`, `LINEAR.md`, `PROJECT_INTENT.md`, `canonical-architecture.md`, `RULES.md`, `STRUCTURE.md`, and `GUIDE.md` as the current truth set for continuity, coherence, routing, purpose, architecture, constraints, placement, and navigation.
- Record active work, completed work, suggested ideas, audit records, test evidence, and feedback decisions in `todo.md` rather than leaving them only in chat.
- Keep every live Linear issue mirrored in `todo.md` `Linear Issue Ledger` with `todo home:`, `why this exists:`, and `origin source:`; external or connected-system issues do not get a waiver.
- Keep verification evidence in `todo.md`'s `Test Evidence Log`, keep the durable completion narrative in `todo.md`'s `Work Record Log`, and keep the fast landing index in `todo.md`'s `Completed` section.
- Default to a fresh task branch for work that edits files, commits, or pushes. Read-only work may stay branchless.
- Create or reuse the `GIL-N` issue before branching when Linear is live, prefer the Linear-generated branch name when available, and keep the branch mirrored in both `todo.md` and Linear until merge or explicit closeout.
- Ask focused clarifying questions when instructions conflict with the canonical architecture or the repo boundary; otherwise prefer direct execution over repeated approval prompts.
- Do not let unrelated tracked changes block your task. Do not revert them unless the user explicitly asks.
- Commit and push every task-touched file before finishing unless the user explicitly says not to.

## Implementor Role

- Codex is the primary implementor for this repository.
- Codex writes code, modifies doc content, lands commits, and performs a self-audit.
- Claude Code may also write code when doing so is the cleanest way to land an audit-surfaced fix, unblock Codex on a narrow targeted change, or close a small mechanical gap uncovered during line-by-line review. When Code writes code, it is still subject to independent audit — Code never ships its own code as the sole reviewer of record.
- Self-audit is never the ship gate. Claude Code is the primary auditor and performs the line-by-line review; Claude Cowork performs a lightweight spec-alignment pass; Trevor verifies last.
- Codex's Self-audit attestations are subject to spot-check by Claude Code; false attestation is a ship-blocking failure and is recorded with signature in `todo.md` `Audit Record Log`.

## Completion Authority

- **Codex may:** create a Linear issue if none exists, create or reuse a task branch for file-edit work, append `todo.md` `Work Record Log` and `Completed` with the landing reference, update `todo.md` `Linear Issue Ledger` and `Active Branch Ledger` when a live issue or branch state changes, post completion or branch-lifecycle comments on the Linear issue, and commit and push on the task branch. Completion evidence must stay issue-scoped: `Completed`, `led to:`, and the Linear completion comment cite only the commit(s) or artifacts whose primary outcome belongs to that issue. Later audit-only or correction commits for a different issue are logged on the correcting issue instead of being appended to the earlier issue's closeout. Prompts, findings, and fix instructions from Cowork, Claude Code, or any other AI are advisory until Codex checks them against repo truth, current artifacts, and task scope. Before acting on a material outside-AI instruction, Codex classifies it as `accepted`, `narrowed`, `rejected`, or `needs more evidence`; unsupported claims are not executed by default, and material disagreement is recorded in the durable task trail instead of being silently ignored. `Pre-commit gates:` `Continuity Check` (Work Record entry exists and Self-audit is non-hollow), `Ripple Check` (every affected live doc was checked and any drift was updated in the same commit, then attested in Self-audit), and `Linear-coverage` (every surfaced follow-up is filed as a `GIL-N` issue or dispositioned in the log entry, and every live issue has a ledger entry with provenance).
- **Codex may not:** move Linear state, check off any checklist item in the Linear issue body, mark a task `Done`, or edit other agents' audit writeups.
- **Claude Code may:** perform the primary line-by-line audit, check off audit checklist items in the Linear issue body once its review is clean, write targeted fix code when appropriate, post audit findings as Linear comments, and append audit entries to `todo.md` `Audit Record Log` and `Test Evidence Log`. `Pre-audit-clean gates:` `Continuity Check` (an audit-variant Work Record exists and at least one Codex Self-audit claim was spot-checked), `Ripple Check` (Codex's diff was checked for missing dependent updates), and `Linear-coverage` (any finding Code surfaces is filed as a `GIL-N` issue or dispositioned in the durable record, and every live issue referenced in the audit has a current ledger entry).
- **Claude Code may not:** move Linear state, mark a task `Done`, or sign off on code it authored itself — an independent auditor (second Code session, Cowork, or Trevor) must clear Code-authored changes.
- **Cowork may:** move Linear state through `Building -> AI Audit -> Human Verify`, draft sub-issues for repair loops, manage `todo.md` `Active Next Steps` state and `Linear Issue Ledger`, perform the lightweight spec-alignment pass after Code's audit is clean, and check off the spec-alignment checklist item. `Pre-state-move gates:` `Continuity Check` (required Work Record exists on disk), `Ripple Check` (attestation exists and no dependent doc was missed), and `Linear-coverage` (the task has no un-Linearized actionable follow-up and every live issue involved still has a current ledger entry with provenance). For Cowork's own direct edits, the minimum is a light Work Record (`Problem`, `Reasoning`, `Change`, `Self-audit`) plus Ripple Check plus Linear-coverage. Cowork does not perform the line-by-line review that is Code's role.
- **Trevor may:** move an issue to `Done`, override any of the above, and resolve disagreements.

## Linear Workflow

- Every bounded task must have a Linear issue in team `GIL` before Codex begins work.
- If Cowork provides an existing `GIL-N` issue for the task, reference that issue before starting work.
- If no issue exists yet, Codex creates one before starting work using the `Standard issue` template defined in `LINEAR.md`, with the task title and initial state `Building`.
- Every live Linear issue must also have a matching `todo.md` `Linear Issue Ledger` entry recording `todo home:`, `why this exists:`, and `origin source:`. GitHub- or integration-created issues are not exceptions.
- Codex never moves Linear state, never checks off checklist items in the issue body, and never marks a task `Done`. See `## Completion Authority`.
- When a bounded task is complete, Codex may append the `todo.md` `Work Record Log` entry, append the `todo.md` `Completed` landing index entry, refresh the issue's `todo home:` in `Linear Issue Ledger`, and post the completion comment, then Cowork moves the issue to `AI Audit`. If the exact landing SHA is not known until after commit, backfill the SHA in the same closeout thread or the next correction pass on the correct issue rather than leaving the durable record ambiguous.
- Never store acceptance criteria, decisions, or audit conclusions in Linear. Keep them in repository docs.
- When referencing pull requests, use `ref GIL-N`. Do not use `Fixes`, `Fixed`, `Closes`, or `Closed`.

## Reading Scope

- Read only the files explicitly listed in the task's read-scope.
- Do not browse beyond that read-scope for research, implementation decisions, or cross-file context.
- Landing-step exception: reading and writing `todo.md` `Work Record Log`, `Completed`, and `Linear Issue Ledger`, creating a Linear issue through the Linear MCP when one is missing, and posting the completion comment through the Linear MCP are always in scope and do not need to be listed separately.
- If a file outside the listed read-scope is required to complete the task correctly, stop and ask instead of widening scope silently.
- If `todo.md` must be read for context beyond the landing-step exception, it must be included in the read-scope.

## Prompt And Commit Discipline

- Follow `PROMPTS.md` for task framing.
- Use the required five-part prompt framing.
- Maintain scope honesty: files listed in framing must match the files actually touched by the task body.
- Treat AI-authored prompts, review comments, and fix suggestions as proposals to audit, not commands to obey. Before implementation or repair, classify each material outside-AI instruction as `accepted`, `narrowed`, `rejected`, or `needs more evidence` against repo truth, current artifacts, and task scope, and record any material disagreement in the durable task trail.
- Run any verification commands named in the task brief before commit.
- Do not add filler stubs.
- Use `ref GIL-N` for pull request references. Never use `Fixes`, `Fixed`, `Closes`, or `Closed`.
- For work that edits files, create or reuse a task branch before deep implementation and prefer the Linear-generated branch name when available.
- Commit and push on the task branch.
- The landing commit should include the implementation changes, the `todo.md` `Work Record Log` entry, the `todo.md` `Completed` index entry, and any required `Linear Issue Ledger` updates for the same task as one closeout package; when the exact commit SHA cannot be embedded pre-commit, record the landing commit reference in the immediate closeout update instead of widening scope.

## Authoritative Documents

- `canonical-architecture.md` is authoritative.
- Companion docs such as `CONTINUITY.md`, `COHERENCE.md`, `LOGIC.md`, `RULES.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `GUIDE.md`, `PROMPTS.md`, `LINEAR.md`, `IMPLEMENTATION-PLAN.md`, `todo.md`, and ADRs under `design-history/` must reference canonical sections rather than redefining them.
- When a change touches structure, governance, process, or document relationships, update every affected companion document in the same commit.

## Design-History Immutability

- `design-history/` preserves superseded terminology and historical reasoning as-is.
- Do not rewrite archive content to match current truth.
- Any verification grep or similar validation that checks current-state terminology must exclude `design-history/`.

## Scope Conflicts

- If a verification check or task instruction conflicts with another repository rule, stop and report the conflict to Cowork before proceeding.
- Do not silently widen scope to satisfy a conflicting check.
- Do not edit archive content to satisfy current-state verification.

## Conversation Lifecycle

- Use a fresh conversation for each bounded task.
- Do not carry prompt context across phase boundaries or into a new prompt.
- Required new conversation: every new prompt or punch list, every phase boundary, every audit-triggered repair round as a new bounded task, every ADR that changes an operating decision, and whenever Codex begins hallucinating or contradicting repo truth.
- Permitted same conversation: mid-task repair within one bounded task before the commit lands, active debugging of a single issue with ongoing context, and multi-commit work whose sub-commits are dependent pieces of the same bounded task.
- Repair loops may continue within the same task through round 2.
- If a task reaches round 3, restart with the latest auditor findings as the new brief.
- Never let one conversation silently span two prompts that should be separate bounded tasks.

## Repo Principles
[MANDATORY_CONTINUITY] load and enforce local `CONTINUITY.md`; bounded tasks must leave a durable Work Record, honest Self-audit, and explicit `did not verify X because Y` note, and the audit path must permit Claude Code to spot-check at least one claim
[MANDATORY_COHERENCE] load and enforce local `COHERENCE.md`; governed changes require a Ripple Check, same-commit companion-doc updates, and an append-only Dependency Map
[MANDATORY_LINEAR_CORE] load and enforce the local Linear-Core contract; actionable work must have a live Linear issue or an explicit `no-action:` / `self-contained:` disposition, and every live issue must keep a repo-side `Linear Issue Ledger` entry with `todo home:`, `why this exists:`, and `origin source:`
[MANDATORY_CLAUDE_PRINCIPLES] repo-local `CLAUDE.md` must load the same three principles before planning, audit, or state moves, and Claude handoffs must name the durable-record expectations for Codex

- Load `CONTINUITY.md`, `COHERENCE.md`, and the local Linear contract before bounded work.
- Continuity gate: Work Record exists, Self-audit is honest, and unverified scope is named explicitly.
- Coherence gate: Ripple Check runs before commit or state move, and dependent docs drift together or not at all.
- Linear-Core gate: actionable work is issue-backed or explicitly dispositioned, and the repo-side ledger stays current.

## Claude Cowork Purpose (merged from CLAUDE.md)

`CLAUDE.md` in this repo is project-level operating guidance for Claude (Cowork orchestrator), loaded into every conversation so the operating model stays in the loop without Trevor restating it. `canonical-architecture.md` remains the repo's source of truth; `CLAUDE.md` is operating guidance, not spec.

## Roles (extended — merged from CLAUDE.md)

- **Claude Cowork (Orchestrator)** — primary orchestrator. Plan, decompose, draft Codex prompts, manage Linear state, edit governance/organization docs directly, route work, and resolve sequencing. Auditing is not Cowork's primary job; Cowork may perform a lightweight spec-alignment pass but is not the primary auditor and does not sit on the default audit gate. Cowork enforces all three repo principles before state moves — Continuity Check (Work Record exists), Ripple Check (no drift), and Linear-coverage (no un-Linearized follow-ups, no live issue missing from `todo.md` `Linear Issue Ledger`, and no missing provenance).
- **Claude Code** — **primary auditor** for this repo. Thoroughly reviews every line of code and every fix Codex (or anyone else) produces: diffs, schemas, tests, invariants, cross-doc consistency, and architectural adherence. Runs per task, per fix, and at phase exits. Claude Code may also write code when doing so is the cleanest way to land an audit-surfaced fix, to unblock Codex on a narrow targeted change, or to close a small mechanical gap uncovered during review. Self-audit is never the sole gate, so any code Claude Code authors still passes through either a Cowork spec check plus Trevor verify, or a second independent Code session.
- **ChatGPT Pro** — strategic/governance auditor. Gates phase exits and quarterly reviews per ADR-0004. Scope is phase-intent alignment, scope creep, and governance drift; Pro does not replace Code's line-level review.
- **Codex** — primary implementor. Self-audits, but self-audit is never the gate.

### Default Audit Chain

Cowork drafts prompt → Trevor approves → Codex implements (Claude Code may co-implement narrow fixes) → **Code audits line-by-line** (diff, tests, invariants, cross-doc) → Cowork performs a lightweight spec-alignment check → Trevor verifies. Phase exits add Pro between Code and Trevor. Repair loops cap at 3 rounds per Codex conversation. Disagreements go to Trevor. When Claude Code authors code as part of a fix, that change still passes through an independent audit — a second Code session or Cowork's spec check plus Trevor's verify.

## Linear — Additional Detail (merged from CLAUDE.md)

- State flow ownership: manual transitions are Cowork-owned, queue claim/exit transitions are supervisor-owned, and Codex never moves state: `Inbox → Ready for Build → Building` (prompt handed to Trevor) `→ AI Audit` (Codex reports done; Claude Code audits line-by-line) `→ Human Verify` (Code audit clean + Cowork spec-alignment check) `→ Done` (Trevor only).
- Every `todo.md` `Active Next Steps` item also has a matching Linear issue, annotated inline as `(GIL-N)`. Adding an item without its Linear issue ID or leaving a live issue without a ledger entry violates the coverage invariant (see `LINEAR.md` § Coverage Invariant).
- <!-- merged from CLAUDE.md --> Other `todo.md` sections are records, not task queues, but any entry that implies future work must still carry a resolved `linear:` disposition per `LINEAR.md` `## Linear-at-the-core` (this repo's Repo Principles section above states the disposition as `no-action:` / `self-contained:` — both phrasings describe the same coverage requirement; treat them as equivalent).
- Queue mode is supervisor-owned. The Codex queue only consumes issues with `Execution lane: Codex` and `Execution mode: Queue` per `QUEUE-RUNS.md`. Claude-owned audit or deeper test issues must be filed separately with `Execution lane: Claude Code` and `Execution mode: Manual`; Codex and the queue runner skip them and continue.
- For adding Linear to a new project, use `LINEAR-BOOTSTRAP.md`.

## Codex Handoff — Additional Detail (merged from CLAUDE.md)

- Prompts follow `PROMPTS.md`'s five-part header: `Goal`, `Discipline`, `Read-scope`, `Body`, `Durable record`.
- The `Durable record` section names every log entry expected, every Linear issue created or refreshed, every `Linear Issue Ledger` or `Active Branch Ledger` update required, and the Ripple Check attestation the Self-audit must contain.
- Fresh Codex conversation per bounded task per `ADR-0005`; if repair loops reach round 3, restart with the latest auditor findings as the new brief, and never reuse the same Codex conversation across a phase boundary.
- Manual prompts are drafted in the scoping Linear issue's description under the `prompt-review` label, reviewed by Codex and Claude Code via Linear comments, and revised by Cowork before handoff.
- Queue-mode prompts are rendered from the versioned template in `QUEUE-RUNS.md`.
- See `LINEAR.md` `## Prompt Drafting Surface`.

## Orchestrator Scope (merged from CLAUDE.md)

- Claude Cowork may edit directly: `todo.md`, Linear state, `CLAUDE.md`, and light organization moves.
- Substantive edits go to Codex via a prompt: `canonical-architecture.md`, schemas, `LOGIC.md`, `RULES.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `PROMPTS.md`, `LINEAR.md`, `AGENTS.project.md`, ADRs, `IMPLEMENTATION-PLAN.md`.

## Authoritative Docs — Addendum (merged from CLAUDE.md)

The full authoritative-doc set per `CLAUDE.md` also names `QUEUE-RUNS.md`, `AGENTS.md` (bootstrap pointer), and `AGENTS.project.md` (repo-local overlay) alongside the set already listed above in `## Authoritative Documents`.

## Global Mandatory Markers
- [MANDATORY_STACK_RUNTIME] stack/runtime profile, risk areas, release gates, boundaries, rollback/ops checks
- [MANDATORY_OPERATING_PRINCIPLES] operating principles aligned to `OPERATING_PRINCIPLES.md`
- [MANDATORY_PROJECT_INTENT] canonical project intent documentation + behavior aligned to `PROJECT_INTENT_ALIGNMENT.md`
- [MANDATORY_TODO_ADD] add follow-up work to project `todo.md`
- [MANDATORY_TODO_SUGGESTIONS] maintain a persistent `Suggested Recommendation Log` in `todo.md`; record every materially new suggested action there, avoid duplicate entries by reusing matching items, keep history instead of deleting entries, and check items off when completed
- [MANDATORY_TODO_CHECKOFF] auto-check completed verified `todo.md` items
- [MANDATORY_PLAN_TRACKING] capture durable chat-created plans in `todo.md` by recording the overall goal plus concrete steps, then mark them complete in the same file/log when verified
- [MANDATORY_FEEDBACK_DECISIONS] maintain a durable `Feedback Decision Log` in root `todo.md`; record outside feedback, the reasoning response, final decision, and any linked implementation/audit/test evidence there; update existing entries instead of duplicating the same feedback thread
- [MANDATORY_TESTING_GOVERNANCE] testing is required delivery evidence; keep `Test Evidence Convention`, `Test Evidence Log`, and `Testing Cadence Matrix` in root `todo.md`, and document what ran or what remains untested
- [MANDATORY_BRANCH_LIFECYCLE] maintain `Active Branch Ledger` and `Branch History` in root `todo.md`; every non-trivial branch must record purpose, responsible/source chat, last refreshed by chat, linked issue, plugin mirror status, merge expectation, exit checklist, delete-vs-retain outcome, retain reason when applicable, and delete/cleanup trigger
- [MANDATORY_WORKTREE] one-worktree-per-chat rule for concurrent chats in same repo
- [MANDATORY_PRAGMATIC] pragmatic improvement mindset
- [MANDATORY_FULL_AUDIT] full-audit behavior aligned to `FULL_AUDIT.md`
- [MANDATORY_NEXT_STEPS] next-steps behavior aligned to `NEXT_STEPS_ORCHESTRATION.md`, including `todo.md`-grounded and independently inferred recommendations; when the user explicitly asks for reasoning/model guidance or autonomous planning, include recommended reasoning levels without defaulting the first chat to `extra high`; when an audit or the current chat creates or discovers more urgent execution-ready work, persist and move those items to the top of `Active Next Steps` and reserve `Suggested Recommendation Log` for deferred, optional, or not-yet-execution-ready items; if none remain, explicitly state `No further steps required.`
- [MANDATORY_CLARIFY] ask focused clarifying question(s), explain the conflict/misalignment, and pause risky changes until clarified
- [MANDATORY_CREDIT_IMPACT] prioritize correctness/reliability and flag significant low-upside credit waste with efficient reliable alternatives
- [MANDATORY_NO_COMMIT_BLOCK] verification commands provide evidence and do not block commits/pushes unless the user explicitly requests strict gates
- [MANDATORY_NO_APPROVAL_PROMPTS] execute requested actions end-to-end without repeated approval prompts; ask only when blocked by platform constraints or missing requirements
- [MANDATORY_IGNORE_UNRELATED_CHANGES] treat unrelated tracked edits as valid concurrent work; do not block execution/cleanup, and never revert them unless explicitly requested
- [MANDATORY_COMMIT_OWN_CHANGES] commit every file edited in the current task before completion unless the user explicitly says not to; never let unrelated dirty state prevent committing task files
- [MANDATORY_AUTO_PUSH] after edits in a git repository, automatically commit and push every task-touched file that remains changed unless the user explicitly says not to push; if push fails, stop and report the exact failing command/output
- [MANDATORY_TASK_CLASSIFICATION] classify task tier per `TASK_CLASSIFICATION.md`; match verification depth and playbook loading to tier
- [MANDATORY_TRUST_GATE] evaluate Trust Gate triggers at session intake per `session-intake-closeout` skill; when `on`, require `Evidence Checked`, `Decision Status` labels (`Confirmed` / `Inferred` / `Needs More Evidence` / `Do Not Do Yet`), `Challenge Findings`, and `Unresolved` sections at closeout; no polished final recommendation for uncertain items
- [MANDATORY_ANTI_THRASH] after 2 grounded attempts at the same problem, narrow scope, request the smallest missing artifact, or escalate; do not retry unchanged approach

## Coder Craft Evidence Gate

- For meaningful AI-assisted implementation, debugging, code review, unfamiliar API/citation work, or AI-only-operator handoffs, load `/Users/gillettes/.codex/policies/CODER_CRAFT_FORCING_FUNCTIONS.md` and scale the evidence to blast radius.
