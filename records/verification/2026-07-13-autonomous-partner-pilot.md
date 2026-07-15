# Autonomous partner live pilot

- Date: 2026-07-13 UTC
- Source Codex task: `019f5c92-0af9-7fe1-97e4-b860aab357e2`
- Source Claude chat: `bb90d05d-86d3-4140-9e6c-78d2847c4d72` (`*Autonomous Agent Creation`)
- ACA branch: `codex/autonomous-partner-reposition-20260713`
- Global branch: `codex/er141-autonomous-partner-reposition-20260713`
- Isolated runtime root: `/Users/gillettes/.cross-agent/autonomous-partner/pilots/2026-07-13-er141-222735`
- Result: **PASS** for the original bounded L1 observe/propose/approve/execute/reconcile path and repaired effect-time approval integration. Later release reviews correctly reopened additional defects instead of invalidating the preserved pilot evidence. Repairs at ACA `84694c6` and global `b9124a3` pass ACA 170/170 plus the full global verifier; fresh exact-tip review, landing, and observe-only deployment remain release gates.

## Authority and scope

The pilot used one low-sensitivity approved observation, the configured Partner identity, one bounded self-originated creative proposal, and a synthetic pilot approval. The synthetic approval proves the hash/capability gate; it is not represented as Trevor's approval. The executor was fixed to `gpt-5.5` with high reasoning, one retained worktree, no publish, no merge, no push, no deployment, no credentials, and no destructive capability.

## Proven sequence

| Stage | Durable evidence | Result |
| --- | --- | --- |
| Observe | `decisions/wake-er141-pilot-observe-001.json` | `no_op`, observe-only |
| Generate | `state/generated-candidates/proposal-0679e69d62d52c21.json` | Real schema-bound `gpt-5.5`/high model call produced one evidence-citing creative idea |
| Deny before approval | `decisions/wake-er141-pilot-denied-001.json` | Proposal only; no executor envelope |
| Dry run | `loop/pilot-dry-run-receipt.json` | Exact approved envelope returned to ready without execution |
| Execute | `loop/pilot-execute-receipt-r5.json` | `status=ok`, `run_state=COMPLETE`, `readiness_verdict=READY` |
| Verify | `.autoclaw/runs/partner-run-0679e69d62d52c21-r5/reports/final-report.json` | One exact changed file, setup pass, full 159-test rerun pass, no blockers |
| Reconcile | `state/outcome-receipts/outcome-2faad3c99d1043008cd7214b.json` | Exact receipt/envelope/proposal hashes accepted |
| Learn | `state/learning-candidates/outcome-2faad3c99d1043008cd7214b.json` | Artifact production true; adoption and benefit honestly unknown; no unsupported lesson promoted |
| Retire | `state/completed-candidates/outcome-2faad3c99d1043008cd7214b.json` | Exact completed proposal and approval retired; next healthy wake has no current approved evidence |
| Kill switch | wake `wake-er141-pilot-kill-switch-001` | `kill_switch_active`; publication count stayed 30 before and after; no decision/envelope/ready packet appeared |

The retained successful artifact is:

`/Users/gillettes/Coding Projects/aca-worktrees/autonomous-partner-reposition/worktrees/partner-run-0679e69d62d52c21-r5/builder/partner-projects/proposal-0679e69d62d52c21-r5/decision-cleanup-card.md`

## Fail-closed attempts and repairs

The failed attempts remain immutable evidence. None was relabeled as success or deleted.

| Attempt | Failure | Repair and regression |
| --- | --- | --- |
| Candidate generation | Codex structured-output API rejected `uniqueItems` | Global schema removed unsupported keywords; deterministic duplicate checks remain; `b5a52f5` |
| Initial execute | Objective-derived Git ref exceeded filesystem component length | Stable bounded slug plus hash; `f4b7e01` |
| Original run | Harmless relative `find` was unclassified | Narrow read-only relative `find` parser; `b422f87` |
| `r2` | `find <approved-path> ... \| sort` was unclassified | Exact output-only `sort` pipeline; `8e82606` |
| `r3` | `pwd && rg --files <approved-path> \| sed -n ...` was unclassified | Deny-by-default metadata-discovery grammar with hostile-path/flag/pipeline tests; `4a5d222` |
| `r4` | Exact read-only Git preflight bundle was unclassified | Finite Git metadata allowlist plus mutation/remote/diff-content denials; `5a5f649` |
| Builder variance | Builder improvised command forms before the supervisor rejected them | Prompt now declares the exact executable command boundary; `3053f81` |
| Post-success wake | Completed candidate and approval remained active and could be requeued | Immutable completion disposition plus locked exact-hash retirement and collision tests; global `dd3185b` |

