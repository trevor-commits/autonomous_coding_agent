# ADR-0002: Audit Tiebreaker Protocol

**Date:** 2026-04-20
**Status:** Accepted
**Issue:** `GIL-8`

## Context

The repo now depends heavily on multi-actor review loops:

- Codex implements
- Claude Code performs the primary line-by-line audit
- Claude Cowork runs the spec-alignment pass and orchestration
- Trevor remains the final human verifier
- ChatGPT Pro is queued as the strategic/governance auditor in later phases

That structure improves quality only if disagreement is handled cleanly. By
2026-04-15, the planning review had already identified a missing protocol:
what happens when Codex and an auditor disagree on whether a finding is real,
load-bearing, or actually fixed?

Without an explicit tiebreaker, the repo risks exactly the failure mode the
governance stack is supposed to prevent:

- findings bouncing between Codex and the auditor without closure
- repairs getting stalled by argument instead of evidence
- chat-only disagreement with no durable trail
- silent override of an auditor or implementor without a recorded decision

The repo needed a bounded escalation path that stays evidence-first and ends in
a human decision when the models cannot converge.

## Decision

Adopt the following audit tiebreaker protocol for unresolved substantive
disagreement between Codex and an auditor.

### Trigger

The protocol triggers when all of these are true:

1. an auditor claims a finding is real, unresolved, or insufficiently fixed
2. Codex disagrees materially
3. the disagreement would change whether the work should be repaired,
   re-audited, blocked, or allowed to proceed
4. repo truth and direct evidence do not resolve it immediately

This protocol is for substantive disagreements, not style preferences or
editorial suggestions.

### Required shape

The disagreement escalates in this order:

1. **Auditor restatement with concrete evidence**
   The auditor restates the finding using direct evidence such as:
   - `file:line`
   - command output
   - failing test name
   - artifact path
   - schema or rule citation

2. **Codex restatement with concrete counter-position**
   Codex responds with direct counter-evidence or a narrowed correction.
   If Codex is uncertain, it says so explicitly instead of bluffing.

3. **Trevor arbitration**
   If the disagreement still stands after the evidence restatement, Trevor
   decides. That decision is binding for the current task.

### Recording requirement

Every tiebreaker decision is written into `todo.md` `Feedback Decision Log`
with the tag `tiebreaker` and should include:

- the finding in dispute
- the auditor evidence
- Codex's counter-position
- Trevor's final decision
- the resulting implementation or no-action disposition

If the disagreement creates new work, that work gets a `GIL-N` issue or an
explicit `no-action:` / `self-contained:` disposition in the durable record.

### Hard rule

No finding may bounce between Codex and an auditor without human resolution
once the tiebreaker trigger is met.

The allowed outcomes are:

- Codex accepts the finding and repairs it
- the auditor withdraws or narrows the finding
- Trevor arbitrates and the repo records the decision

Repeated back-and-forth without one of those outcomes is a process failure.

## Consequences

### Accepted

- Audit disagreements now end in a bounded, durable process instead of open
  loops.
- Auditors must present concrete evidence, not just intuition.
- Codex must answer with evidence or explicit uncertainty, not rhetorical
  dismissal.
- Trevor's arbitration becomes part of repo memory rather than chat-only
  folklore.

### Rejected

- Letting Codex and the auditor keep contesting the same finding indefinitely
- Treating "the louder model wins" as an audit protocol
- Silently overriding an audit finding without writing down why

## Follow-on

This ADR is the foundation for later multi-auditor governance work, especially
`GIL-10` (ChatGPT Pro strategic audit cadence). When Pro and Claude Code
disagree materially on a finding or gate decision, this ADR is the escalation
path.
