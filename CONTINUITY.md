# Continuity

**Date:** April 16, 2026  
**Authority:** Repo governance derived from `AGENTS.project.md`, `RULES.md`, and `LINEAR.md`.
**Purpose:** Define the continuity principle for this repository so bounded work leaves a durable, findable record instead of dying with the conversation that produced it.

## Principle

"Your conversation is temporary, the repo is permanent." Nothing survives a session boundary unless it is written into the repo, signed by the responsible agent, and pointed to from a stable home that future readers can find without replaying the chat.

## What counts as written and findable

A fact is durable only when all three are true:

- It has a file-home in the repo or an explicitly allowed companion surface such as `todo.md` or `~/.claude/CLAUDE.md`.
- It is signed by the actor who is claiming the work through a named field such as `by:` or an explicit audit attribution.
- It is pointed-to from an index, guide, issue, or section that future readers already know to check.

Work that is merely implied by a diff, described in a chat, or left in a tool comment without a stable repo pointer is not continuity. It is recoverable only by luck.

## What dies if not recorded

If it is not written, assume it is gone. That includes rejected alternatives, abandoned paths, surprise findings, Codex output that was discarded and why, audit conclusions that did not turn into an issue, research detours, things tried and failed, and any future work that surfaced during implementation but never made it into a durable record.

## Pre-exit reflex

Before ending a turn or landing a commit, ask:

1. What did I learn, decide, reject, or confirm that is not yet in the repo?
2. What ripples did my changes create that still need to be reconciled under `COHERENCE.md`?
3. What future work did I surface that is not yet a `GIL-N` issue or explicitly dispositioned under `LINEAR.md`?

If the answer to any of those questions is "something," the task is not closed yet.

## Work Record Format

Every bounded task, fix, or audit writes a Work Record in `todo.md`.

```text
Problem:
Reasoning:
Diagnosis inputs:
Implementation inputs:
Fix:
Self-audit:
by:
triggered by:
led to:
linear:
```

The six required narrative fields are `Problem`, `Reasoning`, `Diagnosis inputs`, `Implementation inputs`, `Fix`, and `Self-audit`. The attribution fields `by:`, `triggered by:`, `led to:`, and `linear:` make the entry findable and accountable instead of anonymous prose.

`led to:` is closeout evidence, not a narrative flourish. It names the actual commit(s), issue(s), artifact paths, or explicit `no-action:` outcomes produced by that task. Placeholder text is temporary only; once the real landing SHA or correction commit is known, the durable record is backfilled on the correct issue instead of being left to chat history.

## Self-audit honesty

Self-audit is method, not claim. Each check named in the record must say how it was verified, what was actually observed, and what remains unverified. Every Self-audit includes an explicit line in the form `did not verify X because Y` for anything skipped, blocked, or intentionally left out. Claude Code spot-checks at least one claim per audit. A hollow attestation is harder to clear than an admitted gap because it corrupts the record future work depends on.

## Motive

This is legacy-over-compliance. The goal is not to satisfy a checklist; it is to leave a trustworthy trail that still makes sense after the conversation is gone. Your name is on the line when you sign the attestation. A missed finding can be repaired. A false or empty attestation poisons the repo's memory and makes every later audit more expensive.

## Applies to

| Actor | Required form | What it must capture |
|---|---|---|
| Codex | Full six-field Work Record | Problem, reasoning, diagnosis inputs, implementation inputs, fix, Self-audit, plus `by:`, `triggered by:`, `led to:`, and `linear:` |
| Claude Code | Full form with audit variant | Same structure, but `Audit method` may replace `Self-audit` when the record is strictly an audit artifact |
| Cowork | Light form | `Problem`, `Reasoning`, `Change`, `Self-audit`, plus the same attribution and `linear:` fields |

## Where the rules live

- `AGENTS.project.md` `## Completion Authority` defines who must satisfy the Continuity Check before a commit lands or a Linear state move happens.
- `PROMPTS.md` `## Prompt framing convention` defines the five-part prompt header that must name the durable record up front.
- `LINEAR.md` ties state-move preconditions to the existence of Work Record entries and Linear-coverage.
- `RULES.md` `R-CONT-01` through `R-CONT-05` make the principle enforceable.
