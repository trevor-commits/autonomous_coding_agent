## Why

The reviewed Agency v2 foundation cannot safely publish observations until ACA accepts and semantically validates the exact version-2 contract. Landing the backward-compatible consumer first preserves Stage 0 rollback, makes hash/namespace/time errors fail closed at the policy boundary, and prevents the global producer from defining its own acceptance rules.

## What Changes

**Wake compatibility**
- From: ACA accepts only the unchanged Stage 0 wake version 1.
- To: ACA accepts unchanged wake v1 and a wake v2 whose only contract change is the observation item shape.

**Observation validation**
- Add the closed `partner-observation/v2` schema.
- Recompute canonical `source_revision` and observation `id`.
- Enforce exact collector namespaces, logical uniqueness, timestamp order/skew, and collector-specific TTL ceilings.
- Reject the complete wake on an unknown field, duplicate, namespace mismatch, invalid timestamp, stale/overlong TTL, or hash mismatch.

**Activation posture**
- Keep all global v2 collectors and runtime activation out of this change.
- Preserve existing Stage 0 behavior for wake v1.

## Capabilities

### New Capabilities

- `partner-observation-contract`: backward-compatible wake versioning plus exact schema and semantic validation for bounded Agency v2 observations.

### Modified Capabilities

None. Existing identity, goals, approvals, maturity, outcomes, ranking, authority, and decision behavior remain unchanged.

## Impact

Affected surfaces are the wake/observation schemas, `supervisor/partner_contracts.py`, focused partner-contract tests, schema navigation, OpenSpec records, and project continuity records. There is no new dependency, process, scheduler, model call, collector, effect, or deployment change.
