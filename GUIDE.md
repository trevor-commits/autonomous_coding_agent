# Document Guide

**Date:** April 12, 2026
**Purpose:** This document explains what every core document in this repo is, why it exists, how it relates to the others, and when to read it. If you're new to this repo — human or agent — start here.

---

## How the Documents Fit Together

The documents in this repo form three layers: a source of truth for building, a set of companion docs that make the source of truth easier to understand and apply, and a set of historical docs that record how we got here.

```
                    ┌─────────────────────────┐
                    │  canonical-architecture  │  ← Build from this
                    │     (source of truth)    │
                    └────────────┬────────────┘
                                 │
    ┌────────┬────────┬──────────┬────────────┬──────────┬──────────────────────┐
    │        │        │          │            │          │                      │
 LOGIC.md RULES.md PROMPTS.md STRUCTURE.md AGENTS.md IMPLEMENTATION-PLAN.md
 (how it  (what's   (how AI    (where      (agent    (what to build,
  works)  allowed)  should     things go)  rules)    in what order)
                    work)
                                 │
                    ┌────────────┴────────────┐
                    │  canonical-architecture  │
                    │      -synthesis.md       │  ← How we got here
                    └────────────┬────────────┘
                                 │
          ┌──────────┬───────────┼───────────┬──────────┐
          │          │           │           │          │
      original    v2 deleg.  codex-audit  three-way  FINAL-ARCH
      review      arch.      reconcil.    reconcil.  DECISION
```

---

## Core Documents

These are the documents that matter for building and operating the system. Read them in this order for human onboarding and architectural understanding. Agent startup order is different: agents should read `AGENTS.md` at the start of the session, then use the order below as needed for deeper context.

### 1. `canonical-architecture.md`

**What it is:** The single source of truth for the entire system architecture. Every architectural decision, component spec, contract schema, phase machine definition, permission model, memory tier, and verification strategy is defined here.

**Why it exists:** Three independent AI architecture reviews (Claude, Codex, ChatGPT Pro) were reconciled into one converged design. This document is the output of that convergence — not a debate log, not a compromise, but the canonical implementation target.

**When to read it:** Before building anything. Before making any architectural decision. Before questioning whether a rule is real. If any other document in this repo conflicts with this one, this one wins.

**Who maintains it:** Trevor approves changes. Codex or Claude may propose updates, but changes to the canonical architecture require Trevor's sign-off.

### 2. `LOGIC.md`

**What it is:** A conceptual explanation of how the system works — the run lifecycle, the delegation model, the failure handling flow, the verification sequence, the memory tiers, and how all the pieces connect end to end.

**Why it exists:** The canonical architecture is comprehensive but dense (23 sections, 1200+ lines). LOGIC.md explains the same system in narrative form so you can understand the *why* without parsing every section of spec. It introduces no new decisions — everything in it is derived from canonical-architecture.md.

**When to read it:** When you need to understand the system's behavior conceptually. When onboarding. When you're about to build a module and want to understand how it fits into the whole before reading the spec for your specific section.

**Relationship to canonical-architecture.md:** LOGIC.md is a lens on the canonical architecture. If they ever conflict, canonical-architecture.md is correct and LOGIC.md should be updated.

### 3. `RULES.md`

**What it is:** Every enforceable rule in the system, organized by category — ownership boundaries, single-writer rules, commit rules, forbidden git operations, typed action rules, shell policy, contract requirements, phase transition rules, stop conditions, permission rules per agent, verification rules, memory rules, reporting rules, and v1 exclusions.

**Why it exists:** The canonical architecture embeds rules throughout 23 sections. RULES.md extracts them into one flat reference so you can quickly answer "is this allowed?" without searching the full spec. It introduces no new rules — everything in it traces back to canonical-architecture.md.

**When to read it:** When building a module that enforces constraints (policy engine, action validator, shell filter). When auditing whether a module correctly implements a rule. When an agent asks "can I do X?" — check RULES.md first.

**Relationship to canonical-architecture.md:** RULES.md is a derived index. If they conflict, canonical-architecture.md is correct.

### 4. `PROMPTS.md`

**What it is:** The prompt operating system for this project. It explains how prompts should be constructed, what every production prompt must contain, the mandatory self-test -> independent review -> fix audit loop, and the concrete prompt library for both building the platform and operating a real run.

**Why it exists:** The canonical architecture says the supervisor owns legality and prompts own strategy, implementation shaping, diagnosis, review, and audit. Without a prompt source of truth, those roles drift into ad hoc mega-prompts, weak review discipline, and inconsistent testing cadence. This document prevents that.

**When to read it:** Before authoring new strategy prompts. Before changing review or audit behavior. Before deciding how often testing, peer review, and re-audit should run.

**Relationship to canonical-architecture.md:** PROMPTS.md is the companion for prompt behavior, not architectural authority. If a prompt rule conflicts with the canonical role boundaries, the canonical architecture wins and PROMPTS.md should be updated.

### 5. `STRUCTURE.md`

**What it is:** A map of every folder in this repo and the target repo — what belongs in each, who manages it, when it gets created, and what does not belong there.

**Why it exists:** Once implementation starts, Codex will be creating directories and files across multiple phases. Without a clear structure doc, files end up in random places and the repo becomes disorganized. This document prevents that by defining the layout before code exists.

**When to read it:** Before creating any new directory or file. Before asking "where does this go?" If you add a new top-level folder, update this document.

