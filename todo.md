# TODO

## Active Next Steps
Current goal: keep the repo implementation-ready by finishing the remaining Phase 0 work on top of a clean, well-indexed documentation surface.
- [ ] Phase 0A.5: trim the initial implementation surface to a smaller v1 by reducing externally visible action families and collapsing operational memory to a minimal first-pass shape; push the heavier Phase 5 hardening items behind a later v1.1-style threshold.
- [ ] Phase 0.1: write the first target repo's `.agent/contract.yml` using the canonical repo-contract shape and keep the initial scope intentionally narrow.
- [ ] Phase 0.2: manually validate the target repo contract end-to-end on a clean checkout, including setup, test, app launch, and health check.
- [ ] Phase 0.2a: document CI parity for the first implementation repo so GitHub Actions reuses repo-contract commands, fast/unit/smoke gates, and structured artifacts instead of inventing repo behavior in workflow YAML.
- [ ] Phase 0.3: create 3 to 5 benchmark run contracts covering simple fix, scoped feature, and UI-touching work.
- [ ] Phase 0.4: verify local tool readiness for the first implementation pass: Codex CLI auth path works, Claude access path works, Python is ready, and Playwright is installable.
- [ ] Phase 1.1: build the deterministic supervisor foundation before any bounded strategy-layer integration.
- [ ] Phase 1.2: implement contract parsing, run directory creation, shell/path guardrails, and single-writer worktree control.
- [ ] Phase 1.3: implement deterministic verification runners, failure fingerprinting, checkpointing, and final report generation.

## Governance Shortcuts

- New execution-ready work goes in `Active Next Steps`.
- Optional or deferred ideas go in `Suggested Recommendation Log`.
- Audit requests, findings, and dispositions go in `Audit Record Log`.
- User feedback, plan refinements, and accepted or rejected guidance go in `Feedback Decision Log`.
- Concrete repo changes are summarized in `WORK-LOG.md`.

## Completed
Preserve a durable completion trail for verified work instead of deleting it from active planning.
- [x] 2026-04-12: established the documentation baseline for the project, including `canonical-architecture.md` as source of truth, companion docs, README/guide/indexing, and historical-design separation.
- [x] 2026-04-12: added `PROMPTS.md` as the prompt-system source of truth, including prompt-writing rules, build/run prompt libraries, mandatory self-test -> independent review -> fix-audit loops, and explicit testing/audit cadence guidance.
- [x] 2026-04-14: completed Phase 0A.1 through Phase 0A.4 by filling `PROJECT_INTENT.md`, clarifying the repo boundary, adding standalone schemas, normalizing terminal-state vocabulary, and recording a follow-up audit.
- [x] 2026-04-14: reorganized the repo documentation surface by moving historical material under `design-history/`, adding `REPO_MAP.md`, and making navigation plus governance-record locations explicit.
- [x] 2026-04-14: documented the multi-AI repo-audit thread in `design-history/feedback-reconciliation-2026-04-14.md`, including what each AI recommended, which claims were stale vs repo-grounded, the resulting accepted/deferred decisions, and the failure modes to guard against before implementation starts.

## Suggested Recommendation Log
Keep materially new suggestions here so they survive beyond the current chat.
- Do not delete old entries; mark them completed, declined, deferred, or superseded with date and chat context.
- Keep audit-created items here only when they are deferred, optional, or not yet execution-ready; otherwise promote them into `## Active Next Steps`.
- When a suggestion comes from an audit or feedback review, link back to the originating audit record or `Feedback Decision Log` entry and later note which chat implemented or declined it.
- 2026-04-12: Keep `acpx` behind an adapter instead of making it part of the supervisor spine on the first implementation pass. Status: deferred until the builder adapter is being built.
- 2026-04-12: When Phase 4 starts, materialize the canonical prompt pack from `PROMPTS.md` into versioned `supervisor/prompts/` files plus parseable schema fixtures so prompt regressions can be tested directly. Status: deferred until Phase 4.
- 2026-04-12: Add a prompt-regression harness that replays representative planning, build, review, fix-audit, and final-audit cases to catch prompt drift before it reaches real runs. Status: deferred until Phase 4/5.
- 2026-04-14: Implement CI first as a contract-driven validator in the first real implementation repo, with fast/unit/smoke gates and structured artifacts, then extract a reusable template only after that pattern is proven. Status: accepted and promoted into Active Next Steps as Phase 0.2a.
- 2026-04-14: Add GitHub governance hardening only after executable control-plane surfaces exist (`supervisor/`, `schemas/`, tests, workflows). Minimum expected later set: CODEOWNERS for control-plane files, required checks, Dependabot, CodeQL, and secret-scanning hygiene. Status: deferred until after Phase 0A and initial implementation scaffolding.

