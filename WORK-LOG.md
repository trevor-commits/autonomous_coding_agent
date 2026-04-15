## 2026-04-14 — PROJECT_INTENT filled

- Replaced template with real intent sourced from `canonical-architecture.md` §1 and `README.md`.
- Open questions surfaced: whether `PROJECT_INTENT.md` should also mirror any additional v1 scope constraints from `RULES.md` or completion signals from `IMPLEMENTATION-PLAN.md` that were outside this task's required reading set.

## 2026-04-14 — Repo boundary resolved

- STRUCTURE.md rewritten to remove `.agent/` + `.autoclaw/` dual-location ambiguity.
- Boundary: target owns `.agent/contract.yml`; control plane owns schemas/supervisor/fixtures/tests; run artifacts under `.autoclaw/runs/` (gitignored).
- Cross-doc edits: `canonical-architecture.md:390,980,1003`; `LOGIC.md:132,174,176`; `RULES.md:153,268-269`; `IMPLEMENTATION-PLAN.md:175,269-281,289,461,583`.
- Added `.gitignore`.

## 2026-04-14 — Schemas scaffolded

- Created `schemas/{run-contract,strategy-decision,failure-fingerprint,defect-packet,readiness-report}.schema.json`.
- Source sections (by `canonical-architecture.md` heading): `8.1 Repo Contract`, `8.2 Run Contract`, `9. Phase Machine`, `9.3 Typed Action Graph`, `10.5 Release Checker`, `16. Defect Packet Standard`, `18. Failure Handling`, and `20. Reporting`.
- Open questions surfaced per schema: `run-contract` env metadata beyond `required_vars` and `template` is not yet specified; `strategy-decision` payloads for several typed actions are still only partially defined; `failure-fingerprint` does not yet define any canonical raw stderr or low-level payload field; `defect-packet` names no canonical network-artifact field despite network capture being required; `readiness-report` still reflects mixed final-state versus readiness-verdict vocabulary and an unresolved `artifact_manifest` entry shape.
- Pending terminal-state normalization: yes.

## 2026-04-14 — Terminal-state vocabulary normalized

- `run_state` ∈ {`COMPLETE`, `BLOCKED`, `UNSUPPORTED`, `IN_PROGRESS`}; `readiness_verdict` ∈ {`READY`, `NOT_READY`, `NEEDS_MORE_EVIDENCE`}.
- COMPLETE legality rule codified in `RULES.md`.
- ADR-0001 created under `design-history/`.
- Files touched: `canonical-architecture.md`, `LOGIC.md`, `RULES.md`, `PROMPTS.md`, `IMPLEMENTATION-PLAN.md`, `design-history/ADR-0001-terminal-state-normalization.md`, `WORK-LOG.md`.
- Schemas updated: `schemas/readiness-report.schema.json`, `schemas/strategy-decision.schema.json`.
