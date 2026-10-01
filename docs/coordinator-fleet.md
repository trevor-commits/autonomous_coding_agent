# Coordinator fleet (Cursor Cloud Agents and similar)

Multiple autonomous agents often work the same autonomous_coding_agent checkout (Cursor Cloud Agents, Codex coordinator runs, or parallel audit/repair lanes). Keep collisions predictable.

## One branch, one PR

- Each agent run uses its **own** git branch (`cursor/<topic>-<suffix>` on Cloud Agents).
- Commit and push on that branch only; open **one draft PR per branch**. Do not reuse another agent's branch without explicit handoff.
- Before merging, rebase onto current `main` if the branch sat idle — stale branches can miss recent governance or runtime fixes.

## Shared rules, not duplicated prose

- Root **`AGENTS.md`** is the thin bootstrap pointer (global read order + local authority).
- **`AGENTS.project.md`** is the authoritative repo-local overlay (roles, completion authority, Linear workflow, markers).
- **`CLAUDE.md`** stays thin and routes through `AGENTS.md`; do not fork long rule blocks into `CLAUDE.md`.

Repo-specific gates (Continuity, Ripple Check, Linear-coverage) live in `CONTINUITY.md`, `COHERENCE.md`, and `LINEAR.md` — update them in the same commit when harness or workflow docs change.

## Supervisor queue fleet (different concern)

Unattended **supervisor-mediated queue** execution (`QUEUE-RUNS.md`, `python3 -m supervisor.main queue …`) is a separate runtime lane from IDE/cloud agents. Queue runs consume Linear issues with `Execution lane: Codex` and `Execution mode: Queue`; they do not share branch naming with Cloud Agent runs. Do not assume a queue worktree and a Cloud Agent branch are coordinated unless `todo.md` `Active Branch Ledger` says so.

## Cloud Agent environment

- Read `AGENTS.md` then `AGENTS.project.md` before planning or landing.
- Python 3.11+; run tests with `python3 -m unittest discover -s tests -v` (or the narrowest module named in the task).
- No secrets in commits, PR bodies, or logs; keep credentials in operator-local stores only.

## When two agents touch the same subsystem

Prefer **serial ownership** (one agent on `supervisor/`, another on docs-only). If both must edit the same files, merge `main` frequently and keep PRs small so review can see overlap early.
