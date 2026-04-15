# Feedback Reconciliation

> Historical archive note: this document preserves the April 2026 feedback thread as decision history. Use `../todo.md`, `../WORK-LOG.md`, `../canonical-architecture.md`, and `../REPO_MAP.md` for the current repo state.

**Date:** April 14, 2026  
**Status:** Historical decision record and audit-memory document  
**Authority:** This document is not the architectural source of truth. `canonical-architecture.md` remains the implementation authority.  
**Purpose:** Preserve the reasoning, sequence, disagreements, corrections, and resulting decisions from the April 2026 multi-AI repo-audit thread so future sessions do not have to reconstruct the logic from chat transcripts.

## 1. Why This Exists

The user explicitly wanted this repository to:

- start strong
- be thorough enough to have a real chance of succeeding
- avoid predictable future failure
- preserve the logic and reasoning behind design and process decisions
- record not just the final answer, but how the decision was reached

This document captures that thread.

## 2. Repo State At Time Of Review

At the time of this reconciliation, the repository was still a documentation-first project.

Observed state:

- 18 files at max depth 2
- approximately 8,737 lines of Markdown
- no `schemas/`
- no `supervisor/`
- no `tests/`
- no `.github/`
- no repo-local implementation scaffolding beyond the planning documents

Key live documents reviewed:

- `README.md`
- `GUIDE.md`
- `AGENTS.md`
- `PROJECT_INTENT.md`
- `canonical-architecture.md`
- `LOGIC.md`
- `RULES.md`
- `STRUCTURE.md`
- `PROMPTS.md`
- `IMPLEMENTATION-PLAN.md`
- `todo.md`

Key repo truth at the time:

- The canonical architecture was already supervisor-centered, not AI-manager-centered.
- The repo itself was still too prose-heavy and too weak at the machine boundary.
- The main remaining risk had shifted from "bad architecture" to "good architecture, under-specified repo."

## 3. Repo-Grounded Baseline Before Evaluating The Feedback

Before judging any external audit, the following repo-grounded conclusions were established from the checked-in docs.

### 3.1 What The Canonical Architecture Already Solved

The current source of truth already established:

- deterministic supervisor ownership of workflow correctness
- bounded AI strategy instead of AI-owned legality
- typed domain actions instead of raw shell or git control
- repo contract plus run contract as the automation interface
- deterministic final gate and evidence-backed readiness
- one writer and one browser owner
- structured defect packets and structured run artifacts
- exclusion of transcript-sharing memory and external semantic memory in v1

This matters because several external audits criticized older design states that were already superseded in `canonical-architecture.md`.

### 3.2 What The Repo Still Lacked

The strongest remaining problems were not the top-level architecture. They were repo-operational gaps:

- `PROJECT_INTENT.md` was still an empty template
- no standalone schemas existed for the machine-facing boundaries
- terminal-state and readiness vocabulary had drifted across companion docs
- repo-vs-target-repo folder ownership was ambiguous
- companion docs duplicated too much operational detail
- Phase 5 hardening was still too ambitious for a repo with zero code

## 4. Audit Thread Chronology

This section records what each AI said, what was useful, what was wrong or stale, and how the repo owner chose to interpret it.

### 4.1 ChatGPT Pro: Initial Architecture / Governance Audit

Main thrust:

- the repo was not yet set up in the best way
- supervisor should own correctness
- typed actions should replace raw mutation verbs
- repo contracts should be mandatory
- completion should be deterministic
- worktree-per-run should replace a looser git model
- operational state should move out of mutable Markdown
- GitHub governance and security defaults should be added

What was useful:

- strong emphasis on contracts
- strong emphasis on typed actions
- strong emphasis on deterministic completion
- strong emphasis on structured runtime state
- strong emphasis on not over-trusting prompts

What was stale or inaccurate relative to the current repo:

- it treated raw `git_command`, `run_hook`, `write_memory`, and `declare_complete` as if they were still the active design rather than banned examples in the canonical document
- it criticized a manager-centric control model that had already been replaced in the current source of truth
- it described `docs/agent-memory/*` as if it were still the active runtime substrate, even though the canonical architecture had already shifted to `.autoclaw/runs/` and `.autoclaw/memory/`

Decision:

- accept the implementation-direction advice
- reject the stale diagnosis of the current canonical architecture

### 4.2 Claude Response To ChatGPT Pro

Main thrust:

- mostly agreed with the critique
- emphasized supervisor-centric control, typed actions, repo contract, completion gate, worktree-per-run, and memory layering
- softened the priority of GitHub governance
- called out failure fingerprinting, budgets, and observability as underweighted

What was useful:

- prioritization of supervisor-enforced control
- emphasis on hard completion legality
- emphasis on failure fingerprinting and budget enforcement

What was weak:

