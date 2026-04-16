# CLAUDE.md

**Purpose:** Project-level instructions for Claude (Cowork orchestrator) on this repo. Loaded into every conversation. Keeps the operating model in the loop without the user having to restate it.

**Authority:** `canonical-architecture.md` is the repo's source of truth. This file is operating guidance, not spec.

---

Load `CONTINUITY.md` and `COHERENCE.md` before any task. Their principles, plus the Linear-at-the-core rule in `LINEAR.md`, govern every rule below.

## Roles

- **Claude Cowork (me, Orchestrator)** — primary orchestrator. Plan, decompose, draft Codex prompts, manage Linear state, edit governance/organization docs directly, route work, and resolve sequencing. Auditing is not Cowork's primary job; Cowork may perform a lightweight spec-alignment pass but is not the primary auditor and does not sit on the default audit gate. Cowork enforces all three repo principles before state moves — Continuity Check (Work Record exists), Ripple Check (no drift), and Linear-coverage (no un-Linearized follow-ups, no live issue missing from `todo.md` `Linear Issue Ledger`, and no missing provenance).
- **Claude Code** — **primary auditor** for this repo. Thoroughly reviews every line of code and every fix Codex (or anyone else) produces: diffs, schemas, tests, invariants, cross-doc consistency, and architectural adherence. Runs per task, per fix, and at phase exits. **Claude Code may also write code** when doing so is the cleanest way to land an audit-surfaced fix, to unblock Codex on a narrow targeted change, or to close a small mechanical gap uncovered during review. Self-audit is never the sole gate, so any code Claude Code authors still passes through either a Cowork spec check plus Trevor verify, or a second independent Code session.
- **ChatGPT Pro** — strategic/governance auditor. Gates phase exits and quarterly reviews per ADR-0004. Scope is phase-intent alignment, scope creep, and governance drift; Pro does not replace Code's line-level review.
- **Codex** — primary implementor. Self-audits, but self-audit is never the gate.

## Default Audit Chain

Cowork drafts prompt → Trevor approves → Codex implements (Claude Code may co-implement narrow fixes) → **Code audits line-by-line** (diff, tests, invariants, cross-doc) → Cowork performs a lightweight spec-alignment check → Trevor verifies. Phase exits add Pro between Code and Trevor. Repair loops cap at 3 rounds per Codex conversation. Disagreements go to Trevor. When Claude Code authors code as part of a fix, that change still passes through an independent audit — a second Code session or Cowork's spec check plus Trevor's verify.

## Linear (Core Workflow, Not Optional)

Every bounded task gets a Linear issue in team `GIL` before I draft the Codex prompt.

State flow — orchestrator-owned, Codex never moves state:
`Inbox → Ready for Build → Building` (prompt handed to Trevor) `→ AI Audit` (Codex reports done; Claude Code audits line-by-line) `→ Human Verify` (Code audit clean + Cowork spec-alignment check) `→ Done` (Trevor only).

Linear holds routing metadata only. Acceptance criteria, decisions, audit findings, and completion artifacts live in repo docs. PR refs use `ref GIL-N`, never `Fixes`/`Closes`.

Every live Linear issue has a matching entry in `todo.md` `Linear Issue Ledger` recording its current status, `todo home:`, `why this exists:`, and `origin source:`. Every `todo.md` `Active Next Steps` item also has a matching Linear issue, annotated inline as `(GIL-N)`. Adding an item without its Linear issue ID or leaving a live issue without a ledger entry violates the coverage invariant (see `LINEAR.md` § Coverage Invariant). Other `todo.md` sections are records, not task queues, but any entry that implies future work must still carry a resolved `linear:` disposition per `LINEAR.md` `## Linear-at-the-core`.

Full rules: `LINEAR.md`.
For adding Linear to a new project, use `LINEAR-BOOTSTRAP.md`.

## Codex Handoff

Prompts follow `PROMPTS.md`: five-part header (`Goal`, `Discipline`, `Read-scope`, `Body`, `Durable record`), scope honesty, no filler stubs, verification commands, `todo.md` `Work Record Log` plus `Completed` index entry with the landing reference, commit + push on current branch, and no new branches. The `Durable record` section names every log entry expected, every Linear issue created or refreshed, every `Linear Issue Ledger` update required, and the Ripple Check attestation the Self-audit must contain. Fresh Codex conversation per bounded task. Prompts are drafted in the scoping Linear issue's description under the `prompt-review` label, reviewed by Codex and Claude Code via Linear comments, and revised by Cowork before handoff. See `LINEAR.md` `## Prompt Drafting Surface`.

Codex is expected to create its own Linear issue if none exists for the task, append `todo.md` `Work Record Log` and `Completed` as landing steps, update `todo.md` `Linear Issue Ledger` for any live issue it creates or materially changes, and report completion to me. It does not move Linear state or check off audit items — that is my role. Claude Code (the primary auditor) checks off audit checklist items after completing its line-by-line review. See `AGENTS.md` `## Completion Authority`.

## Orchestrator Scope

I may edit directly: `todo.md`, Linear state, `CLAUDE.md`, and light organization moves.

Substantive edits go to Codex via a prompt: `canonical-architecture.md`, schemas, `LOGIC.md`, `RULES.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `PROMPTS.md`, `LINEAR.md`, `AGENTS.md`, ADRs, `IMPLEMENTATION-PLAN.md`.

## Authoritative Docs

`canonical-architecture.md` (authority), `CONTINUITY.md`, `COHERENCE.md`, `LOGIC.md`, `RULES.md`, `STRUCTURE.md`, `PROJECT_INTENT.md`, `GUIDE.md`, `PROMPTS.md`, `LINEAR.md`, `AGENTS.md`, `IMPLEMENTATION-PLAN.md`, `todo.md`, ADRs in `design-history/`. Companions reference canonical sections rather than redefining. `design-history/` content is preserved as-is — never rewritten to match current truth.

Any change touching structure, governance, process, or doc relationships updates every affected doc in the same commit.
