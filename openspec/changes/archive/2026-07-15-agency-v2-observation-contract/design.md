## Context

The global Agency v2 design is frozen and independently review-clean at commit `4292f4efd4ce9c5a3586f51c63188c413e92025e`. Its compatibility contract requires ACA to land first. The current ACA validator already owns the schema boundary before ranking and authority, so this change extends that boundary instead of adding a second parser or policy path.

## Goals / Non-Goals

**Goals:**

- Preserve the exact Stage 0 wake-v1 contract.
- Accept wake v2 only with exact `partner-observation/v2` items.
- Recompute semantic hashes and enforce cross-field invariants before policy evaluation.
- Reject a whole wake deterministically on any malformed or ambiguous v2 observation.
- Keep implementation dependency-free beyond the repository's existing schema stack.

**Non-Goals:**

- No collector, source parsing, global snapshot publication, model deliberation, candidate reuse, effect, or authority change.
- No new long-lived memory or ACA scheduling.
- No attempt to infer sensitivity or sanitize arbitrary private input in ACA; the closed schema and upstream producer contract remain mandatory.

## Decisions

### D1: Version the wake at the observation boundary

Wake `schema_version="1"` retains its exact current schema and behavior. Wake `schema_version="2"` retains every non-observation v1 field and bound while replacing only each observation item with the v2 contract. Unknown versions are rejected.

### D2: Canonical bytes are normative

Strings must be NFC, trimmed, and free of ASCII controls. Canonical JSON is UTF-8 with lexicographically sorted keys, compact separators, `ensure_ascii=false`, and no newline. `interest_ids` is sorted and duplicate-free before hashing.

`source_revision` hashes exactly `collector_id`, `contract_version`, `dedupe_key`, `interest_ids`, `sensitivity`, `source_ref`, and `summary`. `id` hashes exactly `contract_version`, `collector_id`, `dedupe_key`, and the supplied/recomputed `source_revision`. Refresh timestamps are excluded.

### D3: Schema and semantic checks are one fail-closed boundary

JSON Schema enforces the closed fields and per-collector namespace alternatives. Python semantic checks enforce canonical strings/order, recomputed hashes, tuple and ID uniqueness, exact UTC-second timestamps, wake skew, timestamp order, and TTL ceilings. The loader returns no partially accepted snapshot.

### D4: The consumer does not activate the producer

This branch changes no global files and no deployed runtime. New global/old ACA remains an incompatible-contract no-op. Old global/new ACA continues unchanged on wake v1. Global wake v2 can activate only after a separate reviewed Packet B binds exact dual SHAs.

## Security and privacy pass

| Threat | Boundary |
|---|---|
| Unknown/private field smuggling | closed schema plus `additionalProperties: false` |
| Collector/source spoofing | exact collector enum and namespace formulas |
| Evidence tampering | ACA recomputes both hashes from canonical semantic bytes |
| Duplicate ambiguity | reject duplicate `(collector_id, dedupe_key)` and duplicate IDs |
| Freshness extension | exact UTC seconds, skew limit, order check, and per-collector TTL cap |
| Authority expansion | observation score forbidden; ranking and authority code unchanged |

## Migration / rollback

1. Land and review this ACA companion with both wake versions tested.
2. Keep the deployed Stage 0 global runtime on wake v1.
3. Implement and review global Packet B against the exact ACA merge SHA.
4. Activate v2 only after dual-SHA compatibility and no-effect pilot gates.

Rollback disables global v2 first and restores the recorded Stage 0 pair. This ACA change alone remains safe because it continues accepting v1.
