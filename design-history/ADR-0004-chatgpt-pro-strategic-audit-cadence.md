# ADR-0004: ChatGPT Pro Strategic Audit Cadence

**Date:** 2026-04-20
**Status:** Accepted
**Issue:** `GIL-10`

## Context

By 2026-04-15, the repo had already converged on a multi-actor quality model:

- Codex implements
- Claude Code performs the primary line-by-line audit
- Claude Cowork orchestrates, sequences work, and performs a lightweight
  spec-alignment pass
- Trevor remains the final human verifier

What was still missing was a durable answer to a different question: when and
how should ChatGPT Pro be used?

Pro had already proved useful as a strategic counterweight in planning and
audit-reconciliation threads. It surfaced repo-shape problems, governance
posture issues, and machine-checkable gaps that were easy for implementation-
proximate review loops to underweight. But without an explicit cadence, Pro
would remain an ad hoc extra opinion instead of a stable part of the operating
model.

The repo needed a bounded strategic-audit role that:

- catches phase-level drift without duplicating Claude Code's line-by-line work
- gives Trevor a recurring governance check instead of a one-off chat habit
- keeps audit ownership clear so "more auditors" does not become "blurred
  auditors"
- preserves the audit brief and output shape in repo truth rather than chat
  memory

## Decision

Adopt ChatGPT Pro as the recurring strategic/governance auditor with a fixed
cadence, fixed scope boundary, and fixed audit-brief shape.

### Cadence

Pro is engaged at these times:

1. **Every phase boundary** as a gate audit:
   - `0A`
   - `0B`
   - `0C`
   - `1`
   - `2`
   - `3`
   - `4`

2. **Phase 1 mid-build architecture checkpoint**, jointly with Claude Code,
   after subphase `1.2` lands and before `1.3` begins

3. **Quarterly whole-repo strategic review**

4. **Ad hoc on drift**, whenever Trevor explicitly requests it or when the
   orchestrator sees meaningful uncertainty about scope creep, architectural
   drift, governance posture, or whether the current phase is still solving the
   right problem

### Scope boundary

Pro's role is strategic and governance-focused. Pro is responsible for:

- phase-intent alignment against `PROJECT_INTENT.md`
- scope-creep detection
- governance-posture review
- architectural-drift review against the canonical design and active ADRs
- meta-checks on whether the current audit chain is missing the right class of
  question

Pro is **not** the primary verifier of executable detail. Pro does **not**
replace Claude Code for:

- schema correctness
- test-result validation
- `file:line` correctness
- diff-level implementation review
- deterministic gate reruns

That work remains Claude Code's primary line-by-line audit surface.

### Required audit brief

Each Pro audit uses an orchestrator-prepared brief. At minimum, the brief
includes:

- `PROJECT_INTENT.md`
- `canonical-architecture.md`
- relevant ADRs
- commit-range fingerprint
- the relevant tail of `todo.md` `Audit Record Log`
- the relevant tail of `todo.md` `Feedback Decision Log`

The brief exists because strategic audit quality depends on the current repo
state and decision trail, and Pro may not always have a clean live read of the
entire workspace.

### Required output shape

Each Pro audit returns:

- `GREEN`, `YELLOW`, or `RED` for each scoped review line
- `P1`, `P2`, and `P3` findings where applicable
- a punch list
- an explicit `not checked` list

This output is recorded in the repo's durable audit trail rather than treated
as a chat-only opinion.

### Disagreement handling

If Pro and Claude Code disagree materially on a finding, gate decision, or
required repair, the escalation path is `ADR-0002`.

That means:

1. the disagreeing auditor restates the finding with concrete evidence
2. Codex (or the relevant implementor) restates the counter-position with
   evidence or explicit uncertainty
3. Trevor arbitrates if the disagreement remains substantive

## Consequences

### Accepted

- Pro now has a durable, bounded role in the repo rather than an informal
  "extra opinion" role.
- Phase exits gain a strategic/governance check without overloading the
  line-level audit lane.
- The repo's audit chain stays differentiated:
  - Codex implements
  - Claude Code audits line-by-line
  - Cowork orchestrates and checks spec alignment
  - Pro audits strategic/governance fit
  - Trevor arbitrates and verifies
- Future sessions can tell when Pro should be used without reconstructing the
  cadence from old chat logs.

### Rejected

- Using Pro as another line-by-line code reviewer
- Running Pro only when someone remembers
- Letting Pro and Claude Code silently overlap on schema/test/`file:line`
  validation
- Treating strategic audits as authoritative if their brief, scope, and
  `not checked` list are not explicit

## Follow-on

This ADR makes `GIL-11` more important, not less. If Codex conversation
lifecycle is still loose, phase-boundary and repair-round audit discipline will
drift even with the right Pro cadence. `GIL-11` remains the next queued
governance lane after this landing.
