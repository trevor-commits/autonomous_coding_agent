# Linear

**Date:** April 15, 2026
**Authority:** Repo governance derived from `RULES.md` and `AGENTS.project.md`. This document governs how Linear is used for this repository; the authoritative source of truth remains in repo docs.
**Purpose:** Define Linear as the operator board for this repository. This is a repo-governance choice derived from `RULES.md`'s three-tier memory model and supervisor-owned run model, together with `AGENTS.project.md`'s docs-first, not-yet-implementation posture. Linear is an external operator board, not one of the three memory tiers.

---

## Guardrail

No authoritative duplication.

This is not "never duplicate." Short summaries and lightweight checklists in Linear are fine. Acceptance criteria, decisions, ADRs, audit conclusions, completion logs, and cadence schedules are authoritative and live only in the repo.

## What Goes In Linear vs. The Repo

### In Linear

Routing metadata only:

- issue title
- status
- assignee
- `Branch:` current task branch once created
- `Branch status:` such as `active`, `review-ready`, `blocked`, `merged-pending-cleanup`, or `closed-no-merge`
- `Merge target:` where the branch is expected to land
- `Why this exists:` one-line reason the issue exists at all
- `Origin source:` where the issue came from (manual operator request, audit finding, GitHub/PR automation, or another connected system)
- `Risk level:` whether the issue is safe for unattended queue execution
- `Approval required:` whether unattended execution must stop for a human gate
- authoritative spec link
- authoritative decision-docs link
- PR link
- completion-artifact link
- blocker-reason link
- lightweight checklist

### In The Repo

Authoritative and never duplicated in Linear:

- acceptance criteria
- ADRs
- `LOGIC.md`, `RULES.md`, `PROJECT_INTENT.md`, `canonical-architecture.md`, and `STRUCTURE.md`
- `todo.md` specs
- Codex completion logs
- Claude audit writeups
- ChatGPT audit findings
- recurring-audit cadence schedule

## Linear-at-the-core

Linear holds scheduling; repo docs hold truth. Together with `CONTINUITY.md` and `COHERENCE.md`, this is a root repo principle. Any audit finding, feedback decision, suggestion, or surfaced follow-up that implies future work gets a Linear issue in the same commit, or is dispositioned `no-action: <reason>` or `self-contained: <reason>` in the log entry. Nothing actionable sits un-Linearized, and no live Linear issue is allowed to float without a durable `todo.md` home that explains why it exists and where it came from.

## Coverage Invariant

Every live Linear issue in team `GIL` except terminal states (`Done`, `Canceled`) must appear in `todo.md` `## Linear Issue Ledger`. Each ledger entry records the issue ID, current status, `todo home:`, `why this exists:`, and `origin source:`.

Every `todo.md` `Active Next Steps` item must also have a matching Linear issue in team `GIL` before the item is considered actionable. The Linear issue ID is annotated inline in `todo.md` as `(GIL-N)`.

This is bidirectional:

- Adding an item to `Active Next Steps` without creating a Linear issue is a violation.
- Creating or leaving a live Linear issue without a `Linear Issue Ledger` entry is a violation, even when the issue came from GitHub or another connected system instead of manual creation.
- Creating a live Linear issue for planned, reactive, interrupt, or externally generated work requires a matching `todo.md` ledger entry immediately, even if the item is not yet execution-ready.
- Any log entry whose content implies future action must resolve its `linear:` field in the same commit. A missing or unresolved `linear:` field is a coverage violation.
- When GitHub or another connected system creates or reopens a Linear issue, the first repo-side action is to add or refresh the matching `Linear Issue Ledger` entry with the exact trigger named in `origin source:`.

When an item moves from `Active Next Steps` to `Completed`, the Linear issue moves to `Done` in the same logical commit and the ledger entry's `todo home:` is updated. When an item is removed or deferred, the Linear issue is moved to `Canceled` or returned to `Inbox`, and the ledger entry is updated to show the new home or removed only after the issue is terminal.

Invariant introduced 2026-04-16 after a gap was discovered where 9 of 14 Active Next Steps items had no Linear issue.

`Linear-coverage` is clean only when all of these are true:

