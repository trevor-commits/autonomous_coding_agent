# Queue Runs

**Date:** April 16, 2026
**Authority:** `canonical-architecture.md` defines runtime ownership, `LINEAR.md` defines queue metadata in Linear, `PROMPTS.md` defines prompt shape, and `RULES.md` defines stop conditions and queue legality.
**Purpose:** Define the exact operating contract for supervisor-mediated unattended execution of Linear issues.

## Guardrail

Linear nominates work. It does not issue arbitrary commands. The supervisor reads queue metadata from Linear, resolves the authoritative repo docs named by that metadata, normalizes the result into a run contract, and only then launches Codex. Linear issue metadata is routing input, not a third source of truth.

## What "One Long Run" Means

A walk-away session is a long-lived queue supervisor process composed of many separate issue-runs.

- One issue-run equals one claimed Linear issue, one fresh Codex conversation, one run ID, one writable worktree or branch, one landing commit or blocked outcome, and one queue-exit comment.
- The queue process may continue across many issues, but Codex context does not carry from one issue to the next.
- Claude-owned audit or test work is separate lane work. The Codex queue does not absorb it.

## Eligible Issue Schema

Every queue-capable issue uses the Standard issue template in `LINEAR.md` plus two routing fields:

- `Execution lane:` `Codex` | `Claude Code` | `Cowork` | `Trevor`
- `Execution mode:` `Queue` | `Manual`

Required fields for any issue the Codex queue may claim:

- `Authoritative spec path:`
- `Authoritative decision docs:` when applicable
- `Why this exists:`
- `Origin source:`
- `Execution lane: Codex`
- `Execution mode: Queue`

Codex queue eligibility predicate:

1. The status is `Ready for Build`.
2. `Execution lane` is `Codex`.
3. `Execution mode` is `Queue`.
4. `Authoritative spec path` resolves to repo-visible truth.
5. No `prompt-review` label is present.
6. No `Blocked-external` label is present.
7. The issue is not already claimed by another live run.
8. No unresolved `Blocked reason artifact` is recorded for the current attempt.
9. The target repo exposes the required repo contract and queue-closeout surfaces.

Issues are handled by lane as follows:

- `Execution lane != Codex` or `Execution mode = Manual`: skip without mutation.
- `Claude Code` audit or test issues stay in their own lane and are ignored by the Codex queue.
- Missing required queue fields on an otherwise Codex-targeted issue are treated as a queue-schema failure: the supervisor writes the blocker, moves the issue to `Blocked`, and continues.
- Issues already in `Building`, `AI Audit`, `Human Verify`, `Done`, or `Canceled` are never reclaimed by the Codex queue.

When Codex surfaces later audit or deeper test work that belongs to Claude Code, it creates a separate Linear issue with:

- `Execution lane: Claude Code`
- `Execution mode: Manual` until a dedicated Claude queue exists
- a precise `Authoritative spec path` or repo artifact path naming what Claude Code must inspect

Codex does not pull that issue back into the same queue pass.

## Supervisor Loop

1. Discover candidates. Query Linear for `Ready for Build` issues and sort deterministically by priority, then oldest `updatedAt`, then issue ID.
2. Validate eligibility. Apply the queue predicate above. Lane mismatches and manual-mode issues are skipped silently in runtime logs. Queue-schema failures on Codex-targeted issues become `Blocked`.
3. Claim the issue. Create a new `run_id`, acquire the single-writer lease, move the issue to `Building`, and post a claim comment with the `run_id`, the authoritative spec path, and the run branch or worktree.
4. Normalize inputs. Read the authoritative repo docs, repo contract, and queue metadata; derive the run contract and allowed path scope. If normalization fails, write the blocked artifact, comment, move the issue to `Blocked`, release the claim, and continue.
5. Launch a fresh Codex session. Use the queue prompt template in this document together with `PROMPTS.md`. The prompt is issue-scoped and does not mention any other queue items.
6. Enforce self-test cadence. Codex runs the narrowest deterministic check after each material edit cluster and the full required verification pack before handoff. Self-testing is mandatory, not discretionary.
7. Land successful work. If the final deterministic pack passes, the supervisor writes or verifies the repo closeout artifacts, creates the landing commit, pushes it, posts the completion comment, moves the issue to `AI Audit`, releases the claim, and continues to the next eligible Codex issue.
8. Handle blocked work. If retries are exhausted or verification remains red, the supervisor writes the blocked reason artifact, posts the blocker comment, moves the issue to `Blocked`, releases the claim, and continues unless a global stop rule has triggered.
9. Ignore Claude-lane follow-up issues. Claude-owned audit or test tickets created during the run remain out of scope for the Codex queue and do not block the queue from continuing once the current issue has either landed or blocked cleanly.
10. Exit cleanly. The queue ends when no eligible Codex issues remain or a global stop rule fires. The queue process then writes its final report and stops.

