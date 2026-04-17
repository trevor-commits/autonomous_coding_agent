# Implementation Plan

## Summary

The route is now approved and anchored to a real target repo: finish the
repo-local unblockers, onboard `bible-ai` as the first implementation repo, and
unlock the first truthful Phase 3 slice instead of expanding generic autonomy.

## Project DNA

- Product character: strict, operator-facing, evidence-first
- Uniqueness axis: runtime-owned correctness instead of AI-owned workflow
  theater
- Trust signal: one writer, bounded queue legality, deterministic verification,
  and repo-visible closeout
- Anti-template rule: do not pretend this is a generic AI swarm, generic
  dashboard, or broad platform before one real repo is proven

## Selected Plan Variant

- `Optimal` (approved)
- Why: it keeps the scope honest. It does not jump to Phase 4/5, and it no
  longer hides behind internal prep because the first target repo is now named:
  `bible-ai`.

## What Belongs in v1

- Local `.codex-agent` state and bounded approval path for this repo
- Branch/Linear lifecycle reset (`GIL-55`) so future execution uses the right
  branch discipline again
- First implementation repo selection plus Phase 0 contract/manual baseline
- One bounded Phase 3 app-launch and Playwright verification slice on a real repo
- Durable evidence in repo docs and Linear throughout the flow

## First-Version Limit

- `deliverable 1`: truthful autopilot state and approval checkpoint in this repo
- `deliverable 2`: repo-local lifecycle/governance unblocker (`GIL-55`)
- `deliverable 3`: `bible-ai` onboarded as the first real target repo and its
  Phase 0 baseline completed
- `deliverable 4`: one bounded Phase 3 verification slice proven against that repo

## What Stays Out

- Phase 4 bounded Claude strategy
- Phase 5 operational memory/resume hardening
- multi-writer execution
- auto-merge, auto-deploy, or generic hosted control plane scope

## Later Recommendations

- After the first real repo proof: webhook-first queue wakeups, deeper eval
  coverage, and only then bounded Claude strategy.

## Archetype and Playbook

- `automation-script`
- Supporting archetype: `api-integration-worker`
- Playbooks: `automation-script.md` + `api-integration-worker.md`

## Stack

- Python 3.10+ deterministic supervisor
- Codex CLI as sole writer
- Claude audit path plus Trevor verify
- Linear for routing/queue metadata
- Playwright for target-repo UI verification
- Repo docs and local run artifacts as the durable truth surfaces

## Safe Defaults

- Secrets live only in env or provider panels.
- Do not add broad product-user data storage to this repo without a real use case.
- Keep operator/service access separate and keep privileged tokens out of logs,
  code, and client surfaces.
- Before handoff, run a dependency/security check and explicitly note any
  skipped verification.

## Stages

1. Freeze the approved plan in `.codex-agent`, with `Optimal` locked and
   `bible-ai` named as the first implementation repo.
2. Land the repo-local lifecycle/governance unblocker without widening scope.
3. Complete the truthful Phase 0 baseline in `bible-ai`.
4. Return to this repo's next real milestone: one Phase 3 app-launch/UI
   verification slice backed by artifacts.

## Acceptance Criteria

- The approved plan names `bible-ai` as the first implementation repo and does
  not blur repo-local work with target-repo work.
- `.codex-agent` artifacts agree on the same goal, open question, and
  approved variant.
- The plan explicitly names what is deferred instead of implying "later magic."
- The next execution step is blocked only by real implementation work, not by a
  missing operator decision.

## Anti-Template Check

- This plan fits because the repo already has meaningful control-plane work; the
  missing truth is target-repo proof, not more generic architecture words.
- We explicitly avoided default SaaS/UI assumptions, generic AI-manager scope,
  and premature Phase 4/5 expansion.

## Known Risks

- If `GIL-55` stays open, future execution could keep drifting away from the
  restored branch/Linear lifecycle policy.
- If `bible-ai` onboarding stalls after approval, the project can still drift
  back into repo-local polish without proving the end-to-end harness.
- If the plan jumps into broader autonomy before one real repo succeeds, the
  repo may accumulate more control-plane scope than trustworthy proof.

## Remaining Manual Inputs

- No further approval input is required for this checkpoint.
- If execution hits an environment-specific blocker in `bible-ai`, the next
  manual input is the correct checkout/branch or any missing local access
  details.
