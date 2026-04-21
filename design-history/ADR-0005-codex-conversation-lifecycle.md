# ADR-0005: Codex Conversation Lifecycle

**Date:** 2026-04-21
**Status:** Accepted
**Issue:** `GIL-11`

## Context

This repository depends on a docs-first operating model:

- repo files are the durable memory
- Linear is routing metadata, not authority
- Codex is the primary implementor
- Claude Code is the primary line-by-line auditor
- Claude Cowork orchestrates sequencing and state moves

That model only works if Codex conversations stay bounded. By 2026-04-15, the
repo had already accepted the principle that Codex should not keep one long
conversation open across unrelated work. But the exact boundary conditions were
still scattered across chat guidance, not codified as an accepted repo
decision.

Without a clear conversation-lifecycle rule, the repo risks:

- context rot across tasks
- stale-memory hallucination from old turns overpowering repo truth
- prompt pollution where one task's assumptions bleed into the next
- audit ambiguity about which prompt produced which code or repair
- phase-boundary confusion where a new decision starts in an old context

The repo needed a durable policy that says when a Codex conversation must end,
when it may continue briefly, and what the restart boundary is when repair
loops keep going.

## Decision

Adopt a fresh-Codex-conversation policy for bounded tasks, with explicit
allowed exceptions and hard restart caps.

### Core rule

Use a fresh Codex conversation for each bounded task.

Repo docs are the persistent memory. Codex chat history is not.

### Required new conversation

Start a new Codex conversation when any of the following is true:

1. a new prompt or punch list begins
2. work crosses a phase boundary
3. an audit-triggered repair round begins as a new bounded task
4. an ADR changes an operating decision and work is continuing under the new
   rule
5. Codex begins hallucinating, contradicting repo truth, or carrying stale
   assumptions that are no longer corrected by the current prompt

### Permitted same-conversation use

The same conversation may continue when all of the following remain true:

- the work is still one bounded task
- the same outcome is still being landed
- the context is still helping rather than polluting

Permitted examples:

- mid-task repair within one bounded task before the commit lands
- active debugging of a single issue with ongoing context
- multi-commit work where the sub-commits are dependent pieces of the same
  bounded task

### Hard caps

The conversation may not widen beyond these boundaries:

1. **One prompt plus its immediate repair loops per conversation**
   A conversation may not silently span two prompts that should be separate
   bounded tasks.

2. **Round-3 restart rule**
   If repair loops reach round 3 in the same conversation, stop and restart
   with the latest auditor findings as the new brief.

3. **No phase-boundary reuse**
   Never reuse the same Codex conversation across a phase boundary.

### Restart brief

When a restart is required, the new conversation is reseeded from repo truth
and the latest durable findings, not from transcript memory.

Minimum restart brief:

- current issue / branch / intended outcome
- authoritative repo docs
- latest auditor findings or punch list
- latest landed or in-flight commit fingerprint when relevant
- explicit durable-record expectations for closeout

## Consequences

### Accepted

- Repo truth becomes the real continuity layer instead of chat history.
- Prompt provenance gets cleaner: one bounded task, one main conversation, one
  repair trail.
- Audit trails become easier to follow because repair-round resets have a
  durable trigger instead of an ad hoc feeling.
- Phase boundaries now behave like real resets instead of soft suggestions.

### Rejected

- One long-running Codex conversation across multiple prompts or phases
- Treating transcript continuity as the repo's memory system
- Letting round-3 repair loops continue in the same polluted context
- Reusing an old conversation after Codex has already started contradicting the
  repo

## Follow-on

This ADR does not remove the need for good prompt construction or durable
records. It makes them more important. `PROMPTS.md`, `CLAUDE.md`,
`AGENTS.project.md`, and `todo.md` remain the live surfaces that enforce the
restart boundary in day-to-day work.