## Codex Prompt Template Per Issue

Queue-mode Codex runs use a versioned template. The supervisor fills the placeholders exactly; it does not improvise a bespoke per-issue command surface.

```text
Goal: Implement {issue_id} in {repo_path} using the authoritative spec at {spec_path}. One issue-run only. Touch only the scope justified by the named spec and decision docs.

Discipline: Code is allowed. Use only the supervisor-provided branch or worktree. Do not move Linear state, do not edit Linear checklists, and do not commit or push; the supervisor owns queue claim, landing commit, and push. Self-test frequently. If the issue metadata conflicts with the authoritative repo docs, stop and report the conflict instead of guessing.

For repo content, limit substantive reads to:
- {spec_path} ({spec_reason})
- {decision_doc_1} ({decision_reason_1})
- {decision_doc_2} ({decision_reason_2})
- {.agent/contract.yml or equivalent repo contract path} (required verification and runtime commands)
- {known_target_files_or_directories} (expected touch surface)
- todo.md (only if the repo governance bundle requires Work Record / Completed / Test Evidence closeout)

Do not read other repo docs unless required by higher-priority agent instructions or validation.

Body:
1. Validate that the issue is still a Codex-owned queue issue (`Execution lane: Codex`, `Execution mode: Queue`) and that the authoritative spec path resolves cleanly. If not, stop with evidence.
2. For fixes, capture baseline failure evidence before changing code. For features or refactors, capture the pre-change baseline for the touched area.
3. Implement only the bounded scope required for this issue. Do not absorb adjacent backlog items or other queue issues.
4. After each material edit cluster, run the narrowest deterministic check that can falsify the latest change. Record failures honestly and adapt.
5. Before handoff, run the required issue verification pack exactly as named by the repo contract and authoritative spec.
6. If you surface follow-up work outside this issue, create a separate Linear issue or record an explicit `no-action:` or `self-contained:` disposition. Any later audit or deeper test work for Claude Code must be filed as a separate issue with `Execution lane: Claude Code` and `Execution mode: Manual`.
7. Report blockers with concrete evidence. Do not invent missing facts, hidden decisions, or acceptance criteria.

Constraints:
- Ignore every other queue item completely.
- Do not widen scope beyond the authoritative spec and allowed paths.
- Do not claim or complete Claude-owned audit or test work.
- Do not leave the issue without a truthful self-audit or verification evidence.
- Print a one-line summary of files modified.

Durable record:
- Append the repo's `todo.md` `Work Record Log` entry for this issue-run when that governance surface exists.
- Append the repo's `Completed` index entry on successful landings when that governance surface exists.
- Append the repo's `Test Evidence Log` entry with the exact commands run and observed results when that governance surface exists.
- Refresh the repo's `Linear Issue Ledger` entry for every live issue created or materially changed when that governance surface exists.
- Create any surfaced follow-up issues in Linear during the same closeout pass, including Claude-owned audit or test issues when applicable.
- The Self-audit must include the Ripple Check, the Linear-coverage disposition, and an explicit `did not verify X because Y` line for anything skipped or deferred.
```

