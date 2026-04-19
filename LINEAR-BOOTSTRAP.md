# LINEAR-BOOTSTRAP.md

## §1 Convention and pre-flight intake <!-- For Trevor and Claude Cowork -->

Every new project gets a Linear team before its first Codex prompt is drafted. The team name matches the repo name, the prefix is a Trevor-chosen 3-4 letter code, the repo's `LINEAR.md` is ported per §2, and the Linear workspace is configured per §3.

Intake checklist:

1. What is the target repo absolute path?
2. What is the Linear team name?
3. What is the Linear team prefix (3-4 letters)?
4. Which authoritative repo docs should be preserved in the ported `LINEAR.md`? Enumerate them by inspecting the target repo root.
5. Is the target repo's root `AGENTS.md` a thin stub with a `*.project.md` or similar overlay? If yes, the Linear pointer goes in the overlay, not the root.

Usage flow: Claude Cowork runs the intake, fills the §2 template braces, hands the filled prompt to Trevor, and Trevor hands it to a fresh Codex session in the target repo.

## §2 Codex prompt template — Linear governance port <!-- For Codex, to be run in the target repo after intake -->

Inputs: `{REPO_PATH}`, `{TEAM_NAME}`, `{TEAM_PREFIX}`, `{AUTHORITATIVE_DOCS}`, `{AGENTS_POINTER_TARGET}`

```text
Usage note: this template is filled in by Claude Cowork after running the §1 intake, then handed to Codex in the target repo.

Goal: Port Linear governance into `{REPO_PATH}` by creating a tailored `LINEAR.md`, adding a `## Linear` pointer section in `CLAUDE.md`, adding a Linear pointer in `{AGENTS_POINTER_TARGET}`, and updating `todo.md` so it can mirror every live Linear issue with provenance before appending a `Completed` entry. One new file, three edited files.

Discipline: No code. Follow the target repo's documented branch policy for this doc-only task: create or reuse a task branch if that repo requires edit work on branches; otherwise stay branchless. Leave changes staged but do NOT commit — Trevor will review the staged diff before commit. If the target repo documents a different commit convention for doc-only work, follow that target-repo policy instead.

For repo content, limit substantive reads to:
- `LINEAR.md`
  (the authority this port generalizes from; use it to adapt statuses, issue shape, template content, integration settings, and governance rules to the target repo)
- `CLAUDE.md`
  (to add the `## Linear` pointer section in the right place)
- `{AGENTS_POINTER_TARGET}`
  (to place the Linear pointer in the authoritative AGENTS surface resolved during intake)
- `todo.md`
  (to locate or create the `## Linear Issue Ledger` convention block, then append the completion entry)

Do not read other repo docs unless required by higher-priority agent instructions or validation.

Body:
1. Create `LINEAR.md` at the target repo root by adapting this repo's `LINEAR.md` to the target repo's actual authoritative docs, workflows, and terminology.
2. Strip companion-doc references that do not exist in the target repo instead of inventing placeholders. This includes examples such as `LOGIC.md`, `RULES.md`, `STRUCTURE.md`, `canonical-architecture.md`, and `design-history/` when they are absent.
3. If the target repo uses a decision-record convention other than ADRs, map every ADR reference to that convention while preserving the same governance meaning.
4. Add a `## Linear` pointer section in `CLAUDE.md` that points readers to `LINEAR.md` for the repo's Linear workflow rules.
5. Add a Linear pointer in `{AGENTS_POINTER_TARGET}`. If the root `AGENTS.md` is only a thin stub that defers to another authoritative overlay, keep the stub minimal and put the pointer in the overlay instead.
6. Update `todo.md` so it has a `## Linear Issue Ledger` section or convention block that mirrors every live issue with `todo home:`, `why this exists:`, and `origin source:`.
7. Append a `todo.md` `Completed` entry dated today with one line describing the Linear bootstrap addition.

