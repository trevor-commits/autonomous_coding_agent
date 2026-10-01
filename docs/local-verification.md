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

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success (`--governance-only` or full run) |
| `2` | Unknown CLI flag (see `--help`) |
| `1` | Test failure, missing governance file/section, or portability smoke failure |

### GitHub Actions matrix

The `python` job in `.github/workflows/ci.yml` runs `bash scripts/verify-local.sh` on **ubuntu-latest** for Python **3.11** and **3.12** only. Local parity is the same command on either version after `pip install -e .`.

## Expected unittest volume (offline clone)

After `pip install -e .`, a full run should end with **OK** and a small, stable skip set (no network, no secrets):

| Outcome | Typical count | Why skipped |
| --- | --- | --- |
| Tests run | **259** | Full `tests/` discover |
| Skipped | **12** | Live Codex (`ACA_RUN_LIVE_CODEX_TESTS` unset), macOS Seatbelt sandbox, external benchmark target-repo paths |

Re-baseline these numbers when adding or removing tests. Fast regression guards (no full discover):

- `tests/test_verify_local_entrypoint.py` — subprocess `--governance-only`, `--help`, unknown-flag exit `2`
- `tests/test_governance_portability.py` — mirrors shell portability loop and operator doc wiring
- `tests/test_ci_workflow_parity.py` — CI must delegate to `scripts/verify-local.sh` (no duplicated unittest/compileall steps)

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: jsonschema` (or `yaml`, `referencing`) | Editable install missing | `python3 -m pip install -e .` once (network) |
| `portability smoke failed — absolute ACA checkout path in …` | macOS-only checkout path in a live nav doc | Use repo-relative links in `GUIDE.md`, `README.md`, `AGENTS.md`, `design-history/README.md` (GIL-12 subset) |
| `AGENTS.project.md` must expose exactly one ## Repo Principles | Duplicate heading (GIL-44) | Keep a single `## Repo Principles` at the top; rename merged legacy blocks |
| Benchmark fixture path failures | External `gillette-website` (or override) absent | Expected on CI/clones — see [fixtures/README.md](../fixtures/README.md) |
| Full suite slow (~2–3 min) | Normal | Use `--governance-only` for doc edits; run full `verify-local.sh` before push |

Governance portability rules are enforced in both `scripts/verify-local.sh` and `tests/test_governance_portability.py`; keep `NAV_DOCS` in the Python test aligned with the shell loop.

| Check | `verify-local.sh --governance-only` | Full run + `tests/test_governance_portability.py` |
| --- | --- | --- |
| Required governance files / todo sections | yes | yes (via unittest after discover) |
| README / IMPLEMENTATION-PLAN / AGENTS.md → verify script | yes | yes |
| `GUIDE.md` quick-ref wiring | no (shell) | yes |
| `docs/local-verification.md` section contract | no (shell) | yes |
| CI workflow parity (no inline unittest) | grep in shell | `tests/test_ci_workflow_parity.py` |
| Nav doc portability (GIL-12 subset) | yes | yes |

## Offline verify recipe (cloud agent / fresh VM)

No Linear writes, no secrets, no merge. From repo root:

```bash
python3 -m pip install -e .
bash scripts/verify-local.sh
bash scripts/verify-local.sh --governance-only
python3 -m unittest \
  tests.test_verify_local_entrypoint \
  tests.test_governance_portability \
  tests.test_ci_workflow_parity -v
```

Expect full discover **259** tests, **12** skipped, exit **0**. Re-baseline counts in this doc when the suite size changes.

## Optional gates (not CI parity)

| Gate | How |
| --- | --- |
| Live Codex containment probes | `ACA_RUN_LIVE_CODEX_TESTS=1 bash scripts/verify-local.sh` |
| macOS Seatbelt sandbox tests | Run on Darwin; picked up automatically by unittest |
| Benchmark fixtures against a real target repo | Checkout the external repo at the path expected by the fixture; see [fixtures/README.md](../fixtures/README.md) |