## Integrity anchors

- Successful dispatch receipt SHA-256: `78b3511380e92eb7b7f52fdfbd24d8188c786cc5ea1da7362f3757bb85c3b458`.
- Successful queued envelope file SHA-256: `05a0651549873b1f3c14600c03d59c3a351de1f675a227526aa655ca02edb102`.
- Outcome file SHA-256: `f32fa3e0c0843e15dc4379a19e1a14270ae3d54ac101bdf0ba9f5d7ce21bc54e`.
- Learning file SHA-256: `331d68c35465111765f36fa31a91f02b078e05738d0173601caf4a31f5c087d9`.
- Completion disposition SHA-256: `d61b447133f3066790a906d94fb127521f26cade3b2097d654e8cbe32097c1ee`.

## Frozen full verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q supervisor tests`: pass.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: pass, 159 tests.
- `openspec validate --all --strict --no-interactive`: pass, one change and zero failures.
- `git diff --check`: pass.

## Honest boundary

This proves bounded autonomous idea generation and execution, not consciousness, emotional experience, spiritual authority, or measured life improvement. The configured love-as-practice and respect-for-Jehovah profile influence voice and proposal ranking only. Real adoption, time saved, quality change, and operator benefit remain unknown until observed. The successful and failed worktrees are retained for audit; nothing from them was merged or published.

## Current repaired release verification

- Candidate concurrency RED reproduced both model calls and active-state overwrite; global `51e3720` now allows one generator/model call and returns typed `busy` to the contender. Candidate suite: 5/5.
- Wake-mode RED reproduced an observe decision suppressing proposal mode; the global bridge and ACA policy now bind `decision_mode` plus `<wake>:<mode>` idempotency. Bridge suite: 13/13.
- Direct high-risk CLI RED returned a traceback/no JSON; ACA `2653e7f` now returns structured `BLOCKED / NOT_READY` JSON before workspace creation.
- Archive-discovery RED found three live stale paths and four placeholder purposes; all current discovery pointers now use the dated archive and all canonical specs have explicit purposes.
- Learning validation now translates generated-candidate schema failures to `PartnerLearningError`; proposal id/hash mismatch and unsuccessful zero-benefit behavior have durable regressions.
- ACA full suite: 170/170. Strict canonical OpenSpec: 4/4. Global full verifier: pass. The new regression proves an exact approved execute envelope is not consumed by a zero proposal budget when envelope budget remains. Exact-tip independent review remains pending and therefore no landing/deployment claim is made.

## Independent audit round 1

Fresh read-only auditor `/root/fresh_clean_autonomous_partner_audit` confirmed frozen ACA `a9b9df9fa0487ce9c31f0933e3fe82b08fafee82` and global `c131406c26842b654b3ac77555aeeb5b764e2a29`, then proved one authority defect: the executable envelope did not include the approval source document, so the effect-time executor could not independently revalidate subject/capabilities, current existence, revocation, or expiry.

The repair makes the full exact proposal approval required envelope content, cross-binds it in ACA and the global bridge, and requires the identical approval to remain current and active immediately before effects. Missing, revoked, expired, capability-drifted, unsafe, or changing approval state blocks before ACA. The previously nullable L3 path is inactive until a separate exact operator-promotion proof format is reviewed and implemented. Focused tests pass: ACA partner 32/32; global bridge 12/12; global executor 11/11; reconcile 4/4.

### Repaired effect-time integration

