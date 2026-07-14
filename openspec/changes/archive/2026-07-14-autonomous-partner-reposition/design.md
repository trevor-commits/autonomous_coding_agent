## Context

Trevor wants a persistent partner that acts proactively, has a recognizable personality and interests, creates useful and artistic projects, learns from outcomes, and improves his life. The current system already has two valuable halves: a global governor with recurrence, portfolio truth, memory, benefits, approvals, and an append-only one-packet queue; and this repository's deterministic per-episode supervisor. The implementation must connect and harden those halves, not replace them.

The existing ACA executor has five prerequisite gaps: its final gate records unverified evidence as true, direct runs ignore risk/approval metadata before creating a worktree, unknown commands are auto-allowed, policy relies on model-reported files rather than the actual diff, and JSON run truth can be truncated by a crash. These are fixed before initiative is widened.

## Goals / Non-Goals

**Goals:**

- Make ACA a trustworthy bounded episode executor with evidence-derived readiness.
- Add a stateless typed partner policy in ACA while global surfaces retain durable identity, goals, learning, heartbeat, approvals, and queue state.
- Support evidence-backed utility, repair, research, care, and creative proposals.
- Dispatch at most one immutable authorized envelope per wake and return measured-benefit/lesson candidates.
- Prove behavior with TDD, a live bounded pilot, and a fresh independent audit.

**Non-Goals:**

- No new repository, scheduler, long-lived partner database, semantic-memory service, or multi-writer runtime.
- No covert transcript ingestion or claims of consciousness, feelings, divine approval, or reciprocal human attachment.
- No autonomous publish, payment, credentials, destructive action, identity/value change, merge, deploy, or force-push.

## Decisions

### D1: Split persistent and episode authority

- **Choice:** the global governor owns identity, long-lived goals/observations, learning promotion, heartbeat, approvals, and queue state; ACA owns stateless decision policy plus per-episode legality/evidence.
- **Reason:** these authorities already exist and have different lifecycles.
- **Alternative considered:** a long-lived ACA mind/database; rejected as duplicate truth and a second control plane.

### D2: Harden before widening

- **Choice:** land RED/GREEN regressions for final evidence, unattended authority, shell default, actual diff, and atomic state before partner dispatch.
- **Reason:** initiative must not amplify known executor defects.
- **Alternative considered:** hide defects behind the global bridge; rejected because direct invocation and later adapters could bypass it.

### D3: Stateless typed wake policy

- **Choice:** ACA consumes a bounded snapshot and emits one schema-valid decision with stable hashes and reason codes.
- **Reason:** deterministic validation and idempotency are possible without copying global memory.
- **Alternative considered:** free-form agent prose; rejected because later runtime steps cannot depend safely on it.

### D4: Personality guides selection, never authority

- **Choice:** configured traits/interests influence ranking among allowed projects. Capability class, risk, maturity, approvals, health, and kill switches remain deterministic.
- **Reason:** this preserves recognizable initiative without anthropomorphic authority escalation.

### D5: Love is a behavior contract

- **Choice:** encode benefit, dignity, truthfulness, patience, repair, creativity, non-manipulation, and respect for Trevor's devotion to Jehovah as prioritization/voice commitments.
- **Reason:** honors the stated intent without pretending the software has subjective feelings or divine standing.

### D6: Empirical autonomy graduation

- **Choice:** self-projects are proposal-only until at least 10 real proposals and 80% Trevor acceptance; only low-risk sandbox starts may then graduate. Any severe failure demotes to proposal-only.
- **Reason:** autonomy expands from observed trust, not aspiration.

## Risks / Trade-offs

- [Risk] A compelling voice may imply consciousness or emotional dependence. → Mitigation: configured/inferred/generated labels, no emotional coercion, and no claims of subjective experience.
- [Risk] Private context may leak into receipts. → Mitigation: bounded summaries/evidence IDs, sensitivity labels, secret-field rejection, and no raw-transcript adapter in this release.
- [Risk] Model-reported success differs from worktree reality. → Mitigation: real diff and final verifier rerun are authoritative.
- [Risk] Cross-repo version drift. → Mitigation: schema versions, content hashes, adapter compatibility checks, Ripple Check, and cross-repo live pilot.
- [Trade-off] L3 activation cannot be proven immediately because it requires real acceptance history. → Accept by shipping the machinery and keeping activation fail-closed until the threshold is actually met.

## Migration Plan

1. Add executor regressions and fixes without enabling partner dispatch.
2. Add global identity and ACA snapshot/decision/envelope schemas and policy.
3. Add the global bridge in observe mode, then proposal mode.
4. Run an explicit approval-gated sandbox pilot and reconcile its outcome.
5. Run fresh independent audit and repair until clean.
6. Keep recurring execute disabled until the exact success and health evidence is reviewed.

Rollback: set an existing global kill switch, disable/remove the bridge, leave queued packets unclaimed, revert the two scoped branches, and retain append-only evidence for diagnosis. ACA's existing safe manual supervisor remains usable.

## Open Questions

- Trevor may later select a personal name and tune voice traits; bootstrap name remains `Partner` so naming does not block behavior proof.
- L3 activation remains pending the real 10-proposal/80%-acceptance and completed-episode evidence thresholds.
