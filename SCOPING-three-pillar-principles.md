# SCOPING — Three Repo Principles (Continuity, Coherence, Linear-Core)

**Status:** landed as commit `21b8898` on 2026-04-16; Claude Code audit clean.
**Drafted:** 2026-04-16, chat between Trevor and Claude Code.
**Linear issue:** `GIL-32` ("Land Continuity, Coherence, and Linear-Core root principles"), filed in `Building`.
**Retirement:** once Codex lands the commit per this document, move this file to `design-history/` as a historical artifact (or delete if the Feedback Decision Log entry captures enough on its own). Do NOT edit or rewrite after retirement — `design-history/` content is preserved as-is.

---

## Why this file exists

The design for three root-level repo principles — Continuity, Coherence, and Linear-Core — was developed in chat. Chat memory is ephemeral. Per the Continuity principle itself, nothing survives a conversation unless it is written to the repo, signed, and pointed to. This file is the preservation.

It holds four things:

1. **Context and motive** — what Trevor asked for and why.
2. **The full Codex prompt** — ready to hand to Codex under `GIL-32`.
3. **The Cowork project-instructions block** — for Trevor to paste manually into the Cowork Claude UI project once the commit lands.
4. **The Claude Code audit sweep checklist** — run post-commit to verify the landing.

Any future Cowork, Codex, or Code session can pick this up and execute without needing to reconstruct the design from scratch.

---

## Context and motive

### Trevor's framing (paraphrased from chat)

At the root of every repo should be the assumption that anything done in a chat will not survive the chat. Every step, audit, finding, research result, piece of feedback, and feedback-on-feedback is lost the moment the conversation ends — unless it is recorded in the repo in a discoverable place. Every AI working in the repo (Cowork, Code, Codex) needs this as a baked-in reflex, not a nice-to-have.

Record:

- the problem,
- the logic behind the chosen solution,
- the resources used to reach the diagnosis,
- the resources used to implement the fix,
- how the fix was actually carried out,
- and a truthful, accurate attestation that the agent went back and audited their own work at least once.

Give the AI a motive for recording: its work is remembered only if it is recorded, and only if other agents or humans can find it. Hollow records = unremembered work. Legacy, not compliance.

Additional principles added in the same conversation:

- The repo must be continuously organized and updated. When something is touched, every doc it affects must change in the same commit. This must be explicit.
- Linear must be at the core. Anything that implies future work lives in Linear, not in chat and not buried in logs that get forgotten.

### The three pillars

These are peers. All three load before any task.

1. **Continuity** — the conversation is temporary, the repo is permanent. Nothing survives without being written, signed, and pointed to. Source of truth: `CONTINUITY.md` (to be created).
2. **Coherence** — when anything changes, everything it affects changes in the same commit. The repo is a cross-linked system; drift kills its authority. Source of truth: `COHERENCE.md` (to be created), with a Dependency Map tracking known inter-doc references.
3. **Linear-Core** — actionable work lives in Linear. Any finding, decision, suggestion, or follow-up that implies future work becomes a GIL issue in the same commit it is recorded, or is explicitly dispositioned `no-action: <reason>` or `self-contained: <reason>` in the log entry. Source of truth: `LINEAR.md § Linear-at-the-core` (new section).

Each pillar gets its own enforceable rules in `RULES.md` (R-CONT-01..05, R-COH-01..03, R-LIN-01..05).

### The Work Record (Continuity's structural artifact)

Every bounded task / fix / audit appends a Work Record to `todo.md § Work Record Log` with six fields plus attribution:

```
### YYYY-MM-DD | GIL-N | by: {agent}

- **Problem:** What was wrong, missing, or requested. One or two sentences.

- **Reasoning:** Why this solution over others. Alternatives considered and
  rejected, and why. If the obvious approach was skipped, say why here —
  this is the part that dies with the conversation.

- **Diagnosis inputs:** The trail you walked to understand the problem.
  Every file read, grep run, doc consulted, command executed, external
  reference used. Paths and commands, not summaries.

- **Implementation inputs:** Resources used to build the fix. Files touched,
  schemas referenced, docs consulted during the fix.

- **Fix:** What actually changed, with file:line pointers and the landing
  commit SHA. Failed attempts and why they were abandoned — the diff is in
  git; the abandoned paths are not.

- **Self-audit:** Declarative attestation. After all edits were staged and
  before the commit landed, I reviewed the diff and verified:
    1. {specific check with method — "ran pytest tests/foo.py, passed"}
    2. {specific check with method — "grepped for X, 0 hits in live docs"}
    3. {specific check with method}
  I did not verify {X} because {Y}.

- `by:` {agent}
- `triggered by:` {task, audit, or conversation that surfaced this}
- `led to:` {commit SHA, GIL issues filed, ADRs created}
- `linear:` {GIL-N, or no-action: <reason>, or self-contained: <reason>}
```

