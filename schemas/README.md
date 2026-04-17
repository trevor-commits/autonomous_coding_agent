# Schemas

This directory holds the canonical JSON Schemas for machine-crossing boundaries in the autonomous coding system: repo contracts, run contracts, strategy decisions, failure fingerprints, defect packets, and final readiness reports.

To validate a JSON instance locally with the `ajv` CLI, use commands in these shapes:

```bash
npx ajv validate --spec=draft2020 -s schemas/repo-contract.schema.json -d /path/to/repo-contract.json
npx ajv validate --spec=draft2020 -s schemas/run-contract.schema.json -d /path/to/run-contract.json
```

Any schema change must be logged in `todo.md`, with verification evidence added there when the change affects validation behavior. If a change is breaking, bump the schema's `$id` minor suffix as part of that change instead of silently reusing the previous identifier.
