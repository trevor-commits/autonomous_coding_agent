## Why

The repository already provides a tested deterministic delivery supervisor, but it is dormant and cannot yet be trusted beneath a persistent autonomous partner. Its final gate currently asserts evidence it has not verified, direct runs do not enforce queue risk/approval metadata, unknown shell commands default to allowed, actual worktree changes can diverge from model-reported files, and run truth is not written atomically. Fixing those boundaries and adding a typed stateless partner policy lets the existing global governor become proactive without creating a second control plane, scheduler, or memory system.

## What Changes

**Executor evidence and authority**
- From: readiness trusts hard-coded evidence booleans and reported activity.
- To: final readiness depends on a real authoritative rerun, real artifacts, pre-effect unattended authority checks, actual-diff scope checks, default-deny unknown commands, and atomic run truth.
- Reason: a recurring governor needs evidence-backed results and fail-closed effects.
- Impact: direct unsafe contracts that previously ran will block.

**Persistent partner composition**
- Add a global machine-readable identity and bounded wake snapshot.
- Add a stateless ACA policy that emits exactly one no-op, proposal, authorized executor envelope, or lesson candidate.
- Add a thin global bridge to the existing autonomous-loop queue, approvals, receipts, benefit, and memory surfaces.
- Keep self-originated work approval-gated until empirical graduation thresholds are met.

## Capabilities

### New Capabilities

- `executor-evidence-authority`: Truthful final-gate evidence, pre-effect authority checks, actual-diff reconciliation, default-deny shell behavior, and atomic run state.
- `partner-identity-initiative`: Typed identity, preferences, evidence-backed useful/creative proposal scoring, maturity thresholds, and identity-without-authority invariants.
- `governed-partner-dispatch`: One hash-bound executor envelope per eligible wake through the existing global queue, kill switches, approvals, and receipts.
- `outcome-benefit-learning`: Provenance-bound benefit and lesson candidates returned to existing global goal, memory, and improvement surfaces.

### Modified Capabilities

None. This repository had no living OpenSpec capability specifications before this change.

## Impact

Affected surfaces include `supervisor/main.py`, policy/run-store helpers, new partner schemas/policy/CLI/tests, source-of-truth docs, and the global autonomous-loop bridge/config/runbook/tests. No new runtime dependency, scheduler, semantic-memory service, or provider credential is introduced. Existing safe run contracts remain compatible; unsafe unattended contracts now fail closed before builder effects.