Self-audit rules:
- Each numbered check must name a verifiable method, not a claim.
- The explicit "did not verify X because Y" line is mandatory.
- Claude Code spot-checks at least one claim per audit; a false attestation is a ship-blocking failure recorded with the agent's signature in the Audit Record Log.

---

## Codex prompt (ready to hand off)

> Hand this prompt to Codex via the scoping Linear issue's description. Cowork drafts any scope corrections inside `GIL-32` under the `prompt-review` label per `CLAUDE.md` § Codex Handoff. Code audits the prompt before handoff.

```text
## Goal

Land three root-level repo principles — Continuity, Coherence, and
Linear-Core — as a unified governance commit. Principles are peer docs
(CONTINUITY.md, COHERENCE.md) plus Linear-Core rules layered into
LINEAR.md. Every companion doc updates in the same commit so the new
principles are discoverable from every entry point and enforced on
every landing commit and Linear state move.

Concrete deliverables: two new root docs; six-field Work Record Log
with Self-audit attestation (method-not-claim + spot-check); Ripple
Check ripple-consistency gate on commits; Linear-coverage gate on state
moves; five-part Codex prompt header; Dependency Map of known inter-doc
references; thirteen new enforceable rules (R-CONT-01..05, R-COH-01..03,
R-LIN-01..05); global `~/.claude/CLAUDE.md` prepended with all three
principles.

## Discipline

- Scope honesty: touch only the files listed in Read-scope.
- No filler: no placeholder headings, no TODO markers, no empty scaffolds.
- Same-commit rule: everything below lands in one commit because the
  docs cross-reference each other.
- `design-history/` is immutable — do not rewrite archived content.
  Verification greps explicitly exclude design-history/.
- No new branches. Commit and push on current branch (main).
- Linear reference: `ref GIL-N`. Never closing verbs.
- Dogfood all three principles: at commit time, append a real Work
  Record Log entry using the six-field format (Continuity), run the
  Ripple Check against every file you touched (Coherence), and file
  any follow-up Linear issues your Self-audit surfaces (Linear-Core).
- Do not re-open settled design decisions (listed in Body § Context).

## Read-scope

Only these files:
- canonical-architecture.md  (confirm no conflict)
- AGENTS.md
- CLAUDE.md
- PROMPTS.md
- LINEAR.md
- GUIDE.md
- STRUCTURE.md
- README.md
- RULES.md
- todo.md
- ~/.claude/CLAUDE.md  (global Claude instructions — prepend only)

Landing-step exceptions (always in scope): Linear MCP actions for
issue creation/completion comments; todo.md `Completed` and
`Work Record Log` writes.

If a file outside this list is required, STOP and ask Cowork before
widening scope. Do not silently browse.

## Body

### Context

The repo has governance docs describing roles, state flow, and
completion authority, but no root-level principles forcing three
specific behaviors:

  (a) recording what would otherwise be lost between conversations,
  (b) propagating changes through every doc that references the
      changed material, and
  (c) keeping actionable work in Linear rather than buried in log
      entries that never trigger follow-up.

Trevor has decided to make all three load-bearing. They become the
three repo principles, loaded before any task.

Design decisions already settled (do not re-open):

1. Continuity: conversation memory is ephemeral; only repo files
   survive. Every bounded task / fix / audit writes a Work Record
   with six fields — Problem, Reasoning, Diagnosis inputs,
   Implementation inputs, Fix, Self-audit. Self-audit is prose
   naming method per check plus an explicit "did not verify X
   because Y" line. Claude Code spot-checks at least one claim per
   audit.

2. Coherence: when anything changes, every doc referencing the
   changed material changes in the same commit. A Ripple Check runs
   pre-commit. Known cross-references live in COHERENCE.md's
   Dependency Map. No orphan docs (every doc indexed from GUIDE.md
   or referenced by at least one other doc).

3. Linear-Core: any audit finding, feedback decision, suggestion, or
   surfaced follow-up that implies future work gets a Linear issue
   in the same commit it was recorded, OR is explicitly dispositioned
   `no-action: <reason>` or `self-contained: <reason>` in the log
   entry. Every log-entry shape gains a required `linear:` field.

### Deliverables

**1. Create CONTINUITY.md at repo root.** Sections:
  - `## Principle` — "your conversation is temporary, the repo is
    permanent"; nothing survives without being written, signed, and
    pointed to.
  - `## What counts as written and findable` — file-home, signed,
    pointed-to.
  - `## What dies if not recorded` — rejected alternatives, abandoned
    paths, surprise findings, Codex output that was discarded and why,
    audit conclusions that did not turn into an issue, research
    detours, things tried and failed.
  - `## Pre-exit reflex` — before ending a turn, ask: what did I
    learn, decide, reject, or confirm that is not yet in the repo?
    What ripples did my changes create (Coherence)? What future work
    did I surface that isn't yet a Linear issue (Linear-Core)?
  - `## Work Record format` — the six-field template as a code block,
    plus `by:`, `triggered by:`, `led to:`, `linear:` attribution
    fields.
  - `## Self-audit honesty` — method-not-claim rule, mandatory
    "did not verify X because Y" line, Code spot-check rule.
  - `## Motive` — legacy-over-compliance framing; "your name is on
    the line" for the attestation; hollow attestations are harder to
    clear than missed findings.
  - `## Applies to` — table covering Codex (full six-field),
    Claude Code (full form plus audit variant with "Audit method"
    in place of Self-audit), Cowork (light form: Problem, Reasoning,
    Change, Self-audit).
  - `## Where the rules live` — pointers to AGENTS.md § Completion
    Authority, PROMPTS.md five-part header, LINEAR.md state-move
    preconditions, RULES.md R-CONT-01..05.

