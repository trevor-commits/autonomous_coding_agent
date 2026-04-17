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

The `Plugin decision ledger` section below is the curated current-truth place
to track plugin conclusions for this repo. Future Codex conversations should
append raw plugin observations and trial notes to `docs/plugin-intake.md`, then
update the ledger only when the repo's actual plugin stance changes.

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

## Plugin decision ledger

This is the durable plugin tracker for this repository. When a later Codex
conversation discusses a plugin, runs a real plugin-backed task, or changes the
conclusion, update the matching row here instead of starting a second tracker.

`Tried here?` means the repo has a durable record of real plugin use or a
repo-side workflow trial. Merely having a plugin available in the session does
not count as tried.

| Plugin | Tried here? | Current stance | Use now for | Do not use for | Revisit trigger |
|---|---|---|---|---|---|
| `Linear` | Yes | Use now, bounded | issue creation, queue hygiene, routing metadata, provenance checks | workflow authority or storing acceptance criteria and decisions in Linear | only if the queue contract or Linear boundary changes |
| `GitHub` | No durable repo-side trial yet | Use now, bounded when needed | PR review comments, CI context, and audit follow-up in real target-repo work | making GitHub the owner of repo truth, queue legality, or task acceptance | when target-repo PR and CI work becomes active |
| `Superpowers` | Yes | Use now, selectively | governance/design discipline, planning, review, and honest closeout checks | turning docs-only work into heavy process, branch churn, or subagent theater | when this repo becomes implementation-heavy enough to justify broader skill stacks |
| `Autopilot` | Installed locally; no task-backed repo-side run yet | Use selectively for fuzzy project intake | discovery questions, brief creation, route selection, and handoff framing when a project starts as an idea instead of a bounded issue | routine bounded repo tasks or implementation execution once direction is already known | when a real project starts from a vague idea and needs route shaping before spec or build work |
| `HOTL` | Installed locally; no task-backed repo-side run yet | Use now, selectively | implementation discipline, review, verification, and resumable execution once a bounded plan exists | replacing repo truth, acting as queue authority, or forcing heavy ceremony on trivial fixes | when a real implementation slice or risky repair needs stronger execution guardrails |
| `Cavekit` | Installed locally; no task-backed repo-side run yet | Use selectively for spec-heavy work | requirements, acceptance criteria, build-task decomposition, and pre-build traceability; current Blueprint-family candidate | rediscovering already-approved plans or owning the whole implementation loop | when a fuzzy or large feature needs real spec/decomposition before code |
| `CodeRabbit` | Repo-side config landed; operator chose to trial it first; live GitHub PR-review run still pending | Use now, bounded as the active dedicated-review trial | dedicated PR review, deterministic/mechanical pre-audit, and bug/security/lint/test signal before Claude or human review | replacing repo-truth review, architectural audit, or completion authority | after 3-5 real PRs show whether its review quality justifies the cost and any stronger gates |
| `plugin-eval` | No durable repo-side run yet | Use now, bounded | benchmarking plugins, models, or workflow variants before adoption decisions | replacing architectural judgment with a single score or installing plugins on vibes | whenever a plugin or workflow choice is contested and evidence is cheaper than debate |
| `Brooks Lint` | No | Run a spike later | second-pass code review with a maintainability and test-quality lens | default review ownership or a substitute for deterministic/scanner review | if `CodeRabbit` plus Claude review still misses maintainability or test-quality issues |
| `Session Orchestrator` | No | Study / spike later | wave execution, quality gates, and clean session close-out as a possible execution envelope | becoming the default queue or supervisor substrate before this repo resolves its own execution model | if real implementation work shows the current execution envelope is too thin |
| `Agent Message Queue` | No | Later / conditional | file-based agent handoffs and cross-session messaging if real multi-agent collaboration appears | adding a messaging bus before cross-session handoff is a concrete bottleneck | if cross-project or cross-session handoffs become recurring operational pain |
| `Registry Broker` | No | Do not adopt now | specialist delegation only if later proven necessary | introducing brokered delegation before local subagents and the repo role chain are exhausted | if the repo later needs external specialist pools beyond local subagents |
| `Claude Code for Codex` | No | Later / conditional | tracked Claude review, rescue, or background jobs launched from Codex | duplicating the existing Codex-to-Claude bridge and audit chain without a concrete tracked-job need | if background Claude review or rescue jobs become operationally valuable |
| `ECC` | No | Study as a source library only | harvesting specific TDD, security, or verification ideas from a large skill catalog | wholesale install that lets a giant external workflow redefine this repo | if a specific capability is needed and smaller plugins do not cover it |
| `Figma` | No | Later / conditional | operator UI or app-supervisor UI design work | early-stage governance work where it adds no leverage | when a real UI surface is in scope |
| `Vercel` | No | Later / conditional | preview environments, frontend verification, and AI SDK experiments | auto-deploy authority or hosted-platform dependence in the v1 core | when preview or frontend workflow becomes real |
| `Cloudflare` | No | Later / conditional | webhook intake hosting, Workers experiments, and possible workflow-substrate exploration | backdooring the hosting/runtime decision through plugin availability | when the runtime hosting choice is actively being made |
| `Gmail` | No | Low now | operator follow-up and reminder workflows | core runtime or control-plane responsibilities | when operator follow-up pain becomes concrete |
| `Google Calendar` | No | Low now | review cadence, reminders, and operator scheduling | core runtime or repo-authority work | when scheduling friction becomes a real bottleneck |
| `Hugging Face` | No | Not yet evaluated; do not adopt by default | model/dataset research or remote-job experiments only if a concrete repo need appears | widening the repo around hosted ML tooling without a specific architecture need | when a real model-eval, dataset, or remote-job task exists |

Notes:

- The current allow-now set is still role-bounded rather than plugin-maximal:
  `Linear`, `GitHub`, `Superpowers`, `HOTL`, `CodeRabbit`, and
  `plugin-eval` are usable now inside the limits above.
- `Autopilot` and `Cavekit` are installed locally but should remain selective
  phase owners, not default workflow owners.
- The current code-review comparison call for this repo is: `GitHub Copilot`
  still looks better on cost and GitHub-native integration for a small private
  repo, but `CodeRabbit` is still the likelier stronger dedicated PR-review
  product. Trevor chose to test review quality first, so `CodeRabbit` is the
  active trial path and Copilot remains the cheaper fallback baseline for later
  re-evaluation.
- `CodeRabbit` now has repo-local configuration at `.coderabbit.yaml`, but the
  GitHub App installation and first live PR review are still manual operator
  work rather than a completed repo-side automation step.
- `docs/coderabbit-review-settings.md` is the detailed operator companion for
  the exact CodeRabbit settings, caveats, and reasoning behind the current
  trial posture.
- `docs/superpowers-playbook.md` remains the detailed usage guide for
  `Superpowers`; this ledger records the decision status, not the full
  workflow.
- `docs/codex-plugin-operator-cheatsheet.md` is the operational companion for
  `Autopilot`, `HOTL`, `Cavekit`, `CodeRabbit`, and `plugin-eval`.

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
- Plugin adoption remains bounded by the ledger above. Anything outside the
  allow-now set stays deferred, low-priority, or not-yet-evaluated until a
  later task proves a concrete need.