- every live Linear issue has a `Linear Issue Ledger` entry with `todo home:`, `why this exists:`, and `origin source:`
- every `Active Next Steps` item has its `GIL-N`
- every live Linear issue's current status and repo-side home agree
- every durable log entry that implies future work has a resolved `linear:` value (`GIL-N`, `no-action: <reason>`, or `self-contained: <reason>`)

## Branch Lifecycle Mirror

For file-edit work, Linear should be involved before the first substantive edit instead of being updated only at the end.

- Create or reuse the `GIL-N` issue before branching.
- Prefer Linear's generated branch name when available.
- Keep the issue or its linked PR/comment current with the branch name, branch status, merge target, and later the PR/completion references.
- `todo.md` remains the canonical branch ledger; Linear is the routing mirror that makes branch state visible from the operator board.

## Statuses

| Status | Linear category | Notes |
|---|---|---|
| Inbox | Backlog | First Backlog status; explicit default for newly created issues |
| Ready for Build | Unstarted | Build-ready queue |
| Building | Started | Active implementation, including doc work and ADR drafting |
| AI Audit | Started | Claude reviewing Codex output |
| Human Verify | Started | Trevor's final signoff |
| Blocked | Started | Kept visible as active work |
| Done | Completed | Manual-only; see `Automation` |
| Canceled | Canceled | Terminal non-delivery state |

Triage is the preferred ingress for externally generated, webhook-triggered, or support-style intake when the workspace supports it. If Triage is unavailable or intentionally disabled, `Inbox` acts as the manual equivalent and the same normalization rules still apply before an issue may enter `Ready for Build`.

The happy path is:

`Building -> AI Audit -> Human Verify -> Done`

The naming is deliberate. `AI Audit` means Claude Code performing the primary line-by-line review of Codex output (with Cowork running a lightweight spec-alignment pass afterward). `Human Verify` means Trevor's final signoff. This avoids overloading Linear's product-level review semantics and the dedicated Reviews surface for PR notifications.

Before an issue enters `AI Audit`, these preconditions must already be true:

- a `todo.md` `Work Record Log` entry with full Self-audit exists
- all actionable findings surfaced during the task have Linear issues or explicit `no-action:` / `self-contained:` dispositions
- the Ripple Check is complete and attested

Before the default-path transition from `AI Audit` to `Human Verify`, these preconditions must already be true:

- Claude Code has spot-checked at least one Self-audit claim and recorded the outcome in `todo.md` `Audit Record Log`
- the coherence sweep for the task's scope is clean
- the `Linear-coverage` check is clean

## Failure Routing

- AI Audit failure (Claude Code's line-by-line review surfaces a P0/P1, or Cowork's spec-alignment pass disagrees) returns the issue to `Building` with findings linked from the repo.
- Human Verify failure returns the issue to `Building` for a code or logic regression, or to `AI Audit` for a missed audit criterion.
- Recurring failure signatures escalate into a new issue or the defect-packet workflow. No silent loops.

## Non-Code And Planning Tasks

`Building` covers any active work, including Codex-authored docs and ADR drafting.

Tasks that produce no code artifact may skip `AI Audit` and move:

`Ready for Build -> Building -> Human Verify -> Done`

Skipping `AI Audit` is a per-task decision recorded in the issue checklist. The default is to include `AI Audit`.
Skipping `AI Audit` does not waive the Work Record, Ripple Check, or Linear-coverage requirements.

## Done

`Done` means: terminal disposition recorded in the repo, and merged if a PR exists.

`Done` is moved manually and is never an automation destination. This keeps docs and governance tasks compatible with the same flow even when no PR exists.

## Assignee Semantics

Assignee means accountable owner, usually Trevor. It does not mean "who is acting right now." The current actor is represented by status plus checklist state.

If Linear later adopts an agent or delegation field, use that for tool actors. Do not overload assignee.

Guardrail:

- no issue may remain unassigned once it enters `Ready for Build`
- no PR may use `ref GIL-123` unless the issue already has an accountable owner set

This prevents Linear's default behavior from auto-assigning the PR linker to an otherwise unassigned issue.

## Issue Shape

Use one issue per bounded task. Do not default into parent and sub-issue sprawl.

Every issue body contains:

