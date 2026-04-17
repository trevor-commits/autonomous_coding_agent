# CodeRabbit Review Settings

**Date:** April 17, 2026  
**Purpose:** Preserve the exact CodeRabbit settings, caveats, and reasoning
for this repository so later AI sessions can audit the configuration and the
operator decision trail without reconstructing it from chat history.

`.coderabbit.yaml` is the machine-readable source of truth for settings that
CodeRabbit supports in repo config. This document is the operator-facing
companion for:

- rationale behind those values
- UI fields intentionally left blank
- settings discussed in chat that are UI-only or caveated
- the exact order the settings were reviewed in operator setup

If this document and `.coderabbit.yaml` diverge on a repo-supported field, the
YAML should be corrected in the same change. UI-only or support-caveated fields
should stay documented here.

## Current stance

- This repo is trialing `CodeRabbit` first for dedicated PR-review quality.
- `GitHub Copilot` remains the cheaper GitHub-native fallback baseline, not the
  active review lane.
- The intended flow is: Codex or `HOTL` lands a bounded diff -> `CodeRabbit`
  runs the mechanical pre-audit -> Claude Code or Trevor does the deeper
  architectural and acceptance pass.
- Blocking behavior stays off until the repo has seen 3-5 real PRs with useful
  review signal and acceptable noise.

## Supported settings in repo config

These are the settings currently encoded in
[`/.coderabbit.yaml`](/Users/gillettes/Coding Projects/Autonomous Coding Agent/.coderabbit.yaml).
They are listed in the same order used during the operator setup pass.

| Setting | Value | Why |
|---|---|---|
| `profile` | `chill` | This repo is docs/governance heavy; `assertive` is more likely to produce noisy low-value feedback. |
| `request_changes_workflow` | `false` | `CodeRabbit` is a review layer, not a gate, until the trial proves it deserves stronger control. |
| `high_level_summary` | `true` | High-level change summaries are useful for review context. |
| `high_level_summary_instructions` | custom 4-8 bullet technical summary | Keeps summaries technical and avoids release-note fluff. |
| `high_level_summary_placeholder` | `""` | Avoid rewriting the PR description body by default. |
| `high_level_summary_in_walkthrough` | `true` | Put the summary in the walkthrough comment instead of relying on the PR body. |
| `auto_title_placeholder` | `""` | Do not let `CodeRabbit` rewrite PR titles by default. |
| `auto_title_instructions` | `""` | No title-generation behavior is desired right now. |
| `review_status` | `true` | Status visibility is useful. |
| `review_details` | `false` | Extra internal detail is more noise than signal for this repo right now. |
| `commit_status` | `true` | Review completion should surface as a commit status. |
| `fail_commit_status` | `false` | Do not turn temporary product failures into a hard red status during the trial. |
| `collapse_walkthrough` | `true` | Keeps walkthrough output compact. |
| `changed_files_summary` | `true` | File-level overview is useful. |
| `sequence_diagrams` | `false` | Diagrams are unnecessary for most PRs in this repo and can create noise. |
| `estimate_code_review_effort` | `false` | Not useful enough to justify the extra output. |
| `assess_linked_issues` | `false` | This repo already keeps issue truth in repo docs and `todo.md`; the extra assessment is low-value. |
| `related_issues` | `false` | Avoid speculative issue linkage noise. |
| `related_prs` | `false` | Avoid speculative PR linkage noise. |
| `suggested_labels` | `false` | Solo-maintainer repo; label suggestions are not currently useful. |
| `labeling_instructions` | `[]` | No label suggestion program is active right now. |
| `auto_apply_labels` | `false` | Never auto-apply labels while label suggestion is off. |
| `suggested_reviewers` | `false` | Solo-maintainer repo; reviewer suggestion adds no value. |
| `auto_assign_reviewers` | `false` | Never auto-assign reviewers while reviewer suggestion is off. |
| `in_progress_fortune` | `false` | Fortune messages are presentation noise. |
| `poem` | `false` | Poetry is presentation noise. |
| `enable_prompt_for_ai_agents` | `true` | If `CodeRabbit` leaves a useful inline comment, AI agents should be able to consume the generated fix prompt. |
| `path_filters` | `!**/__pycache__/**`, `!**/*.pyc` | Ignore trivial Python cache artifacts. |
| `path_instructions` | five scoped instruction blocks | Teach `CodeRabbit` the difference between supervisor code, tests, schemas, live governance docs, and archive docs. |
| `abort_on_close` | `true` | Do not let stale review jobs keep running after PR close/merge. |
| `disable_cache` | `false` | No reason to pay the cost of always-fresh dependency/code fetches during the trial. |

