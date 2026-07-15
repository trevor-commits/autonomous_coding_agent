# partner-observation-contract Specification

## Purpose
Define ACA's backward-compatible, fail-closed boundary for accepting the frozen Agency v2 observation contract without activating producers, models, dispatch, effects, recurrence, or new authority.

## Requirements
### Requirement: Wake v2 is backward compatible at the observation boundary
ACA SHALL continue accepting the unchanged Stage 0 wake `schema_version="1"`. It SHALL also accept wake `schema_version="2"`, where only the observation item contract changes and every other wake field retains its version-1 meaning and bounds. Unknown wake versions MUST be rejected.

#### Scenario: Old global calls new ACA
- **WHEN** the Stage 0 global runtime sends a valid unchanged wake v1 to the companion ACA
- **THEN** existing Stage 0 validation and decision behavior remain unchanged

#### Scenario: Unknown wake version arrives
- **WHEN** a wake uses a schema version other than 1 or 2
- **THEN** ACA rejects it before ranking or authority policy

### Requirement: Version-2 observations use one exact closed schema
Every wake-v2 observation SHALL validate against ACA's `schemas/partner-observation-v2.schema.json`, which MUST remain byte-identical to the archived contract at `openspec/changes/archive/2026-07-15-agency-v2-observation-contract/contracts/partner-observation-v2.schema.json`. Unknown fields, missing fields, invalid collector names, invalid namespaces, observation-level opportunity scores, or non-low sensitivity MUST reject the complete wake.

#### Scenario: One observation has an unknown field
- **WHEN** one otherwise valid v2 observation adds any field not in the schema
- **THEN** ACA rejects the complete wake without returning a partially accepted snapshot

#### Scenario: Collector namespace is crossed
- **WHEN** a collector uses another collector's dedupe key or source reference
- **THEN** ACA rejects the complete wake

### Requirement: ACA recomputes canonical observation hashes
ACA SHALL normalize no input silently. Every string MUST already be NFC, trimmed, and free of ASCII controls; `interest_ids` MUST already be sorted and duplicate-free. ACA SHALL encode canonical JSON with sorted keys, compact separators, and `ensure_ascii=false`, then recompute `source_revision` and `id` from the exact projections in `openspec/changes/archive/2026-07-15-agency-v2-observation-contract/contracts/agency-v2-packet-a.md`.

#### Scenario: Only timestamps refresh
- **WHEN** `observed_at` and `expires_at` change within valid bounds while semantic fields remain identical
- **THEN** the same source revision and observation ID remain valid

#### Scenario: One semantic input is tampered
- **WHEN** any hashed semantic field, source revision, or observation ID changes independently
- **THEN** ACA rejects the complete wake before ranking or authority policy

#### Scenario: Noncanonical Unicode or array order arrives
- **WHEN** a string is not NFC/trimmed or `interest_ids` is unsorted
- **THEN** ACA rejects it rather than rewriting the evidence before hashing

### Requirement: Logical observations are unique
Within one wake, `(collector_id, dedupe_key)` tuples and observation IDs MUST each be unique. Any duplicate SHALL reject the complete wake.

#### Scenario: Duplicate logical key arrives
- **WHEN** two observations share one collector and dedupe key, even if other fields differ
- **THEN** ACA rejects the complete wake

#### Scenario: Duplicate ID arrives
- **WHEN** two observations carry the same observation ID
- **THEN** ACA rejects the complete wake

### Requirement: Observation time bounds are exact
Wake-v2 observation timestamps SHALL use UTC RFC 3339 whole seconds ending in `Z`. `observed_at` MUST be no more than five seconds after wake `created_at`, MUST precede `expires_at`, `expires_at` MUST be later than wake `created_at`, and the observation MUST satisfy a collector-specific maximum TTL: 24 hours for todo markers, five minutes for Resource Governor, and 30 minutes for autonomous-loop health.

#### Scenario: Future skew exceeds five seconds
- **WHEN** an observation is more than five seconds after wake creation
- **THEN** ACA rejects the complete wake

#### Scenario: TTL exceeds collector ceiling
- **WHEN** an observation's expiry exceeds its collector-specific maximum by one second
- **THEN** ACA rejects the complete wake

#### Scenario: Evidence expired before wake creation
- **WHEN** an observation's expiry is not later than wake `created_at`
- **THEN** ACA rejects the complete wake as stale

#### Scenario: Fractional or offset timestamp arrives
- **WHEN** an observation timestamp has fractional seconds or a non-`Z` offset
- **THEN** ACA rejects the complete wake

### Requirement: Packet A grants no activation or authority
The ACA companion SHALL NOT collect observations, activate global wake v2, call a model, create a candidate, schedule work, persist new global truth, or widen an effect capability merely because it accepts a valid wake-v2 observation. Existing ranking and authority remain separate downstream gates.

#### Scenario: Valid v2 wake is validated
- **WHEN** ACA accepts a schema- and semantics-valid wake v2
- **THEN** acceptance alone causes no global state mutation, model call, queue dispatch, or authority change