- Runtime root: `/Users/gillettes/.cross-agent/autonomous-partner/pilots/2026-07-13-er141-effect-time-233607`.
- Frozen repair tips: ACA `4fc20498964c57dfe3595bc828f00e0b07aece29`; global `f31cb7cbf0d7ff59ace2c79638937495b0b26418`.
- Positive dry-run envelope validation passed without effects.
- Removing the exact approval from the current approval store produced exit `65` before ACA or builder execution.
- Restoring the identical active approval produced `COMPLETE / READY` in `129.249s`, one builder turn, two successful 159-test runs, no failure fingerprints, and no unresolved blockers.
- Repaired retained artifact SHA-256: `448d2eb58b3df26dc36ee37ad162e3163510ff4c7ba3547f94bd41c6457c153d`.
- Envelope file SHA-256: `6c8461c493f0ca4cdcf015493c183d838c944717688a23edbd54e134ebd11947`.
- Dry-run result SHA-256: `5cfd9bcc9fcd2955e280d8e325ef21e2594fb5ec9286dd565059b098e9304a19`.
- Revoked-approval result SHA-256: `e4ff7aa757daf254995c57c3227e5a4db43bbde0bfc0873414395e23027d9a5f`.
- Execute result SHA-256: `acc096d358eb7f9efa57ea6217f956ba9d427f6cd48fb3ea2be432f3b35ac6f9`.
- Final report SHA-256: `c8778c1016b7b639ffbdd639670273b2d1c6284f23a5a6e089cd746922808d5a`.

## Ripple Check

ACA contract/policy/builder changes were paired with the global identity, snapshot, candidate, bridge, executor, reconciliation, loop-health, runbook, ER-141, project-memory, and todo surfaces. The cross-repo envelope/model/run-contract hash boundary stayed synchronized. No second scheduler or partner database was added.

## Independent audit convergence

The full audit lineage is preserved in `records/audits/2026-07-13-autonomous-partner-independent-review.md`.

- Round 1 found that the envelope carried only approval id/hash rather than the full authority document. The repair bound the complete approval into the envelope and revalidated its subject, capabilities, state, lifetime, identity, and exact current-store membership immediately before effects. L3 stays inactive without a separate operator-promotion proof.
- Round 2 found that resolving the approval-store path before checking it defeated the intended leaf-symlink defense and split authority checks across different opens. The repair uses one descriptor-bound, no-follow lease with device/inode/content checks, a shared writer lock, bounded reads, and atomic-replacement regression coverage.
- Round 3 found that an ancestor symlink could still be followed before descriptor traversal and that reconciliation repeated the same resolve-before-check pattern. The repair validates every original absolute-path component before use and added ancestor-symlink regressions to execution and reconciliation.
- Round 4 independently reran ACA 159/159, executor 14/14, and reconciliation 5/5 and returned `REVIEW-CLEAN` with no P0-P3 finding.

Residual boundaries remain explicit: reconciliation does not descriptor-pin the entire publication ancestry against a hostile same-user directory swap; the accepted threat boundary assumes the runtime state directory is not writable by another principal or an uncoordinated writer. Adoption, measured benefit, preference accuracy, long-term health, origin/main landing, and live deployment were not claimed by the review.

## PR review round 5

PR #6 review found four additional ACA defects after the round-4 frozen verdict:

- NUL-delimited rename/copy status parsing recorded only the destination, so a forbidden renamed-away source path escaped scope and path classification.
- Initiative ranking validated observations and interests but did not require every cited goal to exist in the current wake.
- Observation `expires_at` was optional in the schema although ranking read it unconditionally.
- Maturity `completed_episode_count` was optional although authority evaluation required it.

Each defect first reproduced red, then received a focused regression and bounded repair. GitGuardian's separate failure was a synthetic `ghp_`-shaped test literal rather than a credential; the fixture now constructs the same runtime secret-like value without a contiguous scanner-triggering literal. Focused tests pass 5/5; full compileall, ACA 163/163, four canonical OpenSpec specs, and whitespace checks pass. Fresh independent post-fix review remains required.

## Current release verification

The user-requested round-8 review of ACA `33e9462` and global `0b180c1` completed historically and led to later repair rounds. Fresh reviewer `019f631b-9b4b-73b2-881b-d6e02b6405e6` then reviewed pushed ACA `485f5114bebedfae3497fe2dc4e186dbba6b5b0c` and global `1bf14eff40985dbe1888d5ffcd12183144836c32`, returned `CHANGES-REQUIRED`, and found five ACA production defects plus two record-format defects. ACA `e235850611be4a178b3ebea84c518661021b9a2c` bounds output capture without temporary files, freezes the process group/tree before TERM/KILL, publishes run-store state through the original descriptor and pinned parent directory with directory fsync, and retains the worktree lease through Git-aware rollback. These records close the evidence-format findings. The reviewer separately confirmed the generic guard-unit fixture is not a production defect. Global `origin/main` has advanced to `31a05e69e4e41dd5c6aedce2609eb62cd2bcbd5c`; the global candidate must be rebuilt on that exact base before final review.