- it still treated the current repo as if the canonical document had not already made the supervisor-centric rewrite
- it relied too much on prior memory and not enough on the actual checked-in repo state

Decision:

- accept the prioritization
- reject the implication that the canonical architecture still needed the fundamental control-path rewrite

### 4.3 Codex Repo-Grounded Correction

Main thrust:

- the canonical architecture was already supervisor-centered and bounded
- stop re-litigating top-level architecture
- shift focus to implementation surfaces and machine-checkable boundaries

Core correction:

- the repo's bottleneck was no longer "wrong architecture"
- the bottleneck was "right architecture, insufficient repo discipline and executable structure"

Decision:

- use checked-in repo state as the primary evidence source for all later judgments in the thread

### 4.4 ChatGPT Pro: Follow-Up Repo-Hardening Audit

Main thrust:

- the next layer of improvement should be contracts, schemas, self-tests, reproducible environments, CI/security hardening, and replay discipline
- the harness should test itself, not only target repos
- every boundary should become schema-checked
- runtime state should not be primarily Markdown
- GitHub hardening and Playwright Test should be standardized

What was useful:

- the self-testing harness recommendation
- schema-everywhere recommendation
- machine-checkable repo recommendation
- distinction between repo truth and run truth

What was overstated or premature:

- GitHub governance was still presented too close to the core execution path for a docs-only repo
- OIDC and some hosted-workflow hardening were good later, not Phase 0 blockers
- some Codex/OpenAI guidance was generic rather than repo-specific

Decision:

- accept schemas, self-tests, and structured state as urgent
- defer most GitHub and hosted-workflow hardening until executable surfaces exist

### 4.5 Claude Code Repo Audit

Main thrust:

- the architecture was sound
- the repo was drifting toward "docs about docs"
- the implementation-facing glue was missing or contradictory

Critical issues it raised:

- `PROJECT_INTENT.md` was an empty template
- no canonical schema files existed for `StrategyDecision` and failure fingerprints
- `COMPLETE` legality was not bolted down tightly enough in one place
- Codex availability and fallback were under-specified
- design-history clutter and doc duplication were raising cognitive load

What was especially strong:

- grounded in actual files
- pointed to specific contradictions and drift risks
- prioritized the issues that would block a Phase 0 implementer immediately

What needed correction:

- it claimed `todo.md` and `IMPLEMENTATION-PLAN.md` contradicted each other on Phase 0 status; at the time of review, both still treated Phase 0 as pending

Decision:

- treat this as the strongest repo-grounded audit in the thread
- accept almost all of it, with the specific contradiction claim corrected

### 4.6 Claude Cowork Synthesis

Main thrust:

- schemas, contracts, and self-tests should come before governance hardening
- Claude Code's repo-grounded audit should carry more weight than generic GitHub-hygiene advice
- OIDC, rulesets, and some governance overhead were later-stage work

What was useful:

- the sequencing was right
- it correctly highlighted convergence across independent audits

Decision:

- accept its prioritization

### 4.7 ChatGPT Pro Final Synthesis

Main thrust:

- adopt most of Claude Code's critical issues
- adopt schema/contract/self-test priorities from the earlier feedback
- defer governance theater until the repo stops being docs-only
- stop writing new architecture narratives

What was useful:

- the strongest version of its sequencing advice
- explicit call to freeze doc sprawl and build executable truth

What still needed correction:

- it again described the architecture as if it still exposed the older prompt-centric control model

Decision:

- accept the sequencing
- reject the stale architecture diagnosis

## 5. Convergence Across Independent Feedback

These themes appeared repeatedly across the thread and were treated as real signal.

### 5.1 Schemas Were Missing

Repeated by:

- ChatGPT Pro
- Claude Code
- Claude Cowork
- Codex repo-grounded analysis

Conclusion:

- the repo was too prose-driven at the machine boundary
- standalone schemas became an accepted near-term requirement

### 5.2 Markdown Should Not Be The Primary Runtime State

Repeated by:

- ChatGPT Pro
- Claude Code
- Claude Cowork
- Codex repo-grounded analysis

Conclusion:

- Markdown remained appropriate for architecture, rules, prompts, and historical reasoning
- runtime state, readiness, defect routing, and execution evidence should be structured

### 5.3 The Repo Needed To Become Machine-Checkable

Repeated by:

- ChatGPT Pro
- Claude Code
- Claude Cowork
- Codex repo-grounded analysis

Conclusion:

- the repo had crossed the point where more prose added less value than schemas, tests, and executable invariants

## 6. Final Decisions From This Thread

These were the repo-grounded decisions taken from the conversation.

### 6.1 Decisions Accepted