## Active Branch Ledger
Keep one entry per non-trivial active branch so any chat can see why it exists, which chat opened or resumed it, what work is active, what must happen before merge or closeout, and whether the branch should be deleted or intentionally retained.
Legacy branches opened before this workflow may still need manual backfill; use `TODO: verify` instead of guessing until those entries are added.
Each active branch entry should include:
- `source chat`
- `last refreshed by chat`
- `purpose`
- `merge expectation`
- `exit checklist`
- `delete when` or `retain after close`
- `retain reason` when not deleting

## Branch History
- No closed branch entries recorded yet.

## Audit Record Convention
- Record each audit, ship-check, or substantial verification-driven review in an easy-to-find project audit log entry.
- Each entry should capture:
  - `date`
  - `type` (for example `full audit`, `targeted audit`, `ship-check`, `governance review`)
  - `scope`
  - `repo fingerprint` (branch + commit when available)
  - `prior audit reference`
  - `source/work chat`
  - `audit chat`
  - `implementation chat` or `disposition chat`
  - `separate follow-up audit` (`yes` / `no` plus reason when `no`)
  - `commands / evidence`
  - `tested`
  - `not tested`
  - `findings opened or updated`
  - `fixes closed / verified`
  - `declined / deferred findings`
  - `better-path challenge`
  - `references` (issue, PR, commit, or log path)
- When a finding is later implemented, deferred, declined, or superseded, update the existing audit trail instead of deleting the history.