- `Authoritative spec path:`
- `Authoritative decision docs:` if applicable
- `Branch:` once created
- `Branch status:` once created
- `Merge target:`
- `Why this exists:`
- `Origin source:`
- `Execution lane:` `Codex`, `Claude Code`, `Cowork`, or `Trevor`
- `Execution mode:` `Queue` or `Manual`
- `Risk level:` `Low`, `Medium`, or `High`
- `Approval required:` `No` or `Yes`
- `PR:` once opened
- `Completion artifact:` once filed
- `Blocked reason artifact:` only when status is `Blocked`
- `Checklist:` `Cowork drafts Codex prompt` -> `Codex creates or reuses the task branch` -> `Codex builds` -> `Work Record Log entry written (Codex)` -> `Ripple Check complete and attested (Codex)` -> `Claude Code audits line-by-line (or N/A with one-line reason)` -> `Cowork spec-alignment check` -> `Linear-coverage confirmed for surfaced findings (Cowork)` -> `Trevor verifies` -> `completion artifact filed in repo`
- `Enforcement checkbox: ☐ No acceptance criteria, decisions, or audit conclusions in this issue body — linked to repo doc instead`
- fixed footer: `Repo docs are authoritative; this issue tracks state and links only.`

Supervisor-gated phase transitions inside a Codex run are not represented in Linear.

Queue-mode issues deliberately do not carry free-form command text. The issue nominates the bounded work through repo links and routing metadata; the supervisor derives the executable run contract from the repo truth.

Queue-mode issues may also carry normalization metadata when the supervisor
needs bounded inputs that the authoritative spec path alone cannot supply
safely:

- `Allowed paths:` first manual drain implementation requires this line on
  Codex queue issues so the supervisor can freeze a truthful write scope before
  Codex starts.
- `Forbidden paths:` optional override; if omitted, the supervisor falls back
  to its default companion exclusions.
- `Verification pack:` optional override naming the deterministic repo-contract
  commands the queue run must execute before handoff.
- `Retry budget:` optional override for the queue run's repair-loop ceiling.

These are routing inputs, not acceptance criteria. The authoritative spec still
lives in the repo doc named by `Authoritative spec path:`.

## Labels

Labels are scoped to two groups and applied at issue creation. The taxonomy is small by design — labels are for filtering and routing, not for tracking state (state lives in the status) or acceptance criteria (those live in the authoritative repo spec linked from the issue).

**Work type** (what kind of deliverable the issue produces; exactly one per issue):

