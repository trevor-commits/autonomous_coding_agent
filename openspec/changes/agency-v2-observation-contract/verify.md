# Verification Report: Agency v2 Observation Contract

## Result

**PASS for Packet A implementation and local review.** ACA accepts the unchanged wake-v1 contract and the exact bounded wake-v2 observation contract. Acceptance alone produces no new candidate, authority, dispatch, effect, producer, scheduler, or deployment activation.

## Structural validation

- `openspec validate --all --strict --no-interactive`: 5/5 pass.
- OpenSpec tasks: 10/11 complete; only final commit, push, PR, and remote-tip proof remain.
- Exact implementation base: `origin/main@282eb5118cfcd95263ffc9e409edce1ba831d623`.
- Runtime, change-packet, and frozen global observation schemas are byte-identical at SHA-256 `924dcf74ce336e5011af89fa9428fdac9d6254a6e3fddc0f5d00efe244790877`.
- `git diff --check`: pass.

## Behavior and test evidence

- Focused RED failed six valid-v2 acceptance/boundary cases against the v1-only implementation while legacy behavior stayed green.
- Focused GREEN contract/runtime suite: 31/31 pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -q`: 250 tests pass with two intentional live/stress opt-in skips.
- In-memory compilation: 63 Python files pass without writing bytecode.
- Project-memory, AGENTS, repo-principles, and todo-governance validators pass.
- Independent read-only review closed one P2 and three P3 regression/governance gaps and returned literal `REVIEW-CLEAN`.

## Compatibility and no-effect proof

- Wake v1 remains accepted with its original observation shape.
- Wake v2 accepts only the exact closed observation-v2 schema and recomputes both canonical hashes.
- A valid wake-v2 observe call returns `no_op` / `observe_only`, consumes no candidate iterator, produces no evidence or payload, and mutates neither snapshot nor candidate.
- No existing ranking, authority, execution, queue, recurrence, or Stage 0 deployment file changed.

## Coherence and Ripple Check

The wake/observation schemas, semantic loader, regression tests, schema index, OpenSpec packet, project memory, branch ledger, Work Record, Audit Record, Feedback Decision, and Test Evidence were reconciled together. Global producer activation and the immutable Stage 0 runtimes remain unchanged.

## Deferred or unproved

- Remote CI, PR review, merge containment, and branch cleanup remain final Packet A landing gates.
- Packet B owns global producers, exact dual-SHA compatibility, no-effect deployment proof, and activation/rollback receipts.
- Deliberation, recurring model calls, candidate reuse, effects, broader authority, natural usefulness, adoption, and measured benefit belong to later packets and are not claimed here.

This change must not be archived before merge and the required Ripple Check/completed-index update.