## Stop / Skip Policy

Use three outcomes only: global stop, issue block, or skip.

### Global Stop And Halt The Queue

These conditions stop the entire queue supervisor process:

- Linear or queue-runner auth fails, so issues can no longer be claimed or released safely.
- Codex is unavailable or cannot start new issue-runs.
- The supervisor cannot create the isolated run branch or worktree or cannot acquire the single-writer lease.
- A landing commit is created but the push fails. The current issue is marked `Blocked`, then the queue halts because repo state is now ambiguous.
- A queue-internal error or repeated supervisor bug affects the legality of later issues.

### Block The Current Issue, Then Continue

These conditions block the claimed issue but do not stop the whole queue:

- The authoritative spec path is missing, unreadable, or contradicts the Linear routing metadata.
- The repo contract or required queue-closeout surfaces are missing for this repo.
- Baseline verification is already red in a way the current issue is not allowed to repair.
- A required secret, service dependency, or local prerequisite for this issue is missing.
- The same failure fingerprint exceeds the allowed retry ceiling for this issue.
- The final required deterministic verification pack stays red after the allowed repair loops.
- The work turns out to require another lane and cannot be cleanly split into a follow-up issue.

### Skip Without Mutation, Then Continue

These conditions never become Codex work in the current pass:

- `Execution lane` is not `Codex`.
- `Execution mode` is `Manual`.
- The issue still carries the `prompt-review` label.
- The issue carries the `Blocked-external` label.
- The issue is already claimed by another live run.
- The issue is no longer in `Ready for Build`.

Claude-owned audit or test issues are always skipped by the Codex queue unless the repo later defines a dedicated Claude queue with its own contract.

## Logging, Commit, And Comment Flow

Queue mode uses all three truth tiers defined in `RULES.md`.

### Run Truth

The supervisor writes queue-runtime artifacts under `.autoclaw/runs/<run_id>/`, including:

- the normalized queue metadata
- the rendered Codex prompt
- commands run and exit codes
- logs, screenshots, traces, and defect packets
- the final machine-readable and human-readable run reports

### Repo Truth

When the repo has the governance bundle required for queue mode, the issue-run writes:

- `todo.md` `Work Record Log` for every claimed issue, including blocked outcomes
- `todo.md` `Completed` for successful landings
- `todo.md` `Test Evidence Log` for the deterministic checks that were actually run
- `todo.md` `Linear Issue Ledger` refreshes for any new or materially changed live issues

If the repo cannot provide those closeout surfaces, queue mode is unsupported for that repo rather than being silently downgraded to chat-only memory.

### Linear Truth

The supervisor owns queue comments and queue-state transitions. Codex does not move Linear state.

Successful issue-run flow:

1. Claim comment posted at `Building` with `run_id`, queue owner, and authoritative spec path.
2. Repo closeout artifacts written.
3. Supervisor creates one landing commit for the issue-run and pushes it before claiming the next issue.
4. Completion comment posted with:
   - `run_id`
   - branch or worktree reference
   - landing commit SHA
   - verification commands and results
   - repo artifact paths
   - any follow-up issue IDs
   - explicit next lane: `AI Audit`
5. Issue moves from `Building` to `AI Audit`.

Blocked issue-run flow:

1. Blocked reason artifact written in repo truth and run truth.
2. Blocker comment posted with the failure class, key evidence, artifact path, and whether the queue will continue.
3. Issue moves from `Building` to `Blocked`.

Skipped issues do not get state changes or queue comments. They remain available to the correct lane or later manual handling.

## Commit Ownership

The supervisor owns queue landing commits and pushes. Codex writes and self-tests the change; it does not own the landing mechanics.

- One successful issue-run produces exactly one landing commit.
- Each blocked issue-run may produce a docs-only closeout commit when the repo governance bundle requires durable blocked records.
- Commit messages follow the target repo's policy. If the repo policy is silent, the supervisor falls back to its standard run-scoped commit format.
- The queue does not claim the next issue until the current issue's required push has succeeded.
