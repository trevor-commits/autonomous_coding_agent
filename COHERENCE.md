# Coherence

**Date:** April 16, 2026  
**Authority:** Repo governance derived from `AGENTS.md`, `RULES.md`, and `LINEAR.md`.  
**Purpose:** Define the coherence principle for this repository so live docs stay synchronized and the repo remains authoritative instead of drifting into contradiction.

## Principle

"When anything changes, everything it affects must change with it, in the same commit." This repo is a cross-linked system, not a pile of independent notes. Drift kills its authority because every reader then has to guess which document is still right.

## The Ripple Check

Run this pre-commit reflex on every governance change:

1. Identify every section you changed.
2. For each changed section, consult the Dependency Map for every known referencing doc.
3. Read each referencing doc and confirm it still matches.
4. Update any doc that drifted, in the same commit.
5. In the Self-audit, list each ripple check you performed and the method you used to verify consistency.

If a dependency is known and the companion doc was not checked, the commit is not coherent yet.

## Dependency Map

This map is append-only. Every future commit that adds a new inter-doc reference also adds a row here in the same commit.

| Changed surface | Dependent docs to check in the same commit | Why the ripple exists |
|---|---|---|
| `CLAUDE.md` `## Roles` | `AGENTS.md` `## Completion Authority`; `LINEAR.md` state descriptions; `IMPLEMENTATION-PLAN.md` `Who Does What`; `todo.md` `## Audit Watermarks` | Role boundaries and audit ownership must stay aligned across orchestrator, auditor, and completion surfaces. |
| `CLAUDE.md` `## Default Audit Chain` | `AGENTS.md` audit-chain language; `LINEAR.md` state flow | Review order and state meaning drift together if only one surface changes. |
| `canonical-architecture.md` any governing section | `LOGIC.md`; `RULES.md`; `STRUCTURE.md`; `PROJECT_INTENT.md` | Canonical architecture is authoritative, so companion docs must point back to it instead of redefining it. |
| `PROMPTS.md` header shape | `CLAUDE.md` `## Codex Handoff`; `AGENTS.md` `## Prompt And Commit Discipline` | Prompt framing rules are load-bearing only if the handoff and enforcement docs match the same shape. |
| `todo.md` log shapes | `AGENTS.md` `## Reading Scope`; `CONTINUITY.md` `## Work Record format`; `LINEAR.md` state-move preconditions | Durable record requirements, landing-step scope, and Linear coverage must all speak the same log language. |
| `LINEAR.md` state flow | `CLAUDE.md`; `AGENTS.md`; `IMPLEMENTATION-PLAN.md` exit criteria | Linear status meanings are only trustworthy when the surrounding workflow docs agree. |
| `CONTINUITY.md` | `AGENTS.md` `## Completion Authority` Continuity Check; `CLAUDE.md` top-of-file loading instruction; `PROMPTS.md` five-part header; `RULES.md` `R-CONT-*` | The continuity principle must be loaded, enforced, and named consistently at intake, execution, and audit time. |
| `COHERENCE.md` | `AGENTS.md` `## Completion Authority` Ripple Check; `CLAUDE.md` top-of-file loading instruction; `PROMPTS.md` `Durable record`; `RULES.md` `R-COH-*` | The Ripple Check is real only if the intake docs, prompt contract, and rule index all require it. |
| Linear-Core governance | `LINEAR.md` `## Linear-at-the-core`; every forward log-entry shape in `todo.md`; `RULES.md` `R-LIN-*` | Actionable work must resolve to Linear or an explicit disposition everywhere it can be recorded. |
| `QUEUE-RUNS.md` | `LINEAR.md`; `PROMPTS.md`; `RULES.md`; `AGENTS.md`; `CLAUDE.md`; `GUIDE.md`; `README.md`; `todo.md` | Queue intake, lane ownership, prompt rendering, stop or skip policy, and closeout records must stay synchronized or unattended execution will drift. |
| Role boundaries | `CLAUDE.md`; `AGENTS.md`; `LINEAR.md`; `IMPLEMENTATION-PLAN.md`; `todo.md` `## Audit Watermarks` | Ownership drift creates audit ambiguity and false completion signals across the repo. |

## Staleness and Orphans

Staleness is caught at commit time by the Ripple Check and periodically by explicit coherence audits. Orphans are live docs that are neither indexed from `GUIDE.md` nor referenced by another live doc. Orphans do not get to linger: they are either indexed or retired in the same commit they are discovered.

## Motive

A repo that drifts is a repo that dies. Once two live docs disagree, every later reader pays the tax of deciding which one to trust. That turns source-of-truth documentation into folklore. You inherited a coherent map; leave a coherent map.

## Applies to

| Actor | Coherence duty |
|---|---|
| Codex | Runs the Ripple Check before every commit and attests it in the Work Record Self-audit |
| Claude Code | Verifies Ripple Check attestations during audit and runs periodic coherence sweeps at phase boundaries |
| Cowork | Confirms Ripple Check completion before any Linear state move |

## Where the rules live

- `RULES.md` `R-COH-01` through `R-COH-03` make the Ripple Check, Dependency Map upkeep, and orphan prevention enforceable.
- `AGENTS.md` `## Completion Authority` makes coherence a gate instead of a suggestion.
