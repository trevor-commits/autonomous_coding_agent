# Codex Repair Prompt — Phase 0A Punch List

**Source:** Merged findings from Claude Cowork + Claude Code dual independent audits of commits 26ac6e9–9a9efaa (2026-04-15). All items below are confirmed P1 or accepted P2 by both auditors. Run this as one session; do not create a branch.

---

## Context

The Phase 0A cleanup pass (5 prompts + 1 user-directed reorg commit, 9 total commits) fixed: PROJECT_INTENT.md stub, repo-boundary ambiguity, terminal-state vocabulary drift, missing schemas, and design-history clutter. What remains is a punch list of 7 concrete items. Fix them in this order. Every fix commits separately with a clear scope tag. Do not reorganize anything not named here. Do not run a self-audit commit — the next audit is Claude's job, not Codex's.

---

## Required Reading

Read only these files before beginning work. Do not browse other docs unless a specific fix below names an additional file.

1. `schemas/strategy-decision.schema.json` — full file (it is short, under 200 lines).
2. `schemas/defect-packet.schema.json` — full file.
3. `canonical-architecture.md` — only §5.2 "Typed Action Graph" (search heading), §9 "Phase Machine" (search heading), and the "Terminal States and Readiness Verdict" section added in the prior pass. Do not read other sections.
4. `AGENTS.md` — lines 55–95 only.
5. `IMPLEMENTATION-PLAN.md` — only the Phase 0 prerequisites section (search "Phase 0" and "prerequisites"; read the first match block and its checklist, approximately 30 lines).
6. `RULES.md` — only the stop conditions section (search "UNSUPPORTED"; read the paragraph defining it, approximately 10 lines).
7. `design-history/AUDIT-2026-04-14.md` — the full file (it is the Codex self-audit from the prior pass; you are closing its punch list here).
8. `GUIDE.md` — full file (you will be merging content into it from REPO_MAP.md).
9. `REPO_MAP.md` — full file (you are merging its unique content into GUIDE.md then deleting it).
10. `WORK-LOG.md` — full file (you are merging its unique content into `todo.md` then deleting it).
11. `todo.md` — the "Completed" section and the "Feedback Decision Log" (last 30 lines) only.

---

## Fix 1 — Correct `schemas/strategy-decision.schema.json` field inversion

**Bug:** The `oneOf` block has `checkpoint_candidate` requiring `["action", "run_state", "reason"]` and `propose_terminal_state` requiring only `["action", "reason"]`. Both are backwards.

**Fix:**
- `checkpoint_candidate` must require only `["action", "reason"]`. It does not carry `run_state`.
- `propose_terminal_state` must require `["action", "reason", "run_state"]`. It is the one action that proposes a terminal run state and must name it.
- Update each variant's `description` field inside the `oneOf` block to reference the canonical example in `canonical-architecture.md §5.2` so future readers know the derivation.
- Verify the schema's `examples` array is consistent with the corrected required fields. The example at `propose_terminal_state` already shows `run_state: "BLOCKED"` — confirm it still validates after the fix.

**Commit:**
```
git add schemas/strategy-decision.schema.json
git commit -m "fix(schemas): correct checkpoint_candidate vs propose_terminal_state required fields"
git push
```

---

## Fix 2 — Relax `schemas/defect-packet.schema.json` evidence constraints

**Bug:** The `evidence` object requires all three of `screenshot`, `console_log`, and `trace`. Real defects (network errors, console-only failures, test timeouts, build failures) will not have all three. A validator built against this schema will reject every legitimate defect packet that lacks one evidence type.

**Fix:**
- Make `screenshot`, `console_log`, and `trace` all optional (remove them from the `required` array inside `evidence`).
- Add a constraint that at least one of the three must be present. Use one of:
  - `minProperties: 1` on the `evidence` object if all three are the only defined properties, OR
  - An `anyOf` at the `evidence` level requiring at least one non-null entry.
