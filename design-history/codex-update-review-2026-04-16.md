# Codex Update Review And Repo-Fit Analysis — 2026-04-16

## Purpose

Preserve the reasoning behind the 2026-04-16 research pass over the latest Codex CLI release so later AI auditors can reconstruct:

- what Trevor asked for
- what external evidence was consulted
- which new Codex capabilities matter for this repo's operating model
- which are worth adopting, which need further evaluation, and which are rejected
- which adoption candidates are queued for Trevor selection before Linear issues are opened

This is a design-history memo, not an active source-of-truth doc. Current truth still lives in `canonical-architecture.md`, `QUEUE-RUNS.md`, `LINEAR.md`, `PROMPTS.md`, `RULES.md`, `AGENTS.project.md`, `IMPLEMENTATION-PLAN.md`, and `todo.md`.

## Trigger

Trevor asked Cowork to heavily research the latest Codex update and evaluate how its new features and plugins could help this repo.

Operating constraints carried into the analysis:

- Cowork is the orchestrator/auditor; Codex is the worker; Claude Code is the primary auditor.
- Linear remains routing metadata; the supervisor owns queue legality and commit landing.
- Fresh Codex conversation per bounded task; no transcript hoarding.
- Codex is the sole writer in v1; Playwright is the sole browser owner.
- Every governance change must ripple across companion docs in the same commit.

## Working Question

Given the Codex CLI at v0.121.0 (GA) and v0.122.0-alpha.x (2026-04-15 / 2026-04-16), which newly shipped capabilities map cleanly onto this repo's deterministic supervisor, queue contract, audit chain, and prompt system, and which should be deferred or rejected because they conflict with the repo's authority model?

## Codex Update Under Examination

**Release window:** 2026-04-11 (v0.120.0) through 2026-04-16 (v0.122.0-alpha.5). Primary GA target is v0.121.0, published 2026-04-15.

### Inventory Of New Capabilities

