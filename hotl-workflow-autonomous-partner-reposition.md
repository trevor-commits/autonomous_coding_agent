---
intent: Reposition the tested autonomous coding harness as the bounded executor beneath a persistent, proactive, creative, learning partner without creating a second scheduler or weakening deterministic authority.
success_criteria: Identity, durable goals, governed initiative, learning, one-packet wakes, global heartbeat integration, live pilot evidence, and a fresh independent audit are all green.
risk_level: high
auto_approve: true
branch: codex/autonomous-partner-reposition-20260713
worktree: true
dirty_worktree: allow
---

## Maximum reliable work packet

- **Goal:** ship the complete L1/L2 partner path and L3 promotion machinery defined in `docs/designs/autonomous-partner.md`.
- **In scope:** executor safety hardening; global identity/goals/learning integration; stateless initiative and authority policy; CLI; executor envelopes; global bridge; health/receipts; live pilot; docs; tests; independent audit; and repair.
- **Out of scope:** a second scheduler/control plane, covert transcript ingestion, auto-publish/payment/credentials/destructive actions, multi-writer execution, or pretending that configured personality is consciousness.
- **Risk controls:** TDD, schema-bound crossings, truthful final-gate evidence, unattended-authority preflight, default-deny shell policy, actual-diff reconciliation, atomic run truth, one packet per wake, kill switches, isolated worktrees, immutable receipts, no-new-dependency default, and empirical promotion thresholds.
- **Verification:** focused red/green tests, full suite, global bridge hermetic suite, live bounded pilot, Ripple Check, OpenSpec strict validation, and fresh-session adversarial review.
- **Rollback:** disable the bridge; set the existing kill switch; remove queued partner packets; revert the two scoped branches; retain append-only receipts for diagnosis.
- **Review path:** Codex self-audit, independent clean-session code/safety/spec audit, fixes, and repeated review until clean.

## Steps

- [x] **Step 1: Reconcile the request and planning surfaces**
action: Extend ER-141 with Trevor's expanded partner, creativity, growth, love-as-practice, and full-build request; add branch/work records in both repos; initialize the OpenSpec change and bind it to this design.
loop: until enforcement and OpenSpec parity checks pass
max_iterations: 3
verify: openspec validate --all --strict --no-interactive

- [x] **Step 2: Write executor truth and authority regression tests**
action: Add failing tests for false final-gate evidence, approval-required and high-risk direct-run rejection before worktree creation, default denial of unknown commands, actual-diff scope mismatch, and crash-safe atomic run-state writes.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_main.py" -v && ! python3 -m unittest discover -s tests -p "test_policy.py" -v && ! python3 -m unittest discover -s tests -p "test_run_store.py" -v
gate: human

- [x] **Step 3: Harden executor truth and authority boundaries**
action: Make final readiness derive from real artifacts and authoritative reruns; reject unsafe unattended contracts before effects; default unknown commands to escalate; reconcile real diffs; and write run truth atomically.
loop: until executor safety regressions pass
max_iterations: 5
verify: python3 -m unittest discover -s tests -p 'test_main.py' -v && python3 -m unittest discover -s tests -p 'test_policy.py' -v && python3 -m unittest discover -s tests -p 'test_run_store.py' -v
gate: human

- [ ] **Step 4: Write partner identity and snapshot contract tests**
action: Add failing tests for global identity schema validation, stable hashing, configured-versus-inferred labels, approved amendment overlays, bounded snapshot fields, and rejection of raw private content or secrets.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_partner_contracts.py" -v
gate: human

- [ ] **Step 5: Implement identity and stateless snapshot contracts**
action: Add the global bootstrap Partner profile plus ACA schemas/loaders for bounded identity, goals, observations, approvals, maturity statistics, and executor outcomes; do not add another partner database.
loop: until partner contract tests pass
max_iterations: 4
verify: python3 -m unittest discover -s tests -p 'test_partner_contracts.py' -v
gate: human

- [ ] **Step 6: Write initiative and creativity scoring tests**
action: Add failing tests for benefit, harm prevention, interest fit, novelty, effort, confidence, risk, staleness, project kinds, and deterministic tie-breaking.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_partner_initiative.py" -v

- [ ] **Step 7: Implement initiative selection**
action: Implement typed evidence-backed proposal generation and deterministic ranking for utility, repair, research, care, and creative projects.
loop: until initiative tests pass
max_iterations: 4
verify: python3 -m unittest discover -s tests -p 'test_partner_initiative.py' -v

- [ ] **Step 8: Write authority-gate adversarial tests**
action: Add failing tests proving personality, interests, model text, ambiguous approvals, and high scores cannot authorize outward, credential, payment, destructive, identity-change, or policy-change effects.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_partner_authority.py" -v
gate: human

