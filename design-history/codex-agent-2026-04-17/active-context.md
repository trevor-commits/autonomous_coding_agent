# Active Context

## Current Decisions

- Treat the project as an automation harness first, with API-routing as a
  supporting concern.
- Keep the orchestration mode `solo` until the first real Phase 3 slice proves
  there is a useful non-blocking delegation opportunity.
- The `Optimal` route is approved.
- `bible-ai` is the first implementation repo for the truthful Phase 0 path.
- The next bounded execution path is: finish the remaining repo-local
  lifecycle and Phase 0 control items, then use the proven `bible-ai` baseline
  to unlock the first truthful Phase 3 slice instead of repeating onboarding.

## Open Questions

- Whether `GIL-55` should land before the remaining repo-local Phase 0 docs or
  whether those docs can close in parallel without blurring the next milestone.
- Which of `GIL-23`, `GIL-8`, `GIL-10`, and `GIL-11` are truly blocking
  `GIL-29` versus eligible for explicit defer/resequence.

## Selected Packs

- `memory-bank`
- `responsibility-map`
- `scope-discipline`

## Next Decision Point

No further approval checkpoint is blocking execution. The next decision is
sequencing: `GIL-55`, the remaining repo-local Phase 0 items, and then
`GIL-29` on top of the proven `bible-ai` baseline.
