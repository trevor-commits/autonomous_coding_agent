# Launch Plan

**Date:** April 15, 2026
**Purpose:** Reconcile what launch-related pieces already exist in this repository versus what is still future implementation work.

This repository is still docs-first. It does not yet ship a runnable supervisor, deployment pipeline, or production service. That distinction matters because some launch-related work is already implemented as documentation and operator process, while other pieces are only planned.

## Current Status

| Item | Status | Evidence | Notes |
|---|---|---|---|
| Rollout runbook | Implemented | `LINEAR-BOOTSTRAP.md` §3 `Linear-UI setup runbook` | This is a real operator runbook for rolling out the Linear workflow in practice. |
| Smoke lane | Implemented at the plan/spec level | `IMPLEMENTATION-PLAN.md` §0.2.1 `Define CI Parity Before CI Exists`; `canonical-architecture.md` CI gates and `commands.ui_smoke` references | The smoke lane is already defined as part of the contract-driven validation model. It is not yet executed in this repo because this repo is not the implementation repo. |
| Production rollout lane | Not implemented in this repo | No runnable deployment lane exists in the active repo tree | This remains future work for the first real implementation repo, not this docs-only source-of-truth repo. |
| Post-launch monitoring | Not implemented | No active monitoring workflow, alerting path, or operations dashboard is defined in active docs as a landed process | Monitoring should be added only when a production runtime exists to monitor. |

## Reconciliation Rule

Do not collapse all launch-adjacent work into a single `Not implemented yet` bucket.

- If a runbook, gate, or lane already exists as an active documented workflow, mark it as implemented at the documentation/process level.
- If the repo does not yet contain runnable automation or production infrastructure for that lane, say that explicitly instead of implying the doc or process is absent.
- Reserve `Not implemented` for capabilities that are neither landed as process nor present as executable system behavior.

## Scope Boundary

This file describes the current state of launch planning in the source-of-truth repository only.

- It does not claim that a production deployment system already exists.
- It does claim that rollout guidance and a smoke-lane definition already exist and should not be described as missing.