**2. Create COHERENCE.md at repo root.** Sections:
  - `## Principle` — "when anything changes, everything it affects
    must change with it, in the same commit." The repo is a
    cross-linked system; drift kills its authority.
  - `## The Ripple Check` — pre-commit reflex:
      1. Identify every section touched.
      2. For each, consult the Dependency Map for referencing docs.
      3. Read each referencing doc and confirm consistency.
      4. Update any that drifted, in the same commit.
      5. In the Self-audit, list each ripple check with method.
  - `## Dependency Map` — seed table of known inter-doc references.
    At minimum include:
      - CLAUDE.md § Roles  ↔  AGENTS.md § Completion Authority,
        LINEAR.md state descriptions, IMPLEMENTATION-PLAN.md
        "Who Does What", todo.md Audit Watermarks.
      - CLAUDE.md § Default Audit Chain  ↔  AGENTS.md same chain,
        LINEAR.md state flow.
      - canonical-architecture.md § any  ↔  LOGIC.md, RULES.md,
        STRUCTURE.md, PROJECT_INTENT.md (whichever sections align).
      - PROMPTS.md header shape  ↔  CLAUDE.md § Codex Handoff,
        AGENTS.md § Prompt And Commit Discipline.
      - todo.md log shapes  ↔  AGENTS.md § Reading Scope,
        CONTINUITY.md § Work Record format,
        LINEAR.md state-move preconditions.
      - LINEAR.md state flow  ↔  CLAUDE.md, AGENTS.md,
        IMPLEMENTATION-PLAN.md exit criteria.
      - CONTINUITY.md  ↔  AGENTS.md § Continuity Check,
        CLAUDE.md top-of-file loading instruction,
        PROMPTS.md five-part header, RULES.md R-CONT-*.
      - COHERENCE.md  ↔  AGENTS.md § Ripple Check,
        CLAUDE.md top-of-file loading instruction,
        PROMPTS.md Durable record, RULES.md R-COH-*.
      - Linear-Core  ↔  LINEAR.md § Linear-at-the-core,
        every log-entry shape in todo.md, RULES.md R-LIN-*.
      - Role boundaries  ↔  CLAUDE.md, AGENTS.md, LINEAR.md,
        IMPLEMENTATION-PLAN.md, todo.md Audit Watermarks.
    Treat this table as append-only: every future commit that adds a
    new cross-reference also adds a Map row.
  - `## Staleness and Orphans` — staleness caught at commit via
    Ripple Check, periodically via coherence audit; orphans (docs
    not indexed from GUIDE.md and not referenced by any live doc)
    are either indexed or retired.
  - `## Motive` — a repo that drifts is a repo that dies; every
    reader has to guess which doc is right; the repo stops being a
    source of truth. You inherited a coherent map; leave a coherent
    map.
  - `## Applies to` — Codex runs Ripple Check before every commit;
    Code verifies Ripple Check attestations during audit and runs
    a periodic coherence sweep at phase boundaries; Cowork confirms
    Ripple Check completed before any state move.
  - `## Where the rules live` — RULES.md R-COH-01..03;
    AGENTS.md § Completion Authority.