- Update the schema `description` to explain the "at least one evidence field required" rule.
- Update the `examples` array so at least one example shows a minimal defect packet with only `console_log` present, and one shows a full defect with all three.

**Commit:**
```
git add schemas/defect-packet.schema.json
git commit -m "fix(schemas): make defect evidence fields optional with at-least-one constraint"
git push
```

---

## Fix 3 — Resolve `autobot/` vs `autoclaw/` naming split

**Bug:** Git checkpoint tags use the prefix `autobot/<run-id>/...`; runtime directories use `.autoclaw/runs/...`; commit messages, STRUCTURE.md, and IMPLEMENTATION-PLAN.md use `autoclaw`. No file explains the split or makes a decision.

**Decision:** `autoclaw` is the canonical prefix everywhere. Git tags, runtime dirs, commit message scopes, and all prose use `autoclaw`. `autobot` is retired.

**Fix:**
- Search `canonical-architecture.md`, `RULES.md`, `STRUCTURE.md`, `IMPLEMENTATION-PLAN.md`, and `design-history/ADR-0001-terminal-state-normalization.md` for `autobot`. Replace every occurrence with `autoclaw`.
- Search the same files plus `LOGIC.md` and `PROMPTS.md` for the git-tag format `autobot/<run-id>/...` and replace with `autoclaw/<run-id>/...`.
- In `design-history/ADR-0001-terminal-state-normalization.md`, add a one-paragraph appendix titled "Naming convention" that records this decision: `autoclaw` is the canonical system prefix for all runtime directories, git tags, and tool identifiers; `autobot` was the prior working name and is now retired.
- Do not create a separate ADR for this — the ADR-0001 appendix is sufficient.

**Commit:**
```
git add canonical-architecture.md RULES.md STRUCTURE.md IMPLEMENTATION-PLAN.md LOGIC.md PROMPTS.md design-history/ADR-0001-terminal-state-normalization.md
git commit -m "fix(naming): retire autobot/ prefix; autoclaw is canonical everywhere"
git push
```

---

## Fix 4 — Add Codex-unavailable `UNSUPPORTED` exit to Phase 0 prerequisites

**Bug:** `IMPLEMENTATION-PLAN.md` Phase 0 prerequisites treat Codex CLI availability as a given with no documented behavior when it is absent.

**Decision:** Codex CLI is a hard runtime dependency for v1. If `codex --version` fails at Phase 0 entry, the supervisor exits with `run_state = UNSUPPORTED`. The `acpx` adapter path referenced in canonical-architecture.md §21 is explicitly deferred to v1.1.

**Fix:**
- In `IMPLEMENTATION-PLAN.md`, locate the Phase 0 prerequisites checklist. Add one checklist item: `[ ] Codex CLI responds to codex --version; if absent, Phase 0 exits with run_state = UNSUPPORTED (acpx adapter deferred to v1.1)`.
- Add one sentence after it explaining the rationale: the supervisor cannot delegate builder tasks without a working Codex CLI; an adapter layer is a planned extension, not a v1 requirement.
- In `RULES.md`, locate the `UNSUPPORTED` stop condition definition. Add a sentence: "Codex CLI unavailable at Phase 0 entry is a canonical UNSUPPORTED trigger."
- Do not touch any other Phase 0 content.

**Commit:**
```
git add IMPLEMENTATION-PLAN.md RULES.md
git commit -m "docs(phase0): document Codex CLI as hard dependency with UNSUPPORTED exit"
git push
```

---

## Fix 5 — Strip `[MANDATORY_*]` markers from `AGENTS.md`

**Bug:** `AGENTS.md` lines 62–88 contain a `[MANDATORY_*]` policy block that references `~/.codex/` files not present in this repo. Any fresh agent session reading AGENTS.md will treat these as authoritative instructions and look for files that do not exist.

