# Superpowers Playbook

Repo-specific guidance for using the `Superpowers` plugin in this repository.

`PROJECT_INTENT.md` and `canonical-architecture.md` still define what this repo
is for. This document only explains when Superpowers skills help versus when
they create unnecessary process overhead.

## Current repo reality

This repository is still mostly a source-of-truth architecture and governance
repo. The main risks here are:

- architecture drift
- companion-doc drift across live docs
- plans that are too vague to implement cleanly later
- closing governance work without durable verification

That means the best Superpowers usage here is design discipline and review
discipline, not implementation ceremony.

## Recommended default stacks

### Architecture, contract, or governance changes

Use this when changing `canonical-architecture.md`, `RULES.md`, `PROMPTS.md`,
`LINEAR.md`, `QUEUE-RUNS.md`, or other live design/governance surfaces.

Recommended stack:

1. `brainstorming`
2. `writing-plans` when the change implies follow-on implementation work or a
   multi-step rollout
3. `requesting-code-review`
4. `verification-before-completion`

Why:

- The main failure mode is bad design or cross-doc inconsistency, not missing
  code.
- These skills improve decision quality and reduce companion-doc drift.

### Audit follow-up or contradiction resolution

Use this when two docs, two audits, or a doc and a workflow disagree.

Recommended stack:

1. `systematic-debugging`
2. `requesting-code-review`
3. `verification-before-completion`

Why:

- The debugging skill is still useful when the "bug" is a process contradiction
  or broken contract, not just executable code.

### Future runtime implementation kickoff

Use this only once the repo starts landing real supervisor/runtime code.

Recommended stack:

1. `brainstorming`
2. `writing-plans`
3. `test-driven-development`
4. `requesting-code-review`
5. `verification-before-completion`

Why:

- At that point the repo starts behaving more like an implementation repo and
  TDD becomes worth the cost.

## Skills that fit well here

- `brainstorming`: best first step for architecture, workflow, prompt, and
  contract changes.
- `writing-plans`: good for turning repo truth into bounded implementation
  phases or rollout steps.
- `requesting-code-review`: good for multi-doc consistency checks.
- `verification-before-completion`: always useful before claiming a governance
  landing is done.
- `systematic-debugging`: useful when repo rules, queue semantics, or audit
  results conflict.

## Skills that are conditional

- `test-driven-development`: use only when this repo contains real runtime code
  for the supervisor or related execution surfaces.
- `executing-plans`: useful once implementation work exists and the plan is
  already accepted.
- `receiving-code-review`: use when addressing substantive external audit
  feedback rather than just filing or summarizing it.

## Skills that are usually overkill here

- `using-git-worktrees`: still useful only when there are concurrent chats or a
  real isolation need beyond the default task-branch workflow.
- `subagent-driven-development`: high overhead for a repo whose main surface is
  still docs and governance.
- `dispatching-parallel-agents`: only worth it if there are clearly independent
  write scopes, which is uncommon in companion-doc work.
- `finishing-a-development-branch`: relevant once a task branch is pushed and
  waiting for review or merge, but still overkill for very small doc-only tasks.

## Repo-specific guardrails

- Do not apply the full Superpowers workflow mechanically. The repo's own
  AGENTS, Continuity, Coherence, and Linear-Core rules are stricter and more
  specific than the plugin defaults.
- Treat Superpowers as a decision-quality layer first, not as a reason to add
  more process than the repo needs.
- When a change touches multiple live docs, prioritize Ripple Check discipline
  over ritual TDD or extra branch choreography beyond the repo's default
  task-branch flow.
- If a task is a direct question or a very small doc correction, a lightweight
  `verification-before-completion` pass is usually enough.

## Practical rule of thumb

For this repo, use Superpowers mostly to make designs clearer, plans sharper,
and closeouts more honest.

Do not use it as an excuse to run an implementation-heavy workflow against a
documentation-first repository.
