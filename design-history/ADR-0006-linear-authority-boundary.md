# ADR-0006: Linear Authority Boundary Confirmed

## Context

On 2026-04-15, during Linear workspace setup, the question was raised whether Linear should hold more authority — specifically whether acceptance criteria, ADRs, audit conclusions, completion logs, or cadence schedules should migrate from the repo into Linear. A four-way audit was run: Claude (Cowork orchestrator), Codex, Claude Code, and ChatGPT Pro each answered independently.

## Decision

Linear's scope remains exactly as defined in `LINEAR.md` — operator routing only. The repo remains authoritative for all knowledge content. No authority migrates to Linear. Two narrow, non-duplicative expansions are sanctioned: Projects as grouping containers when an initiative spans ~5+ related issues, with concrete current candidates being the Codex conversation lifecycle work governed by ADR-0005 and the Phase 0A punch list; and recurring issues mirroring the repo cadence doc, as already permitted by `LINEAR.md` under `Recurring Audits`. A new deferred-capability entry is added: a Current executor custom field, separate from Assignee, to be revisited if it becomes hard to tell at a glance whose turn it is on an issue.

All four auditors converged on the same boundary. Repo-as-truth supports AI workers reading files directly without API roundtrips on every run. ADRs, contracts, and acceptance criteria need git's atomic diffs, PR review, and locality with code. Done is a manual gate after AI Audit and Human Verify; Linear PR-merge automation would silently bypass that gate. Solo-operator plus AI-heavy flow means Linear's team-collaboration strengths are not yet load-bearing. Vendor-neutrality also matters: a Linear outage or pricing change should never be an existential event for the project.

## Consequences

`LINEAR.md` gains an Expansion Discipline subsection citing this ADR. The Projects entry under Hierarchy features is updated to name the ADR-0005 work and Phase 0A as concrete current candidates. A new Custom fields subsection is added to Deferred Capabilities containing the Current executor field.

Deferred capabilities are adopted reactively when their stated trigger fires. The Deferred Capabilities list in `LINEAR.md` should shrink over time as triggers fire, not grow speculatively.
