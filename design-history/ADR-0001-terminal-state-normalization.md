# ADR-0001: Terminal-State Normalization

## Context

The documentation had drifted into four overlapping vocabularies for terminal run outcomes and readiness decisions: `READY/BLOCKED/UNSUPPORTED`, `COMPLETE/BLOCKED/UNSUPPORTED`, `READY/NOT_READY`, and `NEEDS_MORE_EVIDENCE`. That drift created a false-green risk because a reader or implementation could treat readiness output as the same thing as the supervisor's terminal run conclusion.

## Decision

Normalize the vocabulary as follows:

- `run_state` is what the supervisor concludes about the run overall and is one of `COMPLETE`, `BLOCKED`, `UNSUPPORTED`, or `IN_PROGRESS`.
- `readiness_verdict` is what the final readiness gate emits and is one of `READY`, `NOT_READY`, or `NEEDS_MORE_EVIDENCE`.
- `run_state = COMPLETE` is legal only when `readiness_verdict = READY`, all required artifacts named in the run contract exist, all authoritative required checks passed on the final rerun, and no unresolved high-severity defect packets are open.
- `NEEDS_MORE_EVIDENCE` is not terminal. It triggers one more evidence-gathering loop up to the configured bound; after that bound it degrades to `NOT_READY` and the run goes to `BLOCKED`.

The canonical source of truth for this vocabulary is `canonical-architecture.md` under the section titled `Terminal States and Readiness Verdict`.

## Consequences

- Schemas must use these exact enum values.
- Supervisor tests must assert the `run_state = COMPLETE` legality rule.
- Companion docs should reference the canonical section and this ADR instead of redefining the vocabulary again.

## Naming convention

`autoclaw` is the canonical system prefix for runtime directories, git tags, commit-message prefixes, and tool identifiers. `autobot` was an earlier working name and is now retired; future docs and implementation surfaces should use `autoclaw` consistently.
