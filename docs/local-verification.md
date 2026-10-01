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

`bash scripts/verify-local.sh --help` prints the same usage text.

## Expected unittest volume (offline clone)

After `pip install -e .`, a full run should end with **OK** and a small, stable skip set (no network, no secrets):

| Outcome | Typical count | Why skipped |
| --- | --- | --- |
| Tests run | **257** | Full `tests/` discover |
| Skipped | **12** | Live Codex (`ACA_RUN_LIVE_CODEX_TESTS` unset), macOS Seatbelt sandbox, external benchmark target-repo paths |

Re-baseline these numbers when adding or removing tests; `tests/test_verify_local_entrypoint.py` only checks the governance subprocess path.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: jsonschema` (or `yaml`, `referencing`) | Editable install missing | `python3 -m pip install -e .` once (network) |
| `portability smoke failed — absolute ACA checkout path in …` | macOS-only checkout path in a live nav doc | Use repo-relative links in `GUIDE.md`, `README.md`, `AGENTS.md`, `design-history/README.md` (GIL-12 subset) |
| `AGENTS.project.md` must expose exactly one ## Repo Principles | Duplicate heading (GIL-44) | Keep a single `## Repo Principles` at the top; rename merged legacy blocks |
| Benchmark fixture path failures | External `gillette-website` (or override) absent | Expected on CI/clones — see [fixtures/README.md](../fixtures/README.md) |
| Full suite slow (~2–3 min) | Normal | Use `--governance-only` for doc edits; run full `verify-local.sh` before push |

Governance portability rules are enforced in both `scripts/verify-local.sh` and `tests/test_governance_portability.py`; keep `NAV_DOCS` in the Python test aligned with the shell loop.

## Optional gates (not CI parity)

| Gate | How |
| --- | --- |
| Live Codex containment probes | `ACA_RUN_LIVE_CODEX_TESTS=1 bash scripts/verify-local.sh` |
| macOS Seatbelt sandbox tests | Run on Darwin; picked up automatically by unittest |
| Benchmark fixtures against a real target repo | Checkout the external repo at the path expected by the fixture; see [fixtures/README.md](../fixtures/README.md) |

## Open draft PR survey (2026-10-01, deeper pass)

Surveyed **open draft** pull requests on `trevor-commits/autonomous_coding_agent`. No merges, no Linear/todo landing, no live external writes, no secrets.

| PR | Branch | Focus | Overlap with usage-burn |
| --- | --- | --- | --- |
| [#13](https://github.com/trevor-commits/autonomous_coding_agent/pull/13) | `cursor/usage-burn-reliability-b7b3` | `verify-local.sh`, CI parity, governance smoke, portability, operator docs | **Canonical draft** — all usage-burn commits land here |
| [#12](https://github.com/trevor-commits/autonomous_coding_agent/pull/12) | `cursor/agents-harness-hygiene-7665` | Harness docs (`docs/coordinator-fleet.md`, CLAUDE/AGENTS), `tests/test_agent_harness.py`, `COHERENCE.md` / `todo.md` | Overlaps `AGENTS.md`, `GUIDE.md`, `IMPLEMENTATION-PLAN.md`, harness spec paths — rebase onto `main` after #13 |

**Recommendation:** Land usage-burn (#13) first for verify/CI truth, then rebase harness hygiene (#12) and run `bash scripts/verify-local.sh` plus `python3 -m unittest tests.test_agent_harness -v`.

### Deeper pass additions (same branch)

- Governance smoke requires `docs/local-verification.md`, executable `scripts/verify-local.sh`, and a README pointer to the script.
- `tests/test_verify_local_entrypoint.py` — subprocess `--governance-only` and `--help` (fast regression guard).
- `IMPLEMENTATION-PLAN.md` prerequisites aligned to Python **3.11+** (`pyproject.toml`).
- This page: expected skip matrix, troubleshooting, NAV_DOCS sync note.

## Still tracked elsewhere

- **GIL-12** — remaining absolute paths in some `docs/*.md` operator memos (plugin install paths, global policy paths) and all of `todo.md` historical Work Record prose.
- **GIL-44** — duplicate `## Repo Principles` heading removed in `AGENTS.project.md` (second block renamed); `SCOPING-three-pillar-principles.md` root file and stale `IMPLEMENTATION-PLAN.md` read-scope references remain open.
- **Linear / `todo.md` Work Record** — out of scope for cloud usage-burn; human closeout when Trevor promotes the draft.
