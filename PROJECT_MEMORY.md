# Project Memory
<!-- shared cross-AI project memory (ER-036) — schema: .project-memory.schema.yaml -->
<!-- write protocol + policy: /Users/gillettes/.codex/policies/PROJECT_MEMORY.md -->

## Active goal

- Land and independently verify Agency v2 Packet A: backward-compatible ACA acceptance and semantic validation of the frozen observation-v2 wake contract, with no global producer activation or authority expansion. Source: Trevor autonomous-partner goal; coordinator `019f5f11-5758-7790-b1b6-6f36cb50868f`; predecessor `019f5c92-0af9-7fe1-97e4-b860aab357e2`.

## Durable decisions

- Keep this repository. Do not archive it or create a replacement.
- Global surfaces own persistent identity, goals, approved observations, approvals, maturity, learning promotion, benefit, heartbeat, and queue state. ACA owns stateless typed wake policy plus per-episode legality/evidence.
- Personality and love-as-practice guide voice and ranking, never authority. Respect for Trevor's devotion to Jehovah is a configured relationship boundary, not a claim of divine standing.
- Recurring observe may deploy after proof. Recurring execute remains off until the bounded pilot and fresh independent audit are clean.
- L3 history thresholds are necessary but not sufficient. A separate exact operator-promotion proof format is not implemented, so every effectful proposal still requires a current, exact, proposal-bound approval.
- Agency v2 lands ACA-first and backward compatible: new ACA accepts unchanged wake v1 and exact wake v2; global v2 remains inactive until a separately reviewed Packet B binds exact ACA/global SHAs.

## Current implementation state

- Executor evidence, unattended-authority, command-default, actual-diff, atomic-state, bounded worktree-ref, safe discovery-command, and completed-candidate replay defects are repaired with regressions.
- Identity, initiative ranking, authority, one-decision runtime, outcome learning, CLI, schemas, snapshot builder, real model candidate generation, global bridge, queue integration, executor adapter, and exact completion retirement exist on isolated branches.
- The isolated live pilot passed observe, proposal, pre-approval denial, synthetic exact approval, dry-run, real `gpt-5.5`/high retained-worktree execution, 159-test final rerun, outcome/unknown-benefit reconciliation, no-replay retirement, and kill-switch proof. Evidence: `records/verification/2026-07-13-autonomous-partner-pilot.md`.
- PR review later found four ACA gaps: renamed-away source paths were skipped, candidate goals were not bound to the current wake, and schema-valid observations/maturity could omit fields later read unconditionally. TDD repairs now include both rename paths, require current goal provenance, and reject incomplete wake evidence; the full suite is green at 163 tests. The token-shaped test fixture was rewritten without weakening runtime secret rejection.
- Stage 0 is landed and deployed. ACA production tip `561d771a4904ec0d911604dd98bba207f170c5a9` passed deterministic/live 238, 100/100 containment stress, OpenSpec 4/4, memory/static, remote CI/security, direct cross-repo containment, and zero-residue gates. Fresh reviewer `/root/containment_review` returned literal `REVIEW-CLEAN`. PR #7 merged as `7d29eb910b80238e0ab3f89dad277b186a0f945c`; stale PR #6 closed unmerged. The immutable ACA runtime is detached and clean at `/Users/gillettes/Coding Projects/aca-runtime/autonomous-partner/7d29eb9`.
- OpenSpec verification/retrospective are complete and the change is archived at `openspec/changes/archive/2026-07-14-autonomous-partner-reposition/`; its four capability specs are synchronized under `openspec/specs/`.
- The Stage 0 release gate is complete. The paired global runtime is detached at merge `ef6802e22d5cf70c9e139c469a480f81a21a8a34`, points to this ACA runtime, and is installed with both loop and bridge modes fixed to `observe`. Direct and managed launchd runs emit a typed `no_op` with zero candidates, ready packets, or inflight packets; recurring execute remains off. The empty approved-observation feed means proactive usefulness and measured benefit remain intentionally unproved. Agency v2 now owns the bounded observation adapter and graduated-agency design: broadly allow reversible private/local work while reserving hard gates for destructive, irreversible, credentialed, financial, privacy-expanding, security-sensitive, and outward-facing effects.
- Packet A is implemented test-first on `codex/agency-v2-packet-a` from `origin/main@282eb5118cfcd95263ffc9e409edce1ba831d623`: wake v1 remains unchanged; wake v2 uses the byte-identical reviewed observation schema plus canonical hash, namespace, duplicate, skew/staleness, and TTL validation. Focused RED failed 6 valid-v2 paths; focused contract/runtime GREEN passes 31/31; full deterministic ACA passes 250 tests with 2 intentional opt-in skips; OpenSpec passes 5/5. Independent reviewer `/root/aca_packet_a_review` closed one P2 and three P3 regression/governance gaps and returned literal `REVIEW-CLEAN`. Implementation commit `bfa4b315768b7cf8a3c60de4183496e7a34e781e` is pushed with exact remote-tip equality and ready PR #9 is open. PR review raised two durability updates, now accepted, and one schema-pattern suggestion, rejected because it would break the exact frozen three-way schema bytes while the semantic boundary already rejects fractional seconds and offsets; final remote checks and merge containment remain.

## Gotchas

- ACA run `COMPLETE` means a verified retained worktree/report, not automatic merge or publish.
- Empty observations/candidates are the safe default; the policy never invents evidence.
- The global bridge and ACA envelope schemas are a cross-repo compatibility boundary and must be changed together.
- Structured-output schemas accepted by local validators may include keywords rejected by the Codex output-schema API; keep model schemas to the supported subset and retain deterministic post-validation.
- Completed proposal state must be retired by exact hash after outcome reconciliation or a later wake can requeue an already-complete run ID.
- Immutable detached-process ownership is macOS-specific in this release; the non-macOS environment/ancestry fallback is not claimed as equivalent. Deploy Stage 0 only on the verified SHA-pinned macOS runtime.
- Accepting wake v2 in ACA is not activation proof. The deployed Stage 0 pair stays pinned to wake v1 until Packet B passes dual-SHA compatibility, no-effect, resource-admission, and independent-review gates.