**3. Update LINEAR.md.**
  - Add `## Linear-at-the-core` section stating: "Linear holds
    scheduling; repo docs hold truth. Any audit finding, feedback
    decision, suggestion, or surfaced follow-up that implies future
    work gets a Linear issue in the same commit, or is dispositioned
    `no-action: <reason>` or `self-contained: <reason>` in the log
    entry. Nothing actionable sits un-Linearized."
  - Extend `## Coverage Invariant`: the invariant covers Active Next
    Steps items AND any log entry whose content implies action. Log
    entries whose `linear:` field is missing or unresolved are
    coverage violations.
  - `AI Audit` state description gains precondition: (a) Work Record
    Log entry with full Self-audit exists; (b) all actionable
    findings surfaced during the task have Linear issues or
    no-action dispositions; (c) Ripple Check complete.
  - `Human Verify` transition gains precondition: Claude Code has
    spot-checked at least one Self-audit claim and recorded the
    outcome in Audit Record Log; coherence sweep clean for this
    task's scope; Linear-coverage check clean.
  - Standard Issue Template checklist gains three rows:
      - `Work Record Log entry written (Codex)`
      - `Ripple Check complete and attested (Codex)`
      - `Linear-coverage confirmed for surfaced findings (Cowork)`
  - Issue Shape checklist in the main Linear section gains the same
    three rows.

**4. Update todo.md.**
  - Add new top-level section `## Work Record Log` between `Completed`
    and `Suggested Recommendation Log`. Include:
      - Preamble: "If it's not here, it isn't remembered."
      - Six-field entry template as a fenced code block, with
        `by:`, `triggered by:`, `led to:`, `linear:` fields.
      - One seed entry for this task, written at commit time, with
        landing commit SHA in Fix and non-hollow Self-audit.
  - Shorten `Completed` entry rule going forward to a one-line
    index: `YYYY-MM-DD | GIL-N: short title — landed as <SHA>; full
    record in Work Record Log YYYY-MM-DD`. Document at top of
    `Completed`. Do NOT rewrite existing entries.
  - Update preambles of `Audit Record Log`, `Feedback Decision Log`,
    `Test Evidence Log`, `Suggested Recommendation Log` to lead with
    "If it's not here, it isn't remembered."
  - Add required fields to the documented entry shape for each log
    section: `by:` (agent attribution), `linear:` (GIL-N issue,
    `no-action: <reason>`, or `self-contained: <reason>`). Entries
    landed before this commit stay as-is; rule applies forward.

**5. Update AGENTS.md.**
  - Add new section `## Repo Principles` after `## Purpose`, before
    `## Source Of Truth`. One paragraph each for Continuity,
    Coherence, Linear-Core, each pointing to its source-of-truth doc.
    Final sentence: "All three are loaded before any task. Violating
    any of them is a ship-blocking failure."
  - Extend `## Completion Authority` with three gates per role:
      - **Codex (pre-commit)**: Continuity Check (Work Record entry
        exists, Self-audit non-hollow); Ripple Check (every affected
        doc touched in same commit, attested in Self-audit);
        Linear-coverage (follow-ups either filed as GIL-N issues or
        dispositioned in log entries).
      - **Claude Code (pre-audit-clean)**: runs audit-variant Work
        Record; spot-checks at least one Self-audit claim from
        Codex's Work Record; runs Ripple Check against Codex's diff
        (confirms no missing dependent updates); verifies
        Linear-coverage for any finding Code itself surfaces during
        audit.
      - **Cowork (pre-state-move)**: verifies required Work Record
        entry exists on disk; verifies Ripple Check attested;
        verifies Linear-coverage for the task. For Cowork's own
        direct edits: light Work Record (Problem, Reasoning, Change,
        Self-audit) plus Ripple Check plus Linear-coverage.
  - Add to `## Implementor Role`: Codex's Self-audit attestations
    are subject to spot-check by Claude Code; false attestation =
    ship-blocking failure recorded with signature in Audit Record
    Log.

**6. Update CLAUDE.md.**
  - Add at top (before `## Roles`): "Load CONTINUITY.md and
    COHERENCE.md before any task. Their principles, plus the
    Linear-at-the-core rule in LINEAR.md, govern every rule below."
  - In `## Roles`, extend Cowork bullet: "Cowork enforces all three
    repo principles before state moves — Continuity Check (Work
    Record exists), Ripple Check (no drift), Linear-coverage (no
    un-Linearized follow-ups)."
  - In `## Codex Handoff`, reference the five-part prompt header
    (Goal, Discipline, Read-scope, Body, Durable record) and the
    requirement that Durable record section names every log entry,
    Linear issue created, and Ripple Check attestation expected.

