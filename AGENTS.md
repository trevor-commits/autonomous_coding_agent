# AGENTS.md (Autonomous Coding Agent)

This root file intentionally stays thin so repo-local policy does not drift from the global stack.

## Required Read Order
1. `$CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md` when `CODEX_HOME` is unset)
2. `AGENTS.project.md`
3. `PROJECT_INTENT.md`
4. `PROJECT_MEMORY.md` — shared cross-AI project memory; schema: `.project-memory.schema.yaml`; write policy: `$CODEX_HOME/policies/PROJECT_MEMORY.md`
5. `todo.md`

## Local Authority
- `AGENTS.project.md` is the authoritative repo-local overlay for this repository.
- Do not treat this file as a second copy of the global AGENTS policy.
- Keep repo-specific edits in `AGENTS.project.md` so the root file remains a stable pointer.

## Agent harness files (this repo)

| File | Role |
|---|---|
| **`AGENTS.md`** (root) | Thin bootstrap pointer: global read order, local authority, harness index. |
| **`AGENTS.project.md`** | Authoritative repo-local overlay (roles, completion authority, Linear workflow, markers). |
| **`CLAUDE.md`** | Thin Claude/Cowork entrypoint; routes through `AGENTS.md` — do not duplicate long rule blocks here. |
| **`docs/coordinator-fleet.md`** | Cursor Cloud Agent / multi-agent branch and PR hygiene (distinct from supervisor queue execution). |

Parallel cloud or coordinator agents should read `docs/coordinator-fleet.md` before branching or opening a PR.