**Fix:**
- Read lines 62–88 of AGENTS.md carefully. For each `[MANDATORY_*]` marker:
  - If the policy it references is already stated explicitly elsewhere in this repo (in RULES.md, LOGIC.md, canonical-architecture.md, or the body of AGENTS.md itself), delete the marker and add a prose cross-reference to the location where the rule actually lives.
  - If the policy is not stated anywhere in this repo, inline a one-sentence summary of the rule into the AGENTS.md body text (no marker syntax) and note it is a local repo rule.
  - If the marker references a capability or file path that is purely external to this repo (`~/.codex/`, global Codex settings, etc.) and has no analog inside this repo, delete the marker entirely without replacement.
- After the edit, verify no line in AGENTS.md references a path outside this repo or a file not present in this repo.

**Commit:**
```
git add AGENTS.md
git commit -m "fix(agents): replace [MANDATORY_*] markers with inline rules or cross-references"
git push
```

---

## Fix 6 — Merge and delete `REPO_MAP.md` and `WORK-LOG.md`

**Why:** Both files were added in the repo reorganization pass. Both overlap existing docs: `REPO_MAP.md` duplicates GUIDE.md's navigation purpose; `WORK-LOG.md` duplicates todo.md's Completed and governance trail. Three sources now tell readers "what's in the repo" and two tell them "what's been done." The redundancy exceeds the utility.

**Fix — REPO_MAP.md:**
- Read `REPO_MAP.md` in full.
- Read `GUIDE.md` in full.
- Identify any content in REPO_MAP.md that is NOT already present in GUIDE.md. Specifically look for: the "Where does X go?" decision table, the governance record location list (Audit/Feedback/Test logs), and the "Active Source of Truth" file listing.
- Merge the unique content into GUIDE.md. Place navigation/lookup content in a section titled "Quick Reference — Where to Find Things" near the top of GUIDE.md (after the intro, before the reading order). Preserve the governance record location list as a brief paragraph.
- After merging, delete `REPO_MAP.md`.
- Update any references to `REPO_MAP.md` in `README.md`, `AGENTS.md`, `STRUCTURE.md`, `todo.md`, and `design-history/README.md`. Replace each with a reference to the appropriate GUIDE.md section.

**Fix — WORK-LOG.md:**
- Read `WORK-LOG.md` in full.
- Read the "Completed" section and the "Feedback Decision Log" tail of `todo.md`.
- For each dated entry in WORK-LOG.md: if a corresponding entry already exists in todo.md Completed (same date, same scope), it is a duplicate — skip it. If no corresponding entry exists, append it to todo.md Completed with the same date and a note "from WORK-LOG.md".
- After merging, delete `WORK-LOG.md`.
- Update any references to `WORK-LOG.md` in README.md, AGENTS.md, STRUCTURE.md, GUIDE.md, and todo.md's Governance Shortcuts section. Replace with a reference to `todo.md` Completed.

**Commit:**
```
git add -A
git commit -m "docs(cleanup): merge REPO_MAP into GUIDE.md; merge WORK-LOG into todo.md; delete both"
git push
```

---

## Fix 7 — Address remaining findings from `design-history/AUDIT-2026-04-14.md`

The Codex self-audit identified 5 findings. The reorg commit (9a9efaa) addressed zero of them. Address all five now.

**Required reading for this fix only:** `design-history/AUDIT-2026-04-14.md` punch list (lines 23–29).

**Finding 1 (P1): Historical docs carry stale terminal-state vocabulary.**
Files: `design-history/FINAL-ARCHITECTURE-DECISION.md` and `design-history/three-way-reconciliation-final.md`.
Fix: Add a banner comment at the top of each file:
```
> **ARCHIVED — superseded.** This document predates terminal-state normalization (ADR-0001). Vocabulary such as `READY/NOT_READY/BLOCKED` used as `run_state`, and `.autoclaw/` boundary references, reflect the prior design. See `canonical-architecture.md §9.1 "Terminal States and Readiness Verdict"` and `STRUCTURE.md §1` for current truth.
```
Do not rewrite any content inside these files.

