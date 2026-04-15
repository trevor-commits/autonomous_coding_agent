# Schemas

This directory holds the canonical JSON Schemas for machine-crossing boundaries in the autonomous coding system: contracts, strategy decisions, failure fingerprints, defect packets, and final readiness reports.

To validate a JSON instance locally with the `ajv` CLI, use a command in this shape:

```bash
npx ajv validate --spec=draft2020 -s schemas/run-contract.schema.json -d /path/to/instance.json
```

Any schema change must be logged in `WORK-LOG.md`. If a change is breaking, bump the schema's `$id` minor suffix as part of that change instead of silently reusing the previous identifier.
