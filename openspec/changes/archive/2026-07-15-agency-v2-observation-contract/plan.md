# Agency v2 Packet A implementation plan

> Execute through `hotl-workflow-agency-v2-packet-a.md`. The primary integrator owns shared files, verification, git state, and the final gate. A delegated writer may own only one bounded step at a time after a fresh Resource Governor `intent=new` allow.

**Goal:** add a backward-compatible ACA wake-v2 observation boundary that implements the frozen global contract exactly and does not activate any producer or effect.

**Architecture:** extend the existing `load_contract()` schema boundary. Select the wake schema by exact top-level version, then run v2-only semantic validation before returning the snapshot. Keep canonicalization/hash helpers small and dependency-free.

**Files:** `schemas/partner-observation-v2.schema.json`, `schemas/partner-wake-snapshot.schema.json`, `supervisor/partner_contracts.py`, `tests/test_partner_contracts.py`, `schemas/README.md`, this OpenSpec packet, `PROJECT_MEMORY.md`, and `todo.md`.

## Task 1: RED compatibility and schema tests

- Add helpers that build known-valid v1 and v2 snapshots from deterministic UTC-second fixtures.
- Prove existing v1 validation still passes unchanged.
- Prove valid v2 schema acceptance, exact field closure, collector enums, and source namespaces.
- Run the focused suite and preserve the intended pre-implementation failures.

## Task 2: RED semantic-invariant tests

- Implement test-side canonical projections only to construct fixtures, not to call production helpers.
- Cover both hash formulas, timestamp-only refresh stability, one-field tampering, Unicode NFC/trim/control rejection, sorted interests, duplicate tuple/ID rejection, five-second skew, strict timestamp order, and each TTL ceiling plus one-second overflow.
- Prove any invalid item rejects the whole wake.

## Task 3: Minimal GREEN implementation

- Add the exact runtime observation schema copied from the reviewed packet.
- Version the wake schema without changing v1 field semantics or bounds.
- Add small private helpers for canonical-string checks, exact timestamp parsing, projection encoding, SHA-256, namespace/uniqueness checks, and TTL selection.
- Call semantic validation only after schema validation and before snapshot return.
- Do not change ranking, authority, runtime scheduling, or persistent state.

## Task 4: Verification and records

- Run focused partner-contract tests, full unit discovery, schema parsing, in-memory compilation, strict OpenSpec validation, project-memory validation, repo verifier if present, and `git diff --check`.
- Update exact durable records, including what was not activated or tested live.
- Obtain fresh read-only review against the frozen commit and repair accepted findings with regressions before PR.