**Relationship to canonical-architecture.md:** The run directory layout comes from Section 15. The worktree layout comes from Section 12. The supervisor module list comes from the implementation plan. STRUCTURE.md compiles these into one reference.

### 6. `AGENTS.md`

**What it is:** Operating instructions for any agent (AI or human) working in this repo. Points to the source of truth, lists working rules (preserve source-of-truth distinction, don't re-open settled decisions, keep runtime consistent with canonical doc), and states the current implementation priority.

**Why it exists:** Agents start conversations without context. AGENTS.md gives them the minimum orientation to avoid making mistakes — which doc is authoritative, what the settled decisions are, and what not to touch casually.

**When to read it:** At the start of every agent session that touches this repo. It's short — read the whole thing. For humans reading the repo for the first time, it makes more sense after the canonical architecture and companion docs establish the system context.

**Relationship to canonical-architecture.md:** AGENTS.md points to it as the authority and summarizes the key operating constraints. It does not redefine any architecture.

### 7. `IMPLEMENTATION-PLAN.md`

**What it is:** The step-by-step execution plan — what to build, in what order, who builds it, how to verify each step, and what the exit criteria are for each phase. Covers Phase 0 (repo prep) through Phase 5 (operational memory hardening), with exact Codex prompts, verification checklists, baseline metrics, and risk mitigation.

**Why it exists:** The canonical architecture says *what* to build. The implementation plan says *how* to build it, in what sequence, with what tooling, and how to know each step is done.

**When to read it:** When starting a new phase. When writing a Codex prompt. When deciding whether the current phase is complete. When comparing metrics across phases.

**Relationship to canonical-architecture.md:** The implementation plan is derived from the architecture. Every module it tells Codex to build maps to a component or section in the canonical architecture. If the plan and the architecture conflict on a design point, the architecture wins.

### 8. `GUIDE.md` (this document)

**What it is:** The meta-document you're reading now. Explains what every document is, why it exists, and how they relate.

**Why it exists:** The repo has grown to include 12+ documents. Without a guide, it's not obvious which ones matter, which are historical, and what order to read them in. This document solves the "where do I start?" problem.

**When to read it:** When you're new to the repo. When you're not sure which document to consult for a specific question.

### 9. `README.md`

**What it is:** The repo's front page. Lists the recommended reading order, the design-history documents, the current architectural direction, and the next build focus.

**Why it exists:** Standard repo orientation. The first thing anyone sees.

**When to read it:** First. It points you to everything else, including this guide.

### 10. `CHANGELOG.md` (does not exist yet — created in Phase 1)

**What it is:** A running log of what was built, when, and by whom.

**Why it exists:** The implementation plan tells Codex to log changes here after every module. This creates an audit trail of what was built in what order.

**When to read it:** When you want to know what's been built so far or when a specific module was added.

---

## Design-History Documents

These documents record the architectural debate that produced the canonical architecture. They are not the implementation authority — `canonical-architecture.md` supersedes all of them. But they remain useful for understanding *why* decisions were made.

### `canonical-architecture-synthesis.md`

The narrative history of how the architecture evolved through four stages: component thinking → AI manager thinking → delivery harness thinking → final responsibility split. Accurately records what each AI (Claude, Codex, ChatGPT Pro) got right and wrong, including Claude's control-path inversion in v2 and the subsequent concession. This is the most useful historical doc because it explains the *reasoning* behind the settled decisions.

### `FINAL-ARCHITECTURE-DECISION.md`

An executive summary of the converged architecture, written during the convergence. Marked as "Historical summary, superseded as implementation authority." Still useful as a quick-reference overview of the key design decisions and their sources (which AI proposed each one and why).

### `autonomous-agent-system-architecture-review.md`

Claude's original 17-section architecture review — the foundation document. Covers the full stack audit, agent roles, branch strategy, auth, cost, failure modes, MVP scope, and roadmap. Historical context for where the project started.

### `agent-delegation-architecture-v2.md`

Claude's delegation model that put Claude as the autonomous manager. The orchestration model is superseded (the canonical architecture inverts the control relationship), but the prompt library and delegation patterns remain valid reference material for the Phase 4 strategy layer design.

### `codex-audit-and-reconciliation.md`

Point-by-point Claude vs. Codex reconciliation. Documents where they agreed, where they disagreed, and what the merged position was at that stage. The adopted schemas (run contract, defect packet) originated here.

### `three-way-reconciliation-final.md`

The three-model merge with scorecard. Documents how Claude, Codex, and ChatGPT Pro's reviews were compared and reconciled. Historical reference for the convergence process.

---

## Quick Reference: Which Document Answers Which Question

| Question | Document |
|----------|----------|
| What is the architecture? | `canonical-architecture.md` |
| How does the system work conceptually? | `LOGIC.md` |
| Is this action allowed? | `RULES.md` |
| How should prompts, reviews, and re-audits work? | `PROMPTS.md` |
| Where does this file go? | `STRUCTURE.md` |
| What should an agent know before working here? | `AGENTS.md` |
| What do I build next? | `IMPLEMENTATION-PLAN.md` |
| What are all these documents? | `GUIDE.md` (this file) |
| Where do I start? | `README.md` |
| What's been built so far? | `CHANGELOG.md` |
| Why was this decision made? | `canonical-architecture-synthesis.md` |
| What did the original reviews say? | Design-history documents |
