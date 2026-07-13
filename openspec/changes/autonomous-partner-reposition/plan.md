# Autonomous Partner Reposition Implementation Plan

> **For agentic workers:** execute through `hotl-workflow-autonomous-partner-reposition.md`; use fresh bounded workers only for isolated test/implementation/review slices, while the primary Codex session owns integration, shared files, verification, and git state.

**Goal:** Ship a persistent proactive partner by composing the existing global governor with a stateless partner policy and a hardened ACA episode executor.

**Architecture:** Global surfaces own identity, long-lived goals/observations, learning, benefit, heartbeat, approvals, and queue state. ACA consumes bounded snapshots, emits one typed decision, and executes only hash-bound authorized run contracts with truthful evidence.

**Tech Stack:** Python standard library plus existing PyYAML/jsonschema, JSON Schema, SQLite only where already present globally, Bash 3.2-compatible bridge code, OpenSpec, HOTL, unittest/pytest.

**Canonical micro-step source:** `hotl-workflow-autonomous-partner-reposition.md`. This plan binds those executable steps to OpenSpec tasks without duplicating action/verify/gate text.

---

## Task 1: Executor Evidence And Authority

- [x] **Step 1.1:** Add focused RED cases in `tests/test_main.py`, `tests/test_policy.py`, and `tests/test_run_store.py`; run each and capture the intended failure.
- [x] **Step 1.2:** Implement evidence-derived final rerun/artifact checks in `supervisor/main.py`; run focused GREEN and existing final-gate tests.
- [x] **Step 1.3:** Implement pre-worktree risk/approval validation in `supervisor/main.py`; prove builder/worktree calls remain zero on denial.
- [x] **Step 1.4:** Make unmatched commands fail closed in `supervisor/policy.py`; keep exact repo-contract commands allowed.
- [x] **Step 1.5:** Reconcile actual `git status --porcelain` paths in `supervisor/main.py`; prove an omitted forbidden path blocks.
- [x] **Step 1.6:** Implement same-directory fsync plus atomic replace in `supervisor/run_store.py`; prove failed publish preserves prior JSON.
- [x] **Step 1.7:** Run `python3 -m unittest tests.test_main tests.test_policy tests.test_run_store` and refactor without changing behavior.
- [ ] **Step 1.8:** Commit the coherent executor-hardening outcome with its tests and OpenSpec task updates.

## Task 2: Partner Identity, Initiative, And Learning Policy

- [ ] **Step 2.1:** Add global `config/autonomous-partner/identity.yml` plus ACA JSON schemas for identity, snapshot, decision, approval, envelope, outcome, and lesson candidate.
- [ ] **Step 2.2:** Add RED schema/hash/privacy cases in `tests/test_partner_contracts.py`.
- [ ] **Step 2.3:** Implement typed loaders/canonical hashes in `supervisor/partner_contracts.py`; run GREEN.
- [ ] **Step 2.4:** Add RED scoring/tie/staleness/project-kind cases in `tests/test_partner_initiative.py`.
- [ ] **Step 2.5:** Implement deterministic ranking in `supervisor/partner_initiative.py`; run GREEN.
- [ ] **Step 2.6:** Add RED capability/maturity/approval/identity-no-authority/idempotency cases in `tests/test_partner_authority.py` and `tests/test_partner_runtime.py`.
- [ ] **Step 2.7:** Implement one-decision stateless policy in `supervisor/partner_policy.py`; run GREEN.
- [ ] **Step 2.8:** Add RED/GREEN benefit and lesson-candidate logic in `tests/test_partner_learning.py` and `supervisor/partner_learning.py`.
- [ ] **Step 2.9:** Add RED/GREEN JSON CLI cases in `tests/test_partner_cli.py` and `supervisor/partner_cli.py`.
- [ ] **Step 2.10:** Run all partner tests, full ACA tests, and commit the coherent partner-policy outcome.

## Task 3: Global Bridge And Governed Dispatch

- [ ] **Step 3.1:** Add RED cases in `scripts/autonomous-partner-bridge.test.sh` for discovery, timeout, schema/hash/binding, kill-switch race, and no-clobber publish.
- [ ] **Step 3.2:** Implement `scripts/autonomous-partner-bridge` and the ACA runner adapter using explicit absolute paths and bounded JSON output.
- [ ] **Step 3.3:** Extend `scripts/autonomous-loop` only at its documented runner/receipt seam; do not change scheduler, selection, lock, or packet ownership.
- [ ] **Step 3.4:** Wire existing identity/goals/observations/benefit/memory inputs and approval/lesson outputs without adding a second long-lived state store.
- [ ] **Step 3.5:** Run bridge, autonomous-loop, health, global verifier, and cross-repo compatibility checks; commit the coherent bridge outcome.

## Task 4: Live Proof, Independent Audit, And Landing

- [ ] **Step 4.1:** Reconcile ACA/global canonical docs, runbooks, ledgers, dependency maps, and project memory.
- [ ] **Step 4.2:** Run full ACA/global automated verification and freeze relevant hashes.
- [ ] **Step 4.3:** Run the isolated live observe/proposal/deny/approve/envelope/outcome/lesson/kill-switch pilot and write durable evidence.
- [ ] **Step 4.4:** Start a fresh read-only audit session against the frozen branches, rerun its evidence, and record findings.
- [ ] **Step 4.5:** Add regressions and fixes for every accepted finding; repeat audit until review-clean.
- [ ] **Step 4.6:** Complete `verify.md`, `retrospective.md`, OpenSpec archive, Ripple Check, completion/test/audit records, scoped commits/pushes, and remote containment verification.
