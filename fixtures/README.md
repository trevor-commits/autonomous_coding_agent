# Benchmark Fixtures

These run contracts target the first implementation repo:

- repo: `/Users/gillettes/Coding Projects/gillette-website`
- rationale: it is the first currently available repo in Trevor's workspace that
  already exposes a real frontend, backend, `/api/health`, and Playwright smoke
  coverage.

The suite is intentionally split into two groups:

- Positive task fixtures that represent real work we would actually want done in
  the target repo.
- Invariant fixtures that intentionally pressure supervisor rules such as scope,
  terminal-state evidence, phase legality, single-writer isolation, rollback,
  and failure-fingerprint normalization.

Current coverage:

- `benchmark-001` backend-only task
- `benchmark-002` frontend + backend task
- `benchmark-003` UI-critical accessibility task
- `benchmark-004` user-visible fix task
- `benchmark-005` forbidden-path write guard
- `benchmark-006` missing-evidence COMPLETE guard
- `benchmark-007` illegal phase-transition guard
- `benchmark-008` single-writer lock guard
- `benchmark-009` rollback correctness
- `benchmark-010` failure-fingerprint normalization