Constraints:
- Do not modify docs other than `LINEAR.md`, `CLAUDE.md`, `{AGENTS_POINTER_TARGET}`, and `todo.md`.
- Do not invent a branch rule for the target repo; follow its documented edit-work policy.
- Do not commit unless the target repo's own documented policy explicitly requires it for this kind of task.
- Stop and report on conflict instead of guessing.
- Print a one-line summary of files modified after the change.
```

## §3 Linear-UI setup runbook <!-- For Trevor, performed in the Linear web UI -->

Perform these steps in the Linear web UI after §2's port lands. Each step lists the exact screen, the action, and the reason so future Trevor doesn't have to re-derive it.

**Team creation.**
- Create team. Name matches repo name. Prefix is the 3-4 letter code confirmed in §1 intake.

**Team Settings → General.**
- Confirm Identifier matches §1 prefix.
- Timezone: local.
- Estimates: Not in use (no estimation discipline defined).
- Create issues by email: Off (non-governed intake path).
- Enable detailed issue history: **On** (strengthens audit trail for AI Audit / Human Verify discipline).

**Team Settings → Issue statuses.**
Linear seeds 7 defaults: Backlog / Todo / In Progress / In Review / Done / Canceled / Duplicate. Replace with the 8 from `LINEAR.md § Statuses` by **renaming in place** where possible (safer than delete-then-add, since each category requires at least one status):
- Pre-step: delete or archive the auto-seeded onboarding issues (e.g. `GIL-1 Get familiar with Linear`, `Set up your teams`, `Connect your tools`, `Import your data`). Otherwise the rename moves them into a real workflow state.
- Re-point "Duplicate issue status" destination dropdown to `Canceled` before deleting the `Duplicate` status.
- Rename `Backlog` → `Inbox`; keep as Default.
- Rename `Todo` → `Ready for Build`.
- Rename `In Progress` → `Building`.
- Rename `In Review` → `AI Audit`; clear the default description `"Pull request is being reviewed"`.
- Add `Human Verify` to Started category.
- Add `Blocked` to Started category; set the icon color distinct from the other Started statuses (red or orange) so stalled work is visually obvious.
- Keep `Done` in Completed.
- Keep `Canceled` in Canceled.
- Delete `Duplicate`.
- Paste the one-line description for each status from `LINEAR.md § Statuses`.

**Team Settings → Workflows & automations.**
All PR automations must be `No action` while the repo is in docs-only phase. The default `On PR merge → Done` silently bypasses AI Audit and Human Verify even with `ref <PREFIX>-N` (not `Fixes`).
- On draft PR open → No action.
- On PR open → No action.
- On PR review request or activity → No action.
- On PR ready for merge → No action.
- On PR merge → No action.
- Auto-close parent issues → Off.
- Auto-close sub-issues → Off.
- Auto-close stale issues → **Off** (staleness is a repo cadence concern; Linear auto-flipping to Canceled would ghost-transition with no repo artifact).
- Auto-archive closed items after → **Never** (per `LINEAR.md § Archival` — deferred).

**Team Settings → Triage.**
- Off initially. Adopting later requires updating `LINEAR.md § Statuses`.

**Team Settings → Cycles.**
- Off (no sprint cadence defined).

**Workspace → Issue labels.**
- Create the exact label set documented in the repo's `LINEAR.md § Labels` section, grouped identically. Workspace-scoped labels are available to every team automatically — do not duplicate at team scope.
- If the repo's `LINEAR.md` does not yet have a `§ Labels` section, **add it during this step**, not after. Label taxonomy drift between repo doc and Linear UI was a real cost in the 2026-04-15 setup.

**Workspace → Templates (or Team → Templates).**
- Create the `Standard issue` template using the body block from `LINEAR.md § Standard Issue Template` verbatim. Use Linear's checklist toolbar to create checkbox items; pasted markdown `[ ]` does not render as interactive checkboxes.
- Status default on the template inherits from the team's default status (not settable separately).

**Workspace → Installed Agents.**
- Remove Codex (and any other coding tool delegation agent) from this surface. The MCP server and the Installed Agents surface are different — the MCP server stays, the delegation agent goes. This enforces `Codex-In-Linear Delegation` being disabled at the tool level rather than only in governance doc.

**Workspace → GitHub integration.**
- Connect a personal GitHub account so activity attributes to the real user.
- Issues Sync: Off (dual-truth hazard).
- Commit linking: Off initially.
- Branch-copy auto-assign / move-to-started: Off.
- PR-state routing rules live in team Workflows & automations (covered above).

**Workspace → AI, Agents, Slack, Notion, Google Calendar, Zapier, etc.**
- All skipped per `LINEAR.md § Deferred Capabilities` unless a specific trigger there has fired.

**Personal notifications.**
- Tune down from Linear's noisy defaults: keep assignments, @-mentions, and status changes on owned issues; disable the rest. Not governance, just comfort.

## §4 Known pitfalls

Mistakes seen in prior setups and their mitigations, recorded so future setups do not relearn them.

1. **Default PR-merge automation silently bypasses audits.** Linear ships with `On PR merge → Done`. Even with `ref <PREFIX>-N` instead of `Fixes`, the automation still flips the issue when that PR merges. Set every PR automation row to `No action` during bootstrap.
2. **Status category minimums block bulk deletion.** Each Linear status category requires at least one status. Rename existing statuses in place rather than delete-then-add. Re-point the `Duplicate issue status` destination before deleting the `Duplicate` status itself.
3. **Onboarding seed issues contaminate the board.** Linear auto-creates several "Get familiar with Linear" issues at team creation. Delete or archive them before renaming the `Todo` status, otherwise they inherit `Ready for Build` and look like real queued work.
4. **Auto-archive and auto-close stale defaults flip state without a repo artifact.** Both default to six months. Set archive to Never and auto-close stale to Off. Staleness and archival are repo cadence concerns, not Linear timer concerns.
5. **Labels created in UI but never documented in `LINEAR.md`.** If the taxonomy lives only in Linear, subsequent prompts that try to "extend the Routing group" will reference structure that doesn't exist in the repo. Create the `§ Labels` section in `LINEAR.md` as part of label creation, not after.
6. **Pasted markdown checkboxes do not render as interactive checklists.** Linear's issue-body editor requires checklists to be created via its toolbar. Pasting `- [ ] item` produces literal text. Build the `Standard issue` template by selecting checklist in the toolbar.
7. **Installed Agents and MCP server are different surfaces.** Removing an installed agent (e.g. Codex) does not remove the MCP server connection and vice versa. `LINEAR.md § Integrations` distinguishes them; bootstrap should too.
8. **Detailed issue history is off by default.** Turn it on during General setup. Auditability is load-bearing for the AI Audit / Human Verify workflow.
9. **`<PREFIX>` placeholder left in `LINEAR.md` after prefix is confirmed.** Replace every occurrence with the actual team prefix (including in `Guardrail`, `PR Linking Convention`, and any `Fixes`/`Closes` examples) during bootstrap, not later.
10. **Prompts that reference existing doc structure without reading the file first.** Before drafting any Codex prompt that says "extend the X section" or "append to the Y group," open the target file and confirm the structure exists exactly as named. This is the single cheapest audit step and eliminates a common class of blocked Codex runs.
