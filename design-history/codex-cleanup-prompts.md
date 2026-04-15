# Codex Cleanup Prompts — Phase 0 Unblock Pass

Five prompts, run in sequence. Each prompt tells Codex exactly which files to read so it stays in repo-style. **Do not create branches.** Work on the current branch. After each prompt, commit with the suggested message. Every prompt ends by appending to `WORK-LOG.md` (create if missing) under a dated entry.

---

## Prompt 1 — Fill `PROJECT_INTENT.md`

```
You are working in the Autonomous Coding Agent repo on the current branch. Do not create a new branch.

GOAL
Replace the placeholder template in PROJECT_INTENT.md with the real project intent. The purpose of this repo is already stated implicitly in canonical-architecture.md §1 and in README.md — your job is to make it explicit and first-class.

REQUIRED READING (read only these; do not browse the rest of the repo)
1. PROJECT_INTENT.md — the current template you are replacing.
2. canonical-architecture.md §1 "Purpose & Scope" (lines ~1–80) — the authoritative purpose statement.
3. README.md — repo-level framing, tone, and terminology.
4. GUIDE.md §"How to read this repo" (first ~60 lines) — learn how the repo wants docs to cross-reference each other.

WHAT TO PRODUCE IN PROJECT_INTENT.md
A single document, no TODOs, no placeholders, with these sections in order:
- Purpose — one paragraph, derived from canonical-architecture.md §1, written as a declarative statement not a goal list.
- Primary users — who runs this system and in what role (orchestrator, auditor, builder). Derive from canonical-architecture.md and the user-role framing in GUIDE.md.
- Non-goals — explicit list of what this repo will NOT do in v1. Pull from canonical-architecture.md "v1 Exclusions" and RULES.md if the scope constraints are named there. If any non-goal is not already written down, do not invent one; flag it at the bottom under an "Open questions" section instead.
- Success metrics — observable, verifiable outcomes that indicate v1 is done. Prefer metrics already named in canonical-architecture.md or IMPLEMENTATION-PLAN.md over newly invented ones.
- Relationship to other docs — one short paragraph pointing readers to canonical-architecture.md (source of truth), RULES.md (constraints), LOGIC.md (control flow), STRUCTURE.md (folders), and GUIDE.md (reading order). This section makes PROJECT_INTENT.md a valid entry point.

STYLE RULES
- Match the prose tone of canonical-architecture.md. No bullets-only sections; use prose with minimal lists.
- Do not restate the architecture. Link to canonical-architecture.md for anything architectural.
- Do not exceed ~150 lines.

LOGGING
Create WORK-LOG.md at the repo root if it does not exist. Append a dated entry:
  ## 2026-04-14 — PROJECT_INTENT filled
  - Replaced template with real intent sourced from canonical-architecture.md §1 and README.md.
  - Open questions surfaced: <list any>.

COMMIT
Single commit at the end of this task:
  git add PROJECT_INTENT.md WORK-LOG.md
  git commit -m "docs(intent): replace template with real project intent"
  git push

DO NOT
- Do not create a branch.
- Do not edit any file other than PROJECT_INTENT.md and WORK-LOG.md.
- Do not invent non-goals or success metrics that are not already grounded in canonical-architecture.md, RULES.md, or IMPLEMENTATION-PLAN.md.
```

---

## Prompt 2 — Resolve the repo-boundary ambiguity in `STRUCTURE.md`

