# AGENTS.md (Autonomous Coding Agent)

This root file intentionally stays thin so repo-local policy does not drift from the global stack.

## Required Read Order
1. Global policy: `~/.codex/AGENTS.md` when present on the operator machine (typical Codex home on macOS). Linux and cloud checkouts without that tree skip to item 2.
2. `AGENTS.project.md` — authoritative repo-local overlay for this repository
3. `PROJECT_INTENT.md`
4. `PROJECT_MEMORY.md` — shared cross-AI project memory; schema: `.project-memory.schema.yaml`; global write policy: `~/.codex/policies/PROJECT_MEMORY.md` when present
5. `todo.md`

## Local Authority
- `AGENTS.project.md` is the authoritative repo-local overlay for this repository.
- Do not treat this file as a second copy of the global AGENTS policy.
- Keep repo-specific edits in `AGENTS.project.md` so the root file remains a stable pointer.

## Local verification
- From a fresh clone: `python3 -m pip install -e .` then `bash scripts/verify-local.sh` (matches the Python jobs in `.github/workflows/ci.yml`).
