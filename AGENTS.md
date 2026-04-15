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

- Use `PROJECT_INTENT.md`, `canonical-architecture.md`, `RULES.md`, `STRUCTURE.md`, and `GUIDE.md` as the current truth set for purpose, architecture, constraints, placement, and navigation.
- Record active work, completed work, suggested ideas, audit records, test evidence, and feedback decisions in `todo.md` rather than leaving them only in chat.
- Keep verification evidence in `todo.md`'s `Test Evidence Log`, and keep the durable completion trail in `todo.md`'s `Completed` section.
- Keep the current-checkout bias unless the user explicitly asks for isolation or concurrent work makes a separate branch/worktree necessary.
- Ask focused clarifying questions when instructions conflict with the canonical architecture or the repo boundary; otherwise prefer direct execution over repeated approval prompts.
- Do not let unrelated tracked changes block your task. Do not revert them unless the user explicitly asks.
- Commit and push every task-touched file before finishing unless the user explicitly says not to.

## Implementor Role

- The agent is the sole implementor for this repository.
- The agent writes code, modifies doc content, lands commits, and performs a self-audit.
- Self-audit is never the ship gate. Claude Code and Claude Cowork audit after implementation, and Trevor verifies last.

## Completion Authority

- **Codex may:** create Linear issues, append `todo.md` `Completed` entries, commit and push on the current branch, and report completion to Cowork.
- **Only Cowork may:** move Linear issue state through `Building -> AI Audit -> Human Verify`, check off audit or review checklist items, and manage `todo.md` `Active Next Steps` state.
- **Only Trevor may:** move issues to `Done`, override any state, and grant final signoff.

## Linear Workflow

- Every task corresponds to a Linear issue in team `GIL`.
- If Cowork provides an existing `GIL-N` issue for the task, reference that issue before starting work.
- If no issue exists yet, Codex creates one before starting work using the `Standard issue` template defined in `LINEAR.md`, with the task title and initial state `Building`.
- Codex never moves Linear issue state after creation.
- When a bounded task is complete, report it as done so Cowork can move the issue to `AI Audit`.
- Codex never moves an issue to `Human Verify`, `Done`, or `Canceled`.
- Never store acceptance criteria, decisions, or audit conclusions in Linear. Keep them in repository docs.
- When referencing pull requests, use `ref GIL-N`. Do not use `Fixes`, `Fixed`, `Closes`, or `Closed`.

## Reading Scope

- Read only the files explicitly listed in the task's read-scope.
- Do not browse beyond that read-scope for research, implementation decisions, or cross-file context.
- Landing-step exception: appending to `todo.md` `Completed` and creating a Linear issue are always in scope and do not need to be listed separately.
- If a file outside the listed read-scope is required to complete the task correctly, stop and ask instead of widening scope silently.
- If `todo.md` must be read for context beyond appending the landing entry, it must be included in the read-scope.

## Prompt And Commit Discipline

- Follow `PROMPTS.md` for task framing.
- Use the required four-part prompt framing.
- Maintain scope honesty: files listed in framing must match the files actually touched by the task body.
- Do not add filler stubs.
- Commit and push on the current branch.
- Never create a branch for repo work in this repository.
- As a normal landing step, append a `todo.md` `Completed` entry and record the landing commit SHA when it is available as part of closeout.

## Authoritative Documents

- `canonical-architecture.md` is authoritative.
- Companion docs such as `LOGIC.md`, `RULES.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `GUIDE.md`, `PROMPTS.md`, `LINEAR.md`, `IMPLEMENTATION-PLAN.md`, `todo.md`, and ADRs under `design-history/` must reference canonical sections rather than redefining them.
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
- Repair loops may continue within the same task through round 2.
- If a task reaches round 3, restart with the latest auditor findings as the new brief.