**Finding 2 (P1): Historical docs carry stale boundary language.**
Same files. The banner above covers this. Confirm the banner is present on both files.

**Finding 3 (P1): `strategy-decision.schema.json` field inversion.**
Fixed in Fix 1 above. Mark as resolved.

**Finding 4 (P2): `STRUCTURE.md` Changes Propagated appendix has drifted line numbers.**
Fix: Rewrite the "Changes Propagated" appendix to reference file and section heading instead of absolute line numbers. Format: `RULES.md — "Stop Conditions" section: aligned UNSUPPORTED definition`. Do not guess or recheck all lines; use heading-level references throughout.

**Finding 5 (P2): Companion docs restate terminal-state rule instead of pointing at canonical §9.1.**
Files: `LOGIC.md` (line 10 paragraph), `PROMPTS.md` (readiness verdict prompt block), `IMPLEMENTATION-PLAN.md` (Phase 4 final-audit step).
Fix for each: Replace the paragraph that restates the normalized rule with a one-sentence reference: "For the canonical `run_state` and `readiness_verdict` vocabulary and legality rules, see `canonical-architecture.md §9.1 "Terminal States and Readiness Verdict"`." Keep any locally enforcement-specific text (e.g. RULES.md's COMPLETE legality checklist stays as written — it is an invariant, not a restatement).

**Commit:**
```
git add design-history/FINAL-ARCHITECTURE-DECISION.md design-history/three-way-reconciliation-final.md STRUCTURE.md LOGIC.md PROMPTS.md IMPLEMENTATION-PLAN.md
git commit -m "docs(audit): close AUDIT-2026-04-14 punch list — banners, heading refs, companion-doc references"
git push
```

---

## Logging

After all 7 fixes are committed, append one entry to `todo.md` Completed:

```
- [x] 2026-04-15: closed Phase 0A punch list — schema field inversion, defect evidence constraints, autobot/autoclaw naming, Codex auth UNSUPPORTED exit, AGENTS.md markers, REPO_MAP/WORK-LOG merge-and-delete, AUDIT-2026-04-14 findings. Commits: <list SHAs>.
```

And append one entry to `todo.md` Test Evidence Log:

```
- 2026-04-15 | command(s):
  (1) grep -r autobot . --include="*.md" --include="*.json" --include="*.yml" (must return zero hits outside design-history/);
  (2) grep -rn "MANDATORY_" AGENTS.md (must return zero hits);
  (3) pip install jsonschema --quiet && python3 -c "
import json, jsonschema
for name in ['strategy-decision','defect-packet','readiness-report','failure-fingerprint','run-contract']:
    s = json.load(open(f'schemas/{name}.schema.json'))
    for ex in s.get('examples', []):
        jsonschema.validate(ex, s)
        print(f'PASS: {name} example valid')
" (all examples must pass; any ValidationError is a failure);
  (4) grep -n "REPO_MAP" README.md AGENTS.md STRUCTURE.md GUIDE.md (must return zero hits);
  (5) grep -n "WORK-LOG" README.md AGENTS.md STRUCTURE.md GUIDE.md (must return zero hits)
  | result: <pass/fail per command> | log/PR reference: <commit SHAs>
```

**Commit the log entries:**
```
git add todo.md
git commit -m "docs(log): record Phase 0A punch list completion in todo.md"
git push
```

---

## Constraints

- Do not create a branch. All work on the current branch.
- Do not add any new documents. Every change is a fix or a consolidation.
- Do not re-open settled architecture decisions in `canonical-architecture.md §2–8`.
- Do not run a self-audit commit. The next audit is Claude's job.
- Do not reorganize any files or folders not named in this prompt.
- Do not touch Phase 5 scope items — they are deferred to v1.1 and documented in `todo.md`.
- Scope of each commit must match exactly the files named in its fix block. If a file not named here requires a change, stop and note it in the commit message as "noted but out of scope" rather than touching it silently.