- fill `PROJECT_INTENT.md` instead of leaving a `TODO: verify` template
- add standalone schemas before implementation depends on them
- normalize terminal-state and readiness vocabulary in one place
- clarify this repo vs target-repo ownership before Phase 0 code work
- add invariant tests for the supervisor itself early
- reduce v1 action and memory scope to a smaller minimum viable set
- move toward less root clutter and clearer separation of live docs vs history
- stop producing new architecture narratives until executable surfaces exist

### 6.2 Decisions Accepted With Scope Limits

- structured runtime state:
  accepted, but only for machine state; architecture reasoning still belongs in Markdown
- GitHub governance:
  accepted as worthwhile, but not as the next blocking step for a docs-only repo
- Playwright Test:
  accepted as the right direction for the UI lane, but not before Phase 1 and supervisor basics exist
- `acpx` fallback planning:
  accepted as a design issue, but not enough to block Phase 0 documentation cleanup

### 6.3 Decisions Deferred

- OIDC
- advanced rulesets
- CODEOWNERS and branch-protection expansion
- CodeQL
- Dependabot
- secret-scanning hardening beyond standard hygiene
- full operational-memory hardening
- flaky-test quarantine
- resume / interruption recovery
- rate-limit backoff
- retention policies

These were deferred because the repo still lacked executable runtime code, schemas, and tests.

### 6.4 Decisions Rejected Or Corrected

- rejected the claim that the current canonical architecture still centered an AI manager
- rejected the claim that raw `git_command`, `run_hook`, or `write_memory` remained live actions in the active design
- corrected the claim that `todo.md` and `IMPLEMENTATION-PLAN.md` already disagreed on whether Phase 0 was complete
- rejected the idea that another architecture rewrite was the highest-value next step

## 7. Failure Modes This Thread Tried To Prevent

The user explicitly wanted to think ahead about what could go wrong. The following failure modes were treated as the ones most likely to waste time or doom the project later.

### 7.1 False-Green Completion

Cause:

- inconsistent meanings for `COMPLETE`, `READY`, `BLOCKED`, `UNSUPPORTED`, `NOT_READY`, and `NEEDS_MORE_EVIDENCE`

Why dangerous:

- the system can appear to be done while still missing required proof

### 7.2 Wrong Repo / Wrong Boundary Implementation

Cause:

- ambiguity between what belongs in this repo versus in a target repo

Why dangerous:

- the first implementer can build contracts, schemas, fixtures, or run-state machinery in the wrong place

### 7.3 Parser Drift

Cause:

- prose describing machine outputs that have no concrete schema

Why dangerous:

- strategy, defect routing, readiness, and reports drift the moment code starts consuming them

### 7.4 Memory Poisoning

Cause:

- building cross-run memory before failure normalization and post-run validation are stable

Why dangerous:

- the system may learn the wrong thing and repeat bad strategies more confidently

### 7.5 Toolchain Deadlock

Cause:

- vague expectations around Codex, Claude access, Playwright, and fallback paths

Why dangerous:

- the build path can stall before the first useful run

### 7.6 Governance Before Substance

Cause:

- spending early effort on branch/ruleset/security ceremony before the repo has code to protect

Why dangerous:

- time is burned without reducing the main implementation risk

### 7.7 Companion-Doc Drift

Cause:

- the same operational rules repeated across multiple Markdown docs

Why dangerous:

- future edits change one copy and silently invalidate another

## 8. Resulting Priority Shift

The thread changed the effective near-term priorities.

### Previous practical priority

- keep refining architecture and companion docs
- prepare for eventual implementation

### Updated practical priority

1. clean the repo so it has one clear truth
2. define the machine boundaries with standalone schemas
3. normalize terminal-state legality and repo ownership rules
4. build the smallest executable supervisor/test surface
5. defer governance and hardening that do not unblock those steps

## 9. Relationship To Other Repo Documents

This document should be read as:

- a historical explanation of how the repo owner evaluated external AI feedback
- a durable memory record for why certain audit recommendations were accepted, deferred, or corrected
- a companion to `todo.md` audit and feedback logs

This document should **not** be read as:

- the source of truth for architecture
- a replacement for `canonical-architecture.md`
- a replacement for future schemas, tests, or contracts

## 10. Practical Takeaway

The main conclusion from the April 2026 multi-AI audit thread was:

**The architecture was good enough to build from. The repository was not yet disciplined enough to build from efficiently.**

That shifted the work from:

- "argue about the control model"

to:

- "make the repo machine-checkable, tighter, and less ambiguous before implementation starts"

## 11. Current Intent Of This Record

Future sessions should be able to answer these questions without reopening the entire chat transcript:

- What did each AI actually say?
- Which parts were stale because they described older designs?
- Which criticisms were grounded in the real repo?
- Which recommendations were accepted, deferred, or rejected?
- What failure modes were considered before implementation started?
- Why did the repo owner choose the current priority order?

That is the reason this document exists.
