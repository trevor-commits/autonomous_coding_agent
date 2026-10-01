#!/usr/bin/env bash
# Offline-friendly local verification aligned with .github/workflows/ci.yml.
# Requires Python 3.11+ and installed package deps (jsonschema, PyYAML, referencing).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: scripts/verify-local.sh [--governance-only | --help]

Runs the default local verification path for this repo:
  1. Ensure runtime imports resolve (editable install only if missing)
  2. unittest discover -s tests
  3. compileall supervisor tests
  4. governance smoke (required docs/sections)

Options:
  --governance-only   Skip tests and compileall; run governance smoke only.
  --help              Print this message and exit 0.

Optional environment (not part of default CI parity):
  ACA_RUN_LIVE_CODEX_TESTS=1   Enable live Codex containment tests (network/tools).
  macOS only: Seatbelt sandbox tests run automatically on Darwin.

Benchmark fixtures that point at an external target repo skip path checks when
that repo is absent (see fixtures/README.md).
EOF
}

governance_only=0
if [[ "${1:-}" == "--governance-only" ]]; then
  governance_only=1
elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
elif [[ -n "${1:-}" ]]; then
  usage >&2
  exit 2
fi

if ! python3 -c "import jsonschema, referencing, yaml" >/dev/null 2>&1; then
  echo "verify-local: installing editable package (needs network once)..." >&2
  python3 -m pip install -e .
fi

run_governance_smoke() {
  test -f AGENTS.md
  test -f AGENTS.project.md
  test -f CLAUDE.md
  test -f CONTINUITY.md
  test -f COHERENCE.md
  test -f LINEAR.md
  test -f PROJECT_INTENT.md
  test -f todo.md
  test -f pyproject.toml
  test -f docs/local-verification.md
  test -f scripts/verify-local.sh

  grep -q 'scripts/verify-local.sh' README.md

  grep -q '^## What To Read' CLAUDE.md
  grep -q '^## Repo Principles' AGENTS.project.md
  grep -q '^## Work Record Format' CONTINUITY.md
  grep -q '^## Active Next Steps' todo.md
  grep -q '^## Linear Issue Ledger' todo.md
  grep -q '^## Work Record Log' todo.md
  grep -q '^## Audit Record Log' todo.md
  grep -q '^## Test Evidence Log' todo.md

  # One canonical ## Repo Principles in AGENTS.project.md (prose block at top).
  test "$(grep -c '^## Repo Principles' AGENTS.project.md)" -eq 1

  # Live navigation/onboarding docs stay portable (GIL-12 subset enforced in CI).
  local nav_doc
  for nav_doc in GUIDE.md README.md AGENTS.md design-history/README.md; do
    if grep -q '/Users/gillettes/Coding Projects/Autonomous Coding Agent/' "$nav_doc"; then
      echo "verify-local: portability smoke failed — absolute ACA checkout path in ${nav_doc}" >&2
      exit 1
    fi
  done
}

if [[ "$governance_only" -eq 1 ]]; then
  run_governance_smoke
  echo "verify-local: governance smoke OK"
  exit 0
fi

python3 -m unittest discover -s tests -v
python3 -m compileall -q supervisor tests
run_governance_smoke
echo "verify-local: tests, compileall, and governance smoke OK"