```
You are working in the Autonomous Coding Agent repo on the current branch. Do not create a new branch.

GOAL
STRUCTURE.md currently describes `.agent/` and `.autoclaw/` as folders that live in BOTH this control-plane repo and in target repos. That is the single biggest Phase 0 blocker: the next implementer cannot place contracts, fixtures, schemas, or run state without a clear rule. Your job is to eliminate the dual-location ambiguity and write the boundary down as canonical.

THE BOUNDARY (this is the decision you are implementing, not re-opening)
- TARGET REPO owns: `.agent/contract.yml` and any target-repo-specific contract artifacts. That is it. `.agent/` means "target repo contract surface."
- THIS (CONTROL-PLANE) REPO owns: `schemas/`, `fixtures/`, `supervisor/`, `tests/`, `prompts/` (if adopted), `policies/` (if adopted), and historical docs under `design-history/`.
- RUN ARTIFACTS: supervisor-owned on disk under `.autoclaw/runs/<run-id>/` at runtime. `.autoclaw/` is gitignored. It does NOT live in the target repo and it does NOT get committed to this repo.
- TOOLCHAIN: Codex CLI is a hard runtime dependency. acpx is the adapter. If Codex is unavailable, Phase 0 halts at entry.

REQUIRED READING
1. STRUCTURE.md in full (it is the file you are rewriting).
2. canonical-architecture.md — only §§ titled "Folder Structure", "Control Plane vs Target", "Runtime State", and "Memory" (search by heading; do not read the whole doc).
3. RULES.md — only the section enumerating file-placement rules or forbidden paths (search for "forbidden", "path", "placement", "writer").
4. AGENTS.md — only the top orientation block, to confirm tone.

WHAT TO PRODUCE
Rewrite STRUCTURE.md so that:
- Section 1 states the boundary rule above as the first authoritative paragraph, in prose.
- Section 2 lists ONLY this repo's folders, with a one-line purpose each. Order: `schemas/`, `supervisor/`, `fixtures/`, `tests/`, `prompts/`, `policies/`, `design-history/`, plus doc files at root. Do not list individual files.
- Section 3 lists the target-repo surface. It contains one folder (`.agent/`) and one file convention (`.agent/contract.yml`). Name any companion files (e.g. `.agent/ui-acceptance.yml`) only if canonical-architecture.md already names them.
- Section 4 describes runtime state: `.autoclaw/runs/<run-id>/state.json` plus any sibling artifact conventions already named in canonical-architecture.md. State explicitly that `.autoclaw/` is gitignored in both this repo and in target repos.
- Section 5 is a "Where does X go?" decision table in prose (not a giant table) covering: a new schema, a new benchmark fixture, a new supervisor test, a new run artifact, a new policy rule, a new ADR, a new prompt template. For each, name the folder and give a one-sentence rationale.

CROSS-DOC UPDATES
- If canonical-architecture.md, LOGIC.md, RULES.md, or IMPLEMENTATION-PLAN.md contain any sentence that says or implies `.agent/` lives in this repo, or that `.autoclaw/` lives in a target repo, update that sentence to point at STRUCTURE.md and align with the boundary above. Touch the minimum lines required.
- Do not rewrite entire sections of those docs. Small surgical edits only.
- List every such cross-doc edit at the end of STRUCTURE.md in a "Changes propagated" appendix with file path and line number.

.gitignore
Add a `.gitignore` at the repo root (create if missing) that ignores at minimum: `.autoclaw/`, `.claude/`, `worktrees/`, `node_modules/`, `__pycache__/`, `.venv/`, `.env`, `.env.*`, `dist/`, `build/`. Keep it minimal; do not add ecosystem-specific rules we do not yet need.

LOGGING
Append to WORK-LOG.md:
  ## 2026-04-14 — Repo boundary resolved
  - STRUCTURE.md rewritten to remove `.agent/` + `.autoclaw/` dual-location ambiguity.
  - Boundary: target owns `.agent/contract.yml`; control plane owns schemas/supervisor/fixtures/tests; run artifacts under `.autoclaw/runs/` (gitignored).
  - Cross-doc edits: <list file:line pairs>.
  - Added .gitignore.

COMMIT
Single commit:
  git add STRUCTURE.md .gitignore WORK-LOG.md <any cross-doc files touched>
  git commit -m "docs(structure): resolve control-plane vs target-repo boundary"
  git push

DO NOT
- Do not open `.agent/` debate. The boundary is decided; you are writing it down.
- Do not introduce new folders not named above.
- Do not touch canonical-architecture.md beyond the surgical alignment edits described.
```

---

## Prompt 3 — Scaffold the five schemas

