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
- no PR may use `ref <PREFIX>-123` unless the issue already has an accountable owner set

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

## AI-Strategy Role Boundary

Per `RULES.md`, the AI strategy layer may decompose work, compose builder prompts, propose review timing, diagnose stalls, and restate audit findings. Claude drafts Codex prompts and may propose when review should happen.

Claude does not own phase-transition or completion authority. Those stay with the supervisor.

## Integrations

These are separate mechanisms and must not be conflated.

### Linear MCP Server

Enabled. This provides compatible clients such as Claude Code and Cowork with programmatic read and write access to Linear data. It is a data protocol, not a custom prompt surface.

### Open Issues In Coding Tools

Enabled. This is a separate Linear launch workflow that opens Codex or Claude Code with issue metadata and a custom prompt telling the tool to read the authoritative repo spec first and treat the Linear issue as routing metadata only. The custom prompt belongs to this launch flow, not to MCP.

### Codex-In-Linear Delegation

Disabled by policy, not because of a capability gap. The integration exists; this repo does not use it because `RULES.md` keeps run spawning and worktree ownership under the supervisor.

## GitHub Account And Sync Settings

- connect a personal GitHub account in Linear so activity, comments, and assignee mapping resolve to the real user rather than generic GitHub activity
- keep GitHub Issues Sync disabled to avoid dual truth across title, description, status, assignee, labels, and comments
- keep commit linking disabled initially; only PR references should participate when automation is enabled later
- keep the "Copy branch name -> auto-assign / move to Started" preference disabled while statuses are still manually controlled

## PR Linking Convention

Default to `ref <PREFIX>-123` in the PR description. `<PREFIX>` is the actual Linear team prefix. If no workspace exists yet, keep `<PREFIX>` as an explicit placeholder rather than inventing one.

Do not use `Fixes <PREFIX>-123` or `Closes <PREFIX>-123` by default. Closing magic words bypass the intended `Building -> AI Audit -> Human Verify -> Done` flow by letting Linear drive issue state from branch push and merge events.

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

## Governance Note

`LINEAR.md` is repo truth. It governs how Linear is used for this repository, but it does not itself live in Linear.
