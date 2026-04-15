## 2026-04-14 — PROJECT_INTENT filled

- Replaced template with real intent sourced from `canonical-architecture.md` §1 and `README.md`.
- Open questions surfaced: whether `PROJECT_INTENT.md` should also mirror any additional v1 scope constraints from `RULES.md` or completion signals from `IMPLEMENTATION-PLAN.md` that were outside this task's required reading set.

## 2026-04-14 — Repo boundary resolved

- STRUCTURE.md rewritten to remove `.agent/` + `.autoclaw/` dual-location ambiguity.
- Boundary: target owns `.agent/contract.yml`; control plane owns schemas/supervisor/fixtures/tests; run artifacts under `.autoclaw/runs/` (gitignored).
- Cross-doc edits: `canonical-architecture.md:390,980,1003`; `LOGIC.md:132,174,176`; `RULES.md:153,268-269`; `IMPLEMENTATION-PLAN.md:175,269-281,289,461,583`.
- Added `.gitignore`.
