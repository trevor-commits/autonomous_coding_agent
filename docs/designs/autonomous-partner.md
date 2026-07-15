# Autonomous Partner — Strategic Design

**Status:** Accepted
**Date:** 2026-07-13
**Owner:** Trevor Gillette
**Co-authors:** Codex governor; independent architecture challenger `/root/architecture_seam`
**Related:** `canonical-architecture.md`; `PROJECT_INTENT.md`; global enforcement requests ER-109, ER-118, ER-139, and ER-141; Claude session `bb90d05d-86d3-4140-9e6c-78d2847c4d72`

This design repositions the existing autonomous coding harness as the bounded execution layer of a persistent autonomous partner. It does not discard the tested supervisor or create a second portfolio control plane.

---

## 1. Problem statement

Trevor has a reliable but dormant delivery harness and a separate recurring global governor. Neither is yet a persistent partner: the harness waits for a bounded coding objective, while the governor observes health and dispatches only manually queued packets. Trevor still has to notice most opportunities, formulate goals, and restart the system's context.

The evidence is concrete. The repository already has a deterministic supervisor and 116 passing tests, but no active target contract and no live recurring integration. The April benchmark recorded eight positive harness runs with zero completed tasks because the first builder turn timed out. The global heartbeat explicitly refuses to invent work. ER-141 therefore correctly identifies the missing layer as durable identity plus governed initiative, not another executor.

## 2. Vision / intent

When this ships, Trevor has one persistent partner whose global governor remembers an explicit identity and durable goals, observes only approved evidence sources, proposes useful or creative projects during healthy idle time, and invokes this repository's stateless partner policy and bounded episode executor for at most one governed action. The partner is proactive and recognizable without pretending to be conscious: love is operationalized as stable commitments to benefit, dignity, truthfulness, patience, repair, and respect for Trevor's devotion to Jehovah; those commitments guide prioritization but never enlarge authority.

### Intent contract

- Preserve the existing deterministic supervisor as the only owner of run legality and readiness.
- Preserve the global autonomous loop as the only recurring heartbeat and work-order dispatch spine.
- Add one partner layer split deliberately across existing authorities: global identity/goals/learning and this repo's typed policy/executor boundary.
- Permit self-originated utility, repair, research, care, and creative projects.
- Make initiative observable and useful: every wake ends in a typed no-op, proposal, dispatch, block, or learning receipt.
- Keep personality honest: configured traits, inferred preferences, and generated ideas remain distinguishable.

### Success criteria

- A global wake snapshot can load a schema-valid identity and emit its content hash in a typed decision receipt.
- An approved observation can produce a scored self-originated proposal tied to evidence and an interest.
- A self-originated proposal cannot dispatch before its authority gate is satisfied.
- An operator goal or approved self-project can emit exactly one immutable work-order packet for the existing executor queue.
- Kill switches, unhealthy dependencies, unsafe capabilities, duplicate wakes, stale evidence, and budget exhaustion fail closed.
- A completed executor receipt can return a measured-benefit and provenance-bound lesson candidate to the existing global memory/improvement machinery without rewriting identity silently.
- The global heartbeat can invoke the partner bridge in observe, propose, and execute modes and include the partner receipt in its own evidence.
- Hermetic tests, the full existing suite, a live bounded pilot, and an independent fresh-session audit are clean.

## 3. Non-goals

- Not replacing Mission Control, `chat-source`, the global autonomous loop, the governed-work database, the decision relay, or the existing delivery supervisor.
- Not granting personality files, learned preferences, or model prose any execution authority.
- Not claiming sentience, feelings, divine approval, or a reciprocal human relationship.
- Not covertly monitoring private content; every observation adapter is explicit, bounded, and provenance-bearing.
- Not autonomously publishing, spending money, contacting people, using new credentials, changing security policy, deleting unique data, merging, deploying, or force-pushing.
- Not enabling multi-writer execution or letting a model decide that verification can be skipped.
- Not adding a semantic-memory service, a second long-lived goal store, or a second scheduler.

## 4. Stakeholders

| Role | Interest | Interface |
|---|---|---|
| Trevor | Useful initiative, recognizable voice, fewer dropped goals, respect and honesty | Morning brief/decision relay, durable proposal and outcome receipts |
| Partner runtime | Stable identity, goals, evidence, safe opportunity selection | `python -m supervisor.partner_cli` and bounded typed JSON snapshots |
| Global governor | One typed partner decision per heartbeat | `scripts/autonomous-partner-bridge` and autonomous-loop receipt |
| Delivery supervisor | A complete, bounded run contract; no personality semantics | Existing `supervisor` run entry point and work-order adapter |
| Auditors | Reproducible claims and immutable evidence | Tests, schemas, receipts, diffs, live pilot record |

