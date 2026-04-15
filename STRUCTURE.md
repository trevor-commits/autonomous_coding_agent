# Structure

**Date:** April 14, 2026  
**Authority:** `canonical-architecture.md`, with boundary alignment notes propagated below.

## 1. Boundary

The boundary is fixed. The target repo owns only its `.agent/` contract surface, beginning with `.agent/contract.yml` and any target-repo-specific contract companions that the canonical architecture explicitly names. This control-plane repo owns the version-controlled implementation and governance surfaces for the system itself: `schemas/`, `supervisor/`, `fixtures/`, `tests/`, `prompts/` if adopted, `policies/` if adopted, and historical records under `design-history/`, plus the root documentation set. Runtime state is supervisor-owned on disk under `.autoclaw/runs/<run-id>/` and related `.autoclaw/` runtime paths, is gitignored everywhere, and is never treated as committed source in either repo. Codex CLI is a hard runtime dependency, `acpx` is the adapter, and Phase 0 stops at entry if Codex is unavailable.

## 2. Control-Plane Repo Contents

- `schemas/` holds the canonical machine-crossing schemas that define stable shapes for contracts, decisions, defects, and reports.
- `supervisor/` holds the deterministic runtime code that enforces legality, phase ordering, ownership boundaries, and artifact production.
- `fixtures/` holds control-plane-owned benchmark inputs and other reusable test fixtures used to exercise the system.
- `tests/` holds automated tests for supervisor behavior, contracts, policies, and other control-plane code.
- `prompts/` holds version-controlled prompt templates if the project chooses to split prompt assets into their own folder rather than embedding them elsewhere.
- `policies/` holds repo-local policy assets if the project adopts a dedicated policy folder beyond the root rules documents.
- `design-history/` holds ADRs and other historical records that explain how settled decisions were reached without becoming the active source of truth.
- Root doc files hold the canonical architecture, companion docs, onboarding material, and other source-of-truth markdown entry points for the repo.

## 3. Target-Repo Surface

The target repo exposes one automation surface: `.agent/`. In v1, the only canonical file convention required there is `.agent/contract.yml`, which declares how that target repo is set up, tested, launched, checked for health, and otherwise automated. If future contract companions are added, they belong there only when `canonical-architecture.md` names them explicitly; this document does not widen that surface by implication.

## 4. Runtime State

Runtime state is supervisor-owned and lives under `.autoclaw/` only while the system is running or preserving post-run evidence. The canonical per-run anchor is `.autoclaw/runs/<run-id>/state.json`, with sibling runtime artifacts already named by the architecture: `contract.json`, `plan.json`, `execution.log`, `defects/`, `artifacts/` with `screenshots/`, `videos/`, `logs/`, and `traces/`, plus `reports/` for final outputs. Cross-run operational memory, when enabled, lives alongside runs under `.autoclaw/memory/` as supervisor-managed runtime data rather than repo truth. `.autoclaw/` is gitignored in both this repo and any target repo; it is runtime storage, not committed structure.

## 5. Where Does X Go?

A new schema goes in `schemas/` because it defines a reusable contract shape that multiple lanes or tools must interpret the same way. A new benchmark fixture goes in `fixtures/` because fixtures are control-plane-owned inputs for validating the system, not target-repo source or runtime residue. A new supervisor test goes in `tests/` because tests must live with the control-plane code they verify. A new run artifact goes under `.autoclaw/runs/<run-id>/` because artifacts are evidence produced by a specific run and should not be promoted into version-controlled truth. A new policy rule goes in `policies/` if that folder is adopted, otherwise in the root rules documents, because policy belongs to the control plane rather than the target repo. A new ADR goes in `design-history/` because it records decision history without replacing the canonical architecture. A new prompt template goes in `prompts/` if that folder is adopted, because prompt assets are part of the control-plane implementation surface and should not be mixed into runtime artifact storage.

## Changes Propagated

- `canonical-architecture.md:390,980,1003`
- `LOGIC.md:132,174,176`
- `RULES.md:153,268-269`
- `IMPLEMENTATION-PLAN.md:175,269-281,289,461,583`
