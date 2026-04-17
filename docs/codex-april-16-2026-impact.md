# Codex April 16, 2026 Impact

**Date:** April 16, 2026  
**Source:** [OpenAI: Codex for (almost) everything](https://openai.com/index/codex-for-almost-everything/)  
**Purpose:** Record how the April 16, 2026 Codex product update should affect
this repository's tooling and operating guidance without silently rewriting the
canonical architecture.

`PROJECT_INTENT.md`, `canonical-architecture.md`, and `QUEUE-RUNS.md` remain
authoritative. If this memo conflicts with those docs, the canonical docs win.
This memo is an interpretation and prioritization aid, not a hidden architecture
change.

## What changed in the April 16 update

OpenAI's April 16, 2026 Codex update expands Codex beyond code editing alone.
The official release says Codex can now:

- operate the local computer with background computer use
- use an in-app browser for web work
- generate images in the same workflow
- remember preferences and learn from prior actions
- resume and schedule ongoing work through stronger automations
- work more deeply across developer workflows such as PR review comments,
  multiple terminals, remote devboxes over SSH, and more plugins

This matters here because this repo is designing a long-running autonomous
delivery harness, not just a prompt collection.

## Adopt now

These are good fits immediately, but as operator workflow or repo-guidance
improvements rather than v1 runtime authority changes.

### 1. Treat long-running Codex sessions as a better operator tool

The update strengthens the case for the repo's issue-by-issue queue model:
separate issue runs, durable closeout, resumed work, and ongoing automation.
That aligns with `README.md` and `QUEUE-RUNS.md` rather than conflicting with
them.

Use now:

- resumed work across bounded issue runs
- automation for follow-up work and recurring review tasks
- richer operator-side oversight of longer Codex tasks

Do not infer from this that Codex memory becomes repo truth. The repo still
requires durable records in files.

### 2. Use richer developer-workflow features during real target-repo work

The update's support for PR review comments, multiple terminals, and SSH
devboxes is immediately useful when this repo starts validating against real
implementation repos.

Use now:

- GitHub review-comment workflows during audit or repair work
- multi-terminal sessions when comparing repo truth, verification output, and
  runtime state
- SSH devboxes when the target repo or app cannot be exercised locally

This is a tooling improvement, not permission to move merge/deploy authority
away from the deterministic supervisor.

### 3. Use computer use and the in-app browser as exploration aids

The new browser/computer-use capabilities are useful for exploring UI changes,
checking frontend behavior, and speeding up operator iteration. They are a good
operator-assist layer for this repo's future UI and target-repo work.

Use now:

- exploratory frontend checks
- faster design iteration for app/UI work
- non-API app interactions during manual investigation

Keep the authority boundary: Playwright remains the intended verifier in v1.

### 4. Use only the plugins that improve routing or auditability now

The April 16 update makes plugins more useful, but this repo should adopt them
selectively. Use plugins that reinforce routing, review, and context gathering.
Do not turn them into a new workflow owner.

## Defer for v1

These are plausible future capabilities, but they should remain outside the v1
core runtime until the supervisor path is proven.

### 1. Multi-agent parallel work inside the runtime

The product now supports more parallel agent workflows, but this repo's v1
architecture still requires one code-writing agent per run worktree. Parallel
agents may help the human operator or this repo's own authoring process, but
they should not weaken the runtime's single-writer guarantee.

### 2. Memory as a runtime dependency

The update's memory feature is useful for user experience and operator help, but
this repo explicitly rejects transcript-driven truth and external semantic-memory
dependence in v1. Memory can remain an operator convenience or later v1.1
investigation, not a source of durable authority.

### 3. Browser/computer-use as the primary verifier

The update improves interactive browser use, but v1 still wants deterministic
verification. Keep Playwright as the browser owner for authoritative readiness
claims. Computer use can support exploration, not replace the verifier.

### 4. Broad plugin-driven expansion

The update adds many plugins, but this repo explicitly does not want broad
plugin-marketplace integration as part of the v1 core system. More plugins
should be evaluated later only when they clearly reduce operator toil without
creating a second control plane.

## Explicitly reject in docs

These should stay explicitly out of bounds unless the canonical architecture is
changed on purpose.

### 1. Do not let Codex memory replace repo memory

Repo truth still belongs in version-controlled docs, `todo.md`, and runtime
artifacts named by the supervisor. Memory may speed up an agent, but it does not
become an authoritative source.

### 2. Do not relax single-writer discipline

The product update makes parallel work more attractive, but this repo's v1
discipline is still one writer and one browser owner. Parallelism is not a free
upgrade here; it would materially change the legality model.

### 3. Do not let plugins or integrations become workflow authority

Linear, GitHub, and other tools remain routing, context, and audit surfaces.
They do not get to issue privileged commands or bypass supervisor
normalization.

### 4. Do not treat the April 16 update as permission for autonomous merge or deploy

The update improves tooling breadth, not the repo's acceptance of auto-merge or
production deployment in v1.

## Plugin fit for this repo

The plugins currently enabled in this environment are unevenly useful for this
repository.

| Plugin | Fit now | Best use here | Why not more |
|---|---|---|---|
| `Linear` | High | issue creation, queue hygiene, routing metadata, provenance checks | must remain routing-only, never workflow authority |
| `GitHub` | High | PR review comments, CI context, review loops, audit follow-up | GitHub is still an external validator, not the owner |
| `Figma` | Medium later | future operator UI or app-supervisor UI design work | low immediate value while the repo is still mostly docs/governance |
| `Vercel` | Medium later | preview environments, frontend verification, AI SDK experiments | v1 explicitly avoids auto-deploy and hosted-platform dependence |
| `Cloudflare` | Medium later | webhook intake hosting, Workers experiments, possible workflow substrate exploration | platform choice is not settled here and should not be backdoored by plugin availability |
| `Gmail` | Low now | operator follow-up and automation experiments | does not materially advance the core runtime design |
| `Google Calendar` | Low now | reminders, review cadence, operator scheduling | useful operationally, not architecturally central |

Notes:

- The April 16 update also highlights more plugins in general, but the repo
  should still adopt only the narrow set that supports routing, review, or
  tightly bounded operator workflows.
- `Superpowers` is discussed separately in
  `docs/superpowers-playbook.md`. It is relevant to workflow discipline, but it
  is not one of the enabled plugins listed for this session.

## Recommended next stance

For this repo, the April 16 update should be read as:

- **yes** to better operator workflows, richer review loops, resumed work, and
  stronger issue-by-issue Codex sessions
- **not yet** to memory-backed truth, plugin-heavy runtime expansion, or
  multi-writer runtime parallelism
- **no** to weakening the deterministic supervisor, Playwright ownership, or
  repo-truth discipline

## Follow-up disposition

No new canonical-architecture change is required from this memo alone.

- Existing Phase 2 work already covers the core Codex integration question.
- Existing queue and governance docs already cover why Linear and GitHub remain
  bounded surfaces.
- Plugin expansion beyond `Linear` and `GitHub` is deferred unless a later task
  proves a concrete need.
