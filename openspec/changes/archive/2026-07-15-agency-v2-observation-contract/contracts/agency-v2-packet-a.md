# ACA Agency v2 Packet A contract

Status: frozen implementation contract copied from the independently reviewed global Agency v2 wire contract at commit `4292f4efd4ce9c5a3586f51c63188c413e92025e`.

## Canonical encoding

Before hashing, every string MUST be Unicode NFC, contain no ASCII control character, and equal its leading/trailing-whitespace trim. Arrays whose order is not semantic MUST be sorted and duplicate-free.

Canonical JSON is UTF-8 JSON with keys sorted lexicographically, separators exactly `,` and `:`, `ensure_ascii=false`, and no trailing newline. Hashes are lowercase SHA-256 hex.

## Compatibility

ACA MUST continue to accept the unchanged Stage 0 wake `schema_version="1"`. Wake `schema_version="2"` changes only the observation item contract; identity, goals, approvals, maturity, outcomes, and their bounds retain wake-v1 meaning.

Every v2 observation MUST validate against `partner-observation-v2.schema.json`.

## Semantic projection and hashes

The source-revision projection contains exactly:

```json
{
  "collector_id": "...",
  "contract_version": "partner-observation/v2",
  "dedupe_key": "...",
  "interest_ids": [],
  "sensitivity": "low",
  "source_ref": "...",
  "summary": "..."
}
```

`source_revision` is `sha256:` plus SHA-256 of its canonical JSON. `id` is `obs-v2-` plus SHA-256 of canonical JSON containing exactly `contract_version`, `collector_id`, `dedupe_key`, and `source_revision`. ACA MUST recompute and compare both. Timestamps are excluded.

## Whole-wake semantic rules

- Uniqueness is `(collector_id, dedupe_key)`; duplicate tuples or duplicate IDs reject the complete wake.
- Collector, dedupe-key, and source-ref combinations MUST match the exact schema namespaces.
- Unknown fields or a hash mismatch reject the complete wake.
- `observed_at` and `expires_at` MUST be UTC RFC 3339 seconds ending in `Z`, with no fractional seconds.
- `observed_at` MUST be no more than five seconds after wake `created_at` and MUST be earlier than `expires_at`; `expires_at` MUST also be later than wake `created_at` so stale evidence cannot enter policy.
- Maximum TTL is 24 hours for `todo-marker/v1`, five minutes for `resource-governor/v1`, and 30 minutes for `autonomous-loop-health/v1`.
- Observation-level opportunity scores do not exist and MUST be rejected.

## Cross-version matrix

| Global | ACA | Required result |
|---|---|---|
| Stage 0 wake v1 | Stage 0 v1-only | existing behavior works |
| Stage 0 wake v1 | companion v1+v2 | existing behavior works unchanged |
| Agency v2 wake v2 | Stage 0 v1-only | incompatible-contract no-op before any model call |
| Agency v2 wake v2 | companion v1+v2 | eligible only after separate global activation gates |
