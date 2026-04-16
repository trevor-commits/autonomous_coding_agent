# Linear

**Date:** April 15, 2026
**Authority:** Repo governance derived from `RULES.md` and `AGENTS.md`. This document governs how Linear is used for this repository; the authoritative source of truth remains in repo docs.
**Purpose:** Define Linear as the operator board for this repository. This is a repo-governance choice derived from `RULES.md`'s three-tier memory model and supervisor-owned run model, together with `AGENTS.md`'s docs-first, not-yet-implementation posture. Linear is an external operator board, not one of the three memory tiers.

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

Triage is not enabled in the initial rollout. If Triage is later enabled, update this document.

The happy path is:

`Building -> AI Audit -> Human Verify -> Done`

The naming is deliberate. `AI Audit` means Claude reviewing Codex output. `Human Verify` means Trevor's final signoff. This avoids overloading Linear's product-level review semantics and the dedicated Reviews surface for PR notifications.

## Failure Routing

- AI Audit failure returns the issue to `Building` with findings linked from the repo.
- Human Verify failure returns the issue to `Building` for a code or logic regression, or to `AI Audit` for a missed audit criterion.
- Recurring failure signatures escalate into a new issue or the defect-packet workflow. No silent loops.

## Non-Code And Planning Tasks

`Building` covers any active work, including Codex-authored docs and ADR drafting.

Tasks that produce no code artifact may skip `AI Audit` and move:

`Ready for Build -> Building -> Human Verify -> Done`

Skipping `AI Audit` is a per-task decision recorded in the issue checklist. The default is to include `AI Audit`.

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
- `PR:` once opened
- `Completion artifact:` once filed
- `Blocked reason artifact:` only when status is `Blocked`
- `Checklist: Claude drafts Codex prompt -> Codex builds -> Claude audits (or N/A with one-line reason) -> Trevor verifies -> completion artifact filed in repo`
- `Enforcement checkbox: ☐ No acceptance criteria, decisions, or audit conclusions in this issue body — linked to repo doc instead`
- fixed footer: `Repo docs are authoritative; this issue tracks state and links only.`

Supervisor-gated phase transitions inside a Codex run are not represented in Linear.

## Labels

Labels are scoped to two groups and applied at issue creation. The taxonomy is small by design — labels are for filtering and routing, not for tracking state (state lives in the status) or acceptance criteria (those live in the authoritative repo spec linked from the issue).

**Work type** (what kind of deliverable the issue produces; exactly one per issue):