1. **Plugin distribution surface** — `codex marketplace add` supports installing plugin marketplaces from GitHub, git URLs, local directories, and direct `marketplace.json` URLs. The CLI exposes `/plugins` to manage installed plugins. A plugin bundles skills, optional app connectors, and MCP servers.
2. **Skills authoring format** — Skills are now the canonical authoring unit. A skill is a directory with a required `SKILL.md` (YAML frontmatter + markdown body) plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`. Codex discovers skills hierarchically from `.agents/skills/` (repo), `~/.agents/skills/` (user), `/etc/codex/skills/` (admin), and bundled system skills, and uses progressive disclosure (reads metadata first, full body only when invoked).
3. **Subagents** — `[agents]` config block plus per-agent TOML under `~/.codex/agents/` or `.codex/agents/`. Defaults: `max_threads=6`, `max_depth=1`. Subagents inherit parent sandbox/approval/MCP overrides. Includes an experimental `spawn_agents_on_csv` tool for batch-spawning one worker per CSV row.
4. **`/review` presets** — Built-in review modes: against a base branch, uncommitted changes, a specific commit, or custom instructions. Each run lands as its own turn for side-by-side comparison.
5. **Thread automations** — Schedule wake-ups that preserve conversation context, targeted at long-running process checks or follow-up loops.
6. **Memory controls** — TUI and app-server controls for memory mode, reset/deletion, and memory-extension cleanup. "Memories" explicitly designed to carry preferences and project conventions across threads.
7. **`codex exec-server` (experimental)** — Remote/app-server subcommand with egress websocket transport, remote `--cd` forwarding, runtime remote-control enablement, and sandbox-aware filesystem APIs.
8. **Realtime V2** — Streams background agent progress while work is still running; queues follow-up responses.
9. **MCP expansion** — Resource reads, tool-call metadata, custom-server tool search, server-driven elicitations, file-parameter uploads, namespaced MCP registration, parallel-call opt-in, sandbox-state metadata for MCP servers.
10. **Sandbox hardening** — Secure devcontainer profile with bubblewrap support; macOS sandbox allowlists for Unix sockets; removed the `danger-full-access` denylist-only network mode; macOS sandbox/proxy fix for private DNS.
11. **Consumer-surface features (informational only)** — In-app browser, computer use for macOS (not in EEA/UK/CH), task sidebar, artifact viewer for PDF/spreadsheet/doc previews, PR review sidebar with GitHub integration, SSH remote connections (alpha), multi-window support, Intel Mac support.

## External Evidence Consulted

- OpenAI Codex changelog (v0.120.0 → v0.122.0-alpha.5, 2026-04-11 to 2026-04-16): [developers.openai.com/codex/changelog](https://developers.openai.com/codex/changelog)
- OpenAI Codex CLI reference and features: [developers.openai.com/codex/cli](https://developers.openai.com/codex/cli), [developers.openai.com/codex/cli/features](https://developers.openai.com/codex/cli/features), [developers.openai.com/codex/cli/reference](https://developers.openai.com/codex/cli/reference)
- OpenAI Codex Agent Skills docs: [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- OpenAI Codex Subagents docs: [developers.openai.com/codex/subagents](https://developers.openai.com/codex/subagents)
- OpenAI Codex GitHub releases (v0.121.0, v0.122.0-alpha): [github.com/openai/codex/releases](https://github.com/openai/codex/releases)
- Secondary coverage: The New Stack, AlternativeTo, PAS7, Blake Crosley's CLI reference (used only to triangulate, not as authority).

Where external claims were not directly verifiable against the official changelog, they are not relied on for adoption recommendations below.

## Fit Evaluation Against Repo Contract

The repo's authority model is the frame every capability is evaluated against: deterministic supervisor owns legality and queue state, Codex is the sole writer with a fresh conversation per bounded task, Claude Code is the primary auditor, Linear is routing metadata only, and `canonical-architecture.md` is the source of truth.

### Adopt (high-fit, low-risk)

**A1. Repo-local Codex skills for the prompt system.**
Package the `PROMPTS.md` five-part header and the `QUEUE-RUNS.md` queue-prompt template as Codex skills under `.agents/skills/` in this repo. Progressive disclosure keeps metadata cheap and only pulls full instructions on invocation, which matches the repo's preference for narrow read-scopes. This formalizes what today is copy-pasted prompt framing.

**A2. `/review` presets for Codex self-audit.**
Codex's `/review` against-base-branch and against-uncommitted-changes presets give a cheap, repeatable self-audit surface before the work is handed to Claude Code for the primary audit. The presets do not replace Code's line-by-line review; they raise the floor of Codex's pre-handoff Self-audit.

**A3. Namespaced MCP registration and parallel-call opt-in.**
The Linear MCP already runs alongside plugin-provided MCPs. Namespacing removes tool-name collision risk, and parallel-call opt-in is a no-op unless a prompt explicitly authorizes it, which fits the supervisor's single-writer posture.

**A4. Sandbox-state metadata on MCP servers.**
Queue-mode needs every MCP call to surface its sandbox posture so the supervisor's allowed-paths guardrail cannot be silently widened by a server that escalates itself. This is evidence the current `QUEUE-RUNS.md § Drift And Scope Guardrails` section already wants.

**A5. Devcontainer/bubblewrap profile and the removal of `danger-full-access` denylist-only networking.**
Aligns with `RULES.md` stop conditions and `canonical-architecture.md`'s sandbox posture. The removed denylist-only mode was the kind of footgun the repo has always forbidden in prose — the CLI now refuses it at the tool level.

### Explore (conditional, phase-gated)

**E1. `codex exec-server` as the supervisor's launch substrate.**
Experimental. If matured, it could replace ad-hoc `codex exec` wiring with a first-class remote-control surface that exposes sandbox-aware filesystem APIs — directly useful for the durable workflow substrate still marked open in `design-history/queue-upgrade-research-2026-04-16.md § Still Intentionally Open`. Defer until GA, but track.

**E2. Subagents as a read-only exploration tool inside a single issue-run.**
`max_depth=1` and sandbox inheritance make subagents safer than they sound, but spawning writer subagents violates "one writer." A constrained use case — spawning read-only subagents to fan out codebase exploration before implementation, with no write authority — could be explored as a Phase-4 capability if tests show it reduces context bloat without weakening scope honesty. Not for queue mode.

**E3. Thread automations as a reconciliation-sweep substrate.**
The queue is webhook-first, but `QUEUE-RUNS.md § Intake Model` already requires a slower reconciliation sweep as recovery. Thread automations could run that sweep with preserved context. Only worth adopting if it beats a plain scheduled supervisor tick; measure before adopting.

**E4. Realtime V2 streaming for observability.**
Could feed the `run_trace_id` observability plan by streaming agent progress into the supervisor's event log. Value depends on whether the eventual tracing backend can consume it cleanly. Defer until the tracing substrate is chosen.

**E5. Structured memory controls (reset/deletion/extension cleanup).**
The repo's official position is that conversation memory is temporary and repo files are the only durable record. Memory reset/deletion controls are useful precisely because they let the supervisor enforce the fresh-conversation-per-bounded-task rule mechanically. Adopt only if the adoption preserves that rule — no cross-thread "memories" allowed.

### Reject (conflicts with repo authority model)

**R1. In-app browser and computer-use.**
Violates `canonical-architecture.md § 3.4 One Browser Owner`. Playwright remains the sole browser owner; the queue does not get a second driver even for "reading" tasks.

**R2. Cross-thread memory carryover as a default.**
The Codex app's "Memories" feature proposes carrying preferences and project conventions across threads automatically. That directly conflicts with `PROMPTS.md § 9`, `AGENTS.project.md § Conversation Lifecycle`, and the fresh-conversation-per-bounded-task rule. The control surface (A/R5 above) is adoptable; automatic memory carryover is not.

**R3. Consumer surfaces (task sidebar, chats-without-project, PR review sidebar, artifact viewer, menu bar, system tray, Intel Mac, SSH alpha).**
These are not supervisor-controlled and do not map to any repo-authoritative surface. They are not harmful, but treating them as part of the repo contract would blur the authority boundary. Informational only.

**R4. `spawn_agents_on_csv` for queue work.**
Batch spawning one worker per CSV row looks like a shortcut past the supervisor's claim/commit/push legality. It is explicitly incompatible with `QUEUE-RUNS.md § Supervisor Loop` and `§ Commit Ownership`.

## Concrete Adoption Candidates

These are candidates, not filed issues. They stage into `todo.md § Suggested Recommendation Log` and wait for Trevor to select before Cowork drafts Codex prompts and opens `GIL-N` issues under the normal audit chain.

1. **Skills-ify the repo prompt system.** Create `.agents/skills/repo-prompts/SKILL.md` packaging the five-part header and the queue-mode prompt template; reference `PROMPTS.md` and `QUEUE-RUNS.md` as authoritative, never redefine. Target docs affected if adopted: `STRUCTURE.md`, `GUIDE.md`, `PROMPTS.md` (to reference the skill as the installation surface). Rationale maps to A1.
2. **Adopt `/review` in Codex Self-audit.** Extend `AGENTS.project.md § Prompt And Commit Discipline` to say Codex Self-audit may invoke `/review` against the uncommitted-changes preset before handoff, with results captured in the Work Record entry. Does not change `PROMPTS.md § Self-audit attestation` — Self-audit remains method-not-claim. Rationale maps to A2.
3. **Lock MCP namespacing and sandbox-state surfacing in the run contract.** Amend `QUEUE-RUNS.md § Eligible Issue Schema` and the supervisor-frozen run-contract fields so each attached MCP declares namespace + sandbox-state, rejected at claim time if missing. Rationale maps to A3 and A4.
4. **Adopt the devcontainer/bubblewrap profile as the reference queue-sandbox profile.** Add an `ADR` under `design-history/` naming this profile the default for queue-mode sandbox; amend `RULES.md` stop conditions to forbid the removed `danger-full-access` denylist-only mode explicitly. Rationale maps to A5.
5. **Open-item tracking for `codex exec-server`, subagents, thread automations, realtime V2, and memory controls.** Extend the open-items list in `design-history/queue-upgrade-research-2026-04-16.md § Still Intentionally Open` to carry these so the queue-upgrade research trail stays the single index for deferred runtime-substrate decisions. Rationale maps to E1–E5.
6. **Record the rejections.** Add an explicit rejections paragraph to the same queue-upgrade memo so later AIs cannot resurrect `spawn_agents_on_csv`, in-app browser, computer-use, or cross-thread memory carryover without re-opening the argument. Rationale maps to R1–R4.

Each candidate, once approved, becomes a `GIL-N` scoping issue in `Inbox`, then follows the normal prompt-review → Ready for Build → Codex → Code audit → Cowork spec check → Trevor verify chain.

## Weaker Alternatives Rejected

- **"Just install every Codex plugin from the marketplace."** The marketplace is a distribution surface, not a curation policy. Installing broadly would pull MCP servers, connectors, and skills into the supervisor's trust boundary without scope honesty. Plugins entering this repo must pass the same read-scope and authority analysis as any other dependency.
- **"Let subagents write in parallel to get queue throughput up."** One writer is the whole point. Parallel writers break single-writer safety and would require a rewrite of the claim/commit/push legality model.
- **"Replace the supervisor's reconciliation sweep with thread automations today."** Thread automations are a Codex-side scheduler, not a supervisor-owned one. Adopting them now would relocate authority out of the supervisor without evidence the tradeoff is net positive.
- **"Use cross-thread memories so Codex remembers repo conventions between issues."** Repo files are the durable memory. Cross-thread memories would leak context between bounded tasks and erode the fresh-conversation rule.

## Mapping To Repo Truth

If Trevor approves any candidate above, the landing scope is:

- `canonical-architecture.md` for any architecture-touching change (E1, A5 when it becomes the runtime substrate)
- `QUEUE-RUNS.md` for intake, run-contract, and sandbox guardrail changes (A3, A4, A5)
- `PROMPTS.md` and `AGENTS.project.md` for prompt/Self-audit surface changes (A1, A2)
- `RULES.md` for stop conditions (A5)
- `STRUCTURE.md` and `GUIDE.md` for navigation to the new `.agents/skills/` location (A1)
- `design-history/queue-upgrade-research-2026-04-16.md` for open-items updates (E1–E5, R1–R4 rejections)
- `todo.md` `Work Record Log`, `Completed`, `Linear Issue Ledger`, `Audit Record Log`, `Test Evidence Log` for each landing
- New ADR under `design-history/` for the devcontainer/bubblewrap adoption

Substantive edits go to Codex via a prompt per `CLAUDE.md § Orchestrator Scope`. Cowork does not edit `canonical-architecture.md`, `QUEUE-RUNS.md`, `PROMPTS.md`, `RULES.md`, or schemas directly.

## Still Intentionally Open

- Whether `codex exec-server` becomes the durable workflow runtime substrate or whether the repo standardizes on Vercel Workflow, Temporal, or another runtime. (See `design-history/queue-upgrade-research-2026-04-16.md § Still Intentionally Open`.)
- Whether skills adoption extends beyond the prompt system (e.g., a dedicated `queue-closeout` skill that automates `todo.md § Work Record Log` + `Completed` + `Linear Issue Ledger` updates).
- Whether the repo should publish its Codex skill bundle as a git-URL plugin for other target repos to install via `codex marketplace add`.
- Whether realtime V2 streaming belongs in the supervisor's event log now, or waits for the trace backend decision.

## Audit Guidance For Later AIs

If you are auditing this decision later, verify in this order:

1. `canonical-architecture.md` for the authority model the analysis is written against.
2. `QUEUE-RUNS.md` for the queue-side implications of each adoption candidate.
3. `PROMPTS.md` for the prompt-system surfaces that skills would attach to.
4. `AGENTS.project.md` for Codex, Claude Code, and Cowork authority boundaries.
5. `design-history/queue-upgrade-research-2026-04-16.md` for the prior research trail that this memo extends rather than replaces.
6. `todo.md § Suggested Recommendation Log` for which candidates Trevor selected and which were declined or deferred.
7. This memo for the Codex-specific reasoning and the rejections that should not be casually reopened.

The main thing to challenge is not "could we adopt more Codex features?" The better audit question is "did any adoption widen Codex's authority past sole-writer, widen Linear's authority past routing metadata, or weaken the fresh-conversation rule?" If yes, re-open.

## Sources

- OpenAI Codex changelog: [developers.openai.com/codex/changelog](https://developers.openai.com/codex/changelog)
- OpenAI Codex CLI: [developers.openai.com/codex/cli](https://developers.openai.com/codex/cli)
- OpenAI Codex CLI features: [developers.openai.com/codex/cli/features](https://developers.openai.com/codex/cli/features)
- OpenAI Codex CLI reference: [developers.openai.com/codex/cli/reference](https://developers.openai.com/codex/cli/reference)
- OpenAI Codex Agent Skills: [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- OpenAI Codex Subagents: [developers.openai.com/codex/subagents](https://developers.openai.com/codex/subagents)
- openai/codex GitHub releases: [github.com/openai/codex/releases](https://github.com/openai/codex/releases)
- Introducing Codex: [openai.com/index/introducing-codex](https://openai.com/index/introducing-codex/)
- Introducing upgrades to Codex: [openai.com/index/introducing-upgrades-to-codex](https://openai.com/index/introducing-upgrades-to-codex/)