## Summary instructions

The configured summary prompt is:

```text
Write a concise technical summary in 4-8 bullets. Prioritize behavioral changes, invariants touched, schema or contract changes, tests added or updated, and any governance or documentation ripple effects. Avoid marketing language, avoid poetry, and do not restate unchanged files.
```

This repo wants reviewer context, not marketing copy or release-note theater.

## Path filters

```text
!**/__pycache__/**
!**/*.pyc
```

## Path instructions

### `supervisor/**/*.py`

```text
Treat this as deterministic supervisor/runtime code, not app-layer glue.
Prioritize correctness findings over style suggestions.
Focus on:
- illegal phase transitions, terminal-state invariants, and stop conditions
- single-writer / single-browser ownership assumptions
- evidence, report, and artifact correctness
- path, shell, contract, and worktree safety regressions
- prompt text not replacing code-level enforcement
```

### `tests/**/*.py`

```text
Focus on invariant coverage and regression protection.
Flag missing tests when the diff changes:
- illegal transitions or forbidden operations
- failure fingerprinting or report/evidence behavior
- contract parsing, policy guardrails, or worktree safety
Avoid asking for duplicate coverage when existing tests already cover the behavior.
```

### `schemas/**/*.json`

```text
Focus on contract compatibility and source-of-truth drift.
Flag:
- required-field or enum changes without coordinated companion updates
- schema/example/name mismatches versus supervisor code
- changes that silently widen or weaken validation semantics
```

### Live docs and governance surfaces

Path:

```text
{README.md,AGENTS.md,AGENTS.project.md,CLAUDE.md,CONTINUITY.md,COHERENCE.md,GUIDE.md,IMPLEMENTATION-PLAN.md,LINEAR.md,LOGIC.md,PROJECT_INTENT.md,PROMPTS.md,QUEUE-RUNS.md,RULES.md,STRUCTURE.md,canonical-architecture.md,todo.md,docs/**/*.md}
```

Instructions:

```text
Treat these as live governance or source-of-truth documents.
Focus on:
- contradictions against canonical-architecture.md, RULES.md, CONTINUITY.md, COHERENCE.md, and LINEAR.md
- missing Ripple Check companion updates across live docs
- broken cross-references, stale process claims, or governance drift
Avoid low-value prose nitpicks when the meaning is already clear.
```

### `design-history/**/*.md`

```text
Treat this directory as archive material, not live source-of-truth docs.
Do not suggest normalizing superseded terminology or rewriting history to match current docs unless the pull request explicitly intends archive repair.
Only flag changes for accidental corruption, broken references, or factual mistakes introduced by the current diff.
```

## UI-only and caveated settings

These settings were discussed in chat and are intentionally preserved here even
when they are not encoded in repo config or need a support caveat.

### Leave blank

- `High level summary placeholder`
- `Auto title placeholder`
- `Auto title instructions`
- `Labeling instructions`

Reason:

- the repo does not want `CodeRabbit` rewriting the PR body or title by default
- label suggestion is off, so labeling instructions would be dead config

### Labeling instructions

The current recommendation is to leave label instructions empty because:

- `suggested_labels` is off
- `auto_apply_labels` is off
- this repo does not currently benefit from automated PR labeling

If the repo later turns label suggestions on, the first and only pre-seeded
instruction should be:

Label: `slop`

Instruction:

```text
Suggest this label only when the PR appears low-quality, overly noisy, mechanically generated without sufficient repo-specific reasoning, or bundles unrelated changes with weak verification. Do not suggest it for normal large diffs, docs-heavy PRs, or intentionally broad refactors that are still coherent and verified.
```

### Anti-Slop

Desired UI setting:

- enabled
- label: `slop`

Important caveat:

According to CodeRabbit's configuration reference, slop detection is only for
public GitHub repositories as of the current docs refresh. That means this
setting should be treated as a desired review preference, not a core part of
the repo's trusted workflow unless the hosting/support conditions actually
match.

## What remains manual

- install and authorize the `CodeRabbit` GitHub App for this repository
- open or update a real PR so `CodeRabbit` actually reviews it
- calibrate the trial on 3-5 real PRs before enabling stronger gating such as
  `request_changes_workflow`

## References

- Official YAML setup guide:
  [CodeRabbit Configuration via YAML](https://docs.coderabbit.ai/getting-started/yaml-configuration)
- Official schema-derived configuration reference:
  [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