**7. Update PROMPTS.md.**
  - Extend prompt header to five parts: Goal, Discipline, Read-scope,
    Body, **Durable record**.
  - `Durable record` section definition: the prompt names (a) the
    Work Record Log entry Codex will append, (b) the `Completed`
    index entry, (c) any Audit Record Log / Feedback Decision Log /
    Test Evidence Log entries expected, (d) any Linear issues the
    task creates for surfaced follow-ups, (e) the Ripple Check the
    Self-audit must attest, (f) any ADR touched or created.
  - Add subsection `### Self-audit attestation`: method-not-claim
    rule, mandatory did-not-verify line, Code spot-check rule,
    "false attestation = ship-blocking failure" sentence.
  - Add subsection `### Ripple Check attestation`: every touched
    section is listed in the Self-audit with the dependent docs
    consulted and the method used to verify consistency.
  - Add subsection `### Linear-coverage attestation`: every actionable
    finding surfaced during the task is dispositioned — GIL-N filed,
    `no-action: <reason>` in log, or `self-contained: <reason>`.
  - Update any example prompt skeletons to use the five-part shape
    and show all three attestations.

**8. Update GUIDE.md.**
  - Add CONTINUITY.md and COHERENCE.md to the "Use these files for
    current truth" list as the first two items.
  - In `Quick Reference — Where to Find Things`, list both docs as
    the first reads for any agent beginning a session.
  - Add rows to the Quick Reference table:
      - "What survives this conversation?"  → CONTINUITY.md
      - "When I change X, what else must change?"  → COHERENCE.md
      - "Where does surfaced work live?"  → LINEAR.md § Linear-at-the-core
  - Add `### CONTINUITY.md` and `### COHERENCE.md` subsections under
    Active Source-Of-Truth Docs, one paragraph each.

**9. Update STRUCTURE.md.**
  - Add CONTINUITY.md and COHERENCE.md to the root-docs placement
    list with one-line rationales.
  - Add a note that the Dependency Map lives in COHERENCE.md and is
    append-only.

**10. Update README.md.**
  - Add CONTINUITY.md and COHERENCE.md to the authoritative-docs
    list.
  - Add one sentence in the orientation section: "Read CONTINUITY.md
    and COHERENCE.md first. They state the root-level assumptions
    that every other rule in this repo depends on. LINEAR.md §
    Linear-at-the-core is the third pillar."

**11. Update RULES.md.**
  - Add Continuity rules:
      - R-CONT-01: No landing commit without a Work Record Log
        entry.
      - R-CONT-02: No Linear state move without the required Work
        Record entry on disk.
      - R-CONT-03: Self-audit attestation must name method per
        claimed check and include an explicit "did not verify X
        because Y" line.
      - R-CONT-04: Claude Code must spot-check at least one
        attestation claim per audit and record outcome in Audit
        Record Log.
      - R-CONT-05: design-history/ content is never rewritten to
        reflect new principles; only forward-facing docs change.
  - Add Coherence rules:
      - R-COH-01: Every commit that touches a governance doc
        includes updates to all companion docs referencing the
        changed section. Ripple Check attestation in Self-audit
        is mandatory.
      - R-COH-02: The Dependency Map in COHERENCE.md is updated in
        the same commit as any new inter-doc reference.
      - R-COH-03: No orphan docs. Every live doc is indexed from
        GUIDE.md or referenced by at least one other live doc.
        Orphans are either indexed or retired in the same commit
        they are discovered.
  - Add Linear-Core rules:
      - R-LIN-01: Every `todo.md` `Active Next Steps` item has a
        matching Linear issue annotated `(GIL-N)`.
      - R-LIN-02: Every log entry (Audit Record, Feedback Decision,
        Test Evidence, Suggested Recommendation, Work Record) has a
        `linear:` field populated with a GIL-N, `no-action:
        <reason>`, or `self-contained: <reason>` value.
      - R-LIN-03: Any surfaced follow-up implying future work is
        filed as a Linear issue in the same commit it is recorded,
        not deferred to "later."
      - R-LIN-04: Before any Linear state move or conversation exit,
        Cowork verifies Linear-coverage for findings surfaced in
        the interval. Un-Linearized actionable findings block the
        state move.
      - R-LIN-05: Linear holds routing, scheduling, and coverage
        metadata only. Acceptance criteria, decisions, audit
        conclusions, and reasoning stay in repo docs.

