# PROJECT_INTENT

## Purpose

This repository defines the source-of-truth intent, constraints, and build target for an autonomous coding system whose runtime accepts a coding objective, plans and executes bounded implementation work, runs deterministic quality gates, launches the target app locally, verifies the UI functionally and visually, routes failures into repair loops, and ends with a ready or not-ready decision backed by structured artifacts. It exists to make that implementation target explicit and buildable, not to act as a design-history dump or an open-ended multi-agent experimentation space.

## Primary users

The primary user is the operator responsible for running, evaluating, and tightening the system as an autonomous delivery harness. The system itself is organized around three working roles that the repo documents and implementation plan must keep distinct: the orchestrator, which is the deterministic supervisor that owns legality and completion; the builder, which in v1 is Codex as the sole code-writing lane; and the auditor, which is the review and verification path that inspects artifacts, reruns gates, and verifies the app and UI before a readiness outcome is emitted. GUIDE.md's reading order exists so both humans and agents can enter the repo through the same role-aware framing rather than reconstructing intent from scattered documents.

## Non-goals

In v1, this repository is not defining or building a control plane around OpenClaw, using Gemini as an active worker, supporting multi-writer parallelism, or depending on Zep or any other external semantic memory layer. It also does not target autonomous merge to `main`, autonomous production deployment, or broad plugin marketplace integrations as part of the core system. For memory, v1 explicitly excludes transcript-based shared memory, raw transcript retrieval as primary memory, chain-of-thought storage, and promotion of undocumented assumptions into durable truth.

## Success metrics

v1 is done when the system can be run as the narrow, reliable harness described in the canonical architecture and produce evidence for that claim. Observable completion means a run can accept a coding objective, validate the repo contract and run contract, enforce single-writer and single-browser ownership, implement backend and frontend changes through the bounded builder lane, run the required deterministic gates, launch the app locally, perform UI verification, route failures into repair loops, and finish with a readiness outcome that is justified by artifacts rather than narration. Those artifacts must include the structured evidence model named in the architecture: logs, exit codes, diffs, screenshots, traces, and structured reports. Just as importantly, completion in v1 still means staying narrow: one supported repo family, one writer, one browser verifier, one review path, runtime-owned correctness, and no auto-merge or auto-deploy behavior.

## Relationship to other docs

Use this file as the entry-point statement of intent, then go to `canonical-architecture.md` for the authoritative architecture, `RULES.md` for enforceable constraints, `LOGIC.md` for the control-flow explanation, `STRUCTURE.md` for where implementation pieces belong, and `GUIDE.md` for the recommended reading order across the repo. This document names what the project is for; the other documents explain how that purpose is constrained, structured, and implemented.

## Open questions

- Should this document eventually mirror any additional v1 scope constraints from `RULES.md` or completion signals from `IMPLEMENTATION-PLAN.md` that were outside this task's required reading set?