## Audit Record Log
- 2026-04-12 | type: governance review | scope: companion-doc consistency after canonical architecture adoption | source/work chat: current repo audit thread | commands/evidence: document review only | findings opened or updated: LOGIC terminal-state mismatch, auth prerequisite overspecification, AGENTS global-reference ambiguity, empty active queue, onboarding-order ambiguity
- 2026-04-12 | type: governance review | scope: prompt-system source-of-truth addition and review-loop hardening | source/work chat: current prompt operating system thread | commands/evidence: document review plus cross-doc consistency check | findings opened or updated: prompt-authority gap closed, independent-review loop made explicit, event/time-based testing cadence defined, phase-4 prompt operationalization deferred into follow-up
- 2026-04-14 | type: governance review | scope: CI rollout documentation and plan placement | source/work chat: CI documentation placement thread | commands/evidence: targeted architecture/plan/todo/readme review | findings opened or updated: CI belongs in the first implementation repo, must be contract-driven, must emit structured artifacts, and should only be templated after local parity is proven
- 2026-04-14 | type: full audit reconciliation | scope: repo-state-grounded evaluation of ChatGPT Pro, Claude, Claude Code, Claude Cowork, and Codex feedback on repository readiness | source/work chat: multi-AI repo audit reconciliation thread | commands/evidence: direct review of README, GUIDE, AGENTS, PROJECT_INTENT, canonical architecture, companion docs, implementation plan, and todo log; local file inventory and line-count check | findings opened or updated: empty PROJECT_INTENT template, repo-vs-target-repo boundary ambiguity, terminal-state/readiness vocabulary drift, missing standalone schemas, docs-heavy root clutter, over-ambitious v1 hardening scope | references: `design-history/feedback-reconciliation-2026-04-14.md`
- 2026-04-14 | type: governance review | scope: repo structure cleanup, historical-doc archiving, and navigation/governance-record clarity | source/work chat: current repo organization request | commands/evidence: root file inventory review, cross-reference search, archive move review, README/GUIDE/STRUCTURE/todo consistency pass | findings opened or updated: root clutter reduced, archive boundary made explicit, repo-map gap closed, governance-record locations made discoverable | references: `design-history/AUDIT-2026-04-14.md`, `REPO_MAP.md`
- 2026-04-15 | type: full audit | scope: Claude Cowork (orchestrator) independent audit of all 9 Codex commits since Phase 0A cleanup pass began | audit chat: Claude Cowork | repo fingerprint: main @ 9a9efaa | commands/evidence: `git log --oneline -20`, `git show --stat` per commit, `ls schemas/`, terminal-state grep, `.agent/.autoclaw` boundary grep, direct read of strategy-decision.schema.json, defect-packet.schema.json, REPO_MAP.md, STRUCTURE.md, WORK-LOG.md | findings opened: (P1) strategy-decision.schema.json field inversion — checkpoint_candidate wrongly requires run_state, propose_terminal_state wrongly omits it; (P1) defect-packet.schema.json over-constrains evidence — all three evidence fields required, real defects won't satisfy this; (P1) autobot/ vs autoclaw/ naming split unresolved across git tags and runtime dirs; (P1) REPO_MAP.md uses absolute paths, breaks portability; (P2) AGENTS.md [MANDATORY_*] block unchanged, still references ~/.codex/ paths outside this repo; (P2) companion docs restate terminal-state rule instead of referencing canonical §9.1; (P2) STRUCTURE.md Changes Propagated appendix line numbers drifted post-reorg; (P2) WORK-LOG.md and REPO_MAP.md overlap README/GUIDE/todo, redundancy now exceeds utility; (P3) AUDIT-2026-04-14.md placed in design-history/ while its punch list is still open; governance finding: Codex violated audit-pass read-only constraint by reorganizing in the same commit as the audit, flagged and corrected after Trevor confirmed the reorg was prompted separately | fixes closed/verified: PROJECT_INTENT.md filled, repo boundary clean in active docs, 5 schemas exist and are structurally sound, ADR-0001 landed, design-history/ archive clean, terminal-state vocabulary correct in live docs, .gitignore present | separate follow-up audit: yes — Claude Code ran independently; see next entry | references: `design-history/AUDIT-2026-04-14.md`
- 2026-04-15 | type: full audit | scope: Claude Code independent audit of all 9 Codex commits | audit chat: Claude Code (separate session) | repo fingerprint: main @ 9a9efaa | prior audit reference: Cowork audit above | commands/evidence: direct file reads of all schemas, AGENTS.md, IMPLEMENTATION-PLAN.md, canonical-architecture.md, LOGIC.md, PROMPTS.md, RULES.md, design-history/AUDIT-2026-04-14.md; grep for terminal-state terms and boundary refs; git log inspection | score against prior punch list: 4 fixed, 3 partial, 3 not fixed | findings opened: (P1) strategy-decision.schema.json inversion confirmed with exact line numbers (lines 74-78 vs 113-123); (P1) defect-packet.schema.json evidence over-constraint confirmed — screenshot+console_log+trace all required; (P1) autobot/ vs autoclaw/ split confirmed — git tags use autobot/, runtime dirs use autoclaw/, no explanation; (P1) Codex auth fallback undefined — UNSUPPORTED exit path missing from Phase 0 prerequisites; (P1) AGENTS.md [MANDATORY_*] lines 62-88 unchanged; (P2) REPO_MAP.md + WORK-LOG.md redundancy — three sources now say "what's in the repo", two say "what's been done"; (P2) companion doc restatement of terminal-state rule; (P2) Codex self-audit (commit 21d36d8) identified 5 blockers, then final commit 9a9efaa addressed zero of them — self-audit confirmed unreliable as a gate | governance finding: self-audit should not count as authoritative gate; external actor (Claude) must audit Codex output | fixes closed/verified: aligns with Cowork audit — same 4 items confirmed fixed | separate follow-up audit: yes — merged verdict produced in current chat; repair prompt drafted | references: `design-history/AUDIT-2026-04-14.md`

## Test Evidence Convention
- Testing is required delivery evidence. If a check is skipped, blocked, or only partially run, record the reason and the remaining risk.
- Record each verification run as:
  - `date` (YYYY-MM-DD)
  - `command(s)` executed
  - `result` (pass/fail + short note)
  - `log/PR reference` (commit SHA, CI URL, or local log path)
- When a verification run closes or updates an audit finding, cross-reference the matching audit record entry and the chat or commit that performed the work.

