# Structure

**Date:** April 15, 2026  
**Authority:** `canonical-architecture.md`

## 1. Boundary

The boundary is fixed. The target repo owns only its `.agent/` contract surface, beginning with `.agent/contract.yml` and any target-repo-specific contract companions that the canonical architecture explicitly names. This control-plane repo owns the version-controlled implementation and governance surfaces for the system itself: `schemas/`, `supervisor/`, `fixtures/`, `tests/`, `prompts/` if adopted, `policies/` if adopted, the active root documentation set, and historical records under `design-history/`. Runtime state is supervisor-owned on disk under `.autoclaw/runs/<run-id>/` and related `.autoclaw/` runtime paths, is gitignored everywhere, and is never treated as committed source in either repo. Direct Codex CLI integration is the hard runtime dependency for the smallest v1; any alternate adapter path such as `acpx` is a later hardening concern, and Phase 0 stops at entry if Codex is unavailable.

## 2. Control-Plane Repo Contents

- `schemas/` holds the canonical machine-crossing schemas that define stable shapes for contracts, decisions, defects, and reports.
- `supervisor/` will hold the deterministic runtime code that enforces legality, phase ordering, ownership boundaries, and artifact production once implementation starts.
- `fixtures/` will hold control-plane-owned benchmark inputs and other reusable validation fixtures.
- `tests/` will hold automated tests for supervisor behavior, contracts, policies, and other control-plane code.
- `prompts/` holds version-controlled prompt templates if the prompt system is extracted into its own folder.
- `policies/` holds repo-local policy assets if the project adopts a dedicated policy folder beyond the root rules documents.
- `design-history/` holds ADRs, archived architecture drafts, old reconciliations, and audit reports that preserve how decisions were reached without becoming active source of truth.
- Root doc files hold the current onboarding, navigation, architecture, rules, planning, and governance records that explain the repo as it exists now.
- `CONTINUITY.md` lives at the repo root because continuity is a load-bearing rule for every bounded task and its durable record.
- `COHERENCE.md` lives at the repo root because coherence is a load-bearing rule for every commit and the append-only Dependency Map belongs with the live governance surface.

## 3. Target-Repo Surface

The target repo exposes one automation surface: `.agent/`. In v1, the only canonical file convention required there is `.agent/contract.yml`, which declares how that target repo is set up, tested, launched, checked for health, and otherwise automated. If future contract companions are added, they belong there only when `canonical-architecture.md` names them explicitly; this document does not widen that surface by implication.

## 4. Runtime State

Runtime state is supervisor-owned and lives under `.autoclaw/` only while the system is running or preserving post-run evidence. The canonical per-run anchor is `.autoclaw/runs/<run-id>/state.json`, with sibling runtime artifacts already named by the architecture: `contract.json`, `plan.json`, `execution.log`, `defects/`, `artifacts/` with `screenshots/`, `videos/`, `logs/`, and `traces/`, plus `reports/` for final outputs. Cross-run operational memory, when enabled later, lives alongside runs under `.autoclaw/memory/` as supervisor-managed runtime data rather than repo truth, but the smallest v1 does not require that directory to exist. `.autoclaw/` is gitignored in both this repo and any target repo; it is runtime storage, not committed structure.

## 5. Where Does X Go?

A new schema goes in `schemas/` because it defines a reusable contract shape that multiple lanes or tools must interpret the same way. A new benchmark fixture goes in `fixtures/` because fixtures are control-plane-owned inputs for validating the system, not target-repo source or runtime residue. A new supervisor test goes in `tests/` because tests must live with the control-plane code they verify. A new run artifact goes under `.autoclaw/runs/<run-id>/` because artifacts are evidence produced by a specific run and should not be promoted into version-controlled truth. A new policy rule goes in `policies/` if that folder is adopted, otherwise in the root rules documents, because policy belongs to the control plane rather than the target repo. A new ADR, reconciliation note, archived audit, or dated research-backed decision memo goes in `design-history/` because historical reasoning belongs behind the active source-of-truth boundary. A new prompt template goes in `prompts/` if that folder is adopted, because prompt assets are part of the control-plane implementation surface and should not be mixed into runtime artifact storage. A new navigation or onboarding document belongs at the repo root if it describes current truth for both humans and agents.

## 6. Governance Records

Use `todo.md` for durable planning, the `Active Next Steps` execution queue, the `Linear Issue Ledger` that mirrors every live issue with `todo home:`, `why this exists:`, and `origin source:`, plus suggestions, audit logs, test evidence, feedback decisions, and the `Completed` trail of landed repo changes. Use `design-history/` for archived audit reports, reconciliations, and superseded architecture documents that should remain available without cluttering the active root surface.

The Dependency Map lives in `COHERENCE.md` and is append-only. Ripple ownership is part of the active governance surface, not archive material.

## Appendix: Changes Propagated

- `canonical-architecture.md` — `Repo Contract`, `Runtime State`, and `Terminal States and Readiness Verdict` sections: aligned the boundary, runtime-state placement, and terminal-state source of truth.
- `LOGIC.md` — `What This System Does` section: points terminal-state vocabulary back to `canonical-architecture.md §9.1`.
- `RULES.md` — `Contract Rules`, `Phase Transition Rules`, and `Stop Conditions` sections: aligned `UNSUPPORTED` triggers and terminal-state enforcement language.
- `IMPLEMENTATION-PLAN.md` — `Phase 0: Repo Preparation and Manual Baseline`, `Phase 2.2 Strategy Decision API`, and `Phase 4` prompt-deliverable sections: aligned boundary expectations, naming, and canonical terminal-state references.