```
You are working in the Autonomous Coding Agent repo on the current branch. Do not create a new branch.

GOAL
Create the five JSON Schemas that define every machine-crossing boundary in the system. Until these exist, LOGIC.md, PROMPTS.md, and IMPLEMENTATION-PLAN.md all reference types that have no canonical shape. Your job is to convert the prose definitions already in canonical-architecture.md into Draft 2020-12 JSON Schemas and place them under `schemas/` in this repo.

THE FIVE SCHEMAS (names are authoritative; use these exact filenames)
1. schemas/run-contract.schema.json — the shape of `.agent/contract.yml` (commands: setup, test, app_up, app_health; plus any fields canonical-architecture.md names).
2. schemas/strategy-decision.schema.json — the output the AI strategy layer hands the supervisor.
3. schemas/failure-fingerprint.schema.json — the normalized form of a test/runtime failure used for cross-run memory.
4. schemas/defect-packet.schema.json — what the UI/readiness verifier emits when it finds a defect.
5. schemas/readiness-report.schema.json — the final readiness gate output.

REQUIRED READING
1. canonical-architecture.md — read only the sections that define each of the five types. Search for headings or occurrences of: "contract", "StrategyDecision", "failure fingerprint", "defect packet", "readiness report", "Release Checker". Read those sections and their immediate surrounding context. Do not read the whole document.
2. PROMPTS.md — read only the prompt sections that reference these types (search for the same terms). Use them to confirm field names actually consumed downstream.
3. IMPLEMENTATION-PLAN.md — read only the phase sections that consume these types (search same terms). Use them to confirm required vs optional fields.
4. STRUCTURE.md — read the freshly-written Section 2 and Section 5 to confirm `schemas/` is the correct location.

WHAT TO PRODUCE
For each schema:
- $schema: "https://json-schema.org/draft/2020-12/schema"
- $id: a stable URI of the form "https://autonomous-coding-agent.local/schemas/<name>.schema.json"
- title, description
- type: object
- additionalProperties: false at the top level and at every nested object level unless canonical-architecture.md explicitly allows extension
- required: list every field the prose calls mandatory; everything else optional
- For enum-like fields (state, verdict, severity), define them as string enums with the exact values used in the docs AFTER prompt 4 normalization. If you run this prompt BEFORE prompt 4, use the values currently in canonical-architecture.md §"Phases" and flag at the end that they will be revisited.
- For every field, include a description string explaining what it is and, where useful, pointing at the canonical-architecture.md section (by heading, not line number) that defines it.
- Include an `examples` array at the top of each schema with one minimal valid example and, where useful, one valid maximal example.

TERMINAL STATE COORDINATION
- If prompt 4 (terminal-state normalization) has already run, use the normalized vocabulary. Check canonical-architecture.md first. If `run_state` and `readiness_verdict` are already separated there, follow that.
- If prompt 4 has NOT run yet, use the current vocabulary from canonical-architecture.md as-is and add a top-level `x-pending-normalization: true` extension field on any schema that contains a terminal-state enum. Prompt 4 will clean these up.

VALIDATION
Add schemas/README.md (short) explaining:
- Purpose of the schemas directory.
- How to validate an instance against a schema locally (reference `ajv` CLI; do not add it as a dependency yet — just name the command).
- A rule that any schema change requires a corresponding note in WORK-LOG.md and a bumped $id minor suffix if the change is breaking.

DO NOT ADD
- Do not add supervisor code, validators, or CI yet.
- Do not invent fields that are not named in canonical-architecture.md, PROMPTS.md, or IMPLEMENTATION-PLAN.md. If a field seems missing, list it in the schema's description as an open question. Do not silently invent it.

LOGGING
Append to WORK-LOG.md:
  ## 2026-04-14 — Schemas scaffolded
  - Created schemas/{run-contract,strategy-decision,failure-fingerprint,defect-packet,readiness-report}.schema.json.
  - Source sections (by canonical-architecture.md heading): <list them>.
  - Open questions surfaced per schema: <list>.
  - Pending terminal-state normalization: <yes|no based on whether prompt 4 already ran>.

COMMIT
Single commit:
  git add schemas/ WORK-LOG.md
  git commit -m "schemas: scaffold five boundary schemas (contract, strategy, fingerprint, defect, readiness)"
  git push

DO NOT
- Do not create a branch.
- Do not edit canonical-architecture.md, LOGIC.md, RULES.md, PROMPTS.md, or IMPLEMENTATION-PLAN.md.
- Do not add runtime code, tooling, or package manifests.
```