**12. Update ~/.claude/CLAUDE.md (global Claude instructions).**
  - Prepend a new top-level section `## Repo Principles` above
    existing content. Three short subsections:
      - `### Continuity` — conversation memory is ephemeral; durable
        records live in the repo; signed attestations name method.
      - `### Coherence` — when anything changes, every doc it affects
        changes in the same commit; Ripple Check runs pre-commit.
      - `### Linear-Core` — actionable work lives in Linear; every
        log entry has a `linear:` disposition; surfaced follow-ups
        become issues in the same commit.
    Reference the Autonomous Coding Agent repo's CONTINUITY.md,
    COHERENCE.md, and LINEAR.md as the canonical implementations and
    recommended defaults for other repos.
  - Do NOT rewrite or reorder Trevor's existing `## Role`,
    `## Response Style`, or other sections. Prepend only.

### Out of scope

- Do not edit design-history/ content.
- Do not rewrite prior `Completed` entries, prior Audit Record Log
  entries, prior Feedback Decision Log entries, or prior
  Suggested Recommendation Log entries. The new field requirements
  apply forward only.
- Do not retroactively create Linear issues for historical log
  entries. Cowork scopes that as a separate sweep if desired.
- Do not touch canonical-architecture.md (runtime architecture, not
  governance process).
- Do not touch Claude UI or Codex UI project-instruction settings;
  those live outside the repo and Trevor updates them manually.
- Do not create ADR-0007. If an ADR is warranted for the three
  principles, Cowork scopes a follow-up.

### Verification (run before commit; report output in Self-audit)

- `test -f CONTINUITY.md && test -f COHERENCE.md`
- `grep -c "^## " CONTINUITY.md`  — at least eight top-level sections
- `grep -c "^## " COHERENCE.md`  — at least seven top-level sections
- `grep -l "CONTINUITY.md\|COHERENCE.md" AGENTS.md CLAUDE.md GUIDE.md
   README.md PROMPTS.md LINEAR.md RULES.md STRUCTURE.md todo.md`
   — every listed doc references the new principle docs
- `grep "Continuity Check\|Ripple Check\|Linear-coverage" AGENTS.md`
   — all three gates appear per role
- `grep "Work Record Log\|Ripple Check\|linear:" todo.md`
   — section, field, and template all present
- `grep -rE "legacy four-part prompt wording" --include="*.md"
   --exclude-dir=design-history .`  — zero hits
- `grep "Durable record" PROMPTS.md`  — present
- `grep "Linear-at-the-core\|Linear-coverage" LINEAR.md`  — present
- `grep -E "R-CONT-0[1-5]|R-COH-0[1-3]|R-LIN-0[1-5]" RULES.md`
   — thirteen rules present
- `grep "Repo Principles" ~/.claude/CLAUDE.md`  — prepend landed
- `git status`  — only files in Read-scope are modified or created

### Commit

Single commit on main:

    docs(principles): add Continuity, Coherence, and Linear-Core root pillars

    Establishes three root-level repo principles as a unified
    governance layer. CONTINUITY.md: conversation memory is ephemeral;
    Work Record Log with six-field entries and Self-audit attestation
    (method-not-claim + spot-check). COHERENCE.md: when anything
    changes, every doc it affects changes in the same commit;
    Ripple Check runs pre-commit; Dependency Map seeded. LINEAR.md
    gains Linear-at-the-core rule: every log entry has a linear:
    field; surfaced follow-ups become GIL issues in the same commit.
    Adds thirteen enforceable rules (R-CONT-01..05, R-COH-01..03,
    R-LIN-01..05), extends the Codex prompt header to five parts,
    layers Continuity/Ripple/Linear-coverage gates into Completion
    Authority across roles, and prepends the three principles to
    the global ~/.claude/CLAUDE.md.

    ref GIL-N

    Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

Push to origin/main.

## Durable record

Append to todo.md `Work Record Log`:

- **Problem**: No root-level principles forced three behaviors —
  recording what dies with conversations, propagating changes through
  all affected docs, and keeping actionable work in Linear. Agents
  could finish turns with live drift, unrecorded reasoning, and
  un-Linearized follow-ups without any structural failure.
