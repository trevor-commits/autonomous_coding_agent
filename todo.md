# TODO

## Active Next Steps
Current goal: turn the settled architecture into a working deterministic supervisor foundation without reopening the core design.
- [ ] Phase 0.1: write the first target repo's `.agent/contract.yml` using the canonical repo-contract shape and keep the initial scope intentionally narrow.
- [ ] Phase 0.2: manually validate the target repo contract end-to-end on a clean checkout, including setup, test, app launch, and health check.
- [ ] Phase 0.3: create 3 to 5 benchmark run contracts covering simple fix, scoped feature, and UI-touching work.
- [ ] Phase 0.4: verify local tool readiness for the first implementation pass: Codex CLI auth path works, Claude access path works, Python is ready, and Playwright is installable.
- [ ] Phase 1.1: build the deterministic supervisor foundation before any bounded strategy-layer integration.
- [ ] Phase 1.2: implement contract parsing, run directory creation, shell/path guardrails, and single-writer worktree control.
- [ ] Phase 1.3: implement deterministic verification runners, failure fingerprinting, checkpointing, and final report generation.

## Completed
Preserve a durable completion trail for verified work instead of deleting it from active planning.
- [x] 2026-04-12: established the documentation baseline for the project, including `canonical-architecture.md` as source of truth, companion docs, README/guide/indexing, and historical-design separation.
- [x] 2026-04-12: added `PROMPTS.md` as the prompt-system source of truth, including prompt-writing rules, build/run prompt libraries, mandatory self-test -> independent review -> fix-audit loops, and explicit testing/audit cadence guidance.

## Suggested Recommendation Log
Keep materially new suggestions here so they survive beyond the current chat.
- Do not delete old entries; mark them completed, declined, deferred, or superseded with date and chat context.
- Keep audit-created items here only when they are deferred, optional, or not yet execution-ready; otherwise promote them into `## Active Next Steps`.
- When a suggestion comes from an audit or feedback review, link back to the originating audit record or `Feedback Decision Log` entry and later note which chat implemented or declined it.
- 2026-04-12: Keep `acpx` behind an adapter instead of making it part of the supervisor spine on the first implementation pass. Status: deferred until the builder adapter is being built.
- 2026-04-12: When Phase 4 starts, materialize the canonical prompt pack from `PROMPTS.md` into versioned `supervisor/prompts/` files plus parseable schema fixtures so prompt regressions can be tested directly. Status: deferred until Phase 4.
- 2026-04-12: Add a prompt-regression harness that replays representative planning, build, review, fix-audit, and final-audit cases to catch prompt drift before it reaches real runs. Status: deferred until Phase 4/5.

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