---

## Prompt 4 — Normalize terminal-state vocabulary

```
You are working in the Autonomous Coding Agent repo on the current branch. Do not create a new branch.

GOAL
The docs currently use four overlapping vocabularies for terminal states and readiness verdicts (`READY/BLOCKED/UNSUPPORTED`, `COMPLETE/BLOCKED/UNSUPPORTED`, `READY/NOT_READY`, `NEEDS_MORE_EVIDENCE`). That is the false-green pathway. Normalize to the model below and propagate it consistently.

THE NORMALIZATION (this is the decision — you are writing it down)
- `run_state` (what the supervisor concludes about the run overall) ∈ { COMPLETE, BLOCKED, UNSUPPORTED, IN_PROGRESS }.
- `readiness_verdict` (what the final readiness gate emits) ∈ { READY, NOT_READY, NEEDS_MORE_EVIDENCE }.
- `run_state = COMPLETE` is legal ONLY when:
  (a) `readiness_verdict = READY`, AND
  (b) all required artifacts named in the run contract exist, AND
  (c) all authoritative required checks passed on the final rerun, AND
  (d) no unresolved high-severity defect packets are open.
  Any other combination produces `BLOCKED` or `UNSUPPORTED` per existing RULES.md stop conditions.
- `NEEDS_MORE_EVIDENCE` is not terminal. It causes the supervisor to run one more evidence-gathering loop up to the configured bound; after that bound it degrades to `NOT_READY` and the run goes to `BLOCKED`.

REQUIRED READING
Read only the sections of each file that currently use any of the overlapping terms. Search each file for the terms: "READY", "NOT_READY", "COMPLETE", "BLOCKED", "UNSUPPORTED", "NEEDS_MORE_EVIDENCE", "readiness", "terminal state", "run state".
1. canonical-architecture.md — all matches, with surrounding paragraph context.
2. LOGIC.md — all matches.
3. RULES.md — all matches, especially any "Stop Conditions" section.
4. PROMPTS.md — all matches, especially verifier/readiness prompts.
5. IMPLEMENTATION-PLAN.md — all matches.
6. STRUCTURE.md — should not need changes, but verify.
7. schemas/ (if prompt 3 has run) — all enum fields using these terms; remove any `x-pending-normalization` markers.

WHAT TO PRODUCE
Edits only — no new files except possibly an ADR (below). For each file above:
- Replace every occurrence with the normalized vocabulary above.
- Where a paragraph previously conflated `run_state` and `readiness_verdict`, split them into two sentences so the reader sees they are separate concepts.
- In canonical-architecture.md, add (or update if it exists) a section titled "Terminal States and Readiness Verdict" that states the normalization rule verbatim as above. Place it near the existing Phases section. This section becomes the single source of truth; every other doc should point here rather than restate.
- In RULES.md, state the `run_state = COMPLETE` legality rule (a–d above) as an enforceable invariant.

ADR
Create design-history/ADR-0001-terminal-state-normalization.md (create design-history/ if it does not yet exist — if prompt 5 / a later pass has not moved historical docs yet, just create the folder and place this ADR there). ADR structure:
- Context: the prior four-vocabulary drift and the false-green risk.
- Decision: the normalization above.
- Consequences: schemas must use these exact enum values; supervisor tests must assert the legality rule; companion docs reference this ADR instead of redefining the vocabulary.

SCHEMAS
If schemas/ exists from prompt 3, update:
- run-contract.schema.json — no change expected.
- strategy-decision.schema.json — if it has a state-ish field, align.
- readiness-report.schema.json — `verdict` enum = [READY, NOT_READY, NEEDS_MORE_EVIDENCE].
- Add a new top-level field OR separate schema field as needed to carry `run_state` on the supervisor's final summary. If uncertain whether `run_state` belongs on the readiness-report or a separate run-summary object, add it to readiness-report under `run_state` and note the open question in the schema description.
- Remove any `x-pending-normalization: true` markers.

LOGGING
Append to WORK-LOG.md:
  ## 2026-04-14 — Terminal-state vocabulary normalized
  - run_state ∈ {COMPLETE, BLOCKED, UNSUPPORTED, IN_PROGRESS}; readiness_verdict ∈ {READY, NOT_READY, NEEDS_MORE_EVIDENCE}.
  - COMPLETE legality rule codified in RULES.md.
  - ADR-0001 created under design-history/.
  - Files touched: <list>.
  - Schemas updated: <list or "none">.

COMMIT
Single commit:
  git add -A
  git commit -m "docs(states): normalize run_state vs readiness_verdict; add ADR-0001"
  git push

DO NOT
- Do not create a branch.
- Do not invent new terminal states beyond the set above.
- Do not touch lines that don't use the four overlapping terms. Scope is vocabulary-only.
```

