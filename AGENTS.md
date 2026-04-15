# AGENTS.md

## Purpose

Repo-local instructions for agents working in this repository.

## Source Of Truth

The canonical architecture for this project lives in:

- `canonical-architecture.md`

If another document conflicts with it, follow `canonical-architecture.md`.

The design-history narrative lives in:

- `design-history/canonical-architecture-synthesis.md`

Older architecture documents now live under `design-history/` and are historical context only unless explicitly referenced for a specific comparison task.

## What This Repository Is

This repository currently holds architecture, planning, and source-of-truth documentation for an autonomous coding system.

For quick file lookup, use `REPO_MAP.md`. For reading order, use `GUIDE.md`.

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

## Global Mandatory Markers
The policy and playbook filenames referenced below are global Codex resources, not repo-local files. Resolve them under `/Users/gillettes/.codex/` and `/Users/gillettes/.codex/policies/` unless a specific instruction says otherwise. Do not assume they exist inside this repository.

- [MANDATORY_STACK_RUNTIME] stack/runtime profile, risk areas, release gates, boundaries, rollback/ops checks
- [MANDATORY_OPERATING_PRINCIPLES] operating principles aligned to `OPERATING_PRINCIPLES.md`
- [MANDATORY_PROJECT_INTENT] canonical project intent documentation + behavior aligned to `PROJECT_INTENT_ALIGNMENT.md`
- [MANDATORY_TODO_ADD] add follow-up work to project `todo.md`
- [MANDATORY_TODO_SUGGESTIONS] maintain a persistent `Suggested Recommendation Log` in `todo.md`; record every materially new suggested action there, avoid duplicate entries by reusing matching items, keep history instead of deleting entries, and check items off when completed
- [MANDATORY_TODO_CHECKOFF] auto-check completed verified `todo.md` items
- [MANDATORY_PLAN_TRACKING] capture durable chat-created plans in `todo.md` by recording the overall goal plus concrete steps, then mark them complete in the same file/log when verified
- [MANDATORY_FEEDBACK_DECISIONS] maintain a durable `Feedback Decision Log` in root `todo.md`; record outside feedback, the reasoning response, final decision, and any linked implementation/audit/test evidence there; update existing entries instead of duplicating the same feedback thread
- [MANDATORY_TESTING_GOVERNANCE] testing is required delivery evidence; keep `Test Evidence Convention`, `Test Evidence Log`, and `Testing Cadence Matrix` in root `todo.md`, and document what ran or what remains untested
- [MANDATORY_BRANCH_LIFECYCLE] maintain `Active Branch Ledger` and `Branch History` in root `todo.md`; every non-trivial branch must record purpose, responsible/source chat, last refreshed by chat, merge expectation, exit checklist, delete-vs-retain outcome, retain reason when applicable, and delete/cleanup trigger
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