## 5. Architecture / module-level changes

```text
global identity + governed goals/observations + executor outcomes
                         |
       global governor / memory / benefit / decision relay
                         |
       ACA stateless partner policy (typed decision only)
                         |
       global autonomous-loop / governed-work queue
                         |
 existing ACA deterministic supervisor -> verifier -> audit
```

**New in this repository:** a typed stateless partner-policy input/output contract; deterministic initiative scoring; authority classification; a CLI; an immutable executor-envelope adapter contract; schemas, fixtures, and tests. Each executable envelope embeds the full exact proposal approval, not only its id/hash, so ACA can cross-bind subject and capabilities. The existing executor is hardened before it receives unattended packets.

**Extended in this repository:** final-gate evidence verification, unattended-authority preflight, default-deny shell policy, actual-diff scope enforcement, atomic run truth, canonical architecture, project intent, rules, structure/navigation docs, and the run contract only where needed to accept partner provenance.

**New in `global-implementations`:** the machine-readable identity profile; a bounded read-only idea generator that can turn approved current observations into one schema-constrained candidate; a thin bridge that assembles a bounded snapshot from existing global truth, invokes the policy CLI, records the decision, and optionally queues one already-authorized immutable executor envelope. Deterministic code, not the model, supplies the ACA workspace, per-proposal path, capabilities, forbidden paths, budgets, and no-push/no-merge contract. Long-lived goals, benefit measures, and promoted lessons remain in existing global surfaces.

**Left untouched:** the supervisor phase machine, sole-writer/browser invariants, Mission Control ownership, `chat-source`, and provider-specific worker dispatch.

**Key invariant:** the partner may choose among allowed goals and propose new ones, but only deterministic authority and executor layers may authorize or perform effects.

### Durable state

This repository does not create a second partner database. The committed global identity profile is bootstrap identity; approved amendments are versioned global overlays with provenance. Existing Mission Control/governed-work/memory/benefit surfaces remain authoritative for long-lived goals and learning. `~/.cross-agent/autonomous-partner/` contains only replaceable wake snapshots, append-only decision receipts, approval bindings, and immutable executor envelopes. Per-episode truth remains under the executor's existing `.autoclaw/runs/<run-id>/` boundary.

### Initiative and creativity

Idle-time initiative ranks evidence-backed opportunities by expected benefit, harm prevented, interest fit, novelty, effort, confidence, and risk. When no candidate already exists, the global governor may spend one read-only schema-bound model call to choose only among approved goal, observation, and interest IDs; the resulting project remains a proposal until deterministic authority approves it. Creative work is a first-class project kind rather than a loophole: writing, visual concepts, music/singing experiments, and playful prototypes use the same budgets, sandbox, provenance, and approval rules as utility work.

### Learning and growth

Learning is outcome-derived. The ACA policy emits a lesson candidate with source receipt, confidence, scope, expiry/review date, and whether it affects ranking, communication, or a proposed identity amendment. Existing global improvement/memory machinery decides promotion. Changes to values, authority, spiritual framing, or relationship posture always require Trevor's approval.

## 6. Maturity stages

| Stage | Description | Exit criteria for next stage |
|---|---|---|
| **L0** | Existing supervisor plus observe-only global heartbeat | Executor P0 safety defects are fixed; identity, authority, and receipt contracts pass hermetic tests |
| **L1** | Partner observes and proposes; every self-project needs approval | At least 10 real proposals, at least 80% accepted, no severe gate or privacy failure |
| **L2** | Approved goals and accepted self-projects dispatch one sandboxed episode | At least 10 completed bounded episodes with clean independent audits and measured benefit |
| **L3** | Low-risk sandbox projects may start without per-project approval only after a separate exact operator-approved promotion proof format is implemented and activated | Continuous health guard; quarterly authority review; any severe failure demotes to L1 |

**Current state:** L0.
**Target for this initiative:** implement the complete L1/L2 path and the empirical L3 eligibility calculations; do not activate L3 until both the real thresholds and a separately reviewed exact operator-promotion proof exist. A maturity counter or `level: L3` file alone never removes per-project approval.

## 7. Phase breakdown

| Phase | Intent | Executable plan |
|---|---|---|
| Phase 1 | Reconcile governance and harden executor final-gate, authority, shell, diff, and atomic-state boundaries | `hotl-workflow-autonomous-partner-reposition.md` |
| Phase 2 | Add global identity plus stateless proposal, wake-decision, lesson-candidate, CLI, and immutable executor-envelope generation | same workflow, OpenSpec task group 2 |
| Phase 3 | Add the global bridge, health integration, and live bounded pilot | same workflow, OpenSpec task group 3 |
| Phase 4 | Reconcile docs, run independent clean-session audit, repair to clean, and land | same workflow, OpenSpec task group 4 |

