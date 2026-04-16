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

- Codex is the primary implementor for this repository.
- Codex writes code, modifies doc content, lands commits, and performs a self-audit.
- Claude Code may also write code when doing so is the cleanest way to land an audit-surfaced fix, unblock Codex on a narrow targeted change, or close a small mechanical gap uncovered during line-by-line review. When Code writes code, it is still subject to independent audit — Code never ships its own code as the sole reviewer of record.
- Self-audit is never the ship gate. Claude Code is the primary auditor and performs the line-by-line review; Claude Cowork performs a lightweight spec-alignment pass; Trevor verifies last.

## Completion Authority

- **Codex may:** create a Linear issue if none exists, append `todo.md` `Completed` with the landing commit reference, post a completion comment on the Linear issue, and commit and push on the current branch.
- **Codex may not:** move Linear state, check off any checklist item in the Linear issue body, mark a task `Done`, or edit other agents' audit writeups.
- **Claude Code may:** perform the primary line-by-line audit, check off audit checklist items in the Linear issue body once its review is clean, write targeted fix code when appropriate, post audit findings as Linear comments, and append audit entries to `todo.md` `Audit Record Log` and `Test Evidence Log`.
- **Claude Code may not:** move Linear state, mark a task `Done`, or sign off on code it authored itself — an independent auditor (second Code session, Cowork, or Trevor) must clear Code-authored changes.
- **Cowork may:** move Linear state through `Building -> AI Audit -> Human Verify`, draft sub-issues for repair loops, manage `todo.md` `Active Next Steps` state, perform the lightweight spec-alignment pass after Code's audit is clean, and check off the spec-alignment checklist item. Cowork does not perform the line-by-line review that is Code's role.
- **Trevor may:** move an issue to `Done`, override any of the above, and resolve disagreements.

## Linear Workflow

- Every bounded task must have a Linear issue in team `GIL` before Codex begins work.
- If Cowork provides an existing `GIL-N` issue for the task, reference that issue before starting work.
- If no issue exists yet, Codex creates one before starting work using the `Standard issue` template defined in `LINEAR.md`, with the task title and initial state `Building`.
- Codex never moves Linear state, never checks off checklist items in the issue body, and never marks a task `Done`. See `## Completion Authority`.
- When a bounded task is complete, Codex may append the `todo.md` `Completed` landing entry and post the completion comment, then Cowork moves the issue to `AI Audit`.
- Never store acceptance criteria, decisions, or audit conclusions in Linear. Keep them in repository docs.
- When referencing pull requests, use `ref GIL-N`. Do not use `Fixes`, `Fixed`, `Closes`, or `Closed`.

## Reading Scope

- Read only the files explicitly listed in the task's read-scope.
- Do not browse beyond that read-scope for research, implementation decisions, or cross-file context.
- Landing-step exception: reading and writing `todo.md` `Completed`, creating a Linear issue through the Linear MCP when one is missing, and posting the completion comment through the Linear MCP are always in scope and do not need to be listed separately.
- If a file outside the listed read-scope is required to complete the task correctly, stop and ask instead of widening scope silently.
- If `todo.md` must be read for context beyond the landing-step exception, it must be included in the read-scope.

## Prompt And Commit Discipline

- Follow `PROMPTS.md` for task framing.
- Use the required four-part prompt framing.
- Maintain scope honesty: files listed in framing must match the files actually touched by the task body.
- Run any verification commands named in the task brief before commit.
- Do not add filler stubs.
- Use `ref GIL-N` for pull request references. Never use `Fixes`, `Fixed`, `Closes`, or `Closed`.
- Commit and push on the current branch.
- Never create a branch for repo work in this repository.
- The landing commit should include the implementation changes and the `todo.md` `Completed` entry for the same task as one closeout package; when the exact commit SHA cannot be embedded pre-commit, record the landing commit reference in the immediate closeout update instead of widening scope.

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