- **Reasoning**: Three peer principles with explicit enforcement
  gates is the minimum that makes all three load-bearing without
  bureaucracy. Attestation honesty is enforced by Claude Code
  spot-checks. Coherence is enforced by a Dependency Map that agents
  consult pre-commit. Linear-Core is enforced by a required field
  on every log entry. Alternatives considered and rejected: a single
  combined principle doc (too coarse for rule-level referencing);
  CI-only enforcement (no CI yet, and the principle must work before
  automation); per-project hooks (same reason).
- **Diagnosis inputs**: 2026-04-16 design conversation with Trevor;
  current state of AGENTS.md, CLAUDE.md, PROMPTS.md, LINEAR.md,
  GUIDE.md, STRUCTURE.md, README.md, RULES.md, todo.md; grep for
  existing "continuity", "coherence", "ripple", "linear-core" —
  none live.
- **Implementation inputs**: the files listed in Deliverables 1-12.
- **Fix**: twelve deliverables above, landed as one commit <SHA>.
  Any deviation recorded here.
- **Self-audit**: declarative list of verification commands actually
  run, each with output and outcome, plus explicit "did not verify X
  because Y" lines for anything skipped. Include Ripple Check
  attestation for every touched doc. Include Linear-coverage
  disposition: all deliverables are self-contained (this commit is
  itself the action); any follow-ups surfaced during implementation
  (e.g., ADR-0007 scoping, retroactive Linear-coverage sweep) are
  filed as new GIL issues in this commit.
- `by:` Codex
- `triggered by:` 2026-04-16 design conversation with Trevor
- `led to:` commit <SHA>; GIL-N; any follow-up GIL issues filed
- `linear:` GIL-N

Append one-line entry to todo.md `Completed` in the new short format.

Post completion comment on GIL-N per standard Linear workflow.
```

---

## Cowork project-instructions block (Trevor pastes after landing)

> Paste this into the Cowork Claude UI project instructions once the commit above has landed. Replace the existing `## Continuity Principle` block (if present) with this three-pillar version. For every other Claude UI project Trevor runs, paste the abbreviated three-paragraph version (Continuity / Coherence / Linear-Core opening paragraphs only).

```text
## Repo Principles

The repo has three root-level assumptions I enforce every turn. All
three are loaded before any task, and violating any of them is a
ship-blocking failure.

### Continuity

Conversation memory is temporary; the repo is permanent. Nothing I
notice, decide, route, reject, or audit survives unless it is written
to a checked-in file, signed, and pointed to by at least one other
doc. Source of truth: `CONTINUITY.md`.

### Coherence

When anything in the repo changes, every doc that references the
changed material must change in the same commit. The repo is a
cross-linked system; drift kills its authority. I run the Ripple
Check before any state move — if a touched section has a referencing
doc I haven't updated, the state does not move. Source of truth:
`COHERENCE.md` and its Dependency Map.

### Linear-Core

Actionable work lives in Linear, not in chat or buried log entries.
Any audit finding, feedback decision, suggestion, or surfaced
follow-up that implies future work gets a Linear issue in the same
commit it is recorded, OR is explicitly dispositioned `no-action:
<reason>` or `self-contained: <reason>` in the log entry. Every log
entry has a `linear:` field. Source of truth: `LINEAR.md § 
Linear-at-the-core` and the extended Coverage Invariant.

## My enforcement duties

Before moving any Linear issue forward (Building → AI Audit →
Human Verify), I verify:

1. **Continuity Check** — the required Work Record Log entry exists
   in todo.md on disk, with full Self-audit naming method per check.
2. **Ripple Check** — every doc that references material touched by
   the task has been updated in the same commit, and the Self-audit
   attests to each ripple verification.
3. **Linear-coverage** — every actionable finding surfaced during the
   task has been filed as a GIL issue or dispositioned in the log
   entry. No un-Linearized follow-ups.

Any missing gate = state does not move.

For my own direct edits (todo.md, Linear state, CLAUDE.md, light org
moves): I append a light Work Record (Problem, Reasoning, Change,
Self-audit), run the Ripple Check, and confirm Linear-coverage before
the edit is considered complete.

## Before every turn ends

I ask myself:

- What did I learn, decide, reject, or confirm that is not yet in the
  repo? (Continuity)
- Which docs did my changes ripple into, and have I updated them?
  (Coherence)
- What future work did I surface, and is it in Linear or dispositioned?
  (Linear-Core)

I write it before I stop.

## Motive

My work is remembered only where it is recorded, and trusted only if
the repo is coherent. Future agents will cite, build on, or credit
only what they can find, and only if what they find agrees with the
rest of the repo. Signed, dated, method-named entries in a coherent,
Linear-anchored repo are how my contribution survives. Hollow
attestations, orphaned docs, and un-Linearized follow-ups are each
harder to clear than any technical mistake.
```