---

## Prompt 5 — Self-audit of prompts 1–4

```
You are the AUDITOR for prompts 1–4 that just ran in this repo. You did not do the work; you are verifying it. Be skeptical. Do not fix anything in this pass — produce an audit report only. A separate follow-up pass will do repairs.

GOAL
Produce AUDIT-2026-04-14.md at the repo root containing a red/yellow/green verdict for each of the four changes, plus a consolidated punch list.

REQUIRED READING
1. WORK-LOG.md — the claims the implementer made about what was done.
2. git log for the last 5 commits — what actually landed.
3. The four targets in full:
   a. PROJECT_INTENT.md
   b. STRUCTURE.md (and .gitignore)
   c. schemas/ directory (every .schema.json plus schemas/README.md)
   d. canonical-architecture.md "Terminal States" section, RULES.md COMPLETE legality rule, design-history/ADR-0001-*.md, any schema enums touched.
4. canonical-architecture.md in the sections each change claims to derive from — use this to verify the edits did not invent anything.

AUDIT CHECKS — PROMPT 1 (PROJECT_INTENT)
- No `TODO`, no `verify`, no `<placeholder>`, no empty sections remain.
- Purpose paragraph is grounded in canonical-architecture.md §1 (not invented).
- Non-goals are either lifted from canonical-architecture.md/RULES.md/IMPLEMENTATION-PLAN.md or flagged as open questions. Any silently invented non-goal → RED.
- Success metrics are observable. "Works well" or similar vague metrics → YELLOW.
- "Relationship to other docs" section exists and points at canonical-architecture/RULES/LOGIC/STRUCTURE/GUIDE.
- File is under ~150 lines.

AUDIT CHECKS — PROMPT 2 (STRUCTURE + boundary)
- STRUCTURE.md states the boundary rule in Section 1 before any folder list.
- No sentence anywhere in the repo still says `.agent/` lives in this repo OR `.autoclaw/` lives in a target repo. Search globally.
- `.gitignore` contains `.autoclaw/`, `.claude/`, `worktrees/` at minimum.
- "Where does X go?" decision guide covers at least: schema, fixture, supervisor test, run artifact, policy rule, ADR, prompt template.
- "Changes propagated" appendix lists each cross-doc edit with file:line; spot-check 3 of them — open the file at that line and confirm the edit landed.

AUDIT CHECKS — PROMPT 3 (schemas)
- All five files exist with the exact names specified.
- Each has $schema Draft 2020-12, $id, title, description, type:object, additionalProperties:false at root.
- Each has at least one `examples` entry that is structurally valid against its own schema (mentally validate; do not execute).
- No field exists that cannot be traced to a naming occurrence in canonical-architecture.md, PROMPTS.md, or IMPLEMENTATION-PLAN.md. Grep for each field name; if zero hits outside the schema itself → RED with the field name.
- schemas/README.md exists.
- If prompt 4 has run, no `x-pending-normalization` markers remain.

AUDIT CHECKS — PROMPT 4 (terminal states)
- canonical-architecture.md has exactly one authoritative "Terminal States and Readiness Verdict" section; other docs reference it rather than redefining.
- RULES.md states the COMPLETE legality rule (a–d) verbatim or equivalently.
- Grep every .md file for each of: READY, NOT_READY, COMPLETE, BLOCKED, UNSUPPORTED, NEEDS_MORE_EVIDENCE. Every occurrence must fit the normalized model. Any stray `READY` used as a run_state, or any stray `COMPLETE` used as a readiness verdict → RED with file:line.
- design-history/ADR-0001-terminal-state-normalization.md exists with Context/Decision/Consequences.
- readiness-report.schema.json enum matches {READY, NOT_READY, NEEDS_MORE_EVIDENCE}.

CROSS-CUTTING CHECKS
- No commits on a branch other than the one the user was on. `git log --all --oneline | head -20` should show work on the active branch only.
- Every claim in WORK-LOG.md maps to a real file change in `git log -p`.
- No file outside the allowed scope of its prompt was modified (e.g. Prompt 1 should not have touched RULES.md).

REPORT FORMAT (AUDIT-2026-04-14.md)
Structure:
  # Audit — Phase 0 Cleanup Pass (2026-04-14)
  ## Verdicts
  - Prompt 1 (intent): GREEN | YELLOW | RED — one-sentence reason.
  - Prompt 2 (boundary): ...
  - Prompt 3 (schemas): ...
  - Prompt 4 (states): ...
  - Cross-cutting: ...

  ## Findings
  For each finding: severity (P1/P2/P3), file:line, what is wrong, what the fix is. No prose hand-wringing; one paragraph max per finding.

  ## Punch list (in fix order)
  Numbered list of concrete follow-up edits. This is what a subsequent repair prompt will execute.

  ## Evidence checked
  Bullet list of the grep queries you ran and the commits you inspected, so a human can reproduce.

LOGGING
Append to WORK-LOG.md:
  ## 2026-04-14 — Self-audit of Phase 0 cleanup
  - Report: AUDIT-2026-04-14.md.
  - Overall: <GREEN|YELLOW|RED>.
  - Highest-severity finding: <one line>.

COMMIT
Single commit:
  git add AUDIT-2026-04-14.md WORK-LOG.md
  git commit -m "audit: Phase 0 cleanup pass verification report"
  git push

DO NOT
- Do not fix anything in this pass.
- Do not create a branch.
- Do not edit PROJECT_INTENT.md, STRUCTURE.md, schemas/, canonical-architecture.md, RULES.md, LOGIC.md, PROMPTS.md, IMPLEMENTATION-PLAN.md, or any ADR.
- Do not mark GREEN on any check you only partially verified. If in doubt, YELLOW with a reason.
```

