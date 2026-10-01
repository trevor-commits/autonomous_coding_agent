# Local verification

This page is the operator-facing companion to `scripts/verify-local.sh` and the Python jobs in [.github/workflows/ci.yml](../.github/workflows/ci.yml).

## Default path (CI parity)

From a fresh clone on Python 3.11+:

```bash
python3 -m pip install -e .
bash scripts/verify-local.sh
```

The script runs, in order:

1. Editable install **only when** `jsonschema`, `referencing`, or `PyYAML` imports are missing (network once).
2. `python3 -m unittest discover -s tests -v`
3. `python3 -m compileall -q supervisor tests`
4. Governance smoke — required files/sections plus navigation portability checks on `GUIDE.md`, `README.md`, `AGENTS.md`, and `design-history/README.md`.

Fast doc-only slice:

```bash
bash scripts/verify-local.sh --governance-only
```

## Optional gates (not CI parity)

| Gate | How |
| --- | --- |
| Live Codex containment probes | `ACA_RUN_LIVE_CODEX_TESTS=1 bash scripts/verify-local.sh` |
| macOS Seatbelt sandbox tests | Run on Darwin; picked up automatically by unittest |
| Benchmark fixtures against a real target repo | Checkout the external repo at the path expected by the fixture; see [fixtures/README.md](../fixtures/README.md) |

## Open draft PR survey (2026-10-01)

Surveyed **open draft** pull requests on `trevor-commits/autonomous_coding_agent` before this deeper pass. No merges, no Linear/todo landing, no live external writes.

| PR | Branch | Focus | Overlap with usage-burn |
| --- | --- | --- | --- |
| [#13](https://github.com/trevor-commits/autonomous_coding_agent/pull/13) | `cursor/usage-burn-reliability-b7b3` | `verify-local.sh`, CI parity, governance smoke repair, README/AGENTS portability | **This line** — deeper commits land on the same branch |
| [#12](https://github.com/trevor-commits/autonomous_coding_agent/pull/12) | `cursor/agents-harness-hygiene-7665` | Harness docs (`coordinator-fleet`, CLAUDE/AGENTS), `tests/test_agent_harness.py`, `todo.md` landing | Touches `AGENTS.md` / `GUIDE.md` — reconcile before merging both drafts |

**Recommendation:** Land usage-burn (#13) first for verify/CI truth, then rebase harness hygiene (#12) onto `main` and resolve any `AGENTS.md` / `GUIDE.md` conflicts.

## Still tracked elsewhere

- **GIL-12** — remaining absolute paths in some `docs/*.md` operator memos (plugin install paths, global policy paths) and all of `todo.md` historical Work Record prose.
- **GIL-44** — duplicate `## Repo Principles` heading removed in `AGENTS.project.md` (second block renamed); `SCOPING-three-pillar-principles.md` root file and stale `IMPLEMENTATION-PLAN.md` read-scope references remain open.
- **Linear / `todo.md` Work Record** — out of scope for cloud usage-burn; human closeout when Trevor promotes the draft.
