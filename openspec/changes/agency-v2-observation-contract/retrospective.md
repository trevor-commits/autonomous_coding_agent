# Retrospective: Agency v2 Observation Contract

## What Packet A contains

ACA now has one backward-compatible, stateless consumer boundary for the frozen observation-v2 contract. It validates the exact item schema and semantic invariants before returning a wake snapshot, while leaving all production, deliberation, authority, and effect paths unchanged.

## Evidence

- Six intended pre-implementation failures demonstrated the missing v2 boundary without breaking legacy tests.
- The focused contract/runtime suite passes 31/31; the full deterministic suite passes 250 tests with two explicit opt-in skips.
- All three frozen schema copies are byte-identical.
- Strict OpenSpec, project-memory, governance, compile, residue, and diff gates pass.
- Independent review returned `REVIEW-CLEAN` after four accepted regression/governance corrections.

## What worked

- Landing the consumer before producers preserved old-global/new-ACA rollback compatibility.
- Exact schemas plus recomputed semantic hashes kept cross-repo trust mechanical instead of prose-based.
- Test-side fixture hashing remained independent from production helpers, so the tests can catch formula drift.
- A single writer plus a read-only reviewer avoided integration races while still parallelizing the audit lane.

## What did not work at first

- Manual schema-hash comparison was not enough; byte parity needed a permanent test.
- Validator-only v2 coverage did not lock the runtime no-effect promise.
- Comparing an ordinary list before and after observe mode proved non-mutation, not non-consumption; a sentinel iterator was required.
- The first branch-ledger entry omitted two mandatory lifecycle labels even though their disposition was implicit elsewhere.

Each accepted finding became a regression or durable governance correction before the clean verdict.

## Deliberate deviations

- No dependency was added for canonicalization or time handling.
- Packet A does not add a collector, model call, persistent state, scheduler, effect, or new authority.
- The OpenSpec change remains unarchived until merge and the post-merge Ripple Check.

## Reusable lesson candidates

- A frozen cross-repo schema deserves a byte-parity regression, not only a one-time hash receipt.
- A no-effect contract should prove both empty output and zero input consumption.
- Backward-compatible consumer-first rollout is the safer boundary when producer activation is a separate risk gate.

These are retrospective candidates only; this file does not create new global policy.
