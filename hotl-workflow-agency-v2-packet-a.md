---
intent: Implement ACA Agency v2 Packet A so the stateless partner accepts a bounded observation v2 wake contract without activating new producers, deliberation, or effects.
success_criteria: ACA validates v1 and v2 wakes exactly, enforces the frozen observation namespace, canonical hash, duplicate, timestamp, TTL, and compatibility rules, passes the complete verification stack, and receives an independent review-clean verdict.
risk_level: medium
auto_approve: true
branch: codex/agency-v2-packet-a
worktree: false
dirty_worktree: allow
---

## Maximum reliable work packet

- **Goal:** land ACA Packet A from the reviewed Agency v2 wire contract at global commit `4292f4efd4ce9c5a3586f51c63188c413e92025e`.
- **In scope:** an ACA OpenSpec delta; the observation v2 JSON schema; v1/v2 wake-schema compatibility; semantic validation for namespaces, canonical hashes, duplicates, RFC3339 timestamps, and collector TTLs; focused regression tests; schema documentation; and durable project records.
- **Out of scope:** global observation producers, global snapshot activation, deliberation receipts, reuse, effects, recurring execute, new authority, new storage, a second scheduler, raw/private-content ingestion, or changes to detached Stage 0 runtimes.
- **Risk controls:** test-first implementation, exact enum/namespace constraints, whole-wake rejection on any invalid observation, no observation-level opportunity score, no new dependency, one writer at a time, controller-owned integration, and independent read-only review.
- **Verification:** focused RED then GREEN tests, all partner contract tests, full unit suite, in-memory compilation, strict OpenSpec validation, schema parsing, project-memory validation, and whitespace/status checks.
- **Rollback:** disable use of wake schema v2 at the global caller; revert this single Packet A branch; leave the Stage 0 observe-only deployment pinned to its existing immutable SHAs.
- **Review path:** controller verifies every delegated diff and command, then a fresh read-only reviewer audits contract fidelity, security/privacy, compatibility, and scope before PR/merge.

## Steps

Completed HOTL run: `agency-v2-packet-a-20260715T085056Z` (7/7 verified). Ready PR #9 is open; merge containment, post-merge OpenSpec archive/Ripple Check, and branch cleanup are external landing gates rather than unfinished workflow steps.

- [x] **Step 1: Freeze the ACA Packet A OpenSpec delta**
action: Create the ACA `agency-v2-observation-contract` OpenSpec brainstorm, proposal, design, spec delta, tasks, and plan from the frozen global Packet A contract; explicitly preserve v1 compatibility and exclude producer activation, deliberation, and effects.
loop: until strict OpenSpec validation passes
max_iterations: 3
verify: openspec validate agency-v2-observation-contract --strict --no-interactive

- [x] **Step 2: Write observation v2 contract tests first**
action: Add focused failing tests for v2 schema acceptance, v1 unchanged behavior, exact collector and namespace rules, canonical NFC hash derivation, duplicate rejection, timestamp skew/order, collector TTL ceilings, unknown fields, and rejection of observation-level opportunity scores.
loop: false
verify:
  type: artifact
  path: records/verification/2026-07-15-agency-v2-packet-a-red.md
  assert:
    kind: contains
    value: "FAILED (errors=6)"

- [x] **Step 3: Implement the minimal v1 plus v2 contract**
action: Add the observation v2 schema, extend the wake schema only at the observation boundary, and implement dependency-free semantic validation that makes every Step 2 regression pass while preserving all v1 identity, goal, approval, maturity, and outcome behavior.
loop: until focused partner-contract tests pass
max_iterations: 5
verify: python3 -m unittest tests.test_partner_contracts -v

- [x] **Step 4: Reconcile contract documentation and durable state**
action: Update schema navigation, ACA OpenSpec tasks, project memory, todo active packet, Work Record, branch ledger, Feedback Decision, Ripple Check, and test-evidence surfaces with exact scope and honest non-activation claims.
loop: until repo governance validators pass
max_iterations: 3
verify: /Users/gillettes/.codex/scripts/validate-project-memory.sh .

- [x] **Step 5: Run the complete ACA verification stack**
action: Run schema parsing, focused tests, the full unit suite, no-bytecode in-memory compilation, strict OpenSpec validation, diff checks, and any repo verifier that applies; repair only owned Packet A failures.
loop: until all owned checks are green
max_iterations: 5
verify: python3 -m unittest discover -s tests -v

- [x] **Step 6: Run a fresh independent read-only audit**
action: Have a fresh non-writing reviewer compare the exact branch diff to the frozen global Packet A contract, with special attention to compatibility, canonicalization, hash projections, TTL/time boundaries, privacy, duplicate handling, and accidental scope expansion; record findings and disposition.
loop: until the independent verdict is review-clean
max_iterations: 4
verify:
  type: artifact
  path: records/audits
  assert:
    kind: matches-glob
    value: "*agency-v2-packet-a*.md"

- [x] **Step 7: Re-verify, commit, push, and open the Packet A PR**
action: Fix accepted audit findings with regressions, rerun immutable verification, complete OpenSpec verify and retrospective artifacts without archiving before merge, update exact durable evidence, commit only owned files, push the branch, open a reviewable PR, and prove remote-tip equality.
loop: until no actionable finding or uncommitted owned file remains
max_iterations: 4
verify: git status --short