---

## My audit of these prompts (what I just wrote)

Before you hand these to Codex, things to know:

**Strengths.** Each prompt names the exact files to read, which keeps Codex from drifting into the 8,700 lines of repo prose. Scope is bounded per prompt. Logging is consistent (`WORK-LOG.md` every time). No branching. Audit is fully isolated from the work and tests the same specific properties the work was supposed to produce — not generic "is this good?" checks.

**Known risks you should accept or adjust.**

1. Prompts 3 and 4 have an ordering dependency. Prompt 3 handles it with `x-pending-normalization` markers, but if you run prompt 4 *before* prompt 3, the schema coordination section of prompt 4 becomes a no-op. Recommended order: 1 → 2 → 3 → 4 → 5. Don't parallelize.

2. Prompt 2 makes a unilateral boundary decision (target owns `.agent/contract.yml`; control plane owns `schemas/`/`supervisor/`/`fixtures/`/`tests/`; `.autoclaw/` is gitignored on both sides). I proposed this in my last message and you said yes, but Codex will treat it as fixed. If you want it reopened, do it before running prompt 2.

3. Prompt 4's `NEEDS_MORE_EVIDENCE` retry bound is intentionally not specified ("the configured bound"). Codex will leave it abstract. That's correct for Phase 0 — don't let Codex invent a number.

4. Prompt 3 instructs Codex to flag missing fields as open questions rather than invent them. This will likely produce several open questions per schema. That's the right outcome; don't treat it as incomplete work.

5. The audit prompt (5) will run grep-style checks mentally. For the stray-terminal-state check especially, Codex may miss occurrences inside code blocks or prose quotes. If prompt 5 comes back GREEN, still spot-check that specific grep yourself.

Prompts file saved here:

[View the prompts](computer:///sessions/blissful-elegant-sagan/mnt/Autonomous Coding Agent/codex-cleanup-prompts.md)
> Historical archive note: this prompt batch records the instructions that drove the initial Phase 0 cleanup work. Paths and expectations inside it reflect that point in time and are not current source-of-truth guidance.
