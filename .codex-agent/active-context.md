# Active Context

## Current Decisions

- Treat the project as an automation harness first, with API-routing as a
  supporting concern.
- Keep the orchestration mode `solo` until the first target repo is chosen and
  the critical path is no longer blocked by one operator decision.
- The `Optimal` route is approved.
- `bible-ai` is the first implementation repo for the truthful Phase 0 path.
- The next bounded execution path is: close the repo-local unblockers, then
  write and validate the first `bible-ai` repo contract instead of staying in
  endless internal prep.

## Open Questions

- Which `bible-ai` checkout and branch should host the first contract and
  manual-baseline pass when execution begins.
- Whether `GIL-55` should land immediately before the `bible-ai` contract slice
  or in parallel as the next repo-local unblocker.

## Selected Packs

- `memory-bank`
- `responsibility-map`
- `scope-discipline`

## Next Decision Point

No further approval checkpoint is blocking execution. The next decision is
sequencing: `GIL-55` first or the first `bible-ai` Phase 0 slice first.