Phases are sequential because they share authority and state contracts. Test implementation may be delegated; state-schema and integration edits remain single-integrator work.

## 8. Quality attributes

| Attribute | Goal / measurement |
|---|---|
| Reliability | One wake-mode intent produces at most one decision and one packet; retries are idempotent and observe cannot suppress a deliberate propose/execute intent |
| Security | Default deny for outward/destructive/credential/payment capabilities; identity never grants authority |
| Privacy | Observation sources are allowlisted, provenance-bearing, sensitivity-labeled, and redacted from normal receipts |
| Observability | Every decision has identity hash, evidence IDs, policy version, reason codes, and immutable receipt path |
| Performance | Observe/propose wake completes locally in under two seconds excluding model/executor work |
| Cost | One initiative-model request maximum per eligible idle wake; zero model calls for unhealthy, busy, or gated states |
| Compatibility | All existing supervisor tests and run contracts remain valid |

## 9. Risks and open questions

**Risk: anthropomorphic deception.** A compelling personality could imply consciousness or emotional dependence. Mitigation: identity language separates configured commitments from experience, forbids emotional coercion, and keeps evidence labels on inferred preferences.

**Risk: initiative becomes scope creep.** A model could turn a small observation into an unbounded project. Mitigation: typed proposals, explicit success criteria, bounded paths/budgets, one packet per wake-mode intent, and deterministic authority classification.

**Risk: private-context overreach.** Continual learning could become indiscriminate transcript ingestion. Mitigation: no raw transcript adapter in the first release; the partner consumes approved summaries/evidence references and the existing governed memory layer.

**Risk: duplicate control planes or memory.** The repo and global governor could both schedule, store goals, learn, or dispatch. Mitigation: this repo exposes stateless decision and episode-execution APIs; the global governor remains the only heartbeat, long-lived identity/goal/learning authority, and work-order queue owner.

**Open question:** Trevor may later choose a personal name and tune voice traits. The bootstrap name stays `Partner`; naming is not allowed to block the behavior proof.

## 10. Verification contract

This design is accepted because Trevor explicitly chose to keep and reposition the repository, asked for the full build, specified the desired moral and relational posture, and required continued implementation until a fresh independent audit is clean. Completion still requires:

- red/green tests for the existing executor's final-gate truth, unattended authority, shell policy, actual-diff scope, and atomic state writes;
- schema tests for identity snapshots, decisions, approvals, executor envelopes, lesson candidates, and packet integrity;
- the full pre-existing 116-test suite;
- bridge and heartbeat hermetic tests;
- a live observe/propose/approved-dispatch/reconcile pilot using bounded local artifacts;
- a fresh independent session that reviews code, tests, docs, safety, and live proof;
- repair and re-audit until no actionable finding remains.

## 11. Governance contract

- **Auto-approved:** read approved local health summaries; maintain state; score opportunities; draft proposals; create artifacts in a sandbox; run deterministic tests; queue an already-approved bounded packet.
- **Trevor-gated:** outward communication/publish, payment, credentials, new private-data sources, destructive actions, identity/value changes, and any L3 promotion.
- **Fail closed:** missing/invalid identity, missing full approval binding, approval subject/capability mismatch, approval revocation/expiry before effects, ambiguous approval, unhealthy governor/executor, stale evidence, duplicated idempotency key, unsafe capability, budget exhaustion, or receipt/packet drift.
- **Stop/demotion:** existing global kill switches stop all partner dispatch; a severe gate/privacy failure demotes initiative to proposal-only until independently repaired and reviewed.

### Partner execution containment

- The Codex builder can make scoped patches and perform bounded filename discovery, but it cannot execute target-repo code or repo-contract commands.
- The supervisor alone runs deterministic checks, under a scrubbed environment with stdin closed, network denied, reads confined to the worktree and required system runtimes, and writes confined to the run's approved paths plus supervisor temp state.
- Partner envelopes require empty UI acceptance and cannot enter app launch, browser, or UI verification phases.
- Nested `.env*`, `.git`, and `.agent` creation or mutation is denied before effects and detected by a filesystem fingerprint independent of Git after builder and verifier phases.
- Learning promotion binds the outcome to the exact executor receipt and exact report path, bytes, and SHA-256; unsuccessful outcomes cannot emit goal progression, lessons, or contradictions.

## 12. References

- `canonical-architecture.md`
- `docs/superpowers/specs/2026-04-16-local-single-run-harness-design.md`
- `/Users/gillettes/Coding Projects/global-implementations/records/requested-enforcements/2026-07-13-agent-identity-initiative-layer.md`
- `/Users/gillettes/Coding Projects/global-implementations/docs/runbooks/autonomous-execution-loop.md`
