# Autonomous partner live pilot

- Date: 2026-07-13 UTC
- Source Codex task: `019f5c92-0af9-7fe1-97e4-b860aab357e2`
- Source Claude chat: `bb90d05d-86d3-4140-9e6c-78d2847c4d72` (`*Autonomous Agent Creation`)
- ACA branch: `codex/autonomous-partner-reposition-20260713`
- Global branch: `codex/er141-autonomous-partner-reposition-20260713`
- Isolated runtime root: `/Users/gillettes/.cross-agent/autonomous-partner/pilots/2026-07-13-er141-222735`
- Result: **STAGE 0 PASS AND DEPLOYED.** The preserved pilot remains valid evidence; every later accepted release finding is repaired. Exact ACA tip `561d771a4904ec0d911604dd98bba207f170c5a9` passed deterministic/live 238, 100/100 containment stress, OpenSpec 4/4, memory/static, remote CI/security, direct cross-repo containment, and zero-residue gates. Fresh reviewer `/root/containment_review` returned literal `REVIEW-CLEAN`; PR #7 merged as `7d29eb910b80238e0ab3f89dad277b186a0f945c`; stale PR #6 closed unmerged. The detached ACA runtime at `/Users/gillettes/Coding Projects/aca-runtime/autonomous-partner/7d29eb9` is paired with global runtime `ef6802e` in observe-only mode.

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

Round 20 re-opened containment before landing. Reviewer `/root/containment_review` challenged the inherited dirty repair rather than accepting its summary and found fail-open scanner handling, unproved final survivors, unconditional sandbox-tag deletion, PID/group reuse risk, a paired global helper that had not been wired into callers, and branch leakage after partial worktree creation. ACA `2c5b1331d2c55f7c5f1a1bc2aa2320a1013bfdf0` is the pushed implementation repair. It uses an inherited macOS sandbox-policy tag as immutable process ownership, stable process-start identities before every signal, STOP-before-TERM/KILL on all exit paths, two clean final scans before tag removal, bounded pipe capture, and rollback that deletes only a branch created by the failed operation.

Preserved proof at the implementation tip:

- RED: the focused reviewer reproductions failed on reused root/group identity, scanner failure, persistent survivor, and partial-add branch leakage before the repair.
- GREEN: `python3 -m unittest -v tests.test_process_runner` ran 17 tests successfully with only the explicit opt-in stress test skipped; `python3 -m unittest -v tests.test_worktree` passed 9/9.
- GREEN: `PROCESS_CONTAINMENT_STRESS=1 python3 -m unittest -v tests.test_process_runner.ProcessRunnerTests.test_tag_only_containment_stress_100_runs` passed 100 post-return release-gated iterations in 72.439 seconds.
- GREEN: the paired global helper's corrected 100-run gate passed in 148.405 seconds; its 16-test file and the complete current-main global verifier also passed.
- Static: in-memory compile, no source bytecode residue, and `git diff --check` passed in both repositories.

Round 21 cumulative testing exposed two macOS integration defects before release. ACA `9c5bd622d9bff532a102b7ca4e89f7d1c70023da` replaces nested partner/containment sandboxes with one composed Seatbelt profile: partner restrictions are evaluated first, the unique immutable ownership rule is appended last, and only the tag directory receives a narrow read exception. The first cumulative live Codex run then proved that the Codex CLI owns another inner permission-profile sandbox; wrapping the CLI itself in the immutable tag prevented both an allowed patch and its inner sandbox. ACA `d199c5f` therefore gives the trusted, repo-code-disabled Codex host a separately named child-sandbox runner that retains gated ancestry/environment cleanup without an outer Seatbelt profile. Generic repository commands and deterministic partner verification still require the immutable tag, and the Codex PreToolUse guard plus permission profile still deny root writes, repo-code execution, control reads, network, and unlisted tools before effects.

Exact implementation-tip proof for ACA `d199c5f`:

- RED: the original cumulative partner tests failed three times with nested `sandbox_apply: Operation not permitted`; after profile composition, the first live Codex run and one targeted rerun failed because the outer tag blocked the allowed patch and inner Codex sandbox.
- GREEN: focused process/partner/verifier coverage passed 29 tests with the explicit 100-run gate skipped; the forced partner test disables ancestry and environment discovery so the composed immutable tag is the only way to reap the detached child.
- GREEN: the real Codex boundary probe passed twice after the child-owned-sandbox repair, including one exact-tip run in 31.799 seconds. The allowed patch landed while the root patch, supervisor command, control-directory read, secret exposure, and repo-code effects stayed denied.
- GREEN: deterministic full ACA passed 237 tests with the live Codex and opt-in stress gates skipped; live-enabled full ACA passed 237 tests with only the opt-in stress skipped.
- GREEN: exact-tip immutable-tag stress passed 100/100 in 72.865 seconds. A separate composed-profile tag-only stress passed 25/25 during the repair loop.
- GREEN: strict OpenSpec passed 4/4, project-memory validation passed, in-memory source compilation passed, and `git diff --check` passed before the evidence record update.

