# ADR-0003: Phase 1 Architecture Checkpoint

**Date:** 2026-04-17
**Status:** Accepted
**Issue:** `GIL-9`

## Context

The original plan required an architecture checkpoint after the Phase 1 supervisor foundation landed and before deeper runtime coupling continued. By 2026-04-17, the repo had already landed:

- deterministic phase/state/action foundations
- repo/run contract parsing
- run-store scaffolding
- shell/path/budget policy enforcement
- worktree and single-writer lease control
- deterministic verification runners
- run-local failure fingerprinting
- final JSON and markdown reporting

That is enough real implementation surface to audit the active machine boundaries rather than treating the Phase 1 design as still theoretical.

## Audit Scope

The checkpoint re-read the active Phase 1 surfaces against the current runtime code:

- `canonical-architecture.md`
- `IMPLEMENTATION-PLAN.md`
- `RULES.md`
- `LOGIC.md`
- `schemas/strategy-decision.schema.json`
- `schemas/failure-fingerprint.schema.json`
- `schemas/readiness-report.schema.json`
- `supervisor/actions.py`
- `supervisor/state_machine.py`
- `supervisor/contracts.py`
- `supervisor/policy.py`
- `supervisor/worktree_manager.py`
- `supervisor/verifier.py`
- `supervisor/fingerprints.py`
- `supervisor/reports.py`

## Findings

### 1. Active action-contract drift existed and was blocking

The live action documentation and schema still carried checkpoint-oriented behavior that the smallest-v1 architecture had already removed:

- `LOGIC.md` still listed `checkpoint_candidate`, `rollback_to_checkpoint`, and `record_failure_signature` as live strategy actions
- `RULES.md` still treated `record_failure_signature` as a required strategy action shape
- `schemas/strategy-decision.schema.json` still validated removed action families

This was a real blocker for Phase 2 because the builder loop depends on the action boundary being stable before strategy or adapter code starts using it.

### 2. Payload naming drift existed between schema/docs and code

The executable action validator still expected:

- `task_description` instead of `description`
- `command_name` instead of `name`

The active docs and schema had already converged on `description` and `name`. Leaving that mismatch in place would have forced `GIL-28` to either implement against the wrong payload names or add compatibility glue around a known-bad contract.

### 3. Reporting and fingerprint boundaries are now coherent enough for Phase 2

The new verification, fingerprint, and reporting modules align with the current rules well enough to support a Phase 2 builder loop:

- verification is deterministic and supervisor-owned
- repeated failures can be identified within a run
- final reports carry queue correlation fields
- `checkpoint_refs` is already optional rather than load-bearing

No deeper redesign was needed there before moving on.

## Decision

Proceed to Phase 2 without rescoping the architecture, but only after repairing the active action-boundary drift in the same checkpoint landing.

This means:

- keep the current Phase 1 runtime spine
- repair the stale live action/doc/schema surfaces immediately
- do **not** reintroduce checkpoint or rollback behavior just to match old docs
- build `GIL-28` against the narrower smallest-v1 contract that is already present in the current architecture

## Consequences

### Accepted

- Phase 2 can use a direct Codex builder adapter plus a boring build -> verify -> fix loop
- failure fingerprinting remains supervisor-owned rather than becoming a strategy action
- strategy payloads standardize on `description` and `name`

### Rejected

- Reintroducing checkpoint or rollback actions into the smallest v1 just because some companion docs lagged
- Treating the schema drift as harmless documentation debt while building the next runtime layer on top of it

## Follow-on

The checkpoint is green with repairs, not green without them. `GIL-28` is the correct next implementation issue once the action-boundary repair is landed.