- [ ] **Step 9: Implement default-deny authority**
action: Implement capability classification, maturity-level rules, empirical promotion thresholds, kill-switch checks, explicit approval binding, and reason-coded denials.
loop: until authority tests pass
max_iterations: 4
verify: python3 -m unittest discover -s tests -p 'test_partner_authority.py' -v
gate: human

- [ ] **Step 10: Write decision and idempotency tests**
action: Add failing tests for unhealthy/busy/no-evidence no-ops, max-one proposal or executor envelope, duplicate wake keys, stale evidence, budgets, immutable hashes, and no long-lived state mutation in ACA.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_partner_runtime.py" -v
gate: human

- [ ] **Step 11: Implement the stateless partner decision runtime**
action: Combine the supplied global identity/goals/observations/outcomes snapshot with initiative and authority policy to emit one typed no-op, proposal, executor envelope, or lesson candidate without scheduling or storing global truth.
loop: until decision-runtime tests pass
max_iterations: 5
verify: python3 -m unittest discover -s tests -p 'test_partner_runtime.py' -v
gate: human

- [ ] **Step 12: Write outcome-learning candidate tests**
action: Add failing tests for executor receipt reconciliation, measured benefit, goal progression suggestions, scoped lesson candidates, expiry, contradiction handling, and gated identity-amendment proposals.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_partner_learning.py" -v

- [ ] **Step 13: Implement outcome-derived learning candidates**
action: Convert executor outcomes into provenance-bound benefit and lesson candidates for the existing global memory/improvement layer while keeping identity/value amendments approval-gated.
loop: until learning-candidate tests pass
max_iterations: 4
verify: python3 -m unittest discover -s tests -p 'test_partner_learning.py' -v

- [ ] **Step 14: Write CLI contract tests**
action: Add failing tests for init, observe, add-goal, propose, approve, wake, reconcile, status, and machine-readable error/receipt output.
loop: false
verify: ! python3 -m unittest discover -s tests -p "test_partner_cli.py" -v
gate: human

- [ ] **Step 15: Implement the operator and governor CLI**
action: Add a dependency-free CLI that exposes partner operations, defaults to observe-only, emits JSON, and never accepts secrets as arguments.
loop: until CLI tests pass
max_iterations: 4
verify: python3 -m unittest discover -s tests -p 'test_partner_cli.py' -v
gate: human

- [ ] **Step 16: Write global bridge tests**
action: In the isolated global branch, add failing hermetic tests for bridge discovery, partner timeouts, JSON validation, kill-switch inheritance, one-packet queueing, and receipt binding.
loop: false
verify: bash scripts/autonomous-partner-bridge.test.sh

- [ ] **Step 17: Implement the thin global bridge**
action: Add the bridge and extend the existing autonomous heartbeat to invoke it without becoming a second scheduler or inventing unapproved work.
loop: until bridge and autonomous-loop tests pass
max_iterations: 5
verify: bash scripts/autonomous-partner-bridge.test.sh && bash scripts/autonomous-loop.test.sh && bash scripts/autonomous-loop-health.test.sh
gate: human

- [ ] **Step 18: Reconcile canonical docs and schemas**
action: Update source-of-truth architecture, intent, rules, structure, navigation, runbook, schemas, OpenSpec artifacts, project memory, todo records, and dependency maps without rewriting design history.
loop: until repo and OpenSpec validators pass
max_iterations: 4
verify: openspec validate --all --strict --no-interactive

- [ ] **Step 19: Run the complete automated verification stack**
action: Run compilation, focused partner suites, the entire existing test suite, global policy/repo verifiers, shell syntax, ShellCheck where available, and whitespace checks; repair owned failures.
loop: until all owned checks are green
max_iterations: 6
verify: python3 -m compileall -q supervisor tests && python3 -m unittest discover -s tests -v

- [ ] **Step 20: Run a live bounded partner pilot**
action: Use isolated runtime state to prove observe, self-proposal, denied pre-approval dispatch, explicit approval, one queued sandbox packet, executor outcome reconciliation, learning, and kill-switch behavior with durable receipts.
loop: until the live pilot evidence is internally consistent
max_iterations: 4
verify:
  type: artifact
  path: records/verification
  assert:
    kind: matches-glob
    value: "*autonomous-partner*p*.md"
gate: human

- [ ] **Step 21: Run a fresh independent audit**
action: Start a clean read-only agent session to audit architecture, code, schemas, tests, privacy, safety, live evidence, docs, scope, and rollback against this design; record every finding.
loop: until the independent verdict is review-clean
max_iterations: 5
verify:
  type: artifact
  path: records/audits
  assert:
    kind: matches-glob
    value: "*autonomous-partner*.md"
gate: human

- [ ] **Step 22: Repair, re-verify, archive, and land**
action: Fix all accepted findings with regressions, rerun immutable verification, complete OpenSpec verify/retrospective/archive plus Ripple Check, commit scoped files, push both branches, and verify remote containment.
loop: until no actionable finding or uncommitted owned file remains
max_iterations: 6
verify: git status --short
gate: human