Round 22 reviewer `/root/containment_review` found that ACA cleanup could count one observed empty scan as two when the confirmation deadline expired. That could remove the immutable ownership tag without the documented two-observation proof. ACA `d70781488ae8aabeb3ad8302bf6fd854bb39cf02` separates the three-second cleanup-confirmation window from scan count, removes synthetic confirmation, and fails closed after only one real empty scan. Focused process-runner coverage passes 21 tests with the explicit stress gate skipped. The paired review also found global orchestration hosts were incorrectly wrapped in a non-composable outer tag; global `4bafc30f9bda29238776755f9b2ca12d152807f0` repairs exact natural snapshot, candidate→Codex, and executor→ACA routes while keeping generic leaf commands tagged. The direct global→ACA sandbox canary and complete global verifier pass. Both exact code tips are pushed.

Round 23 exact-tip deterministic repetition at `0b84551` exposed one test-fixture aliasing defect, not a production containment escape. `test_success_stops_detached_descendant_before_late_write` patched `_tagged_lease_processes` with one mutable `return_value={}`. Production `tagged_processes()` correctly merged Seatbelt inventory into that object, so the mock replayed already-dead PIDs forever and the real two-scan gate failed closed. ACA `71a92ff` returns a fresh empty mapping per scan. The formerly failing test passes and the repaired tree passes deterministic 238 with the live and opt-in stress gates skipped. Final record-tip deterministic/live/stress/OpenSpec/static repetition remains required.

Full ACA record-tip gates, exact remote checks, and a fresh literal `REVIEW-CLEAN` remain the release gate. On non-macOS platforms the environment/ancestry fallback is weaker than the immutable macOS tag; Stage 0 deployment remains pinned to the verified macOS host rather than treating that fallback as equivalent containment.

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
- Round-19 implementation tip `ada9d2acd3cfb2b3540db163b85198a411cc0269` passes the complete deterministic suite at 222 tests with one intentional live skip and the live-enabled suite at 222/222. The record-bearing successor receives the same exact-tip repetition before push/review; earlier pushed tips remain superseded.

Round-19 containment repair supersedes exact pushed `5a053ab`: a fresh reviewer proved a normal-success detached descendant could write after return. The first ancestry-only repair failed immediate-detach stress and was strengthened with a gated-spawn process-tree lease plus inherited per-run lease discovery. Focused ACA process/sandbox tests pass 13/13; direct paired reproductions show no late write or live child; sequential stress passes ACA 30/global 100 and concurrent stress passes 50/50 per repo. Exact implementation `ada9d2acd3cfb2b3540db163b85198a411cc0269` passes deterministic 222 with one intentional live skip and live-enabled 222/222. Record-bearing exact repetition, remote CI, and fresh review remain gates.

At this historical pre-landing snapshot, the remaining gates were final static/remote/review proof, main landing, immutable deployment, and live health. The final section below closes those Stage 0 gates. Post-release work belongs to coordinator Codex `019f5f11-5758-7790-b1b6-6f36cb50868f`: connect a bounded approved observation adapter and design graduated agency so reversible private/local work becomes broadly available without weakening hard gates for destructive, irreversible, credentialed, financial, privacy-expanding, security-sensitive, or outward-facing effects.

## Final Stage 0 landing and deployment closeout

- Exact reviewed ACA tip: `561d771a4904ec0d911604dd98bba207f170c5a9`.
- ACA PR #7: merged 2026-07-15 UTC as `7d29eb910b80238e0ab3f89dad277b186a0f945c`; reviewed tip is an ancestor of `origin/main`.
- Superseded ACA PR #6: closed unmerged at stale tip `bd5fa34f0cfefd193f1f168d4b6f2f938a5fbb27` with a pointer to #7.
- Paired global tip and merge: `0926a150b975aef40b5a820c1eced69ea1b6ea49` merged by PR #23 as `ef6802e22d5cf70c9e139c469a480f81a21a8a34`; exact tip is contained by global `origin/main`.
- Immutable runtimes: ACA `/Users/gillettes/Coding Projects/aca-runtime/autonomous-partner/7d29eb9`; global `/Users/gillettes/Coding Projects/gi-runtime/autonomous-loop/ef6802e`; both detached, clean, and exact-SHA pinned.
- Direct proof: loop returned `status=ok`, `action=observe_only`; health returned `healthy`.
- Managed proof: launchd loaded the exact global script and ACA root; `RunAtLoad` completed with exit `0`, a typed partner `no_op`, zero candidates, zero ready packets, and zero inflight packets. The managed health check completed with exit `0` and no unacknowledged failed dispatch.
- Natural interval proof: at `2026-07-15T07:05:39Z` the loop advanced from run 1 to run 2 without a kickstart, exited `0`, and emitted another observe-only typed `no_op` with zero candidates, ready packets, or inflight packets. The health job independently advanced to run 2, exited `0`, and wrote `status=healthy` at `2026-07-15T07:05:57Z`; neither stderr log changed.
- Safety boundary: both loop and bridge remain `observe`; recurring execute is off; the committed observation feed is empty; adoption and measured benefit remain unproved.

Provenance: executor=codex:gpt-5.6-sol:high; audit=L4-review-clean; scripts=ACA-unittest,live-builder-containment,containment-stress,OpenSpec,project-memory,global-verify,cross-repo-canary,launchd-direct-managed-natural; escalations=0; routing=T3; notes=Stage 0 landed and SHA-pinned observe-only deployment healthy