## Open draft PR survey (2026-10-01, deepest pass + reliability lock)

Surveyed **open draft** pull requests on `trevor-commits/autonomous_coding_agent`. No merges, no Linear/todo landing, no live external writes, no secrets.

| PR | Branch | Focus | Overlap with usage-burn |
| --- | --- | --- | --- |
| [#13](https://github.com/trevor-commits/autonomous_coding_agent/pull/13) | `cursor/usage-burn-reliability-b7b3` | `verify-local.sh`, CI parity, governance smoke, portability, operator docs | **Canonical draft** — all usage-burn commits land here |
| [#12](https://github.com/trevor-commits/autonomous_coding_agent/pull/12) | `cursor/agents-harness-hygiene-7665` | Harness docs (`docs/coordinator-fleet.md`, CLAUDE/AGENTS), `tests/test_agent_harness.py`, `COHERENCE.md` / `todo.md` | Overlaps `AGENTS.md`, `GUIDE.md`, `IMPLEMENTATION-PLAN.md`, harness spec paths — rebase onto `main` after #13 |

### File-level overlap (#12 vs #13)

| Path | #13 | #12 | Merge note |
| --- | --- | --- | --- |
| `AGENTS.md` | verify wiring | harness read order | Reconcile harness text after verify links land |
| `GUIDE.md` | portable links + verify quick-ref | harness / fleet pointers | Prefer #13 nav portability; fold #12 fleet rows |
| `IMPLEMENTATION-PLAN.md` | verify-local + Python 3.11+ | harness prerequisites | Keep #13 verify block; merge #12 harness deltas |
| `README.md` | Local Runtime section | indexing | #13 owns verify truth |
| `docs/coordinator-fleet.md` | — | new/expanded | Lands with #12 only |
| `tests/test_agent_harness.py` | — | new | Run after rebase: `python3 -m unittest tests.test_agent_harness -v` |
| `todo.md` / `COHERENCE.md` | — | ledger / ripple | Human closeout; not part of usage-burn |

**Recommendation:** Land usage-burn (#13) first for verify/CI truth, then rebase harness hygiene (#12) and run the [offline verify recipe](#offline-verify-recipe-cloud-agent--fresh-vm) plus `python3 -m unittest tests.test_agent_harness -v`.

### Usage-burn pass additions on #13 (same branch)

- Governance smoke requires `docs/local-verification.md`, executable `scripts/verify-local.sh`, README + CI workflow pointers to the script.
- `tests/test_verify_local_entrypoint.py` — subprocess `--governance-only`, `--help`, unknown-flag exit `2`.
- `tests/test_ci_workflow_parity.py` — blocks CI drift back to inline `unittest` / `compileall`.
- `tests/test_governance_portability.py` — `GUIDE.md` quick-reference wiring and CI delegation checks.
- `IMPLEMENTATION-PLAN.md` prerequisites aligned to Python **3.11+** (`pyproject.toml`).
- This page: exit codes, CI matrix, expected skip matrix, troubleshooting, NAV_DOCS sync note.
- **Reliability lock (this pass):** shell smoke also requires `IMPLEMENTATION-PLAN.md` + `AGENTS.md` verify wiring; Python contract test for operator doc sections and test/skip baselines; `-h` parity test; enforcement table + offline cloud recipe above.

## Still tracked elsewhere

- **GIL-12** — remaining absolute paths in some `docs/*.md` operator memos (plugin install paths, global policy paths) and all of `todo.md` historical Work Record prose.
- **GIL-44** — duplicate `## Repo Principles` heading removed in `AGENTS.project.md` (second block renamed); `SCOPING-three-pillar-principles.md` root file and stale `IMPLEMENTATION-PLAN.md` read-scope references remain open.
- **Linear / `todo.md` Work Record** — out of scope for cloud usage-burn; human closeout when Trevor promotes the draft.