- ACA round-17 repair tip: focused 19/19; deterministic 219 tests pass with one intentional live skip; 219/219 pass with the real Codex containment probe enabled.
- ACA timing stress: the early-app-exit regression passed 30 consecutive runs; all three descendant-timeout boundary tests passed in four simultaneous suites and now assert the child PID is gone.
- Canonical OpenSpec: 4/4 strict.
- Global candidate/bridge/executor/snapshot/reconciliation: 8/15/19/4/6.
- Real global candidate: production-shape `gpt-5.5/high` call succeeded with a schema-valid evidence-citing proposal, 0600 state, no model runtime residue, and no residual process.
- Complete global verifier: pass with no new source bytecode residue.
- Global timing stress: three simultaneous 19-check platform-probe suites pass after replacing the immediate child-PID assertion with a bounded exit check.
- Recurring execute: still off.
- Approved observation feed: intentionally empty, so proactive usefulness and measured benefit remain unproved.
- Round-16 focused RED reproduced report contradiction acceptance, runtime symlink escape, `.autoclaw` read/write exposure, missing nested residue detection, and permission-widening blindness. Focused GREEN is 34/34; deterministic and live-enabled full suites pass 215 with the expected non-live skip only; strict OpenSpec is 4/4; project-memory, compile/no-cache, and diff checks pass.
- Round-17 focused RED proved the descriptor-reopen and abandoned-worktree defects and the former code lacked bounded capture; the synchronized timeout regression exercises the TERM-before-freeze escape. Focused GREEN is 19/19. Deterministic ACA passes 219 with one intentional live skip; live-enabled ACA passes 219/219; strict OpenSpec is 4/4; project-memory, in-memory compile/no-cache, and diff checks pass at implementation tip `e235850`.
- The first record-tip live run at `d6c1479` failed only because the final model narration said `blocked` rather than the test's accepted word `denied`; all authority-bearing filesystem, command, and secret assertions passed. The prose oracle now accepts either word, and the exact live boundary test passes after repair. Complete exact-tip repetition remains pending.
- Local Python 3.11/3.12 ad hoc runs were not claimed because those interpreters lack the repo's PyYAML dependency; required remote Python 3.11/3.12 checks remain a post-push gate rather than prompting a local dependency install.
- Final record-tip repetition: pending after the round-17 records and current-main global reconciliation are committed. The prior exact pushed tips are superseded by the round-17 `CHANGES-REQUIRED` verdict.

Round-19 containment repair supersedes exact pushed `5a053ab`: a fresh reviewer proved a normal-success detached descendant could write after return. The first ancestry-only repair failed immediate-detach stress and was strengthened with a gated-spawn process-tree lease plus inherited per-run lease discovery. Focused ACA process/sandbox tests pass 13/13; direct paired reproductions show no late write or live child; concurrent immediate-detach stress passes 50/50 for ACA and 50/50 for global. Full deterministic/live suites, record-bearing exact tips, remote CI, and fresh review remain gates.

The remaining Stage 0 gates are full repetition on the evidence-only exact tips, a fresh independent `REVIEW-CLEAN`, origin/main landing, SHA-pinned observe-only deployment, and live health proof. Post-release work belongs to coordinator Codex `019f5f11-5758-7790-b1b6-6f36cb50868f`: connect a bounded approved observation adapter and design graduated agency so reversible private/local work becomes broadly available without weakening hard gates for destructive, irreversible, credentialed, financial, privacy-expanding, security-sensitive, or outward-facing effects.

Provenance: executor=codex:gpt-5.5:high; audit=L4-pending; scripts=ACA-unittest,live-builder-containment,OpenSpec,project-memory,global-verify; escalations=0; routing=T3; notes=pilot retained; round-17 repairs green; current-main reconciliation, final exact repeat, and review pending
