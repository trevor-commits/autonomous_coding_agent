# Agency v2 Packet A independent review

## Audited Chat

- Audited chat name: `Coordinator: Autonomous Partner Agency v2`
- Audited chat repo/cwd: `global-implementations` / `/Users/gillettes/Coding Projects/global-implementations`
- Active implementation repo/cwd: `Autonomous Coding Agent` / `/Users/gillettes/Coding Projects/aca-worktrees/agency-v2-packet-a`
- Provider: Codex
- Full ID: `019f5f11-5758-7790-b1b6-6f36cb50868f`
- Transcript/resolved path: `/Users/gillettes/.codex/sessions/2026/07/13/rollout-2026-07-13T22-20-00-019f5f11-5758-7790-b1b6-6f36cb50868f.jsonl`
- Independent reviewer: native read-only subagent `/root/aca_packet_a_review`

## Reviewed state

- Branch: `codex/agency-v2-packet-a`
- Exact base and review-time `origin/main`: `282eb5118cfcd95263ffc9e409edce1ba831d623`
- Frozen global design commit: `4292f4efd4ce9c5a3586f51c63188c413e92025e`
- Frozen observation-schema SHA-256: `924dcf74ce336e5011af89fa9428fdac9d6254a6e3fddc0f5d00efe244790877`
- Review boundary: the complete uncommitted Packet A implementation diff plus its OpenSpec and durable records. The reviewer had a read-only mandate and reported identical pre/post Git state after every round.
- Landing reference: the reviewed implementation was committed without code/schema/test changes as `bfa4b315768b7cf8a3c60de4183496e7a34e781e`, pushed with exact remote-tip equality, and opened as ready PR #9.

## Finding-to-fix lineage

| Round | Severity | Finding | Disposition and proof |
| --- | --- | --- | --- |
| 1 | P2 | The runtime observation schema matched the frozen copy manually but byte parity was not regression-locked. | Accepted. `test_runtime_schema_matches_the_frozen_change_contract` now compares the runtime and OpenSpec schema bytes directly. |
| 1 | P3 | Wake-v2 acceptance had no runtime-level no-effect regression. | Accepted. A valid v2 wake now reaches `decide_wake(..., mode="observe")` and proves typed `no_op` / `observe_only`, unchanged snapshot/candidate, empty evidence/payload, and zero candidate iteration. |
| 1 | P3 | The active branch ledger lacked explicit linked-issue and plugin-mirror fields. | Accepted. The ledger now records the self-contained ER-141 disposition and `plugin mirror status: not applicable`. |
| 2 | P3 | The first no-effect repair compared an ordinary candidate list before/after, which did not prove the list was never read. | Accepted. The regression now uses a one-shot sentinel iterator whose external flag stays false and separately preserves candidate equality. |
| 3 | — | No remaining actionable finding. | `REVIEW-CLEAN`. Two bounded repair tests, schema byte parity, and diff checks passed; prior complete-diff review findings remained closed. |

## Independent evidence

- Focused partner contract/runtime suite: 31/31 pass.
- Full deterministic ACA suite: 250 tests pass with two intentional live/stress opt-in skips.
- Strict OpenSpec validation: 5/5 pass.
- Runtime, ACA OpenSpec, and frozen global schema copies are byte-identical at the recorded SHA-256.
- Project-memory, AGENTS, repo-principles, todo-governance, in-memory compile, JSON parse, residue, and `git diff --check` gates pass.
- The reviewer independently confirmed canonical/hash/private-data probes, v1 compatibility, v2 time/TTL boundaries, and absence of producer, dispatch, authority, or runtime activation in Packet A.

## Verdict

`REVIEW-CLEAN` for the implemented Packet A scope. No unresolved P0, P1, P2, or P3 finding remains in the reviewed code/schema/test boundary.

Remote CI, PR review, merged-commit containment, deployed dual-SHA compatibility, global wake-v2 activation, natural recurrence, model deliberation, dispatch, and effects were not part of this local review. They remain explicit later gates rather than implied proof.

## PR review addendum

CodeRabbit reviewed implementation commit `bfa4b315768b7cf8a3c60de4183496e7a34e781e` on PR #9 and posted three comments. The stale workflow/PR-state and Work Record `led to:` comments were accepted and repaired with exact run, artifact, commit, and PR references. The request to add timestamp regexes to the runtime JSON Schema was declined: Packet A is contractually bound to byte-identical ACA change/runtime and frozen global schema copies at SHA-256 `924dcf74ce336e5011af89fa9428fdac9d6254a6e3fddc0f5d00efe244790877`; changing only ACA would create cross-repo drift, while changing the frozen global contract would reopen the completed design gate. The semantic validator already requires `YYYY-MM-DDTHH:MM:SSZ`, and regressions reject both fractional seconds and offsets before a wake is returned.

Provenance: executor=codex:gpt-5.6-sol:high; audit=L4-review-clean; scripts=focused-unittest,full-unittest,OpenSpec,project-memory,schema-parity,in-memory-compile,governance,diff; escalations=0; routing=T3; notes=single-writer implementation with one read-only reviewer