- `ADR` — issue produces an Architecture Decision Record in `design-history/`.
- `Governance` — issue edits one of the authoritative governance docs (`RULES.md`, `LOGIC.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `canonical-architecture.md`, `LINEAR.md`, `AGENTS.md`, `PROMPTS.md`, `CLAUDE.md`).
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

**PR:** (once opened)

**Completion artifact:** (once filed)

**Blocked reason artifact:** (only if status is Blocked)

---

**Checklist**

- [ ] Claude drafts Codex prompt
- [ ] Codex builds
- [ ] Claude audits (or N/A with one-line reason: ____)
- [ ] Trevor verifies
- [ ] Completion artifact filed in repo

---

- [ ] **Enforcement:** No acceptance criteria, decisions, or audit conclusions in this issue body — linked to repo doc instead

---

_Repo docs are authoritative; this issue tracks state and links only._
```

If the template in Linear ever drifts from this block, the repo wins and the Linear template is corrected.

## AI-Strategy Role Boundary

Per `RULES.md`, the AI strategy layer may decompose work, compose builder prompts, propose review timing, diagnose stalls, and restate audit findings. Claude drafts Codex prompts and may propose when review should happen.

Claude does not own phase-transition or completion authority. Those stay with the supervisor.

## Prompt Drafting Surface

Codex prompts are drafted inside the Linear issue that scopes the work, not only in chat. This is an orchestration convenience, not an authority shift.

Workflow:

1. Cowork creates or opens the issue, moves it to `Ready for Build`, writes the first-draft prompt into the issue description, and applies the `prompt-review` label.
2. Codex and Claude Code read the description and post their audits as Linear comments, prefixed `[Codex Audit]` or `[Code Audit]` for scanability.
3. Cowork revises the description in place, then posts a summary comment noting which audit points were accepted or rejected and why.
4. When the prompt is final, Cowork removes the `prompt-review` label. The prompt is now ready to hand to Codex for implementation under the normal `Building → AI Audit → Human Verify → Done` flow.

Guardrails:

- Prompts in Linear descriptions are a drafting surface, not authority. The authoritative spec the prompt points to remains in the repo.
- Audit comments are transient. Any decision durable enough to matter later is distilled into an ADR or the repo doc it touches — never left to live only as a Linear comment.
- The prompt of record is the final version Codex logs in `todo.md` under `## Completed` after its run. Linear's description-edit history is convenient but not load-bearing.
- Code and Codex write comments only. Neither moves issue state; that remains Cowork's responsibility per AI-Strategy Role Boundary.

## Integrations

These are separate mechanisms and must not be conflated.

### Linear MCP Server

Enabled. This provides compatible clients such as Claude Code and Cowork with programmatic read and write access to Linear data. It is a data protocol, not a custom prompt surface.

### Open Issues In Coding Tools

Enabled. This is a separate Linear launch workflow that opens Codex or Claude Code with issue metadata and a custom prompt telling the tool to read the authoritative repo spec first and treat the Linear issue as routing metadata only. The custom prompt belongs to this launch flow, not to MCP.

### Codex-In-Linear Delegation

Disabled by policy, not because of a capability gap. The integration exists; this repo does not use it because `RULES.md` keeps run spawning and worktree ownership under the supervisor. On 2026-04-15 Codex was removed from Linear's Installed Agents surface to reinforce this policy at the tool level, not just in doc.

## GitHub Account And Sync Settings

- connect a personal GitHub account in Linear so activity, comments, and assignee mapping resolve to the real user rather than generic GitHub activity
- keep GitHub Issues Sync disabled to avoid dual truth across title, description, status, assignee, labels, and comments
- keep commit linking disabled initially; only PR references should participate when automation is enabled later
- keep the "Copy branch name -> auto-assign / move to Started" preference disabled while statuses are still manually controlled

## PR Linking Convention

Default to `ref GIL-123` in the PR description. `GIL` is the Linear team prefix for the Gillettewsc team, confirmed on 2026-04-15.

Do not use `Fixes GIL-123` or `Closes GIL-123` by default. Closing magic words bypass the intended `Building -> AI Audit -> Human Verify -> Done` flow by letting Linear drive issue state from branch push and merge events.

Branch names may include the issue ID for navigability. Branching itself is still an operator and supervisor concern, not something Claude should instruct Codex to create.

### Skip / Ignore Escape Hatch

If a PR should not move issue state at all, use the currently documented suppression tokens:

- `<skip|ignore> <issue-id>`

Use either form with the specific issue ID being suppressed. These suppress Linear's PR-linking automation for that PR.

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

This repository is still in its docs-only phase per `AGENTS.md`, so all status moves are manual.

Set every GitHub PR and commit automation destination in Linear team settings to `No action`. Keep commit linking disabled. Keep the branch-copy auto-assign and move-to-started preference disabled.

Writing a policy sentence is not enough on its own. Linear's defaults otherwise move issues to `In Progress` when PRs open and to `Done` when PRs merge, regardless of whether the PR used a non-closing reference verb.

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

Every `Blocked` issue must link to a repo artifact that explains what would unblock it. Acceptable artifacts include a `todo.md` entry, defect packet, ADR, or blocker note.

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

- **Triage status** — separate inbound queue distinct from `Inbox`. Not enabled in initial rollout; the Statuses section above flags this and notes that adopting Triage later requires updating this document.
- **Linear Agent Skills** — reusable Linear-Agent prompts invoked by slash command or auto-selected. Skipped because the current flow has no repeated Linear-Agent request that justifies one. Revisit if a request pattern emerges.
- **Triage Intelligence** (paid plan) — auto-infers team, project, labels, assignee for new issues. Skipped because triage is manual in the current flow and the plan tier does not include it.
- **Agent automations** (paid plan) — automated workflows triggered when issues hit Triage. Skipped with Triage.
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
- GitHub Issues Sync — disabled (GitHub Account And Sync Settings).
- Commit linking — disabled initially (GitHub Account And Sync Settings).
- Branch-copy auto-assign / move-to-started — disabled (GitHub Account And Sync Settings).
- "On open in coding tool" and "On move to started, assign to self" — disabled (GitHub Account And Sync Settings).
- Auto-archive rule — deferred (Archival).

If any item in this section is later adopted, move it out of this list and update the relevant operational section above. This section should shrink over time as decisions get made, not grow into a parallel spec.

## Governance Note

`LINEAR.md` is repo truth. It governs how Linear is used for this repository, but it does not itself live in Linear.
For bootstrapping Linear on new projects, see `LINEAR-BOOTSTRAP.md`.
