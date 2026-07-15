# Brainstorm: Agency v2 observation contract companion

## Problem

Stage 0 accepts one exact wake version-1 observation shape. The reviewed Agency v2 design needs correction-aware observations with collector identity, stable semantic revisions, deterministic IDs, bounded freshness, and source namespaces. The global producer cannot activate until ACA can independently validate that contract while preserving the Stage 0 rollback pair.

## Options considered

### 1. Replace wake v1 in place

Rejected. It would invalidate the proven Stage 0 global/ACA pair and make rollback dependent on an atomic two-repository deployment.

### 2. Accept arbitrary observation objects and validate later

Rejected. Unknown fields, malformed hashes, duplicate logical observations, or stale evidence could reach ranking or authority code.

### 3. Add a backward-compatible wake v2 boundary

Selected. Wake v1 remains unchanged. Wake v2 changes only the observation item contract; ACA validates every v2 item against a closed schema and recomputes all semantic invariants before any partner policy runs.

## Guardrails

- No global producer activation in this packet.
- No observation-level opportunity score.
- No raw/private source ingestion or new storage.
- Any invalid v2 observation rejects the complete wake.
- Unknown versions fail closed.
- Old global/new ACA remains a valid Stage 0 pair.