## Test Evidence Log
- 2026-04-12 | command(s): manual document review | result: pass with follow-up fixes required | log/PR reference: local documentation cleanup chat
- 2026-04-12 | command(s): `git diff --check -- PROMPTS.md README.md GUIDE.md IMPLEMENTATION-PLAN.md todo.md`; `rg -n "PROMPTS\\.md|self-test|fix-audit|independent review|re-audit" README.md GUIDE.md IMPLEMENTATION-PLAN.md PROMPTS.md todo.md`; repo-level check discovery for `package.json` / `pnpm-workspace.yaml` | result: pass; cross-doc references and review-loop terms are consistent, and this docs repo does not expose repo-level Node checks to run | log/PR reference: current prompt operating system thread
- 2026-04-14 | command(s): targeted `rg` and `sed` review across `canonical-architecture.md`, `IMPLEMENTATION-PLAN.md`, `README.md`, and `todo.md` for CI/gates/artifact references | result: pass; CI flow is now documented as contract-driven future implementation work rather than immediate generic repo CI | log/PR reference: current CI documentation placement thread
- 2026-04-14 | command(s): `git diff --check -- README.md GUIDE.md todo.md design-history/feedback-reconciliation-2026-04-14.md`; `rg -n "feedback-reconciliation-2026-04-14\\.md|Phase 0A\\.1|Phase 0A\\.2|Phase 0A\\.3|Phase 0A\\.4|Phase 0A\\.5|multi-AI repo audit thread" README.md GUIDE.md todo.md design-history/feedback-reconciliation-2026-04-14.md` | result: pass; new reconciliation document, repo index entries, and audit/todo references are internally consistent | log/PR reference: current documentation and reconciliation thread
- 2026-04-14 | command(s): `find . -maxdepth 2 -type f | sort`; `rg -n "design-history/|REPO_MAP\\.md|Feedback Decision Log|Audit Record Log|Suggested Recommendation Log|WORK-LOG\\.md" README.md GUIDE.md STRUCTURE.md AGENTS.md todo.md REPO_MAP.md design-history/README.md`; `git diff --check` | result: pass; historical docs moved under `design-history/`, navigation docs point to the new layout, and governance-record locations are explicit | log/PR reference: current repo organization thread
- 2026-04-15 | command(s): `git log --oneline -20`; `git show --stat` per commit 26ac6e9 e748ed3 f7c1ef1 af993be 21d36d8 9a9efaa; terminal-state grep across all *.md; `.agent/.autoclaw` boundary grep; direct reads of strategy-decision.schema.json lines 67-141, defect-packet.schema.json evidence block, REPO_MAP.md, STRUCTURE.md, WORK-LOG.md, AGENTS.md lines 60-90 | result: partial pass — 4 items confirmed fixed, 2 schema bugs confirmed (field inversion + evidence over-constraint), 3 P1 items unresolved (autobot/autoclaw split, Codex auth fallback, AGENTS.md markers), REPO_MAP/WORK-LOG redundancy flagged | log/PR reference: Audit Record Log entries 2026-04-15 (both); repair prompt at `codex-repair-prompt.md`

## Testing Cadence Matrix
| Trigger | Command(s) | Cadence | Gate Criteria |
|---|---|---|---|
| Documentation/process change | `git diff --check` plus targeted cross-doc consistency review | Per change | No whitespace/diff hygiene issues and every new source-of-truth doc is linked from the repo guide/index |
| Prompt template / review-loop change | Prompt contract review plus one sample render / schema sanity check for each changed prompt family | Per change | Prompt inputs, outputs, review ownership, and re-audit requirements remain explicit |
| Active implementation work in a target repo | Repo-contract deterministic checks for the touched scope, then full required suite for green candidates | After each milestone, after each fix, and daily on active branches | Failing check reproduced before fix when applicable; required targeted/full suites recorded with evidence |
| Independent review / fix audit loop | Secondary-AI review, then post-fix independent audit | After every green milestone candidate and after every review-driven fix | No unresolved P0/P1 findings; fixes are re-audited until clean |
| Release/readiness review | Full deterministic suite, UI verification when applicable, final independent audit | Pre-release / pre-READY | Acceptance criteria have direct evidence and final audit returns clean or blockers are documented |

## Feedback Decision Log
Record outside feedback and the resulting reasoning once, then update the same entry as the decision evolves.
- Each entry should capture:
  - `date`
  - `feedback source`
  - `feedback summary`
  - `evaluation chat`
  - `reasoning response`
  - `decision status` (`accepted`, `partial`, `deferred`, `rejected`, or `superseded`)
  - `implementation/disposition chat`
  - `linked branch / audit / suggestion / test evidence`