- `ADR` — issue produces an Architecture Decision Record in `design-history/`.
- `Governance` — issue edits one of the authoritative governance docs (`RULES.md`, `LOGIC.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `canonical-architecture.md`, `LINEAR.md`, `AGENTS.md`, `AGENTS.project.md`, `PROMPTS.md`, `CLAUDE.md`).
- `Docs` — issue edits non-governance docs (guides, README, indexes, completion logs).
- `Feature` — issue implements new behavior in runtime code.
- `Improvement` — issue refactors, clarifies, or strengthens existing behavior without new capability.
- `Defect` — issue fixes a bug or audit-surfaced regression.

**Routing** (how the issue moves through the system; zero or more per issue):

- `Blocked-external` — work is paused pending an external dependency (vendor response, waiting on a human outside the repo). Pair with status `Blocked`.
- `Cadence` — recurring issue mirroring a scheduled audit or review defined in the repo cadence doc.
- `Audit-finding` — issue was created by an audit (Code, Pro, or Claude) documenting a finding that needs its own tracked resolution.
- `prompt-review` — applied by Cowork while a draft prompt in the issue description is open for Codex and Claude Code audit comments. Removed by Cowork once the prompt is final. See `## Prompt Drafting Surface`.

If the Linear workspace label set ever drifts from this block, the repo wins and Linear is corrected.

## Standard Issue Template

The Linear workspace defines one universal issue template named `Standard issue`. It is the default template for new issues and prefills the issue body shape defined in the Issue Shape section. Variants should not be created until a specific work type demonstrably needs additional fields.

The unchecked boxes shown below are example template content for Linear issue bodies. They are not this repository's backlog and they are not meant to be checked off inside `LINEAR.md`.

The template body is:

```text
**Authoritative spec path:**

**Authoritative decision docs:** (if applicable)

**Branch:** (once created)

**Branch status:** (once created)

**Merge target:**

**Why this exists:**

**Origin source:**

**Execution lane:**

**Execution mode:**

**Risk level:**

**Approval required:**

**PR:** (once opened)

**Completion artifact:** (once filed)

**Blocked reason artifact:** (only if status is Blocked)

---

**Checklist**

- [ ] Cowork drafts Codex prompt
- [ ] Codex creates or reuses the task branch
- [ ] Codex builds
- [ ] Work Record Log entry written (Codex)
- [ ] Ripple Check complete and attested (Codex)
- [ ] Claude Code audits line-by-line (or N/A with one-line reason: ____)
- [ ] Cowork spec-alignment check
- [ ] Linear-coverage confirmed for surfaced findings (Cowork)
- [ ] Trevor verifies
- [ ] Completion artifact filed in repo

---

- [ ] **Enforcement:** No acceptance criteria, decisions, or audit conclusions in this issue body — linked to repo doc instead

---

_Repo docs are authoritative; this issue tracks state and links only._
```

If the template in Linear ever drifts from this block, the repo wins and the Linear template is corrected.

## Queue Execution

`QUEUE-RUNS.md` defines the exact unattended queue contract. Linear supplies routing metadata only.

Preferred intake model:

- verified Linear webhooks wake the queue supervisor when issue state changes matter
- Linear Triage or `Inbox` acts as the normalization lane before queue work becomes claimable
- Triage rules, Triage Intelligence, or agent automations may enrich routing metadata only; they may not author repo truth or issue executable commands
- the supervisor still performs the final queue-eligibility check against repo truth before claiming any issue

Codex queue eligibility requires all of the following:

- status `Ready for Build`
- `Execution lane: Codex`
- `Execution mode: Queue`
- `Risk level: Low` or `Medium`
- `Approval required: No`
- valid `Authoritative spec path`
- no `prompt-review` label
- no `Blocked-external` label

Queue runs also enforce these guardrails:

- the supervisor snapshots the issue and authoritative inputs at claim time
- the supervisor records claim, trace, and intake identifiers for every issue-run
- Codex works only inside the supervisor-derived allowed paths for that run
- off-scope discoveries are absorbed only when they are direct adjacent blockers that still fit the same allowed paths, verification pack, and decision ownership
- discovered high-risk actions or approval-bound operations block the issue instead of being improvised in-run
- everything else becomes a separate issue or an explicit `no-action:` / `self-contained:` disposition

Issues for later Claude Code audit or deeper test work must explicitly set:

- `Execution lane: Claude Code`
- `Execution mode: Manual`

Codex and the queue supervisor skip those issues and continue. They do not absorb them into the current Codex pass.

## AI-Strategy Role Boundary

Per `RULES.md`, the AI strategy layer may decompose work, compose builder prompts, propose review timing, diagnose stalls, and restate audit findings. Cowork drafts Codex prompts and may propose when review should happen. Claude Code is the primary auditor of implementation output — it performs the line-by-line review and may author targeted fix code during audit per `CLAUDE.md § Roles` and `AGENTS.project.md § Completion Authority`.

Neither Cowork nor Claude Code owns phase-transition or completion authority. Those stay with the supervisor at runtime and with Trevor at the governance layer.

## Prompt Drafting Surface

Codex prompts are drafted inside the Linear issue that scopes the work, not only in chat. This is an orchestration convenience, not an authority shift.

Workflow:

1. Cowork creates or opens the issue, moves it to `Ready for Build`, writes the first-draft prompt into the issue description, and applies the `prompt-review` label.
2. Claude Code (primary prompt auditor) and Codex read the description and post their audits as Linear comments, prefixed `[Code Audit]` or `[Codex Audit]` for scanability. Code's pass is the load-bearing one. Codex's pass must challenge material prompt instructions and imported AI findings against repo truth, current evidence, and scope, classifying them as `accepted`, `narrowed`, `rejected`, or `needs more evidence` instead of merely flagging implementability concerns.
3. Cowork revises the description in place, then posts a summary comment noting which audit points were accepted, narrowed, rejected, or left needing more evidence and why.
4. When the prompt is final, Cowork removes the `prompt-review` label. The prompt is now ready to hand to Codex for implementation under the normal `Building → AI Audit → Human Verify → Done` flow.

Guardrails:

- Prompts in Linear descriptions are a drafting surface, not authority. The authoritative spec the prompt points to remains in the repo.
- Another AI's prompt or review comment is advisory until the final prompt is revised by Cowork and the implementing Codex pass confirms the instruction still matches repo truth, evidence, and scope.
- Audit comments are transient. Any decision durable enough to matter later is distilled into an ADR or the repo doc it touches — never left to live only as a Linear comment.
- The prompt of record is the final version Codex logs in `todo.md` under `## Completed` after its run. Linear's description-edit history is convenient but not load-bearing.
- Code and Codex write comments only. Neither moves issue state directly. Manual-workflow state changes remain Cowork's responsibility; queue-mode state changes remain supervisor-owned under `QUEUE-RUNS.md`. Code does, however, check off audit checklist items in the issue body after its line-by-line review is clean (see `AGENTS.project.md § Completion Authority`).
- Queue-mode issues do not require a handcrafted issue-description prompt. When `Execution mode: Queue`, the supervisor renders the versioned Codex template from `QUEUE-RUNS.md` and `PROMPTS.md`.

## Integrations

These are separate mechanisms and must not be conflated.

### Linear MCP Server

Enabled. This provides compatible clients such as Claude Code and Cowork with programmatic read and write access to Linear data. It is a data protocol, not a custom prompt surface.

### Verified Webhooks

Preferred for unattended queue intake. Webhooks wake the supervisor when issue state changes matter, but they are not execution authority by themselves. The supervisor still verifies the event, reconciles current Linear state, normalizes the issue into a bounded run contract, and only then decides whether work is claimable.

### Open Issues In Coding Tools

Enabled. This is a separate Linear launch workflow that opens Codex or Claude Code with issue metadata and a custom prompt telling the tool to read the authoritative repo spec first and treat the Linear issue as routing metadata only. The custom prompt belongs to this launch flow, not to MCP.

### Codex-In-Linear Delegation

Direct Installed-Agent delegation remains disabled by policy. The integration exists, but this repo does not let Linear hand Codex arbitrary commands or become the workflow owner. Queue execution is allowed only through the supervisor-mediated contract in `QUEUE-RUNS.md`, where Linear nominates eligible work and the supervisor owns normalization, claim, state transitions, and landing mechanics. On 2026-04-15 Codex was removed from Linear's Installed Agents surface to reinforce this boundary at the tool level, not just in doc.

## GitHub Account And Sync Settings

- connect a personal GitHub account in Linear so activity, comments, and assignee mapping resolve to the real user rather than generic GitHub activity
- keep GitHub Issues Sync disabled to avoid dual truth across title, description, status, assignee, labels, and comments
- keep commit linking disabled initially; only PR references should participate when automation is enabled later
- use the issue-generated branch name when available; if Linear offers copy-branch support, use it for naming while keeping automatic assignee or status side effects disabled
- if any connected system still creates an issue, the repo-side response is not "leave it in Linear"; add or refresh the matching `todo.md` `Linear Issue Ledger` entry immediately with a concrete `origin source:`

## PR Linking Convention

Default to `ref GIL-123` in the PR description. `GIL` is the Linear team prefix for the Gillettewsc team, confirmed on 2026-04-15.

Do not use `Fixes GIL-123` or `Closes GIL-123` by default. Closing magic words bypass the intended `Building -> AI Audit -> Human Verify -> Done` flow by letting Linear drive issue state from branch push and merge events.

Branch names should include the issue ID, and for normal file-edit work Codex should usually create or reuse the Linear-generated branch before deep implementation. Linear supplies naming and routing context; it does not become execution authority.

### Skip / Ignore Escape Hatch

If a PR should not move issue state at all, use the currently documented suppression tokens:

- `<skip|ignore> <issue-id>`

Use either form with the specific issue ID being suppressed. These suppress Linear's PR-linking automation for that PR.

Verify the current Linear-supported suppression syntax against Linear's PR-linking docs before relying on it. The token form has changed historically; if Linear's current docs disagree, the docs win and this section is corrected.

## Bidirectional Traceability

Linear issue IDs belong only in task-local artifacts:

- `todo.md` entries
- blocker notes
- audit records
- completion logs
- PRs

Do not add Linear IDs to stable source-of-truth docs such as `PROJECT_INTENT.md`, `RULES.md`, `LOGIC.md`, `canonical-architecture.md`, or `STRUCTURE.md` unless the task is specifically about editing that document.

## Automation

### Now

GitHub PR and commit automations remain manual-safe and should stay at `No action`. Queue-mode issue automation is allowed only through the supervisor contract in `QUEUE-RUNS.md`.

Set every GitHub PR and commit automation destination in Linear team settings to `No action`. Keep commit linking disabled. Use issue-generated branch names and PR links for visibility, but do not let branch or PR events move issue state automatically.

Writing a policy sentence is not enough on its own. Linear's defaults otherwise move issues to `In Progress` when PRs open and to `Done` when PRs merge, regardless of whether the PR used a non-closing reference verb.

When the queue runner exists, the only allowed supervisor-owned state moves are:

- `Ready for Build` -> `Building` when the supervisor claims a Codex-eligible queue issue
- `Building` -> `AI Audit` when the landing commit, repo completion artifacts, and completion comment exist
- `Building` -> `Blocked` when the blocked reason artifact and blocker comment exist

`Human Verify` and `Done` remain outside the Codex queue lane.

Completion-comment discipline:

- the completion comment cites only the commit(s), artifact paths, and verification that belong to that issue's landing
- if a later audit-only or correction commit belongs to a different `GIL-N`, it is posted on that issue instead of being appended to the earlier issue's comment
- when a commit SHA was unknown at write time, the correcting or immediate-closeout update backfills the exact SHA on the correct issue

### Later

When runtime implementation exists and branch protections are real, the allowed deterministic PR-state routing is:

- draft PR open -> `Building`
- review request or review activity -> `AI Audit`
- PR merge -> `No action`

`Human Verify` is always manual after Claude signoff in `AI Audit`.

Tasks that skip `AI Audit` also stay manual for the handoff into `Human Verify`.

`Done` is always manual after the repo completion artifact is filed.

Do not enable merge-ready automation until GitHub branch protections and review or check rules exist in practice.

## Recurring Audits

The repo cadence document is authoritative for schedule. A recurring Linear issue may mirror that schedule as a reminder, but it points back to the repo cadence doc rather than replacing it.

If the repo and Linear recurrence ever disagree, the repo wins and the Linear recurrence is corrected. Actionable findings become normal one-off issues.

## Blocked Discipline

Every `Blocked` issue must link to a repo artifact that explains what would unblock it. Acceptable artifacts are authoritative repo documents — a `todo.md` entry, defect packet, ADR, or blocker note committed to the repo. A Linear comment or description does not satisfy this; the artifact must live in the repo so the unblock condition survives outside Linear.

If the blocker is another task, also use Linear's native blocked and blocking relation.

No bare `Blocked` issues.

## Archival

Deferred. Do not configure an auto-archive rule yet.

If archival is adopted later, configure it at the team level. Linear archives at the team level, not per issue. Revisit only if board noise becomes a real problem.

## Deferred Capabilities

Linear features that were reviewed during initial setup and consciously skipped. Recorded here so future revisits don't have to re-discover what exists. Skipping is the current decision, not a permanent rule — revisit when the listed trigger applies.

Some entries in this list are also enforced as policy elsewhere in this document (Codex-in-Linear delegation, GitHub Issues Sync, commit linking, branch-copy auto-assign, auto-archive). The references below are for capability awareness, not policy duplication — the authoritative rule for those items remains where it appears earlier in this document.

### Expansion Discipline

Deferred capabilities are adopted reactively when their stated trigger fires. This list should shrink over time as triggers fire, not grow speculatively. See ADR-0006.

### Hierarchy features

- **Projects** — multi-issue containers for grouped initiatives or milestones. Skipped because no current work groups under named initiatives. Revisit when an initiative spans more than ~5 related issues that need shared status, lead, and timeline. Concrete current candidates if/when adopted: the Codex conversation lifecycle work (ADR-0005) and the Phase 0A punch list.
- **Project labels** — labels scoped to Projects rather than issues. Deferred with Projects.
- **Project templates** — prefilled Project shapes. Deferred with Projects.
- **Initiatives** — groups of Projects toward a strategic effort. Deferred with Projects; Initiatives have nothing to group without Projects in use.

### Triage and AI features

- **Triage status** — no longer a conceptual no. It is now the preferred pre-queue normalization lane when the workspace supports it. If still unavailable in practice, `Inbox` remains the manual equivalent.
- **Linear Agent Skills** — reusable Linear-Agent prompts invoked by slash command or auto-selected. Skipped because the current flow has no repeated Linear-Agent request that justifies one. Revisit if a request pattern emerges.
- **Triage Intelligence** (paid plan) — acceptable only for routing enrichment (team, labels, assignee, issue categorization) before queue normalization. It must not become a source of acceptance criteria, commands, or audit truth.
- **Agent automations** (paid plan) — acceptable only for Triage-to-routing metadata enrichment or notifications. They may not claim issues, emit executable instructions, or bypass supervisor normalization.
- **AI Summaries** (paid plan) — AI-generated summaries across Linear. Skipped because the repo is the source of truth for summaries; Linear-side summaries would invite drift.

### Issue intake

- **Custom Form issue templates** — structured intake forms with required fields and dropdowns, intended for non-technical Asks-style submissions. Skipped because issue body shape is enforced by checklist, not form fields, and the operator pool is small. Revisit if external requesters start submitting issues.

### Custom fields

- **Current executor custom field** — separate from `Assignee` (which per Assignee Semantics is the accountable owner, not the current actor). Skipped because status plus checklist state currently makes it clear who is acting. Revisit if it becomes hard to tell at a glance whose turn it is on an issue.

### Connected accounts and external surfaces

- **Slack connected account** (per-user attribution and Slack-side notifications) — skipped unless the operator actively works in Slack. Connecting later requires no governance change.
- **Slack workspace integration for Linear Agent** — skipped with the per-user connection.
- **Google Calendar OOO sync** — propagates calendar OOO status into Linear. Skipped pending an OOO-driven routing need.
- **Notion connected account** — previews Linear issues inside Notion. Skipped because Notion would become a third surface for "truth" and undermine the repo-is-authoritative premise.
- **View pull requests in Linear** (Alpha) — surfaces PR review notifications inside Linear. Skipped because PR review lives in GitHub in this flow.
- **Linear Agent integrations** — Slack, Microsoft Teams, Gong. Skipped pending adoption of those tools.

### Coding-tool surface

- **Coding tools not enabled** — Amp, Conductor, Cursor, Devin, Factory, GitHub Copilot, Lovable, Netlify Agent Runners, OpenCode, Replit, v0, Warp, Windsurf, Zed. Only Claude Code, Codex CLI, and Codex desktop are part of the flow per the Integrations section above. Adding any other tool requires updating this document first.
- **Custom script** coding-tool entry — runs a script defined in `~/.linear/coding-tools.json` when launching an issue. Skipped because the existing Codex CLI and Claude Code launchers cover the flow. Revisit only if a per-issue launch behavior cannot be expressed by those tools.
- **Custom link** coding-tool entry — opens a web-based tool with `{{prompt}}` injected. Skipped for the same reason.

### Personal account security

- **Passkeys** — passwordless sign-in for the operator's Linear account. Optional security upgrade unrelated to flow; revisit independently of governance.
- **Personal API keys** — direct GraphQL access. Not needed because the Linear MCP server uses OAuth. Create one only if a custom script or non-MCP integration needs raw API access.

### Automation referenced elsewhere as policy

The following are listed here for capability awareness; the binding rule is in the section noted in parentheses, not here.

- Codex-in-Linear delegation — disabled by policy (Integrations).
- supervisor-mediated queue execution from Linear routing metadata — allowed only through `QUEUE-RUNS.md` and never through direct Installed-Agent delegation.
- GitHub Issues Sync — disabled (GitHub Account And Sync Settings).
- Commit linking — disabled initially (GitHub Account And Sync Settings).
- Branch-copy auto-assign / move-to-started — disabled (GitHub Account And Sync Settings).
- "On open in coding tool" and "On move to started, assign to self" — disabled (GitHub Account And Sync Settings).
- Auto-archive rule — deferred (Archival).

If any item in this section is later adopted, move it out of this list and update the relevant operational section above. This section should shrink over time as decisions get made, not grow into a parallel spec.

## Governance Note

`LINEAR.md` is repo truth. It governs how Linear is used for this repository, but it does not itself live in Linear.
For bootstrapping Linear on new projects, see `LINEAR-BOOTSTRAP.md`.