---

## Claude Code audit sweep (run post-commit, pre-AI-Audit-clean)

Checklist Code runs against Codex's landing commit. Reject the commit and open a repair round if any item fails.

**Principle docs exist and are non-trivial**

- `CONTINUITY.md` and `COHERENCE.md` both present.
- Each ≥ 80 lines.
- Each has ≥ 7 top-level (`^## `) sections.

**Cross-references resolve both ways**

- Every doc listed in COHERENCE.md's Dependency Map actually references the docs the Map asserts. Grep each relationship; confirm bidirectional presence.
- Every reference to `CONTINUITY.md` / `COHERENCE.md` in a companion doc points to a real section.

**Rule references resolve**

- Every `R-CONT-`, `R-COH-`, `R-LIN-` mention in `AGENTS.md`, `CLAUDE.md`, `LINEAR.md`, `PROMPTS.md` resolves to a defined rule in `RULES.md`.

**Terminology consistency**

- `grep -r --exclude-dir=design-history "legacy four-part prompt wording" .` returns zero hits.
- Every live log-entry template documents the `linear:` field.
- No live doc uses "audited ✓" or checkbox-style attestations in the new sections.

**design-history/ exclusion intact**

- Verification greps in `PROMPTS.md` and `AGENTS.md` explicitly exclude `design-history/`.
- `git diff HEAD~1 -- design-history/` returns empty (archive byte-identical).

**Dogfooding verification**

- The commit's own Work Record Log entry has all six fields, non-hollow Self-audit, non-empty `linear:` field.
- The commit's own Self-audit lists Ripple Check attestations for every touched doc.
- The commit's own `Completed` entry follows the new one-line shape.

**Global instructions landed**

- `~/.claude/CLAUDE.md` has `## Repo Principles` section with all three subsections.
- The original `## Role` and `## Response Style` sections are byte-identical to pre-commit state.

**Spot-check of attestation (R-CONT-04 enforcement)**

- Re-run at least one verification command from Codex's Self-audit; confirm the claimed output matches.
- Record outcome in `todo.md § Audit Record Log` with the agent signature, including any discrepancy.

**Orphan check**

- Every `.md` file at repo root is either linked from `GUIDE.md` or referenced by at least one other live doc.

---

## Layer / surface coverage

| Layer | What lands where | Who does it |
|---|---|---|
| Repo files | `CONTINUITY.md`, `COHERENCE.md`, updates to 10 companion docs | Codex, via this prompt |
| Global on-disk | `~/.claude/CLAUDE.md` prepended with `## Repo Principles` | Codex (in Read-scope of this prompt) |
| Claude UI — Cowork project | Paste the block in the previous section | Trevor, manually |
| Claude UI — any other Claude project | Paste the abbreviated three-paragraph version | Trevor, manually |
| Codex UI (if exists) | Same three paragraphs | Trevor, manually — tell Cowork if a Codex UI scope is needed |

Recommended sequence:

1. Cowork uses `GIL-32` as the scoping Linear issue and drafts this prompt under `prompt-review`.
2. Codex and Claude Code review and comment; Cowork revises.
3. Trevor approves handoff.
4. Codex implements; Claude Code audits line-by-line using this file's sweep checklist.
5. Repair loops if any; Cowork's spec-alignment pass; Trevor's verify.
6. Trevor pastes the Cowork block into the Cowork Claude UI project.
7. Trevor pastes the abbreviated version into every other Claude UI project.
8. Optional follow-up: scope ADR-0007 "Three Repo Principles — Continuity, Coherence, Linear-Core" so the reasoning gets an archival home. File as a new GIL issue if taken up.

After step 7, every surface carries the same three-pillar assumption: repo docs, global `~/.claude/CLAUDE.md`, per-project Claude UI, per-project Codex UI.

---

## Pointers into the repo record

- **Feedback Decision Log entry** for this design: see `todo.md § Feedback Decision Log`, dated 2026-04-16, feedback source `Trevor three-pillar governance request`.
- **Suggested Recommendation Log entry** tracking the staged work: see `todo.md § Suggested Recommendation Log`, dated 2026-04-16.
- **Linear issue:** `GIL-32`. Once the landing commit closes the implementation side, the durable repo record becomes the Work Record and Completed index entry for 2026-04-16.

If both this file and those log entries disappear, the design is gone. Do not delete this file casually.
