# Schemas

The `partner-*` schemas define the stateless autonomous-partner boundary: configured identity, bounded wake snapshot, exact approval, one typed decision, immutable executor envelope, executor outcome, and expiring lesson candidate. The wake snapshot accepts the unchanged Stage 0 version 1 plus version 2, whose changed boundaries are the exact `partner-observation-v2.schema.json` item contract and one required canonical `identity_artifact_hash`; the v2-only hash is forbidden in v1. Schema validation is necessary but not sufficient: `supervisor.partner_contracts.validate_wake_snapshot` recomputes version-2 observation hashes and the canonical identity-artifact binding, then enforces canonical text, logical uniqueness, timestamp/skew, and collector TTL rules before policy; `validate_executor_envelope` enforces cross-field hashes and authority bindings.

This directory holds the canonical JSON Schemas for machine-crossing boundaries in the autonomous coding system: repo contracts, run contracts, strategy decisions, failure fingerprints, defect packets, and final readiness reports.

To validate a JSON instance locally with the `ajv` CLI, use commands in these shapes:

```bash
npx ajv validate --spec=draft2020 -s schemas/repo-contract.schema.json -d /path/to/repo-contract.json
npx ajv validate --spec=draft2020 -s schemas/run-contract.schema.json -d /path/to/run-contract.json
```

Any schema change must be logged in `todo.md`, with verification evidence added there when the change affects validation behavior. If a change is breaking, bump the schema's `$id` minor suffix as part of that change instead of silently reusing the previous identifier.
