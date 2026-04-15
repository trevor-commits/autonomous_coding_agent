# TODO

## Active Next Steps
Current goal: turn the settled architecture into a machine-checkable Phase 0 starting point without reopening the core design.
- [ ] Phase 0A.1: fill `PROJECT_INTENT.md` from the already-settled purpose and problem framing in `canonical-architecture.md`, then align README/GUIDE references so the repo has one real canonical intent document instead of a `TODO: verify` template.
- [ ] Phase 0A.2: normalize repo-boundary documentation so this repo clearly owns supervisor code, schemas, prompts, and tests, while target repos own their own `.agent/contract.yml`; remove or rewrite any doc wording that currently makes `.agent/` or `.autoclaw/` ownership ambiguous.
- [ ] Phase 0A.3: define standalone machine-facing schemas before implementation depends on them: `run-contract`, `strategy-decision`, `failure-fingerprint`, `defect-packet`, and `readiness-report`.
- [ ] Phase 0A.4: normalize terminal-state and readiness vocabulary across canonical and companion docs so `COMPLETE`, `BLOCKED`, `UNSUPPORTED`, `READY`, `NOT_READY`, and `NEEDS_MORE_EVIDENCE` have one legal meaning each.
- [ ] Phase 0A.5: trim the initial implementation surface to a smaller v1 by reducing externally visible action families and collapsing operational memory to a minimal first-pass shape; push the heavier Phase 5 hardening items behind a later v1.1-style threshold.
- [ ] Phase 0.1: write the first target repo's `.agent/contract.yml` using the canonical repo-contract shape and keep the initial scope intentionally narrow.
- [ ] Phase 0.2: manually validate the target repo contract end-to-end on a clean checkout, including setup, test, app launch, and health check.
- [ ] Phase 0.2a: document CI parity for the first implementation repo so GitHub Actions reuses repo-contract commands, fast/unit/smoke gates, and structured artifacts instead of inventing repo behavior in workflow YAML.
- [ ] Phase 0.3: create 3 to 5 benchmark run contracts covering simple fix, scoped feature, and UI-touching work.
- [ ] Phase 0.4: verify local tool readiness for the first implementation pass: Codex CLI auth path works, Claude access path works, Python is ready, and Playwright is installable.
- [ ] Phase 1.1: build the deterministic supervisor foundation before any bounded strategy-layer integration.
- [ ] Phase 1.2: implement contract parsing, run directory creation, shell/path guardrails, and single-writer worktree control.
- [ ] Phase 1.3: implement deterministic verification runners, failure fingerprinting, checkpointing, and final report generation.

## Completed
Preserve a durable completion trail for verified work instead of deleting it from active planning.
- [x] 2026-04-12: established the documentation baseline for the project, including `canonical-architecture.md` as source of truth, companion docs, README/guide/indexing, and historical-design separation.
- [x] 2026-04-12: added `PROMPTS.md` as the prompt-system source of truth, including prompt-writing rules, build/run prompt libraries, mandatory self-test -> independent review -> fix-audit loops, and explicit testing/audit cadence guidance.
- [x] 2026-04-14: documented the multi-AI repo-audit thread in `feedback-reconciliation-2026-04-14.md`, including what each AI recommended, which claims were stale vs repo-grounded, the resulting accepted/deferred decisions, and the failure modes to guard against before implementation starts.

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
- 2026-04-14 | type: full audit reconciliation | scope: repo-state-grounded evaluation of ChatGPT Pro, Claude, Claude Code, Claude Cowork, and Codex feedback on repository readiness | source/work chat: multi-AI repo audit reconciliation thread | commands/evidence: direct review of README, GUIDE, AGENTS, PROJECT_INTENT, canonical architecture, companion docs, implementation plan, and todo log; local file inventory and line-count check | findings opened or updated: empty PROJECT_INTENT template, repo-vs-target-repo boundary ambiguity, terminal-state/readiness vocabulary drift, missing standalone schemas, docs-heavy root clutter, over-ambitious v1 hardening scope | references: `feedback-reconciliation-2026-04-14.md`

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
- 2026-04-14 | command(s): `git diff --check -- README.md GUIDE.md todo.md feedback-reconciliation-2026-04-14.md`; `rg -n "feedback-reconciliation-2026-04-14\\.md|Phase 0A\\.1|Phase 0A\\.2|Phase 0A\\.3|Phase 0A\\.4|Phase 0A\\.5|multi-AI repo audit thread" README.md GUIDE.md todo.md feedback-reconciliation-2026-04-14.md` | result: pass; new reconciliation document, repo index entries, and audit/todo references are internally consistent | log/PR reference: current documentation and reconciliation thread

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
- 2026-04-14 | feedback source: multi-AI repo audit thread (ChatGPT Pro, Claude, Claude Code, Claude Cowork, Codex analysis) | feedback summary: external audits converged on schemas, structured runtime state, self-tests, and machine-checkable boundaries as the main missing layer; they diverged on how stale the current architecture still was and on how urgently GitHub governance should be added | evaluation chat: current documentation and reconciliation thread | reasoning response: accepted the repo-grounded implementation priorities (intent doc, schema set, terminal-state normalization, repo-boundary cleanup, smaller v1 scope, early harness tests); corrected stale claims about the current canonical architecture still being manager-centric; deferred most GitHub hardening until executable control-plane surfaces exist | decision status: partial | implementation/disposition chat: current documentation and reconciliation thread | linked branch / audit / suggestion / test evidence: Audit Record Log entry 2026-04-14; `feedback-reconciliation-2026-04-14.md`