- Reuse or update an existing entry when the same feedback thread comes back instead of opening duplicate records.
- 2026-04-12 | feedback source: Claude companion-doc audit | feedback summary: align terminal-state language, relax Codex auth prerequisite, disambiguate global policy references, populate `todo.md`, clarify human vs agent doc-reading order | evaluation chat: current documentation cleanup thread | reasoning response: accepted in substance; implemented the four direct fixes and clarified onboarding order without reordering the README's human-oriented reading path | decision status: accepted | implementation/disposition chat: current documentation cleanup thread | linked branch / audit / suggestion / test evidence: Audit Record Log entry 2026-04-12; Test Evidence Log entry 2026-04-12
- 2026-04-12 | feedback source: Trevor prompt-system request | feedback summary: add a canonical prompt document, make testing cadence explicit, require self-review plus another AI review, and re-audit fixes until the work comes back clean | evaluation chat: current prompt operating system thread | reasoning response: accepted; implemented in `PROMPTS.md`, indexed from the repo guide/front page, and reflected in the testing/audit governance records | decision status: accepted | implementation/disposition chat: current prompt operating system thread | linked branch / audit / suggestion / test evidence: Audit Record Log entry 2026-04-12 (prompt-system source-of-truth addition); Test Evidence Log entry 2026-04-12
- 2026-04-14 | feedback source: Trevor CI rollout request | feedback summary: document how CI should fit this repo and ensure it gets implemented at the right time and in the right form | evaluation chat: current CI documentation placement thread | reasoning response: accepted with scope correction; documented CI as a future contract-driven validator for the first implementation repo, not as immediate generic multi-language CI in this docs-only repo | decision status: accepted | implementation/disposition chat: current CI documentation placement thread | linked branch / audit / suggestion / test evidence: Audit Record Log entry 2026-04-14; Test Evidence Log entry 2026-04-14; Active Next Steps Phase 0.2a
- 2026-04-14 | feedback source: multi-AI repo audit thread (ChatGPT Pro, Claude, Claude Code, Claude Cowork, Codex analysis) | feedback summary: external audits converged on schemas, structured runtime state, self-tests, and machine-checkable boundaries as the main missing layer; they diverged on how stale the current architecture still was and on how urgently GitHub governance should be added | evaluation chat: current documentation and reconciliation thread | reasoning response: accepted the repo-grounded implementation priorities (intent doc, schema set, terminal-state normalization, repo-boundary cleanup, smaller v1 scope, early harness tests); corrected stale claims about the current canonical architecture still being manager-centric; deferred most GitHub hardening until executable control-plane surfaces exist | decision status: partial | implementation/disposition chat: current documentation and reconciliation thread | linked branch / audit / suggestion / test evidence: Audit Record Log entry 2026-04-14; `design-history/feedback-reconciliation-2026-04-14.md`
- 2026-04-14 | feedback source: Trevor repo organization request | feedback summary: organize the file structure, keep docs synchronized with the new layout, add a clear navigation document for humans and agents, and make feedback/audit/change-request history easy to find | evaluation chat: current repo organization thread | reasoning response: accepted with one structural simplification; active source-of-truth docs stay at the root, historical material moves under `design-history/`, and governance history remains centralized in `todo.md` plus `WORK-LOG.md` rather than spreading across multiple overlapping log files | decision status: accepted | implementation/disposition chat: current repo organization thread | linked branch / audit / suggestion / test evidence: `REPO_MAP.md`; Audit Record Log entry 2026-04-14; Test Evidence Log entry 2026-04-14
- 2026-04-15 | feedback source: Claude Cowork + Claude Code dual independent audit of Codex Phase 0A cleanup (9 commits through 9a9efaa) | feedback summary: both audits independently confirmed 2 schema bugs (strategy-decision field inversion, defect-packet evidence over-constraint), 3 unresolved P1 items from prior punch list (autobot/autoclaw split, Codex auth fallback, AGENTS.md markers), and 2 redundancy problems (REPO_MAP.md + WORK-LOG.md overlap). Governance finding: Codex self-audit is not a reliable gate — external actor must audit. | evaluation chat: current audit session | reasoning response: accepted all P1 findings from both audits. Accepted Claude Code's call to delete REPO_MAP.md and WORK-LOG.md (merge unique content to GUIDE.md and todo.md first) — redundancy now exceeds navigation utility. Accepted governance rule: self-audit passes are read-only; Codex may not reorganize or add files during an audit commit. Deferred Phase 5 hardening (flaky-test registry, resume, concurrent locks) to v1.1 explicitly. Kept Codex auth as hard dependency with BLOCKED exit — no adapter design in Phase 0. NEEDS_MORE_EVIDENCE trigger logic deferred to Phase 4. ADR-0001 stale-archive banner approach accepted over full rewrite of historical docs. | decision status: accepted | implementation/disposition chat: current audit session | linked branch / audit / suggestion / test evidence: Audit Record Log entries 2026-04-15; Test Evidence Log entry 2026-04-15; repair prompt at `codex-repair-prompt.md`
